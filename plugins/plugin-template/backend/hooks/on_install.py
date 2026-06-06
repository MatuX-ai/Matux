"""
我的插件 - 安装钩子

在插件安装完成后执行。
"""

import os
import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def main():
    """
    安装钩子主函数
    
    环境变量:
        PLUGIN_ID: 插件 ID
        PLUGIN_VERSION: 插件版本
        PLUGIN_DIR: 插件安装目录
        DATA_DIR: 插件数据目录
        PLATFORM: 操作系统平台
        ARCH: 系统架构
    """
    try:
        # 获取环境变量
        plugin_id = os.environ.get('PLUGIN_ID', 'unknown')
        plugin_version = os.environ.get('PLUGIN_VERSION', '0.0.0')
        plugin_dir = Path(os.environ.get('PLUGIN_DIR', '.'))
        data_dir = Path(os.environ.get('DATA_DIR', '.'))
        platform = os.environ.get('PLATFORM', 'unknown')
        arch = os.environ.get('ARCH', 'unknown')
        
        logger.info(f"开始安装插件: {plugin_id} v{plugin_version}")
        logger.info(f"平台: {platform} {arch}")
        logger.info(f"插件目录: {plugin_dir}")
        logger.info(f"数据目录: {data_dir}")
        
        # 1. 创建数据目录
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✓ 数据目录创建成功")
        
        # 2. 创建子目录
        (data_dir / 'cache').mkdir(exist_ok=True)
        (data_dir / 'logs').mkdir(exist_ok=True)
        (data_dir / 'config').mkdir(exist_ok=True)
        logger.info("✓ 子目录创建成功")
        
        # 3. 创建默认配置文件
        config_file = data_dir / 'config' / 'settings.json'
        default_config = {
            "enabled": True,
            "version": plugin_version,
            "installed_at": "2026-06-06T12:00:00Z",
            "settings": {
                "theme": "default",
                "language": "zh-CN"
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        logger.info("✓ 默认配置创建成功")
        
        # 4. 创建日志文件
        log_file = data_dir / 'logs' / 'plugin.log'
        log_file.touch(exist_ok=True)
        logger.info("✓ 日志文件创建成功")
        
        # 5. 执行平台特定操作
        if platform == 'win32':
            logger.info("执行 Windows 特定初始化...")
            # Windows 特定操作
        elif platform == 'darwin':
            logger.info("执行 macOS 特定初始化...")
            # macOS 特定操作
        elif platform == 'linux':
            logger.info("执行 Linux 特定初始化...")
            # Linux 特定操作
        
        # 6. 验证安装
        if not config_file.exists():
            raise Exception("配置文件创建失败")
        
        logger.info(f"✓ 插件 {plugin_id} 安装完成")
        return 0
        
    except Exception as err:
        logger.error(f"✗ 安装失败: {err}")
        return 1


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 执行安装钩子
    exit_code = main()
    sys.exit(exit_code)
