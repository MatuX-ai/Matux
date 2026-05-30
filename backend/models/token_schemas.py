"""
Token 管理相关的 Pydantic 模型
用于 API 请求/响应验证
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TokenPackageResponse(BaseModel):
    """Token 套餐响应模型"""
    id: int
    name: str
    package_type: Optional[str]
    token_count: int
    price: float
    is_active: bool
    validity_days: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseTokenRequest(BaseModel):
    """购买 Token 套餐请求模型"""
    package_id: int = Field(..., description="套餐 ID", gt=0)
    payment_method: str = Field(..., description="支付方式 (wechat/alipay)")


class PurchaseTokenResponse(BaseModel):
    """购买 Token 套餐响应模型"""
    success: bool
    message: str
    order_no: str
    token_amount: int
    payment_amount: float
    payment_status: str


class UserBalanceResponse(BaseModel):
    """用户余额响应模型"""
    user_id: int
    total_tokens: int
    used_tokens: int
    remaining_tokens: int
    monthly_bonus_tokens: int
    last_bonus_date: Optional[datetime]


class TokenUsageRecordResponse(BaseModel):
    """Token 使用记录响应模型"""
    id: int
    token_amount: int
    usage_type: str
    usage_description: Optional[str]
    resource_id: Optional[int]
    resource_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenUsageListResponse(BaseModel):
    """Token 使用记录列表响应模型"""
    total: int
    page: int
    page_size: int
    records: List[TokenUsageRecordResponse]


class RechargeRecordResponse(BaseModel):
    """充值记录响应模型"""
    id: int
    package_name: str
    token_amount: int
    payment_amount: float
    payment_method: str
    payment_status: str
    order_no: str
    created_at: datetime


class TokenStatsResponse(BaseModel):
    """Token 统计信息响应模型"""
    total_tokens: int
    used_tokens: int
    remaining_tokens: int
    monthly_bonus: int
    last_bonus_date: Optional[datetime]
    month_usage: int
    total_spent: float
    recent_recharges: List[Dict]
    recent_usages: List[Dict]


class CostEstimateRequest(BaseModel):
    """成本预估请求模型"""
    feature_type: str = Field(...,
                              description="功能类型 (ai_teacher/course_generation)")
    params: Dict = Field(default={}, description="功能参数")


class CostEstimateResponse(BaseModel):
    """成本预估响应模型"""
    success: bool
    feature_type: str
    estimated_tokens: int
    description: str
