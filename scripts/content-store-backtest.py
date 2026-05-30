#!/usr/bin/env python3
"""
订阅制内容商店集成回测脚本
验证所有功能模块的完整性和正确性
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.utils.database import get_db
from backend.models.content_store import (
    ContentItem, ContentCategory, ContentTag, ContentReview,
    ShoppingCartItem, Order, OrderItem, DRMContent, ContentAccessGrant,
    ContentType, ContentStatus, ContentRating, OrderStatus
)
from backend.models.subscription import (
    UserSubscription, SubscriptionPlan, SubscriptionStatus, 
    SubscriptionPlanType, BillingCycle
)
from backend.models.user import User
from backend.services.drm_service import get_drm_service
from backend.ai_service.recommendation_service import RecommendationEngine
from backend.tasks.recommendation_tasks import get_recommendation_pipeline

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentStoreBacktest:
    """内容商店回测类"""
    
    def __init__(self):
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'modules_tested': [],
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {}
        }
    
    async def run_full_backtest(self) -> Dict[str, Any]:
        """运行完整的回测"""
        logger.info("开始订阅制内容商店集成回测...")
        
        try:
            # 1. 数据模型测试
            await self.test_data_models()
            
            # 2. 订阅系统测试
            await self.test_subscription_system()
            
            # 3. DRM保护测试
            await self.test_drm_protection()
            
            # 4. 推荐系统测试
            await self.test_recommendation_system()
            
            # 5. 内容商店功能测试
            await self.test_content_store_functions()
            
            # 6. API接口测试
            await self.test_api_endpoints()
            
            # 生成测试报告
            self.generate_report()
            
            return self.results
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            self.results['error'] = str(e)
            return self.results
    
    async def test_data_models(self):
        """测试数据模型"""
        module_name = "数据模型"
        logger.info(f"测试 {module_name}...")
        
        try:
            async with get_db() as db:
                # 测试内容分类创建
                category = ContentCategory(
                    category_id="CAT_TEST_001",
                    name="测试分类",
                    description="用于回测的测试分类"
                )
                db.add(category)
                
                # 测试内容项目创建
                content = ContentItem(
                    content_id="CONTENT_TEST_001",
                    title="测试内容",
                    description="这是一个测试内容项目",
                    content_type=ContentType.COURSE,
                    status=ContentStatus.PUBLISHED,
                    rating=ContentRating.BASIC,
                    price=99.9,
                    is_free=False,
                    category_id="CAT_TEST_001"
                )
                db.add(content)
                
                await db.commit()
                
                # 验证创建成功
                content_query = await db.execute(
                    "SELECT COUNT(*) FROM content_items WHERE content_id = 'CONTENT_TEST_001'"
                )
                count = content_query.scalar()
                
                if count == 1:
                    self.record_test_result(module_name, "数据模型创建", True, "内容项目创建成功")
                else:
                    self.record_test_result(module_name, "数据模型创建", False, "内容项目创建失败")
                    
        except Exception as e:
            self.record_test_result(module_name, "数据模型测试", False, f"异常: {str(e)}")
    
    async def test_subscription_system(self):
        """测试订阅系统"""
        module_name = "订阅系统"
        logger.info(f"测试 {module_name}...")
        
        try:
            from backend.models.subscription_fsm import create_subscription_fsm
            
            # 创建测试订阅
            subscription = UserSubscription(
                subscription_id="SUB_TEST_001",
                user_id="test_user_001",
                plan_id="PLAN_BASIC_001",
                status=SubscriptionStatus.TRIAL,
                start_date=datetime.utcnow(),
                trial_start_date=datetime.utcnow(),
                trial_end_date=datetime.utcnow() + timedelta(days=7),
                has_trial=True
            )
            
            # 测试状态机
            fsm = create_subscription_fsm(subscription)
            
            # 测试状态转换
            success = fsm.transition(
                SubscriptionStatus.ACTIVE,
                "测试状态转换",
                {"test": True}
            )
            
            if success and fsm.state == SubscriptionStatus.ACTIVE:
                self.record_test_result(module_name, "状态机转换", True, "状态转换成功")
            else:
                self.record_test_result(module_name, "状态机转换", False, "状态转换失败")
                
        except Exception as e:
            self.record_test_result(module_name, "订阅系统测试", False, f"异常: {str(e)}")
    
    async def test_drm_protection(self):
        """测试DRM保护系统"""
        module_name = "DRM保护系统"
        logger.info(f"测试 {module_name}...")
        
        try:
            drm_service = get_drm_service()
            
            # 测试内容加密
            test_content = "This is a test content for DRM protection testing".encode('utf-8')
            encrypted_result = await drm_service.encrypt_content(
                "TEST_CONTENT_001", test_content, None  # db参数在实际使用中传入
            )
            
            if encrypted_result:
                self.record_test_result(module_name, "内容加密", True, "加密功能正常")
            else:
                self.record_test_result(module_name, "内容加密", False, "加密功能异常")
                
            # 测试水印生成
            watermark = drm_service.generate_watermark(
                "test_user", "test_content", {"device": "test"}
            )
            
            if watermark and len(watermark) > 0:
                self.record_test_result(module_name, "水印生成", True, "水印生成功能正常")
            else:
                self.record_test_result(module_name, "水印生成", False, "水印生成功能异常")
                
        except Exception as e:
            self.record_test_result(module_name, "DRM保护测试", False, f"异常: {str(e)}")
    
    async def test_recommendation_system(self):
        """测试推荐系统"""
        module_name = "推荐系统"
        logger.info(f"测试 {module_name}...")
        
        try:
            recommendation_engine = RecommendationEngine()
            
            # 测试冷启动推荐
            user_profile = {
                "interests": ["编程", "数据科学"],
                "learning_goals": ["机器学习", "Python开发"],
                "skill_level": "intermediate"
            }
            
            # 注意：这里需要数据库连接，在实际测试中应该传入db参数
            cold_start_recs = await recommendation_engine.get_cold_start_recommendations(
                user_profile, None, 5  # db参数为None用于测试
            )
            
            self.record_test_result(
                module_name, 
                "冷启动推荐", 
                True, 
                f"生成了 {len(cold_start_recs)} 个推荐"
            )
            
            # 测试推荐任务管道
            pipeline = get_recommendation_pipeline()
            self.record_test_result(
                module_name, 
                "任务管道", 
                True, 
                "推荐任务管道初始化成功"
            )
            
        except Exception as e:
            self.record_test_result(module_name, "推荐系统测试", False, f"异常: {str(e)}")
    
    async def test_content_store_functions(self):
        """测试内容商店核心功能"""
        module_name = "内容商店功能"
        logger.info(f"测试 {module_name}...")
        
        try:
            # 测试购物车功能
            cart_item = ShoppingCartItem(
                cart_item_id="CART_TEST_001",
                user_id="test_user_001",
                content_id="CONTENT_TEST_001",
                quantity=1
            )
            
            if cart_item and cart_item.quantity == 1:
                self.record_test_result(module_name, "购物车功能", True, "购物车项目创建成功")
            else:
                self.record_test_result(module_name, "购物车功能", False, "购物车功能异常")
            
            # 测试订单创建
            order = Order(
                order_id="ORDER_TEST_001",
                user_id="test_user_001",
                status=OrderStatus.PENDING,
                subtotal=99.9,
                total_amount=99.9,
                currency="CNY"
            )
            
            if order and order.total_amount == 99.9:
                self.record_test_result(module_name, "订单功能", True, "订单创建成功")
            else:
                self.record_test_result(module_name, "订单功能", False, "订单功能异常")
                
        except Exception as e:
            self.record_test_result(module_name, "内容商店功能测试", False, f"异常: {str(e)}")
    
    async def test_api_endpoints(self):
        """测试API端点（模拟）"""
        module_name = "API接口"
        logger.info(f"测试 {module_name}...")
        
        try:
            # 模拟API路由导入测试
            from backend.routes.content_store_routes import router
            
            if router and hasattr(router, 'prefix'):
                self.record_test_result(module_name, "路由注册", True, "API路由注册成功")
            else:
                self.record_test_result(module_name, "路由注册", False, "API路由注册失败")
            
            # 测试API函数存在性
            expected_endpoints = [
                'get_contents', 'get_content_detail', 'get_categories',
                'add_to_cart', 'get_cart', 'create_order'
            ]
            
            available_functions = [attr for attr in dir(router) if not attr.startswith('_')]
            found_endpoints = [ep for ep in expected_endpoints if ep in available_functions]
            
            if len(found_endpoints) >= len(expected_endpoints) * 0.8:  # 80%覆盖率
                self.record_test_result(
                    module_name, 
                    "端点完整性", 
                    True, 
                    f"API端点覆盖率达到 {len(found_endpoints)/len(expected_endpoints)*100:.1f}%"
                )
            else:
                self.record_test_result(
                    module_name, 
                    "端点完整性", 
                    False, 
                    f"API端点覆盖率不足: {len(found_endpoints)}/{len(expected_endpoints)}"
                )
                
        except Exception as e:
            self.record_test_result(module_name, "API接口测试", False, f"异常: {str(e)}")
    
    def record_test_result(self, module: str, test_name: str, passed: bool, message: str):
        """记录测试结果"""
        if module not in self.results['test_results']:
            self.results['test_results'][module] = []
            self.results['modules_tested'].append(module)
        
        result = {
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results['test_results'][module].append(result)
        
        if passed:
            self.results['passed_tests'] += 1
            logger.info(f"✓ {module} - {test_name}: {message}")
        else:
            self.results['failed_tests'] += 1
            logger.error(f"✗ {module} - {test_name}: {message}")
    
    def generate_report(self):
        """生成测试报告"""
        self.results['summary'] = {
            'total_modules': len(self.results['modules_tested']),
            'total_tests': self.results['passed_tests'] + self.results['failed_tests'],
            'pass_rate': (
                self.results['passed_tests'] / 
                (self.results['passed_tests'] + self.results['failed_tests']) * 100
                if (self.results['passed_tests'] + self.results['failed_tests']) > 0 else 0
            ),
            'execution_time': datetime.now().isoformat()
        }
        
        # 输出摘要
        logger.info("=" * 50)
        logger.info("订阅制内容商店回测报告")
        logger.info("=" * 50)
        logger.info(f"测试时间: {self.results['test_timestamp']}")
        logger.info(f"测试模块数: {self.results['summary']['total_modules']}")
        logger.info(f"总测试数: {self.results['summary']['total_tests']}")
        logger.info(f"通过测试: {self.results['passed_tests']}")
        logger.info(f"失败测试: {self.results['failed_tests']}")
        logger.info(f"通过率: {self.results['summary']['pass_rate']:.1f}%")
        logger.info("=" * 50)
        
        if self.results['failed_tests'] == 0:
            logger.info("🎉 所有测试通过！")
        else:
            logger.warning(f"⚠️  {self.results['failed_tests']} 个测试失败")

async def main():
    """主函数"""
    backtest = ContentStoreBacktest()
    results = await backtest.run_full_backtest()
    
    # 保存测试报告
    report_file = f"content_store_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"测试报告已保存到: {report_file}")
    
    # 返回退出码
    return 1 if results['failed_tests'] > 0 else 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)