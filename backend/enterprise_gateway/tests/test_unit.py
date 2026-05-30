"""
企业API网关单元测试
测试各个核心组件的功能正确性
"""

from datetime import datetime, timedelta
import unittest
from unittest.mock import Mock, patch

from models.enterprise_models import DeviceWhitelist, EnterpriseClient
from services.device_whitelist_service import DeviceWhitelistService
from services.enterprise_oauth_service import EnterpriseOAuthService
from utils.jwt_utils import JWTUtil
from utils.security_utils import SecurityUtil


class TestJWTUtil(unittest.TestCase):
    """JWT工具测试类"""

    def setUp(self):
        self.jwt_util = JWTUtil()

    def test_generate_client_secret(self):
        """测试客户端密钥生成"""
        secret1 = self.jwt_util.generate_client_secret()
        secret2 = self.jwt_util.generate_client_secret()

        # 验证长度
        self.assertEqual(len(secret1), 32)
        self.assertEqual(len(secret2), 32)

        # 验证唯一性
        self.assertNotEqual(secret1, secret2)

        # 验证包含预期字符类型
        self.assertTrue(any(c.isalpha() for c in secret1))
        self.assertTrue(any(c.isdigit() for c in secret1))
        self.assertTrue(any(c in "!@#$%^&*" for c in secret1))

    def test_generate_client_id(self):
        """测试客户端ID生成"""
        client_id1 = self.jwt_util.generate_client_id()
        client_id2 = self.jwt_util.generate_client_id()

        # 验证格式
        self.assertTrue(client_id1.startswith("ent_"))
        self.assertTrue("_" in client_id1)

        # 验证唯一性
        self.assertNotEqual(client_id1, client_id2)

    def test_create_and_verify_token(self):
        """测试令牌创建和验证"""
        data = {"client_id": "test_client", "scope": "api:read"}

        # 创建令牌
        token = self.jwt_util.create_access_token(data)
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

        # 验证令牌
        payload = self.jwt_util.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["client_id"], "test_client")
        self.assertEqual(payload["scope"], "api:read")

        # 验证过期令牌
        expired_token = self.jwt_util.create_access_token(
            data, timedelta(seconds=-1)  # 立即过期
        )
        expired_payload = self.jwt_util.verify_token(expired_token)
        self.assertIsNone(expired_payload)

    def test_extract_client_id(self):
        """测试从令牌提取客户端ID"""
        data = {"client_id": "extract_test_client"}
        token = self.jwt_util.create_access_token(data)

        extracted_id = self.jwt_util.extract_client_id(token)
        self.assertEqual(extracted_id, "extract_test_client")

        # 测试无效令牌
        invalid_token = "invalid.token.string"
        extracted_id = self.jwt_util.extract_client_id(invalid_token)
        self.assertIsNone(extracted_id)


class TestSecurityUtil(unittest.TestCase):
    """安全工具测试类"""

    def setUp(self):
        self.security_util = SecurityUtil()

    def test_validate_ip_address(self):
        """测试IP地址验证"""
        # 有效的IPv4地址
        self.assertTrue(self.security_util.validate_ip_address("192.168.1.1"))
        self.assertTrue(self.security_util.validate_ip_address("255.255.255.255"))

        # 无效的IPv4地址
        self.assertFalse(self.security_util.validate_ip_address("256.1.1.1"))
        self.assertFalse(self.security_util.validate_ip_address("192.168.1"))
        self.assertFalse(self.security_util.validate_ip_address("invalid.ip"))

        # IPv6地址测试（简化）
        self.assertTrue(self.security_util.validate_ip_address("2001:db8::1"))
        self.assertTrue(self.security_util.validate_ip_address("::1"))

    def test_validate_mac_address(self):
        """测试MAC地址验证"""
        # 有效的MAC地址格式
        self.assertTrue(self.security_util.validate_mac_address("AA:BB:CC:DD:EE:FF"))
        self.assertTrue(self.security_util.validate_mac_address("aa-bb-cc-dd-ee-ff"))
        self.assertTrue(self.security_util.validate_mac_address("AABB.CCDD.EEFF"))
        self.assertTrue(self.security_util.validate_mac_address("aabbccddeeff"))

        # 无效的MAC地址
        self.assertFalse(self.security_util.validate_mac_address("invalid-mac"))
        self.assertFalse(
            self.security_util.validate_mac_address("GG:HH:II:JJ:KK:LL")
        )  # 包含无效字符

    def test_generate_device_fingerprint(self):
        """测试设备指纹生成"""
        fingerprint1 = self.security_util.generate_device_fingerprint(
            "192.168.1.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        fingerprint2 = self.security_util.generate_device_fingerprint(
            "192.168.1.2", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        # 验证格式（SHA256哈希）
        self.assertEqual(len(fingerprint1), 64)
        self.assertEqual(len(fingerprint2), 64)

        # 相同输入应该产生相同指纹
        fingerprint3 = self.security_util.generate_device_fingerprint(
            "192.168.1.1", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        self.assertEqual(fingerprint1, fingerprint3)

        # 不同输入应该产生不同指纹
        self.assertNotEqual(fingerprint1, fingerprint2)

    def test_sanitize_input(self):
        """测试输入清理"""
        # 正常输入
        clean_input = self.security_util.sanitize_input("normal input")
        self.assertEqual(clean_input, "normal input")

        # 包含危险字符的输入
        dangerous_input = self.security_util.sanitize_input(
            "<script>alert('xss')</script>"
        )
        self.assertEqual(dangerous_input, "scriptalertxss/script")

        # 长输入截断
        long_input = "a" * 1500
        sanitized = self.security_util.sanitize_input(long_input)
        self.assertEqual(len(sanitized), 1000)

    def test_hmac_signature(self):
        """测试HMAC签名"""
        message = "test message"
        secret = "test secret"

        # 生成签名
        signature = self.security_util.calculate_hmac_signature(message, secret)
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex digest

        # 验证签名
        is_valid = self.security_util.verify_hmac_signature(message, signature, secret)
        self.assertTrue(is_valid)

        # 验证无效签名
        is_valid = self.security_util.verify_hmac_signature(message, "invalid", secret)
        self.assertFalse(is_valid)


class TestEnterpriseModels(unittest.TestCase):
    """企业数据模型测试类"""

    def test_enterprise_client_model(self):
        """测试企业客户端模型"""
        client = EnterpriseClient(
            client_name="Test Company",
            client_id="ent_test_123",
            redirect_uris="https://test.com/callback",
            api_quota_limit=1000,
            contact_email="admin@test.com",
        )

        # 测试基本属性
        self.assertEqual(client.client_name, "Test Company")
        self.assertEqual(client.client_id, "ent_test_123")
        self.assertEqual(client.api_quota_limit, 1000)
        self.assertEqual(client.current_usage, 0)

        # 测试配额检查
        self.assertTrue(client.has_quota_available())

        # 测试使用计数
        client.increment_usage()
        self.assertEqual(client.current_usage, 1)

        # 测试字典转换
        client_dict = client.to_dict()
        self.assertIn("id", client_dict)
        self.assertIn("client_name", client_dict)
        self.assertIn("client_id", client_dict)

    def test_device_whitelist_model(self):
        """测试设备白名单模型"""
        device = DeviceWhitelist(
            device_id="device_123",
            device_name="Test Device",
            ip_address="192.168.1.100",
            is_approved=True,
        )

        # 测试基本属性
        self.assertEqual(device.device_id, "device_123")
        self.assertEqual(device.device_name, "Test Device")
        self.assertTrue(device.is_approved)

        # 测试有效性检查
        self.assertTrue(device.is_valid())

        # 测试过期检查
        device.expires_at = datetime.utcnow() - timedelta(days=1)
        self.assertTrue(device.is_expired())
        self.assertFalse(device.is_valid())

        # 测试字典转换
        device_dict = device.to_dict()
        self.assertIn("id", device_dict)
        self.assertIn("device_id", device_dict)
        self.assertIn("is_approved", device_dict)


class TestEnterpriseOAuthService(unittest.TestCase):
    """企业OAuth服务测试类"""

    def setUp(self):
        self.oauth_service = EnterpriseOAuthService()
        self.mock_db = Mock()

    @patch("services.enterprise_oauth_service.get_db")
    def test_validate_client_credentials(self, mock_get_db):
        """测试客户端凭据验证"""
        mock_get_db.return_value = iter([self.mock_db])

        # 创建模拟客户端
        mock_client = Mock()
        mock_client.is_active = True
        mock_client.verify_client_secret.return_value = True

        self.mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_client
        )

        # 测试有效凭据
        result = self.oauth_service.validate_client_credentials(
            "test_client", "test_secret"
        )
        self.assertTrue(result)

        # 测试无效凭据
        mock_client.verify_client_secret.return_value = False
        result = self.oauth_service.validate_client_credentials(
            "test_client", "wrong_secret"
        )
        self.assertFalse(result)

    def test_jwt_util_integration(self):
        """测试JWT工具集成"""
        # 测试客户端ID生成
        client_id = self.oauth_service.jwt_util.generate_client_id()
        self.assertTrue(client_id.startswith("ent_"))

        # 测试密钥生成
        secret = self.oauth_service.jwt_util.generate_client_secret()
        self.assertEqual(len(secret), 32)


class TestDeviceWhitelistService(unittest.TestCase):
    """设备白名单服务测试类"""

    def setUp(self):
        self.device_service = DeviceWhitelistService()
        self.mock_db = Mock()

    def test_generate_device_id(self):
        """测试设备ID生成"""
        device_id = self.device_service.generate_device_id(
            "192.168.1.1", "Mozilla/5.0 (Test)"
        )

        self.assertIsInstance(device_id, str)
        self.assertEqual(len(device_id), 64)  # SHA256哈希长度


if __name__ == "__main__":
    unittest.main()
