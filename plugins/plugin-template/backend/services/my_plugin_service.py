"""
我的插件 - 服务层

这是一个示例服务文件，展示如何创建插件的业务逻辑。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MyPluginService:
    """
    我的插件服务
    
    负责插件的核心业务逻辑。
    """
    
    def __init__(self):
        """初始化服务"""
        self.config = {}
        self.data_store = {}
        logger.info("MyPluginService 初始化完成")
    
    async def start(self):
        """
        启动服务
        
        如果 manifest 中设置 autoStart: true，此方法会自动调用。
        """
        logger.info("MyPluginService 启动")
        # 初始化资源
        self.data_store = {
            "items": [],
            "settings": {}
        }
    
    async def stop(self):
        """
        停止服务
        
        在插件卸载或禁用时调用。
        """
        logger.info("MyPluginService 停止")
        # 清理资源
        self.data_store.clear()
    
    def process_data(self, name: str, value: Optional[str] = None) -> Dict[str, Any]:
        """
        处理数据
        
        Args:
            name: 数据名称
            value: 数据值
        
        Returns:
            Dict[str, Any]: 处理结果
        """
        logger.info(f"处理数据: name={name}, value={value}")
        
        # 业务逻辑
        result = {
            "name": name,
            "value": value,
            "processed": True,
            "timestamp": "2026-06-06T12:00:00Z"
        }
        
        # 存储数据
        self.data_store.setdefault("items", []).append(result)
        
        return result
    
    def get_items(self, limit: int = 10, offset: int = 0) -> list:
        """
        获取项目列表
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            list: 项目列表
        """
        items = self.data_store.get("items", [])
        return items[offset:offset + limit]
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config: 新配置
        
        Returns:
            bool: 是否成功
        """
        try:
            self.config.update(config)
            logger.info(f"配置已更新: {config}")
            return True
        except Exception as err:
            logger.error(f"更新配置失败: {err}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置
        
        Returns:
            Dict[str, Any]: 当前配置
        """
        return self.config.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计数据
        """
        return {
            "total_items": len(self.data_store.get("items", [])),
            "config_keys": len(self.config),
            "status": "running"
        }
