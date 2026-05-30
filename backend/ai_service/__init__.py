"""
AI服务包
"""

from .ai_manager import AIManager
from .difficulty_calculator import (
    DifficultyCalculator,
    DifficultyLevel,
    PerformanceMetrics,
)
from .dynamic_course import (
    DynamicCourseGenerator,
    DynamicCourseRequest,
    DynamicCourseResponse,
    StudentProfile,
)
from .knowledge_graph_manager import (
    KnowledgeGraphManager,
    KnowledgeNode,
    KnowledgeRelationship,
)
from .markov_analyzer import BehaviorEvent, BehaviorType, MarkovChainAnalyzer
from .models import (
    AvailableModelsResponse,
    CodeGenerationRequest,
    CodeGenerationResponse,
    ModelInfo,
    ModelProvider,
    ProgrammingLanguage,
)
from .recommendation_service import RecommendationEngine

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
