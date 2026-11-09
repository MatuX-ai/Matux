/**
 * AI FAB 4 态状态服务（P0-5）
 *
 * 4 态：
 *   - idle    默认（绿点呼吸）
 *   - message AI 有未读消息（蓝底徽章 +1/+2/+3）
 *   - reward  有未领取成就/EXP（金色星星粒子）
 *   - stuck   当前任务停留 > 10min 未完成（橙色求助信号）
 *
 * 状态联动：
 *   - message 由 AI 消息总线驱动（unreadCount）
 *   - reward 由 LevelEventService 升级 + DailyCheckin 签到驱动（pendingRewards）
 *   - stuck  由 DailyTasksWidget 当前任务停留时间驱动（taskStuckMinutes）
 *
 * 优先级：stuck > reward > message > idle
 *
 * @see 桌面端游戏化P0升级.md §2.5
 */

import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subscription, combineLatest } from 'rxjs';

export type FabState = 'idle' | 'message' | 'reward' | 'stuck';

@Injectable({
  providedIn: 'root',
})
export class AIFabStateService implements OnDestroy {
  private readonly stateSubject = new BehaviorSubject<FabState>('idle');
  readonly state$: Observable<FabState> = this.stateSubject.asObservable();

  private readonly unreadSubject = new BehaviorSubject<number>(0);
  readonly unreadCount$: Observable<number> = this.unreadSubject.asObservable();

  private readonly rewardSubject = new BehaviorSubject<number>(0);
  readonly pendingRewards$: Observable<number> = this.rewardSubject.asObservable();

  private readonly stuckSubject = new BehaviorSubject<number>(0);
  readonly taskStuckMinutes$: Observable<number> = this.stuckSubject.asObservable();

  /** 主动开场白（FAB 打开时若非 idle，可触发） */
  private readonly openingSubject = new BehaviorSubject<string | null>(null);
  readonly openingMessage$: Observable<string | null> = this.openingSubject.asObservable();

  private stateSub: Subscription;

  constructor() {
    this.stateSub = combineLatest([
      this.unreadSubject,
      this.rewardSubject,
      this.stuckSubject,
    ]).subscribe(([unread, reward, stuck]) => {
      this.recompute(unread, reward, stuck);
    });
  }

  ngOnDestroy(): void {
    this.stateSub.unsubscribe();
  }

  // ===== setters =====

  setUnread(n: number): void {
    this.unreadSubject.next(Math.max(0, n));
  }
  incUnread(): void {
    this.unreadSubject.next(this.unreadSubject.value + 1);
  }
  clearUnread(): void {
    this.unreadSubject.next(0);
  }

  setRewards(n: number): void {
    this.rewardSubject.next(Math.max(0, n));
  }
  addReward(): void {
    this.rewardSubject.next(this.rewardSubject.value + 1);
  }
  consumeReward(): void {
    this.rewardSubject.next(Math.max(0, this.rewardSubject.value - 1));
  }

  setStuckMinutes(n: number): void {
    this.stuckSubject.next(Math.max(0, n));
  }
  clearStuck(): void {
    this.stuckSubject.next(0);
  }

  /** 主动开场白：FAB 打开前调用，消费后清空 */
  popOpeningMessage(): string | null {
    const v = this.openingSubject.value;
    this.openingSubject.next(null);
    return v;
  }
  private pushOpeningMessage(text: string): void {
    this.openingSubject.next(text);
  }

  // ===== state machine =====

  private recompute(unread: number, reward: number, stuck: number): void {
    let next: FabState = 'idle';
    let opening: string | null = null;
    if (stuck > 10) {
      next = 'stuck';
      opening = `注意到你在这道题停留 ${stuck} 分钟了，需要我提示一下思路吗？`;
    } else if (reward > 0) {
      next = 'reward';
      opening = '刚看到你又升级了！要来聊聊新称号的故事吗？';
    } else if (unread > 0) {
      next = 'message';
      opening = `我有 ${unread} 条新消息要告诉你`;
    }
    if (this.stateSubject.value !== next) {
      this.stateSubject.next(next);
    }
    if (opening) {
      this.pushOpeningMessage(opening);
    }
  }

  // ===== for tests =====

  resetForTest(): void {
    this.unreadSubject.next(0);
    this.rewardSubject.next(0);
    this.stuckSubject.next(0);
    this.stateSubject.next('idle');
    this.openingSubject.next(null);
  }
}
