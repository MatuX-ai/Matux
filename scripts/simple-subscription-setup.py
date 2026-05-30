#!/usr/bin/env python3
"""
简化版订阅系统设置脚本
"""

import sqlite3
import os
from pathlib import Path

def setup_simple_subscription_db():
    """设置简化的订阅数据库"""
    
    # 确保数据目录存在
    data_dir = Path("g:/iMato/data")
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "imato.db"
    
    print(f"数据库路径: {db_path}")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 创建简化版订阅计划表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                billing_cycle TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # 创建简化版用户订阅表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                start_date TEXT,
                end_date TEXT,
                auto_renew INTEGER DEFAULT 1
            )
        """)
        
        # 插入测试数据
        test_plans = [
            ('BASIC_MONTHLY', '基础版月付', 29.90, 'monthly'),
            ('PRO_MONTHLY', '专业版月付', 99.90, 'monthly'),
            ('ENTERPRISE_YEARLY', '企业版年付', 999.00, 'yearly')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO subscription_plans 
            (plan_id, name, price, billing_cycle) 
            VALUES (?, ?, ?, ?)
        """, test_plans)
        
        # 提交更改
        conn.commit()
        
        # 验证创建
        cursor.execute("SELECT plan_id, name, price FROM subscription_plans")
        plans = cursor.fetchall()
        
        print("\n创建的订阅计划:")
        for plan in plans:
            print(f"  - {plan[0]}: {plan[1]} - ¥{plan[2]}")
        
        print(f"\n✓ 数据库设置完成！共创建 {len(plans)} 个订阅计划")
        
        # 关闭连接
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 数据库设置失败: {e}")
        return False

def test_subscription_service():
    """测试订阅服务的基本功能"""
    try:
        # 测试导入
        import sys
        sys.path.append('g:/iMato/backend')
        
        # 测试模型导入
        from models.subscription import SubscriptionPlan, SubscriptionStatus
        print("✓ 订阅模型导入成功")
        
        # 测试服务导入
        from services.subscription_service import subscription_service
        print("✓ 订阅服务导入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 服务测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("简化版订阅系统设置")
    print("=" * 50)
    
    # 设置数据库
    if setup_simple_subscription_db():
        print("\n" + "=" * 30)
        print("测试服务功能")
        print("=" * 30)
        
        # 测试服务
        if test_subscription_service():
            print("\n🎉 简化版订阅系统设置完成！")
            print("\n现在可以:")
            print("1. 运行后端服务: cd g:/iMato/backend && py main.py")
            print("2. 访问API文档: http://localhost:8000/docs")
            print("3. 测试订阅API端点")
        else:
            print("\n⚠ 服务测试部分失败，但数据库已设置完成")
    else:
        print("\n✗ 设置失败")