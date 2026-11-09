/**
 * 每日签到服务（P0-4）
 *
 * 职责：
 * - 持久化今日签到状态（localStorage）
 * - 计算连续签到天数（跨日断签 streak 重置）
 * - 签到返 EXP + streak + 3 张主推任务卡
 * - 提供 Observable 状态流供组件订阅
 *
 * localStorage keys:
 *   - daily-checkin:{userId}:{YYYY-MM-DD} = "1"
 *   - daily-checkin:{userId}:streak = number（最后连续天数）
 *   - daily-checkin:{userId}:lastDate = "YYYY-MM-DD"
 *
 * @see 桌面端游戏化P0升级.md §2.4
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';

import type { DailyTask } from '../../user/student/services/student-dashboard-data.service';

export interface CheckinRewardCard {
  taskId: string;
  title: string;
  icon: string;
  rewardExp: number;
  rarity: DailyTask['rarity'];
}

export interface CheckinResult {
  exp: number;
  streak: number;
  rewards: CheckinRewardCard[];
  /** 距离下一里程碑还差几天 */
  nextMilestoneDays: number;
}

@Injectable({
  providedIn: 'root',
})
export class DailyCheckinService {
  private readonly checkedInTodaySubject = new BehaviorSubject<boolean>(false);
  readonly isCheckedInToday$: Observable<boolean> = this.checkedInTodaySubject.asObservable();
  /** 当前连续签到天数（展示用） */
  streakDays = 0;

  private userId: string | null = null;
  private today: string = this.toDateKey(new Date());

  /** 由父组件在挂载时调用一次，注入当前用户与候选任务池 */
  bootstrap(userId: string | null, _allTasks: DailyTask[]): void {
    this.userId = userId;
    this.today = this.toDateKey(new Date());
    this.streakDays = this.loadStreak();
    this.checkedInTodaySubject.next(this.isCheckedInToday());
  }

  /** 当前是否已签到 */
  isCheckedInToday(): boolean {
    if (!this.userId) return false;
    try {
      return localStorage.getItem(this.checkedKey()) === '1';
    } catch {
      return false;
    }
  }

  /**
   * 执行签到；同日重复调用返 null。
   * 持久化 today + 更新 streak，连续天数按 lastDate 跨日累加。
   */
  checkIn(candidateTasks: DailyTask[]): CheckinResult | null {
    if (this.isCheckedInToday()) return null;

    const today = this.toDateKey(new Date());
    const lastDate = this.loadLastDate();
    let newStreak = 1;
    if (lastDate) {
      const last = new Date(lastDate);
      const cur = new Date(today);
      const diff = Math.round((cur.getTime() - last.getTime()) / 86400000);
      if (diff === 1) {
        newStreak = this.streakDays + 1;
      } else if (diff <= 0) {
        // 同日或回退，忽略
      } else {
        newStreak = 1; // 断签
      }
    }
    this.streakDays = newStreak;
    this.persist(today, newStreak);

    // 选 3 张主推卡
    const rewards = this.pickRewards(candidateTasks, 3);

    // 计算下一里程碑
    const milestones = [3, 7, 14, 30, 100, 365];
    const nextMilestone = milestones.find((m) => m > newStreak) ?? 0;
    const nextMilestoneDays = nextMilestone ? nextMilestone - newStreak : 0;

    this.checkedInTodaySubject.next(true);

    return {
      exp: 50,
      streak: newStreak,
      rewards,
      nextMilestoneDays,
    };
  }

  /** 仅刷新"今天"键（用于长会话跨天时刷新 UI） */
  refreshToday(): void {
    this.today = this.toDateKey(new Date());
    this.checkedInTodaySubject.next(this.isCheckedInToday());
  }

  // ===== private =====

  private pickRewards(tasks: DailyTask[], n: number): CheckinRewardCard[] {
    const pool = (tasks ?? []).filter((t) => !t.completed);
    if (pool.length === 0) return [];
    // 偏好 epic/legendary + 随机打散
    const weighted = [...pool].sort((a, b) => {
      const score = (r: DailyTask['rarity']) =>
        ({ legendary: 4, epic: 3, rare: 2, common: 1 }[r] ?? 1);
      return score(b.rarity) - score(a.rarity);
    });
    const out: CheckinRewardCard[] = [];
    const used = new Set<string>();
    for (const t of weighted) {
      if (out.length >= n) break;
      if (used.has(t.id)) continue;
      out.push({
        taskId: t.id,
        title: t.title,
        icon: t.icon,
        rewardExp: t.rewardExp,
        rarity: t.rarity,
      });
      used.add(t.id);
    }
    // 不够则补随机
    while (out.length < n && used.size < pool.length) {
      const t = pool[Math.floor(Math.random() * pool.length)];
      if (used.has(t.id)) continue;
      out.push({
        taskId: t.id,
        title: t.title,
        icon: t.icon,
        rewardExp: t.rewardExp,
        rarity: t.rarity,
      });
      used.add(t.id);
    }
    return out;
  }

  private toDateKey(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  private checkedKey(): string {
    return `daily-checkin:${this.userId ?? 'guest'}:${this.today}`;
  }
  private streakKey(): string {
    return `daily-checkin:${this.userId ?? 'guest'}:streak`;
  }
  private lastDateKey(): string {
    return `daily-checkin:${this.userId ?? 'guest'}:lastDate`;
  }

  private loadStreak(): number {
    try {
      const v = localStorage.getItem(this.streakKey());
      return v ? Number(v) || 0 : 0;
    } catch {
      return 0;
    }
  }
  private loadLastDate(): string | null {
    try {
      return localStorage.getItem(this.lastDateKey());
    } catch {
      return null;
    }
  }
  private persist(today: string, streak: number): void {
    try {
      localStorage.setItem(this.checkedKey(), '1');
      localStorage.setItem(this.streakKey(), String(streak));
      localStorage.setItem(this.lastDateKey(), today);
    } catch {
      // 忽略 localStorage 不可用
    }
  }

  /** 测试用：重置所有状态 */
  resetForTest(): void {
    this.streakDays = 0;
    this.checkedInTodaySubject.next(false);
  }

  /** 调试 Observable 工厂 */
  observe(noop = false): Observable<boolean> {
    return noop ? of(false) : this.isCheckedInToday$;
  }
}
