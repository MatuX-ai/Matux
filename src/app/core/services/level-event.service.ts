/**
 * 等级升级事件服务（P0-2 触发源 ↔ Modal 解耦）
 *
 * AchievementCenterCard 监听 level.current 变化并 emit，
 * StudentDashboard 上挂载的 <app-level-up-modal> 订阅 levelUp$ 显示。
 *
 * 同一用户同一等级不重复触发（Map<userId, lastLevel> 去重）。
 *
 * @see 桌面端游戏化P0升级.md §2.2 P0-2
 */

import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

import type { UserLevel } from '../../user/student/services/student-dashboard-data.service';

export interface LevelUpPayload {
  old: UserLevel;
  next: UserLevel;
  totalExp: number;
}

@Injectable({
  providedIn: 'root',
})
export class LevelEventService {
  private readonly subject = new Subject<LevelUpPayload>();
  /** 升级事件流 */
  readonly levelUp$: Observable<LevelUpPayload> = this.subject.asObservable();

  /** 每个用户的上一次等级缓存（去重） */
  private readonly lastLevelByUser = new Map<string, number>();

  /**
   * 触发升级事件
   * @param userId 用户 ID（缺失时跳过去重）
   * @param old 上一个等级快照
   * @param next 当前等级快照（current 必须 > old.current）
   * @param totalExp 升级后的累计 EXP
   */
  emitLevelUp(userId: string | null, old: UserLevel, next: UserLevel, totalExp: number): void {
    if (!next || next.current <= old.current) return;
    if (userId) {
      const last = this.lastLevelByUser.get(userId);
      if (last === next.current) return; // 同等级去重
      this.lastLevelByUser.set(userId, next.current);
    }
    this.subject.next({ old, next, totalExp });
  }

  /** 测试/调试用：重置去重缓存 */
  reset(): void {
    this.lastLevelByUser.clear();
  }
}
