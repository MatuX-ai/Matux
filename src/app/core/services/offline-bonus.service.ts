/**
 * 离线奖励加倍服务（P1-2）
 *
 * 职责：
 * - 监听 online / offline 事件 + navigator.onLine
 * - 暴露 isOffline$ / bonusMultiplier$ / pendingOfflineExp$ 三个 Observable
 * - 提供 applyMultiplier(baseExp) → number 工具方法
 * - 提供 accumulateOfflineExp(exp) 累计离线经验
 * - 同步重置 pending 数（online 后调用 resetPending）
 *
 * 复用：
 * - localStorage 持久化 `imato:offline-bonus:pending-exp`
 *
 * @see 桌面端游戏化P1升级.md §2.2
 */

import { DOCUMENT } from '@angular/common';
import { Inject, Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

const STORAGE_KEY_PENDING = 'imato:offline-bonus:pending-exp';

/** 倍率常量（避免 magic number） */
const MULTIPLIER_ONLINE = 1.0;
const MULTIPLIER_OFFLINE = 2.0;
/** 离线完成每日任务额外一次性奖励 */
const OFFLINE_DAILY_TASK_BONUS = 50;

@Injectable({
  providedIn: 'root',
})
export class OfflineBonusService implements OnDestroy {
  private readonly isOfflineSubject = new BehaviorSubject<boolean>(this.detectOffline());
  readonly isOffline$: Observable<boolean> = this.isOfflineSubject.asObservable();

  private readonly multiplierSubject = new BehaviorSubject<number>(
    this.isOfflineSubject.value ? MULTIPLIER_OFFLINE : MULTIPLIER_ONLINE
  );
  readonly bonusMultiplier$: Observable<number> = this.multiplierSubject.asObservable();

  private readonly pendingSubject = new BehaviorSubject<number>(this.loadPending());
  readonly pendingOfflineExp$: Observable<number> = this.pendingSubject.asObservable();

  /** offline 切换事件，用于组件动画触发 */
  private readonly toggleSubject = new Subject<boolean>();
  readonly toggle$: Observable<boolean> = this.toggleSubject.asObservable();

  private readonly onlineHandler = (): void => this.setOnline(false);
  private readonly offlineHandler = (): void => this.setOnline(true);

  constructor(@Inject(DOCUMENT) private readonly doc: Document) {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.onlineHandler);
      window.addEventListener('offline', this.offlineHandler);
    }
  }

  ngOnDestroy(): void {
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.onlineHandler);
      window.removeEventListener('offline', this.offlineHandler);
    }
  }

  /**
   * 应用倍率：
   * - 在线 → 1.0
   * - 离线 → 2.0
   */
  applyMultiplier(baseExp: number): number {
    return Math.round(baseExp * this.multiplierSubject.value);
  }

  /**
   * 离线完成每日任务额外一次性奖励
   * 在线时返回 0
   */
  offlineDailyTaskBonus(): number {
    return this.isOfflineSubject.value ? OFFLINE_DAILY_TASK_BONUS : 0;
  }

  /**
   * 累积离线 EXP（localStorage 持久化）
   * 调用场景：applyMultiplier 之后若处于 offline 模式，再 + 离线日奖励累计
   */
  accumulateOfflineExp(exp: number): void {
    if (exp <= 0 || !this.isOfflineSubject.value) return;
    const next = this.pendingSubject.value + exp;
    this.pendingSubject.next(next);
    this.savePending(next);
  }

  /**
   * 上线时清零已同步的离线 EXP
   * 由调用方在 sync 完成后调用
   */
  resetPending(): void {
    this.pendingSubject.next(0);
    this.savePending(0);
  }

  /** 当前快照（非 Observable 同步读取） */
  isCurrentlyOffline(): boolean {
    return this.isOfflineSubject.value;
  }

  currentMultiplier(): number {
    return this.multiplierSubject.value;
  }

  currentPending(): number {
    return this.pendingSubject.value;
  }

  /* === private === */

  private detectOffline(): boolean {
    if (typeof navigator !== 'undefined' && typeof navigator.onLine === 'boolean') {
      return !navigator.onLine;
    }
    return false;
  }

  private setOnline(offline: boolean): void {
    const wasOffline = this.isOfflineSubject.value;
    if (wasOffline === offline) return;
    this.isOfflineSubject.next(offline);
    this.multiplierSubject.next(offline ? MULTIPLIER_OFFLINE : MULTIPLIER_ONLINE);
    this.toggleSubject.next(offline);
  }

  private loadPending(): number {
    try {
      const raw = this.doc.defaultView?.localStorage?.getItem(STORAGE_KEY_PENDING);
      if (!raw) return 0;
      const n = Number(raw);
      return Number.isFinite(n) && n >= 0 ? n : 0;
    } catch {
      return 0;
    }
  }

  private savePending(n: number): void {
    try {
      this.doc.defaultView?.localStorage?.setItem(STORAGE_KEY_PENDING, String(n));
    } catch {
      /* 忽略 localStorage 错误（隐私模式 / SSR） */
    }
  }
}
