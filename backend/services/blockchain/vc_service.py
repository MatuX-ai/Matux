"""
可验证凭证服务
处理W3C可验证凭证的创建、验证和管理
"""

import base64
from datetime import datetime, timedelta
import hashlib
import json
import logging
from typing import Any, Dict, List

from cryptography.hazmat.primitives.asymmetric import ed25519

from models.verifiable_credential import (
    CredentialStatusType,
    CredentialSubject,
    SkillCertificateCredential,
    VCProof,
    VerifiableCredential,
)

logger = logging.getLogger(__name__)


class VCCryptoService:
    """凭证加密服务"""

    @staticmethod
    def generate_ed25519_keypair() -> tuple[bytes, bytes]:
        """
        生成Ed25519密钥对

        Returns:
            (private_key, public_key) 密钥对
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return (private_key.private_bytes_raw(), public_key.public_bytes_raw())

    @staticmethod
    def sign_vc(vc_json: str, private_key_bytes: bytes) -> str:
        """
        对凭证进行签名

        Args:
            vc_json: 凭证JSON字符串
            private_key_bytes: 私钥字节

        Returns:
            JWS签名
        """
        try:
            # 创建私钥对象
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                private_key_bytes
            )

            # 计算签名
            signature = private_key.sign(vc_json.encode("utf-8"))

            # 构造JWS（简化版）
            header = '{"alg":"EdDSA"}'
            payload = (
                base64.urlsafe_b64encode(vc_json.encode("utf-8"))
                .decode("utf-8")
                .rstrip("=")
            )
            sig = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

            return f"{header}.{payload}.{sig}"

        except Exception as e:
            logger.error(f"凭证签名失败: {e}")
            raise Exception(f"签名失败: {str(e)}")

    @staticmethod
    def verify_vc_signature(
        vc_json: str, signature: str, public_key_bytes: bytes
    ) -> bool:
        """
        验证凭证签名

        Args:
            vc_json: 凭证JSON字符串
            signature: JWS签名
            public_key_bytes: 公钥字节

        Returns:
            验证结果
        """
        try:
            # 解析JWS
            parts = signature.split(".")
            if len(parts) != 3:
                return False

            header, payload, sig = parts

            # 验证payload匹配
            expected_payload = (
                base64.urlsafe_b64encode(vc_json.encode("utf-8"))
                .decode("utf-8")
                .rstrip("=")
            )
            if payload != expected_payload:
                return False

            # 创建公钥对象
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)

            # 解码签名
            sig_bytes = base64.urlsafe_b64decode(sig + "=" * (4 - len(sig) % 4))

            # 验证签名
            public_key.verify(sig_bytes, vc_json.encode("utf-8"))
            return True

        except Exception:
            return False


class VerifiableCredentialService:
    """可验证凭证服务"""

    def __init__(self):
        self.crypto_service = VCCryptoService()
        # 在实际应用中，这里应该从安全存储中获取密钥
        self._issuer_private_key = None
        self._issuer_public_key = None

    def initialize_issuer_keys(self, private_key_hex: str = None):
        """
        初始化颁发者密钥

        Args:
            private_key_hex: 私钥十六进制字符串（可选）
        """
        if private_key_hex:
            # 从十六进制字符串恢复私钥
            private_key_bytes = bytes.fromhex(private_key_hex)
            public_key = ed25519.Ed25519PrivateKey.from_private_bytes(
                private_key_bytes
            ).public_key()
            public_key_bytes = public_key.public_bytes_raw()
        else:
            # 生成新的密钥对
            private_key_bytes, public_key_bytes = (
                self.crypto_service.generate_ed25519_keypair()
            )

        self._issuer_private_key = private_key_bytes
        self._issuer_public_key = public_key_bytes

        logger.info("颁发者密钥初始化完成")
        return private_key_bytes.hex()

    def create_skill_certificate(
        self,
        holder_did: str,
        issuer_did: str,
        skill_name: str,
        skill_level: str,
        evidence: List[str] = None,
        validity_days: int = 730,  # 默认2年
        **kwargs,
    ) -> VerifiableCredential:
        """
        创建技能证书凭证

        Args:
            holder_did: 持有者DID
            issuer_did: 颁发者DID
            skill_name: 技能名称
            skill_level: 技能等级
            evidence: 证明材料列表
            validity_days: 有效期天数
            **kwargs: 其他凭证属性

        Returns:
            VerifiableCredential对象
        """
        if not self._issuer_private_key:
            raise Exception("颁发者密钥未初始化")

        # 创建凭证主体
        subject_data = {
            "id": holder_did,
            "skill": skill_name,
            "level": skill_level,
        }

        # 添加额外属性
        subject_data.update(kwargs.get("subject_attributes", {}))

        credential_subject = CredentialSubject(**subject_data)

        # 创建凭证
        issuance_date = datetime.now()
        expiration_date = issuance_date + timedelta(days=validity_days)

        vc = SkillCertificateCredential(
            id=f"urn:uuid:{self._generate_uuid()}",
            issuer=issuer_did,
            issuanceDate=issuance_date.isoformat() + "Z",
            expirationDate=expiration_date.isoformat() + "Z",
            credentialSubject=credential_subject,
            skill_name=skill_name,
            skill_level=skill_level,
            evidence=evidence or [],
            issuing_organization=kwargs.get("organization"),
            status=CredentialStatusType.ACTIVE,
        )

        # 生成签名
        vc_json = vc.to_json_ld()
        jws = self.crypto_service.sign_vc(vc_json, self._issuer_private_key)

        # 添加证明
        proof = VCProof(
            type="Ed25519Signature2020",
            created=issuance_date.isoformat() + "Z",
            verificationMethod=f"{issuer_did}#keys-1",
            proofPurpose="assertionMethod",
            jws=jws,
        )

        vc.proof = proof
        return vc

    def verify_credential(self, vc: VerifiableCredential) -> Dict[str, Any]:
        """
        验证凭证

        Args:
            vc: 可验证凭证对象

        Returns:
            验证结果字典
        """
        result = {"valid": False, "errors": [], "warnings": []}

        try:
            # 1. 基本格式验证
            if not vc.id or not vc.issuer or not vc.issuanceDate:
                result["errors"].append("缺少必需字段")
                return result

            # 2. 日期验证
            if vc.is_expired():
                result["errors"].append("凭证已过期")

            # 3. 状态验证
            if vc.status != CredentialStatusType.ACTIVE:
                result["errors"].append(f"凭证状态异常: {vc.status.value}")

            # 4. 签名验证
            if vc.proof and self._issuer_public_key:
                vc_without_proof = vc.copy(update={"proof": None})
                vc_json = vc_without_proof.to_json_ld()

                if not self.crypto_service.verify_vc_signature(
                    vc_json, vc.proof.jws, self._issuer_public_key
                ):
                    result["errors"].append("数字签名验证失败")
            elif vc.proof:
                result["warnings"].append("无法验证签名（缺少公钥）")

            # 5. 上下文验证
            if "https://www.w3.org/2018/credentials/v1" not in vc.context:
                result["warnings"].append("缺少标准VC上下文")

            result["valid"] = len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"验证过程出错: {str(e)}")

        return result

    def revoke_credential(
        self, vc: VerifiableCredential, reason: str = ""
    ) -> VerifiableCredential:
        """
        撤销凭证

        Args:
            vc: 要撤销的凭证
            reason: 撤销原因

        Returns:
            更新后的凭证
        """
        vc.status = CredentialStatusType.REVOKED
        if vc.proof:
            vc.proof.revocationReason = reason

        # 在实际应用中，这里应该将撤销信息发布到凭证状态列表
        logger.info(f"凭证 {vc.id} 已撤销，原因: {reason}")
        return vc

    def create_presentation(
        self, credentials: List[VerifiableCredential], holder_did: str
    ) -> str:
        """
        创建可验证展示

        Args:
            credentials: 凭证列表
            holder_did: 持有者DID

        Returns:
            VP JSON-LD字符串
        """
        # 简化实现，实际应用中需要更复杂的展示创建逻辑
        presentation = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": f"urn:uuid:{self._generate_uuid()}",
            "type": ["VerifiablePresentation"],
            "verifiableCredential": [vc.to_json_ld() for vc in credentials],
            "holder": holder_did,
        }

        return json.dumps(presentation, ensure_ascii=False, indent=2)

    def _generate_uuid(self) -> str:
        """生成UUID"""
        return hashlib.md5(
            f"{datetime.now().isoformat()}{id(self)}".encode()
        ).hexdigest()

    def export_issuer_public_key(self) -> str:
        """导出颁发者公钥（十六进制格式）"""
        if self._issuer_public_key:
            return self._issuer_public_key.hex()
        return ""

    def get_verification_method(self, issuer_did: str) -> str:
        """获取验证方法URI"""
        return f"{issuer_did}#keys-1"


# 单例实例
vc_service = VerifiableCredentialService()
