"""
验证 AI-Edu 数据库内容
"""

from sqlalchemy import create_engine, text
from pathlib import Path

db_path = Path(__file__).parent.parent / 'data' / 'ai_edu_standalone.db'
database_url = f"sqlite:///{db_path}"

engine = create_engine(database_url)

print("=" * 80)
print("AI-Edu 数据库验证")
print("=" * 80)

with engine.connect() as conn:
    # 查询模块
    print("\n📚 课程模块:")
    result = conn.execute(text("SELECT * FROM ai_edu_modules"))
    modules = result.fetchall()
    
    if modules:
        for module in modules:
            print(f"\n  模块 ID: {module[0]}")
            print(f"  模块代码：{module[1]}")
            print(f"  名称：{module[2]}")
            print(f"  描述：{module[3]}")
            print(f"  分类：{module[4]}")
            print(f"  预计课时：{module[6]}")
            print(f"  预计时长：{module[7]}分钟")
    else:
        print("  暂无数据")
    
    # 查询课时
    print("\n\n📖 课程课时:")
    result = conn.execute(text("SELECT * FROM ai_edu_lessons"))
    lessons = result.fetchall()
    
    if lessons:
        for lesson in lessons:
            print(f"\n  课时 ID: {lesson[0]}")
            print(f"  课时代码：{lesson[2]}")
            print(f"  标题：{lesson[3]}")
            print(f"  副标题：{lesson[4]}")
            print(f"  类型：{lesson[5]}")
            print(f"  基础积分：{lesson[15]}")
            print(f"  是否有测验：{'是' if lesson[10] else '否'}")
            print(f"  是否有实践：{'是' if lesson[12] else '否'}")
    else:
        print("  暂无数据")
    
    # 统计信息
    print("\n\n📊 统计信息:")
    result = conn.execute(text("SELECT COUNT(*) FROM ai_edu_modules"))
    module_count = result.scalar()
    print(f"  模块总数：{module_count}")
    
    result = conn.execute(text("SELECT COUNT(*) FROM ai_edu_lessons"))
    lesson_count = result.scalar()
    print(f"  课时总数：{lesson_count}")

print("\n" + "=" * 80)
print("✅ 验证完成!")
print("=" * 80)
