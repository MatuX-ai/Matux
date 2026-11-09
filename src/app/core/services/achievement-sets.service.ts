/**
 * 成就套装服务（P2-B）
 *
 * 职责：
 * 1. 内置预定义成就套装
 * 2. 计算每个套装的完成进度
 * 3. 提供排序 / 筛选 / 推荐
 * 4. 增强 ExtendedAchievementBadge（添加解锁率 / 套装归属等）
 *
 * @see 桌面端游戏化P2升级.md §3
 */

import { Injectable } from '@angular/core';

import type {
  AchievementBonusReward,
  AchievementSet,
  AchievementSetProgress,
  ExtendedAchievementBadge,
} from '../../features/achievement-integration/models/achievement.model';
import type { AchievementBadge } from '../../features/achievement-integration/models/achievement.model';

// ================ 内置套装 ================

/**
 * 预定义套装
 */
const DEFAULT_SETS: AchievementSet[] = [
  {
    id: 'set-perfect-attendance',
    name: '全勤奖',
    description: '连续 7 / 14 / 30 / 60 / 100 天打卡',
    emoji: '📅',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #34d399 0%, #047857 100%)',
    achievementIds: ['streak-7', 'streak-14', 'streak-30', 'streak-60', 'streak-100'],
    bonusReward: {
      type: 'badge',
      value: 'badge-perfect-attendance',
      label: '全勤徽章',
      emoji: '🎖️',
    },
    order: 1,
  },
  {
    id: 'set-python-master',
    name: 'Python 大师',
    description: '精通 Python 编程的全部核心技能',
    emoji: '🐍',
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, #60a5fa 0%, #1e40af 100%)',
    achievementIds: ['py-variable', 'py-loop', 'py-function', 'py-class', 'py-debug'],
    bonusReward: {
      type: 'title',
      value: 'Python 大师',
      label: '专属称号',
      emoji: '👑',
    },
    order: 2,
  },
  {
    id: 'set-stem-explorer',
    name: 'STEM 探索者',
    description: '完成 STEM 实验的全部主题',
    emoji: '🔬',
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #a78bfa 0%, #6d28d9 100%)',
    achievementIds: ['stem-water', 'stem-electric', 'stem-light', 'stem-chem'],
    bonusReward: {
      type: 'exp',
      value: 500,
      label: '500 EXP',
      emoji: '⚡',
    },
    order: 3,
  },
  {
    id: 'set-social-butterfly',
    name: '社交达人',
    description: '在社区中积极互动',
    emoji: '🦋',
    color: '#ec4899',
    gradient: 'linear-gradient(135deg, #f472b6 0%, #be185d 100%)',
    achievementIds: ['social-first-post', 'social-10-comments', 'social-100-likes'],
    bonusReward: {
      type: 'badge',
      value: 'badge-social-butterfly',
      label: '社交徽章',
      emoji: '💬',
    },
    order: 4,
  },
  {
    id: 'set-first-steps',
    name: '初学者之旅',
    description: '完成入门阶段的所有里程碑',
    emoji: '🌱',
    color: '#22c55e',
    gradient: 'linear-gradient(135deg, #86efac 0%, #15803d 100%)',
    achievementIds: ['first-login', 'first-course', 'first-quiz', 'first-project'],
    bonusReward: {
      type: 'badge',
      value: 'badge-first-steps',
      label: '启程徽章',
      emoji: '🌟',
    },
    order: 0,
  },
];

// ================ Service ================

@Injectable({ providedIn: 'root' })
export class AchievementSetsService {
  /**
   * 获取所有套装（按 order 排序）
   */
  getAllSets(): AchievementSet[] {
    return [...DEFAULT_SETS].sort((a, b) => (a.order ?? 999) - (b.order ?? 999));
  }

  /**
   * 获取单个套装
   */
  getSetById(id: string): AchievementSet | undefined {
    return DEFAULT_SETS.find((s) => s.id === id);
  }

  /**
   * 计算所有套装进度
   */
  computeAllProgress(badges: ExtendedAchievementBadge[]): AchievementSetProgress[] {
    const sets = this.getAllSets();
    return sets.map((set) => this.computeProgress(set, badges));
  }

  /**
   * 计算单个套装进度
   */
  computeProgress(set: AchievementSet, badges: ExtendedAchievementBadge[]): AchievementSetProgress {
    const setBadgeMap = new Map<string, ExtendedAchievementBadge>();
    for (const badge of badges) {
      if (set.achievementIds.includes(badge.id)) {
        setBadgeMap.set(badge.id, badge);
      }
    }

    const unlocked = badges.filter(
      (b) => set.achievementIds.includes(b.id) && b.unlocked
    );

    const remaining = set.achievementIds
      .filter((id) => {
        const badge = setBadgeMap.get(id);
        return !badge || !badge.unlocked;
      })
      .map((id) => {
        const existing = setBadgeMap.get(id);
        return (
          existing ?? {
            id,
            name: this.guessName(id),
            icon: '🔒',
            description: '未知成就',
            unlocked: false,
          }
        );
      });

    const totalCount = set.achievementIds.length;
    const unlockedCount = unlocked.length;
    const completionPercent = totalCount === 0 ? 0 : unlockedCount / totalCount;
    const isCompleted = unlockedCount === totalCount && totalCount > 0;

    return {
      set,
      totalCount,
      unlockedCount,
      completionPercent,
      isCompleted,
      remaining,
    };
  }

  /**
   * 将普通 AchievementBadge 增强为 ExtendedAchievementBadge
   * 自动填充：
   * - 解锁率（基于 mock 公式）
   * - 总解锁人数
   * - 套装归属
   * - 关联学习节点
   */
  enhanceBadges(badges: AchievementBadge[]): ExtendedAchievementBadge[] {
    const sets = this.getAllSets();
    const setMap = new Map<string, AchievementSet>();
    for (const set of sets) {
      for (const aid of set.achievementIds) {
        setMap.set(aid, set);
      }
    }

    return badges.map((badge, idx) => {
      const set = setMap.get(badge.id);
      const rarity = badge.rarity ?? 'common';

      // 基于稀有度模拟解锁率（rarity 越稀有 → unlockRate 越低）
      const unlockRate = this.simulateUnlockRate(rarity, idx);

      return {
        ...badge,
        unlockRate,
        totalHolders: Math.round(unlockRate * 50000),
        setId: set?.id,
        relatedSkillIds: this.guessRelatedSkills(badge.id, badge.category),
        obtainedFrom: this.guessObtainedFrom(badge.id, badge.category),
        pointsValue: this.inferPoints(badge, rarity),
        storyLine: this.guessStoryLine(badge.id, badge.name),
      };
    });
  }

  /**
   * 计算用户成就汇总数据（用于 Hero 区）
   */
  summarize(badges: ExtendedAchievementBadge[]): {
    total: number;
    unlocked: number;
    locked: number;
    unlockRate: number;
    byRarity: Record<string, { total: number; unlocked: number }>;
    totalPoints: number;
    earnedPoints: number;
    recentUnlocks: ExtendedAchievementBadge[];
  } {
    const total = badges.length;
    const unlocked = badges.filter((b) => b.unlocked);
    const locked = badges.filter((b) => !b.unlocked);

    const byRarity: Record<string, { total: number; unlocked: number }> = {
      common: { total: 0, unlocked: 0 },
      uncommon: { total: 0, unlocked: 0 },
      rare: { total: 0, unlocked: 0 },
      epic: { total: 0, unlocked: 0 },
      legendary: { total: 0, unlocked: 0 },
    };

    for (const badge of badges) {
      const rarity = (badge.rarity ?? 'common') as string;
      if (!byRarity[rarity]) byRarity[rarity] = { total: 0, unlocked: 0 };
      byRarity[rarity].total++;
      if (badge.unlocked) byRarity[rarity].unlocked++;
    }

    const totalPoints = badges.reduce((sum, b) => sum + (b.pointsValue ?? 0), 0);
    const earnedPoints = unlocked.reduce((sum, b) => sum + (b.pointsValue ?? 0), 0);
    const recentUnlocks = unlocked
      .filter((b) => b.unlockedDate)
      .sort((a, b) => (b.unlockedDate ?? '').localeCompare(a.unlockedDate ?? ''))
      .slice(0, 5);

    return {
      total,
      unlocked: unlocked.length,
      locked: locked.length,
      unlockRate: total === 0 ? 0 : unlocked.length / total,
      byRarity,
      totalPoints,
      earnedPoints,
      recentUnlocks,
    };
  }

  /**
   * 推荐下一组要解锁的成就（按套装完成度从高到低）
   */
  recommendNext(
    badges: ExtendedAchievementBadge[]
  ): AchievementSetProgress[] {
    const progress = this.computeAllProgress(badges);
    return progress
      .filter((p) => !p.isCompleted && p.unlockedCount > 0)
      .sort((a, b) => b.completionPercent - a.completionPercent)
      .slice(0, 3);
  }

  // ================ 私有辅助方法 ================

  /**
   * 模拟解锁率（mock 数据）
   * 公式：common 75%, uncommon 50%, rare 25%, epic 10%, legendary 3%
   * 加少量随机扰动
   */
  private simulateUnlockRate(
    rarity: string,
    seed: number
  ): number {
    const baseMap: Record<string, number> = {
      common: 0.75,
      uncommon: 0.5,
      rare: 0.25,
      epic: 0.1,
      legendary: 0.03,
    };
    const base = baseMap[rarity] ?? 0.5;
    // 用 seed 产生确定性扰动
    const offset = ((seed * 17) % 13) / 100 - 0.06;
    return Math.max(0, Math.min(1, base + offset));
  }

  /**
   * 推断积分价值
   */
  private inferPoints(badge: AchievementBadge, rarity: string): number {
    const map: Record<string, number> = {
      common: 10,
      uncommon: 25,
      rare: 50,
      epic: 100,
      legendary: 250,
    };
    if (badge.points !== undefined) return badge.points;
    return map[rarity] ?? 10;
  }

  /**
   * 推断关联学习节点 ID
   */
  private guessRelatedSkills(id: string, category?: string): string[] {
    const lower = id.toLowerCase();
    const result: string[] = [];

    if (lower.startsWith('py-')) {
      result.push('py-' + lower.slice(3));
    } else if (lower.startsWith('stem-')) {
      result.push('stem-' + lower.slice(5));
    }

    if (category === 'learning') {
      // 关联到 Python 或 STEM 基础节点
      result.push('py-var', 'py-loop');
    } else if (category === 'experiment') {
      result.push('stem-water', 'stem-electric');
    }

    return Array.from(new Set(result));
  }

  /**
   * 推断解锁来源描述
   */
  private guessObtainedFrom(id: string, category?: string): string {
    if (id.startsWith('streak-')) return '连续打卡奖励';
    if (id.startsWith('social-')) return '社区互动';
    if (id.startsWith('py-')) return '完成 Python 相关课程';
    if (id.startsWith('stem-')) return '完成 STEM 实验';
    if (id.includes('first-')) return '入门里程碑';
    return category === 'challenge' ? '挑战任务' : '学习任务';
  }

  /**
   * 推断故事背景
   */
  private guessStoryLine(id: string, name?: string): string {
    const lower = (name ?? id).toLowerCase();
    if (lower.includes('first')) return '🎯 启程之路：每一个伟大的旅程都从第一步开始';
    if (lower.includes('streak')) return '🔥 坚持的力量：连续打卡让成长更有节奏';
    if (lower.includes('master')) return '👑 大师之路：从初学到精通，你已经走过千山万水';
    if (lower.includes('legendary')) return '🌟 传奇诞生：传说级成就属于那些突破极限的人';
    return '✨ 旅程继续：每一枚徽章都是你独一无二的足迹';
  }

  /**
   * 从 ID 推断显示名称（fallback）
   */
  private guessName(id: string): string {
    return id
      .split('-')
      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
      .join(' ');
  }
}