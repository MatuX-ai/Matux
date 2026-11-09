/**
 * 排行榜赛季服务（P1-1）
 *
 * 职责：
 * - 计算当前赛季（按季度切分：Q1=1-3月 / Q2=4-6月 / Q3=7-9月 / Q4=10-12月）
 * - 实时倒计时（精度：天）
 * - 终奖预览（3 档：Top 3 / Top 10 / Top 50）
 *
 * 数据契约：
 * - 赛季名按年份 + 季度动态生成（例：2026 秋季赛）
 * - 90 天一赛季（10/1 起 Q4，1/1 起 Q1）
 * - 终奖 3 档固定：👑 Top 3 / 🏅 Top 10 / ⭐ Top 50
 *
 * @see 桌面端游戏化P1升级.md §2.1
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface SeasonInfo {
  /** 赛季唯一 id，例 `season-2026-q4` */
  id: string;
  /** 显示名（中文例：`2026 秋季赛`） */
  name: string;
  /** 起始日期（含） */
  startDate: Date;
  /** 截止日期（含） */
  endDate: Date;
  /** 赛季天数（90） */
  durationDays: number;
  /** 第几赛季（自 2024-Q1 起） */
  seasonNumber: number;
}

export interface SeasonReward {
  /** 名次区间（例 `1-3`） */
  rankRange: string;
  /** 标题（例 `冠军` / `精英` / `新星`） */
  title: string;
  /** 奖励 EXP */
  exp: number;
  /** 角标 emoji */
  badge: string;
  /** 卡片渐变色 hex */
  gradient: [string, string];
}

export interface TimeRemaining {
  days: number;
  hours: number;
  minutes: number;
  /** 是否已结束 */
  expired: boolean;
}

const EPOCH = new Date(2024, 0, 1);

@Injectable({
  providedIn: 'root',
})
export class SeasonService {
  private readonly currentSubject = new BehaviorSubject<SeasonInfo>(this.computeSeason(new Date()));
  /** 当前赛季信息流（每分钟自动刷新倒计时由调用方计算） */
  readonly currentSeason$: Observable<SeasonInfo> = this.currentSubject.asObservable();

  /** 3 档固定终奖 */
  private readonly REWARDS: ReadonlyArray<SeasonReward> = [
    {
      rankRange: '1-3',
      title: '冠军',
      exp: 1000,
      badge: '👑',
      gradient: ['#fbbf24', '#f59e0b'],
    },
    {
      rankRange: '4-10',
      title: '精英',
      exp: 500,
      badge: '🏅',
      gradient: ['#94a3b8', '#64748b'],
    },
    {
      rankRange: '11-50',
      title: '新星',
      exp: 200,
      badge: '⭐',
      gradient: ['#fb923c', '#c2410c'],
    },
  ];

  /** 获取当前赛季快照 */
  getCurrentSeason(now: Date = new Date()): SeasonInfo {
    return this.computeSeason(now);
  }

  /** 计算赛季剩余时间（精度：天/时/分） */
  timeRemaining(now: Date = new Date()): TimeRemaining {
    const season = this.getCurrentSeason(now);
    const ms = season.endDate.getTime() - now.getTime();
    if (ms <= 0) {
      return { days: 0, hours: 0, minutes: 0, expired: true };
    }
    const days = Math.floor(ms / 86400000);
    const hours = Math.floor((ms % 86400000) / 3600000);
    const minutes = Math.floor((ms % 3600000) / 60000);
    return { days, hours, minutes, expired: false };
  }

  /** 3 档终奖预览（按名次降序；返回深拷贝避免污染） */
  upcomingRewards(): SeasonReward[] {
    return this.REWARDS.map((r) => ({ ...r, gradient: [...r.gradient] as [string, string] }));
  }

  /**
   * 计算给定日期所属赛季
   * - Q1: 1/1 - 3/31
   * - Q2: 4/1 - 6/30
   * - Q3: 7/1 - 9/30
   * - Q4: 10/1 - 12/31
   */
  private computeSeason(now: Date): SeasonInfo {
    const year = now.getFullYear();
    const month = now.getMonth(); // 0-indexed
    const quarter = Math.floor(month / 3) + 1; // 1-4
    const quarterStartMonth = (quarter - 1) * 3;
    const startDate = new Date(year, quarterStartMonth, 1);
    // 截止 = 下一季度首日 - 1 天（即 23:59:59.999 of 月末）
    const endDate = new Date(year, quarterStartMonth + 3, 0, 23, 59, 59, 999);
    const id = `season-${year}-q${quarter}`;
    // 赛季名（中文）按季度映射
    const SEASON_NAMES_ZH: Record<number, string> = {
      1: '春季赛',
      2: '夏季赛',
      3: '秋季赛',
      4: '冬季赛',
    };
    const name = `${year} ${SEASON_NAMES_ZH[quarter]}`;
    const seasonNumber = this.computeSeasonNumber(year, quarter);
    const durationDays = Math.ceil((endDate.getTime() - startDate.getTime()) / 86400000);
    return { id, name, startDate, endDate, durationDays, seasonNumber };
  }

  /** 测试用：手动刷新当前赛季（一般不需要） */
  refresh(now: Date = new Date()): void {
    this.currentSubject.next(this.computeSeason(now));
  }

  private computeSeasonNumber(year: number, quarter: number): number {
    const diffYears = year - EPOCH.getFullYear();
    return diffYears * 4 + quarter;
  }
}
