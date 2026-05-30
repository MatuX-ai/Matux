/**
 * AI-Edu 学习进度 WebSocket 同步服务
 * 支持实时学习进度同步、多设备协作
 */

import { Injectable, OnDestroy } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { filter, map, takeUntil } from 'rxjs/operators';

export interface WebSocketMessage {
  type: string;
  data?: any;
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

@Injectable({
  providedIn: 'root',
})
export class AiEduWebSocketService implements OnDestroy {
  private websocket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 3 秒
  private pingInterval: any = null;
  private pingIntervalMs = 30000; // 30 秒
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

      this.websocket.onopen = (event) => {
        this.reconnectAttempts = 0;
        this.connectionStatusSubject.next('connected');
        this.startPingInterval();
      };

      this.websocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          this.messageSubject.next(message);
        } catch (error) {}
      };

      this.websocket.onclose = (event) => {
        this.connectionStatusSubject.next('disconnected');
        this.stopPingInterval();

        // 尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.websocket.onerror = (error) => {
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

    if (this.websocket) {
      this.websocket.close(1000, 'User disconnected');
      this.websocket = null;
    }

    this.currentUserId = null;
    this.currentOrgId = null;
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
    if (!this.isConnected()) {
      return;
    }

    try {
      this.websocket!.send(JSON.stringify(message));
    } catch (error) {}
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

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;

    setTimeout(() => {
      if (this.currentUserId && this.currentOrgId) {
        this.connect(this.currentUserId, this.currentOrgId, this.getBaseUrl());
      }
    }, this.reconnectDelay);
  }

  /**
   * 获取基础 URL
   */
  private getBaseUrl(): string {
    // 从当前 URL 推断 API 基础 URL
    const origin = window.location.origin;
    return origin.includes('localhost') ? 'http://localhost:8000' : origin;
  }

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

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.disconnect();
  }
}
