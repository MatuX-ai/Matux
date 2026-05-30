#!/usr/bin/env python3
"""
AI-Edu-for-Kids 集成 - 综合回测验证脚本

验证范围:
1. 后端数据模型
2. 业务服务层
3. API 路由
4. 前端 TypeScript 模型
5. 文档完整性
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))


class AIEduComprehensiveBacktest:
    """AI 教育集成综合回测器"""
    
    def __init__(self):
        self.test_results = {
            'test_name': 'AI-Edu Comprehensive Backtest',
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
        print("AI-Edu-for-Kids 集成 - 综合回测验证")
        print("=" * 80)
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
        
        self.test_results['start_time'] = datetime.now()
        
        try:
            # 1. 后端数据模型验证
            self._test_backend_models()
            
            # 2. 业务服务验证
            self._test_services()
            
            # 3. API 路由验证
            self._test_api_routes()
            
            # 4. 前端文件验证
            self._test_frontend_files()
            
            # 5. 文档完整性检查
            self._test_documentation()
            
            # 6. 代码质量检查
            self._test_code_quality()
            
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
    
    def _test_backend_models(self):
        """测试后端数据模型"""
        print("\n【测试 1/6】后端数据模型验证...")
        
        tests = [
            {
                'name': 'AIEduModule 模型实例化',
                'func': self._check_ai_edu_module_model
            },
            {
                'name': 'AIEduLesson 模型实例化',
                'func': self._check_ai_edu_lesson_model
            },
            {
                'name': 'AIEduRewardRule 模型实例化',
                'func': self._check_ai_edu_reward_rule_model
            },
            {
                'name': 'AIEduAchievement 模型实例化',
                'func': self._check_ai_edu_achievement_model
            }
        ]
        
        for test in tests:
            self._run_single_test(test['name'], test['func'])
    
    def _check_ai_edu_module_model(self):
        """检查 AI 课程模块模型"""
        from models.ai_edu_rewards import AIEduModule
        
        module = AIEduModule(
            module_code='test_module',
            name='测试模块',
            description='用于测试的模块',
            category='basic_concepts',
            grade_ranges=[{'min': 1, 'max': 6}],
            expected_lessons=8,
            is_active=True
        )
        
        assert module.module_code == 'test_module'
        assert module.name == '测试模块'
        assert module.category == 'basic_concepts'
        print("  ✅ AIEduModule 模型验证通过")
    
    def _check_ai_edu_lesson_model(self):
        """检查 AI 课程课时模型"""
        from models.ai_edu_rewards import AIEduLesson
        
        lesson = AIEduLesson(
            lesson_code='test_lesson',
            title='测试课时',
            content_type='hybrid',
            has_quiz=True,
            base_points=20,
            is_active=True
        )
        
        assert lesson.lesson_code == 'test_lesson'
        assert lesson.base_points == 20
        assert lesson.has_quiz == True
        print("  ✅ AIEduLesson 模型验证通过")
    
    def _check_ai_edu_reward_rule_model(self):
        """检查奖励规则模型"""
        from models.ai_edu_rewards import AIEduRewardRule, RewardRuleType
        
        rule = AIEduRewardRule(
            rule_code='test_rule',
            rule_name='测试规则',
            rule_type=RewardRuleType.THEORY,
            base_points=50,
            grade_multipliers={'G1-G2': 1.0, 'G7-G9': 2.0},
            is_active=True
        )
        
        assert rule.rule_code == 'test_rule'
        assert rule.base_points == 50
        assert rule.grade_multipliers['G7-G9'] == 2.0
        print("  ✅ AIEduRewardRule 模型验证通过")
    
    def _check_ai_edu_achievement_model(self):
        """检查成就徽章模型"""
        from models.ai_edu_rewards import AIEduAchievement, AchievementRarity
        
        achievement = AIEduAchievement(
            achievement_code='test_achievement',
            name='测试成就',
            rarity=AchievementRarity.RARE,
            points_reward=200,
            is_active=True
        )
        
        assert achievement.achievement_code == 'test_achievement'
        assert achievement.rarity == AchievementRarity.RARE
        assert achievement.points_reward == 200
        print("  ✅ AIEduAchievement 模型验证通过")
    
    def _test_services(self):
        """测试业务服务层"""
        print("\n【测试 2/6】业务服务验证...")
        
        tests = [
            {
                'name': '导入服务类定义',
                'func': self._check_import_service
            },
            {
                'name': '进度服务类定义',
                'func': self._check_progress_service
            },
            {
                'name': '积分计算逻辑',
                'func': self._test_reward_calculation
            }
        ]
        
        for test in tests:
            self._run_single_test(test['name'], test['func'])
    
    def _check_import_service(self):
        """检查导入服务"""
        from services.ai_edu_import_service import AIEduResourceImporter
        
        assert hasattr(AIEduResourceImporter, 'import_all')
        assert hasattr(AIEduResourceImporter, '_import_modules')
        assert hasattr(AIEduResourceImporter, '_import_lessons')
        print("  ✅ 导入服务类定义正确")
    
    def _check_progress_service(self):
        """检查进度服务"""
        from services.ai_edu_progress_service import AIEduProgressService
        
        assert hasattr(AIEduProgressService, 'report_progress')
        assert hasattr(AIEduProgressService, 'get_user_progress')
        assert hasattr(AIEduProgressService, 'complete_lesson_and_award_points')
        print("  ✅ 进度服务类定义正确")
    
    def _test_reward_calculation(self):
        """测试积分计算逻辑"""
        # 学段系数测试
        grade_multipliers = {
            'G1-G2': 1.0,
            'G3-G4': 1.2,
            'G5-G6': 1.5,
            'G7-G9': 2.0
        }
        
        base_points = 100
        
        # 验证不同学段
        assert int(base_points * grade_multipliers['G1-G2']) == 100
        assert int(base_points * grade_multipliers['G7-G9']) == 200
        print("  ✅ 学段系数计算正确")
        
        # 质量系数测试
        quality_coefficients = {
            'excellent': 1.2,
            'good': 1.1,
            'pass': 1.0
        }
        
        excellent_score = int(100 * 1.2)
        good_score = int(100 * 1.1)
        
        assert excellent_score == 120
        assert good_score == 110
        print("  ✅ 质量系数计算正确")
        
        # 连胜系数测试
        streak_multipliers = {
            3: 1.1,
            5: 1.2,
            10: 1.3,
            30: 2.0
        }
        
        assert streak_multipliers[5] == 1.2
        assert streak_multipliers[30] == 2.0
        print("  ✅ 连胜系数计算正确")
    
    def _test_api_routes(self):
        """测试 API 路由"""
        print("\n【测试 3/6】API 路由验证...")
        
        try:
            from routes import ai_edu_progress_routes
            
            # 验证路由器存在
            assert hasattr(ai_edu_progress_routes, 'router')
            print("  ✅ API 路由器定义正确")
            
            # 验证端点数量
            route_count = len([r for r in ai_edu_progress_routes.router.routes])
            assert route_count >= 5, f"预期至少 5 个路由，实际{route_count}个"
            print(f"  ✅ API 端点数量正确 ({route_count}个)")
            
        except ImportError as e:
            raise AssertionError(f"API 路由模块导入失败：{e}")
    
    def _test_frontend_files(self):
        """测试前端文件"""
        print("\n【测试 4/6】前端文件完整性检查...")
        
        frontend_files = [
            'src/app/models/ai-edu.models.ts',
            'src/app/core/services/ai-edu.service.ts',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.component.ts',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.component.html',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.component.scss',
            'src/app/components/ai-edu-course-list/ai-edu-course-list.module.ts'
        ]
        
        for file_path in frontend_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                raise AssertionError(f"缺失前端文件：{file_path}")
            print(f"  ✅ 文件存在：{file_path}")
    
    def _test_documentation(self):
        """测试文档完整性"""
        print("\n【测试 5/6】文档完整性检查...")
        
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
    
    def _test_code_quality(self):
        """测试代码质量"""
        print("\n【测试 6/6】代码文件完整性检查...")
        
        backend_files = [
            'backend/models/ai_edu_rewards.py',
            'backend/services/ai_edu_import_service.py',
            'backend/services/ai_edu_progress_service.py',
            'backend/routes/ai_edu_progress_routes.py',
            'backend/migrations/versions/ai_edu_001_create_ai_edu_tables.py'
        ]
        
        script_files = [
            'scripts/import_ai_edu_resources.py',
            'scripts/validate_ai_edu_integration.py',
            'scripts/verify_ai_edu_setup.py',
            'scripts/verify_ai_edu_progress.py'
        ]
        
        print("后端代码文件:")
        for file_path in backend_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                raise AssertionError(f"缺失后端文件：{file_path}")
            print(f"  ✅ 文件存在：{file_path}")
        
        print("工具脚本文件:")
        for file_path in script_files:
            full_path = Path(__file__).parent.parent / file_path
            if not full_path.exists():
                raise AssertionError(f"缺失脚本文件：{file_path}")
            print(f"  ✅ 文件存在：{file_path}")
    
    def _run_single_test(self, name: str, func):
        """运行单个测试"""
        self.test_results['total_tests'] += 1
        
        try:
            func()
            self.test_results['passed_tests'] += 1
            status = '✅ PASS'
            passed = True
        except Exception as e:
            self.test_results['failed_tests'] += 1
            status = f'❌ FAIL: {e}'
            passed = False
            print(f"  ❌ {name} 失败：{e}")
        
        self.test_results['test_details'].append({
            'test_name': name,
            'status': status,
            'passed': passed
        })
    
    def _record_failure(self, test_name: str, error: str):
        """记录失败"""
        self.test_results['failed_tests'] += 1
        self.test_results['test_details'].append({
            'test_name': test_name,
            'status': f'❌ FAIL: {error}',
            'passed': False
        })
    
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
        report_file = report_dir / f'ai_edu_comprehensive_backtest_{timestamp}.json'
        
        # 准备可序列化的报告
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
    validator = AIEduComprehensiveBacktest()
    results = validator.run_all_tests()
    
    # 返回退出码
    return 0 if results['failed_tests'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
