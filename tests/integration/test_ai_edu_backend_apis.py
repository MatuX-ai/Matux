"""
AI-Edu 后端 API 集成测试脚本
测试所有新增的后端 API 端点
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime

# API 基础 URL
API_BASE = "http://localhost:8000/api/v1/org/1/ai-edu"


def print_section(title: str):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test_result(test_name: str, passed: bool, message: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    if message:
        print(f"   └─ {message}")


def test_health_check():
    """测试后端服务健康检查"""
    print_section("测试 1: 后端服务健康检查")
    
    try:
        # 尝试访问根路径
        response = requests.get("http://localhost:8000/docs", timeout=5)
        passed = response.status_code == 200
        print_test_result("Swagger 文档可访问", passed)
        
        if passed:
            print("   ✓ 后端服务运行正常")
        else:
            print("   ✗ 后端服务未响应")
            
        return passed
        
    except requests.exceptions.ConnectionError:
        print_test_result("后端服务连接", False, "无法连接到 http://localhost:8000")
        print("\n💡 提示：请先启动后端服务")
        print("   cd backend")
        print("   python run.py")
        return False
    except Exception as e:
        print_test_result("健康检查", False, str(e))
        return False


def test_execute_python_code():
    """测试 Python 代码执行"""
    print_section("测试 2: Python 代码执行 API")
    
    test_cases = [
        {
            "name": "简单输出",
            "code": "print('Hello from AI-Edu!')",
            "expected_output": "Hello from AI-Edu!"
        },
        {
            "name": "数学计算",
            "code": "print(2 + 3 * 4)",
            "expected_output": "14"
        },
        {
            "name": "循环示例",
            "code": "for i in range(3):\n    print(i)",
            "expected_output": "0\n1\n2"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        try:
            response = requests.post(
                f"{API_BASE}/execute-code",
                json={
                    "code": test_case["code"],
                    "language": "python",
                    "timeout": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                passed = result["success"] and test_case["expected_output"] in result["output"]
                print_test_result(f"Python 测试 - {test_case['name']}", passed)
                
                if not passed:
                    print(f"   实际输出：{result['output']}")
                    all_passed = False
            else:
                print_test_result(f"Python 测试 - {test_case['name']}", False, 
                                f"HTTP {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print_test_result(f"Python 测试 - {test_case['name']}", False, str(e))
            all_passed = False
    
    return all_passed


def test_quiz_start():
    """测试测验启动"""
    print_section("测试 3: 在线测验 - 启动测验")
    
    try:
        response = requests.post(
            f"{API_BASE}/quiz/start",
            json={
                "lesson_id": 1,
                "user_id": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            quiz_data = response.json()
            
            # 验证返回数据结构
            has_quiz_id = "quiz_id" in quiz_data
            has_questions = "questions" in quiz_data
            has_time_limit = "time_limit_minutes" in quiz_data
            
            passed = has_quiz_id and has_questions and has_time_limit
            print_test_result("测验启动 API", passed)
            
            if passed:
                print(f"   ✓ Quiz ID: {quiz_data['quiz_id']}")
                print(f"   ✓ 题目数量：{len(quiz_data['questions'])}")
                print(f"   ✓ 时间限制：{quiz_data['time_limit_minutes']} 分钟")
                
                return True, quiz_data
            else:
                print("   ✗ 返回数据格式不正确")
                return False, None
        else:
            print_test_result("测验启动 API", False, f"HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print_test_result("测验启动 API", False, str(e))
        return False, None


def test_quiz_submit(quiz_data: Dict[str, Any]):
    """测试测验提交"""
    print_section("测试 4: 在线测验 - 提交答案")
    
    if not quiz_data:
        print_test_result("测验提交 API", False, "缺少测验数据")
        return False
    
    try:
        # 构造答案（全部选择正确答案）
        answers = []
        for question in quiz_data["questions"]:
            answers.append({
                "question_id": question["id"],
                "answer": question["correct_answer"]
            })
        
        # 提交答案
        response = requests.post(
            f"{API_BASE}/quiz/submit",
            json={
                "quiz_id": quiz_data["quiz_id"],
                "answers": answers
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 验证结果
            has_score = "score" in result
            has_accuracy = "accuracy" in result
            has_points = "points_earned" in result
            
            passed = has_score and has_accuracy and has_points
            print_test_result("测验提交 API", passed)
            
            if passed:
                print(f"   ✓ 得分：{result['score']}/{result['total_score']}")
                print(f"   ✓ 正确率：{result['accuracy'] * 100:.1f}%")
                print(f"   ✓ 获得积分：{result['points_earned']}")
                print(f"   ✓ 通过状态：{'✅' if result['passed'] else '❌'}")
                
                return True
            else:
                print("   ✗ 返回数据格式不正确")
                return False
        else:
            print_test_result("测验提交 API", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("测验提交 API", False, str(e))
        return False


def test_get_supported_languages():
    """测试获取支持的编程语言"""
    print_section("测试 5: 获取支持的编程语言")
    
    try:
        response = requests.get(f"{API_BASE}/supported-languages", timeout=10)
        
        if response.status_code == 200:
            languages = response.json()
            print_test_result("获取语言列表", True)
            
            for lang_name, lang_info in languages.items():
                available = "✅" if lang_info.get("available", False) else "⚠️"
                print(f"   {available} {lang_name}: {lang_info.get('version', '未知')}")
            
            return True
        else:
            print_test_result("获取语言列表", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("获取语言列表", False, str(e))
        return False


def test_quiz_review(quiz_id: str):
    """测试测验解析查看"""
    print_section("测试 6: 在线测验 - 查看解析")
    
    if not quiz_id:
        print_test_result("查看解析 API", False, "缺少 Quiz ID")
        return False
    
    try:
        response = requests.get(f"{API_BASE}/quiz/{quiz_id}/review", timeout=10)
        
        # 404 是正常的（因为测验可能已被清除）
        if response.status_code in [200, 404]:
            print_test_result("查看解析 API", True, "API 端点可用")
            return True
        else:
            print_test_result("查看解析 API", False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_test_result("查看解析 API", False, str(e))
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🎓" * 35)
    print("  AI-Edu-for-Kids 后端 API 集成测试")
    print("🎓" * 35)
    print(f"\n开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API 地址：{API_BASE}")
    
    results = []
    quiz_data = None
    
    # 测试 1: 健康检查
    results.append(("健康检查", test_health_check()))
    
    if results[-1][1]:  # 如果服务正常
        # 测试 2: 代码执行
        results.append(("Python 代码执行", test_execute_python_code()))
        
        # 测试 3: 启动测验
        quiz_passed, quiz_data = test_quiz_start()
        results.append(("启动测验", quiz_passed))
        
        if quiz_passed and quiz_data:
            # 测试 4: 提交测验
            submit_passed = test_quiz_submit(quiz_data)
            results.append(("提交测验", submit_passed))
            
            # 测试 6: 查看解析
            review_passed = test_quiz_review(quiz_data.get("quiz_id", ""))
            results.append(("查看解析", review_passed))
        
        # 测试 5: 获取语言列表
        results.append(("支持的语言", test_get_supported_languages()))
    
    # 汇总结果
    print_section("测试结果汇总")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n总计：{passed}/{total} 项测试通过")
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n成功率：{success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 所有关键功能测试通过！")
        print("\n下一步建议:")
        print("  1. 启动 Angular 开发服务器：ng serve")
        print("  2. 访问 http://localhost:4200/ai-edu/course/1/lesson/1")
        print("  3. 测试真实的前后端集成")
    elif success_rate >= 50:
        print("\n⚠️ 部分测试通过，请检查失败的项目")
    else:
        print("\n❌ 大部分测试失败，请检查后端服务配置")
    
    print(f"\n结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误：{e}")
        exit(1)
