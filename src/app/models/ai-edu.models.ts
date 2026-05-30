/**
 * AI-Edu-for-Kids 课程学习数据模型
 */

export interface AIEduModule {
  id: number;
  module_code: string;
  name: string;
  description: string;
  category: string;
  grade_ranges: GradeRange[];
  expected_lessons: number;
  expected_duration_minutes: number;
  is_active: boolean;
  display_order: number;
}

export interface GradeRange {
  min: number;
  max: number;
  label?: string;
}

export interface AIEduLesson {
  id: number;
  module_id: number;
  lesson_code: string;
  title: string;
  subtitle?: string;
  content_type: LessonContentType;
  content_url?: string;
  resources: LessonResource[];
  learning_objectives: string[];
  knowledge_points: string[];
  estimated_duration_minutes: number;
  has_quiz: boolean;
  quiz_passing_score: number;
  has_practice: boolean;
  practice_type?: PracticeType;
  base_points: number;
  is_active: boolean;
  display_order: number;
}

export type LessonContentType = 'theory' | 'practice' | 'hybrid';

export type PracticeType = 'python' | 'scratch' | 'ar_vr' | 'hardware';

export interface LessonResource {
  type: ResourceType;
  url: string;
  title?: string;
  description?: string;
}

export type ResourceType = 'video' | 'code' | 'dataset' | 'html' | 'scratch' | 'document';

export interface LearningProgress {
  progress_id: number;
  lesson_id: number;
  lesson_code: string;
  lesson_title: string;
  module_id?: number;
  module_name?: string;
  progress_percentage: number;
  status: ProgressStatus;
  time_spent_seconds: number;
  quiz_score?: number;
  code_quality_score?: number;
  attempt_count: number;
  points_earned: number;
  start_time?: string;
  completion_time?: string;
  last_accessed_time: string;
}

export type ProgressStatus = 'not_started' | 'in_progress' | 'completed';

export interface LearningStatistics {
  total_courses: number;
  completed_courses: number;
  in_progress_courses: number;
  not_started_courses: number;
  total_time_hours: number;
  average_quiz_score: number;
  average_code_score: number;
  total_points: number;
  completion_rate: number;
}

export interface Achievement {
  id: number;
  achievement_code: string;
  name: string;
  description: string;
  icon_url: string;
  rarity: AchievementRarity;
  unlock_conditions: UnlockCondition[];
  points_reward: number;
  integral_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
}

export type AchievementRarity = 'common' | 'rare' | 'epic' | 'legendary' | 'mythic';

export interface UnlockCondition {
  type: string;
  count?: number;
  module_id?: number;
  lesson_id?: number;
}

export interface RewardRule {
  id: number;
  rule_code: string;
  rule_name: string;
  rule_type: RewardRuleType;
  base_points: number;
  grade_multipliers: Record<string, number>;
  quality_coefficients: Record<string, number>;
  streak_multipliers: Record<number, number>;
  is_active: boolean;
}

export type RewardRuleType =
  | 'theory'
  | 'practice'
  | 'project'
  | 'achievement'
  | 'streak'
  | 'special';

export interface ProgressUpdateRequest {
  lesson_id: number;
  progress_percentage: number;
  time_spent_seconds: number;
  quiz_score?: number;
  code_quality_score?: number;
  status: string;
}

export interface LessonCompletionRequest {
  lesson_id: number;
  quiz_score?: number;
  code_quality_score?: number;
  time_spent_seconds: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

// ==================== 课程播放器相关类型 ====================

/**
 * 课程资源类型（扩展版）
 */
export type ExtendedResourceType =
  | 'video'
  | 'code'
  | 'html'
  | 'document'
  | 'quiz'
  | 'dataset'
  | 'scratch';

/**
 * 课程资源详情
 */
export interface CourseResource {
  type: ExtendedResourceType;
  url?: string; // 视频/HTML 的 URL
  content?: string; // 代码/文档的内容
  language?: string; // 编程语言 (code 类型使用)
  title?: string;
  description?: string;
  duration_minutes?: number; // 预计时长
  is_interactive?: boolean; // 是否可交互
}

/**
 * 课程播放器状态
 */
export interface CoursePlayerState {
  moduleId: number;
  lessonId: number;
  lesson: AIEduLesson | null;
  currentResourceIndex: number;
  currentResource: CourseResource | null;
  isPlaying: boolean; // 是否在播放中
  progress: number; // 进度百分比 (0-100)
  isLoading: boolean; // 加载状态
  error: string | null; // 错误信息
}

/**
 * 学习笔记
 */
export interface LearningNote {
  id?: number;
  user_id: number;
  lesson_id: number;
  content: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * 代码执行请求
 */
export interface CodeExecutionRequest {
  code: string;
  language: string;
  timeout?: number; // 超时时间（秒）
}

/**
 * 代码执行结果
 */
export interface CodeExecutionResult {
  success: boolean;
  output: string;
  error?: string;
  execution_time: number; // 执行时间（秒）
  memory_usage?: number; // 内存使用（MB）
}

// ==================== 在线测验相关类型 ====================

/**
 * 题目类型
 */
export type QuestionType = 'choice' | 'fill' | 'code' | 'matching';

/**
 * 测验题目
 */
export interface QuizQuestion {
  id: number;
  type: QuestionType;
  content: string; // 题干
  options?: string[]; // 选择题选项
  correct_answer?: any; // 正确答案
  points: number; // 分值
  difficulty: number; // 难度系数 (1-5)
  explanation?: string; // 答案解析
}

/**
 * 用户答案
 */
export interface QuizAnswer {
  question_id: number;
  answer: any; // 用户答案
}

/**
 * 测验状态
 */
export interface QuizState {
  quiz_id: string;
  lesson_id: number;
  questions: QuizQuestion[];
  current_question_index: number;
  answers: Map<number, any>; // 已答题目
  started_at: string;
  time_limit_minutes?: number; // 时间限制（分钟）
  remaining_time?: number; // 剩余时间（秒）
}

/**
 * 测验结果
 */
export interface QuizResult {
  quiz_id: string;
  score: number; // 得分
  total_score: number; // 总分
  accuracy: number; // 正确率 (0-1)
  time_spent_seconds: number; // 用时
  points_earned: number; // 获得积分
  passed: boolean; // 是否通过
}

/**
 * 测验历史记录
 */
export interface QuizHistory {
  user_id: number;
  history: QuizHistoryItem[];
  total_count: number;
  average_accuracy: number;
  total_points: number;
}

export interface QuizHistoryItem {
  quiz_id: string;
  lesson_id: number;
  lesson_title: string;
  score: number;
  total_score: number;
  accuracy: number;
  passed: boolean;
  completed_at: string;
  points_earned: number;
}
