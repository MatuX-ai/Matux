"""
Token 计费集成测试
验证 AI 功能的 Token 消费逻辑
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from services.token_service import TokenService
from services.llm_assistant_service import LLMAssistantService
from ai_service.dynamic_course import DynamicCourseGenerator, DynamicCourseRequest, StudentProfile
from models.user import User


class TestAIBillingIntegration:
    """AI 计费集成测试"""

    def test_ai_chat_billing_success(self, db_session: Session, test_user: User):
        """测试 AI 对话计费成功"""
        # 1. 购买 Token 套餐
        token_service = TokenService(db_session)
        token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=2,  # 标准包 1000 tokens
            payment_method="wechat",
            order_no=f"BILL_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        # 2. 创建 AI 助手服务
        assistant = LLMAssistantService(db_session)

        # 3. 初始余额
        initial_balance = token_service.get_or_create_user_balance(
            test_user.id)
        assert initial_balance.remaining_tokens == 1000

        # 4. 进行 AI 对话
        import asyncio
        response = asyncio.run(
            assistant.chat(
                user_id=test_user.id,
                message="什么是机器学习？",
                current_lesson_context={"title": "AI 基础"}
            )
        )

        # 5. 验证扣费
        assert 'billing' in response
        assert response['billing']['tokens_consumed'] > 0
        assert response['billing']['usage_type'] == 'ai_teacher'

        # 6. 验证余额减少
        final_balance = token_service.get_or_create_user_balance(test_user.id)
        assert final_balance.remaining_tokens == 1000 - \
            response['billing']['tokens_consumed']

    def test_ai_chat_insufficient_tokens(self, db_session: Session, test_user: User):
        """测试 AI 对话 Token 不足"""
        # 1. 创建用户但不充值
        token_service = TokenService(db_session)
        balance = token_service.get_or_create_user_balance(test_user.id)
        assert balance.remaining_tokens == 0

        # 2. 创建 AI 助手服务
        assistant = LLMAssistantService(db_session)

        # 3. 尝试对话应该抛出异常
        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(
                assistant.chat(
                    user_id=test_user.id,
                    message="什么是机器学习？",
                )
            )

        assert exc_info.value.status_code == 402
        assert "INSUFFICIENT_TOKENS" in str(exc_info.value.detail)

    def test_course_generation_billing(self, db_session: Session, test_user: User):
        """测试课程生成计费"""
        # 1. 购买套餐
        token_service = TokenService(db_session)
        token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=3,  # 高级包 5000 tokens
            payment_method="wechat",
            order_no=f"COURSE_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        # 2. 创建课程生成器
        generator = DynamicCourseGenerator(db_session)

        # 3. 创建课程请求
        request = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=8,
                age=13,
                learning_style="visual",
                interests=["编程", "机器人"],
                learning_goals=["学习 Python 基础"]
            ),
            subject_area="计算机科学",
            learning_objectives=["理解变量和循环"],
            difficulty_level="beginner",
            project_type="实践项目",
            time_constraint=20,
            language="zh-CN"
        )

        # 4. 生成课程
        import asyncio
        response = asyncio.run(
            generator.generate_course(
                user_id=test_user.id,
                request=request
            )
        )

        # 5. 验证扣费（简单课程 50 tokens）
        assert response is not None

        # 6. 验证余额
        stats = token_service.get_token_stats(test_user.id)
        assert stats['used_tokens'] == 50  # 简单课程费用


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
