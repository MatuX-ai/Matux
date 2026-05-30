"""
Admin 后台全局设置 API 路由

提供全局配置的增删改查和测试连接功能
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, status

from models.admin_settings_models import (
    AiServiceConfig,
    ApiSettingsResponse,
    CeleryConfig,
    DatabaseConnectionConfig,
    GlobalApiSettings,
    JupyterHubConfig,
    MqttConfig,
    ObjectStorageConfig,
    OpenHydraConfig,
    PrometheusConfig,
    TestConnectionResponse,
)
from services.admin_settings_service import admin_settings_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/settings",
    tags=["Admin 设置管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"},
    },
)


@router.get(
    "",
    response_model=ApiSettingsResponse,
    summary="获取全局设置",
    description="获取所有 Admin 后台的全局 API 配置",
)
async def get_global_settings() -> ApiSettingsResponse:
    """
    获取全局设置
    
    返回所有已保存的配置项，包括：
    - OpenHydra 集成配置
    - JupyterHub 配置
    - 数据库连接列表
    - MQTT 配置
    - Prometheus 监控配置
    - Celery 任务队列配置
    - 对象存储配置
    - AI 服务配置列表
    """
    try:
        settings = await admin_settings_service.get_settings()
        
        return ApiSettingsResponse(
            success=True,
            message="设置加载成功",
            data=settings,
            error=None
        )
    except Exception as e:
        logger.error(f"获取全局设置失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设置失败：{str(e)}"
        )


@router.post(
    "",
    response_model=ApiSettingsResponse,
    summary="保存全局设置",
    description="保存或更新 Admin 后台的全局 API 配置",
)
async def save_global_settings(
    settings: GlobalApiSettings = Body(
        ...,
        description="全局设置对象",
        example={
            "openHydra": {
                "apiUrl": "http://localhost:8080",
                "apiKey": "openhydra-test-key",
                "enabled": True
            },
            "jupyterHub": {
                "url": "http://localhost:8000",
                "apiToken": "jupyter-test-token",
                "enabled": True
            },
            "databases": [
                {
                    "name": "主数据库",
                    "host": "localhost",
                    "port": 5432,
                    "database": "imato_main",
                    "username": "postgres",
                    "password": "***",
                    "ssl": False,
                    "poolSize": 10,
                    "enabled": True
                }
            ],
            "aiServices": [
                {
                    "serviceName": "DeepSeek",
                    "endpoint": "https://api.deepseek.com/v1",
                    "apiKey": "sk-***",
                    "model": "deepseek-chat",
                    "maxTokens": 4096,
                    "temperature": 0.7,
                    "enabled": False
                }
            ]
        }
    )
) -> ApiSettingsResponse:
    """
    保存全局设置
    
    接收一个完整的全局设置对象并保存到存储中。
    支持增量更新，未提供的字段将保持原值。
    """
    try:
        # 保存设置
        success = await admin_settings_service.save_settings(settings)
        
        if success:
            return ApiSettingsResponse(
                success=True,
                message="设置已保存",
                data=settings,
                error=None
            )
        else:
            return ApiSettingsResponse(
                success=False,
                message="保存失败",
                data=None,
                error="保存设置失败"
            )
            
    except Exception as e:
        logger.error(f"保存全局设置失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存设置失败：{str(e)}"
        )


@router.post(
    "/test-openhydra",
    response_model=TestConnectionResponse,
    summary="测试 OpenHydra 连接",
    description="测试 OpenHydra API 连接是否可用",
)
async def test_openhydra(
    config: OpenHydraConfig = Body(
        ...,
        description="OpenHydra 配置",
        example={
            "apiUrl": "http://localhost:8080",
            "apiKey": "openhydra-test-key",
            "enabled": True,
            "timeout": 5000
        }
    )
) -> TestConnectionResponse:
    """测试 OpenHydra 连接"""
    try:
        result = await admin_settings_service.test_openhydra_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试 OpenHydra 连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-jupyterhub",
    response_model=TestConnectionResponse,
    summary="测试 JupyterHub 连接",
    description="测试 JupyterHub API 连接是否可用",
)
async def test_jupyterhub(
    config: JupyterHubConfig = Body(
        ...,
        description="JupyterHub 配置",
        example={
            "url": "http://localhost:8000",
            "apiToken": "jupyter-test-token",
            "enabled": True
        }
    )
) -> TestConnectionResponse:
    """测试 JupyterHub 连接"""
    try:
        result = await admin_settings_service.test_jupyterhub_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试 JupyterHub 连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-database",
    response_model=TestConnectionResponse,
    summary="测试数据库连接",
    description="测试数据库连接是否可用（支持 PostgreSQL）",
)
async def test_database(
    config: DatabaseConnectionConfig = Body(
        ...,
        description="数据库配置",
        example={
            "name": "主数据库",
            "host": "localhost",
            "port": 5432,
            "database": "imato_main",
            "username": "postgres",
            "password": "***",
            "ssl": False,
            "poolSize": 10,
            "enabled": True
        }
    )
) -> TestConnectionResponse:
    """测试数据库连接"""
    try:
        result = await admin_settings_service.test_database_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试数据库连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-mqtt",
    response_model=TestConnectionResponse,
    summary="测试 MQTT 连接",
    description="测试 MQTT Broker 连接是否可用",
)
async def test_mqtt(
    config: MqttConfig = Body(
        ...,
        description="MQTT 配置",
        example={
            "brokerUrl": "tcp://localhost",
            "port": 1883,
            "username": "mqtt_user",
            "password": "***",
            "tlsEnabled": False,
            "qos": 1,
            "enabled": False
        }
    )
) -> TestConnectionResponse:
    """测试 MQTT 连接"""
    try:
        result = await admin_settings_service.test_mqtt_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试 MQTT 连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-ai-service",
    response_model=TestConnectionResponse,
    summary="测试 AI 服务连接",
    description="测试 AI 服务 API 连接是否可用（支持 OpenAI、DeepSeek、Kimi 等）",
)
async def test_ai_service(
    config: AiServiceConfig = Body(
        ...,
        description="AI 服务配置",
        example={
            "serviceName": "DeepSeek",
            "endpoint": "https://api.deepseek.com/v1",
            "apiKey": "sk-***",
            "model": "deepseek-chat",
            "maxTokens": 4096,
            "temperature": 0.7,
            "enabled": False
        }
    )
) -> TestConnectionResponse:
    """测试 AI 服务连接"""
    try:
        result = await admin_settings_service.test_ai_service_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试 AI 服务连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-prometheus",
    response_model=TestConnectionResponse,
    summary="测试 Prometheus 连接",
    description="测试 Prometheus 监控服务连接是否可用",
)
async def test_prometheus(
    config: PrometheusConfig = Body(
        ...,
        description="Prometheus 配置",
        example={
            "serverUrl": "http://localhost:9090",
            "metricsEndpoint": "/metrics",
            "scrapeInterval": 15,
            "enabled": False
        }
    )
) -> TestConnectionResponse:
    """测试 Prometheus 连接"""
    try:
        result = await admin_settings_service.test_prometheus_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试 Prometheus 连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-object-storage",
    response_model=TestConnectionResponse,
    summary="测试对象存储连接",
    description="测试对象存储服务连接是否可用（支持 S3、MinIO 等）",
)
async def test_object_storage(
    config: ObjectStorageConfig = Body(
        ...,
        description="对象存储配置",
        example={
            "provider": "minio",
            "accessKey": "minioadmin",
            "secretKey": "***",
            "bucket": "imato-storage",
            "region": "us-east-1",
            "endpoint": "http://localhost:9000",
            "enabled": False
        }
    )
) -> TestConnectionResponse:
    """测试对象存储连接"""
    try:
        result = await admin_settings_service.test_object_storage_connection(config)
        return TestConnectionResponse(**result)
    except Exception as e:
        logger.error(f"测试对象存储连接失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试连接失败：{str(e)}"
        )


@router.post(
    "/test-celery",
    response_model=TestConnectionResponse,
    summary="测试 Celery 连接",
    description="测试 Celery 任务队列连接是否可用",
)
async def test_celery(
    config: CeleryConfig = Body(
        ...,
        description="Celery 配置",
        example={
            "brokerUrl": "redis://localhost:6379/0",
            "resultBackendUrl": "redis://localhost:6379/0",
            "defaultQueue": "default",
            "workerCount": 4,
            "enabled": True
        }
    )
) -> TestConnectionResponse:
    """测试 Celery 连接"""
    try:
        # TODO: 实现 Celery 连接测试
        # 需要检查 Redis 或 RabbitMQ 连接
        
        if not config.enabled:
            return TestConnectionResponse(
                success=False,
                message="Celery 服务未启用",
                responseTime=0
            )
        
        # 简单测试：检查 Broker URL 是否可达
        import asyncio
        import time
        from urllib.parse import urlparse
        
        start_time = time.time()
        
        # 解析 Broker URL
        parsed = urlparse(config.brokerUrl)
        
        if parsed.scheme == "redis":
            # Redis Broker
            try:
                import redis
                
                redis_client = redis.Redis(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 6379,
                    password=parsed.password,
                    db=int(parsed.path.strip('/') or 0),
                    socket_timeout=5
                )
                
                # Ping 测试
                if redis_client.ping():
                    response_time = int((time.time() - start_time) * 1000)
                    return TestConnectionResponse(
                        success=True,
                        message="Celery Redis Broker 连接成功",
                        responseTime=response_time
                    )
                    
            except ImportError:
                return TestConnectionResponse(
                    success=False,
                    message="未安装 redis 库",
                    responseTime=int((time.time() - start_time) * 1000)
                )
            except Exception as e:
                return TestConnectionResponse(
                    success=False,
                    message=f"Celery Redis Broker 连接失败：{str(e)}",
                    responseTime=int((time.time() - start_time) * 1000)
                )
        else:
            return TestConnectionResponse(
                success=False,
                message=f"暂不支持的 Broker 类型：{parsed.scheme}",
                responseTime=int((time.time() - start_time) * 1000)
            )
            
    except Exception as e:
        logger.error(f"测试 Celery 连接失败：{e}")
        return TestConnectionResponse(
            success=False,
            message=f"测试连接失败：{str(e)}",
            responseTime=0
        )
