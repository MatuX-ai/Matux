import base64
from datetime import datetime
from io import BytesIO
import logging
from typing import Any, Dict, List, Optional

import cv2
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
import numpy as np
from pydantic import BaseModel

from ..middleware.auth import get_current_user
from ..models.user import User
from ..services.complex_gesture_recognizer import complex_gesture_recognizer
from ..services.mediapipe_gesture_service import mediapipe_gesture_recognizer
from ..services.reward_event_bus import RewardEvent, reward_event_bus

router = APIRouter(prefix="/gesture", tags=["手势识别"])
logger = logging.getLogger(__name__)


class GestureRecognitionResponse(BaseModel):
    """手势识别响应模型"""

    success: bool
    message: str
    data: Dict[str, Any]


class HiddenTaskRewardRequest(BaseModel):
    """隐藏任务奖励请求模型"""

    task_name: str
    points: int
    timestamp: str
    user_id: Optional[int] = None


@router.post("/recognize")
async def recognize_gesture(
    image: UploadFile = File(...),
    timestamp: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """实时手势识别"""
    try:
        # 读取上传的图像
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise HTTPException(status_code=400, detail="无法解码图像")

        # 处理手势识别
        result = mediapipe_gesture_recognizer.process_frame(frame)

        # 发布手势识别事件
        if result["recognized_gestures"]:
            for gesture in result["recognized_gestures"]:
                event = RewardEvent(
                    event_type="gesture_recognized",
                    user_id=current_user.id,
                    data={
                        "gesture_type": gesture.gesture_type.value,
                        "confidence": gesture.confidence,
                        "timestamp": timestamp,
                    },
                    timestamp=(
                        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        if "Z" in timestamp
                        else datetime.now()
                    ),
                )
                await reward_event_bus.publish(event)

        # 处理复杂手势序列
        if result["complex_sequences"]:
            for sequence_name, confidence in result["complex_sequences"]:
                event = RewardEvent(
                    event_type="complex_gesture_sequence",
                    user_id=current_user.id,
                    data={
                        "sequence_name": sequence_name,
                        "confidence": confidence,
                        "timestamp": timestamp,
                    },
                    timestamp=(
                        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        if "Z" in timestamp
                        else datetime.now()
                    ),
                )
                await reward_event_bus.publish(event)

        logger.info(
            f"手势识别完成: 用户{current_user.id}, 识别到{len(result['recognized_gestures'])}个手势"
        )

        return GestureRecognitionResponse(
            success=True, message="手势识别成功", data=result
        )

    except Exception as e:
        logger.error(f"手势识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/hidden-task-reward")
async def handle_hidden_task_reward(
    request: HiddenTaskRewardRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """处理隐藏任务奖励"""
    try:
        # 根据任务名称确定奖励类型
        reward_amount = request.points
        reward_reason = ""

        if request.task_name == "secret_task_1":
            reward_reason = "隐藏任务1奖励 - 手势序列解锁"
        elif request.task_name == "secret_task_2":
            reward_reason = "隐藏任务2奖励 - 复杂手势挑战"
        elif request.task_name == "secret_task_3":
            reward_reason = "隐藏任务3奖励 - 高级手势技能"
        else:
            reward_reason = f"隐藏任务奖励 - {request.task_name}"

        # 发布奖励事件
        event = RewardEvent(
            event_type="hidden_task_completed",
            user_id=current_user.id,
            data={
                "task_name": request.task_name,
                "points": reward_amount,
                "timestamp": request.timestamp,
            },
            timestamp=(
                datetime.fromisoformat(request.timestamp.replace("Z", "+00:00"))
                if "Z" in request.timestamp
                else datetime.now()
            ),
        )

        background_tasks.add_task(reward_event_bus.publish, event)

        logger.info(
            f"隐藏任务奖励已处理: 用户{current_user.id}, 任务{request.task_name}, 奖励{reward_amount}积分"
        )

        return {
            "success": True,
            "message": "隐藏任务奖励已处理",
            "data": {
                "user_id": current_user.id,
                "task_name": request.task_name,
                "points_awarded": reward_amount,
                "reason": reward_reason,
            },
        }

    except Exception as e:
        logger.error(f"处理隐藏任务奖励失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/statistics")
async def get_gesture_statistics(current_user: User = Depends(get_current_user)):
    """获取手势识别统计信息"""
    try:
        statistics = mediapipe_gesture_recognizer.get_gesture_statistics()

        return {"success": True, "data": statistics}

    except Exception as e:
        logger.error(f"获取手势统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/history")
async def get_gesture_history(
    limit: int = 50, current_user: User = Depends(get_current_user)
):
    """获取用户手势历史"""
    try:
        # 这里应该从数据库查询用户的历史手势记录
        # 暂时返回空数据
        history = []

        return {
            "success": True,
            "data": {"history": history, "total_count": len(history)},
        }

    except Exception as e:
        logger.error(f"获取手势历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/test/sample-frame")
async def test_gesture_recognition(
    background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)
):
    """测试手势识别功能（使用样例帧）"""
    try:
        # 创建一个简单的测试图像
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        test_frame[:, :] = [100, 150, 200]  # 蓝色背景

        # 添加一些简单的手势形状（模拟）
        cv2.circle(test_frame, (320, 240), 50, (0, 255, 0), -1)  # 绿色圆圈
        cv2.rectangle(test_frame, (200, 150), (440, 330), (255, 0, 0), 3)  # 蓝色矩形

        # 处理测试帧
        result = mediapipe_gesture_recognizer.process_frame(test_frame)

        # 模拟识别到一些手势
        test_gestures = [
            {
                "type": "circle",
                "confidence": 0.85,
                "duration": 1.2,
                "metadata": '{"source": "test"}',
            }
        ]

        result["recognized_gestures"] = test_gestures

        # 发布测试事件
        event = RewardEvent(
            event_type="gesture_recognized",
            user_id=current_user.id,
            data={
                "gesture_type": "circle",
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat(),
            },
            timestamp=datetime.now(),
        )

        background_tasks.add_task(reward_event_bus.publish, event)

        return GestureRecognitionResponse(
            success=True, message="测试手势识别完成", data=result
        )

    except Exception as e:
        logger.error(f"测试手势识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/clear-buffer")
async def clear_gesture_buffer(current_user: User = Depends(get_current_user)):
    """清空手势缓冲区"""
    try:
        complex_gesture_recognizer.clear_buffer()

        return {"success": True, "message": "手势缓冲区已清空"}

    except Exception as e:
        logger.error(f"清空手势缓冲区失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.get("/supported-gestures")
async def get_supported_gestures():
    """获取支持的手势类型列表"""
    try:
        from ..services.complex_gesture_recognizer import GestureType

        gestures = []
        for gesture_type in GestureType:
            gestures.append(
                {
                    "name": gesture_type.name,
                    "value": gesture_type.value,
                    "description": get_gesture_description(gesture_type),
                }
            )

        return {
            "success": True,
            "data": {
                "basic_gestures": gestures[:12],  # 基础手势
                "special_gestures": gestures[12:],  # 特殊手势
                "total_count": len(gestures),
            },
        }

    except Exception as e:
        logger.error(f"获取支持手势列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


def get_gesture_description(gesture_type) -> str:
    """获取手势描述"""
    descriptions = {
        "UNKNOWN": "未知手势",
        "TAP": "点击手势",
        "SWIPE_LEFT": "左滑手势",
        "SWIPE_RIGHT": "右滑手势",
        "SWIPE_UP": "上滑手势",
        "SWIPE_DOWN": "下滑手势",
        "PINCH_IN": "捏合手势",
        "PINCH_OUT": "展开手势",
        "ROTATE_CLOCKWISE": "顺时针旋转",
        "ROTATE_COUNTERCLOCKWISE": "逆时针旋转",
        "CIRCLE": "圆形手势",
        "V_SHAPE": "V字手势",
        "OK_SIGN": "OK手势",
        "THUMBS_UP": "竖大拇指",
        "PALM_OPEN": "手掌张开",
        "FIST": "握拳",
        "SECRET_GESTURE_1": "隐藏任务手势1",
        "SECRET_GESTURE_2": "隐藏任务手势2",
    }

    return descriptions.get(gesture_type.name, "未定义手势")
