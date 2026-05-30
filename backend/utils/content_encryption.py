"""
内容加密工具集
提供各种内容加密、解密和数字水印功能
"""

import base64
import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

logger = logging.getLogger(__name__)


class ContentEncryptionError(Exception):
    """内容加密异常基类"""


class AES256Encryption:
    """AES-256加密工具"""

    def __init__(self, key: Optional[bytes] = None):
        """
        初始化AES加密器

        Args:
            key: 32字节的加密密钥，如果不提供则自动生成
        """
        if key is None:
            self.key = os.urandom(32)  # 256位密钥
        else:
            if len(key) != 32:
                raise ContentEncryptionError("AES密钥必须是32字节")
            self.key = key

        self.backend = default_backend()

    def encrypt(
        self, data: bytes, associated_data: Optional[bytes] = None
    ) -> Dict[str, str]:
        """
        AES-GCM加密

        Args:
            data: 要加密的数据
            associated_data: 关联数据（不加密但参与认证）

        Returns:
            Dict: 包含加密数据和元数据的字典
        """
        try:
            # 生成随机IV
            iv = os.urandom(12)  # GCM模式推荐12字节IV

            # 创建加密器
            encryptor = Cipher(
                algorithms.AES(self.key), modes.GCM(iv), backend=self.backend
            ).encryptor()

            # 添加关联数据（如果提供）
            if associated_data:
                encryptor.authenticate_additional_data(associated_data)

            # 加密数据
            ciphertext = encryptor.update(data) + encryptor.finalize()

            return {
                "ciphertext": base64.b64encode(ciphertext).decode(),
                "iv": base64.b64encode(iv).decode(),
                "tag": base64.b64encode(encryptor.tag).decode(),
                "associated_data": (
                    base64.b64encode(associated_data).decode()
                    if associated_data
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"AES加密失败: {e}")
            raise ContentEncryptionError(f"加密失败: {str(e)}")

    def decrypt(
        self,
        ciphertext_b64: str,
        iv_b64: str,
        tag_b64: str,
        associated_data_b64: Optional[str] = None,
    ) -> bytes:
        """
        AES-GCM解密

        Args:
            ciphertext_b64: Base64编码的密文
            iv_b64: Base64编码的IV
            tag_b64: Base64编码的认证标签
            associated_data_b64: Base64编码的关联数据

        Returns:
            bytes: 解密后的原始数据
        """
        try:
            # 解码Base64数据
            ciphertext = base64.b64decode(ciphertext_b64)
            iv = base64.b64decode(iv_b64)
            tag = base64.b64decode(tag_b64)
            associated_data = (
                base64.b64decode(associated_data_b64) if associated_data_b64 else None
            )

            # 创建解密器
            decryptor = Cipher(
                algorithms.AES(self.key), modes.GCM(iv, tag), backend=self.backend
            ).decryptor()

            # 添加关联数据（如果提供）
            if associated_data:
                decryptor.authenticate_additional_data(associated_data)

            # 解密数据
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext

        except Exception as e:
            logger.error(f"AES解密失败: {e}")
            raise ContentEncryptionError(f"解密失败: {str(e)}")

    def get_key(self) -> bytes:
        """获取加密密钥"""
        return self.key


class RSAEncryption:
    """RSA非对称加密工具"""

    def __init__(
        self,
        private_key: Optional[rsa.RSAPrivateKey] = None,
        public_key: Optional[rsa.RSAPublicKey] = None,
    ):
        """
        初始化RSA加密器

        Args:
            private_key: 私钥
            public_key: 公钥
        """
        self.backend = default_backend()

        if private_key is None and public_key is None:
            # 生成新的密钥对
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=self.backend
            )
            self.public_key = self.private_key.public_key()
        else:
            self.private_key = private_key
            self.public_key = public_key

    def encrypt(self, data: bytes) -> str:
        """
        RSA加密（使用公钥）

        Args:
            data: 要加密的数据

        Returns:
            str: Base64编码的加密数据
        """
        if not self.public_key:
            raise ContentEncryptionError("没有可用的公钥进行加密")

        try:
            # RSA-OAEP加密
            encrypted = self.public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return base64.b64encode(encrypted).decode()

        except Exception as e:
            logger.error(f"RSA加密失败: {e}")
            raise ContentEncryptionError(f"RSA加密失败: {str(e)}")

    def decrypt(self, encrypted_data_b64: str) -> bytes:
        """
        RSA解密（使用私钥）

        Args:
            encrypted_data_b64: Base64编码的加密数据

        Returns:
            bytes: 解密后的数据
        """
        if not self.private_key:
            raise ContentEncryptionError("没有可用的私钥进行解密")

        try:
            encrypted_data = base64.b64decode(encrypted_data_b64)

            decrypted = self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return decrypted

        except Exception as e:
            logger.error(f"RSA解密失败: {e}")
            raise ContentEncryptionError(f"RSA解密失败: {str(e)}")

    def sign(self, data: bytes) -> str:
        """
        RSA签名

        Args:
            data: 要签名的数据

        Returns:
            str: Base64编码的签名
        """
        if not self.private_key:
            raise ContentEncryptionError("没有可用的私钥进行签名")

        try:
            signature = self.private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"RSA签名失败: {e}")
            raise ContentEncryptionError(f"RSA签名失败: {str(e)}")

    def verify(self, data: bytes, signature_b64: str) -> bool:
        """
        RSA签名验证

        Args:
            data: 原始数据
            signature_b64: Base64编码的签名

        Returns:
            bool: 签名是否有效
        """
        if not self.public_key:
            raise ContentEncryptionError("没有可用的公钥进行验证")

        try:
            signature = base64.b64decode(signature_b64)

            self.public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            return True

        except Exception:
            return False

    def get_public_key_pem(self) -> str:
        """获取PEM格式的公钥"""
        if not self.public_key:
            raise ContentEncryptionError("没有可用的公钥")

        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem.decode()

    def get_private_key_pem(self, password: Optional[str] = None) -> str:
        """获取PEM格式的私钥"""
        if not self.private_key:
            raise ContentEncryptionError("没有可用的私钥")

        encryption_algorithm = (
            serialization.BestAvailableEncryption(password.encode())
            if password
            else serialization.NoEncryption()
        )

        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm,
        )
        return pem.decode()


class DigitalWatermark:
    """数字水印工具"""

    def __init__(self):
        self.wm_methods = {
            "text": self._embed_text_watermark,
            "invisible": self._embed_invisible_watermark,
            "robust": self._embed_robust_watermark,
        }

    def embed_watermark(
        self, content: bytes, watermark_data: Dict[str, Any], method: str = "text"
    ) -> bytes:
        """
        嵌入数字水印

        Args:
            content: 原始内容
            watermark_data: 水印数据
            method: 水印方法 ('text', 'invisible', 'robust')

        Returns:
            bytes: 带水印的内容
        """
        if method not in self.wm_methods:
            raise ContentEncryptionError(f"不支持的水印方法: {method}")

        try:
            return self.wm_methods[method](content, watermark_data)
        except Exception as e:
            logger.error(f"水印嵌入失败: {e}")
            raise ContentEncryptionError(f"水印嵌入失败: {str(e)}")

    def _embed_text_watermark(
        self, content: bytes, watermark_data: Dict[str, Any]
    ) -> bytes:
        """嵌入文本水印（简单实现）"""
        try:
            watermark_str = json.dumps(watermark_data, separators=(",", ":"))
            watermark_bytes = watermark_str.encode()

            # 在内容末尾添加水印标识
            separator = b"\x00WATERMARK\x00"
            watermarked_content = content + separator + watermark_bytes

            return watermarked_content
        except Exception as e:
            raise ContentEncryptionError(f"文本水印嵌入失败: {str(e)}")

    def _embed_invisible_watermark(
        self, content: bytes, watermark_data: Dict[str, Any]
    ) -> bytes:
        """嵌入不可见水印（LSB隐写术）"""
        try:
            # 简化的LSB水印嵌入
            watermark_str = json.dumps(watermark_data)
            watermark_binary = "".join(format(ord(c), "08b") for c in watermark_str)

            # 将水印数据嵌入到内容的最低有效位
            content_list = list(content)
            for i, bit in enumerate(watermark_binary[: len(content_list)]):
                # 修改最低位
                if bit == "1":
                    content_list[i] = content_list[i] | 1
                else:
                    content_list[i] = content_list[i] & 0xFE

            return bytes(content_list)
        except Exception as e:
            raise ContentEncryptionError(f"不可见水印嵌入失败: {str(e)}")

    def _embed_robust_watermark(
        self, content: bytes, watermark_data: Dict[str, Any]
    ) -> bytes:
        """嵌入鲁棒水印（DCT域）"""
        try:
            # 这里实现简化的频域水印
            # 实际应用中需要更复杂的DCT变换
            import numpy as np

            # 将内容转换为numpy数组
            content_array = np.frombuffer(content, dtype=np.uint8)

            # 生成伪随机序列作为水印
            np.random.seed(hash(str(watermark_data)) % (2**32))
            watermark_length = min(len(content_array) // 8, 1000)
            watermark_sequence = np.random.randint(0, 2, watermark_length)

            # 在中频系数中嵌入水印
            for i, bit in enumerate(watermark_sequence):
                idx = len(content_array) // 4 + i * 8
                if idx < len(content_array):
                    if bit == 1:
                        content_array[idx] = min(255, content_array[idx] + 1)
                    else:
                        content_array[idx] = max(0, content_array[idx] - 1)

            return content_array.tobytes()
        except ImportError:
            # 如果没有numpy，回退到简单方法
            return self._embed_text_watermark(content, watermark_data)
        except Exception as e:
            raise ContentEncryptionError(f"鲁棒水印嵌入失败: {str(e)}")

    def extract_watermark(
        self, watermarked_content: bytes, method: str = "text"
    ) -> Optional[Dict[str, Any]]:
        """提取数字水印"""
        try:
            if method == "text":
                return self._extract_text_watermark(watermarked_content)
            elif method == "invisible":
                return self._extract_invisible_watermark(watermarked_content)
            elif method == "robust":
                return self._extract_robust_watermark(watermarked_content)
            else:
                raise ContentEncryptionError(f"不支持的水印提取方法: {method}")
        except Exception as e:
            logger.error(f"水印提取失败: {e}")
            return None

    def _extract_text_watermark(self, content: bytes) -> Optional[Dict[str, Any]]:
        """提取文本水印"""
        try:
            separator = b"\x00WATERMARK\x00"
            parts = content.split(separator)
            if len(parts) >= 2:
                watermark_bytes = parts[-1]
                return json.loads(watermark_bytes.decode())
            return None
        except Exception:
            return None

    def _extract_invisible_watermark(self, content: bytes) -> Optional[Dict[str, Any]]:
        """提取不可见水印"""
        try:
            # 提取LSB信息
            extracted_bits = []
            for byte in content[:1000]:  # 限制提取长度
                extracted_bits.append(str(byte & 1))

            watermark_binary = "".join(extracted_bits)
            # 转换为字符（简化处理）
            watermark_chars = []
            for i in range(0, len(watermark_binary) - 8, 8):
                char_bits = watermark_binary[i : i + 8]
                char_val = int(char_bits, 2)
                if 32 <= char_val <= 126:  # 可打印字符
                    watermark_chars.append(chr(char_val))

            watermark_str = "".join(watermark_chars)
            if watermark_str.startswith("{") and watermark_str.endswith("}"):
                return json.loads(watermark_str)
            return None
        except Exception:
            return None

    def _extract_robust_watermark(self, content: bytes) -> Optional[Dict[str, Any]]:
        """提取鲁棒水印"""
        # 简化实现，实际应用中需要DCT反变换
        return self._extract_text_watermark(content)


class ContentHasher:
    """内容哈希工具"""

    @staticmethod
    def hash_content(content: bytes, algorithm: str = "sha256") -> str:
        """
        对内容进行哈希

        Args:
            content: 内容数据
            algorithm: 哈希算法 ('sha256', 'sha512', 'md5')

        Returns:
            str: 十六进制哈希值
        """
        try:
            if algorithm == "sha256":
                hasher = hashlib.sha256()
            elif algorithm == "sha512":
                hasher = hashlib.sha512()
            elif algorithm == "md5":
                hasher = hashlib.md5()
            else:
                raise ContentEncryptionError(f"不支持的哈希算法: {algorithm}")

            hasher.update(content)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"内容哈希失败: {e}")
            raise ContentEncryptionError(f"哈希失败: {str(e)}")

    @staticmethod
    def verify_hash(
        content: bytes, expected_hash: str, algorithm: str = "sha256"
    ) -> bool:
        """
        验证内容哈希

        Args:
            content: 内容数据
            expected_hash: 期望的哈希值
            algorithm: 哈希算法

        Returns:
            bool: 哈希是否匹配
        """
        try:
            actual_hash = ContentHasher.hash_content(content, algorithm)
            return actual_hash.lower() == expected_hash.lower()
        except Exception:
            return False


# 便捷函数
def create_encryption_key() -> str:
    """创建新的Fernet加密密钥"""
    return Fernet.generate_key().decode()


def encrypt_content_simple(content: bytes, key: str) -> str:
    """简单的内容加密（使用Fernet）"""
    try:
        f = Fernet(key.encode())
        encrypted = f.encrypt(content)
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        raise ContentEncryptionError(f"简单加密失败: {str(e)}")


def decrypt_content_simple(encrypted_b64: str, key: str) -> bytes:
    """简单的内容解密（使用Fernet）"""
    try:
        f = Fernet(key.encode())
        encrypted = base64.b64decode(encrypted_b64)
        return f.decrypt(encrypted)
    except Exception as e:
        raise ContentEncryptionError(f"简单解密失败: {str(e)}")
