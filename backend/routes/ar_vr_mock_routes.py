"""
AR/VR Mock接口API路由
提供完整的Mock服务RESTful API端点
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.ar_vr_mock_service import (
    MOCK_SCENARIOS,
    ARVRMockOrchestrator,
    MockScenario,
)
from utils.database import get_db

logger = logging.getLogger(__name__)

# 创建路由实例
mock_router = APIRouter(prefix="/api/v1/mock/arvr", tags=["AR/VR Mock服务"])

# 全局Mock服务编排器实例
mock_orchestrator: Optional[ARVRMockOrchestrator] = None


async def get_mock_orchestrator_dependency(
    db: Session = Depends(get_db),
) -> ARVRMockOrchestrator:
    """获取Mock服务编排器依赖"""
    global mock_orchestrator
    if mock_orchestrator is None:
        mock_orchestrator = ARVRMockOrchestrator(db)
    return mock_orchestrator


@mock_router.post("/sessions", summary="启动Mock会话")
async def start_mock_session(
    content_id: int = Body(..., description="AR/VR内容ID"),
    user_id: int = Body(..., description="用户ID"),
    scenario: str = Body("ideal_conditions", description="Mock场景"),
    db: Session = Depends(get_db),
):
    """
    启动一个新的AR/VR Mock会话

    场景选项:
    - ideal_conditions: 理想条件（高成功率，低延迟）
    - hardware_failure: 硬件故障（低成功率，传感器错误）
    - network_issues: 网络问题（中等成功率，高延迟）
    - partial_degradation: 部分降级（中等成功率，部分错误）
    - high_latency_env: 高延迟环境（高成功率，极高延迟）
    """
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)

        # 验证场景
        if scenario not in MOCK_SCENARIOS:
            raise HTTPException(
                status_code=400,
                detail=f"无效的场景: {scenario}. 可用场景: {list(MOCK_SCENARIOS.keys())}",
            )

        scenario_enum = MOCK_SCENARIOS[scenario]
        session_id = await orchestrator.start_mock_session(
            content_id, user_id, scenario_enum
        )

        return {
            "success": True,
            "session_id": session_id,
            "content_id": content_id,
            "user_id": user_id,
            "scenario": scenario,
            "message": "Mock会话已成功启动",
        }

    except Exception as e:
        logger.error(f"启动Mock会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mock_router.delete("/sessions/{session_id}", summary="停止Mock会话")
async def stop_mock_session(session_id: str, db: Session = Depends(get_db)):
    """停止指定的Mock会话"""
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)
        success = await orchestrator.stop_mock_session(session_id)

        if success:
            return {
                "success": True,
                "session_id": session_id,
                "message": "Mock会话已成功停止",
            }
        else:
            raise HTTPException(status_code=404, detail="会话不存在")

    except Exception as e:
        logger.error(f"停止Mock会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mock_router.get("/sessions/{session_id}/sensor-data", summary="获取传感器数据")
async def get_sensor_data(
    session_id: str,
    sensor_types: List[str] = Query(
        ["accelerometer", "gyroscope"], description="传感器类型列表"
    ),
    count: int = Query(1, ge=1, le=10, description="数据点数量"),
    db: Session = Depends(get_db),
):
    """
    获取模拟的传感器数据流

    支持的传感器类型:
    - accelerometer: 加速度计
    - gyroscope: 陀螺仪
    - gps: GPS定位
    - camera: 摄像头
    """
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)

        # 验证传感器类型
        valid_sensors = {"accelerometer", "gyroscope", "gps", "camera"}
        invalid_sensors = set(sensor_types) - valid_sensors
        if invalid_sensors:
            raise HTTPException(
                status_code=400, detail=f"无效的传感器类型: {invalid_sensors}"
            )

        # 获取多次数据以满足count要求
        all_data = []
        for _ in range(count):
            data_stream = await orchestrator.get_sensor_data_stream(
                session_id, sensor_types
            )
            all_data.extend(data_stream)
            if count > 1:
                await asyncio.sleep(0.1)  # 模拟采样间隔

        return {
            "success": True,
            "session_id": session_id,
            "sensor_types": sensor_types,
            "data_count": len(all_data),
            "data": all_data,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取传感器数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mock_router.post("/sessions/{session_id}/interactions", summary="处理交互请求")
async def handle_interaction(
    session_id: str,
    interaction_type: str = Body(..., description="交互类型"),
    interaction_data: Dict[str, Any] = Body(..., description="交互数据"),
    db: Session = Depends(get_db),
):
    """
    处理AR/VR交互请求

    交互类型:
    - gesture: 手势交互
    - voice: 语音命令
    """
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)

        # 验证交互类型
        valid_interactions = {"gesture", "voice"}
        if interaction_type not in valid_interactions:
            raise HTTPException(
                status_code=400, detail=f"无效的交互类型: {interaction_type}"
            )

        result = await orchestrator.handle_interaction(
            session_id, interaction_type, interaction_data
        )

        return {
            "success": True,
            "session_id": session_id,
            "interaction_type": interaction_type,
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"处理交互失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mock_router.get("/sessions/{session_id}/physics-state", summary="获取物理状态")
async def get_physics_state(session_id: str, db: Session = Depends(get_db)):
    """获取当前物理引擎状态"""
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)
        physics_state = await orchestrator.get_physics_state(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "physics_state": physics_state,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取物理状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mock_router.get("/scenarios", summary="获取可用场景列表")
async def get_scenarios():
    """获取所有可用的Mock场景配置"""
    scenario_info = {}
    for name, scenario in MOCK_SCENARIOS.items():
        scenario_info[name] = {
            "name": scenario.name,
            "description": scenario.value,
            "characteristics": _get_scenario_characteristics(scenario),
        }

    return {"success": True, "scenarios": scenario_info}


def _get_scenario_characteristics(scenario: MockScenario) -> Dict[str, Any]:
    """获取场景特征描述"""
    characteristics = {
        MockScenario.SUCCESSFUL_INTERACTION: {
            "success_rate": "95%",
            "latency": "10-50ms",
            "error_rate": "1%",
            "best_for": "正常开发测试",
        },
        MockScenario.SENSOR_ERROR: {
            "success_rate": "30%",
            "latency": "50-200ms",
            "error_rate": "40%",
            "best_for": "错误处理测试",
        },
        MockScenario.NETWORK_DELAY: {
            "success_rate": "80%",
            "latency": "200-1000ms",
            "error_rate": "5%",
            "best_for": "网络条件测试",
        },
        MockScenario.PARTIAL_FAILURE: {
            "success_rate": "70%",
            "latency": "30-150ms",
            "error_rate": "20%",
            "best_for": "容错机制测试",
        },
        MockScenario.HIGH_LATENCY: {
            "success_rate": "90%",
            "latency": "500-2000ms",
            "error_rate": "2%",
            "best_for": "性能优化测试",
        },
    }
    return characteristics.get(scenario, {})


@mock_router.get("/sessions", summary="获取活跃会话列表")
async def get_active_sessions(db: Session = Depends(get_db)):
    """获取所有活跃的Mock会话"""
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)

        sessions_info = []
        for session_id, session_data in orchestrator.active_sessions.items():
            sessions_info.append(
                {
                    "session_id": session_id,
                    "content_id": session_data["content_id"],
                    "user_id": session_data["user_id"],
                    "scenario": session_data["scenario"].value,
                    "started_at": session_data["started_at"].isoformat(),
                    "last_activity": session_data["last_activity"].isoformat(),
                    "duration_seconds": (
                        datetime.utcnow() - session_data["started_at"]
                    ).total_seconds(),
                }
            )

        return {
            "success": True,
            "active_sessions": sessions_info,
            "total_count": len(sessions_info),
        }

    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@mock_router.post("/maintenance/cleanup", summary="清理超时会话")
async def cleanup_sessions(
    timeout_minutes: int = Body(30, ge=1, le=1440, description="超时时间（分钟）"),
    db: Session = Depends(get_db),
):
    """清理超时的Mock会话"""
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)
        await orchestrator.cleanup_inactive_sessions(timeout_minutes)

        return {
            "success": True,
            "message": f"已清理 {timeout_minutes} 分钟内无活动的会话",
        }

    except Exception as e:
        logger.error(f"清理会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


import json

# WebSocket端点用于实时数据流
from fastapi import WebSocket


@mock_router.websocket("/sessions/{session_id}/ws/sensor-stream")
async def sensor_data_websocket(
    websocket: WebSocket,
    session_id: str,
    sensor_types: str = "accelerometer,gyroscope",
    db: Session = Depends(get_db),
):
    """
    WebSocket实时传感器数据流

    参数:
    - sensor_types: 逗号分隔的传感器类型列表
    """
    await websocket.accept()

    try:
        orchestrator = await get_mock_orchestrator_dependency(db)

        if session_id not in orchestrator.active_sessions:
            await websocket.send_text(
                json.dumps({"error": "会话不存在", "code": "SESSION_NOT_FOUND"})
            )
            await websocket.close()
            return

        # 解析传感器类型
        sensor_list = [s.strip() for s in sensor_types.split(",")]

        # 发送连接确认
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "session_id": session_id,
                    "sensor_types": sensor_list,
                }
            )
        )

        # 实时数据流循环
        while True:
            try:
                # 获取传感器数据
                data_stream = await orchestrator.get_sensor_data_stream(
                    session_id, sensor_list
                )

                # 发送到客户端
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "sensor_data",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": data_stream,
                        }
                    )
                )

                # 等待下次采样
                await asyncio.sleep(0.1)  # 10Hz采样率

            except Exception as e:
                logger.error(f"WebSocket数据传输错误: {e}")
                await websocket.send_text(
                    json.dumps({"error": str(e), "code": "DATA_TRANSMISSION_ERROR"})
                )
                break

    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        await websocket.close()


# 健康检查端点
@mock_router.get("/health", summary="Mock服务健康检查")
async def health_check():
    """检查Mock服务健康状态"""
    return {
        "status": "healthy",
        "service": "arvr-mock-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


# 性能测试端点
@mock_router.get("/performance/benchmark", summary="性能基准测试")
async def performance_benchmark(
    iterations: int = Query(100, ge=1, le=1000, description="测试迭代次数"),
    db: Session = Depends(get_db),
):
    """运行性能基准测试"""
    try:
        orchestrator = await get_mock_orchestrator_dependency(db)

        # 启动测试会话
        test_session_id = await orchestrator.start_mock_session(
            1, 1, MockScenario.SUCCESSFUL_INTERACTION
        )

        import time

        start_time = time.time()

        # 执行基准测试
        results = []
        for i in range(iterations):
            iteration_start = time.time()

            # 传感器数据获取测试
            sensor_data = await orchestrator.get_sensor_data_stream(
                test_session_id, ["accelerometer", "gyroscope"]
            )

            # 交互处理测试
            interaction_result = await orchestrator.handle_interaction(
                test_session_id, "gesture", {"type": "tap", "position": [0, 0, 0]}
            )

            iteration_time = time.time() - iteration_start
            results.append(
                {
                    "iteration": i + 1,
                    "sensor_data_points": len(sensor_data),
                    "interaction_success": interaction_result["success"],
                    "processing_time_ms": round(iteration_time * 1000, 2),
                }
            )

        total_time = time.time() - start_time
        avg_time = total_time / iterations

        # 清理测试会话
        await orchestrator.stop_mock_session(test_session_id)

        return {
            "success": True,
            "benchmark_results": {
                "total_iterations": iterations,
                "total_time_seconds": round(total_time, 3),
                "average_time_per_iteration_ms": round(avg_time * 1000, 2),
                "throughput_ops_per_second": round(iterations / total_time, 2),
                "detailed_results": results,
            },
        }

    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
