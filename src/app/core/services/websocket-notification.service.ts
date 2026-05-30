/**
 * WebSocket Notification Service
 *
 * WebSocket 实时通知推送服务
 * 支持连接管理、心跳检测、自动重连等功能
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { filter, map } from 'rxjs/operators';

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

@Injectable({
  providedIn: 'root',
})
export class WebSocketNotificationService {
  private ws: WebSocket | null = null;
  private readonly WS_URL = 'ws://localhost:8080/ws/notifications'; // TODO: 替换为实际地址

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

  // 重连配置
  private reconnectAttempts = 0;
  private readonly MAX_RECONNECT_ATTEMPTS = 5;
  private readonly RECONNECT_DELAY = 5000; // 5 秒

  // 是否启用 (开发时可禁用)
  private enabled = true;

  constructor() {}

  /**
   * 连接到 WebSocket 服务器
   */
  connect(): void {
    if (!this.enabled || typeof WebSocket === 'undefined') {
      console.warn('WebSocket 不支持或未启用');
      return;
    }

    if (
      this.ws &&
      (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)
    ) {
      // eslint-disable-next-line no-console
      console.log('WebSocket 已在连接中');
      return;
    }

    this.statusSubject.next(ConnectionStatus.CONNECTING);

    try {
      this.ws = new WebSocket(this.WS_URL);

      this.ws.onopen = () => {
        // eslint-disable-next-line no-console
        console.log('WebSocket 连接成功');
        this.statusSubject.next(ConnectionStatus.CONNECTED);
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        try {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          const message = JSON.parse(event.data) as WsMessage;
          this.messageSubject.next(message);

          if (message.type === WsMessageType.PONG) {
            // 心跳响应，无需处理
          } else if (message.type === WsMessageType.ERROR) {
            console.error('WebSocket 错误:', message.data);
          }
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
      };

      this.ws.onclose = (event) => {
        // eslint-disable-next-line no-console
        console.log('WebSocket 连接关闭:', event.code, event.reason);
        this.statusSubject.next(ConnectionStatus.DISCONNECTED);
        this.stopHeartbeat();

        // 尝试重连
        if (event.code !== 1000) {
          // 非正常关闭
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

    if (this.ws) {
      this.ws.close(1000, '用户主动断开');
      this.ws = null;
    }

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
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.MAX_RECONNECT_ATTEMPTS) {
      console.error('WebSocket 重连次数已达上限');
      return;
    }

    this.reconnectAttempts++;
    this.statusSubject.next(ConnectionStatus.RECONNECTING);

    setTimeout(() => {
      // eslint-disable-next-line no-console
      console.log(`WebSocket 尝试第 ${this.reconnectAttempts} 次重连`);
      this.connect();
    }, this.RECONNECT_DELAY);
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
}
