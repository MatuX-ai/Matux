"""
技能认证区块链API路由
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.blockchain.service import blockchain_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blockchain", tags=["区块链"])


# 请求模型
class CertificateCreateRequest(BaseModel):
    """证书创建请求"""

    holderDID: str
    issuerDID: str
    skillName: str
    skillLevel: str
    evidence: List[str] = []
    expiryDate: Optional[str] = None
    credentialSubject: Optional[Dict[str, Any]] = None


class CertificateRevokeRequest(BaseModel):
    """证书撤销请求"""

    reason: str


class CertificationRequestCreate(BaseModel):
    """认证请求创建"""

    holderDID: str
    skillName: str
    skillLevel: str
    evidence: List[str] = []


class RequestReviewRequest(BaseModel):
    """请求审核"""

    issuerDID: Optional[str] = None
    comments: Optional[str] = None


# 响应模型
class CertificateResponse(BaseModel):
    """证书响应"""

    id: str
    holderDID: str
    issuerDID: str
    skillName: str
    skillLevel: str
    issueDate: str
    expiryDate: str
    status: str
    evidence: List[str]


class SuccessResponse(BaseModel):
    """成功响应"""

    success: bool
    message: str
    data: Optional[Any] = None


@router.on_event("startup")
async def startup_event():
    """应用启动时初始化区块链服务"""
    try:
        await blockchain_service.initialize()
        logger.info("区块链服务初始化完成")
    except Exception as e:
        logger.error(f"区块链服务初始化失败: {e}")


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """健康检查"""
    return await blockchain_service.health_check()


@router.post("/certificates", response_model=SuccessResponse)
async def issue_certificate(request: CertificateCreateRequest):
    """颁发技能证书"""
    try:
        cert_data = request.dict()
        tx_id = await blockchain_service.issue_certificate(cert_data)

        return SuccessResponse(
            success=True,
            message="证书颁发成功",
            data={"transactionId": tx_id, "certificateId": cert_data["id"]},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certificates/{cert_id}", response_model=CertificateResponse)
async def get_certificate(cert_id: str):
    """获取证书详情"""
    try:
        cert_data = await blockchain_service.verify_certificate(cert_id)
        return CertificateResponse(**cert_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/certificates/{cert_id}", response_model=SuccessResponse)
async def revoke_certificate(cert_id: str, request: CertificateRevokeRequest):
    """撤销证书"""
    try:
        tx_id = await blockchain_service.revoke_certificate(cert_id, request.reason)
        return SuccessResponse(
            success=True, message="证书撤销成功", data={"transactionId": tx_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/certificates/holder/{holder_did}", response_model=List[CertificateResponse]
)
async def get_certificates_by_holder(holder_did: str):
    """根据持有者查询证书"""
    try:
        certs = await blockchain_service.get_certificates_by_holder(holder_did)
        return [CertificateResponse(**cert) for cert in certs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/requests", response_model=SuccessResponse)
async def create_certification_request(request: CertificationRequestCreate):
    """创建认证请求"""
    try:
        request_data = request.dict()
        req_id = await blockchain_service.create_certification_request(request_data)

        return SuccessResponse(
            success=True, message="认证请求创建成功", data={"requestId": req_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/requests/{request_id}/approve", response_model=SuccessResponse)
async def approve_request(request_id: str, review: RequestReviewRequest):
    """批准认证请求"""
    try:
        tx_id = await blockchain_service.approve_request(
            request_id, review.issuerDID or ""
        )
        return SuccessResponse(
            success=True, message="认证请求批准成功", data={"transactionId": tx_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/requests/{request_id}/reject", response_model=SuccessResponse)
async def reject_request(request_id: str, review: RequestReviewRequest):
    """拒绝认证请求"""
    try:
        tx_id = await blockchain_service.reject_request(
            request_id, review.comments or "申请不符合要求"
        )
        return SuccessResponse(
            success=True, message="认证请求拒绝成功", data={"transactionId": tx_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/pending", response_model=List[Dict[str, Any]])
async def get_pending_requests():
    """获取待处理的认证请求"""
    try:
        requests = await blockchain_service.get_pending_requests()
        return requests
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{cert_id}", response_model=SuccessResponse)
async def verify_certificate_endpoint(cert_id: str):
    """验证证书有效性"""
    try:
        cert_data = await blockchain_service.verify_certificate(cert_id)
        return SuccessResponse(
            success=True,
            message="证书验证通过",
            data={
                "valid": True,
                "certificate": cert_data,
                "verifiedAt": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        return SuccessResponse(
            success=False,
            message=str(e),
            data={
                "valid": False,
                "error": str(e),
                "verifiedAt": datetime.now().isoformat(),
            },
        )
