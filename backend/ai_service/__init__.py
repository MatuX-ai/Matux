"""
AI服务包

本包的对外导出全部按 PEP 562 懒加载：``from ai_service import X`` 以及
``import ai_service`` 后访问 ``ai_service.X``，都在首次使用时才导入对应子模块。

原因：顶层 eager import 会连锁拉起 torch / transformers / sklearn / numpy /
openai 整条重依赖链（实测 ``import ai_service`` 约 26s），而绝大多数调用点
并不需要其中的任何一个。各调用点仍可直接 ``from ai_service.<sub> import X``
走子模块路径，不经过本模块的懒加载。

新增导出时需同步维护 ``_LAZY_EXPORTS`` 与 ``__all__``。
"""

from importlib import import_module
from typing import Dict, Tuple

#: 导出名 -> (子模块名, 子模块内的属性名)
_LAZY_EXPORTS: Dict[str, Tuple[str, str]] = {
    "AIManager": ("ai_manager", "AIManager"),
    "DifficultyCalculator": ("difficulty_calculator", "DifficultyCalculator"),
    "DifficultyLevel": ("difficulty_calculator", "DifficultyLevel"),
    "PerformanceMetrics": ("difficulty_calculator", "PerformanceMetrics"),
    "DynamicCourseGenerator": ("dynamic_course", "DynamicCourseGenerator"),
    "DynamicCourseRequest": ("dynamic_course", "DynamicCourseRequest"),
    "DynamicCourseResponse": ("dynamic_course", "DynamicCourseResponse"),
    "StudentProfile": ("dynamic_course", "StudentProfile"),
    "KnowledgeGraphManager": ("knowledge_graph_manager", "KnowledgeGraphManager"),
    "KnowledgeNode": ("knowledge_graph_manager", "KnowledgeNode"),
    "KnowledgeRelationship": ("knowledge_graph_manager", "KnowledgeRelationship"),
    "BehaviorEvent": ("markov_analyzer", "BehaviorEvent"),
    "BehaviorType": ("markov_analyzer", "BehaviorType"),
    "MarkovChainAnalyzer": ("markov_analyzer", "MarkovChainAnalyzer"),
    "AvailableModelsResponse": ("models", "AvailableModelsResponse"),
    "CodeGenerationRequest": ("models", "CodeGenerationRequest"),
    "CodeGenerationResponse": ("models", "CodeGenerationResponse"),
    "ModelInfo": ("models", "ModelInfo"),
    "ModelProvider": ("models", "ModelProvider"),
    "ProgrammingLanguage": ("models", "ProgrammingLanguage"),
    "RecommendationEngine": ("recommendation_service", "RecommendationEngine"),
}

__all__ = [
    "AIManager",
    "CodeGenerationRequest",
    "CodeGenerationResponse",
    "AvailableModelsResponse",
    "ModelInfo",
    "ModelProvider",
    "ProgrammingLanguage",
    "RecommendationEngine",
    "MarkovChainAnalyzer",
    "BehaviorEvent",
    "BehaviorType",
    "KnowledgeGraphManager",
    "KnowledgeNode",
    "KnowledgeRelationship",
    "DifficultyCalculator",
    "PerformanceMetrics",
    "DifficultyLevel",
    "DynamicCourseGenerator",
    "DynamicCourseRequest",
    "DynamicCourseResponse",
    "StudentProfile",
]


def __getattr__(name: str):
    """按需解析并缓存子模块导出（PEP 562）。"""
    try:
        submodule, attr = _LAZY_EXPORTS[name]
    except KeyError:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from None

    value = getattr(import_module(f".{submodule}", __name__), attr)
    globals()[name] = value  # 缓存，后续访问不再进入 __getattr__
    return value


def __dir__():
    return sorted(set(globals()) | set(_LAZY_EXPORTS))
