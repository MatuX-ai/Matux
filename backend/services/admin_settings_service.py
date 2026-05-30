"""
Admin 后台全局设置管理服务

提供配置的 CRUD 操作、验证和测试连接功能
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

from models.admin_settings_models import (
    AiServiceConfig,
    CeleryConfig,
    DatabaseConnectionConfig,
    GlobalApiSettings,
    JupyterHubConfig,
    MqttConfig,
    ObjectStorageConfig,
    OpenHydraConfig,
    PrometheusConfig,
)

logger = logging.getLogger(__name__)


class AdminSettingsService:
    """Admin 设置管理服务"""
    
    # 配置文件存储路径（使用 JSON 文件作为快速实现方案）
    SETTINGS_FILE_PATH = Path("backend/data/admin_settings.json")
    
    def __init__(self):
        """初始化服务"""
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """确保数据目录存在"""
        self.SETTINGS_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async def get_settings(self) -> GlobalApiSettings:
        """
        获取全局设置
        
        Returns:
            GlobalApiSettings: 全局设置对象
        """
        try:
            if not self.SETTINGS_FILE_PATH.exists():
                logger.info("设置文件不存在，返回空配置")
                return GlobalApiSettings()
            
            with open(self.SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换为 Pydantic 模型
            settings = GlobalApiSettings(**data)
            logger.info("成功加载设置")
            return settings
            
        except Exception as e:
            logger.error(f"加载设置失败：{e}")
            return GlobalApiSettings()
    
    async def save_settings(self, settings: GlobalApiSettings) -> bool:
        """
        保存全局设置
        
        Args:
            settings: 要保存的设置对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 转换为字典
            settings_dict = settings.model_dump(exclude_none=True)
            
            # 保存到文件
            with open(self.SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, ensure_ascii=False, indent=2)
            
            logger.info("设置已保存")
            return True
            
        except Exception as e:
            logger.error(f"保存设置失败：{e}")
            return False
    
    async def test_openhydra_connection(
        self, 
        config: OpenHydraConfig
    ) -> Dict[str, Any]:
        """
        测试 OpenHydra 连接
        
        Args:
            config: OpenHydra 配置
            
        Returns:
            Dict: 测试结果 {success: bool, message: str, responseTime: int}
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "OpenHydra 服务未启用",
                    "responseTime": 0
                }
            
            async with aiohttp.ClientSession() as session:
                health_url = f"{config.apiUrl}/health"
                headers = {}
                
                if config.apiKey:
                    headers["Authorization"] = f"Bearer {config.apiKey}"
                
                async with session.get(health_url, headers=headers, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "OpenHydra 连接成功",
                            "responseTime": response_time
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"OpenHydra 连接失败：HTTP {response.status}",
                            "responseTime": response_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": "OpenHydra 连接超时",
                "responseTime": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"测试 OpenHydra 连接失败：{e}")
            return {
                "success": False,
                "message": f"OpenHydra 连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def test_jupyterhub_connection(
        self,
        config: JupyterHubConfig
    ) -> Dict[str, Any]:
        """
        测试 JupyterHub 连接
        
        Args:
            config: JupyterHub 配置
            
        Returns:
            Dict: 测试结果
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "JupyterHub 服务未启用",
                    "responseTime": 0
                }
            
            async with aiohttp.ClientSession() as session:
                api_url = f"{config.url}/hub/api"
                headers = {}
                
                if config.apiToken:
                    headers["Authorization"] = f"token {config.apiToken}"
                
                async with session.get(api_url, headers=headers, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "JupyterHub 连接成功",
                            "responseTime": response_time
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"JupyterHub 连接失败：HTTP {response.status}",
                            "responseTime": response_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": "JupyterHub 连接超时",
                "responseTime": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"测试 JupyterHub 连接失败：{e}")
            return {
                "success": False,
                "message": f"JupyterHub 连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def test_database_connection(
        self,
        config: DatabaseConnectionConfig
    ) -> Dict[str, Any]:
        """
        测试数据库连接
        
        Args:
            config: 数据库配置
            
        Returns:
            Dict: 测试结果
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "数据库连接未启用",
                    "responseTime": 0
                }
            
            # 尝试导入异步 PostgreSQL 驱动
            try:
                import asyncpg
                
                # 构建连接字符串
                ssl_mode = "require" if config.ssl else "prefer"
                connection_url = (
                    f"postgresql://{config.username}:{config.password}"
                    f"@{config.host}:{config.port}/{config.database}"
                    f"?ssl={ssl_mode}"
                )
                
                # 尝试连接
                conn = await asyncpg.connect(connection_url, timeout=10)
                await conn.close()
                
                response_time = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "message": "数据库连接成功",
                    "responseTime": response_time
                }
                
            except ImportError:
                # 如果没有安装 asyncpg，使用同步方式（需要 psycopg2）
                logger.warning("asyncpg 未安装，尝试使用同步方式测试")
                return await self._test_database_sync(config, start_time)
                
        except Exception as e:
            logger.error(f"测试数据库连接失败：{e}")
            return {
                "success": False,
                "message": f"数据库连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def _test_database_sync(
        self,
        config: DatabaseConnectionConfig,
        start_time: float
    ) -> Dict[str, Any]:
        """
        使用同步方式测试数据库连接（备用方案）
        
        Args:
            config: 数据库配置
            start_time: 开始时间
            
        Returns:
            Dict: 测试结果
        """
        try:
            import psycopg2
            
            # 建立连接
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password,
                sslmode="require" if config.ssl else "prefer",
                connect_timeout=10
            )
            conn.close()
            
            response_time = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "message": "数据库连接成功",
                "responseTime": response_time
            }
            
        except ImportError:
            return {
                "success": False,
                "message": "未安装数据库驱动（asyncpg 或 psycopg2）",
                "responseTime": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"数据库连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def test_mqtt_connection(
        self,
        config: MqttConfig
    ) -> Dict[str, Any]:
        """
        测试 MQTT 连接
        
        Args:
            config: MQTT 配置
            
        Returns:
            Dict: 测试结果
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "MQTT 服务未启用",
                    "responseTime": 0
                }
            
            # 尝试导入 paho-mqtt
            try:
                import paho.mqtt.client as mqtt
                
                client_id = f"imato_test_{int(time.time())}"
                client = mqtt.Client(client_id=client_id)
                
                # 配置认证
                if config.username and config.password:
                    client.username_pw_set(config.username, config.password)
                
                # 配置 TLS
                if config.tlsEnabled:
                    client.tls_set()
                
                # 尝试连接
                result = client.connect(
                    host=config.brokerUrl.replace("tcp://", "").replace("ssl://", ""),
                    port=config.port,
                    keepalive=5
                )
                
                # 等待连接结果（最多 5 秒）
                for _ in range(50):  # 5 秒超时
                    client.loop(timeout=0.1)
                    if result == 0:  # MQTT_ERR_SUCCESS
                        client.disconnect()
                        response_time = int((time.time() - start_time) * 1000)
                        return {
                            "success": True,
                            "message": "MQTT 连接成功",
                            "responseTime": response_time
                        }
                
                client.disconnect()
                response_time = int((time.time() - start_time) * 1000)
                return {
                    "success": False,
                    "message": f"MQTT 连接失败：错误码 {result}",
                    "responseTime": response_time
                }
                
            except ImportError:
                return {
                    "success": False,
                    "message": "未安装 paho-mqtt 库",
                    "responseTime": int((time.time() - start_time) * 1000)
                }
                
        except Exception as e:
            logger.error(f"测试 MQTT 连接失败：{e}")
            return {
                "success": False,
                "message": f"MQTT 连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def test_ai_service_connection(
        self,
        config: AiServiceConfig
    ) -> Dict[str, Any]:
        """
        测试 AI 服务连接
        
        Args:
            config: AI 服务配置
            
        Returns:
            Dict: 测试结果
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "AI 服务未启用",
                    "responseTime": 0
                }
            
            async with aiohttp.ClientSession() as session:
                # 构建测试请求
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.apiKey}"
                }
                
                # 不同的 API 端点可能需要不同的测试方式
                # 这里使用通用的方式测试
                test_url = config.endpoint.rstrip('/')
                
                # 尝试调用 models 端点或健康检查
                if 'openai' in test_url.lower():
                    test_url += "/models"
                elif 'deepseek' in test_url.lower():
                    test_url += "/models"
                else:
                    # 通用健康检查
                    test_url += "/health"
                
                async with session.get(test_url, headers=headers, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status in [200, 404]:  # 404 也表示服务可用（只是没有该端点）
                        return {
                            "success": True,
                            "message": f"AI 服务 ({config.serviceName}) 可达",
                            "responseTime": response_time
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"AI 服务连接失败：HTTP {response.status}",
                            "responseTime": response_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": "AI 服务连接超时",
                "responseTime": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"测试 AI 服务连接失败：{e}")
            return {
                "success": False,
                "message": f"AI 服务连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def test_prometheus_connection(
        self,
        config: PrometheusConfig
    ) -> Dict[str, Any]:
        """
        测试 Prometheus 连接
        
        Args:
            config: Prometheus 配置
            
        Returns:
            Dict: 测试结果
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "Prometheus 服务未启用",
                    "responseTime": 0
                }
            
            async with aiohttp.ClientSession() as session:
                metrics_url = f"{config.serverUrl}{config.metricsEndpoint}"
                
                async with session.get(metrics_url, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "Prometheus 连接成功",
                            "responseTime": response_time
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Prometheus 连接失败：HTTP {response.status}",
                            "responseTime": response_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": "Prometheus 连接超时",
                "responseTime": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"测试 Prometheus 连接失败：{e}")
            return {
                "success": False,
                "message": f"Prometheus 连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }
    
    async def test_object_storage_connection(
        self,
        config: ObjectStorageConfig
    ) -> Dict[str, Any]:
        """
        测试对象存储连接
        
        Args:
            config: 对象存储配置
            
        Returns:
            Dict: 测试结果
        """
        start_time = time.time()
        
        try:
            if not config.enabled:
                return {
                    "success": False,
                    "message": "对象存储服务未启用",
                    "responseTime": 0
                }
            
            # 使用 boto3 或 aiohttp 测试 S3 兼容存储
            # 这里简化实现，实际项目中建议使用 boto3
            
            async with aiohttp.ClientSession() as session:
                # 尝试访问 bucket
                test_url = config.endpoint or f"https://{config.bucket}.s3.amazonaws.com"
                
                async with session.head(test_url, timeout=10) as response:
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # 200 表示公开可读，403 表示需要认证（也表示服务可用）
                    if response.status in [200, 403]:
                        return {
                            "success": True,
                            "message": "对象存储服务可达",
                            "responseTime": response_time
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"对象存储连接失败：HTTP {response.status}",
                            "responseTime": response_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "message": "对象存储连接超时",
                "responseTime": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"测试对象存储连接失败：{e}")
            return {
                "success": False,
                "message": f"对象存储连接失败：{str(e)}",
                "responseTime": int((time.time() - start_time) * 1000)
            }


# 创建全局服务实例
admin_settings_service = AdminSettingsService()
