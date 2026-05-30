"""
创意激发引擎数据模型
定义创意想法、Prompt模板、评分等相关数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class IdeaCategory(str, Enum):
    """创意分类枚举"""

    TECHNOLOGY = "technology"
    BUSINESS = "business"
    DESIGN = "design"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    ENTERTAINMENT = "entertainment"
    ENVIRONMENT = "environment"
    OTHER = "other"


class ScorerType(str, Enum):
    """评分者类型枚举"""

    AI = "ai"
    HUMAN = "human"
    HYBRID = "hybrid"


class ImageStyle(str, Enum):
    """图像风格枚举"""

    REALISTIC = "realistic"
    ARTISTIC = "artistic"
    CARTOON = "cartoon"
    PHOTOGRAPHIC = "photographic"
    DIGITAL_ART = "digital_art"
    THREE_D_RENDER = "3d_render"


# 数据库模型


class CreativeIdea(Base):
    """创意想法数据库模型"""

    __tablename__ = "creative_ideas"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"))
    ai_generated_content = Column(JSON)
    images = Column(JSON)  # 存储图像URL和元数据
    scores = Column(JSON)  # 存储评分结果
    tags = Column(JSON)  # 标签数组
    is_public = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="creative_ideas")
    prompt_template = relationship("PromptTemplate", back_populates="ideas")
    score_records = relationship("IdeaScore", back_populates="idea")


class PromptTemplate(Base):
    """Prompt模板数据库模型"""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    template = Column(Text, nullable=False)
    variables = Column(JSON)  # 模板变量定义
    description = Column(Text)
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    ideas = relationship("CreativeIdea", back_populates="prompt_template")
    creator = relationship("User", back_populates="created_templates")


class IdeaScore(Base):
    """创意评分记录数据库模型"""

    __tablename__ = "idea_scores"

    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("creative_ideas.id"), nullable=False)
    scorer_type = Column(String(50))  # 'ai', 'human', 'hybrid'
    creativity_score = Column(Numeric(precision=3, scale=2))
    feasibility_score = Column(Numeric(precision=3, scale=2))
    commercial_score = Column(Numeric(precision=3, scale=2))
    total_score = Column(Numeric(precision=3, scale=2))
    analysis_details = Column(JSON)  # 详细分析内容
    reviewer_id = Column(Integer, ForeignKey("users.id"))  # 人工评分者
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    idea = relationship("CreativeIdea", back_populates="score_records")
    reviewer = relationship("User", back_populates="scored_ideas")


# Pydantic模型（用于API请求/响应）


class CreativeIdeaCreate(BaseModel):
    """创建创意想法请求模型"""

    title: str = Field(..., min_length=1, max_length=255, description="创意标题")
    description: Optional[str] = Field(None, max_length=2000, description="创意描述")
    category: Optional[IdeaCategory] = Field(None, description="创意分类")
    prompt_template_id: Optional[int] = Field(None, description="使用的Prompt模板ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_public: bool = Field(default=False, description="是否公开")


class CreativeIdeaUpdate(BaseModel):
    """更新创意想法请求模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[IdeaCategory] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class CreativeIdeaResponse(BaseModel):
    """创意想法响应模型"""

    id: int
    user_id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    prompt_template_id: Optional[int]
    ai_generated_content: Optional[Dict[str, Any]]
    images: Optional[List[Dict[str, Any]]]
    scores: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    is_public: bool
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class PromptTemplateCreate(BaseModel):
    """创建Prompt模板请求模型"""

    name: str = Field(..., min_length=1, max_length=255, description="模板名称")
    category: Optional[str] = Field(None, max_length=100, description="模板分类")
    template: str = Field(..., min_length=10, description="模板内容")
    variables: Optional[Dict[str, Any]] = Field(None, description="模板变量定义")
    description: Optional[str] = Field(None, max_length=1000, description="模板描述")
    is_public: bool = Field(default=True, description="是否公开")


class PromptTemplateResponse(BaseModel):
    """Prompt模板响应模型"""

    id: int
    name: str
    category: Optional[str]
    template: str
    variables: Optional[Dict[str, Any]]
    description: Optional[str]
    usage_count: int
    is_public: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class IdeaGenerationRequest(BaseModel):
    """创意生成请求模型"""

    prompt_template_id: Optional[int] = Field(None, description="Prompt模板ID")
    custom_prompt: Optional[str] = Field(
        None, max_length=2000, description="自定义Prompt"
    )
    category: Optional[IdeaCategory] = Field(None, description="创意分类")
    variables: Optional[Dict[str, Any]] = Field(None, description="模板变量值")
    temperature: float = Field(default=0.8, ge=0.0, le=1.0, description="生成温度")
    max_tokens: int = Field(default=1500, ge=100, le=4000, description="最大令牌数")


class IdeaGenerationResponse(BaseModel):
    """创意生成响应模型"""

    idea_id: int
    title: str
    content: str
    category: Optional[str]
    processing_time: float
    tokens_used: int


class ImageGenerationRequest(BaseModel):
    """图像生成请求模型"""

    prompt: str = Field(
        ..., min_length=10, max_length=1000, description="图像生成Prompt"
    )
    style: ImageStyle = Field(default=ImageStyle.REALISTIC, description="图像风格")
    size: str = Field(default="1024x1024", pattern=r"^\d+x\d+$", description="图像尺寸")
    quality: str = Field(default="standard", description="图像质量")
    n: int = Field(default=1, ge=1, le=10, description="生成图像数量")


class ImageGenerationResponse(BaseModel):
    """图像生成响应模型"""

    images: List[Dict[str, str]]  # 包含URL和元数据
    processing_time: float
    total_cost: float


class IdeaScoreRequest(BaseModel):
    """创意评分请求模型"""

    idea_content: str = Field(..., min_length=50, description="创意内容")
    technical_requirements: Optional[str] = Field(None, description="技术要求")
    business_model: Optional[str] = Field(None, description="商业模式")
    market_context: Optional[str] = Field(None, description="市场背景")
    scoring_criteria: Optional[Dict[str, float]] = Field(
        default=None, description="评分权重配置"
    )


class IdeaScoreResponse(BaseModel):
    """创意评分响应模型"""

    total_score: float = Field(..., ge=0.0, le=10.0, description="总分")
    creativity: float = Field(..., ge=0.0, le=10.0, description="创新性得分")
    feasibility: float = Field(..., ge=0.0, le=10.0, description="可行性得分")
    commercial_value: float = Field(..., ge=0.0, le=10.0, description="商业价值得分")
    detailed_analysis: Dict[str, Any] = Field(..., description="详细分析")
    recommendations: List[str] = Field(..., description="改进建议")


class BusinessEvaluationRequest(BaseModel):
    """商业价值评估请求模型"""

    idea_description: str = Field(..., description="创意描述")
    target_market: str = Field(..., description="目标市场")
    estimated_costs: Dict[str, float] = Field(..., description="成本估算")
    revenue_projections: Dict[str, float] = Field(..., description="收入预测")
    competition_analysis: str = Field(..., description="竞争分析")


class BusinessEvaluationResponse(BaseModel):
    """商业价值评估响应模型"""

    cost_benefit_ratio: float
    market_potential: float
    risk_assessment: Dict[str, Any]
    investment_recommendation: str
    timeline_estimate: str
    resource_requirements: List[str]


# 扩展现有用户模型的关系
from models.user import User

User.creative_ideas = relationship("CreativeIdea", back_populates="user")
User.created_templates = relationship("PromptTemplate", back_populates="creator")
User.scored_ideas = relationship("IdeaScore", back_populates="reviewer")
