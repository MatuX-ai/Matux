"""
iMato 教育培训管理系统 - 签到管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import qrcode
from io import BytesIO
from fastapi.responses import StreamingResponse

from backend.database import get_db
from backend.education.models.attendance import AttendanceRecord, QRCodeToken, CheckinStatus
from backend.education.models.student import StudentProfile
from backend.education.schemas.attendance import (
    CheckinRequest,
    CheckinResponse,
    AttendanceStats,
)

router = APIRouter(prefix="/api/v1/attendance", tags=["签到管理"])


@router.post("/qr/generate")
def generate_qr_code(
    course_schedule_id: str,
    teacher_id: str,
    valid_minutes: int = 5,
    db: Session = Depends(get_db),
):
    """
    生成动态签到二维码

    Args:
        course_schedule_id: 课程表 ID
        teacher_id: 教师 ID
        valid_minutes: 二维码有效时间 (分钟)

    Returns:
        二维码图片和 token 信息
    """
    # 生成 Token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=valid_minutes)

    # 保存 Token 到数据库
    qr_token = QRCodeToken(
        id=str(uuid.uuid4()),
        token=token,
        course_schedule_id=course_schedule_id,
        teacher_id=teacher_id,
        expires_at=expires_at,
    )
    db.add(qr_token)
    db.commit()

    # 生成二维码图片
    qr_data = f"CHECKIN:{token}:{course_schedule_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # 保存到 BytesIO
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "X-Token": token,
            "X-Expires-At": expires_at.isoformat(),
            "Content-Disposition": f"attachment; filename=checkin_qr_{course_schedule_id}.png",
        },
    )


@router.post("/checkin", response_model=CheckinResponse)
def checkin(checkin_data: CheckinRequest, db: Session = Depends(get_db)):
    """
    学生扫码签到

    Args:
        checkin_data: 签到请求数据

    Returns:
        签到结果
    """
    # 验证 Token
    token = db.query(QRCodeToken).filter(
        QRCodeToken.token == checkin_data.token
    ).first()

    if not token:
        raise HTTPException(status_code=400, detail="无效的二维码")

    if token.is_used:
        raise HTTPException(status_code=400, detail="二维码已被使用")

    if datetime.utcnow() > token.expires_at:
        raise HTTPException(status_code=400, detail="二维码已过期")

    # 验证学生
    student = db.query(StudentProfile).filter(
        StudentProfile.id == checkin_data.student_id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 检查课时余额
    if student.remaining_hours <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"课时不足，当前剩余{student.remaining_hours}课时"
        )

    # 计算应扣课时 (假设每次课 2 课时)
    deducted_hours = 2

    # 创建签到记录
    attendance = AttendanceRecord(
        id=str(uuid.uuid4()),
        student_id=student.id,
        course_schedule_id=token.course_schedule_id,
        scheduled_time=datetime.utcnow(),
        checkin_time=datetime.utcnow(),
        status=CheckinStatus.SUCCESS,
        checkin_method="qr_code",
        deducted_hours=deducted_hours,
    )

    db.add(attendance)

    # 扣减课时
    student.remaining_hours -= deducted_hours
    student.total_consumed_hours += deducted_hours

    # 标记 Token 已使用
    token.is_used = True
    token.used_at = datetime.utcnow()
    token.used_by_student_id = student.id

    db.commit()

    return {
        "success": True,
        "message": "签到成功",
        "deducted_hours": deducted_hours,
        "remaining_hours": student.remaining_hours,
        "student_name": student.name,
    }


@router.get("/records/{student_id}")
def get_attendance_records(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    获取学生签到记录

    Args:
        student_id: 学生 ID
        page: 页码
        page_size: 每页数量

    Returns:
        签到记录列表
    """
    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .order_by(AttendanceRecord.checkin_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .count()
    )

    return {
        "total": total,
        "list": records,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats/{student_id}", response_model=AttendanceStats)
def get_attendance_stats(student_id: str, db: Session = Depends(get_db)):
    """
    获取学生签到统计

    Args:
        student_id: 学生 ID

    Returns:
        统计数据
    """
    total_checkins = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == CheckinStatus.SUCCESS,
        )
        .count()
    )

    total_late = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == CheckinStatus.LATE,
        )
        .count()
    )

    total_absent = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.status == CheckinStatus.ABSENT,
        )
        .count()
    )

    total_deducted_hours = (
        db.query(AttendanceRecord.deducted_hours)
        .filter(AttendanceRecord.student_id == student_id)
        .all()
    )
    total_hours = sum([h[0] for h in total_deducted_hours]) or 0

    return {
        "total_checkins": total_checkins,
        "total_late": total_late,
        "total_absent": total_absent,
        "total_deducted_hours": total_hours,
    }
