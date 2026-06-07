/**
 * WebSocket Notification Service
 *
 * WebSocket 实时通知推送服务
 * 支持连接管理、心跳检测、自动重连等功能
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { filter, map } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

/**
 * WebSocket 消息类型
 */
export enum WsMessageType {
  /** 通知消息 */
  NOTIFICATION = 'notification',
  /** 系统消息 */
  SYSTEM = 'system',
  /** 心跳响应 */
  PONG = 'pong',
  /** 错误消息 */
  ERROR = 'error',
}

/**
 * WebSocket 消息结构
 */
export interface WsMessage<T = unknown> {
  /** 消息类型 */
  type: WsMessageType;

  /** 消息内容 */
  data: T;

  /** 发送时间 */
  timestamp: string;

  /** 消息 ID */
  messageId?: string;
}

/**
 * 通知类型的消息数据
 */
export interface NotificationMessageData {
  /** 通知 ID */
  notificationId: number;

  /** 标题 */
  title: string;

  /** 内容摘要 */
  summary: string;

  /** 优先级 */
  priority: 'low' | 'medium' | 'high' | 'urgent';

  /** 跳转链接 */
  link?: string;
}

/**
 * 连接状态
 */
export enum ConnectionStatus {
  /** 未连接 */
  DISCONNECTED = 'disconnected',
  /** 连接中 */
  CONNECTING = 'connecting',
  /** 已连接 */
  CONNECTED = 'connected',
  /** 重连中 */
  RECONNECTING = 'reconnecting',
}

/** 重连状态 */
export interface WsReconnectState {
  attempting: boolean;
  attempt: number;
  maxAttempts: number;
  nextDelay: number;
}

@Injectable({
  providedIn: 'root',
})
export class WebSocketNotificationService implements OnDestroy {
  private ws: WebSocket | null = null;
  private readonly WS_URL = `${environment.wsUrl}/ws/notifications`;

  // 消息接收器
  private messageSubject = new Subject<WsMessage>();
  public messages$ = this.messageSubject.asObservable();

  // 连接状态
  private statusSubject = new BehaviorSubject<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  public connectionStatus$ = this.statusSubject.asObservable();

  // 通知消息流
  public notifications$ = this.messages$.pipe(
    filter((msg) => msg.type === WsMessageType.NOTIFICATION),
    map((msg) => msg.data as NotificationMessageData)
  );

  // 心跳定时器
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private heartbeatTimer: any = null;
  private readonly HEARTBEAT_INTERVAL = 30000; // 30 秒
  private pongTimeoutMs = 10000;
  private pongTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private lastPongTime: number = 0;

  // 重连配置
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseDelay = 2000;
  private maxDelay = 30000;
  private jitterMax = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  // 重连状态流
  private reconnectStateSubject = new BehaviorSubject<WsReconnectState>({
    attempting: false,
    attempt: 0,
    maxAttempts: this.maxReconnectAttempts,
    nextDelay: 0,
  });
  readonly reconnectState$ = this.reconnectStateSubject.asObservable();

  // 是否启用 (开发时可禁用)
  private enabled = true;

  private destroy$ = new Subject<void>();

  constructor() {}

  /**
   * 连接到 WebSocket 服务器
   */
  // eslint-disable-next-line max-lines-per-function
  connect(): void {
    if (!this.enabled || typeof WebSocket === 'undefined') {
      console.warn('WebSocket 不支持或未启用');
      return;
    }

    if (
      this.ws &&
      (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    this.statusSubject.next(ConnectionStatus.CONNECTING);

    try {
      this.ws = new WebSocket(this.WS_URL);

      // 连接超时保护：2 秒连不上就放弃（后端通常没 WS endpoint）
      const connectTimer = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.warn('[WS] 连接超时，主动关闭');
          this.ws.close();
          this.statusSubject.next(ConnectionStatus.DISCONNECTED);
        }
      }, 2000);
      this.ws.addEventListener('open', () => clearTimeout(connectTimer), { once: true });
      this.ws.addEventListener('close', () => clearTimeout(connectTimer), { once: true });
      this.ws.addEventListener('error', () => clearTimeout(connectTimer), { once: true });

      this.ws.onopen = () => {
        this.statusSubject.next(ConnectionStatus.CONNECTED);
        this.reconnectAttempts = 0;
        this.lastPongTime = Date.now();
        this.updateReconnectState(false, 0);
        this.startHeartbeat();
        this.startPongTimeout();
      };

      this.ws.onmessage = (event) => {
        try {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          const message = JSON.parse(event.data) as WsMessage;

          if (message.type === WsMessageType.PONG) {
            this.lastPongTime = Date.now();
          } else if (message.type === WsMessageType.ERROR) {
            console.error('WebSocket 错误:', message.data);
          }

          this.messageSubject.next(message);
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
      };

      this.ws.onclose = (event) => {
        this.statusSubject.next(ConnectionStatus.DISCONNECTED);
        this.stopHeartbeat();
        this.stopPongTimeout();

        // 尝试重连（code 1000=正常关闭不重连）
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('创建 WebSocket 连接失败:', error);
      this.statusSubject.next(ConnectionStatus.DISCONNECTED);
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.stopHeartbeat();
    this.stopPongTimeout();
    this.clearReconnectTimer();

    if (this.ws) {
      this.ws.close(1000, '用户主动断开');
      this.ws = null;
    }

    this.reconnectAttempts = 0;
    this.reconnectStateSubject.next({
      attempting: false,
      attempt: 0,
      maxAttempts: this.maxReconnectAttempts,
      nextDelay: 0,
    });
    this.statusSubject.next(ConnectionStatus.DISCONNECTED);
  }

  /**
   * 发送消息
   */
  send<T>(message: WsMessage<T>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket 未连接，无法发送消息');
    }
  }

  /**
   * 开始心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send({
          type: WsMessageType.PONG,
          data: {},
          timestamp: new Date().toISOString(),
        });
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 计算指数退避延迟（带抖动）
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
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket 重连次数已达上限');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.calculateBackoff(this.reconnectAttempts);

    this.statusSubject.next(ConnectionStatus.RECONNECTING);
    this.updateReconnectState(true, delay);

    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      // eslint-disable-next-line no-console
      console.log(`WebSocket 尝试第 ${this.reconnectAttempts} 次重连`);
      this.connect();
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

  /**
   * 启动 pong 超时检测
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
          this.forceReconnect();
        }
      },
      Math.min(this.pongTimeoutMs, 5000)
    );
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
   * 强制重连
   */
  private forceReconnect(): void {
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close(4001, 'Heartbeat timeout');
      this.ws = null;
    }

    this.statusSubject.next(ConnectionStatus.DISCONNECTED);
    this.stopHeartbeat();
    this.stopPongTimeout();

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * 获取连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 监听特定类型的通知
   */
  onNotificationType(type: WsMessageType): Observable<WsMessage> {
    return this.messages$.pipe(filter((msg) => msg.type === type));
  }

  /**
   * 启用服务
   */
  enable(): void {
    this.enabled = true;
  }

  /**
   * 禁用服务
   */
  disable(): void {
    this.enabled = false;
    this.disconnect();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.clearReconnectTimer();
    this.disconnect();
  }
}
