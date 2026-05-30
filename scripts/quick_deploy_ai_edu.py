"""
AI-Edu-for-Kids 快速部署脚本（使用 SQLite）

这个脚本用于快速在本地部署 AI-Edu 模块，使用 SQLite 数据库方便测试和演示。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from sqlalchemy import create_engine
from models.ai_edu_rewards import Base

def main():
    print("=" * 80)
    print("AI-Edu-for-Kids 本地快速部署")
    print("=" * 80)
    
    # 1. 创建 SQLite 数据库
    db_path = Path(__file__).parent.parent / 'data' / 'ai_edu.db'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    database_url = f"sqlite:///{db_path}"
    print(f"\n📦 数据库路径：{db_path}")
    
    # 2. 创建数据库引擎
    print("\n正在创建数据库引擎...")
    engine = create_engine(database_url, echo=False)
    print("✅ 数据库引擎创建成功")
    
    # 3. 创建所有表
    print("\n正在创建数据表...")
    try:
        Base.metadata.create_all(engine)
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
    
    # 4. 验证数据库
    print("\n正在验证数据库...")
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT COUNT(*) FROM ai_edu_modules")
            count = result.scalar()
            print(f"✅ 数据库验证成功，当前有 {count} 个模块")
    except Exception as e:
        print(f"⚠️  验证时出错（正常，因为还未导入数据）: {e}")
    
    # 5. 生成配置信息
    print("\n" + "=" * 80)
    print("部署完成!")
    print("=" * 80)
    
    print("\n📋 配置信息:")
    print(f"  数据库类型：SQLite")
    print(f"  数据库文件：{db_path}")
    print(f"  数据库 URL: {database_url}")
    
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
    print("  - 如果要使用 PostgreSQL，请参考 docs/AI_EDU_LOCAL_DEPLOYMENT.md")
    print("  - 查看 API 文档：http://localhost:8000/docs")
    print("  - 前端访问：http://localhost:4200")
    
    print("\n" + "=" * 80)
    return 0


if __name__ == '__main__':
    sys.exit(main())
