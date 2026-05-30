/**
 * AI服务客户端配置接口
 */
export interface AIServiceConfig {
  /** API基础URL */
  baseUrl: string;
  /** 访问令牌 */
  accessToken?: string;
  /** 默认超时时间（毫秒） */
  timeout?: number;
  /** 默认请求头 */
  headers?: Record<string, string>;
}

/**
 * AI模型提供商枚举
 */
export enum ModelProvider {
  OPENAI = 'openai',
  LINGMA = 'lingma',
  DEEPSEEK = 'deepseek',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
}

/**
 * 编程语言枚举
 */
export enum ProgrammingLanguage {
  PYTHON = 'python',
  JAVASCRIPT = 'javascript',
  TYPESCRIPT = 'typescript',
  JAVA = 'java',
  CSHARP = 'csharp',
  GO = 'go',
  RUST = 'rust',
  CPP = 'cpp',
  PHP = 'php',
  RUBY = 'ruby',
}

/**
 * 代码生成请求接口
 */
export interface CodeGenerationRequest {
  /** 代码生成提示词 */
  prompt: string;
  /** AI模型提供商 */
  provider?: ModelProvider;
  /** 具体模型名称 */
  model?: string;
  /** 目标编程语言 */
  language?: ProgrammingLanguage;
  /** 生成温度参数 (0.0-1.0) */
  temperature?: number;
  /** 最大生成令牌数 */
  maxTokens?: number;
  /** 系统提示词 */
  systemPrompt?: string;
}

/**
 * 代码生成响应接口
 */
export interface CodeGenerationResponse {
  /** 生成的代码 */
  code: string;
  /** 使用的AI提供商 */
  provider: ModelProvider;
  /** 使用的具体模型 */
  model: string;
  /** 使用的令牌数 */
  tokensUsed: number;
  /** 处理时间（秒） */
  processingTime: number;
  /** 检测到的编程语言 */
  languageDetected?: ProgrammingLanguage;
}

/**
 * 模型信息接口
 */
export interface ModelInfo {
  /** AI模型提供商 */
  provider: ModelProvider;
  /** 模型名称 */
  modelName: string;
  /** 模型描述 */
  description: string;
  /** 最大令牌数 */
  maxTokens: number;
  /** 支持的编程语言 */
  supportedLanguages: ProgrammingLanguage[];
}

/**
 * 可用模型响应接口
 */
export interface AvailableModelsResponse {
  /** 模型列表 */
  models: ModelInfo[];
}

/**
 * 使用统计接口
 */
export interface UsageStats {
  /** 总请求数 */
  totalRequests: number;
  /** 成功请求数 */
  successfulRequests: number;
  /** 成功率 */
  successRate: number;
  /** 按提供商统计 */
  providerStats: {
    provider: string;
    requestCount: number;
    averageProcessingTime: number;
  }[];
}

/**
 * 请求记录接口
 */
export interface AIRequestRecord {
  /** 请求ID */
  id: number;
  /** 提示词（截断） */
  prompt: string;
  /** 模型提供商 */
  modelProvider: string;
  /** 模型名称 */
  modelName: string;
  /** 使用的令牌数 */
  tokensUsed: number;
  /** 处理时间 */
  processingTime: number;
  /** 是否成功 */
  success: boolean;
  /** 创建时间 */
  createdAt: string;
}

/**
 * HTTP错误接口
 */
export interface HttpError {
  /** HTTP状态码 */
  status: number;
  /** 错误信息 */
  message: string;
  /** 详细错误信息 */
  details?: any;
}

/**
 * 分页参数接口
 */
export interface PaginationParams {
  /** 每页数量 */
  limit?: number;
  /** 偏移量 */
  offset?: number;
}

/**
 * 课程推荐接口
 * @see {@link UnifiedCourse} — 对应共享模型中的统一课程类型
 */
export interface CourseRecommendation {
  /** 课程ID — 对应于 UnifiedCourse.id */
  courseId: string;
  /** 课程标题 */
  title: string;
  /** 课程描述 */
  description: string;
  /** 课程分类 */
  category: string;
  /** 难度等级 */
  difficultyLevel: string;
  /** 预估时长（小时） */
  estimatedDuration: number;
  /** 标签列表 */
  tags: string[];
  /** 受欢迎程度 */
  popularityScore: number;
  /** 推荐分数 */
  recommendationScore: number;
  /** 推荐类型 */
  recommendationTypes: string[];
}

/**
 * 课程推荐响应接口
 */
export interface CourseRecommendationsResponse {
  /** 用户ID */
  userId: string;
  /** 推荐课程列表 */
  recommendations: CourseRecommendation[];
  /** 时间戳 */
  timestamp?: string;
}

/**
 * 学习记录接口
 * @see src/shared/models/course.models 中的课程/学习相关类型
 */
export interface LearningRecord {
  /** 课程ID */
  courseId: string;
  /** 课时ID */
  lessonId: string;
  /** 学习进度 (0-1) */
  progress: number;
  /** 学习时长（分钟） */
  timeSpent: number;
  /** 完成状态 */
  completionStatus: 'in_progress' | 'completed' | 'skipped';
  /** 难度评分 (1-5) */
  difficultyRating?: number;
  /** 兴趣评分 (1-5) */
  interestRating?: number;
}

/**
 * 用户学习画像接口
 * @see src/shared/models/auth.models 中的用户相关类型
 */
export interface UserLearningProfile {
  /** 用户ID */
  userId: string;
  /** 学习偏好设置 */
  learningPreferences: Record<string, any>;
  /** 技能水平 */
  skillLevels: Record<string, number>;
  /** 兴趣标签列表 */
  interests: string[];
  /** 最后更新时间 */
  lastUpdated?: string;
}

/**
 * 推荐反馈类型
 */
export type FeedbackType = 'like' | 'dislike' | 'click' | 'skip';

/**
 * 推荐反馈接口
 */
export interface RecommendationFeedback {
  /** 课程ID */
  courseId: string;
  /** 反馈类型 */
  feedbackType: FeedbackType;
  /** 上下文信息 */
  context?: Record<string, any>;
}

/**
 * 推荐反馈响应接口
 */
export interface RecommendationFeedbackResponse {
  /** 消息 */
  message: string;
  /** 反馈ID */
  feedbackId: number;
}

/**
 * 学习统计数据接口
 */
export interface LearningStatistics {
  /** 总学习记录数 */
  totalLearningRecords: number;
  /** 完成课程数 */
  completedCourses: number;
  /** 完成率 */
  completionRate: number;
  /** 平均兴趣评分 */
  averageInterestRating: number;
  /** 活跃学习天数 */
  activeLearningDays: number;
}

/**
 * 推荐统计接口
 */
export interface RecommendationStats {
  /** 用户ID */
  userId: string;
  /** 学习统计 */
  learningStatistics: LearningStatistics;
  /** 系统信息 */
  systemInfo: {
    /** 总课程数 */
    totalCourses: number;
    /** 推荐引擎状态 */
    recommendationEngineStatus: 'active' | 'training_needed';
  };
}

/**
 * 模型刷新响应接口
 */
export interface ModelRefreshResponse {
  /** 消息 */
  message: string;
  /** 模型状态 */
  modelStatus: 'trained' | 'untrained';
  /** 训练数据大小 */
  trainingDataSize: {
    /** 用户数 */
    users: number;
    /** 课程数 */
    courses: number;
  };
}
