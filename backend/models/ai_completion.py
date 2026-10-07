from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelProvider(str, Enum):
    """AI模型提供商枚举"""

    OPENAI = "openai"
    LINGMA = "lingma"
    DEEPSEEK = "deepseek"


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


class CompletionRequest(BaseModel):
    """代码补全请求模型"""

    prefix: str = Field(
        ..., min_length=1, max_length=1000, description="待补全的代码前缀"
    )
    context: List[str] = Field(
        default_factory=list, max_length=50, description="上下文代码行"
    )
    language: Optional[ProgrammingLanguage] = Field(None, description="编程语言")
    provider: Optional[ModelProvider] = Field(
        ModelProvider.OPENAI, description="AI提供商"
    )
    max_suggestions: int = Field(5, ge=1, le=20, description="最大建议数量")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="生成温度")
    user_id: Optional[int] = Field(None, description="用户ID")


class CompletionSuggestion(BaseModel):
    """单个补全建议模型"""

    text: str = Field(..., description="补全文本")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度分数")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关性评分")
    language_features: List[str] = Field(
        default_factory=list, description="语言特征标签"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class CompletionResponse(BaseModel):
    """代码补全响应模型"""

    suggestions: List[CompletionSuggestion] = Field(..., description="补全建议列表")
    processing_time: float = Field(..., ge=0.0, description="处理时间(秒)")
    tokens_used: int = Field(0, ge=0, description="使用的令牌数")
    model_used: str = Field(..., description="使用的具体模型")
    cache_hit: bool = Field(False, description="是否来自缓存")
    context_analyzed: bool = Field(True, description="是否进行了上下文分析")


class UserHistoryRecord(BaseModel):
    """用户历史记录模型"""

    id: Optional[int] = None
    user_id: int = Field(..., description="用户ID")
    code_snippet: str = Field(..., max_length=2000, description="代码片段")
    context: str = Field("", max_length=5000, description="上下文信息")
    language: ProgrammingLanguage = Field(..., description="编程语言")
    usage_count: int = Field(1, ge=1, description="使用次数")
    last_used: datetime = Field(
        default_factory=datetime.utcnow, description="最后使用时间"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )


class CompletionCacheEntry(BaseModel):
    """补全缓存条目模型"""

    id: Optional[int] = None
    prefix_hash: str = Field(..., description="前缀哈希值")
    completions: List[CompletionSuggestion] = Field(..., description="缓存的补全结果")
    confidence_scores: List[float] = Field(..., description="置信度分数列表")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    expires_at: datetime = Field(..., description="过期时间")
    hit_count: int = Field(0, ge=0, description="命中次数")


class ContextAnalysisResult(BaseModel):
    """上下文分析结果模型"""

    scope_level: str = Field(..., description="作用域级别")
    syntax_context: str = Field(..., description="语法上下文")
    variable_declarations: List[str] = Field(
        default_factory=list, description="变量声明"
    )
    function_signatures: List[str] = Field(default_factory=list, description="函数签名")
    imported_modules: List[str] = Field(default_factory=list, description="导入模块")
    current_indentation: int = Field(0, ge=0, description="当前缩进级别")


# CodeCompletion接口实现
class CodeCompletion:
    """实时代码补全服务接口"""

    async def suggest(self, prefix: str, context: List[str]) -> List[str]:
        """
        根据前缀和上下文提供代码补全建议

        Args:
            prefix: 待补全的代码前缀
            context: 上下文代码行列表

        Returns:
            补全建议列表
        """
        raise NotImplementedError("子类必须实现suggest方法")

    async def analyze_context(
        self, code_lines: List[str], cursor_position: int
    ) -> ContextAnalysisResult:
        """
        分析代码上下文

        Args:
            code_lines: 代码行列表
            cursor_position: 光标位置

        Returns:
            上下文分析结果
        """
        raise NotImplementedError("子类必须实现analyze_context方法")

    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户偏好设置

        Args:
            user_id: 用户ID

        Returns:
            用户偏好字典
        """
        raise NotImplementedError("子类必须实现get_user_preferences方法")


class CompletionConfig(BaseModel):
    """补全服务配置模型"""

    enable_caching: bool = Field(True, description="是否启用缓存")
    cache_ttl_hours: int = Field(24, ge=1, le=168, description="缓存过期时间(小时)")
    max_context_lines: int = Field(20, ge=5, le=100, description="最大上下文行数")
    min_prefix_length: int = Field(3, ge=1, le=10, description="最小前缀长度")
    enable_syntax_analysis: bool = Field(True, description="是否启用语法分析")
    default_provider: ModelProvider = Field(
        ModelProvider.DEEPSEEK, description="默认AI提供商"
    )
    fallback_providers: List[ModelProvider] = Field(
        [ModelProvider.OPENAI, ModelProvider.LINGMA], description="备用AI提供商列表"
    )


# ========== DeepSeek AI 辅导相关模型 ==========


class DeepSeekExplainRequest(BaseModel):
    """DeepSeek 代码解释请求"""

    code: str = Field(..., min_length=1, max_length=10000, description="需要解释的代码")
    language: Optional[ProgrammingLanguage] = Field(None, description="编程语言")
    detail_level: str = Field("normal", description="详细程度: brief/normal/detailed")
    provider: Optional[ModelProvider] = Field(ModelProvider.DEEPSEEK, description="AI提供商")
    model: Optional[str] = Field(None, description="模型名称")
    user_id: Optional[int] = Field(None, description="用户ID")


class CodeElement(BaseModel):
    """代码元素"""

    name: str = Field(..., description="元素名称")
    type: str = Field(..., description="元素类型: function/class/variable/import/keyword")
    description: str = Field(..., description="元素描述")
    line_start: int = Field(..., description="起始行号")
    line_end: int = Field(..., description="结束行号")


class CodeComplexity(BaseModel):
    """代码复杂度"""

    score: float = Field(..., description="复杂度分数 0-100")
    level: str = Field(..., description="复杂度级别: low/medium/high")
    factors: List[str] = Field(default_factory=list, description="复杂度因素")


class DeepSeekExplainResponse(BaseModel):
    """DeepSeek 代码解释响应"""

    explanation: str = Field(..., description="代码解释")
    code_elements: List[CodeElement] = Field(default_factory=list, description="代码元素列表")
    complexity: CodeComplexity = Field(..., description="代码复杂度")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    related_concepts: List[str] = Field(default_factory=list, description="相关概念")
    model_used: str = Field(..., description="使用的模型")
    processing_time: float = Field(..., description="处理时间(秒)")


class DeepSeekOptimizeRequest(BaseModel):
    """DeepSeek 代码优化请求"""

    code: str = Field(..., min_length=1, max_length=10000, description="需要优化的代码")
    language: Optional[ProgrammingLanguage] = Field(None, description="编程语言")
    optimization_goals: Optional[List[str]] = Field(
        None, description="优化目标: performance/readability/security/best-practice"
    )
    provider: Optional[ModelProvider] = Field(ModelProvider.DEEPSEEK, description="AI提供商")
    model: Optional[str] = Field(None, description="模型名称")
    user_id: Optional[int] = Field(None, description="用户ID")


class OptimizationImprovement(BaseModel):
    """优化改进项"""

    type: str = Field(..., description="改进类型")
    description: str = Field(..., description="改进描述")
    original_snippet: str = Field(..., description="原始代码片段")
    optimized_snippet: str = Field(..., description="优化后代码片段")
    impact: str = Field(..., description="影响程度: high/medium/low")


class DeepSeekOptimizeResponse(BaseModel):
    """DeepSeek 代码优化响应"""

    original_code: str = Field(..., description="原始代码")
    optimized_code: str = Field(..., description="优化后代码")
    improvements: List[OptimizationImprovement] = Field(default_factory=list, description="改进列表")
    explanation: str = Field(..., description="优化说明")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    model_used: str = Field(..., description="使用的模型")
    processing_time: float = Field(..., description="处理时间(秒)")


class DeepSeekTutorRequest(BaseModel):
    """DeepSeek 智能辅导请求"""

    code: Optional[str] = Field(None, max_length=5000, description="相关代码片段")
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    context: Optional[List[str]] = Field(None, description="上下文代码")
    language: Optional[ProgrammingLanguage] = Field(None, description="编程语言")
    provider: Optional[ModelProvider] = Field(ModelProvider.DEEPSEEK, description="AI提供商")
    model: Optional[str] = Field(None, description="模型名称")
    user_id: Optional[int] = Field(None, description="用户ID")


class CodeExample(BaseModel):
    """代码示例"""

    title: str = Field(..., description="示例标题")
    code: str = Field(..., description="示例代码")
    language: str = Field(..., description="编程语言")
    explanation: str = Field(..., description="代码解释")


class DeepSeekTutorResponse(BaseModel):
    """DeepSeek 智能辅导响应"""

    answer: str = Field(..., description="回答内容")
    code_examples: List[CodeExample] = Field(default_factory=list, description="代码示例")
    related_topics: List[str] = Field(default_factory=list, description="相关主题")
    next_steps: List[str] = Field(default_factory=list, description="后续学习建议")
    model_used: str = Field(..., description="使用的模型")
    processing_time: float = Field(..., description="处理时间(秒)")
