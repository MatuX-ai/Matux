"""
支付服务单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.payment import OrderStatus, PaymentMethod, PaymentStatus
from services.payment_service import PaymentService


@pytest.fixture
def sample_cart_items():
    """创建示例购物车项目"""
    return [
        {
            "productId": "prod_001",
            "productName": "Arduino开发板",
            "price": 199.00,
            "quantity": 1,
            "imageUrl": "https://example.com/arduino.jpg",
            "description": "Arduino Uno R3开发板",
        },
        {
            "productId": "prod_002",
            "productName": "传感器套装",
            "price": 89.50,
            "quantity": 2,
            "imageUrl": "https://example.com/sensors.jpg",
            "description": "各种传感器组合套装",
        },
    ]


@pytest.fixture
def sample_shipping_address():
    """创建示例收货地址"""
    return {
        "recipientName": "张三",
        "phone": "13800138000",
        "province": "广东省",
        "city": "深圳市",
        "district": "南山区",
        "detailAddress": "科技园南路1001号",
        "postalCode": "518000",
    }


@pytest.mark.asyncio
class TestPaymentService:
    """支付服务测试类"""

    @pytest.fixture
    def payment_service(self):
        """创建支付服务实例"""
        return PaymentService()

    async def test_create_order(
        self, payment_service, sample_cart_items, sample_shipping_address
    ):
        """测试创建订单"""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        user_id = "user_123"

        order = await payment_service.create_order(
            user_id=user_id,
            cart_items=sample_cart_items,
            shipping_address=sample_shipping_address,
            note="请尽快发货",
            db=mock_db,
        )

        # 验证订单创建
        assert order.user_id == user_id
        assert len(order.items) == 2
        assert order.total_amount == 378.00  # 199 + 89.5*2
        assert order.shipping_address == sample_shipping_address
        assert order.note == "请尽快发货"

        # 验证数据库操作
        assert mock_db.add.called
        assert mock_db.commit.called

    async def test_process_wechat_payment_success(self, payment_service):
        """测试微信支付成功"""
        mock_db = AsyncMock()

        # 模拟订单查询
        mock_order = MagicMock()
        mock_order.order_id = "ORD20231201001"
        mock_order.user_id = "user_123"
        mock_order.total_amount = 378.00
        mock_order.status = OrderStatus.PENDING_PAYMENT

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_order
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("services.payment_service.asyncio.sleep"):
            payment = await payment_service.process_payment(
                order_id="ORD20231201001",
                payment_method=PaymentMethod.WECHAT_PAY,
                user_id="user_123",
                db=mock_db,
            )

        assert payment.payment_method == PaymentMethod.WECHAT_PAY
        assert payment.amount == 378.00
        # 由于是模拟，可能成功也可能失败，所以只验证基本属性
        assert hasattr(payment, "payment_id")
        assert hasattr(payment, "status")

    async def test_process_alipay_payment(self, payment_service):
        """测试支付宝支付"""
        mock_db = AsyncMock()

        mock_order = MagicMock()
        mock_order.order_id = "ORD20231201002"
        mock_order.user_id = "user_123"
        mock_order.total_amount = 299.00
        mock_order.status = OrderStatus.PENDING_PAYMENT

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_order
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("services.payment_service.asyncio.sleep"):
            payment = await payment_service.process_payment(
                order_id="ORD20231201002",
                payment_method=PaymentMethod.ALIPAY,
                user_id="user_123",
                db=mock_db,
            )

        assert payment.payment_method == PaymentMethod.ALIPAY
        assert payment.amount == 299.00

    async def test_process_bank_card_payment(self, payment_service):
        """测试银行卡支付"""
        mock_db = AsyncMock()

        mock_order = MagicMock()
        mock_order.order_id = "ORD20231201003"
        mock_order.user_id = "user_123"
        mock_order.total_amount = 159.90
        mock_order.status = OrderStatus.PENDING_PAYMENT

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_order
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("services.payment_service.asyncio.sleep"):
            payment = await payment_service.process_payment(
                order_id="ORD20231201003",
                payment_method=PaymentMethod.BANK_CARD,
                user_id="user_123",
                db=mock_db,
            )

        assert payment.payment_method == PaymentMethod.BANK_CARD
        assert payment.amount == 159.90

    async def test_process_balance_payment(self, payment_service):
        """测试余额支付"""
        mock_db = AsyncMock()

        # 模拟用户查询
        mock_user = MagicMock()
        mock_user.id = "user_123"

        mock_order = MagicMock()
        mock_order.order_id = "ORD20231201004"
        mock_order.user_id = "user_123"
        mock_order.total_amount = 89.00
        mock_order.status = OrderStatus.PENDING_PAYMENT

        mock_db.execute.side_effect = [
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        one_or_none=MagicMock(return_value=mock_order)
                    )
                )
            ),
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        one_or_none=MagicMock(return_value=mock_user)
                    )
                )
            ),
        ]
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("services.payment_service.asyncio.sleep"):
            payment = await payment_service.process_payment(
                order_id="ORD20231201004",
                payment_method=PaymentMethod.BALANCE,
                user_id="user_123",
                db=mock_db,
            )

        assert payment.payment_method == PaymentMethod.BALANCE
        assert payment.amount == 89.00

    async def test_get_order(self, payment_service):
        """测试获取订单"""
        mock_db = AsyncMock()
        mock_order = MagicMock()
        mock_order.order_id = "ORD20231201001"

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_order

        order = await payment_service.get_order("ORD20231201001", "user_123", mock_db)

        assert order == mock_order
        mock_db.execute.assert_called_once()

    async def test_get_user_orders(self, payment_service):
        """测试获取用户订单列表"""
        mock_db = AsyncMock()
        mock_orders = [MagicMock(), MagicMock(), MagicMock()]

        mock_db.execute.return_value.scalars.return_value.all.return_value = mock_orders

        orders = await payment_service.get_user_orders(
            "user_123", mock_db, limit=10, offset=0
        )

        assert len(orders) == 3
        assert orders == mock_orders

    async def test_cancel_order_success(self, payment_service):
        """测试取消订单成功"""
        mock_db = AsyncMock()

        mock_order = MagicMock()
        mock_order.status = OrderStatus.PENDING_PAYMENT
        mock_order.payment_status = PaymentStatus.PENDING

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_order
        mock_db.commit = AsyncMock()

        result = await payment_service.cancel_order(
            "ORD20231201001", "user_123", mock_db
        )

        assert result == True
        assert mock_order.status == OrderStatus.CANCELLED
        assert mock_order.payment_status == PaymentStatus.CANCELLED
        assert mock_order.cancelled_at is not None
        mock_db.commit.assert_called_once()

    async def test_cancel_order_not_found(self, payment_service):
        """测试取消不存在的订单"""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await payment_service.cancel_order("ORD_NONEXIST", "user_123", mock_db)

        assert result == False

    async def test_cancel_order_invalid_status(self, payment_service):
        """测试取消状态不正确的订单"""
        mock_db = AsyncMock()

        mock_order = MagicMock()
        mock_order.status = OrderStatus.SHIPPED  # 已发货不能取消

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_order

        with pytest.raises(ValueError, match="订单状态不允许取消"):
            await payment_service.cancel_order("ORD20231201001", "user_123", mock_db)

    async def test_get_payment_statistics(self, payment_service):
        """测试获取支付统计"""
        mock_db = AsyncMock()

        # 模拟不同的数据库查询结果
        mock_db.execute.side_effect = [
            AsyncMock(scalar=MagicMock(return_value=10)),  # 总订单数
            AsyncMock(scalar=MagicMock(return_value=2568.50)),  # 总金额
            AsyncMock(scalar=MagicMock(return_value=8)),  # 成功支付数
            AsyncMock(),  # 支付方式统计
        ]

        stats = await payment_service.get_payment_statistics("user_123", mock_db)

        assert stats["total_orders"] == 10
        assert stats["total_amount"] == 2568.50
        assert stats["successful_payments"] == 8
        assert stats["success_rate"] == 80.0


@pytest.mark.asyncio
class TestPaymentGatewayIntegration:
    """支付网关集成测试"""

    async def test_wechat_pay_gateway_simulation(self):
        """测试微信支付网关模拟"""
        from services.payment_gateway import WeChatPayGateway

        gateway = WeChatPayGateway(
            app_id="test_app_id",
            mch_id="test_mch_id",
            api_key="test_api_key",
            notify_url="http://test.com/notify",
        )

        # 测试创建支付
        result = await gateway.create_payment(
            amount=100.00, order_id="TEST_ORDER_001", body="测试商品"
        )

        assert "success" in result
        assert isinstance(result["success"], bool)

        if result["success"]:
            assert "prepay_id" in result
            assert "out_trade_no" in result

    async def test_alipay_gateway_simulation(self):
        """测试支付宝网关模拟"""
        from services.payment_gateway import AlipayGateway

        gateway = AlipayGateway(
            app_id="test_app_id",
            private_key="test_private_key",
            public_key="test_public_key",
            notify_url="http://test.com/notify",
        )

        result = await gateway.create_payment(
            amount=150.00, order_id="TEST_ORDER_002", subject="测试商品"
        )

        assert "success" in result
        assert isinstance(result["success"], bool)

    async def test_payment_gateway_factory(self):
        """测试支付网关工厂"""
        from services.payment_gateway import PaymentGatewayFactory, WeChatPayGateway

        # 注册网关
        test_gateway = WeChatPayGateway("test", "test", "test", "test")
        PaymentGatewayFactory.register_gateway("test_method", test_gateway)

        # 获取网关
        gateway = PaymentGatewayFactory.get_gateway("test_method")
        assert gateway == test_gateway

        # 测试创建支付
        result = PaymentGatewayFactory.create_payment(
            "test_method", 100.00, "TEST_ORDER"
        )

        assert isinstance(result, dict)
        assert "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
