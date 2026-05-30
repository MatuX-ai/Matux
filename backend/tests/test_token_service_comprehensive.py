"""
Token 服务核心功能单元测试
测试 Token 计费、套餐管理、余额查询等核心功能
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

# 假设的导入路径（根据实际项目结构调整）
from backend.services.token_service import TokenService, TokenPackage
from backend.models.token_models import TokenTransaction, TokenType, TransactionType
from backend.models.user import User


class TestTokenServiceBasic:
    """Token 服务基础功能测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def token_service(self, mock_db):
        """创建 Token 服务实例"""
        return TokenService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """创建示例用户"""
        user = Mock(spec=User)
        user.id = "user_123"
        user.email = "test@example.com"
        return user

    def test_get_token_balance_success(self, token_service, mock_db, sample_user):
        """测试获取 Token 余额成功"""
        # 准备测试数据
        mock_balance = Mock()
        mock_balance.total_tokens = 1000
        mock_balance.used_tokens = 300
        mock_balance.remaining_tokens = 700

        mock_db.query().filter().first.return_value = mock_balance

        # 执行测试
        balance = token_service.get_token_balance(sample_user.id)

        # 验证结果
        assert balance.total == 1000
        assert balance.used == 300
        assert balance.remaining == 700
        assert balance.usage_rate == 0.3  # 30% 使用率

    def test_get_token_balance_no_record(self, token_service, mock_db, sample_user):
        """测试用户没有 Token 记录"""
        mock_db.query().filter().first.return_value = None

        balance = token_service.get_token_balance(sample_user.id)

        assert balance.total == 0
        assert balance.used == 0
        assert balance.remaining == 0

    def test_calculate_token_cost_basic(self, token_service):
        """测试计算 Token 消耗 - 基础场景"""
        # AI 课程生成：基础 10 Token + 每千字 5 Token
        cost = token_service.calculate_token_cost(
            service_type="ai_course_generation",
            metadata={"word_count": 2000}
        )

        assert cost == 20  # 10 + (2000/1000 * 5)

    def test_calculate_token_cost_with_model_tier(self, token_service):
        """测试不同模型级别的 Token 消耗"""
        # GPT-4 高级模型：系数 2.0
        cost_gpt4 = token_service.calculate_token_cost(
            service_type="ai_chat",
            metadata={"model": "gpt-4", "tokens_used": 1000}
        )

        # GPT-3.5 基础模型：系数 1.0
        cost_gpt35 = token_service.calculate_token_cost(
            service_type="ai_chat",
            metadata={"model": "gpt-3.5-turbo", "tokens_used": 1000}
        )

        assert cost_gpt4 > cost_gpt35  # GPT-4 消耗更多

    def test_calculate_token_cost_with_complexity(self, token_service):
        """测试复杂课程的 Token 消耗"""
        # 复杂课程：基础 + 复杂度系数
        cost_simple = token_service.calculate_token_cost(
            service_type="ai_course_generation",
            metadata={"complexity": "basic", "word_count": 1000}
        )

        cost_complex = token_service.calculate_token_cost(
            service_type="ai_course_generation",
            metadata={"complexity": "advanced", "word_count": 1000}
        )

        assert cost_complex > cost_simple


class TestTokenDeduction:
    """Token 扣减功能测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        db.begin = Mock()  # Mock 事务上下文
        return db

    @pytest.fixture
    def token_service(self, mock_db):
        """创建 Token 服务实例"""
        return TokenService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """创建示例用户"""
        user = Mock(spec=User)
        user.id = "user_123"
        user.email = "test@example.com"
        return user

    @pytest.mark.asyncio
    async def test_deduct_tokens_success(self, token_service, mock_db, sample_user):
        """测试成功扣减 Token"""
        # 准备余额数据
        mock_balance = Mock()
        mock_balance.remaining_tokens = 1000

        mock_db.query().filter().first.side_effect = [
            mock_balance]  # 第一次查询返回余额

        # 执行扣减
        result = await token_service.deduct_tokens(
            user_id=sample_user.id,
            amount=100,
            service_type="ai_chat",
            description="AI 聊天消耗"
        )

        assert result.success == True
        assert result.deducted_amount == 100
        assert result.remaining_balance == 900

    @pytest.mark.asyncio
    async def test_deduct_tokens_insufficient_balance(self, token_service, mock_db, sample_user):
        """测试余额不足"""
        mock_balance = Mock()
        mock_balance.remaining_tokens = 50

        mock_db.query().filter().first.side_effect = [mock_balance]

        with pytest.raises(Exception) as exc_info:
            await token_service.deduct_tokens(
                user_id=sample_user.id,
                amount=100,
                service_type="ai_chat"
            )

        assert "insufficient" in str(
            exc_info.value).lower() or "余额不足" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deduct_tokens_creates_transaction(self, token_service, mock_db, sample_user):
        """测试扣减 Token 创建交易记录"""
        mock_balance = Mock()
        mock_balance.remaining_tokens = 1000

        mock_db.query().filter().first.side_effect = [mock_balance]

        await token_service.deduct_tokens(
            user_id=sample_user.id,
            amount=100,
            service_type="ai_chat",
            description="Test deduction"
        )

        # 验证创建了交易记录
        assert mock_db.add.called
        call_args = mock_db.add.call_args[0][0]
        assert isinstance(call_args, TokenTransaction)
        assert call_args.amount == -100  # 扣减为负数
        assert call_args.transaction_type == TransactionType.CONSUMPTION


class TestTokenPackagePurchase:
    """Token 套餐购买测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def token_service(self, mock_db):
        """创建 Token 服务实例"""
        return TokenService(mock_db)

    @pytest.fixture
    def sample_packages(self):
        """创建示例套餐"""
        return {
            "starter": TokenPackage(
                id="starter",
                name="入门版",
                token_amount=500,
                price=9.99,
                currency="USD"
            ),
            "standard": TokenPackage(
                id="standard",
                name="标准版",
                token_amount=1500,
                price=24.99,
                currency="USD"
            ),
            "premium": TokenPackage(
                id="premium",
                name="高级版",
                token_amount=5000,
                price=69.99,
                currency="USD"
            )
        }

    def test_get_package_by_id(self, token_service, sample_packages):
        """测试根据 ID 获取套餐"""
        package = token_service.get_package("starter")

        assert package is not None
        assert package.name == "入门版"
        assert package.token_amount == 500
        assert package.price == 9.99

    def test_get_package_not_found(self, token_service):
        """测试套餐不存在"""
        package = token_service.get_package("non_existent")

        assert package is None

    def test_calculate_package_bonus(self, token_service):
        """测试计算套餐赠送"""
        # 标准版赠送 10%
        bonus_standard = token_service.calculate_package_bonus(1500)
        assert bonus_standard == 150  # 1500 * 0.1

        # 高级版赠送 20%
        bonus_premium = token_service.calculate_package_bonus(5000)
        assert bonus_premium == 1000  # 5000 * 0.2

    @pytest.mark.asyncio
    async def test_purchase_package_success(self, token_service, mock_db):
        """测试购买套餐成功"""
        user_id = "user_123"
        package_id = "starter"

        # Mock 套餐数据
        mock_package = Mock()
        mock_package.token_amount = 500
        mock_package.price = 9.99

        # Mock 用户当前余额
        mock_balance = Mock()
        mock_balance.total_tokens = 100
        mock_balance.remaining_tokens = 80

        mock_db.query().filter().first.side_effect = [
            mock_package, mock_balance]

        # 执行购买
        result = await token_service.purchase_package(user_id, package_id)

        assert result.success == True
        assert result.tokens_added == 500
        assert result.new_balance == 580  # 80 + 500

    @pytest.mark.asyncio
    async def test_purchase_package_invalid_package(self, token_service, mock_db):
        """测试购买不存在的套餐"""
        mock_db.query().filter().first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await token_service.purchase_package("user_123", "invalid_package")

        assert "package not found" in str(
            exc_info.value).lower() or "套餐不存在" in str(exc_info.value)


class TestMonthlyBonusTokens:
    """月度赠送 Token 测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def token_service(self, mock_db):
        """创建 Token 服务实例"""
        return TokenService(mock_db)

    @pytest.mark.asyncio
    async def test_claim_monthly_bonus_eligible(self, token_service, mock_db):
        """测试符合领取条件的月度赠送"""
        user_id = "user_123"

        # Mock 用户许可证（云托管版）
        mock_license = Mock()
        mock_license.license_type = Mock(value="cloud_hosted")
        mock_license.is_active = True

        # Mock 上次领取时间（超过 30 天）
        last_claim = datetime.utcnow() - timedelta(days=35)

        mock_db.query().filter().first.side_effect = [mock_license, last_claim]

        # 执行领取
        result = await token_service.claim_monthly_bonus(user_id)

        assert result.success == True
        assert result.bonus_amount > 0
        assert "claimed" in result.message.lower() or "领取" in result.message

    @pytest.mark.asyncio
    async def test_claim_monthly_bonus_already_claimed(self, token_service, mock_db):
        """测试本月已领取过"""
        user_id = "user_123"

        # Mock 上次领取时间（5 天前）
        last_claim = datetime.utcnow() - timedelta(days=5)

        mock_db.query().filter().first.return_value = last_claim

        result = await token_service.claim_monthly_bonus(user_id)

        assert result.success == False
        assert "already claimed" in str(result).lower() or "已领取" in str(result)

    @pytest.mark.asyncio
    async def test_claim_monthly_bonus_ineligible_license(self, token_service, mock_db):
        """测试许可证类型不符合"""
        user_id = "user_123"

        # Mock 开源版许可证
        mock_license = Mock()
        mock_license.license_type = Mock(value="open_source")

        mock_db.query().filter().first.return_value = mock_license

        result = await token_service.claim_monthly_bonus(user_id)

        assert result.success == False
        assert "ineligible" in str(result).lower() or "不符合条件" in str(result)


class TestTokenTransactionHistory:
    """Token 交易历史测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def token_service(self, mock_db):
        """创建 Token 服务实例"""
        return TokenService(mock_db)

    def test_get_transaction_history_all_types(self, token_service, mock_db):
        """测试获取所有类型的交易历史"""
        user_id = "user_123"

        # Mock 交易记录列表
        mock_transactions = [
            Mock(id=1, amount=500, transaction_type="purchase"),
            Mock(id=2, amount=-50, transaction_type="consumption"),
            Mock(id=3, amount=100, transaction_type="bonus"),
            Mock(id=4, amount=-30, transaction_type="consumption")
        ]

        mock_db.query().filter().order_by().limit().all.return_value = mock_transactions

        transactions = token_service.get_transaction_history(user_id, limit=10)

        assert len(transactions) == 4
        assert transactions[0].amount == 500
        assert transactions[2].amount == 100

    def test_get_transaction_history_by_type(self, token_service, mock_db):
        """测试按类型筛选交易历史"""
        user_id = "user_123"

        # 只查询消费记录
        mock_consumptions = [
            Mock(id=2, amount=-50, transaction_type="consumption"),
            Mock(id=4, amount=-30, transaction_type="consumption")
        ]

        mock_db.query().filter().filter().order_by().all.return_value = mock_consumptions

        transactions = token_service.get_transaction_history(
            user_id,
            transaction_type="consumption",
            limit=10
        )

        assert len(transactions) == 2
        assert all(t.transaction_type == "consumption" for t in transactions)

    def test_get_transaction_history_pagination(self, token_service, mock_db):
        """测试分页获取交易历史"""
        user_id = "user_123"

        # Mock 总共 50 条记录
        mock_transactions_page1 = [Mock(id=i) for i in range(1, 11)]

        mock_db.query().filter().order_by().offset(0).limit(
            10).all.return_value = mock_transactions_page1

        transactions = token_service.get_transaction_history(
            user_id, offset=0, limit=10)

        assert len(transactions) == 10
        assert transactions[0].id == 1
        assert transactions[9].id == 10


class TestTokenStatistics:
    """Token 统计信息测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def token_service(self, mock_db):
        """创建 Token 服务实例"""
        return TokenService(mock_db)

    def test_get_user_token_statistics(self, token_service, mock_db):
        """测试获取用户 Token 统计"""
        user_id = "user_123"

        # Mock 统计数据
        mock_stats = Mock()
        mock_stats.total_purchased = 2000
        mock_stats.total_consumed = 800
        mock_stats.total_bonus = 300
        mock_stats.current_balance = 1500

        mock_db.query().filter().first.return_value = mock_stats

        stats = token_service.get_user_statistics(user_id)

        assert stats.total_purchased == 2000
        assert stats.total_consumed == 800
        assert stats.total_bonus == 300
        assert stats.current_balance == 1500
        assert stats.net_spent == 1200  # 2000 - 800

    def test_calculate_usage_trend(self, token_service):
        """测试计算使用趋势"""
        # Mock 过去 7 天的使用数据
        past_7_days = [100, 120, 80, 150, 200, 180, 160]

        trend = token_service.calculate_usage_trend(past_7_days)

        assert trend.direction == "increasing" or trend.direction == "stable"
        assert trend.average_daily_usage > 0
        assert trend.estimated_monthly_usage > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
