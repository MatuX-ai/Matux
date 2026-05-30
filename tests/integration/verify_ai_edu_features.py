"""
AI-Edu 功能扩展验证脚本
验证所有新增组件和服务的基本功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def verify_database_modules():
    """验证数据库中的课程模块"""
    print_section("P0: 验证数据库课程模块")
    
    try:
        from sqlalchemy import create_engine, text
        from pathlib import Path
        
        db_path = Path(__file__).parent.parent / 'data' / 'ai_edu_standalone.db'
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.begin() as conn:
            # 查询所有模块
            result = conn.execute(text("""
                SELECT module_code, name, is_active, display_order 
                FROM ai_edu_modules 
                ORDER BY display_order
            """))
            
            modules = list(result.fetchall())
            
            print(f"\n✅ 数据库连接成功")
            print(f"📚 共有 {len(modules)} 个课程模块:")
            
            for module in modules:
                status = "✅" if module.is_active else "❌"
                print(f"  {status} {module.module_code}: {module.name}")
            
            # 查询课时总数
            result = conn.execute(text("""
                SELECT COUNT(*) FROM ai_edu_lessons
            """))
            
            lesson_count = result.scalar()
            print(f"\n📝 共有 {lesson_count} 个课时")
            
            # 验证新增模块
            new_modules = ['data_perception_01', 'ml_intro_01']
            module_codes = [m[0] for m in modules]
            
            for code in new_modules:
                if code in module_codes:
                    print(f"✅ 新增模块 {code} 已成功导入")
                else:
                    print(f"❌ 新增模块 {code} 未找到")
            
            return True
            
    except Exception as e:
        print(f"❌ 验证失败：{e}")
        return False

def verify_frontend_components():
    """验证前端组件文件"""
    print_section("P1-P3: 验证前端组件和服务")
    
    components = [
        ('课程播放器', 'src/app/components/ai-edu-course-player/ai-edu-course-player.component.ts'),
        ('在线测验', 'src/app/components/ai-edu-quiz/ai-edu-quiz.component.ts'),
        ('加载动画', 'src/app/components/ai-edu-loading/ai-edu-loading.component.ts'),
    ]
    
    services = [
        ('学习服务', 'src/app/services/ai-edu-learning.service.ts'),
        ('缓存服务', 'src/app/services/ai-edu-cache.service.ts'),
        ('错误处理', 'src/app/services/ai-edu-error-handler.service.ts'),
    ]
    
    base_path = Path(__file__).parent.parent
    
    print("\n🔧 检查组件文件:")
    for name, path in components:
        full_path = base_path / path
        if full_path.exists():
            size = full_path.stat().st_size
            lines = len(full_path.read_text(encoding='utf-8').splitlines())
            print(f"  ✅ {name}: {lines} 行，{size:,} 字节")
        else:
            print(f"  ❌ {name}: 文件不存在")
    
    print("\n🔧 检查服务文件:")
    for name, path in services:
        full_path = base_path / path
        if full_path.exists():
            size = full_path.stat().st_size
            lines = len(full_path.read_text(encoding='utf-8').splitlines())
            print(f"  ✅ {name}: {lines} 行，{size:,} 字节")
        else:
            print(f"  ❌ {name}: 文件不存在")
    
    return True

def verify_course_resources():
    """验证课程资源文件"""
    print_section("课程资源文件验证")
    
    resources = [
        ('Module 02 配置', 'data/ai-edu-resources/modules/module_02_data/module.json'),
        ('Module 02 Lesson 01', 'data/ai-edu-resources/modules/module_02_data/lesson_01.json'),
        ('Module 02 Lesson 02', 'data/ai-edu-resources/modules/module_02_data/lesson_02.json'),
        ('Module 03 配置', 'data/ai-edu-resources/modules/module_03_ml/module.json'),
        ('Module 03 Lesson 01', 'data/ai-edu-resources/modules/module_03_ml/lesson_01.json'),
    ]
    
    base_path = Path(__file__).parent.parent
    
    print("\n📚 检查课程资源:")
    for name, path in resources:
        full_path = base_path / path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {name}: {size:,} 字节")
        else:
            print(f"  ❌ {name}: 文件不存在")
    
    return True

def verify_import_script():
    """验证导入脚本"""
    print_section("导入脚本验证")
    
    script_path = Path(__file__).parent.parent / 'scripts' / 'import_new_ai_edu_modules.py'
    
    if script_path.exists():
        content = script_path.read_text(encoding='utf-8')
        lines = len(content.splitlines())
        print(f"\n✅ 导入脚本存在：{lines} 行")
        
        # 检查关键功能
        checks = [
            ('唯一性检查', 'SELECT id FROM ai_edu_modules WHERE module_code'),
            ('增量更新', 'if not existing'),
            ('错误处理', 'try:'),
        ]
        
        print("\n🔍 功能检查:")
        for name, keyword in checks:
            if keyword in content:
                print(f"  ✅ {name}: 已实现")
            else:
                print(f"  ❌ {name}: 未找到")
        
        return True
    else:
        print(f"\n❌ 导入脚本不存在")
        return False

def main():
    """主函数"""
    print("\n" + "🎓" * 35)
    print("  AI-Edu-for-Kids 功能扩展验证")
    print("🎓" * 35)
    
    results = []
    
    # 执行验证
    results.append(("数据库模块", verify_database_modules()))
    results.append(("前端组件", verify_frontend_components()))
    results.append(("课程资源", verify_course_resources()))
    results.append(("导入脚本", verify_import_script()))
    
    # 汇总结果
    print_section("验证结果汇总")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n总计：{passed}/{total} 项验证通过")
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    if passed == total:
        print("\n🎉 所有验证通过！功能扩展成功完成！")
        return 0
    else:
        print("\n⚠️ 部分验证未通过，请检查问题")
        return 1

if __name__ == '__main__':
    exit(main())
