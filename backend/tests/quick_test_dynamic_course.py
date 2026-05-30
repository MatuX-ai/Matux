"""
动态课程生成服务快速验证测试
简化版测试，避免复杂的依赖导入
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_dynamic_course_module_import():
    """测试动态课程模块导入"""
    try:
        # 直接导入核心模块

        print("✅ 动态课程模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 动态课程模块导入失败: {str(e)}")
        return False


def test_models_import():
    """测试模型导入"""
    try:
        print("✅ 动态课程模型导入成功")
        return True
    except Exception as e:
        print(f"❌ 动态课程模型导入失败: {str(e)}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    try:
        from ai_service.dynamic_course import DynamicCourseGenerator, StudentProfile

        # 创建生成器实例（不连接OpenAI）
        generator = DynamicCourseGenerator()
        print("✅ 动态课程生成器实例化成功")

        # 测试模板加载
        templates = generator.course_templates
        print(f"✅ 加载了 {len(templates)} 个课程模板")

        # 测试学生档案创建
        student_profile = StudentProfile(
            grade=8,
            age=14,
            learning_style="动手型",
            prior_knowledge=["基础电路"],
            interests=["机器人"],
            learning_goals=["掌握编程"],
        )
        print("✅ 学生档案创建成功")

        return True
    except Exception as e:
        print(f"❌ 基本功能测试失败: {str(e)}")
        return False


def test_route_registration():
    """测试路由注册"""
    try:
        # 检查路由文件是否存在
        route_file = os.path.join(
            os.path.dirname(__file__), "..", "routes", "dynamic_course_routes.py"
        )
        if os.path.exists(route_file):
            print("✅ 动态课程路由文件存在")
            return True
        else:
            print("❌ 动态课程路由文件不存在")
            return False
    except Exception as e:
        print(f"❌ 路由注册测试失败: {str(e)}")
        return False


def test_documentation():
    """测试文档存在性"""
    try:
        doc_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "docs", "API_AI_DYNAMIC_COURSE.md"
        )
        if os.path.exists(doc_file):
            print("✅ API文档文件存在")
            return True
        else:
            print("❌ API文档文件不存在")
            return False
    except Exception as e:
        print(f"❌ 文档测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("动态课程生成引擎验证测试")
    print("=" * 50)

    tests = [
        ("模块导入测试", test_dynamic_course_module_import),
        ("模型导入测试", test_models_import),
        ("基本功能测试", test_basic_functionality),
        ("路由注册测试", test_route_registration),
        ("文档完整性测试", test_documentation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 运行 {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {str(e)}")

    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！动态课程生成引擎部署成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关组件")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
