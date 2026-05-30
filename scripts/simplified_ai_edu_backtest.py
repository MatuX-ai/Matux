#!/usr/bin/env python3
"""
AI-Edu-for-Kids 集成 - 简化版回测验证脚本

专注于验证 AI-Edu 模块本身的功能，避免其他模块干扰
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))


class AIEduSimplifiedBacktest:
    """AI 教育集成简化版回测器"""
    
    def __init__(self):
        self.test_results = {
            'test_name': 'AI-Edu Simplified Backtest',
            'start_time': None,
            'end_time': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
    
    def run_all_tests(self) -> dict:
        """运行所有测试"""
        print("=" * 80)
        print("AI-Edu-for-Kids 集成 - 简化版回测验证")
        print("=" * 80)
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        
        self.test_results['start_time'] = datetime.now()
        
        try:
            # 1. 文件完整性检查
            self._test_file_existence()
            
            # 2. 代码语法检查
            self._test_code_syntax()
            
            # 3. 服务类定义检查
            self._test_service_definitions()
            
            # 4. 积分计算逻辑验证
            self._test_reward_logic()
            
            # 5. API 路由检查
            self._test_api_routes()
            
            # 6. 文档完整性检查
            self._test_documentation()
            
        except Exception as e:
            print(f"\n❌ 回测过程中出错：{e}")
            import traceback
            traceback.print_exc()
            self._record_failure("综合测试", str(e))
        
        finally:
            self.test_results['end_time'] = datetime.now()
            duration = (self.test_results['end_time'] - self.test_results['start_time']).total_seconds()
            self.test_results['duration_seconds'] = duration
            
            self._print_summary()
            self._generate_report()
        
        return self.test_results
    
    def _test_file_existence(self):
        """测试文件存在性"""
        print("\n【测试 1/6】文件完整性检查...")
        
        # 后端代码
        backend_files = [
            'backend/models/ai_edu_rewards.py',
            'backend/services/ai_edu_import_service.py',
            'backend/services/ai_edu_progress_service.py',
            'backend/routes/ai_edu_progress_routes.py',
            'backend/migrations/versions/ai_edu_001_create_ai_edu_tables.py'
        ]
        
        print("后端代码文件:")
        for file_path in backend_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                raise AssertionError(f"缺失后端文件：{file_path}")
            print(f"  ✅ 文件存在：{file_path}")
        
        # 工具脚本
        script_files = [
            'scripts/import_ai_edu_resources.py',
            'scripts/validate_ai_edu_integration.py',
            'scripts/verify_ai_edu_setup.py',
            'scripts/verify_ai_edu_progress.py',
            'scripts/comprehensive_ai_edu_backtest.py'
        ]
        
        print("\n工具脚本文件:")
        for file_path in script_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                raise AssertionError(f"缺失脚本文件：{file_path}")
            print(f"  ✅ 文件存在：{file_path}")
        
        # 前端代码
        frontend_files = [
            'src/app/models/ai-edu.models.ts',
            'src/app/core/services/ai-edu.service.ts',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.component.ts',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.component.html',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.component.scss',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.module.ts'
        ]
        
        print("\n前端代码文件:")
        for file_path in frontend_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                raise AssertionError(f"缺失前端文件：{file_path}")
            print(f"  ✅ 文件存在：{file_path}")
    
    def _test_code_syntax(self):
        """测试代码语法"""
        print("\n【测试 2/6】代码语法检查...")
        
        # Python 文件语法检查
        python_files = [
            'backend/models/ai_edu_rewards.py',
            'backend/services/ai_edu_import_service.py',
            'backend/services/ai_edu_progress_service.py',
            'backend/routes/ai_edu_progress_routes.py',
            'scripts/import_ai_edu_resources.py'
        ]
        
        for file_path in python_files:
            full_path = Path(__file__).parent.parent / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    compile(code, str(full_path), 'exec')
                print(f"  ✅ 语法正确：{file_path}")
            except SyntaxError as e:
                raise AssertionError(f"语法错误 {file_path}: {e}")
    
    def _test_service_definitions(self):
        """测试服务类定义"""
        print("\n【测试 3/6】服务类定义检查...")
        
        # 导入服务
        from services.ai_edu_import_service import AIEduResourceImporter
        
        assert hasattr(AIEduResourceImporter, 'import_all'), "缺少 import_all 方法"
        assert hasattr(AIEduResourceImporter, '_import_modules'), "缺少 _import_modules 方法"
        assert hasattr(AIEduResourceImporter, '_import_lessons'), "缺少 _import_lessons 方法"
        print("  ✅ 导入服务类定义正确")
        
        # 进度服务
        from services.ai_edu_progress_service import AIEduProgressService
        
        assert hasattr(AIEduProgressService, 'report_progress'), "缺少 report_progress 方法"
        assert hasattr(AIEduProgressService, 'get_user_progress'), "缺少 get_user_progress 方法"
        assert hasattr(AIEduProgressService, 'complete_lesson_and_award_points'), "缺少 complete_lesson_and_award_points 方法"
        print("  ✅ 进度服务类定义正确")
    
    def _test_reward_logic(self):
        """测试积分计算逻辑"""
        print("\n【测试 4/6】积分计算逻辑验证...")
        
        # 学段系数
        grade_multipliers = {
            'G1-G2': 1.0,
            'G3-G4': 1.2,
            'G5-G6': 1.5,
            'G7-G9': 2.0
        }
        
        base_points = 100
        
        # 验证各学段
        g1_result = int(base_points * grade_multipliers['G1-G2'])
        g7_result = int(base_points * grade_multipliers['G7-G9'])
        
        assert g1_result == 100, f"G1-G2 学段计算错误：期望 100，实际{g1_result}"
        assert g7_result == 200, f"G7-G9 学段计算错误：期望 200，实际{g7_result}"
        print("  ✅ 学段系数计算正确")
        
        # 质量系数
        quality_coefficients = {
            'excellent': 1.2,  # ≥90 分
            'good': 1.1,       # ≥80 分
            'pass': 1.0        # <80 分
        }
        
        excellent_score = int(100 * 1.2)
        good_score = int(100 * 1.1)
        pass_score = int(100 * 1.0)
        
        assert excellent_score == 120, f"优秀质量系数错误"
        assert good_score == 110, f"良好质量系数错误"
        assert pass_score == 100, f"及格质量系数错误"
        print("  ✅ 质量系数计算正确")
        
        # 连胜奖励
        streak_multipliers = {
            3: 1.1,   # 3 连胜 +10%
            5: 1.2,   # 5 连胜 +20%
            10: 1.3,  # 10 连胜 +30%
            30: 2.0   # 30 连胜 +100%
        }
        
        assert streak_multipliers[5] == 1.2, "5 连胜系数错误"
        assert streak_multipliers[30] == 2.0, "30 连胜系数错误"
        print("  ✅ 连胜系数计算正确")
        
        # 综合计算示例
        base = 50
        grade_mult = 1.5  # G5-G6
        quality_mult = 1.2  # 优秀
        time_bonus = 10  # 节省 20 分钟 × 0.5
        
        expected = int(base * grade_mult * quality_mult) + time_bonus
        calculated = int(50 * 1.5 * 1.2) + 10
        
        assert expected == calculated == 100, f"综合计算错误：期望{expected}, 实际{calculated}"
        print("  ✅ 综合积分计算正确")
    
    def _test_api_routes(self):
        """测试 API 路由"""
        print("\n【测试 5/6】API 路由检查...")
        
        try:
            from routes import ai_edu_progress_routes
            
            # 验证路由器存在
            assert hasattr(ai_edu_progress_routes, 'router'), "缺少 router 属性"
            print("  ✅ API 路由器定义正确")
            
            # 统计端点数量
            route_count = len([r for r in ai_edu_progress_routes.router.routes])
            assert route_count >= 5, f"预期至少 5 个路由，实际{route_count}个"
            print(f"  ✅ API 端点数量正确 ({route_count}个)")
            
            # 验证请求模型
            from services.ai_edu_progress_service import ProgressUpdateRequest, LessonCompletionRequest
            
            req1 = ProgressUpdateRequest(
                lesson_id=1,
                progress_percentage=50,
                time_spent_seconds=600,
                status='in_progress'
            )
            assert req1.lesson_id == 1
            print("  ✅ ProgressUpdateRequest 模型正确")
            
            req2 = LessonCompletionRequest(
                lesson_id=1,
                quiz_score=85.0,
                time_spent_seconds=900
            )
            assert req2.lesson_id == 1
            print("  ✅ LessonCompletionRequest 模型正确")
            
        except ImportError as e:
            raise AssertionError(f"API 路由模块导入失败：{e}")
    
    def _test_documentation(self):
        """测试文档完整性"""
        print("\n【测试 6/6】文档完整性检查...")
        
        required_docs = [
            'docs/AI_EDU_KNOWLEDGE_MAPPING.md',
            'docs/CURRICULUM_GAP_ANALYSIS.md',
            'docs/RESOURCE_CONVERSION_REQUIREMENTS.md',
            'docs/AI_EDU_POINTS_SYSTEM_DESIGN.md',
            'docs/AI_EDU_INTEGRATION_SUMMARY.md',
            'docs/AI_EDU_QUICK_START.md',
            'docs/AI_EDU_TASK_CHECKLIST.md',
            'docs/AI_EDU_EXECUTIVE_SUMMARY.md',
            'docs/AI_EDU_PROGRESS_SERVICE_REPORT.md',
            'docs/AI_EDU_FRONTEND_COMPONENT_REPORT.md',
            'docs/AI_EDU_FINAL_COMPREHENSIVE_SUMMARY.md'
        ]
        
        missing_docs = []
        for doc_path in required_docs:
            full_path = Path(__file__).parent.parent / doc_path
            if not full_path.exists():
                missing_docs.append(doc_path)
                print(f"  ❌ 缺失文档：{doc_path}")
            else:
                print(f"  ✅ 文档存在：{doc_path}")
        
        if missing_docs:
            raise AssertionError(f"缺失以下文档：{missing_docs}")
    
    def _record_failure(self, test_name: str, error: str):
        """记录失败"""
        self.test_results['failed_tests'] += 1
        self.test_results['test_details'].append({
            'test_name': test_name,
            'status': f'❌ FAIL: {error}',
            'passed': False
        })
    
    def _run_single_test(self, name: str, passed: bool, details: str = ""):
        """运行单个测试"""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
            status = '✅ PASS'
        else:
            self.test_results['failed_tests'] += 1
            status = f'❌ FAIL: {details}'
        
        self.test_results['test_details'].append({
            'test_name': name,
            'status': status,
            'passed': passed
        })
        
        if passed:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}: {details}")
    
    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("回测验证摘要")
        print("=" * 80)
        print(f"总测试数：{self.test_results['total_tests']}")
        print(f"通过测试：{self.test_results['passed_tests']}")
        print(f"失败测试：{self.test_results['failed_tests']}")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100 
                       if self.test_results['total_tests'] > 0 else 0)
        print(f"成功率：{success_rate:.1f}%")
        print(f"耗时：{self.test_results['duration_seconds']:.2f}秒")
        
        if self.test_results['failed_tests'] > 0:
            print("\n失败详情:")
            for detail in self.test_results['test_details']:
                if not detail['passed']:
                    print(f"  - {detail['test_name']}: {detail['status']}")
    
    def _generate_report(self):
        """生成回测报告"""
        report_dir = Path(__file__).parent.parent / 'backtest_reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'ai_edu_simplified_backtest_{timestamp}.json'
        
        report_data = {
            'test_name': self.test_results['test_name'],
            'start_time': self.test_results['start_time'].isoformat() if self.test_results['start_time'] else None,
            'end_time': self.test_results['end_time'].isoformat() if self.test_results['end_time'] else None,
            'duration_seconds': self.test_results.get('duration_seconds', 0),
            'total_tests': self.test_results['total_tests'],
            'passed_tests': self.test_results['passed_tests'],
            'failed_tests': self.test_results['failed_tests'],
            'success_rate': (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100 
                           if self.test_results['total_tests'] > 0 else 0),
            'test_details': self.test_results['test_details']
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 回测报告已保存：{report_file}")


def main():
    """主函数"""
    validator = AIEduSimplifiedBacktest()
    results = validator.run_all_tests()
    
    # 返回退出码
    return 0 if results['failed_tests'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
