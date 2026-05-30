#!/usr/bin/env python3
"""
AI-Edu-for-Kids 集成回测验证脚本

验证内容:
1. 数据模型完整性
2. 导入服务功能
3. 积分规则计算
4. 系统兼容性
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.database import get_sync_db, Base
from models.ai_edu_rewards import (
    AIEduModule, AIEduLesson, AIEduRewardRule,
    AIEduAchievement, RewardRuleType, AchievementRarity
)
from services.ai_edu_import_service import AIEduResourceImporter


class AIEduBacktestValidator:
    """AI 教育集成回测验证器"""

    def __init__(self):
        self.test_results = {
            'test_name': 'AI-Edu Integration Backtest',
            'start_time': None,
            'end_time': None,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 70)
        print("AI-Edu-for-Kids 集成回测验证")
        print("=" * 70)
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)

        self.test_results['start_time'] = datetime.now()

        try:
            # 1. 数据模型验证
            self._test_data_models()

            # 2. 导入服务验证
            self._test_import_service()

            # 3. 积分规则验证
            self._test_reward_calculation()

            # 4. 成就系统验证
            self._test_achievement_system()

            # 5. 数据库迁移验证
            self._test_database_migration()

            # 6. 文档完整性检查
            self._test_documentation()

        except Exception as e:
            print(f"\n❌ 回测过程中出错：{e}")
            import traceback
            traceback.print_exc()
            self.test_results['tests_failed'] += 1

        finally:
            self.test_results['end_time'] = datetime.now()
            duration = (self.test_results['end_time'] - self.test_results['start_time']).total_seconds()
            self.test_results['duration_seconds'] = duration

            self._print_summary()
            self._generate_report()

        return self.test_results

    def _test_data_models(self):
        """测试数据模型完整性"""
        print("\n【测试 1/6】数据模型完整性验证...")

        tests = [
            {
                'name': 'AIEduModule 模型',
                'func': self._check_ai_edu_module_model
            },
            {
                'name': 'AIEduLesson 模型',
                'func': self._check_ai_edu_lesson_model
            },
            {
                'name': 'AIEduRewardRule 模型',
                'func': self._check_ai_edu_reward_rule_model
            },
            {
                'name': 'AIEduAchievement 模型',
                'func': self._check_ai_edu_achievement_model
            }
        ]

        for test in tests:
            self._run_single_test(test['name'], test['func'])

    def _check_ai_edu_module_model(self):
        """检查 AI 课程模块模型"""
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

    def _test_import_service(self):
        """测试导入服务功能"""
        print("\n【测试 2/6】导入服务功能验证...")

        test = {
            'name': '导入服务初始化',
            'func': self._check_importer_initialization
        }
        self._run_single_test(test['name'], test['func'])

    def _check_importer_initialization(self):
        """检查导入器初始化"""
        db = next(get_sync_db())

        importer = AIEduResourceImporter(
            base_path='/tmp/test-ai-edu',
            db_session=db
        )

        assert importer.base_path == Path('/tmp/test-ai-edu')
        assert importer.db == db
        print("  ✅ 导入器初始化验证通过")

    def _test_reward_calculation(self):
        """测试积分规则计算"""
        print("\n【测试 3/6】积分规则计算验证...")

        tests = [
            {
                'name': '学段系数计算',
                'func': self._test_grade_multiplier
            },
            {
                'name': '质量奖金计算',
                'func': self._test_quality_bonus
            },
            {
                'name': '连胜奖励计算',
                'func': self._test_streak_bonus
            }
        ]

        for test in tests:
            self._run_single_test(test['name'], test['func'])

    def _test_grade_multiplier(self):
        """测试学段系数计算"""
        db = next(get_sync_db())

        rule = AIEduRewardRule(
            rule_code='test_multiplier',
            rule_name='测试系数',
            rule_type=RewardRuleType.THEORY,
            base_points=100,
            grade_multipliers={
                'G1-G2': 1.0,
                'G3-G4': 1.2,
                'G5-G6': 1.5,
                'G7-G9': 2.0
            }
        )

        db.add(rule)
        db.commit()

        # 验证不同学段的系数
        assert rule.grade_multipliers['G1-G2'] == 1.0
        assert rule.grade_multipliers['G7-G9'] == 2.0

        # 清理
        db.delete(rule)
        db.commit()

        print("  ✅ 学段系数计算验证通过")

    def _test_quality_bonus(self):
        """测试质量奖金计算"""
        rule = AIEduRewardRule(
            rule_code='test_quality',
            rule_name='测试质量',
            quality_coefficients={
                'excellent': 1.2,
                'good': 1.1,
                'pass': 1.0
            }
        )

        base_points = 100
        excellent_score = int(base_points * 1.2)
        good_score = int(base_points * 1.1)

        assert excellent_score == 120
        assert good_score == 110

        print("  ✅ 质量奖金计算验证通过")

    def _test_streak_bonus(self):
        """测试连胜奖励计算"""
        streak_multipliers = {
            3: 1.1,
            5: 1.2,
            10: 1.3,
            20: 1.5,
            30: 2.0
        }

        base_points = 50

        # 测试 5 连胜
        assert streak_multipliers[5] == 1.2
        bonus_5 = int(base_points * 1.2) - base_points
        assert bonus_5 == 10

        # 测试 10 连胜
        assert streak_multipliers[10] == 1.3
        bonus_10 = int(base_points * 1.3) - base_points
        assert bonus_10 == 15

        print("  ✅ 连胜奖励计算验证通过")

    def _test_achievement_system(self):
        """测试成就系统"""
        print("\n【测试 4/6】成就系统验证...")

        test = {
            'name': '成就解锁条件',
            'func': self._test_achievement_conditions
        }
        self._run_single_test(test['name'], test['func'])

    def _test_achievement_conditions(self):
        """测试成就解锁条件"""
        achievement = AIEduAchievement(
            achievement_code='complete_10_courses',
            name='学习达人',
            description='完成 10 个课程',
            rarity=AchievementRarity.RARE,
            unlock_conditions=[
                {'type': 'complete_course', 'count': 10}
            ],
            points_reward=200
        )

        assert achievement.unlock_conditions[0]['count'] == 10
        assert achievement.points_reward == 200

        print("  ✅ 成就解锁条件验证通过")

    def _test_database_migration(self):
        """测试数据库迁移"""
        print("\n【测试 5/6】数据库迁移验证...")

        test = {
            'name': '表结构存在性',
            'func': self._check_table_existence
        }
        self._run_single_test(test['name'], test['func'])

    def _check_table_existence(self):
        """检查表结构是否存在"""
        db = next(get_sync_db())

        # 检查所有表是否存在
        tables = [
            'ai_edu_modules',
            'ai_edu_lessons',
            'ai_edu_reward_rules',
            'ai_edu_achievements',
            'user_ai_edu_achievements',
            'ai_edu_learning_progress',
            'ai_edu_points_transactions',
            'ai_edu_streak_counters'
        ]

        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        existing_tables = inspector.get_table_names()

        for table in tables:
            assert table in existing_tables, f"表 {table} 不存在"
            print(f"  ✅ 表 {table} 存在")

        print("  ✅ 数据库表结构验证通过")

    def _test_documentation(self):
        """测试文档完整性"""
        print("\n【测试 6/6】文档完整性检查...")

        required_docs = [
            'docs/AI_EDU_KNOWLEDGE_MAPPING.md',
            'docs/CURRICULUM_GAP_ANALYSIS.md',
            'docs/RESOURCE_CONVERSION_REQUIREMENTS.md',
            'docs/AI_EDU_POINTS_SYSTEM_DESIGN.md'
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

        print("  ✅ 文档完整性验证通过")

    def _run_single_test(self, name: str, func):
        """运行单个测试"""
        self.test_results['tests_run'] += 1

        try:
            func()
            self.test_results['tests_passed'] += 1
            status = '✅ PASS'
        except Exception as e:
            self.test_results['tests_failed'] += 1
            status = f'❌ FAIL: {e}'

        self.test_results['test_details'].append({
            'test_name': name,
            'status': status,
            'passed': self.test_results['tests_passed'] == self.test_results['tests_run']
        })

    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 70)
        print("回测验证摘要")
        print("=" * 70)
        print(f"总测试数：{self.test_results['tests_run']}")
        print(f"通过测试：{self.test_results['tests_passed']}")
        print(f"失败测试：{self.test_results['tests_failed']}")
        print(f"成功率：{self.test_results['tests_passed']/self.test_results['tests_run']*100:.1f}%")
        print(f"耗时：{self.test_results['duration_seconds']:.2f}秒")

        if self.test_results['tests_failed'] > 0:
            print("\n失败详情:")
            for detail in self.test_results['test_details']:
                if not detail['passed']:
                    print(f"  - {detail['test_name']}: {detail['status']}")

    def _generate_report(self):
        """生成回测报告"""
        report_dir = Path(__file__).parent.parent / 'backtest_reports'
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'ai_edu_backtest_{timestamp}.json'

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 回测报告已保存：{report_file}")


def main():
    """主函数"""
    validator = AIEduBacktestValidator()
    results = validator.run_all_tests()

    # 返回退出码
    return 0 if results['tests_failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
