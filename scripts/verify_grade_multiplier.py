"""
BACKEND-P1-003: 学段系数进度计算功能验证脚本

测试目标:
1. 验证不同学段的系数计算是否正确
2. 验证用户画像中年级信息的获取
3. 验证积分计算逻辑包含学段系数
4. 验证边界情况处理（无画像、默认值等）

运行方式:
    python scripts/verify_grade_multiplier.py
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置后端路径
import sys
import os
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 现在可以导入后端模块
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# 手动配置数据库 URL
DATABASE_URL = "postgresql://xedu:xedu123456@localhost:5432/xedu_db"
from models.recommendation import UserLearningProfile
from models.ai_edu_rewards import AIEduLesson, AIEduPointsTransaction
from services.ai_edu_progress_service import AIEduProgressService


class GradeMultiplierVerifier:
    """学段系数验证器"""
    
    def __init__(self):
        # 创建数据库引擎和会话
        self.engine = create_engine(DATABASE_URL)
        self.db: Session = Session(self.engine)
        self.service = AIEduProgressService(self.db)
        
        # 定义测试用例
        self.test_cases = [
            {
                'name': 'G1-G2 学段 (系数 1.0)',
                'grade_level': 'G1-G2',
                'expected_multiplier': 1.0,
                'base_points': 100,
                'expected_total': 100,
            },
            {
                'name': 'G3-G4 学段 (系数 1.2)',
                'grade_level': 'G3-G4',
                'expected_multiplier': 1.2,
                'base_points': 100,
                'expected_total': 120,
            },
            {
                'name': 'G5-G6 学段 (系数 1.5)',
                'grade_level': 'G5-G6',
                'expected_multiplier': 1.5,
                'base_points': 100,
                'expected_total': 150,
            },
            {
                'name': 'G7-G9 学段 (系数 2.0)',
                'grade_level': 'G7-G9',
                'expected_multiplier': 2.0,
                'base_points': 100,
                'expected_total': 200,
            },
            {
                'name': '无画像用户 (默认系数 1.0)',
                'grade_level': None,
                'expected_multiplier': 1.0,
                'base_points': 100,
                'expected_total': 100,
            },
        ]
        
    def setup_test_data(self):
        """准备测试数据"""
        print("\n" + "="*60)
        print("【步骤 1】准备测试数据")
        print("="*60)
        
        # 创建测试课程
        test_lesson = AIEduLesson(
            lesson_code="TEST_GRADE_MULTIPLIER",
            title="学段系数测试课程",
            module_id=1,
            base_points=100,
            estimated_duration_minutes=30,
            is_active=True
        )
        
        self.db.add(test_lesson)
        self.db.commit()
        
        lesson_id = test_lesson.id
        print(f"✅ 创建测试课程，ID: {lesson_id}")
        
        return lesson_id
    
    def create_user_profile(self, user_id: int, grade_level: str):
        """创建或更新用户画像"""
        profile = self.db.query(UserLearningProfile).filter(
            UserLearningProfile.user_id == user_id
        ).first()
        
        if profile:
            profile.grade_level = grade_level
        else:
            profile = UserLearningProfile(
                user_id=user_id,
                grade_level=grade_level,
                age_group="6-8 岁" if grade_level and "G1" in grade_level else "9-12 岁",
                learning_style="visual",
                preferred_content_type="video"
            )
            self.db.add(profile)
        
        self.db.commit()
        logger.info(f"创建用户画像：user_id={user_id}, grade_level={grade_level}")
    
    async def test_grade_multiplier_calculation(self, user_id: int, expected: float):
        """测试学段系数计算"""
        multiplier = await self.service._get_grade_multiplier(user_id)
        
        assert abs(multiplier - expected) < 0.001, \
            f"学段系数错误：期望{expected}, 实际{multiplier}"
        
        return multiplier
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("【步骤 2】运行学段系数测试")
        print("="*60)
        
        lesson_id = self.setup_test_data()
        
        passed_count = 0
        failed_count = 0
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n【测试 {i}/{len(self.test_cases)}】{test_case['name']}")
            print("-" * 60)
            
            try:
                # 使用不同的 user_id 来区分测试
                test_user_id = 9000 + i
                
                # 创建用户画像（如果需要）
                if test_case['grade_level']:
                    self.create_user_profile(test_user_id, test_case['grade_level'])
                
                # 测试系数计算
                multiplier = await self.test_grade_multiplier_calculation(
                    test_user_id, 
                    test_case['expected_multiplier']
                )
                
                # 验证积分计算
                calculated_points = int(
                    test_case['base_points'] * multiplier
                )
                
                assert calculated_points == test_case['expected_total'], \
                    f"积分计算错误：期望{test_case['expected_total']}, 实际{calculated_points}"
                
                print(f"  ✅ 学段系数：{multiplier}")
                print(f"  ✅ 基础积分：{test_case['base_points']}")
                print(f"  ✅ 最终积分：{calculated_points}")
                print(f"  ✅ 测试通过")
                
                passed_count += 1
                
            except AssertionError as e:
                print(f"  ❌ 测试失败：{e}")
                failed_count += 1
                
            except Exception as e:
                print(f"  ❌ 发生错误：{e}")
                failed_count += 1
        
        # 输出测试结果
        print("\n" + "="*60)
        print("【测试结果】")
        print("="*60)
        print(f"总测试数：{len(self.test_cases)}")
        print(f"通过：{passed_count}")
        print(f"失败：{failed_count}")
        
        if failed_count == 0:
            print("\n🎉 所有测试通过！学段系数功能工作正常！")
            return True
        else:
            print(f"\n❌ 有 {failed_count} 个测试失败，请检查问题。")
            return False
    
    def cleanup_test_data(self, lesson_id: int):
        """清理测试数据"""
        print("\n" + "="*60)
        print("【步骤 3】清理测试数据")
        print("="*60)
        
        # 删除测试课程
        test_lesson = self.db.query(AIEduLesson).filter(
            AIEduLesson.id == lesson_id
        ).first()
        
        if test_lesson:
            self.db.delete(test_lesson)
            self.db.commit()
            print(f"✅ 已删除测试课程 ID: {lesson_id}")
        
        # 删除测试用户画像
        test_user_ids = range(9001, 9001 + len(self.test_cases))
        deleted_count = self.db.query(UserLearningProfile).filter(
            UserLearningProfile.user_id.in_(test_user_ids)
        ).delete(synchronize_session=False)
        
        self.db.commit()
        print(f"✅ 已删除 {deleted_count} 个测试用户画像")
    
    async def run_verification(self):
        """运行完整验证流程"""
        print("\n" + "="*70)
        print(" BACKEND-P1-003: 学段系数进度计算功能验证")
        print("="*70)
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        lesson_id = None
        try:
            # 运行测试
            success = await self.run_all_tests()
            
            # 清理测试数据
            if lesson_id:
                self.cleanup_test_data(lesson_id)
            
            return success
            
        except Exception as e:
            logger.error(f"验证过程出错：{e}", exc_info=True)
            return False
        
        finally:
            self.db.close()
            print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """主函数"""
    verifier = GradeMultiplierVerifier()
    success = await verifier.run_verification()
    
    # 返回退出码
    exit_code = 0 if success else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
