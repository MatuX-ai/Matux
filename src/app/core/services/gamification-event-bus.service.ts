/**
 * 【P3-A-2】游戏化事件总线（前端）
 *
 * 与后端 gamification_event_bus 配套：
 * 1. AiEduWebSocketService 收到 gamification_* 消息 → publish()
 * 2. 各组件订阅 onAchievementUnlocked / onNodeStatusUpdated / onSetCompleted
 * 3. 内部使用 RxJS Subject，支持多订阅、过滤、合并
 */

import { Injectable, OnDestroy, inject } from '@angular/core';
import { Observable, Subject, Subscription } from 'rxjs';
import { filter, map } from 'rxjs/operators';

import { resolveBackendWsBase } from '../utils/backend-url.util';
import { AuthService } from './auth.service';

/** 事件类型枚举（与后端保持一致） */
export enum GamificationEventType {
  ACHIEVEMENT_UNLOCKED = 'achievement_unlocked',
  NODE_STATUS_UPDATED = 'node_status_updated',
  SET_COMPLETED = 'set_completed',
  // 【P3-B】AI 教师实时事件
  AI_TEACHER_CELEBRATION = 'ai_teacher_celebration',
  AI_TEACHER_SUGGESTION = 'ai_teacher_suggestion',
  AI_TEACHER_NUDGE = 'ai_teacher_nudge',
}

/** 【P3-B】判断是否为 AI 教师事件 */
export function isAiTeacherEvent(
  type: GamificationEventType | string
): boolean {
  return (
    type === GamificationEventType.AI_TEACHER_CELEBRATION ||
    type === GamificationEventType.AI_TEACHER_SUGGESTION ||
    type === GamificationEventType.AI_TEACHER_NUDGE
  );
}

/** 成就解锁事件载荷 */
export interface AchievementUnlockedEvent {
  achievement_id: string | number;
  name: string;
  rarity: string;
  points?: number;
  related_skill_ids?: string[];
  icon?: string;
  description?: string;
  unlocked_at?: string;
}

/** 节点状态更新事件载荷 */
export interface NodeStatusUpdatedEvent {
  skill_id: string;
  old_status: string;
  new_status: string;
  progress?: number;
  related_achievement_ids?: (string | number)[];
  timestamp?: string;
}

/** 套装完成事件载荷 */
export interface SetCompletedEvent {
  set_id: string;
  set_name: string;
  bonus_reward?: {
    type: string;
    value: string | number;
    label: string;
    emoji?: string;
  };
  timestamp?: string;
}

/** 通用事件封装 */
export interface GamificationEvent<T = unknown> {
  type: GamificationEventType | string;
  data: T;
  timestamp?: string;
}

@Injectable({ providedIn: 'root' })
export class GamificationEventBusService implements OnDestroy {
  private readonly auth = inject(AuthService);

  /** 成就解锁事件流 */
  private readonly achievementUnlocked$ = new Subject<AchievementUnlockedEvent>();

  /** 节点状态更新事件流 */
  private readonly nodeStatusUpdated$ = new Subject<NodeStatusUpdatedEvent>();

  /** 套装完成事件流 */
  private readonly setCompleted$ = new Subject<SetCompletedEvent>();

  /** 通用事件流（不过滤类型） */
  private readonly allEvents$ = new Subject<GamificationEvent>();

  /** 待重放队列（订阅前到达的事件） */
  private pendingEvents: GamificationEvent[] = [];
  private readonly MAX_PENDING = 50;

  // ==================== 【P0-C 修复】/ws/gamification 直连 ====================

  private socket: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private desiredUserId: string | null = null;
  private manuallyClosed = false;
  private readonly MAX_RECONNECT_DELAY_MS = 30_000;

  ngOnDestroy(): void {
    this.disconnect();
    this.achievementUnlocked$.complete();
    this.nodeStatusUpdated$.complete();
    this.setCompleted$.complete();
    this.allEvents$.complete();
  }

  /**
   * 【P0-C 修复】建立 /ws/gamification 连接（幂等，可重复调用）。
   *
   * 之前桌面端只有 /ws/ai-edu 通道，且 URL 因 `app://` origin 拼错而连不上，
   * 成就中心拿不到任何实时推送。这里补上官方游戏化 WS 入口。
   */
  connect(userId: string | number): void {
    const uid = String(userId);
    const current = this.socket;
    const alreadyOpen =
      this.desiredUserId === uid &&
      !!current &&
      (current.readyState === WebSocket.OPEN || current.readyState === WebSocket.CONNECTING);
    if (alreadyOpen) {
      return;
    }

    this.disconnect();
    this.desiredUserId = uid;
    this.manuallyClosed = false;

    const token = this.auth.getAccessToken() ?? '';
    if (!token) {
      console.warn('[GamificationWS] 缺少访问令牌，跳过 /ws/gamification 连接');
      return;
    }

    const url = `${resolveBackendWsBase()}/ws/gamification?token=${encodeURIComponent(token)}`;
    try {
      const socket = new WebSocket(url);
      this.socket = socket;

      socket.onopen = () => {
        this.reconnectAttempts = 0;
        console.info('[GamificationWS] 已连接 /ws/gamification');
      };

      socket.onmessage = (event: MessageEvent) => {
        this.handleSocketMessage(event.data);
      };

      socket.onerror = () => {
        // 具体原因由 onclose 处理（重连 / 放弃）
        console.warn('[GamificationWS] 连接错误');
      };

      socket.onclose = () => {
        this.socket = null;
        if (!this.manuallyClosed) {
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      console.warn('[GamificationWS] 创建连接失败:', err);
      this.scheduleReconnect();
    }
  }

  /** 主动断开（组件卸载 / 登出时调用） */
  disconnect(): void {
    this.manuallyClosed = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      try {
        this.socket.onclose = null;
        this.socket.close();
      } catch {
        // 忽略关闭异常
      }
      this.socket = null;
    }
  }

  private handleSocketMessage(raw: unknown): void {
    if (typeof raw !== 'string') return;
    try {
      const msg = JSON.parse(raw) as { type?: string; data?: unknown; timestamp?: string };
      const type = msg?.type;
      // 控制帧：不作为业务事件分发
      if (!type || type === 'connected' || type === 'pong' || type === 'error') {
        if (type === 'error') {
          console.warn('[GamificationWS] 服务端错误帧:', msg);
        }
        return;
      }
      this.publish({
        type: type as GamificationEventType,
        data: msg.data as never,
        timestamp: msg.timestamp,
      });
    } catch (err) {
      console.warn('[GamificationWS] 无法解析消息:', err);
    }
  }

  private scheduleReconnect(): void {
    if (this.manuallyClosed || this.reconnectTimer !== null) return;
    if (this.reconnectAttempts >= 6) {
      console.warn('[GamificationWS] 重连次数已达上限，停止重试');
      return;
    }
    const delay = Math.min(2000 * 2 ** this.reconnectAttempts, this.MAX_RECONNECT_DELAY_MS);
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      const uid = this.desiredUserId;
      if (uid) {
        // 先重置状态再重连，避免 connect() 的幂等判断提前返回
        this.desiredUserId = null;
        this.connect(uid);
      }
    }, delay);
  }

  /**
   * 由 AiEduWebSocketService 内部调用（不暴露给组件）
   * 接收后端推送的事件，分发给对应的 Subject
   */
  publish(event: GamificationEvent): void {
    // 推入待重放队列
    this.pendingEvents.push(event);
    if (this.pendingEvents.length > this.MAX_PENDING) {
      this.pendingEvents = this.pendingEvents.slice(-this.MAX_PENDING);
    }

    // 通用事件流
    this.allEvents$.next(event);

    // 按类型分派
    switch (event.type) {
      case GamificationEventType.ACHIEVEMENT_UNLOCKED:
        this.achievementUnlocked$.next(event.data as AchievementUnlockedEvent);
        break;
      case GamificationEventType.NODE_STATUS_UPDATED:
        this.nodeStatusUpdated$.next(event.data as NodeStatusUpdatedEvent);
        break;
      case GamificationEventType.SET_COMPLETED:
        this.setCompleted$.next(event.data as SetCompletedEvent);
        break;
      // 【P3-B】AI 教师事件仍会推送到 allEvents$，由 AiTeacherLiveService 订阅
      default:
        // 未知类型：仅推送到 allEvents$
        break;
    }
  }

  /**
   * 订阅成就解锁事件
   */
  onAchievementUnlocked(): Observable<AchievementUnlockedEvent> {
    return this.achievementUnlocked$.asObservable();
  }

  /**
   * 订阅节点状态更新事件
   */
  onNodeStatusUpdated(): Observable<NodeStatusUpdatedEvent> {
    return this.nodeStatusUpdated$.asObservable();
  }

  /**
   * 订阅套装完成事件
   */
  onSetCompleted(): Observable<SetCompletedEvent> {
    return this.setCompleted$.asObservable();
  }

  /**
   * 订阅所有事件（用于调试 / 通用）
   */
  onAnyEvent(): Observable<GamificationEvent> {
    return this.allEvents$.asObservable();
  }

  /**
   * 按类型过滤订阅
   */
  onEvent<T = unknown>(type: GamificationEventType | string): Observable<GamificationEvent<T>> {
    return this.allEvents$.pipe(
      filter((e) => e.type === type),
      map((e) => e as GamificationEvent<T>)
    );
  }

  /**
   * 获取待重放的事件（供新订阅者查看历史）
   */
  getPendingEvents(type?: GamificationEventType | string): GamificationEvent[] {
    if (!type) return [...this.pendingEvents];
    return this.pendingEvents.filter((e) => e.type === type);
  }

  /**
   * 清空待重放队列
   */
  clearPending(): void {
    this.pendingEvents = [];
  }

  /**
   * 注册一个会重新发射待重放事件的新订阅
   */
  replayOnSubscribe<T>(
    subject: Subject<T>,
    type: GamificationEventType | string
  ): Subscription {
    const pending = this.getPendingEvents(type) as GamificationEvent<T>[];
    return new Subscription(() => {
      // 立即发出历史事件
      for (const event of pending) {
        subject.next(event.data);
      }
    });
  }
}
