/**
 * 【P3-A-3】学习地图高亮服务
 *
 * 统一管理学习地图节点高亮状态：
 * 1. 单例 BehaviorSubject 控制当前高亮节点
 * 2. 队列播放（避免同时高亮多个节点）
 * 3. 持续时间可配置（默认 5s）
 * 4. 互斥：新 highlight 同 id 时跳过
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface HighlightState {
  nodeId: string;
  startedAt: number;
  durationMs: number;
}

@Injectable({ providedIn: 'root' })
export class LearningMapHighlightService {
  /** 当前活跃高亮（null = 无） */
  private readonly activeNodeId$ = new BehaviorSubject<string | null>(null);

  /** 当前高亮状态（带元信息） */
  private readonly activeState$ = new BehaviorSubject<HighlightState | null>(null);

  /** 待播放队列 */
  private queue: HighlightState[] = [];

  /** 是否正在播放 */
  private isPlaying = false;

  /** 默认持续时间 */
  private readonly DEFAULT_DURATION_MS = 5000;

  /** 队列项之间间隔（ms） */
  private readonly INTERVAL_MS = 250;

  /** 活跃计时器 */
  private activeTimer: ReturnType<typeof setTimeout> | null = null;

  /** 当前活跃状态的简化 Observable */
  get highlightedNode$(): Observable<string | null> {
    return this.activeNodeId$.asObservable();
  }

  /** 当前完整状态 Observable */
  get activeState$Stream(): Observable<HighlightState | null> {
    return this.activeState$.asObservable();
  }

  /**
   * 触发高亮
   * @param nodeId 节点 ID
   * @param durationMs 持续时间（默认 5000ms）
   */
  highlight(nodeId: string, durationMs: number = this.DEFAULT_DURATION_MS): void {
    if (!nodeId) return;

    // 如果已在高亮同一节点，忽略
    if (this.activeNodeId$.value === nodeId) return;

    const state: HighlightState = {
      nodeId,
      startedAt: Date.now(),
      durationMs,
    };
    this.queue.push(state);
    if (!this.isPlaying) this.playNext();
  }

  /**
   * 批量高亮（一次性入队）
   */
  highlightMany(nodeIds: string[], durationMs?: number): void {
    for (const id of nodeIds) {
      this.highlight(id, durationMs);
    }
  }

  /**
   * 立即清除当前高亮和队列
   */
  clear(): void {
    if (this.activeTimer) {
      clearTimeout(this.activeTimer);
      this.activeTimer = null;
    }
    this.queue = [];
    this.isPlaying = false;
    this.activeNodeId$.next(null);
    this.activeState$.next(null);
  }

  /**
   * 当前是否有节点在播放
   */
  isActive(): boolean {
    return this.activeNodeId$.value !== null;
  }

  /**
   * 队列长度
   */
  getQueueLength(): number {
    return this.queue.length;
  }

  // ================ 私有方法 ================

  private playNext(): void {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      return;
    }
    this.isPlaying = true;
    const state = this.queue.shift()!;

    // 推送给订阅者
    this.activeNodeId$.next(state.nodeId);
    this.activeState$.next(state);

    // 设置结束 timer
    this.activeTimer = setTimeout(() => {
      // 清除
      this.activeNodeId$.next(null);
      this.activeState$.next(null);
      this.activeTimer = null;

      // 间隔后播放下一项
      if (this.queue.length > 0) {
        setTimeout(() => this.playNext(), this.INTERVAL_MS);
      } else {
        this.isPlaying = false;
      }
    }, state.durationMs);
  }
}
