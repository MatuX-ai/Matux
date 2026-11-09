/**
 * 学习地图数据模型（P2-A）
 *
 * 在 SkillTreeNode 基础上构建可视化节点地图，包含：
 * - 节点状态（locked/available/in_progress/mastered/legendary）
 * - 节点连接（前置 → 后置）
 * - 学科 Track（多主题）
 * - 关联成就 / 课程
 *
 * @see 桌面端游戏化P2升级.md §2（P2-A 学习地图）
 */

import type { SkillTreeNode } from './ai-teacher.models';

/** 学科分类 */
export type LearningMapCategory =
  | 'python'
  | 'stem'
  | 'algorithm'
  | 'project'
  | 'creation'
  | 'javascript'
  | 'arduino'
  | 'ai';

/** 节点状态（5 种） */
export type LearningMapStatus =
  | 'locked' // 🔒 锁定：前置未完成
  | 'available' // ⭕ 可学：前置已满足，等待学习
  | 'in_progress' // 🔄 进行中：已开始但未完成
  | 'mastered' // ✅ 已掌握：完成度 ≥ 0.8
  | 'legendary'; // 🏆 传说级：完成度 1.0 且获得特殊奖励

/** 节点稀有度（视觉强化） */
export type LearningMapRarity = 'common' | 'rare' | 'epic' | 'legendary';

/** 关联课程 */
export interface RelatedCourse {
  id: string;
  title: string;
  emoji?: string;
}

/**
 * 学习地图节点（核心数据）
 */
export interface LearningMapNode {
  /** 节点唯一 ID（如 'py-variable'、'stem-water'） */
  id: string;
  /** 节点名称（如 '变量与数据类型'） */
  name: string;
  /** 详细描述 */
  description: string;
  /** 图标 emoji 或 Material icon 名 */
  icon: string;
  /** 学科分类 */
  category: LearningMapCategory;
  /** 章节层级（1 = 入门，5 = 大师） */
  tier: 1 | 2 | 3 | 4 | 5;
  /** 当前状态 */
  status: LearningMapStatus;
  /** 完成进度 0-1 */
  progress: number;
  /** 前置节点 ID 列表（必须全部 mastered 才能解锁） */
  prerequisites: string[];
  /** 后置节点 ID 列表（计算得出，可选缓存） */
  unlocks?: string[];
  /** 关联课程 */
  relatedCourses?: RelatedCourse[];
  /** 关联成就 ID */
  relatedAchievementIds?: string[];
  /** 预计学习时长（分钟） */
  estimatedMinutes: number;
  /** 节点稀有度（视觉强化用） */
  rarity?: LearningMapRarity;
  /** 解锁时间（mastered 时） */
  masteredAt?: string;
}

/**
 * 学习地图轨道（按学科分组）
 */
export interface LearningMapTrack {
  /** Track ID */
  id: string;
  /** Track 名称 */
  name: string;
  /** Track emoji 图标 */
  emoji: string;
  /** Track 主色（HEX） */
  color: string;
  /** Track 渐变（CSS gradient） */
  gradient: string;
  /** Track 描述 */
  description: string;
  /** Track 下所有节点 */
  nodes: LearningMapNode[];
  /** 总节点数 */
  totalNodes: number;
  /** 已掌握节点数 */
  masteredNodes: number;
  /** 进行中节点数 */
  inProgressNodes: number;
  /** 完成度 0-1 */
  completionPercent: number;
  /** 是否为主线（默认 true） */
  isMainTrack?: boolean;
}

/**
 * 学习地图视图模式
 */
export type LearningMapViewMode = 'map' | 'list';

/**
 * 节点位置（用于 SVG 渲染）
 */
export interface LearningMapNodePosition {
  node: LearningMapNode;
  x: number;
  y: number;
}

/**
 * 连线（用于 SVG 渲染）
 */
export interface LearningMapConnection {
  from: LearningMapNodePosition;
  to: LearningMapNodePosition;
  /** 路径 SVG d 属性 */
  path: string;
  /** 是否已完成（from 已 mastered） */
  isCompleted: boolean;
  /** 是否为当前路径（in_progress 节点连向下一可学节点） */
  isActivePath: boolean;
}

/**
 * 学习地图状态聚合
 */
export interface LearningMapSummary {
  totalNodes: number;
  masteredNodes: number;
  inProgressNodes: number;
  availableNodes: number;
  lockedNodes: number;
  legendaryNodes: number;
  overallPercent: number;
  recommendedNext?: LearningMapNode;
}

/**
 * 推荐路径（用于"下一步"按钮）
 */
export interface LearningMapRecommendation {
  node: LearningMapNode;
  reason: string;
  estimatedMinutes: number;
  prerequisiteCount: number;
}

/**
 * 视图模式配置
 */
export interface LearningMapViewConfig {
  mode: LearningMapViewMode;
  selectedTrackId?: string;
  selectedNodeId?: string;
  zoom: number; // 0.5-1.5
}

/**
 * 默认配置
 */
export const DEFAULT_LEARNING_MAP_CONFIG: LearningMapViewConfig = {
  mode: 'map',
  zoom: 1,
};

/**
 * 状态可视化配置
 */
export const NODE_STATUS_CONFIG: Record<
  LearningMapStatus,
  {
    label: string;
    emoji: string;
    color: string;
    glow: string;
    description: string;
  }
> = {
  locked: {
    label: '锁定',
    emoji: '🔒',
    color: '#94a3b8',
    glow: 'none',
    description: '前置技能未解锁',
  },
  available: {
    label: '可学',
    emoji: '⭕',
    color: '#0ea5e9',
    glow: '0 0 12px rgba(14, 165, 233, 0.3)',
    description: '已具备前置条件，可开始学习',
  },
  in_progress: {
    label: '学习中',
    emoji: '🔄',
    color: '#3b82f6',
    glow: '0 0 16px rgba(59, 130, 246, 0.5)',
    description: '正在进行中',
  },
  mastered: {
    label: '已掌握',
    emoji: '✅',
    color: '#10b981',
    glow: '0 0 12px rgba(16, 185, 129, 0.4)',
    description: '已掌握该技能',
  },
  legendary: {
    label: '传说',
    emoji: '🏆',
    color: '#f59e0b',
    glow: '0 0 20px rgba(245, 158, 11, 0.6)',
    description: '完美掌握并解锁特殊奖励',
  },
};

/**
 * Track 主题配置
 */
export const TRACK_THEMES: Record<
  LearningMapCategory,
  {
    label: string;
    emoji: string;
    color: string;
    gradient: string;
  }
> = {
  python: {
    label: 'Python 基础',
    emoji: '🐍',
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
  },
  stem: {
    label: 'STEM 实验',
    emoji: '🔬',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #10b981 0%, #047857 100%)',
  },
  algorithm: {
    label: '算法进阶',
    emoji: '🧮',
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
  },
  project: {
    label: '项目实战',
    emoji: '🛠️',
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)',
  },
  creation: {
    label: '创作工坊',
    emoji: '🎨',
    color: '#ec4899',
    gradient: 'linear-gradient(135deg, #ec4899 0%, #be185d 100%)',
  },
  javascript: {
    label: 'JavaScript',
    emoji: '📜',
    color: '#eab308',
    gradient: 'linear-gradient(135deg, #eab308 0%, #a16207 100%)',
  },
  arduino: {
    label: 'Arduino',
    emoji: '⚡',
    color: '#06b6d4',
    gradient: 'linear-gradient(135deg, #06b6d4 0%, #0e7490 100%)',
  },
  ai: {
    label: 'AI 探索',
    emoji: '🤖',
    color: '#6366f1',
    gradient: 'linear-gradient(135deg, #6366f1 0%, #4338ca 100%)',
  },
};

/**
 * 从 SkillTreeNode 创建 LearningMapNode（辅助工具）
 */
export function fromSkillTreeNode(node: SkillTreeNode): LearningMapNode {
  let status: LearningMapStatus;
  if (node.status === 'mastered') {
    status = node.progress >= 1 ? 'legendary' : 'mastered';
  } else if (node.status === 'learning') {
    status = 'in_progress';
  } else {
    status = 'locked';
  }

  return {
    id: node.id,
    name: node.name,
    description: node.unlockRequirement ?? '开始学习这个技能节点',
    icon: inferIconFromCategory(node.category),
    category: (node.category as LearningMapCategory) ?? 'python',
    tier: 1,
    status,
    progress: node.progress,
    prerequisites: node.parent ? [node.parent] : [],
    estimatedMinutes: 30,
    rarity: 'common',
  };
}

/**
 * 根据学科推测 emoji 图标
 */
function inferIconFromCategory(category: string): string {
  const map: Record<string, string> = {
    python: '🐍',
    javascript: '📜',
    stem: '🔬',
    arduino: '⚡',
    ai: '🤖',
    creative: '🎨',
  };
  return map[category] ?? '⭐';
}