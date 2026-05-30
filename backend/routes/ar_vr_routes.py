"""
AR/VR课程内容API路由
提供AR/VR课程内容管理、传感器数据传输和交互控制的RESTful API
"""

import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from models.ar_vr_content import (
    ARVRContent,
    ARVRContentCreate,
    ARVRContentResponse,
    ARVRContentType,
    ARVRContentUpdate,
    ARVRInteractionLog,
    ARVRPlatform,
    ARVRProgressTracking,
    ARVRSensorData,
    InteractionLogCreate,
    ProgressTrackingCreate,
    ProgressTrackingResponse,
    SensorDataCreate,
    SensorType,
)
from models.user import User
from services.ar_physics_service import ARPhysicsService
from services.ar_vr_content_service import ARVRContentService
from utils.dependencies import get_current_user_sync, get_sync_db

# 临时替代函数
def get_tenant_id() -> int:
    """返回默认租户 ID"""
    return 1

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org/{org_id}/arvr", tags=["AR/VR课程"])


# 依赖注入函数
def get_arvr_service(db: Session = Depends(get_sync_db)) -> ARVRContentService:
    return ARVRContentService(db)


def get_physics_service(db: Session = Depends(get_sync_db)) -> ARPhysicsService:
    return ARPhysicsService(db)


# AR/VR内容管理API
@router.post("/contents", response_model=ARVRContentResponse)
async def create_arvr_content(
    org_id: int = get_tenant_id(),
    content_data: ARVRContentCreate = None,
    current_user: User = Depends(get_current_user_sync),
    arvr_service: ARVRContentService = Depends(get_arvr_service),
):
    """
    创建AR/VR课程内容
    """
    try:
        content = arvr_service.create_arvr_content(org_id, content_data, current_user)
        return content
    except Exception as e:
        logger.error(f"创建AR/VR内容失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contents", response_model=List[ARVRContentResponse])
async def list_arvr_contents(
    org_id: int = get_tenant_id(),
    course_id: Optional[int] = Query(None, description="课程ID"),
    lesson_id: Optional[int] = Query(None, description="课时ID"),
    content_type: Optional[ARVRContentType] = Query(None, description="内容类型"),
    platform: Optional[ARVRPlatform] = Query(None, description="平台类型"),
    arvr_service: ARVRContentService = Depends(get_arvr_service),
):
    """
    列出AR/VR课程内容
    """
    try:
        contents = arvr_service.list_arvr_contents(org_id, course_id, lesson_id)

        # 应用过滤条件
        if content_type:
            contents = [c for c in contents if c.content_type == content_type]
        if platform:
            contents = [c for c in contents if c.platform == platform]

        return contents
    except Exception as e:
        logger.error(f"获取AR/VR内容列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取内容列表失败")


@router.get("/contents/{content_id}", response_model=ARVRContentResponse)
async def get_arvr_content(
    content_id: int,
    org_id: int = get_tenant_id(),
    arvr_service: ARVRContentService = Depends(get_arvr_service),
):
    """
    获取AR/VR课程内容详情
    """
    try:
        content = arvr_service.get_arvr_content(content_id, org_id)
        return content
    except Exception as e:
        logger.error(f"获取AR/VR内容失败: {e}")
        raise HTTPException(status_code=404, detail="内容不存在")


@router.put("/contents/{content_id}", response_model=ARVRContentResponse)
async def update_arvr_content(
    content_id: int,
    update_data: ARVRContentUpdate,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    arvr_service: ARVRContentService = Depends(get_arvr_service),
):
    """
    更新AR/VR课程内容
    """
    try:
        content = arvr_service.update_arvr_content(content_id, org_id, update_data)
        return content
    except Exception as e:
        logger.error(f"更新AR/VR内容失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/contents/{content_id}")
async def delete_arvr_content(
    content_id: int,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    arvr_service: ARVRContentService = Depends(get_arvr_service),
):
    """
    删除AR/VR课程内容
    """
    try:
        arvr_service.delete_arvr_content(content_id, org_id)
        return {"message": "内容删除成功"}
    except Exception as e:
        logger.error(f"删除AR/VR内容失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/contents/{content_id}/upload-build")
async def upload_unity_build(
    content_id: int,
    org_id: int = get_tenant_id(),
    build_file: UploadFile = File(..., description="Unity WebGL构建文件(ZIP格式)"),
    thumbnail_file: UploadFile = File(None, description="缩略图文件"),
    current_user: User = Depends(get_current_user_sync),
    arvr_service: ARVRContentService = Depends(get_arvr_service),
):
    """
    上传Unity WebGL构建文件
    """
    try:
        result = await arvr_service.upload_unity_build(
            content_id, org_id, build_file, thumbnail_file
        )
        return result
    except Exception as e:
        logger.error(f"上传Unity构建文件失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# 传感器数据API
@router.post("/contents/{content_id}/sensor-data")
async def create_sensor_data(
    content_id: int,
    sensor_data: SensorDataCreate,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    创建传感器数据记录
    """
    try:
        sensor_record = ARVRSensorData(
            content_id=content_id,
            user_id=current_user.id,
            org_id=org_id,
            sensor_type=sensor_data.sensor_type,
            data_payload=sensor_data.data_payload,
            session_id=sensor_data.session_id,
            latitude=sensor_data.latitude,
            longitude=sensor_data.longitude,
            altitude=sensor_data.altitude,
            captured_at=(
                sensor_data.captured_at if hasattr(sensor_data, "captured_at") else None
            ),
        )

        db.add(sensor_record)
        db.commit()
        db.refresh(sensor_record)

        return sensor_record
    except Exception as e:
        db.rollback()
        logger.error(f"创建传感器数据失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contents/{content_id}/sensor-data")
async def list_sensor_data(
    content_id: int,
    org_id: int = get_tenant_id(),
    sensor_type: Optional[SensorType] = Query(None, description="传感器类型"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    limit: int = Query(100, description="返回记录数限制", le=1000),
    db: Session = Depends(get_sync_db),
):
    """
    获取传感器数据列表
    """
    try:
        query = db.query(ARVRSensorData).filter(
            ARVRSensorData.content_id == content_id, ARVRSensorData.org_id == org_id
        )

        if sensor_type:
            query = query.filter(ARVRSensorData.sensor_type == sensor_type)

        if session_id:
            query = query.filter(ARVRSensorData.session_id == session_id)

        sensor_data = (
            query.order_by(ARVRSensorData.captured_at.desc()).limit(limit).all()
        )
        return sensor_data
    except Exception as e:
        logger.error(f"获取传感器数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取传感器数据失败")


# 交互日志API
@router.post("/contents/{content_id}/interactions")
async def log_interaction(
    content_id: int,
    interaction_data: InteractionLogCreate,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    记录用户交互日志
    """
    try:
        interaction_log = ARVRInteractionLog(
            content_id=content_id,
            user_id=current_user.id,
            org_id=org_id,
            interaction_type=interaction_data.interaction_type,
            interaction_data=interaction_data.interaction_data,
            interaction_mode=interaction_data.interaction_mode,
            success=interaction_data.success,
            response_time=interaction_data.response_time,
            feedback_score=interaction_data.feedback_score,
            session_id=interaction_data.session_id,
            duration=interaction_data.duration,
            created_at=None,  # 使用数据库默认值
        )

        db.add(interaction_log)
        db.commit()
        db.refresh(interaction_log)

        return interaction_log
    except Exception as e:
        db.rollback()
        logger.error(f"记录交互日志失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# 进度跟踪API
@router.post("/contents/{content_id}/progress")
async def update_progress(
    content_id: int,
    progress_data: ProgressTrackingCreate,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    physics_service: ARPhysicsService = Depends(get_physics_service),
):
    """
    更新学习进度
    """
    try:
        progress_dict = progress_data.dict()
        progress_dict["user_id"] = current_user.id
        physics_service.update_progress_tracking(
            content_id, current_user.id, progress_dict
        )

        return {"message": "进度更新成功"}
    except Exception as e:
        logger.error(f"更新进度失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contents/{content_id}/progress")
async def get_progress(
    content_id: int,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    获取学习进度
    """
    try:
        progress = (
            db.query(ARVRProgressTracking)
            .filter(
                ARVRProgressTracking.content_id == content_id,
                ARVRProgressTracking.user_id == current_user.id,
                ARVRProgressTracking.org_id == org_id,
            )
            .first()
        )

        if not progress:
            # 返回默认进度
            return ProgressTrackingResponse(
                id=0,
                content_id=content_id,
                user_id=current_user.id,
                org_id=org_id,
                progress_percentage=0.0,
                current_state={},
                milestones_reached=[],
                started_at=None,
                last_accessed_at=None,
                completed_at=None,
                time_spent=0.0,
                interaction_count=0,
                assessment_score=None,
            )

        return progress
    except Exception as e:
        logger.error(f"获取进度失败: {e}")
        raise HTTPException(status_code=500, detail="获取进度失败")


# 物理引擎API
@router.get("/contents/{content_id}/physics-state")
async def get_physics_state(
    content_id: int,
    org_id: int = get_tenant_id(),
    physics_service: ARPhysicsService = Depends(get_physics_service),
):
    """
    获取物理引擎状态
    """
    try:
        state = physics_service.get_physics_state(content_id)
        return state
    except Exception as e:
        logger.error(f"获取物理状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取物理状态失败")


@router.post("/contents/{content_id}/voice-command")
async def handle_voice_command(
    content_id: int,
    command_data: dict,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    physics_service: ARPhysicsService = Depends(get_physics_service),
):
    """
    处理语音命令
    """
    try:
        command = command_data.get("command", "")
        result = physics_service.handle_voice_command(
            content_id, current_user.id, command
        )
        return result
    except Exception as e:
        logger.error(f"处理语音命令失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/contents/{content_id}/gesture")
async def handle_gesture_interaction(
    content_id: int,
    gesture_data: dict,
    org_id: int = get_tenant_id(),
    current_user: User = Depends(get_current_user_sync),
    physics_service: ARPhysicsService = Depends(get_physics_service),
):
    """
    处理手势交互
    """
    try:
        result = physics_service.handle_gesture_interaction(
            content_id, current_user.id, gesture_data
        )
        return result
    except Exception as e:
        logger.error(f"处理手势交互失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# WebSocket路由
@router.websocket("/ws/sensor-stream/{content_id}")
async def sensor_data_stream(
    websocket: WebSocket, content_id: int, org_id: int = get_tenant_id()
):
    """
    传感器数据实时流WebSocket连接
    """
    # 这里应该集成WebRTC管理器
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # 处理接收到的传感器数据
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info(f"传感器数据流连接断开: content_id={content_id}")


# 统计信息API
@router.get("/contents/{content_id}/statistics")
async def get_content_statistics(
    content_id: int, org_id: int = get_tenant_id(), db: Session = Depends(get_sync_db)
):
    """
    获取内容统计数据
    """
    try:
        # 获取视图次数
        view_count = (
            db.query(ARVRContent)
            .filter(ARVRContent.id == content_id, ARVRContent.org_id == org_id)
            .first()
            .view_count
        )

        # 获取完成次数
        completion_count = (
            db.query(ARVRProgressTracking)
            .filter(
                ARVRProgressTracking.content_id == content_id,
                ARVRProgressTracking.org_id == org_id,
                ARVRProgressTracking.completed_at.isnot(None),
            )
            .count()
        )

        # 获取平均评分
        avg_rating = (
            db.query(func.avg(ARVRInteractionLog.feedback_score))
            .filter(
                ARVRInteractionLog.content_id == content_id,
                ARVRInteractionLog.org_id == org_id,
                ARVRInteractionLog.feedback_score.isnot(None),
            )
            .scalar()
            or 0.0
        )

        # 获取交互次数
        interaction_count = (
            db.query(ARVRInteractionLog)
            .filter(
                ARVRInteractionLog.content_id == content_id,
                ARVRInteractionLog.org_id == org_id,
            )
            .count()
        )

        return {
            "view_count": view_count,
            "completion_count": completion_count,
            "average_rating": round(float(avg_rating), 2),
            "interaction_count": interaction_count,
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


# 内容推荐API
@router.get("/recommendations")
async def get_arvr_recommendations(
    org_id: int = get_tenant_id(),
    user_id: Optional[int] = Query(None, description="用户ID"),
    limit: int = Query(10, description="推荐数量", le=50),
    db: Session = Depends(get_sync_db),
):
    """
    获取AR/VR内容推荐
    """
    try:
        # 基于流行度和用户兴趣的简单推荐算法
        query = db.query(ARVRContent).filter(
            ARVRContent.org_id == org_id, ARVRContent.is_active == True
        )

        # 按视图次数排序
        contents = query.order_by(ARVRContent.view_count.desc()).limit(limit).all()

        # 如果有用户ID，可以加入个性化推荐逻辑
        if user_id:
            # 这里可以实现更复杂的推荐算法
            pass

        return contents
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail="获取推荐失败")
