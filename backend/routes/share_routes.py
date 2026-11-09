"""
【P3-C】社交分享路由

API 路由：
- POST   /api/v1/share/cards               - 创建分享卡片
- GET    /api/v1/share/cards/{short_code}  - 查询卡片详情
- POST   /api/v1/share/cards/{short_code}/track-view   - 追踪浏览
- POST   /api/v1/share/cards/{short_code}/track-share  - 追踪分享
- GET    /api/v1/share/cards/{card_id}/qr  - 返回 QR 图片

- POST   /api/v1/invite/codes              - 生成邀请码
- GET    /api/v1/invite/codes/me           - 我创建的邀请码列表
- GET    /api/v1/invite/codes/{code}       - 查询邀请码
- POST   /api/v1/invite/codes/{code}/use   - 使用邀请码
- GET    /api/v1/invite/records/me         - 我的邀请记录

落地页（公开）：
- GET    /share/{short_code}               - 分享落地页（HTML）
- GET    /invite/{code}                    - 邀请注册落地页（HTML）
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.share import (
    ShareCard,
)
from models.user import User
from security.risk_control_middleware import captcha_required, risk_check
from services.invite_service import (
    InviteCodeAlreadyExhausted,
    InviteCodeExpired,
    InviteCodeNotFound,
    get_invite_service,
)
from services.share_service import get_share_service
from utils.database import get_sync_db
from utils.dependencies import get_current_user_sync

logger = logging.getLogger(__name__)

# ==================== 模板配置 ====================
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ==================== 共享 API 路由器 ====================
api_router = APIRouter(tags=["社交分享 API"])

# 落地页路由器（公开）
page_router = APIRouter(tags=["社交分享 落地页"])


# ==================== Pydantic Schemas ====================


class CreateCardRequest(BaseModel):
    """创建分享卡片请求"""
    card_type: str = Field(..., description="achievement/course/user_profile/learning_record")
    target_id: int = Field(..., description="目标对象 ID")
    title: Optional[str] = Field(None, description="自定义标题")
    subtitle: Optional[str] = Field(None, description="自定义副标题")
    description: Optional[str] = Field(None, description="自定义描述")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class CreateInviteRequest(BaseModel):
    """创建邀请码请求"""
    usage_limit: Optional[int] = Field(None, description="使用上限（None=无限）")
    reward_type: str = Field("points", description="points/discount/gift")
    reward_value: int = Field(100, description="奖励值")
    channel: Optional[str] = Field(None, description="wechat/weibo/x/link")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class UseInviteRequest(BaseModel):
    """使用邀请码请求"""
    invitee_id: int = Field(..., description="被邀请人用户 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="扩展元数据")


# ==================== 分享卡片 API ====================


@api_router.post("/api/v1/share/cards")
async def create_share_card(
    request_body: CreateCardRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    risk: Dict[str, Any] = Depends(captcha_required),  # 【P3-E】高风险端点：按需 CAPTCHA
):
    """创建分享卡片（生成短链 + 二维码）"""
    try:
        service = get_share_service(db)
        card = service.create_card(
            card_type=request_body.card_type,
            target_id=request_body.target_id,
            creator_id=current_user.id,
            custom_title=request_body.title,
            custom_subtitle=request_body.subtitle,
            custom_description=request_body.description,
            expires_at=request_body.expires_at,
        )
        return {"success": True, "data": card.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/api/v1/share/cards/{short_code}")
async def get_share_card(
    short_code: str,
    db: Session = Depends(get_sync_db),
):
    """查询分享卡片详情（公开 API）"""
    service = get_share_service(db)
    card = service.get_by_short_code(short_code)
    if not card:
        raise HTTPException(status_code=404, detail="分享卡片不存在")
    return {"success": True, "data": card.to_dict()}


@api_router.post("/api/v1/share/cards/{short_code}/track-view")
async def track_view(
    short_code: str,
    db: Session = Depends(get_sync_db),
):
    """追踪浏览行为（+1 view_count）"""
    service = get_share_service(db)
    success = service.track_view(short_code)
    if not success:
        raise HTTPException(status_code=404, detail="分享卡片不存在")
    return {"success": True}


@api_router.post("/api/v1/share/cards/{short_code}/track-share")
async def track_share(
    short_code: str,
    channel: str = Query("link", description="分享渠道：wechat/weibo/x/link/copy"),
    db: Session = Depends(get_sync_db),
    risk: Dict[str, Any] = Depends(risk_check),  # 【P3-E】检查风控（不强制 CAPTCHA）
):
    """追踪分享行为（+1 share_count）"""
    service = get_share_service(db)
    success = service.track_share(short_code, channel=channel)
    if not success:
        raise HTTPException(status_code=404, detail="分享卡片不存在")
    return {"success": True}


@api_router.get("/api/v1/share/cards/{card_id}/qr")
async def get_qr_code(
    card_id: int,
    db: Session = Depends(get_sync_db),
):
    """返回 QR 二维码图片（PNG）"""
    card = db.query(ShareCard).filter_by(id=card_id).first()
    if not card or not card.qr_code_path:
        raise HTTPException(status_code=404, detail="二维码不存在")
    qr_path = Path(card.qr_code_path)
    if not qr_path.exists():
        raise HTTPException(status_code=404, detail="二维码文件不存在")
    return FileResponse(qr_path, media_type="image/png")


# ==================== 邀请码 API ====================


@api_router.post("/api/v1/invite/codes")
async def create_invite_code(
    request_body: CreateInviteRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    captcha: Dict[str, Any] = Depends(captcha_required),  # 【P3-E】高风险：必查 CAPTCHA
):
    """生成邀请码"""
    service = get_invite_service(db)
    invite = service.create_code(
        creator_id=current_user.id,
        usage_limit=request_body.usage_limit,
        reward_type=request_body.reward_type,
        reward_value=request_body.reward_value,
        channel=request_body.channel,
        expires_at=request_body.expires_at,
    )
    return {"success": True, "data": invite.to_dict()}


@api_router.get("/api/v1/invite/codes/me")
async def list_my_invites(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """列出我创建的邀请码"""
    service = get_invite_service(db)
    invites = service.list_by_creator(current_user.id, limit=limit, offset=offset)
    return {
        "success": True,
        "count": len(invites),
        "data": [inv.to_dict() for inv in invites],
    }


@api_router.get("/api/v1/invite/codes/{code}")
async def get_invite_code(
    code: str,
    db: Session = Depends(get_sync_db),
):
    """查询邀请码信息（公开 API）"""
    service = get_invite_service(db)
    invite = service.get_by_code(code)
    if not invite:
        raise HTTPException(status_code=404, detail="邀请码不存在")
    return {"success": True, "data": invite.to_dict()}


@api_router.post("/api/v1/invite/codes/{code}/use")
async def use_invite_code(
    code: str,
    request_body: UseInviteRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    captcha: Dict[str, Any] = Depends(captcha_required),  # 【P3-E】高风险：防刷邀请码
):
    """使用邀请码（注册后调用）"""
    service = get_invite_service(db)
    try:
        record = service.use_code(
            code=code,
            invitee_id=request_body.invitee_id,
            metadata=request_body.metadata,
        )
        return {"success": True, "data": record.to_dict()}
    except InviteCodeNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InviteCodeAlreadyExhausted as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InviteCodeExpired as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/api/v1/invite/records/me")
async def list_my_invite_records(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """列出我的邀请记录"""
    service = get_invite_service(db)
    records = service.list_records_by_inviter(current_user.id, limit=limit, offset=offset)
    return {
        "success": True,
        "count": len(records),
        "data": [r.to_dict() for r in records],
    }


# ==================== 落地页（HTML 模板）====================


@page_router.get("/share/{short_code}", response_class=HTMLResponse)
async def share_landing(
    short_code: str,
    request: Request,
    db: Session = Depends(get_sync_db),
):
    """分享落地页（公开访问）"""
    service = get_share_service(db)
    try:
        data = service.render_landing_data(short_code)
    except LookupError:
        # 卡片不存在或已过期
        return templates.TemplateResponse(
            request,
            "share/expired.html",
            {"short_code": short_code},
            status_code=404,
        )

    return templates.TemplateResponse(
        request,
        "share/landing.html",
        data,
    )


@page_router.get("/invite/{code}", response_class=HTMLResponse)
async def invite_landing(
    code: str,
    request: Request,
    db: Session = Depends(get_sync_db),
):
    """邀请注册落地页（公开访问）"""
    service = get_invite_service(db)
    invite = service.get_by_code(code)
    if not invite or not invite.is_available():
        return templates.TemplateResponse(
            request,
            "share/expired.html",
            {"short_code": code},
            status_code=404,
        )

    inviter = db.query(User).filter_by(id=invite.creator_id).first()
    inviter_name = inviter.username if inviter else "iMato 用户"

    return templates.TemplateResponse(
        request,
        "share/invite.html",
        {
            "invite": invite.to_dict(),
            "inviter_name": inviter_name,
            "code": code,
        },
    )


__all__ = ["api_router", "page_router"]