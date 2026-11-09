/**
 * 成就系统数据模型
 *
 * 定义成就、徽章、进度等核心数据结构
 * 对应后端 gamification 模块的成就系统
 */

/** 成就徽章 */
export interface AchievementBadge {
  id: string;
  name: string;
  icon: string;
  description: string;
  unlocked: boolean;
  unlockedDate?: string;
  category?: AchievementCategory;
  rarity?: AchievementRarity;
  /** 积分价值（P2-B） */
  points?: number;
}

/**
 * 扩展成就徽章（P2-B）
 * 补充：全球解锁率、解锁人数、关联学习节点、套装归属、解锁来源
 */
export interface ExtendedAchievementBadge extends AchievementBadge {
  /** 全球解锁率 0-1（P2-B） */
  unlockRate?: number;
  /** 解锁人数（P2-B） */
  totalHolders?: number;
  /** 关联学习地图节点 ID 列表（P2-C 联动） */
  relatedSkillIds?: string[];
  /** 所属套装 ID（P2-B） */
  setId?: string;
  /** 解锁来源描述（如「完成 Python 循环课程」） */
  obtainedFrom?: string;
  /** 积分价值（P2-B） */
  pointsValue?: number;
  /** 描述上的故事背景（P2-B 叙事化） */
  storyLine?: string;
  /** 解锁等级门槛（可选） */
  requiredLevel?: number;
}

/**
 * 成就套装（P2-B）
 * 一组相关成就的聚合，完成后发放额外奖励
 */
export interface AchievementSet {
  id: string;
  name: string;
  description: string;
  emoji: string;
  /** 套装主色 */
  color: string;
  /** 套装渐变 */
  gradient: string;
  /** 套装内的成就 ID 列表 */
  achievementIds: string[];
  /** 完成后 bonus 奖励 */
  bonusReward?: AchievementBonusReward;
  /** 排序权重 */
  order?: number;
}

/**
 * 套装完成奖励（P2-B）
 */
export interface AchievementBonusReward {
  type: 'exp' | 'badge' | 'title';
  value: number | string;
  label: string;
  emoji?: string;
}

/**
 * 套装进度统计（P2-B）
 */
export interface AchievementSetProgress {
  set: AchievementSet;
  totalCount: number;
  unlockedCount: number;
  /** 0-1 */
  completionPercent: number;
  /** 是否已完成 */
  isCompleted: boolean;
  /** 未解锁的成就（用于提示用户） */
  remaining: ExtendedAchievementBadge[];
}

/** 成就分类 */
export enum AchievementCategory {
  LEARNING = 'learning',
  EXPERIMENT = 'experiment',
  SOCIAL = 'social',
  CHALLENGE = 'challenge',
  HIDDEN = 'hidden',
}

/** 成就稀有度 */
export enum AchievementRarity {
  COMMON = 'common',
  UNCOMMON = 'uncommon',
  RARE = 'rare',
  EPIC = 'epic',
  LEGENDARY = 'legendary',
}

/** 成就进度里程碑 */
export interface ProgressMilestone {
  id: string;
  title: string;
  description: string;
  icon: string;
  progress: number;
  target: number;
  completed: boolean;
  category: AchievementCategory;
}

/** 成就进度 */
export interface AchievementProgress {
  totalBadges: number;
  unlockedBadges: number;
  overallProgress: number;
  completionPercentage: number;
  averageScore: number;
  totalAchievements: number;
  completedAchievements: number;
  categoryProgress: Record<AchievementCategory, number>;
  recentUnlocks: AchievementBadge[];
  milestones: ProgressMilestone[];
}

/** 成就解锁记录 */
export interface AchievementUnlockEvent {
  badgeId: string;
  badgeName: string;
  unlockedAt: string;
  pointsAwarded?: number;
}

/** 成就类型 */
export enum AchievementType {
  BADGE = 'badge',
  TROPHY = 'trophy',
  MEDAL = 'medal',
  CERTIFICATE = 'certificate',
  STAR = 'star',
}

/** 成就状态 */
export enum AchievementStatus {
  LOCKED = 'locked',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  EXPIRED = 'expired',
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  REVISION = 'revision',
}

/** 成就排序字段 */
export enum AchievementSortBy {
  NAME = 'name',
  DATE = 'date',
  RARITY = 'rarity',
  CATEGORY = 'category',
  PROGRESS = 'progress',
}

/** 成就排序选项 */
export interface AchievementSort {
  sortBy: AchievementSortBy;
  ascending: boolean;
}

/** 成就筛选条件 */
export interface AchievementFilter {
  category?: AchievementCategory;
  status?: AchievementStatus;
  type?: AchievementType;
  rarity?: AchievementRarity;
  searchQuery?: string;
}

/** 成就条件 */
export interface AchievementCondition {
  text: string;
  done: boolean;
}

/** 完整成就条目 */
export interface Achievement {
  id: string;
  name: string;
  icon: string;
  description: string;
  type: AchievementType;
  status: AchievementStatus;
  category: AchievementCategory;
  rarity: AchievementRarity;
  progress: number;
  target: number;
  unlockedDate?: string;
  points: number;
  tags: string[];
  requirements: string[];
  conditions?: AchievementCondition[];
  txHash?: string;
}

/** 成就审核记录 */
export interface AchievementReview {
  id: string;
  achievementId: string;
  achievementName: string;
  userId: number;
  userName: string;
  status: AchievementStatus;
  comment: string;
  reviewerId?: number;
  reviewerName?: string;
  submittedAt: string;
  reviewedAt?: string;
}

/** 成就统计 */
export interface AchievementStats {
  totalPoints: number;
  badgesCount: number;
  currentStreak: number;
  longestStreak: number;
  lastActiveDate: string;
}
