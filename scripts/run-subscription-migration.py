#!/usr/bin/env python3
"""
订阅系统数据库迁移脚本
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.logger import setup_logger

# 配置日志
logger = setup_logger('INFO')

def run_sql_migration(db_path: str, sql_file: str):
    """执行SQL迁移文件"""
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 读取SQL文件
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 分割并执行SQL语句
        statements = sql_script.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    logger.info(f"执行SQL语句: {statement[:50]}...")
                except sqlite3.Error as e:
                    logger.warning(f"SQL执行警告: {e}")
                    continue
        
        # 提交更改
        conn.commit()
        logger.info("SQL迁移执行完成")
        
        # 验证表创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        subscription_tables = [table[0] for table in tables if 'subscription' in table[0]]
        
        logger.info(f"创建的订阅相关表: {subscription_tables}")
        
        # 关闭连接
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"SQL迁移失败: {e}")
        return False

def verify_migration(db_path: str):
    """验证迁移结果"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        tables_to_check = [
            'subscription_plans',
            'user_subscriptions', 
            'subscription_payments',
            'subscription_cycles'
        ]
        
        missing_tables = []
        for table in tables_to_check:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"缺少表: {missing_tables}")
            return False
        
        # 检查默认数据
        cursor.execute("SELECT COUNT(*) FROM subscription_plans")
        plan_count = cursor.fetchone()[0]
        logger.info(f"订阅计划数量: {plan_count}")
        
        # 检查视图
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%subscription%'")
        views = cursor.fetchall()
        logger.info(f"创建的视图: {[view[0] for view in views]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"验证迁移失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("订阅系统数据库迁移工具")
    print("=" * 50)
    
    # 数据库路径
    db_path = project_root / "data" / "imato.db"
    migration_file = project_root / "scripts" / "subscription-migration.sql"
    
    # 确保数据目录存在
    db_path.parent.mkdir(exist_ok=True)
    
    # 检查文件存在性
    if not migration_file.exists():
        logger.error(f"迁移文件不存在: {migration_file}")
        return False
    
    print(f"数据库路径: {db_path}")
    print(f"迁移文件: {migration_file}")
    print()
    
    # 执行迁移
    print("开始执行数据库迁移...")
    if run_sql_migration(str(db_path), str(migration_file)):
        print("✓ SQL迁移执行成功")
    else:
        print("✗ SQL迁移执行失败")
        return False
    
    # 验证迁移
    print("验证迁移结果...")
    if verify_migration(str(db_path)):
        print("✓ 迁移验证通过")
    else:
        print("✗ 迁移验证失败")
        return False
    
    print()
    print("🎉 订阅系统数据库迁移完成!")
    print("现在可以使用订阅功能了。")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)