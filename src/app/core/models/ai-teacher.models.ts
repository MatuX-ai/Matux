/**
 * AI 个性化教师数据模型
 *
 * 基于PRD F-08-AI设计，包含：
 * - 学生学习画像（StudentLearningProfile）
 * - 上下文记忆（ContextMemory）
 * - 个性化知识库（KnowledgeState）
 * - 成长轨迹（GrowthTrajectory）
 * - 智能教学建议（TeachingSuggestion）
 * - AI教师人格设置（TeacherPersona）
 */

// ==================== 学习画像 ====================

/** 学习风格（VARK模型） */
export type LearningStyle = 'visual' | 'auditory' | 'reading' | 'kinesthetic';

/** 技能水平 */
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

/** 知识点掌握状态 */
export type KnowledgeStatus = 'mastered' | 'learning' | 'not_started';

/** 薄弱环节 */
export interface WeakPoint {
  knowledgePoint: string;
  mastery: number;
  errorRate: number;
  suggestion: string;
  lastDetected: string;
}

/** 错误模式统计 */
export interface ErrorPattern {
  errorType: string;
  count: number;
  recentExamples: string[];
  relatedKnowledgePoints: string[];
}

/** 注意力特征 */
export interface AttentionProfile {
  averageFocusDurationMinutes: number;
  tabSwitchFrequency: number;
  hesitationTimeMs: number;
  trend: 'improving' | 'stable' | 'declining';
}

/** 情感状态记录 */
export interface EmotionLog {
  timestamp: string;
  emotion: 'frustrated' | 'confused' | 'excited' | 'anxious' | 'bored' | 'confident' | 'neutral';
  source: 'dialogue' | 'quiz_behavior' | 'login_pattern' | 'error_response';
  confidence: number;
}

/** 学习里程碑 */
export interface LearningMilestone {
  id: string;
  type:
    | 'first_blockly'
    | 'python_intro'
    | 'first_independent_project'
    | 'first_debug'
    | 'streak_30_days'
    | 'breakthrough'
    | 'project_master'
    | 'custom';
  title: string;
  description: string;
  achievedAt: string;
  metadata?: Record<string, unknown>;
}

/** 技能树节点 */
export interface SkillTreeNode {
  id: string;
  name: string;
  category: 'python' | 'javascript' | 'stem' | 'arduino' | 'ai' | 'creative';
  progress: number; // 0.0 - 1.0
  status: KnowledgeStatus;
  children?: SkillTreeNode[];
  parent?: string;
  unlockRequirement?: string;
}

/** 学生学习画像（增强版） */
export interface StudentLearningProfile {
  userId: string;
  displayName: string;

  // 基础信息
  gradeLevel: string;
  ageGroup: string;
  learningStyle: LearningStyle;
  preferredContentType: 'video' | 'text' | 'interactive' | 'project';

  // 能力评估
  abilityDimensions: AbilityDimensions;
  interestPreferences: string[];
  knowledgeMastery: Record<string, number>;

  // 统计数据
  totalStudyTimeMinutes: number;
  completedCoursesCount: number;
  averageQuizScore: number;
  currentStreakDays: number;
  longestStreakDays: number;

  // 新增字段（PRD F-08-AI.1）
  weakPoints: WeakPoint[];
  errorPatterns: Record<string, number>;
  attentionProfile: AttentionProfile;
  emotionalStates: EmotionLog[];
  learningMilestones: LearningMilestone[];
  skillTree: SkillTreeNode[];

  // 画像摘要（供AI教师prompt使用）
  personaSeed: string;

  // 学习目标
  learningGoals: string[];

  // 时间戳
  createdAt: string;
  updatedAt: string;
}

/** 多维能力评估 */
export interface AbilityDimensions {
  programmingThinking: number; // 编程思维 0-100
  algorithmAbility: number; // 算法能力
  debuggingSkill: number; // 调试能力
  projectPractice: number; // 项目实践
  stemExperiment: number; // STEM实验
  codeQuality: number; // 代码规范
  independentCompletion: number; // 独立完成率
  questionQuality: number; // 提问质量
}

// ==================== 上下文记忆 ====================

/** 长期记忆条目 */
export interface LongTermMemory {
  id: string;
  userId: string;
  category: 'learning_summary' | 'key_dialogue' | 'milestone' | 'ability_snapshot';
  content: string;
  tags: string[];
  importance: number; // 0.0 - 1.0
  createdAt: string;
  accessCount: number;
  lastAccessedAt: string;
}

/** 会话记忆 */
export interface SessionMemory {
  sessionId: string;
  userId: string;
  recentMessages: ChatMessage[];
  currentTask: string | null;
  startedAt: string;
  lastActivityAt: string;
}

/** 聊天消息 */
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    knowledgeUsed?: boolean;
    confidence?: number;
    referencedMemories?: string[];
    emotionDetected?: EmotionLog['emotion'];
  };
}

/** 知识状态 */
export interface KnowledgeStateItem {
  knowledgePoint: string;
  mastery: number; // 0.0 - 1.0
  status: KnowledgeStatus;
  prerequisites: string[];
  nextTopics: string[];
  lastPracticed: string | null;
  practiceCount: number;
}

// ==================== 成长轨迹 ====================

/** 能力趋势数据点 */
export interface AbilityTrendPoint {
  date: string;
  programmingThinking: number;
  algorithmAbility: number;
  debuggingSkill: number;
  projectPractice: number;
  stemExperiment: number;
  independentCompletion: number;
}

/** 成长轨迹 */
export interface GrowthTrajectory {
  userId: string;
  abilityTrend: AbilityTrendPoint[];
  milestones: LearningMilestone[];
  aiMonthlyMessage: string;
  statistics: GrowthStatistics;
  interestEvolution: InterestEvolution[];
  peerComparison?: PeerComparisonData;
}

/** 同龄对比数据 (P1-5) */
export interface PeerComparisonData {
  /** 同年级平均水平 */
  peerAverages: Record<string, number>;
  /** 用户当前水平 */
  userAverages: Record<string, number>;
  /** 排名百分位 (0-100) */
  percentileRank: number;
  /** 超越同龄人数比例描述 */
  beatRate: string;
  /** 各维度标签 */
  dimensionLabels: Record<string, string>;
}

/** 成长统计 */
export interface GrowthStatistics {
  totalStudyHours: number;
  completedCourses: number;
  completedProjects: number;
  totalQuestions: number;
  questionQualityTrend: 'improving' | 'stable' | 'declining';
}

/** 兴趣演变 */
export interface InterestEvolution {
  period: string;
  interests: { name: string; percentage: number }[];
}

// ==================== 智能教学建议 ====================

/** 诊断类型 */
export type DiagnosisType =
  | 'prerequisite_missing'
  | 'concept_confusion'
  | 'learning_plateau'
  | 'skill_imbalance'
  | 'attention_decline'
  | 'ai_overdependence';

/** 教学建议 */
export interface TeachingSuggestion {
  id: string;
  diagnosisType: DiagnosisType;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  description: string;
  suggestedAction: string;
  relatedKnowledgePoints: string[];
  recommendedCourses: string[];
  createdAt: string;
  isRead: boolean;
}

/** 每日学习建议 */
export interface DailyLearningSuggestion {
  date: string;
  greeting: string;
  yesterdayReview: string;
  todayGoals: string[];
  weakPointReminder: WeakPoint[];
  suggestedCourses: { courseId: string; reason: string }[];
  aiMessage: string;
}

// ==================== AI 教师人格设置 ====================

/** 称呼方式 */
export type AddressMode = 'name' | 'nickname' | 'classmate';

/** 语言风格 */
export type LanguageStyle = 'lively' | 'formal' | 'concise' | 'humorous';

/** 提示程度 */
export type HintLevel = 'direct_answer' | 'guided_thinking' | 'direction_only';

/** 鼓励频率 */
export type EncouragementFrequency = 'high' | 'moderate' | 'milestone_only';

/** Emoji使用程度 */
export type EmojiUsage = 'heavy' | 'moderate' | 'none';

/** AI教师人格配置 */
export interface TeacherPersona {
  userId: string;
  addressMode: AddressMode;
  nickname: string;
  languageStyle: LanguageStyle;
  hintLevel: HintLevel;
  encouragementFrequency: EncouragementFrequency;
  strictness: 'lenient' | 'standard' | 'strict';
  emojiUsage: EmojiUsage;
}

// ==================== AI 教师请求/响应 ====================

/** AI教师对话请求 */
export interface AITeacherChatRequest {
  userId: string;
  message: string;
  sessionId: string;
  context?: {
    currentPage?: string;
    currentCourse?: string;
    currentTask?: string;
  };
}

/** AI教师对话响应 */
export interface AITeacherChatResponse {
  reply: string;
  sessionId: string;
  emotionDetected: EmotionLog['emotion'];
  memoriesReferenced: string[];
  knowledgeUsed: boolean;
  suggestions: TeachingSuggestion[];
  model: string;
  confidence: number;
  inferenceTimeMs: number;
}

/** 学习画像更新请求 */
export interface LearningProfileUpdateRequest {
  weakPoints?: WeakPoint[];
  errorPatterns?: Record<string, number>;
  attentionProfile?: Partial<AttentionProfile>;
  emotionalStates?: EmotionLog[];
  learningMilestones?: LearningMilestone[];
  skillTree?: SkillTreeNode[];
  abilityDimensions?: Partial<AbilityDimensions>;
  knowledgeMastery?: Record<string, number>;
}
