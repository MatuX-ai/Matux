/**
 * 等级称号服务（P0-3 数据层）
 *
 * 提供 10 级阶梯查询、下一级预览、段位色查询。
 * 文案由 i18n 注入（i18n key: level.title.{n} / level.tier.{tier}），
 * 本服务只承载结构化数据。
 *
 * @see 桌面端游戏化P0升级.md §2.3 P0-3
 */

import { Injectable } from '@angular/core';

import type { LevelTier, LevelTitleEntry } from '../models/level-title.model';

/**
 * 10 级称号阶梯表
 * - cumulativeExp: 升到该等级所需的最低累计 EXP
 * - nextBadgeIcon: 升到该等级时解锁的徽章 emoji 预览
 */
const LEVEL_TABLE: ReadonlyArray<LevelTitleEntry> = [
  { level: 1, tier: 'bronze', nextBadgeIcon: '🌱', cumulativeExp: 0 },
  { level: 2, tier: 'bronze', nextBadgeIcon: '📝', cumulativeExp: 100 },
  { level: 3, tier: 'bronze', nextBadgeIcon: '🔁', cumulativeExp: 300 },
  { level: 4, tier: 'silver', nextBadgeIcon: '🛡️', cumulativeExp: 700 },
  { level: 5, tier: 'silver', nextBadgeIcon: '🪄', cumulativeExp: 1500 },
  { level: 6, tier: 'gold', nextBadgeIcon: '🧮', cumulativeExp: 3000 },
  { level: 7, tier: 'gold', nextBadgeIcon: '🔍', cumulativeExp: 5500 },
  { level: 8, tier: 'gold', nextBadgeIcon: '🏛️', cumulativeExp: 9000 },
  { level: 9, tier: 'diamond', nextBadgeIcon: '🤖', cumulativeExp: 14000 },
  { level: 10, tier: 'star', nextBadgeIcon: '👑', cumulativeExp: 21000 },
];

const MAX_LEVEL = LEVEL_TABLE.length;

/** 段位色 hex（与 _stem-tokens.scss 段位色对应） */
const TIER_COLORS: Readonly<Record<LevelTier, string>> = {
  bronze: '#b45309',
  silver: '#94a3b8',
  gold: '#f59e0b',
  diamond: '#06b6d4',
  star: '#ec4899',
};

@Injectable({
  providedIn: 'root',
})
export class LevelTitleService {
  /** 当前等级（越界自动截断） */
  getTitleByLevel(level: number): LevelTitleEntry {
    const safe = Math.max(1, Math.min(MAX_LEVEL, Math.floor(level || 1)));
    return LEVEL_TABLE[safe - 1];
  }

  /** 下一级预览；满级返回 null */
  getNextTitle(currentLevel: number): LevelTitleEntry | null {
    if (currentLevel >= MAX_LEVEL) return null;
    return LEVEL_TABLE[currentLevel]; // currentLevel 是当前，下一级索引 = currentLevel
  }

  /** 段位 hex 色（用于 box-shadow / border） */
  getTierColor(tier: LevelTier): string {
    return TIER_COLORS[tier];
  }

  /** 当前等级升到下一级还需要的 EXP；满级返回 0 */
  expToNext(currentLevel: number, currentTotalExp: number): number {
    const next = this.getNextTitle(currentLevel);
    if (!next) return 0;
    return Math.max(0, next.cumulativeExp - currentTotalExp);
  }

  /** 是否已达满级 */
  isMaxLevel(level: number): boolean {
    return level >= MAX_LEVEL;
  }

  /** 最大等级常量 */
  get maxLevel(): number {
    return MAX_LEVEL;
  }
}
