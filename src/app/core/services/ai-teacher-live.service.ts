/**
 * 【P3-B】AI 教师实时事件前端服务
 *
 * 职责：
 * 1. 接收后端推送的 ai_teacher_* 事件（经 AiEduWebSocketService → GamificationEventBusService）
 * 2. 入队（去重 + TTL 过滤 + 本地勿扰/频控）
 * 3. 提供 pending$ 流供 toast 组件渲染
 * 4. 提供 markRead / dismiss / click 桥接埋点
 */

import { Injectable, OnDestroy, inject } from '@angular/core';
import { BehaviorSubject, Observable, Subject, Subscription } from 'rxjs';
import { distinctUntilChanged, filter, map } from 'rxjs/operators';

import {
  AiTeacherCelebrationPayload,
  AiTeacherLiveEvent,
  AiTeacherLiveSettings,
  AiTeacherNudgePayload,
  AiTeacherRecommendationClickEvent,
  AiTeacherSuggestionPayload,
  DEFAULT_LIVE_SETTINGS,
} from '../models/ai-teacher.models';
import {
  GamificationEvent,
  GamificationEventBusService,
  GamificationEventType,
} from './gamification-event-bus.service';

const MAX_PENDING = 3;
const MAX_HISTORY = 50;

@Injectable({ providedIn: 'root' })
export class AiTeacherLiveService implements OnDestroy {
  private readonly gamificationBus = inject(GamificationEventBusService);

  /** 待展示队列（最多 3 条） */
  private readonly pendingSubject = new BehaviorSubject<AiTeacherLiveEvent[]>(
    []
  );
  readonly pending$: Observable<AiTeacherLiveEvent[]> =
    this.pendingSubject.asObservable();

  /** 已读历史（最多 50 条） */
  private readonly historySubject = new BehaviorSubject<AiTeacherLiveEvent[]>(
    []
  );
  readonly history$: Observable<AiTeacherLiveEvent[]> =
    this.historySubject.asObservable();

  /** 用户级 live settings（前端本地缓存） */
  private readonly settingsSubject = new BehaviorSubject<AiTeacherLiveSettings>(
    this.buildDefaultSettings('')
  );
  readonly settings$: Observable<AiTeacherLiveSettings> =
    this.settingsSubject.asObservable();

  /** 客户端点击/操作埋点流 */
  private readonly clickSubject = new Subject<AiTeacherRecommendationClickEvent>();
  readonly clicks$: Observable<AiTeacherRecommendationClickEvent> =
    this.clickSubject.asObservable();

  /** 当前用户 ID（外部注入） */
  private currentUserId = '';

  private busSub: Subscription | null = null;

  constructor() {
    // 注册到 window（供 WebSocket 服务反向桥接使用）
    if (typeof window !== 'undefined') {
      (window as unknown as { __aiTeacherLiveService?: AiTeacherLiveService })
        .__aiTeacherLiveService = this;
    }
    // 订阅 ai_teacher_* 事件
    this.busSub = this.gamificationBus
      .onAnyEvent()
      .pipe(
        filter((e) => this.isAiTeacherType(e.type)),
        map((e) => this.normalize(e))
      )
      .subscribe((event) => this.ingest(event));
  }

  ngOnDestroy(): void {
    this.busSub?.unsubscribe();
    this.pendingSubject.complete();
    this.historySubject.complete();
    this.settingsSubject.complete();
    this.clickSubject.complete();
  }

  /** 注入当前用户 ID（在用户登录后调用） */
  setUserId(userId: string): void {
    this.currentUserId = userId;
    this.applySettings(this.buildDefaultSettings(userId));
  }

  /** 应用设置 */
  applySettings(settings: AiTeacherLiveSettings): void {
    this.settingsSubject.next(settings);
  }

  /** 获取当前 settings 快照 */
  getSettingsSnapshot(): AiTeacherLiveSettings {
    return this.settingsSubject.value;
  }

  // ========== 入队 / 消费 ==========

  /**
   * 入队一个 AI 教师实时事件
   * - 按 id 去重
   * - TTL 过期自动丢弃
   * - 本地勿扰/频控最后一道兜底
   */
  ingest(event: AiTeacherLiveEvent): void {
    const settings = this.settingsSubject.value;

    // 总开关
    if (!settings.enabled) {
      return;
    }

    // 类型开关
    if (
      event.type === GamificationEventType.AI_TEACHER_CELEBRATION &&
      !settings.celebrationEnabled
    ) {
      return;
    }
    if (
      event.type === GamificationEventType.AI_TEACHER_SUGGESTION &&
      !settings.suggestionEnabled
    ) {
      return;
    }
    if (
      event.type === GamificationEventType.AI_TEACHER_NUDGE &&
      !settings.nudgeEnabled
    ) {
      return;
    }

    // 勿扰
    if (this.isInDnd(settings, new Date())) {
      return;
    }

    // TTL 过期
    if (this.isExpired(event)) {
      return;
    }

    // 去重
    const pending = this.pendingSubject.value;
    if (pending.some((p) => p.id === event.id)) {
      return;
    }
    if (this.historySubject.value.some((p) => p.id === event.id)) {
      return;
    }

    // 入队 + 历史
    const nextPending = [...pending, event].slice(-MAX_PENDING);
    this.pendingSubject.next(nextPending);

    const history = [event, ...this.historySubject.value].slice(0, MAX_HISTORY);
    this.historySubject.next(history);
  }

  /** 用户主动标记已读（移到历史） */
  markRead(id: string): void {
    const pending = this.pendingSubject.value.filter((e) => e.id !== id);
    this.pendingSubject.next(pending);
  }

  /** 全量关闭当前 toast */
  dismissAll(): void {
    const pending = this.pendingSubject.value;
    const now = Date.now();
    pending.forEach((e) =>
      this.clickSubject.next({
        eventId: e.id,
        type: e.type,
        action: 'dismiss',
      })
    );
    this.pendingSubject.next([]);
    void now;
  }

  /** 单条 dismiss */
  dismiss(id: string): void {
    this.markRead(id);
    const event = this.historySubject.value.find((e) => e.id === id);
    if (event) {
      this.clickSubject.next({
        eventId: id,
        type: event.type,
        action: 'dismiss',
      });
    }
  }

  /** CTA 点击 / 自动消失埋点 */
  click(
    event: AiTeacherLiveEvent,
    action: 'cta' | 'auto_expire' = 'cta'
  ): void {
    const payload = event.payload as
      | AiTeacherCelebrationPayload
      | AiTeacherSuggestionPayload
      | AiTeacherNudgePayload;
    this.clickSubject.next({
      eventId: event.id,
      type: event.type,
      action,
      ctaRoute: payload?.ctaRoute ?? undefined,
      ctaLabel: payload?.ctaLabel ?? undefined,
    });
    this.markRead(event.id);
  }

  // ========== 历史回放（断线重连） ==========

  replayFromServer(events: AiTeacherLiveEvent[]): void {
    if (!events || events.length === 0) {
      return;
    }
    for (const evt of events) {
      this.ingest(evt);
    }
  }

  /** 仅供 settingsSubject 加载**
   * 实际获取通过 AiTeacherService.getLiveSettings（HTTP）
   */
  // ========== 内部辅助 ==========

  private isAiTeacherType(t: string): boolean {
    return (
      t === GamificationEventType.AI_TEACHER_CELEBRATION ||
      t === GamificationEventType.AI_TEACHER_SUGGESTION ||
      t === GamificationEventType.AI_TEACHER_NUDGE
    );
  }

  /**
   * 归一化后端事件为前端 AiTeacherLiveEvent
   * 后端 data 字段是包含 id/type/userId/payload/ttlMs/cooldownKey/createdAt 的事件
   */
  private normalize(evt: GamificationEvent): AiTeacherLiveEvent {
    const raw = evt.data as Record<string, unknown> | undefined;
    const type = (evt.type as AiTeacherLiveEvent['type']) ?? raw?.['type'] as AiTeacherLiveEvent['type'];

    if (
      raw &&
      typeof raw['id'] === 'string' &&
      typeof raw['type'] === 'string' &&
      typeof raw['payload'] === 'object'
    ) {
      // 后端 ai_teacher_event_bus 直接推送的完整事件
      return raw as unknown as AiTeacherLiveEvent;
    }
    // 兜底：后端 ws 推过来的 { data: event } 结构
    return {
      id:
        (raw?.['id'] as string) ??
        `evt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      type,
      userId: (raw?.['userId'] as string) ?? this.currentUserId,
      payload: this.extractPayload(raw, type),
      ttlMs: (raw?.['ttlMs'] as number) ?? 10 * 60 * 1000,
      cooldownKey: (raw?.['cooldownKey'] as string) ?? `manual:${type}`,
      createdAt:
        (raw?.['createdAt'] as string) ??
        new Date().toISOString(),
    };
  }

  private isExpired(event: AiTeacherLiveEvent): boolean {
    const created = Date.parse(event.createdAt);
    if (Number.isNaN(created)) {
      return false;
    }
    return Date.now() - created > event.ttlMs;
  }

  /**
   * 从 raw（后端数据）抽取 payload。
   * raw 可能是：{ payload: {...} } 或本身就是事件对象。
   * 三个 AiTeacherLiveEventType 都共享同一 payload 联合类型，所以直接断言为 unknown 后转换。
   */
  private extractPayload(
    raw: Record<string, unknown> | undefined,
    _type: AiTeacherLiveEvent['type']
  ): AiTeacherLiveEvent['payload'] {
    if (raw && typeof raw['payload'] === 'object' && raw['payload']) {
      return raw['payload'] as unknown as AiTeacherLiveEvent['payload'];
    }
    if (raw && raw['title']) {
      // 整个 raw 就是 payload
      return raw as unknown as AiTeacherLiveEvent['payload'];
    }
    return {} as AiTeacherLiveEvent['payload'];
  }

  private isInDnd(s: AiTeacherLiveSettings, now: Date): boolean {
    const hour = now.getHours();
    const start = s.dndStartHour;
    const end = s.dndEndHour;
    if (start === end) {
      return false;
    }
    if (start < end) {
      return hour >= start && hour < end;
    }
    // 跨夜
    return hour >= start || hour < end;
  }

  private buildDefaultSettings(userId: string): AiTeacherLiveSettings {
    return {
      userId,
      updatedAt: new Date().toISOString(),
      ...DEFAULT_LIVE_SETTINGS,
    };
  }
}