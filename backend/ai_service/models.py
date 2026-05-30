"""
AI服务数据模型
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    """AI模型提供商枚举"""

    OPENAI = "openai"
    LINGMA = "lingma"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ProgrammingLanguage(str, Enum):
    """编程语言枚举"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    PHP = "php"
    RUBY = "ruby"


class CodeGenerationRequest(BaseModel):
    """代码生成请求模型"""

    prompt: str = Field(
        ..., min_length=1, max_length=5000, description="代码生成提示词"
    )
    provider: ModelProvider = Field(
        default=ModelProvider.OPENAI, description="AI模型提供商"
    )
    model: Optional[str] = Field(None, description="具体模型名称")
    language: Optional[ProgrammingLanguage] = Field(None, description="目标编程语言")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="生成温度参数")
    max_tokens: int = Field(default=2000, ge=1, le=8000, description="最大生成令牌数")
    system_prompt: Optional[str] = Field(None, description="系统提示词")


class CodeGenerationResponse(BaseModel):
    """代码生成响应模型"""

    code: str = Field(..., description="生成的代码")
    provider: ModelProvider = Field(..., description="使用的AI提供商")
    model: str = Field(..., description="使用的具体模型")
    tokens_used: int = Field(..., description="使用的令牌数")
    processing_time: float = Field(..., description="处理时间（秒）")
    language_detected: Optional[ProgrammingLanguage] = Field(
        None, description="检测到的编程语言"
    )


class ModelInfo(BaseModel):
    """模型信息模型"""

    provider: ModelProvider
    model_name: str
    description: str
    max_tokens: int
    supported_languages: List[ProgrammingLanguage]


class AvailableModelsResponse(BaseModel):
    """可用模型响应模型"""

    models: List[ModelInfo]
