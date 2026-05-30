#!/usr/bin/env python3
"""
Cursor任务解析测试脚本
测试AI助手的任务理解和执行能力
"""

import json
import os
import sys
from pathlib import Path
import time
from typing import Dict, List, Any

class CursorTestingFramework:
    def __init__(self):
        self.test_cases = []
        self.results = []
        self.setup_test_cases()
        
    def setup_test_cases(self):
        """设置测试用例"""
        self.test_cases = [
            {
                "id": "TC001",
                "name": "简单功能实现任务",
                "task": "请帮我创建一个计算两个数之和的TypeScript函数",
                "expected_outcomes": [
                    "生成有效的TypeScript代码",
                    "函数具有正确的参数类型",
                    "包含适当的注释",
                    "代码格式正确"
                ],
                "difficulty": "easy"
            },
            {
                "id": "TC002", 
                "name": "复杂业务逻辑任务",
                "task": "实现一个用户管理系统，包含用户增删改查功能，使用Angular和RxJS",
                "expected_outcomes": [
                    "生成完整的Angular服务",
                    "包含CRUD操作方法",
                    "正确使用RxJS Observable",
                    "遵循Angular最佳实践"
                ],
                "difficulty": "medium"
            },
            {
                "id": "TC003",
                "name": "API集成任务",
                "task": "创建一个与REST API交互的服务，支持错误处理和加载状态",
                "expected_outcomes": [
                    "实现HTTP客户端封装",
                    "包含错误处理机制",
                    "支持加载状态管理",
                    "代码结构清晰"
                ],
                "difficulty": "medium"
            },
            {
                "id": "TC004",
                "name": "代码重构任务",
                "task": "请优化这段代码的性能，减少时间复杂度",
                "expected_outcomes": [
                    "识别性能瓶颈",
                    "提出优化方案",
                    "给出改进后的代码",
                    "说明优化原理"
                ],
                "difficulty": "hard"
            },
            {
                "id": "TC005",
                "name": "Bug修复任务",
                "task": "这个函数在处理大数组时会出现内存溢出，请找出问题并修复",
                "expected_outcomes": [
                    "准确定位问题原因",
                    "提供修复方案",
                    "给出优化后的代码",
                    "解释修复原理"
                ],
                "difficulty": "hard"
            },
            {
                "id": "TC006",
                "name": "架构设计任务",
                "task": "为一个电商平台设计后端API架构，使用FastAPI和PostgreSQL",
                "expected_outcomes": [
                    "提供合理的架构设计",
                    "定义清晰的API端点",
                    "考虑数据模型设计",
                    "包含错误处理策略"
                ],
                "difficulty": "expert"
            }
        ]
    
    def simulate_ai_response(self, task: str) -> Dict[str, Any]:
        """模拟AI助手响应（实际使用时应替换为真实的AI API调用）"""
        # 这里模拟不同类型的AI响应
        responses = {
            "计算两个数之和": {
                "code": """function addNumbers(a: number, b: number): number {
    // 计算两个数字的和
    return a + b;
}

// 使用示例
const result = addNumbers(5, 3);
console.log(result); // 输出: 8""",
                "explanation": "这是一个简单的TypeScript函数，接收两个数字参数并返回它们的和。",
                "quality_score": 0.95
            },
            "用户管理系统": {
                "code": """import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

export interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private baseUrl = 'http://localhost:3000/api/users';
  private usersSubject = new BehaviorSubject<User[]>([]);
  public users$ = this.usersSubject.asObservable();

  constructor(private http: HttpClient) {}

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl).pipe(
      map(users => {
        this.usersSubject.next(users);
        return users;
      }),
      catchError(this.handleError)
    );
  }

  getUser(id: number): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  createUser(user: Partial<User>): Observable<User> {
    return this.http.post<User>(this.baseUrl, user).pipe(
      catchError(this.handleError)
    );
  }

  updateUser(id: number, user: Partial<User>): Observable<User> {
    return this.http.put<User>(`${this.baseUrl}/${id}`, user).pipe(
      catchError(this.handleError)
    );
  }

  deleteUser(id: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: any): Observable<never> {
    console.error('An error occurred:', error);
    throw error;
  }
}""",
                "explanation": "这是一个完整的Angular用户管理服务，实现了CRUD操作，使用RxJS进行响应式编程。",
                "quality_score": 0.88
            }
        }
        
        # 根据任务内容选择合适的响应
        if "计算两个数之和" in task:
            return responses["计算两个数之和"]
        elif "用户管理" in task:
            return responses["用户管理系统"]
        else:
            # 默认响应
            return {
                "code": "// 根据您的需求生成的代码",
                "explanation": "AI助手理解了您的任务需求并提供了相应的解决方案。",
                "quality_score": 0.75
            }
    
    def evaluate_response_quality(self, response: Dict[str, Any], expected_outcomes: List[str]) -> Dict[str, Any]:
        """评估AI响应质量"""
        score = response.get("quality_score", 0)
        code = response.get("code", "")
        explanation = response.get("explanation", "")
        
        # 检查代码质量指标
        quality_metrics = {
            "has_valid_syntax": self.check_syntax_validity(code),
            "has_comments": "://" in code or "/*" in code,
            "follows_best_practices": self.check_best_practices(code),
            "is_complete_solution": len(code.strip()) > 50,
            "has_error_handling": "try" in code or "catch" in code or "handleError" in code
        }
        
        # 计算综合得分
        base_score = score
        quality_bonus = sum(quality_metrics.values()) / len(quality_metrics) * 0.2
        final_score = min(1.0, base_score + quality_bonus)
        
        return {
            "score": final_score,
            "quality_metrics": quality_metrics,
            "meets_expectations": final_score >= 0.8,
            "feedback": self.generate_feedback(quality_metrics, expected_outcomes)
        }
    
    def check_syntax_validity(self, code: str) -> bool:
        """检查代码语法有效性"""
        # 简单的语法检查
        try:
            # 这里可以集成实际的语法检查器
            return "function" in code or "class" in code or "interface" in code
        except:
            return False
    
    def check_best_practices(self, code: str) -> bool:
        """检查是否遵循最佳实践"""
        best_practices_indicators = [
            "const " in code,
            "let " in code,
            "=>" in code,  # 箭头函数
            "interface " in code,
            "type " in code,
            "async " in code,
            "await " in code
        ]
        return sum(best_practices_indicators) >= 2
    
    def generate_feedback(self, quality_metrics: Dict[str, bool], expected_outcomes: List[str]) -> str:
        """生成反馈意见"""
        feedback_parts = []
        
        if not quality_metrics["has_valid_syntax"]:
            feedback_parts.append("代码语法存在问题")
        
        if not quality_metrics["has_comments"]:
            feedback_parts.append("建议添加更多注释说明")
            
        if not quality_metrics["follows_best_practices"]:
            feedback_parts.append("可以采用更多现代JavaScript/TypeScript特性")
            
        if not quality_metrics["is_complete_solution"]:
            feedback_parts.append("解决方案不够完整")
            
        if not quality_metrics["has_error_handling"]:
            feedback_parts.append("建议添加错误处理机制")
        
        if not feedback_parts:
            return "代码质量良好，符合预期要求"
        else:
            return "改进建议: " + "; ".join(feedback_parts)
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        print(f"\n🎯 执行测试: {test_case['id']} - {test_case['name']}")
        print(f"   难度等级: {test_case['difficulty']}")
        print(f"   任务描述: {test_case['task']}")
        
        start_time = time.time()
        
        # 模拟AI响应
        response = self.simulate_ai_response(test_case['task'])
        
        # 评估响应质量
        evaluation = self.evaluate_response_quality(response, test_case['expected_outcomes'])
        
        execution_time = time.time() - start_time
        
        result = {
            "test_id": test_case["id"],
            "test_name": test_case["name"],
            "difficulty": test_case["difficulty"],
            "execution_time": execution_time,
            "ai_response": response,
            "evaluation": evaluation,
            "passed": evaluation["meets_expectations"]
        }
        
        print(f"   执行时间: {execution_time:.2f}秒")
        print(f"   质量得分: {evaluation['score']:.2f}")
        print(f"   测试结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
        print(f"   反馈意见: {evaluation['feedback']}")
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试用例"""
        print("=" * 60)
        print("Cursor AI助手任务解析能力测试")
        print("=" * 60)
        
        results = []
        passed_count = 0
        
        for test_case in self.test_cases:
            result = self.run_test_case(test_case)
            results.append(result)
            if result["passed"]:
                passed_count += 1
        
        # 生成测试报告
        report = self.generate_test_report(results, passed_count)
        
        print("\n" + "=" * 60)
        print("测试完成汇总")
        print("=" * 60)
        print(f"总测试数: {len(results)}")
        print(f"通过测试: {passed_count}")
        print(f"失败测试: {len(results) - passed_count}")
        print(f"成功率: {(passed_count/len(results)*100):.1f}%")
        print(f"平均质量得分: {report['summary']['average_score']:.2f}")
        
        return report
    
    def generate_test_report(self, results: List[Dict], passed_count: int) -> Dict[str, Any]:
        """生成详细的测试报告"""
        scores = [r["evaluation"]["score"] for r in results]
        execution_times = [r["execution_time"] for r in results]
        
        # 按难度分组统计
        difficulty_stats = {}
        for result in results:
            difficulty = result["difficulty"]
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"total": 0, "passed": 0, "scores": []}
            
            difficulty_stats[difficulty]["total"] += 1
            if result["passed"]:
                difficulty_stats[difficulty]["passed"] += 1
            difficulty_stats[difficulty]["scores"].append(result["evaluation"]["score"])
        
        report = {
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_count,
                "failed_tests": len(results) - passed_count,
                "success_rate": passed_count / len(results),
                "average_score": sum(scores) / len(scores),
                "average_execution_time": sum(execution_times) / len(execution_times)
            },
            "difficulty_analysis": difficulty_stats,
            "detailed_results": results,
            "recommendations": self.generate_recommendations(results)
        }
        
        # 保存报告到文件
        self.save_report(report)
        
        return report
    
    def generate_recommendations(self, results: List[Dict]) -> List[str]:
        """基于测试结果生成改进建议"""
        recommendations = []
        
        # 分析常见问题
        low_scores = [r for r in results if r["evaluation"]["score"] < 0.7]
        if len(low_scores) > len(results) * 0.3:
            recommendations.append("建议优化AI模型的理解能力和代码生成质量")
        
        # 检查执行时间
        slow_responses = [r for r in results if r["execution_time"] > 5.0]
        if slow_responses:
            recommendations.append("部分任务响应时间较长，建议优化推理速度")
        
        # 检查失败的测试
        failed_tests = [r for r in results if not r["passed"]]
        if failed_tests:
            common_issues = self.analyze_failure_patterns(failed_tests)
            recommendations.extend(common_issues)
        
        if not recommendations:
            recommendations.append("整体表现良好，继续保持")
        
        return recommendations
    
    def analyze_failure_patterns(self, failed_tests: List[Dict]) -> List[str]:
        """分析失败模式"""
        issues = []
        
        # 按难度分析
        hard_failures = [t for t in failed_tests if t["difficulty"] in ["hard", "expert"]]
        if hard_failures:
            issues.append("在处理复杂任务时准确率有待提升")
        
        # 检查质量问题
        quality_issues = []
        for test in failed_tests:
            metrics = test["evaluation"]["quality_metrics"]
            if not metrics["has_valid_syntax"]:
                quality_issues.append("语法正确性")
            if not metrics["follows_best_practices"]:
                quality_issues.append("最佳实践遵循")
        
        if quality_issues:
            issues.append(f"需要改进{'和'.join(set(quality_issues))}方面")
        
        return issues
    
    def save_report(self, report: Dict[str, Any]):
        """保存测试报告到文件"""
        project_root = Path(__file__).parent.parent
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"cursor_testing_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 详细测试报告已保存到: {report_file}")

def main():
    """主函数"""
    tester = CursorTestingFramework()
    report = tester.run_all_tests()
    
    # 输出最终结论
    success_rate = report["summary"]["success_rate"]
    avg_score = report["summary"]["average_score"]
    
    print("\n" + "=" * 60)
    print("🎯 测试结论")
    print("=" * 60)
    
    if success_rate >= 0.8 and avg_score >= 0.8:
        print("🎉 Cursor AI助手表现出色！")
        print("   - 任务解析准确率高")
        print("   - 代码生成质量优秀")
        print("   - 可以投入生产环境使用")
    elif success_rate >= 0.6:
        print("✅ Cursor AI助手表现良好，但仍需改进")
        print("   - 基本功能可用")
        print("   - 建议针对性优化薄弱环节")
    else:
        print("⚠️ Cursor AI助手需要显著改进")
        print("   - 任务理解能力不足")
        print("   - 代码质量有待提升")
        print("   - 建议重新训练或调整模型")

if __name__ == "__main__":
    main()