#!/usr/bin/env python3
"""
AI-Edu 学习进度服务快速验证脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))


def test_progress_service():
    """测试进度服务类"""
    print("\n【测试】学习进度服务类定义...")

    from services.ai_edu_progress_service import AIEduProgressService

    # 验证类存在必要的方法
    assert hasattr(AIEduProgressService, 'report_progress')
    assert hasattr(AIEduProgressService, 'get_user_progress')
    assert hasattr(AIEduProgressService, 'get_progress_statistics')
    assert hasattr(AIEduProgressService, 'complete_lesson_and_award_points')

    print("  ✅ AIEduProgressService 类定义正确")


def test_request_models():
    """测试请求模型"""
    print("\n【测试】请求/响应模型...")

    from services.ai_edu_progress_service import (
        ProgressUpdateRequest,
        LessonCompletionRequest,
        ProgressStatisticsResponse
    )

    # 测试 ProgressUpdateRequest
    req1 = ProgressUpdateRequest(
        lesson_id=1,
        progress_percentage=50,
        time_spent_seconds=600
    )
    assert req1.lesson_id == 1
    assert req1.progress_percentage == 50
    print("  ✅ ProgressUpdateRequest 模型正常")

    # 测试 LessonCompletionRequest
    req2 = LessonCompletionRequest(
        lesson_id=1,
        quiz_score=85.0,
        time_spent_seconds=900
    )
    assert req2.lesson_id == 1
    assert req2.quiz_score == 85.0
    print("  ✅ LessonCompletionRequest 模型正常")

    # 测试 ProgressStatisticsResponse
    resp = ProgressStatisticsResponse(
        total_courses=10,
        completed_courses=5,
        in_progress_courses=3,
        not_started_courses=2,
        total_time_hours=15.5,
        average_quiz_score=82.5,
        average_code_score=88.0,
        total_points=500,
        completion_rate=50.0
    )
    assert resp.total_courses == 10
    assert resp.completion_rate == 50.0
    print("  ✅ ProgressStatisticsResponse 模型正常")


def test_route_definitions():
    """测试路由定义"""
    print("\n【测试】API 路由定义...")

    # 检查路由文件是否存在语法错误
    try:
        from routes import ai_edu_progress_routes
        print("  ✅ 路由模块导入成功")
    except ImportError as e:
        raise AssertionError(f"路由模块导入失败：{e}")

    # 验证路由器存在
    assert hasattr(ai_edu_progress_routes, 'router')
    print("  ✅ API 路由器定义正确")


def test_code_files_existence():
    """测试代码文件存在性"""
    print("\n【测试】代码文件完整性...")

    required_files = [
        'backend/services/ai_edu_progress_service.py',
        'backend/routes/ai_edu_progress_routes.py'
    ]

    for file_path in required_files:
        full_path = Path(__file__).parent.parent / file_path
        if not full_path.exists():
            raise AssertionError(f"缺失文件：{file_path}")
        print(f"  ✅ 文件存在：{file_path}")


def main():
    """主函数"""
    print("=" * 70)
    print("AI-Edu 学习进度服务验证")
    print("=" * 70)
    print(f"开始时间：{Path(__file__).stat().st_mtime}")

    tests_passed = 0
    tests_failed = 0

    try:
        test_progress_service()
        tests_passed += 1

        test_request_models()
        tests_passed += 1

        test_route_definitions()
        tests_passed += 1

        test_code_files_existence()
        tests_passed += 1

    except Exception as e:
        tests_failed += 1
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()

    finally:
        # 打印摘要
        print("\n" + "=" * 70)
        print("验证摘要")
        print("=" * 70)
        print(f"通过测试：{tests_passed}")
        print(f"失败测试：{tests_failed}")

        success_rate = tests_passed / (tests_passed + tests_failed) * 100 if (tests_passed + tests_failed) > 0 else 0
        print(f"成功率：{success_rate:.1f}%")

        if tests_failed == 0:
            print("\n✅ 所有测试通过！学习进度服务已就绪")

    return 0 if tests_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
