"""
我的插件 - 卸载钩子

在插件卸载前执行。
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def main():
    """
    卸载钩子主函数
    
    环境变量:
        PLUGIN_ID: 插件 ID
        PLUGIN_VERSION: 插件版本
        PLUGIN_DIR: 插件安装目录
        DATA_DIR: 插件数据目录
        KEEP_DATA: 是否保留数据 (true/false)
        PLATFORM: 操作系统平台
        ARCH: 系统架构
    """
    try:
        # 获取环境变量
        plugin_id = os.environ.get('PLUGIN_ID', 'unknown')
        plugin_version = os.environ.get('PLUGIN_VERSION', '0.0.0')
        plugin_dir = Path(os.environ.get('PLUGIN_DIR', '.'))
        data_dir = Path(os.environ.get('DATA_DIR', '.'))
        keep_data = os.environ.get('KEEP_DATA', 'false').lower() == 'true'
        platform = os.environ.get('PLATFORM', 'unknown')
        arch = os.environ.get('ARCH', 'unknown')
        
        logger.info(f"开始卸载插件: {plugin_id} v{plugin_version}")
        logger.info(f"保留数据: {keep_data}")
        
        # 1. 停止服务（如果有）
        logger.info("停止插件服务...")
        # 清理资源
        
        # 2. 清理缓存
        cache_dir = data_dir / 'cache'
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
            logger.info("✓ 缓存已清理")
        
        # 3. 根据用户选择处理数据
        if not keep_data:
            logger.info("清理插件数据...")
            
            # 删除配置文件
            config_dir = data_dir / 'config'
            if config_dir.exists():
                shutil.rmtree(config_dir, ignore_errors=True)
                logger.info("✓ 配置已清理")
            
            # 删除日志文件
            logs_dir = data_dir / 'logs'
            if logs_dir.exists():
                shutil.rmtree(logs_dir, ignore_errors=True)
                logger.info("✓ 日志已清理")
            
            # 删除数据目录
            if data_dir.exists():
                shutil.rmtree(data_dir, ignore_errors=True)
                logger.info("✓ 数据目录已清理")
        else:
            logger.info("保留插件数据")
            
            # 创建卸载标记
            uninstall_marker = data_dir / '.uninstalled'
            with open(uninstall_marker, 'w', encoding='utf-8') as f:
                json.dump({
                    "plugin_id": plugin_id,
                    "version": plugin_version,
                    "uninstalled_at": "2026-06-06T12:00:00Z",
                    "keep_data": True
                }, f, indent=2, ensure_ascii=False)
            
            logger.info("✓ 卸载标记已创建")
        
        # 4. 执行平台特定清理
        if platform == 'win32':
            logger.info("执行 Windows 特定清理...")
            # Windows 特定操作
        elif platform == 'darwin':
            logger.info("执行 macOS 特定清理...")
            # macOS 特定操作
        elif platform == 'linux':
            logger.info("执行 Linux 特定清理...")
            # Linux 特定操作
        
        logger.info(f"✓ 插件 {plugin_id} 卸载完成")
        return 0
        
    except Exception as err:
        logger.error(f"✗ 卸载失败: {err}")
        # 卸载失败不阻塞，继续卸载流程
        return 0


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 执行卸载钩子
    exit_code = main()
    sys.exit(exit_code)
