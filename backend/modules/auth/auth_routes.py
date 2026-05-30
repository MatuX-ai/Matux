"""
统一认证路由
提供手机号注册/登录、家长绑定学生等API端点
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_guardian import GuardianBindRequest, GuardianBindResponse
from modules.auth.auth_service import unified_auth_service, decode_token
from utils.database import get_db

router = APIRouter(prefix="/api/v1/unified-auth", tags=["统一认证"])


# ============ Request/Response Models ============


class PhoneRegisterRequest(BaseModel):
    """手机号注册请求"""

    phone: str = Field(..., description="手机号", min_length=11, max_length=11)
    password: str = Field(..., description="密码", min_length=6, max_length=72)
    username: Optional[str] = Field(None, description="用户名（可选，默认自动生成）")
    role: str = Field(default="student", description="角色：student/parent/teacher")


class PhoneLoginRequest(BaseModel):
    """手机号登录请求"""

    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


class UsernameLoginRequest(BaseModel):
    """用户名登录请求（兼容）"""

    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    """令牌响应"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str


# ============ 中间件辅助 ============


async def get_current_unified_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    """从请求中获取当前统一认证用户（供后续中间件使用）"""
    # 这里需要从请求头获取token，但FastAPI中需要在路由层面处理
    # 实际使用中，通过 Depends(inject_current_user) 模式
    raise NotImplementedError("请使用 inject_current_user 依赖")


# ============ API 端点 ============


@router.post("/register/phone", response_model=TokenResponse, summary="手机号注册")
async def register_by_phone(
    req: PhoneRegisterRequest, db: AsyncSession = Depends(get_db)
):
    """通过手机号注册新用户，返回JWT令牌"""
    try:
        user = await unified_auth_service.register_by_phone(
            db=db,
            phone=req.phone,
            password=req.password,
            username=req.username,
            role=req.role,
        )
        tokens = await unified_auth_service.login_by_phone(
            db=db, phone=req.phone, password=req.password
        )
        if not tokens:
            raise HTTPException(status_code=500, detail="注册后自动登录失败")
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login/phone", response_model=TokenResponse, summary="手机号登录")
async def login_by_phone(
    req: PhoneLoginRequest, db: AsyncSession = Depends(get_db)
):
    """通过手机号+密码登录"""
    try:
        tokens = await unified_auth_service.login_by_phone(
            db=db, phone=req.phone, password=req.password
        )
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/login", response_model=TokenResponse, summary="用户名登录（兼容）")
async def login_by_username(
    req: UsernameLoginRequest, db: AsyncSession = Depends(get_db)
):
    """通过用户名/邮箱+密码登录"""
    try:
        tokens = await unified_auth_service.login_by_username(
            db=db, username=req.username, password=req.password
        )
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
            )
        return TokenResponse(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    req: RefreshRequest, db: AsyncSession = Depends(get_db)
):
    """使用refresh_token获取新的访问令牌"""
    tokens = await unified_auth_service.refresh_access_token(
        db=db, refresh_token=req.refresh_token
    )
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的刷新令牌",
        )
    return TokenResponse(**tokens)


# ============ 家长绑定学生 ============


@router.post(
    "/bind-child", response_model=GuardianBindResponse, summary="家长绑定学生"
)
async def bind_child(
    req: GuardianBindRequest, db: AsyncSession = Depends(get_db)
):
    """家长通过学生手机号绑定学生

    注意：此端点需要在请求头中携带Authorization: Bearer <parent_token>
    实际项目中应通过依赖注入获取当前家长用户ID
    此处简化处理，parent_id 暂由前端传递，后续接入中间件后替换
    """
    # TODO: 接入统一认证中间件后，从 JWT 中获取 parent_id
    # 当前阶段通过请求头传递
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="请携带 Authorization Header，后续版本将自动从 JWT 中解析 parent_id",
    )


@router.get("/children", summary="获取家长绑定的学生列表")
async def get_children(db: AsyncSession = Depends(get_db)):
    """获取当前家长绑定的所有学生"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="请携带 Authorization Header，后续版本将自动从 JWT 中解析 parent_id",
    )


@router.get("/guardians", summary="获取学生的监护人列表")
async def get_guardians(db: AsyncSession = Depends(get_db)):
    """获取当前学生的所有监护人"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="请携带 Authorization Header，后续版本将自动从 JWT 中解析 student_id",
    )


@router.delete("/unbind-child/{student_id}", summary="解绑学生")
async def unbind_child(student_id: int, db: AsyncSession = Depends(get_db)):
    """家长解绑学生"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="请携带 Authorization Header，后续版本将自动从 JWT 中解析 parent_id",
    )
