"""
区块链网关API路由
提供积分发行等区块链相关功能的统一入口
"""

from datetime import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from models.user import User, UserRole
from routes.auth_routes import get_current_user
from services.blockchain.gateway_service import blockchain_gateway_service
from utils.decorators import require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blockchain", tags=["区块链网关"])


# 请求模型
class IssueIntegralRequest(BaseModel):
    """积分发行请求"""

    student_id: str
    amount: int
    description: Optional[str] = None


class OAuthTokenRequest(BaseModel):
    """OAuth2令牌请求"""

    grant_type: str
    client_id: str
    client_secret: str
    scope: Optional[str] = None


# 响应模型
class IssueIntegralResponse(BaseModel):
    """积分发行响应"""

    status: str
    tx_id: str
    timestamp: str
    student_id: str
    amount: int
    description: Optional[str] = None


class GatewayHealthResponse(BaseModel):
    """网关健康检查响应"""

    status: str
    service: str
    version: str
    timestamp: str
    blockchain_connected: bool
    last_block_height: Optional[int] = None


class OAuthTokenResponse(BaseModel):
    """OAuth2令牌响应"""

    access_token: str
    token_type: str
    expires_in: int
    scope: Optional[str] = None


@router.on_event("startup")
async def startup_event():
    """应用启动时初始化区块链网关服务"""
    try:
        await blockchain_gateway_service.initialize()
        logger.info("区块链网关服务初始化完成")
    except Exception as e:
        logger.error(f"区块链网关服务初始化失败: {e}")


@router.get("/health", response_model=GatewayHealthResponse)
async def health_check():
    """区块链网关健康检查"""
    try:
        health_data = await blockchain_gateway_service.health_check()
        return GatewayHealthResponse(
            status="healthy",
            service="Blockchain Gateway",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            blockchain_connected=health_data.get("connected", False),
            last_block_height=health_data.get("last_block_height"),
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return GatewayHealthResponse(
            status="unhealthy",
            service="Blockchain Gateway",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            blockchain_connected=False,
            last_block_height=None,
        )


@router.post("/issue-integral", response_model=IssueIntegralResponse)
@require_role([UserRole.ADMIN, UserRole.ORG_ADMIN])
async def issue_integral(
    request: IssueIntegralRequest, current_user: User = Depends(get_current_user)
):
    """
    发行积分给学生

    Args:
        request: 积分发行请求
        current_user: 当前认证用户

    Returns:
        IssueIntegralResponse: 包含交易哈希的响应

    Raises:
        HTTPException: 权限不足或区块链调用失败
    """
    try:
        # 验证用户角色（教育局或管理员）
        if current_user.role not in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：仅教育局或管理员可发行积分",
            )

        # 调用区块链网关服务
        tx_result = await blockchain_gateway_service.issue_integral(
            student_id=request.student_id,
            amount=request.amount,
            issuer_id=current_user.id,
            description=request.description or f"由{current_user.username}发行积分",
        )

        return IssueIntegralResponse(
            status="success",
            tx_id=tx_result["tx_id"],
            timestamp=datetime.now().isoformat(),
            student_id=request.student_id,
            amount=request.amount,
            description=request.description,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"积分发行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"积分发行失败: {str(e)}",
        )


@router.post("/oauth/token", response_model=OAuthTokenResponse)
async def oauth_token_exchange(request: OAuthTokenRequest):
    """
    OAuth2令牌交换端点

    Args:
        request: OAuth2令牌请求

    Returns:
        OAuthTokenResponse: OAuth2访问令牌
    """
    try:
        # 验证客户端凭据
        if not await blockchain_gateway_service.validate_client_credentials(
            request.client_id, request.client_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的客户端凭据"
            )

        # 生成访问令牌
        token_data = await blockchain_gateway_service.generate_access_token(
            client_id=request.client_id,
            grant_type=request.grant_type,
            scope=request.scope,
        )

        return OAuthTokenResponse(
            access_token=token_data["access_token"],
            token_type="Bearer",
            expires_in=token_data["expires_in"],
            scope=token_data.get("scope"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2令牌交换失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌交换失败: {str(e)}",
        )


@router.get("/students/{student_id}/balance")
async def get_student_balance(
    student_id: str, current_user: User = Depends(get_current_user)
):
    """
    查询学生积分余额

    Args:
        student_id: 学生ID
        current_user: 当前认证用户

    Returns:
        学生积分余额信息
    """
    try:
        balance_data = await blockchain_gateway_service.get_student_balance(student_id)

        return {
            "student_id": student_id,
            "balance": balance_data.get("total_amount", 0),
            "last_updated": datetime.fromtimestamp(
                balance_data.get("updated_at", 0)
            ).isoformat(),
            "query_time": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"查询学生余额失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询余额失败: {str(e)}",
        )


@router.get("/transactions/history")
async def get_transaction_history(
    student_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """
    查询交易历史记录

    Args:
        student_id: 学生ID（可选）
        limit: 返回记录数量限制
        offset: 偏移量
        current_user: 当前认证用户

    Returns:
        交易历史记录列表
    """
    try:
        history_data = await blockchain_gateway_service.get_transaction_history(
            student_id=student_id, limit=limit, offset=offset
        )

        return {
            "transactions": history_data.get("transactions", []),
            "total_count": history_data.get("total_count", 0),
            "limit": limit,
            "offset": offset,
            "query_time": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"查询交易历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询交易历史失败: {str(e)}",
        )


@router.delete("/circuits/breaker/reset")
@require_role(UserRole.ADMIN)
async def reset_circuit_breaker(current_user: User = Depends(get_current_user)):
    """
    重置熔断器（仅管理员）

    Args:
        current_user: 当前认证用户

    Returns:
        重置结果
    """
    try:
        await blockchain_gateway_service.reset_circuit_breaker()

        return {
            "status": "success",
            "message": "熔断器已重置",
            "reset_time": datetime.now().isoformat(),
            "reset_by": current_user.username,
        }

    except Exception as e:
        logger.error(f"重置熔断器失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置熔断器失败: {str(e)}",
        )
