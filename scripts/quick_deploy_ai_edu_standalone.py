"""
AI-Edu-for-Kids 快速部署脚本（独立版本）

这个脚本仅创建 AI-Edu 模块的表，不依赖其他模块。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from sqlalchemy import create_engine, MetaData

def main():
    print("=" * 80)
    print("AI-Edu-for-Kids 本地快速部署 (独立版本)")
    print("=" * 80)
    
    # 1. 创建 SQLite 数据库
    db_path = Path(__file__).parent.parent / 'data' / 'ai_edu_standalone.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    database_url = f"sqlite:///{db_path}"
    print(f"\n📦 数据库路径：{db_path}")
    
    # 2. 创建数据库引擎
    print("\n正在创建数据库引擎...")
    engine = create_engine(database_url, echo=False)
    metadata = MetaData()
    print("✅ 数据库引擎创建成功")
    
    # 3. 定义 AI-Edu 表结构（简化版）
    from sqlalchemy import Column, Integer, String, Text, Float, Boolean, JSON, DateTime, ForeignKey
    
    # 课程模块表
    ai_edu_modules = __import__('sqlalchemy').Table(
        'ai_edu_modules', metadata,
        Column('id', Integer, primary_key=True),
        Column('module_code', String(50), unique=True),
        Column('name', String(100)),
        Column('description', Text),
        Column('category', String(50)),
        Column('grade_ranges', JSON),
        Column('expected_lessons', Integer),
        Column('expected_duration_minutes', Integer),
        Column('is_active', Boolean, default=True),
        Column('display_order', Integer, default=0)
    )
    
    # 课程课时表
    ai_edu_lessons = __import__('sqlalchemy').Table(
        'ai_edu_lessons', metadata,
        Column('id', Integer, primary_key=True),
        Column('module_id', Integer, ForeignKey('ai_edu_modules.id')),
        Column('lesson_code', String(50), unique=True),
        Column('title', String(100)),
        Column('subtitle', String(200)),
        Column('content_type', String(20)),
        Column('content_url', String(500)),
        Column('resources', JSON),
        Column('learning_objectives', JSON),
        Column('knowledge_points', JSON),
        Column('estimated_duration_minutes', Integer),
        Column('has_quiz', Boolean, default=False),
        Column('quiz_passing_score', Float),
        Column('has_practice', Boolean, default=False),
        Column('practice_type', String(20)),
        Column('base_points', Integer, default=20),
        Column('is_active', Boolean, default=True),
        Column('display_order', Integer, default=0)
    )
    
    # 奖励规则表
    ai_edu_reward_rules = __import__('sqlalchemy').Table(
        'ai_edu_reward_rules', metadata,
        Column('id', Integer, primary_key=True),
        Column('rule_code', String(50), unique=True),
        Column('rule_name', String(100)),
        Column('rule_type', String(20)),
        Column('base_points', Integer, default=20),
        Column('grade_multipliers', JSON),
        Column('quality_coefficients', JSON),
        Column('streak_multipliers', JSON),
        Column('is_active', Boolean, default=True)
    )
    
    # 成就徽章表
    ai_edu_achievements = __import__('sqlalchemy').Table(
        'ai_edu_achievements', metadata,
        Column('id', Integer, primary_key=True),
        Column('achievement_code', String(50), unique=True),
        Column('name', String(100)),
        Column('description', Text),
        Column('icon_url', String(500)),
        Column('rarity', String(20)),
        Column('unlock_conditions', JSON),
        Column('points_reward', Integer, default=100),
        Column('integral_reward', Integer, default=0),
        Column('is_active', Boolean, default=True)
    )
    
    # 4. 创建所有表
    print("\n正在创建数据表...")
    try:
        metadata.create_all(engine)
        print("✅ 数据表创建成功")
        
        # 列出创建的表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\n已创建的数据表:")
        for table in tables:
            if table.startswith('ai_edu_'):
                print(f"  - {table}")
        
    except Exception as e:
        print(f"❌ 创建数据表失败：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 5. 插入示例数据
    print("\n正在插入示例数据...")
    try:
        with engine.connect() as conn:
            # 插入一个示例模块
            from sqlalchemy import insert
            
            stmt = insert(ai_edu_modules).values(
                module_code='demo_module_01',
                name='AI 基本概念入门',
                description='人工智能基础概念介绍',
                category='basic_concepts',
                grade_ranges=[{'min': 1, 'max': 6}],
                expected_lessons=8,
                expected_duration_minutes=120,
                is_active=True,
                display_order=1
            )
            conn.execute(stmt)
            conn.commit()
            
            print("✅ 示例数据插入成功")
            
    except Exception as e:
        print(f"⚠️  插入示例数据时出错：{e}")
    
    # 6. 生成配置信息
    print("\n" + "=" * 80)
    print("部署完成!")
    print("=" * 80)
    
    print("\n📋 配置信息:")
    print(f"  数据库类型：SQLite")
    print(f"  数据库文件：{db_path}")
    print(f"  数据库 URL: {database_url}")
    print(f"  创建的表数量：{len([t for t in tables if t.startswith('ai_edu_')])}")
    
    print("\n🎯 下一步操作:")
    print("  1. 准备课程资源到 data/ai-edu-resources/ 目录")
    print("  2. 运行批量导入脚本:")
    print(f"     python scripts/import_ai_edu_resources.py --path {db_path.parent}\\ai-edu-resources --execute")
    print("  3. 启动后端服务:")
    print("     cd backend")
    print("     python main.py")
    print("\n  4. (可选) 启动前端:")
    print("     ng serve")
    
    print("\n💡 提示:")
    print("  - 查看 API 文档：http://localhost:8000/docs")
    print("  - 前端访问：http://localhost:4200")
    print("  - 数据库文件位置：{db_path}")
    
    print("\n" + "=" * 80)
    return 0


if __name__ == '__main__':
    sys.exit(main())
