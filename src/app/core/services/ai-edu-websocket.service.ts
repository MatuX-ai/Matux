/**
 * AI-Edu 学习进度 WebSocket 同步服务
 * 支持实时学习进度同步、多设备协作
 */

import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { filter, map, takeUntil } from 'rxjs/operators';

export interface WebSocketMessage {
  type: string;
  data?: unknown;
  message?: string;
  timestamp?: string;
  error?: string;
  code?: string;
}

export interface ProgressUpdateData {
  lesson_id: number;
  progress_percentage: number;
  status: 'not_started' | 'in_progress' | 'completed';
  time_spent_seconds: number;
  quiz_score?: number;
  code_quality_score?: number;
  timestamp: string;
}

export interface LearningState {
  lesson_id: number;
  progress: number;
  status: string;
  time_spent_seconds: number;
  last_update: string | null;
}

/** 重连状态 */
export interface ReconnectState {
  /** 是否正在重连 */
  attempting: boolean;
  /** 当前重连次数 */
  attempt: number;
  /** 最大重连次数 */
  maxAttempts: number;
  /** 下次重连等待时间 (ms) */
  nextDelay: number;
}

/** WebSocket 配置 */
export interface WebSocketConfig {
  /** 最大重连次数 */
  maxReconnectAttempts?: number;
  /** 基础重连延迟 (ms) */
  baseDelay?: number;
  /** 最大重连延迟上限 (ms) */
  maxDelay?: number;
  /** 抖动范围 (ms)，避免惊群效应 */
  jitterMax?: number;
  /** 心跳发送间隔 (ms) */
  pingIntervalMs?: number;
  /** pong 超时时间 (ms)，超过此时间未收到 pong 判定断线 */
  pongTimeoutMs?: number;
}

@Injectable({
  providedIn: 'root',
})
export class AiEduWebSocketService implements OnDestroy {
  private websocket: WebSocket | null = null;

  // ---- 重连配置 ----
  private maxReconnectAttempts = 5;
  private baseDelay = 1000;
  private maxDelay = 30000;
  private jitterMax = 1000;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  // ---- 重连状态 ----
  private reconnectStateSubject = new BehaviorSubject<ReconnectState>({
    attempting: false,
    attempt: 0,
    maxAttempts: this.maxReconnectAttempts,
    nextDelay: 0,
  });
  /** 重连状态流，可用于 UI 展示 */
  readonly reconnectState$: Observable<ReconnectState> = this.reconnectStateSubject.asObservable();

  // ---- 心跳配置 ----
  private pingIntervalMs = 30000;
  private pongTimeoutMs = 10000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private pongTimeoutTimer: ReturnType<typeof setInterval> | null = null;
  private lastPongTime: number = 0;

  private destroy$ = new Subject<void>();

  private messageSubject = new Subject<WebSocketMessage>();
  private connectionStatusSubject = new Subject<
    'connecting' | 'connected' | 'disconnected' | 'error'
  >();

  private currentUserId: number | null = null;
  private currentOrgId: number | null = null;
  private wsUrl: string = '';

  /** 消息流 */
  get messages$(): Observable<WebSocketMessage> {
    return this.messageSubject.asObservable();
  }

  /** 连接状态流 */
  get connectionStatus$(): Observable<'connecting' | 'connected' | 'disconnected' | 'error'> {
    return this.connectionStatusSubject.asObservable();
  }

  /** 是否已连接 */
  isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }

  /**
   * 更新 WebSocket 配置（在 connect 之前调用生效）
   */
  setConfig(config: WebSocketConfig): void {
    if (config.maxReconnectAttempts !== undefined) {
      this.maxReconnectAttempts = config.maxReconnectAttempts;
    }
    if (config.baseDelay !== undefined) {
      this.baseDelay = config.baseDelay;
    }
    if (config.maxDelay !== undefined) {
      this.maxDelay = config.maxDelay;
    }
    if (config.jitterMax !== undefined) {
      this.jitterMax = config.jitterMax;
    }
    if (config.pingIntervalMs !== undefined) {
      this.pingIntervalMs = config.pingIntervalMs;
    }
    if (config.pongTimeoutMs !== undefined) {
      this.pongTimeoutMs = config.pongTimeoutMs;
    }
    // 同步更新重连状态中的 maxAttempts
    this.reconnectStateSubject.next({
      ...this.reconnectStateSubject.value,
      maxAttempts: this.maxReconnectAttempts,
    });
  }

  /**
   * 连接到 WebSocket 服务
   * @param userId 用户 ID
   * @param orgId 组织 ID
   * @param baseUrl WebSocket 服务器基础 URL
   */
  connect(userId: number, orgId: number, baseUrl: string): void {
    if (this.isConnected()) {
      return;
    }

    this.currentUserId = userId;
    this.currentOrgId = orgId;

    // 构建 WebSocket URL
    const protocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
    const host = baseUrl.replace(/^https?:\/\//, '');
    this.wsUrl = `${protocol}://${host}/ws/ai-edu/progress/${userId}?org_id=${orgId}`;

    this.connectionStatusSubject.next('connecting');

    try {
      this.websocket = new WebSocket(this.wsUrl);

      this.websocket.onopen = () => {
        this.reconnectAttempts = 0;
        this.lastPongTime = Date.now();
        this.connectionStatusSubject.next('connected');
        this.updateReconnectState(false, 0);
        this.startPingInterval();
        this.startPongTimeout();
      };

      this.websocket.onmessage = (event: MessageEvent) => {
        try {
          const message = JSON.parse(event.data as string) as WebSocketMessage;

          // 收到 pong 响应，更新最后 pong 时间
          if (message.type === 'pong') {
            this.lastPongTime = Date.now();
          }

          this.messageSubject.next(message);
        } catch {
          /* 忽略解析错误 */
        }
      };

      this.websocket.onclose = (event) => {
        this.connectionStatusSubject.next('disconnected');
        this.stopPingInterval();
        this.stopPongTimeout();

        // 尝试重连（code 1000=正常关闭不重连）
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.websocket.onerror = () => {
        this.connectionStatusSubject.next('error');
      };
    } catch (error) {
      this.connectionStatusSubject.next('error');
    }
  }

  /**
   * 断开 WebSocket 连接
   */
  disconnect(): void {
    this.stopPingInterval();
    this.stopPongTimeout();
    this.clearReconnectTimer();

    if (this.websocket) {
      this.websocket.close(1000, 'User disconnected');
      this.websocket = null;
    }

    this.currentUserId = null;
    this.currentOrgId = null;
    this.reconnectAttempts = 0;
    this.reconnectStateSubject.next({
      attempting: false,
      attempt: 0,
      maxAttempts: this.maxReconnectAttempts,
      nextDelay: 0,
    });
    this.connectionStatusSubject.next('disconnected');
  }

  /**
   * 发送更新学习进度消息
   */
  updateProgress(progressData: {
    lesson_id: number;
    progress: {
      progress_percentage: number;
      time_spent_seconds: number;
      quiz_score?: number;
      code_quality_score?: number;
      status?: string;
    };
  }): void {
    this.sendMessage({
      type: 'update_progress',
      data: progressData,
    });
  }

  /**
   * 获取当前学习状态
   */
  getCurrentState(): void {
    this.sendMessage({
      type: 'get_state',
    });
  }

  /**
   * 订阅特定课程的进度更新
   */
  subscribeLesson(lessonId: number): void {
    this.sendMessage({
      type: 'subscribe_lesson',
      data: { lesson_id: lessonId },
    });
  }

  /**
   * 取消订阅课程
   */
  unsubscribeLesson(lessonId: number): void {
    this.sendMessage({
      type: 'unsubscribe_lesson',
      data: { lesson_id: lessonId },
    });
  }

  /**
   * 发送心跳
   */
  sendPing(): void {
    this.sendMessage({
      type: 'ping',
    });
  }

  /**
   * 发送通用消息
   */
  sendMessage(message: WebSocketMessage): void {
    if (!this.isConnected() || !this.websocket) {
      return;
    }

    try {
      this.websocket.send(JSON.stringify(message));
    } catch {
      /* 忽略发送错误 */
    }
  }

  /**
   * 监听特定类型的消息
   */
  onMessageType(type: string): Observable<WebSocketMessage> {
    return this.messages$.pipe(
      filter((msg) => msg.type === type),
      takeUntil(this.destroy$)
    );
  }

  /**
   * 监听进度更新
   */
  onProgressUpdate(): Observable<ProgressUpdateData> {
    return this.onMessageType('progress_update').pipe(
      filter((msg) => !!msg.data),
      takeUntil(this.destroy$),
      map((msg) => msg.data as ProgressUpdateData)
    );
  }

  /**
   * 监听进度确认
   */
  onProgressConfirmed(): Observable<ProgressUpdateData> {
    return this.onMessageType('progress_confirmed').pipe(
      filter((msg) => !!msg.data),
      takeUntil(this.destroy$),
      map((msg) => msg.data as ProgressUpdateData)
    );
  }

  /**
   * 监听错误消息
   */
  onErrors(): Observable<WebSocketMessage> {
    return this.onMessageType('error');
  }

  // ========== 重连机制 ==========

  /**
   * 计算指数退避延迟（带抖动）
   * delay = min(maxDelay, baseDelay * 2^attempt) + random(0, jitterMax)
   */
  private calculateBackoff(attempt: number): number {
    const exponentialDelay = Math.min(this.maxDelay, this.baseDelay * Math.pow(2, attempt - 1));
    const jitter = Math.random() * this.jitterMax;
    return Math.floor(exponentialDelay + jitter);
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.calculateBackoff(this.reconnectAttempts);

    this.updateReconnectState(true, delay);

    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      if (this.currentUserId && this.currentOrgId) {
        this.connectionStatusSubject.next('connecting');
        this.connect(this.currentUserId, this.currentOrgId, this.getBaseUrl());
      }
    }, delay);
  }

  /**
   * 更新重连状态
   */
  private updateReconnectState(attempting: boolean, nextDelay: number): void {
    this.reconnectStateSubject.next({
      attempting,
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      nextDelay,
    });
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // ========== 心跳检测 ==========

  /**
   * 启动心跳定时器
   */
  private startPingInterval(): void {
    this.stopPingInterval();

    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendPing();
      }
    }, this.pingIntervalMs);
  }

  /**
   * 停止心跳定时器
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * 启动 pong 超时检测：如果超过 pongTimeoutMs 未收到 pong，强制断开重连
   */
  private startPongTimeout(): void {
    this.stopPongTimeout();

    this.pongTimeoutTimer = setInterval(
      () => {
        if (!this.isConnected()) {
          return;
        }

        const elapsed = Date.now() - this.lastPongTime;
        if (elapsed > this.pongTimeoutMs) {
          // 心跳超时，强制断开触发重连
          this.forceReconnect();
        }
      },
      Math.min(this.pongTimeoutMs, 5000)
    ); // 至少每 5s 检查一次
  }

  /**
   * 停止 pong 超时检测
   */
  private stopPongTimeout(): void {
    if (this.pongTimeoutTimer) {
      clearInterval(this.pongTimeoutTimer);
      this.pongTimeoutTimer = null;
    }
  }

  /**
   * 强制重连：关闭当前连接，onclose 会自动触发 scheduleReconnect
   */
  private forceReconnect(): void {
    if (this.websocket) {
      // 移除 onclose 监听，手动触发重连逻辑
      const _oldOnClose = this.websocket.onclose;
      this.websocket.onclose = null;
      this.websocket.close(4001, 'Heartbeat timeout');
      this.websocket = null;
    }

    this.connectionStatusSubject.next('error');
    this.stopPingInterval();
    this.stopPongTimeout();

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * 获取基础 URL
   */
  private getBaseUrl(): string {
    // 从当前 URL 推断 API 基础 URL
    const origin = window.location.origin;
    return origin.includes('localhost') ? 'http://localhost:8000' : origin;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.clearReconnectTimer();
    this.disconnect();
  }
}
