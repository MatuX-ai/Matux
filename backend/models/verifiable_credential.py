"""
W3C可验证凭证(Verifiable Credentials)数据模型
遵循W3C Verifiable Credentials Data Model 1.0规范
"""

from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class CredentialStatusType(str, Enum):
    """凭证状态类型"""

    ACTIVE = "active"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class ProofType(str, Enum):
    """证明类型"""

    ED25519_SIGNATURE_2020 = "Ed25519Signature2020"
    RSA_SIGNATURE_2018 = "RsaSignature2018"
    ECDSA_SECP256K1_SIGNATURE_2019 = "EcdsaSecp256k1Signature2019"


class ProofPurpose(str, Enum):
    """证明目的"""

    ASSERTION_METHOD = "assertionMethod"
    AUTHENTICATION = "authentication"
    KEY_AGREEMENT = "keyAgreement"
    CAPABILITY_INVOCATION = "capabilityInvocation"
    CAPABILITY_DELEGATION = "capabilityDelegation"


class VCProof(BaseModel):
    """
    W3C VC数字签名证明
    """

    type: ProofType = Field(
        default=ProofType.ED25519_SIGNATURE_2020, description="证明类型"
    )
    created: str = Field(description="证明创建时间 ISO 8601格式")
    verificationMethod: str = Field(description="验证方法URI，通常是DID + # + key-id")
    proofPurpose: ProofPurpose = Field(
        default=ProofPurpose.ASSERTION_METHOD, description="证明目的"
    )
    jws: str = Field(description="JSON Web Signature")
    challenge: Optional[str] = Field(
        default=None, description="挑战值，用于防止重放攻击"
    )
    domain: Optional[str] = Field(default=None, description="域名限制")
    revocationReason: Optional[str] = Field(default=None, description="撤销原因")

    class Config:
        schema_extra = {
            "example": {
                "type": "Ed25519Signature2020",
                "created": "2026-01-01T00:00:00Z",
                "verificationMethod": "did:example:123#keys-1",
                "proofPurpose": "assertionMethod",
                "jws": "eyJhbGciOiJFZERTQSJ9..signature",
            }
        }


class CredentialSubject(BaseModel):
    """
    凭证主体信息
    """

    id: str = Field(description="主体标识符，通常是DID")
    # 可扩展的主体属性
    skill: Optional[str] = Field(default=None, description="技能名称")
    level: Optional[str] = Field(default=None, description="技能等级")
    achievements: Optional[List[str]] = Field(default=None, description="成就列表")

    class Config:
        extra = "allow"  # 允许额外字段


class CredentialStatus(BaseModel):
    """
    凭证状态信息
    """

    id: str = Field(description="状态标识符URL")
    type: str = Field(description="状态类型，如CredentialStatusList2017")


class VerifiableCredential(BaseModel):
    """
    W3C可验证凭证主模型
    """

    # 必需的上下文
    context: List[Union[str, Dict[str, Any]]] = Field(
        default=["https://www.w3.org/2018/credentials/v1"],
        alias="@context",
        description="JSON-LD上下文",
    )

    # 凭证标识符
    id: str = Field(description="凭证唯一标识符 URI格式")

    # 凭证类型
    type: List[str] = Field(
        default=["VerifiableCredential"], description="凭证类型数组"
    )

    # 颁发者
    issuer: Union[str, Dict[str, Any]] = Field(
        description="颁发者标识，可以是字符串DID或对象"
    )

    # 颁发日期
    issuanceDate: str = Field(description="颁发日期 ISO 8601格式")

    # 过期日期（可选）
    expirationDate: Optional[str] = Field(
        default=None, description="过期日期 ISO 8601格式"
    )

    # 凭证主体
    credentialSubject: CredentialSubject = Field(description="凭证主体信息")

    # 凭证状态（可选）
    credentialStatus: Optional[CredentialStatus] = Field(
        default=None, description="凭证状态信息"
    )

    # 数字签名证明
    proof: Optional[VCProof] = Field(default=None, description="数字签名证明")

    # 凭证状态
    status: CredentialStatusType = Field(
        default=CredentialStatusType.ACTIVE, description="凭证状态"
    )

    # 元数据
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")

    @validator("issuanceDate", "expirationDate")
    def validate_datetime_format(cls, v):
        """验证日期时间格式"""
        if v is not None:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("日期必须是有效的ISO 8601格式")
        return v

    @validator("expirationDate")
    def validate_expiration_after_issuance(cls, v, values):
        """验证过期日期必须晚于颁发日期"""
        if v is not None and "issuanceDate" in values:
            issuance = datetime.fromisoformat(
                values["issuanceDate"].replace("Z", "+00:00")
            )
            expiration = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if expiration <= issuance:
                raise ValueError("过期日期必须晚于颁发日期")
        return v

    def to_json_ld(self) -> str:
        """
        转换为JSON-LD格式字符串

        Returns:
            JSON-LD格式的凭证字符串
        """
        # 转换为dict并处理别名
        vc_dict = self.dict(by_alias=True, exclude_none=True)

        # 确保@context在最前面
        if "@context" in vc_dict:
            context = vc_dict.pop("@context")
            result = {"@context": context}
            result.update(vc_dict)
            vc_dict = result

        return json.dumps(vc_dict, ensure_ascii=False, indent=2)

    def calculate_hash(self) -> str:
        """
        计算凭证内容的哈希值

        Returns:
            SHA-256哈希值
        """
        # 排除proof字段计算哈希
        vc_dict = self.dict(exclude={"proof"}, exclude_none=True)
        vc_json = json.dumps(vc_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(vc_json.encode("utf-8")).hexdigest()

    def is_expired(self) -> bool:
        """
        检查凭证是否过期

        Returns:
            是否过期
        """
        if self.expirationDate is None:
            return False

        exp_date = datetime.fromisoformat(self.expirationDate.replace("Z", "+00:00"))
        return datetime.now() > exp_date

    def is_valid(self) -> bool:
        """
        检查凭证是否有效

        Returns:
            是否有效
        """
        # 检查状态
        if self.status != CredentialStatusType.ACTIVE:
            return False

        # 检查过期
        if self.is_expired():
            return False

        # 检查必需字段
        if not all([self.id, self.issuer, self.issuanceDate, self.credentialSubject]):
            return False

        return True

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://www.w3.org/2018/credentials/examples/v1",
                ],
                "id": "http://example.edu/credentials/1872",
                "type": ["VerifiableCredential", "SkillCertificate"],
                "issuer": "did:example:123",
                "issuanceDate": "2026-01-01T00:00:00Z",
                "expirationDate": "2028-01-01T00:00:00Z",
                "credentialSubject": {
                    "id": "did:example:456",
                    "skill": "区块链开发",
                    "level": "专家级",
                    "achievements": ["完成企业级项目", "获得认证"],
                },
                "proof": {
                    "type": "Ed25519Signature2020",
                    "created": "2026-01-01T00:00:00Z",
                    "verificationMethod": "did:example:123#keys-1",
                    "proofPurpose": "assertionMethod",
                    "jws": "eyJhbGciOiJFZERTQSJ9..signature",
                },
            }
        }


class PresentationProof(VCProof):
    """
    展示证明（VP中的证明）
    """

    type: ProofType = Field(
        default=ProofType.ED25519_SIGNATURE_2020, description="证明类型"
    )
    purpose: ProofPurpose = Field(
        default=ProofPurpose.AUTHENTICATION, description="展示目的"
    )


class VerifiablePresentation(BaseModel):
    """
    W3C可验证展示
    """

    context: List[Union[str, Dict[str, Any]]] = Field(
        default=["https://www.w3.org/2018/credentials/v1"],
        alias="@context",
        description="JSON-LD上下文",
    )

    id: str = Field(description="展示唯一标识符")

    type: List[str] = Field(default=["VerifiablePresentation"], description="展示类型")

    verifiableCredential: List[Union[VerifiableCredential, str]] = Field(
        description="包含的可验证凭证列表"
    )

    holder: Optional[str] = Field(default=None, description="展示持有者DID")

    proof: Optional[PresentationProof] = Field(default=None, description="展示证明")

    def to_json_ld(self) -> str:
        """转换为JSON-LD格式"""
        vp_dict = self.dict(by_alias=True, exclude_none=True)

        if "@context" in vp_dict:
            context = vp_dict.pop("@context")
            result = {"@context": context}
            result.update(vp_dict)
            vp_dict = result

        return json.dumps(vp_dict, ensure_ascii=False, indent=2)


# 技能证书专用模型
class SkillCertificateCredential(VerifiableCredential):
    """
    技能证书凭证（继承自VerifiableCredential）
    """

    type: List[str] = Field(
        default=["VerifiableCredential", "SkillCertificate"], description="技能证书类型"
    )

    credentialSubject: CredentialSubject = Field(description="技能证书主体信息")

    # 技能特定字段
    skill_name: str = Field(description="技能名称")

    skill_level: str = Field(description="技能等级")

    evidence: List[str] = Field(default_factory=list, description="技能证明材料")

    issuing_organization: Optional[str] = Field(
        default=None, description="颁发机构名称"
    )

    class Config:
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "@context": ["https://www.w3.org/2018/credentials/v1"],
                "id": "urn:uuid:12345678-1234-1234-1234-123456789abc",
                "type": ["VerifiableCredential", "SkillCertificate"],
                "issuer": "did:example:org123",
                "issuanceDate": "2026-01-01T00:00:00Z",
                "skill_name": "Python编程",
                "skill_level": "高级",
                "evidence": ["项目作品集", "在线评测成绩"],
                "credentialSubject": {"id": "did:example:user456", "name": "张三"},
                "proof": {
                    "type": "Ed25519Signature2020",
                    "created": "2026-01-01T00:00:00Z",
                    "verificationMethod": "did:example:org123#keys-1",
                    "proofPurpose": "assertionMethod",
                    "jws": "signature_here",
                },
            }
        }
