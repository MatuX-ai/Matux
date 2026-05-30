"""
Admin 后台全局设置 Pydantic 模型定义

提供所有配置项的数据验证和序列化模型
对应前端 TypeScript 接口：src/app/admin/shared/models/api-settings.models.ts
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, validator


# ==================== 配置项模型 ====================


class OpenHydraConfig(BaseModel):
    """OpenHydra 服务配置"""
    
    apiUrl: str = Field(..., description="API 基础 URL")
    apiKey: str = Field(default="", description="API 密钥")
    enabled: bool = Field(default=False, description="是否启用")
    timeout: Optional[int] = Field(default=5000, description="超时时间 (毫秒)")
    notes: Optional[str] = Field(default="", description="备注说明")
    
    class Config:
        json_schema_extra = {
            "example": {
                "apiUrl": "http://localhost:8080",
                "apiKey": "openhydra-test-key",
                "enabled": True,
                "timeout": 5000,
                "notes": "OpenHydra 开发环境"
            }
        }


class JupyterHubConfig(BaseModel):
    """JupyterHub 服务配置"""
    
    url: str = Field(..., description="JupyterHub URL")
    apiToken: Optional[str] = Field(default="", description="API Token")
    enabled: bool = Field(default=False, description="是否启用")
    defaultRole: Optional[Literal["user", "admin", "instructor"]] = Field(
        default="user", 
        description="默认用户角色"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "http://localhost:8000",
                "apiToken": "jupyter-test-token",
                "enabled": True,
                "defaultRole": "user"
            }
        }


class DatabaseConnectionConfig(BaseModel):
    """数据库连接配置"""
    
    name: str = Field(..., description="连接名称")
    host: str = Field(..., description="主机地址")
    port: int = Field(..., ge=1, le=65535, description="端口")
    database: str = Field(..., description="数据库名称")
    username: str = Field(..., description="用户名")
    password: Optional[str] = Field(default="", description="密码 (加密存储)")
    ssl: Optional[bool] = Field(default=False, description="SSL 连接")
    poolSize: Optional[int] = Field(default=10, ge=1, le=100, description="连接池大小")
    enabled: bool = Field(default=False, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


class MqttConfig(BaseModel):
    """MQTT 消息服务配置"""
    
    brokerUrl: str = Field(..., description="Broker 地址")
    port: int = Field(default=1883, ge=1, le=65535, description="端口")
    username: Optional[str] = Field(default="", description="用户名")
    password: Optional[str] = Field(default="", description="密码")
    tlsEnabled: Optional[bool] = Field(default=False, description="是否启用 TLS")
    qos: Optional[int] = Field(default=1, ge=0, le=2, description="QoS 级别")
    enabled: bool = Field(default=False, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brokerUrl": "tcp://localhost",
                "port": 1883,
                "username": "mqtt_user",
                "password": "***",
                "tlsEnabled": False,
                "qos": 1,
                "enabled": False
            }
        }


class PrometheusConfig(BaseModel):
    """Prometheus 监控配置"""
    
    serverUrl: str = Field(..., description="Prometheus Server URL")
    metricsEndpoint: str = Field(default="/metrics", description="Metrics 端点")
    scrapeInterval: Optional[int] = Field(default=15, ge=5, le=3600, description="采集间隔 (秒)")
    enabled: bool = Field(default=False, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "serverUrl": "http://localhost:9090",
                "metricsEndpoint": "/metrics",
                "scrapeInterval": 15,
                "enabled": False
            }
        }


class CeleryConfig(BaseModel):
    """Celery 任务队列配置"""
    
    brokerUrl: str = Field(..., description="Broker URL (Redis/RabbitMQ)")
    resultBackendUrl: Optional[str] = Field(default="", description="Result Backend URL")
    defaultQueue: Optional[str] = Field(default="default", description="默认队列名称")
    workerCount: Optional[int] = Field(default=4, ge=1, le=32, description="Worker 数量")
    enabled: bool = Field(default=False, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brokerUrl": "redis://localhost:6379/0",
                "resultBackendUrl": "redis://localhost:6379/0",
                "defaultQueue": "default",
                "workerCount": 4,
                "enabled": True
            }
        }


class ObjectStorageConfig(BaseModel):
    """对象存储配置 (S3 兼容)"""
    
    provider: Literal["aws-s3", "aliyun-oss", "tencent-cos", "minio"] = Field(
        default="minio", 
        description="服务提供商"
    )
    accessKey: str = Field(..., description="Access Key")
    secretKey: str = Field(..., description="Secret Key")
    bucket: str = Field(..., description="Bucket 名称")
    region: Optional[str] = Field(default="", description="区域")
    endpoint: Optional[str] = Field(default="", description="端点 URL")
    enabled: bool = Field(default=False, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "minio",
                "accessKey": "minioadmin",
                "secretKey": "***",
                "bucket": "imato-storage",
                "region": "us-east-1",
                "endpoint": "http://localhost:9000",
                "enabled": False
            }
        }


class AiServiceConfig(BaseModel):
    """AI 服务配置 (通用)"""
    
    serviceName: str = Field(..., description="服务名称")
    endpoint: str = Field(..., description="API 端点")
    apiKey: str = Field(..., description="API 密钥")
    model: Optional[str] = Field(default="", description="模型名称")
    maxTokens: Optional[int] = Field(default=2048, ge=1, le=128000, description="最大 Token 数")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    enabled: bool = Field(default=False, description="是否启用")
    
    class Config:
        json_schema_extra = {
            "example": {
                "serviceName": "DeepSeek",
                "endpoint": "https://api.deepseek.com/v1",
                "apiKey": "sk-***",
                "model": "deepseek-chat",
                "maxTokens": 4096,
                "temperature": 0.7,
                "enabled": False
            }
        }


# ==================== 全局设置汇总模型 ====================


class GlobalApiSettings(BaseModel):
    """全局 API 设置汇总"""
    
    openHydra: Optional[OpenHydraConfig] = Field(default=None, description="OpenHydra 集成配置")
    jupyterHub: Optional[JupyterHubConfig] = Field(default=None, description="JupyterHub 配置")
    databases: Optional[List[DatabaseConnectionConfig]] = Field(
        default=[], 
        description="数据库连接列表"
    )
    mqtt: Optional[MqttConfig] = Field(default=None, description="MQTT 配置")
    prometheus: Optional[PrometheusConfig] = Field(default=None, description="Prometheus 监控配置")
    celery: Optional[CeleryConfig] = Field(default=None, description="Celery 任务队列配置")
    objectStorage: Optional[ObjectStorageConfig] = Field(
        default=None, 
        description="对象存储配置"
    )
    aiServices: Optional[List[AiServiceConfig]] = Field(
        default=[], 
        description="AI 服务配置列表"
    )
    lastUpdated: Optional[str] = Field(default=None, description="最后更新时间")
    updatedBy: Optional[str] = Field(default=None, description="更新者")
    
    class Config:
        json_schema_extra = {
            "example": {
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
        }


# ==================== API 请求/响应模型 ====================


class ApiSettingsResponse(BaseModel):
    """API 设置保存响应"""
    
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(default=None, description="消息")
    data: Optional[GlobalApiSettings] = Field(default=None, description="设置数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "设置已保存",
                "data": {},
                "error": None
            }
        }


class TestConnectionRequest(BaseModel):
    """测试连接请求基类"""
    
    serviceType: str = Field(..., description="服务类型")
    config: dict = Field(..., description="配置对象")


class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    responseTime: Optional[int] = Field(default=None, description="响应时间 (毫秒)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "连接成功",
                "responseTime": 150
            }
        }
