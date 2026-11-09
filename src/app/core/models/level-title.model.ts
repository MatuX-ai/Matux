/**
 * 等级称号数据契约（P0-3 等级系统叙事化）
 *
 * 10 级阶梯对应 5 个段位，详见 LevelTitleService。
 *
 * @see docs/07-产品文档/MatuX_Desktop_最终需求文档.md §6.9 趣味性原则
 * @see 桌面端游戏化P0升级.md §2.3 P0-3
 */

/** 5 个段位枚举（顺序与 Lv 绑定） */
export type LevelTier = 'bronze' | 'silver' | 'gold' | 'diamond' | 'star';

/** 单个等级条目（设计中英文文案由 i18n 提供，此处仅承载数据） */
export interface LevelTitleEntry {
  /** 等级（1-10） */
  level: number;
  /** 段位 */
  tier: LevelTier;
  /** 下一等级解锁徽章 emoji（满级为 null） */
  nextBadgeIcon: string | null;
  /** 累计 EXP 门槛（含本级） */
  cumulativeExp: number;
}
