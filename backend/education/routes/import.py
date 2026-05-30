"""
iMato 教育培训管理系统 - 批量导入 API
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from io import BytesIO

from backend.database import get_db
from backend.education.models.student import StudentProfile, ParentInfo
from backend.education.schemas.student import StudentProfileCreate

router = APIRouter(prefix="/api/v1/import", tags=["批量导入"])


@router.post("/students")
async def batch_import_students(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    批量导入学员数据

    Args:
        file: Excel 文件
        db: 数据库会话

    Returns:
        导入结果统计
    """
    # 验证文件格式
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持 Excel 文件格式")

    try:
        # 读取 Excel 文件
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))

        # 验证必填列
        required_columns = ['姓名', '性别', '手机号']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必填列：{', '.join(missing_columns)}"
            )

        # 解析和验证数据
        success_count = 0
        error_list = []

        for index, row in df.iterrows():
            try:
                # 数据验证
                errors = validate_student_row(row, index + 2)  # +2 因为 Excel 行号从 1 开始，且包含表头
                if errors:
                    error_list.extend(errors)
                    continue

                # 创建学员数据
                student_data = {
                    'name': str(row['姓名']),
                    'gender': 'male' if str(row.get('性别', '男')) == '男' else 'female',
                    'phone': str(row.get('手机号', '')),
                    'email': str(row.get('邮箱', '')) if pd.notna(row.get('邮箱')) else None,
                    'grade': str(row.get('年级', '')) if pd.notna(row.get('年级')) else None,
                    'school': str(row.get('学校', '')) if pd.notna(row.get('学校')) else None,
                    'total_purchased_hours': int(row.get('购买课时数', 0)),
                    'total_consumed_hours': int(row.get('已消耗课时数', 0)),
                }

                # 计算剩余课时
                student_data['remaining_hours'] = (
                    student_data['total_purchased_hours'] -
                    student_data['total_consumed_hours']
                )

                # 创建学员记录
                student = StudentProfile(**student_data)
                db.add(student)
                db.commit()
                db.refresh(student)

                # 如果有家长信息，也一并创建
                parent_name = row.get('家长姓名')
                if pd.notna(parent_name):
                    parent = ParentInfo(
                        name=str(parent_name),
                        relationship_type=str(row.get('关系', '父亲')),
                        phone=str(row.get('家长手机号', '')),
                        student_id=student.id,
                    )
                    db.add(parent)
                    db.commit()

                success_count += 1

            except Exception as e:
                error_list.append({
                    'row': index + 2,
                    'message': str(e),
                    'data': row.to_dict(),
                })

        return {
            'success': success_count,
            'failed': len(error_list),
            'errors': error_list,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败：{str(e)}")


def validate_student_row(row: pd.Series, row_number: int) -> List[dict]:
    """
    验证单行学员数据

    Args:
        row: Excel 行数据
        row_number: 行号

    Returns:
        错误列表
    """
    errors = []

    # 验证姓名
    if pd.isna(row.get('姓名')) or not str(row['姓名']).strip():
        errors.append({
            'row': row_number,
            'message': '姓名不能为空',
        })

    # 验证手机号
    phone = str(row.get('手机号', ''))
    if phone and not phone.isdigit():
        errors.append({
            'row': row_number,
            'message': '手机号必须为数字',
        })
    elif phone and not (10 <= len(phone) <= 15):
        errors.append({
            'row': row_number,
            'message': '手机号格式不正确 (10-15 位)',
        })

    # 验证身份证号
    id_card = str(row.get('身份证号', ''))
    if pd.notna(row.get('身份证号')) and id_card:
        if len(id_card) != 18:
            errors.append({
                'row': row_number,
                'message': '身份证号必须为 18 位',
            })

    return errors


@router.get("/students/template")
async def download_student_template():
    """
    下载学员导入模板

    Returns:
        Excel 文件
    """
    # 创建示例数据
    data = {
        '姓名': ['张三', '李四'],
        '性别': ['男', '女'],
        '出生日期': ['2010-01-01', '2011-02-02'],
        '年级': ['初三', '初二'],
        '学校': ['XX 中学', 'XX 外国语学校'],
        '手机号': ['13800138000', '13900139000'],
        '邮箱': ['zhangsan@example.com', 'lisi@example.com'],
        '身份证号': ['110101201001011234', '110101201102021234'],
        '购买课时数': [100, 80],
        '已消耗课时数': [0, 0],
        '家长姓名': ['张父', '李母'],
        '关系': ['父亲', '母亲'],
        '家长手机号': ['13700137000', '13600136000'],
    }

    df = pd.DataFrame(data)

    # 保存到 BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='学员导入模板')

    output.seek(0)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=学员导入模板.xlsx"},
    )
