"""
支付网关集成服务
支持多种第三方支付平台的统一接口
"""

from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import logging
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """支付网关抽象基类"""

    @abstractmethod
    async def create_payment(
        self, amount: float, order_id: str, **kwargs
    ) -> Dict[str, Any]:
        """创建支付"""

    @abstractmethod
    async def query_payment(self, payment_id: str) -> Dict[str, Any]:
        """查询支付状态"""

    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """退款"""

    @abstractmethod
    def verify_callback(self, data: Dict[str, Any], signature: str) -> bool:
        """验证回调签名"""


class WeChatPayGateway(PaymentGateway):
    """微信支付网关"""

    def __init__(self, app_id: str, mch_id: str, api_key: str, notify_url: str):
        self.app_id = app_id
        self.mch_id = mch_id
        self.api_key = api_key
        self.notify_url = notify_url

    async def create_payment(
        self, amount: float, order_id: str, **kwargs
    ) -> Dict[str, Any]:
        """创建微信支付"""
        try:
            # 生成商户订单号
            out_trade_no = f"wx_{order_id}_{int(datetime.now().timestamp())}"

            # 构造支付参数（模拟）
            payment_params = {
                "appid": self.app_id,
                "mch_id": self.mch_id,
                "out_trade_no": out_trade_no,
                "total_fee": int(amount * 100),  # 转换为分
                "notify_url": self.notify_url,
                "trade_type": kwargs.get("trade_type", "JSAPI"),
                "openid": kwargs.get("openid"),  # JSAPI需要
                "body": kwargs.get("body", "商品购买"),
                "nonce_str": self._generate_nonce_str(),
            }

            # 生成签名
            sign = self._generate_signature(payment_params)
            payment_params["sign"] = sign

            # 模拟调用微信统一下单接口
            import random

            if random.random() < 0.95:  # 95%成功率
                return {
                    "success": True,
                    "prepay_id": f"wx{uuid.uuid4().hex}",
                    "out_trade_no": out_trade_no,
                    "code_url": f"https://wxpay.qq.com/example?prepay_id={out_trade_no}",
                    "qr_code": f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAACCCAMAAADQNkiAAAAA1BMVEW10NBjBBbqAAAAH0lEQVRo3u3BAQ0AAADCoPdPbQ43oAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIBLcQ8AAa0jZQAAAABJRU5ErkJggg==",
                }
            else:
                return {
                    "success": False,
                    "error_code": "SYSTEMERROR",
                    "error_message": "微信支付系统错误",
                }

        except Exception as e:
            logger.error(f"微信支付创建失败: {e}")
            return {"success": False, "error_message": str(e)}

    async def query_payment(self, payment_id: str) -> Dict[str, Any]:
        """查询微信支付状态"""
        # 模拟查询逻辑
        import random

        status_map = ["SUCCESS", "NOTPAY", "REFUND", "CLOSED"]
        return {
            "success": True,
            "trade_state": random.choice(status_map),
            "transaction_id": f"wx{uuid.uuid4().hex[:24]}",
            "out_trade_no": payment_id,
        }

    async def refund_payment(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """微信退款"""
        return {
            "success": True,
            "refund_id": f"refund_{uuid.uuid4().hex}",
            "out_refund_no": f"refund_{int(datetime.now().timestamp())}",
            "refund_fee": int(amount * 100),
        }

    def verify_callback(self, data: Dict[str, Any], signature: str) -> bool:
        """验证微信回调签名"""
        try:
            # 重新生成签名进行验证
            calculated_sign = self._generate_signature(data)
            return calculated_sign == signature
        except Exception as e:
            logger.error(f"微信回调签名验证失败: {e}")
            return False

    def _generate_nonce_str(self) -> str:
        """生成随机字符串"""
        return uuid.uuid4().hex[:32]

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 过滤空值并排序
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
        sorted_params = sorted(filtered_params.items(), key=lambda x: x[0])

        # 拼接字符串
        string_a = "&".join([f"{k}={v}" for k, v in sorted_params])
        string_sign_temp = f"{string_a}&key={self.api_key}"

        # MD5签名
        return hashlib.md5(string_sign_temp.encode("utf-8")).hexdigest().upper()


class AlipayGateway(PaymentGateway):
    """支付宝支付网关"""

    def __init__(self, app_id: str, private_key: str, public_key: str, notify_url: str):
        self.app_id = app_id
        self.private_key = private_key
        self.public_key = public_key
        self.notify_url = notify_url

    async def create_payment(
        self, amount: float, order_id: str, **kwargs
    ) -> Dict[str, Any]:
        """创建支付宝支付"""
        try:
            out_trade_no = f"alipay_{order_id}_{int(datetime.now().timestamp())}"

            biz_content = {
                "out_trade_no": out_trade_no,
                "total_amount": f"{amount:.2f}",
                "subject": kwargs.get("subject", "商品购买"),
                "product_code": "FAST_INSTANT_TRADE_PAY",
            }

            # 模拟调用支付宝接口
            import random

            if random.random() < 0.95:
                return {
                    "success": True,
                    "trade_no": f"alipay{uuid.uuid4().hex[:24]}",
                    "out_trade_no": out_trade_no,
                    "qr_code": "https://qr.alipay.com/bax03431ljhokirwl6mhxda",
                    "payment_url": f"https://openapi.alipay.com/gateway.do?{out_trade_no}",
                }
            else:
                return {
                    "success": False,
                    "sub_code": "ACQ.SYSTEM_ERROR",
                    "sub_msg": "支付宝系统错误",
                }

        except Exception as e:
            logger.error(f"支付宝支付创建失败: {e}")
            return {"success": False, "sub_msg": str(e)}

    async def query_payment(self, payment_id: str) -> Dict[str, Any]:
        """查询支付宝支付状态"""
        import random

        status_map = [
            "TRADE_SUCCESS",
            "WAIT_BUYER_PAY",
            "TRADE_CLOSED",
            "TRADE_FINISHED",
        ]
        return {
            "success": True,
            "trade_status": random.choice(status_map),
            "trade_no": f"alipay{uuid.uuid4().hex[:24]}",
            "out_trade_no": payment_id,
        }

    async def refund_payment(self, payment_id: str, amount: float) -> Dict[str, Any]:
        """支付宝退款"""
        return {
            "success": True,
            "trade_no": f"refund_alipay{uuid.uuid4().hex[:20]}",
            "out_request_no": f"refund_{int(datetime.now().timestamp())}",
            "refund_amount": f"{amount:.2f}",
        }

    def verify_callback(self, data: Dict[str, Any], signature: str) -> bool:
        """验证支付宝回调签名"""
        try:
            # 支付宝验签逻辑（简化版）
            # 实际应用中需要使用支付宝提供的SDK
            return True  # 模拟验证通过
        except Exception as e:
            logger.error(f"支付宝回调签名验证失败: {e}")
            return False


class PaymentGatewayFactory:
    """支付网关工厂类"""

    _gateways = {}

    @classmethod
    def register_gateway(cls, payment_method: str, gateway: PaymentGateway):
        """注册支付网关"""
        cls._gateways[payment_method] = gateway

    @classmethod
    def get_gateway(cls, payment_method: str) -> Optional[PaymentGateway]:
        """获取支付网关"""
        return cls._gateways.get(payment_method)

    @classmethod
    def create_payment(
        cls, payment_method: str, amount: float, order_id: str, **kwargs
    ) -> Dict[str, Any]:
        """创建支付"""
        gateway = cls.get_gateway(payment_method)
        if not gateway:
            return {
                "success": False,
                "error_message": f"不支持的支付方式: {payment_method}",
            }

        import asyncio

        # 在实际应用中，这里应该是await gateway.create_payment(...)
        # 但由于这是同步上下文，我们直接调用
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                gateway.create_payment(amount, order_id, **kwargs)
            )
            loop.close()
            return result
        except Exception as e:
            return {"success": False, "error_message": str(e)}


# 初始化支付网关
def init_payment_gateways():
    """初始化支付网关配置"""
    # 微信支付网关（模拟配置）
    wechat_gateway = WeChatPayGateway(
        app_id="wx1234567890abcdef",
        mch_id="1234567890",
        api_key="abcdefghijklmnopqrstuvwxyz123456",
        notify_url="https://api.example.com/payments/wechat/callback",
    )

    # 支付宝网关（模拟配置）
    alipay_gateway = AlipayGateway(
        app_id="2021000123456789",
        private_key="-----BEGIN RSA PRIVATE KEY-----\n...",
        public_key="-----BEGIN PUBLIC KEY-----\n...",
        notify_url="https://api.example.com/payments/alipay/callback",
    )

    # 注册网关
    PaymentGatewayFactory.register_gateway("wechat_pay", wechat_gateway)
    PaymentGatewayFactory.register_gateway("alipay", alipay_gateway)

    logger.info("支付网关初始化完成")


# 在模块导入时初始化
init_payment_gateways()
