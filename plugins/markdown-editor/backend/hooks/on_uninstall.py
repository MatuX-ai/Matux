"""
Markdown 编辑器 - 卸载钩子

在卸载时执行:
1. 备份用户数据（可选）
2. 清理临时文件
3. 导出文档（可选）
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def on_uninstall(plugin_info: dict, data_dir: str, keep_data: bool = True) -> bool:
    """
    卸载钩子
    
    Args:
        plugin_info: 插件信息（manifest）
        data_dir: 插件数据目录
        keep_data: 是否保留数据
    
    Returns:
        是否成功
    """
    try:
        logger.info("开始卸载 Markdown 编辑器插件...")
        
        base_dir = Path(data_dir)
        
        if not base_dir.exists():
            logger.warning(f"数据目录不存在: {data_dir}")
            return True
        
        # 1. 备份用户文档
        if keep_data:
            logger.info("备份用户文档...")
            
            backup_dir = base_dir / "backups" / f"uninstall_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            documents_dir = base_dir / "documents"
            if documents_dir.exists():
                # 复制所有文档到备份目录
                backup_docs_dir = backup_dir / "documents"
                shutil.copytree(documents_dir, backup_docs_dir)
                
                doc_count = len(list(documents_dir.glob("*.json")))
                logger.info(f"  ✓ 备份了 {doc_count} 个文档到: {backup_docs_dir}")
            
            # 备份配置
            config_path = base_dir / "config.json"
            if config_path.exists():
                shutil.copy2(config_path, backup_dir / "config.json")
                logger.info(f"  ✓ 备份配置文件")
            
            # 创建备份说明
            readme_path = backup_dir / "README.txt"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"""Markdown 编辑器 - 卸载备份
==========================

备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
插件版本: {plugin_info.get('version', 'unknown')}

此备份包含:
- 所有 Markdown 文档（documents/）
- 插件配置文件（config.json）

如果需要恢复数据，请将这些文件复制到新安装的插件数据目录中。

数据目录位置: {data_dir}
""")
            
            logger.info(f"  ✓ 备份完成: {backup_dir}")
        
        # 2. 清理导出文件
        exports_dir = base_dir / "exports"
        if exports_dir.exists():
            export_files = list(exports_dir.glob("*"))
            if export_files:
                logger.info(f"清理 {len(export_files)} 个导出文件...")
                for file in export_files:
                    try:
                        file.unlink()
                    except Exception as e:
                        logger.warning(f"删除文件失败 {file}: {e}")
        
        # 3. 如果选择不保留数据，删除整个数据目录
        if not keep_data:
            logger.info("删除所有用户数据...")
            
            try:
                shutil.rmtree(base_dir)
                logger.info(f"  ✓ 已删除数据目录: {base_dir}")
            except Exception as e:
                logger.error(f"  ✗ 删除数据目录失败: {e}")
                return False
        
        else:
            logger.info("保留用户数据（已备份）")
        
        logger.info("✅ Markdown 编辑器插件卸载完成！")
        
        if keep_data:
            logger.info(f"📁 数据已保留并备份: {backup_dir}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 卸载失败: {e}", exc_info=True)
        return False
