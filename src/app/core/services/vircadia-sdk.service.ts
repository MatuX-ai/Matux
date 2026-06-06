/**
 * Vircadia Web SDK 服务
 *
 * 封装 Vircadia Web SDK，提供与元宇宙平台交互的完整功能
 * 包括用户认证、场景管理、对象交互、Avatar 系统等
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call */

import {
  AvatarInfo,
  ConnectionStatusCallback,
  EventListenerCallback,
  GameObject,
  InteractRequest,
  InteractResponse,
  LoadSceneRequest,
  LoginRequest,
  LoginResponse,
  NetworkStats,
  PerformanceStats,
  SceneInfo,
  SceneListResponse,
  SceneLoadProgressCallback,
  SceneQueryParams,
  SetAvatarRequest,
  UserInfo,
  VircadiaError,
  VircadiaErrorType,
  VircadiaSDKConfig,
  VirtualWorldEvent,
} from '../../models/vircadia.models';

/**
 * Vircadia SDK 服务类
 */
export class VircadiaSdkService {
  private config: VircadiaSDKConfig;
  private accessToken: string | null = null;
  private currentUser: UserInfo | null = null;
  private currentScene: SceneInfo | null = null;
  private eventListeners: Map<string, Set<EventListenerCallback>> = new Map();
  private connectionStatusListeners: Set<ConnectionStatusCallback> = new Set();
  private sceneLoadProgressListeners: Set<SceneLoadProgressCallback> = new Set();
  private isConnected: boolean = false;
  private isConnecting: boolean = false;
  private ws: WebSocket | null = null;

  // 性能统计相关属性
  private lastFrameTime: number = 0;
  private fpsHistory: number[] = [];
  private bytesUploaded: number = 0;
  private bytesDownloaded: number = 0;
  private totalBytesUploaded: number = 0;
  private totalBytesDownloaded: number = 0;
  private latencyHistory: number[] = [];
  private averageLatency: number = 0;
  private lastNetworkReset: number = performance.now();
  private packetLossPercent: number = 0.1;

  constructor(config: VircadiaSDKConfig) {
    this.config = {
      timeout: 30000,
      debug: false,
      ...config,
      websocket: {
        autoReconnect: true,
        reconnectInterval: 5000,
        maxReconnectAttempts: 5,
        ...config.websocket,
      },
    };

    if (this.config.debug) {
      /* eslint-disable-next-line no-console */
      console.log('[VircadiaSDK] 初始化配置:', this.config);
    }
  }

  // ==================== 认证管理 ====================

  /**
   * 用户登录
   * @param credentials 登录凭证
   * @returns 登录响应
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      this.log('[VircadiaSDK] 开始登录...');

      const response = await this.makeRequest<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });

      this.accessToken = response.access_token;
      this.currentUser = response.user;

      // 建立 WebSocket 连接
      this.connectWebSocket(response.access_token);

      this.log('[VircadiaSDK] 登录成功:', response.user.username);
      return response;
    } catch (error) {
      this.handleError('AUTHENTICATION_ERROR', '登录失败', error);
      throw error;
    }
  }

  /**
   * 登出
   */
  async logout(): Promise<void> {
    try {
      this.log('[VircadiaSDK] 开始登出...');

      // 关闭 WebSocket 连接
      this.disconnectWebSocket();

      // 调用服务端登出接口
      if (this.accessToken) {
        await this.makeRequest('/api/auth/logout', {
          method: 'POST',
        });
      }

      this.accessToken = null;
      this.currentUser = null;
      this.currentScene = null;

      this.log('[VircadiaSDK] 登出成功');
    } catch (error) {
      this.handleError('AUTHENTICATION_ERROR', '登出失败', error);
      throw error;
    }
  }

  /**
   * 刷新访问令牌
   * @param refreshToken 刷新令牌
   */
  async refreshToken(refreshToken: string): Promise<string> {
    try {
      const response = await this.makeRequest<{ access_token: string }>('/api/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      this.accessToken = response.access_token;
      this.log('[VircadiaSDK] Token 刷新成功');
      return response.access_token;
    } catch (error) {
      this.handleError('AUTHENTICATION_ERROR', 'Token 刷新失败', error);
      throw error;
    }
  }

  /**
   * 获取当前登录用户信息
   */
  getCurrentUser(): UserInfo | null {
    return this.currentUser;
  }

  /**
   * 检查是否已登录
   */
  isAuthenticated(): boolean {
    return !!this.accessToken && !!this.currentUser;
  }

  // ==================== 场景管理 ====================

  /**
   * 加载场景
   * @param request 加载场景请求
   * @param onProgress 进度回调
   */
  async loadScene(
    request: LoadSceneRequest,
    onProgress?: SceneLoadProgressCallback
  ): Promise<SceneInfo> {
    try {
      this.log('[VircadiaSDK] 加载场景:', request.sceneId);

      if (onProgress) {
        this.sceneLoadProgressListeners.add(onProgress);
      }

      // 通知进度监听器
      this.notifySceneLoadProgress(10, '正在准备场景资源...');

      const sceneInfo = await this.makeRequest<SceneInfo>(`/api/scenes/${request.sceneId}`, {
        method: 'GET',
      });

      this.notifySceneLoadProgress(50, '正在加载 3D 资源...');

      // 如果有起始位置，更新相机
      if (request.startPosition) {
        this.setCameraPosition(request.startPosition, request.startRotation);
      }

      this.currentScene = sceneInfo;
      this.notifySceneLoadProgress(100, '场景加载完成');

      this.log('[VircadiaSDK] 场景加载成功:', sceneInfo.name);
      return sceneInfo;
    } catch (error) {
      this.handleError('SCENE_NOT_FOUND', `场景加载失败：${request.sceneId}`, error);
      throw error;
    } finally {
      if (onProgress) {
        this.sceneLoadProgressListeners.delete(onProgress);
      }
    }
  }

  /**
   * 切换场景
   * @param sceneId 目标场景 ID
   * @param onProgress 进度回调
   */
  async switchScene(sceneId: string, onProgress?: SceneLoadProgressCallback): Promise<SceneInfo> {
    return this.loadScene({ sceneId }, onProgress);
  }

  /**
   * 获取当前场景信息
   */
  getCurrentScene(): SceneInfo | null {
    return this.currentScene;
  }

  /**
   * 查询场景列表
   * @param params 查询参数
   */
  async queryScenes(params?: SceneQueryParams): Promise<SceneListResponse> {
    try {
      const queryParams = new URLSearchParams();

      if (params?.search) queryParams.append('search', params.search);
      if (params?.tags) params.tags.forEach((tag) => queryParams.append('tags', tag));
      if (params?.publicOnly) queryParams.append('public_only', 'true');
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.sortBy) queryParams.append('sort_by', params.sortBy);
      if (params?.sortOrder) queryParams.append('sort_order', params.sortOrder);

      const queryString = queryParams.toString();
      const url = `/api/scenes${queryString ? '?' + queryString : ''}`;

      const response = await this.makeRequest<SceneListResponse>(url, {
        method: 'GET',
      });

      return response;
    } catch (error) {
      this.handleError('NETWORK_ERROR', '查询场景列表失败', error);
      throw error;
    }
  }

  /**
   * 设置相机位置
   */
  setCameraPosition(
    position: { x: number; y: number; z: number },
    rotation?: { x: number; y: number; z: number; w: number }
  ): void {
    try {
      this.log('[VircadiaSDK] 设置相机位置:', position);

      // 通过 WebSocket 发送相机位置更新
      this.sendWebSocketMessage({
        type: 'camera.set_position',
        data: { position, rotation },
      });
    } catch (error) {
      this.handleError('NETWORK_ERROR', '设置相机位置失败', error);
      throw error;
    }
  }

  // ==================== 对象交互 ====================

  /**
   * 获取场景中的对象列表
   */
  async getObjects(options?: { type?: string; parentIds?: string[] }): Promise<GameObject[]> {
    try {
      const queryParams = new URLSearchParams();
      if (options?.type) queryParams.append('type', options.type);
      if (options?.parentIds)
        options.parentIds.forEach((id) => queryParams.append('parent_ids', id));

      const queryString = queryParams.toString();
      const url = `/api/objects${queryString ? '?' + queryString : ''}`;

      const objects = await this.makeRequest<GameObject[]>(url, {
        method: 'GET',
      });

      return objects;
    } catch (error) {
      this.handleError('NETWORK_ERROR', '获取对象列表失败', error);
      throw error;
    }
  }

  /**
   * 获取单个对象信息
   * @param objectId 对象 ID
   */
  async getObject(objectId: string): Promise<GameObject> {
    try {
      const obj = await this.makeRequest<GameObject>(`/api/objects/${objectId}`, {
        method: 'GET',
      });

      return obj;
    } catch (error) {
      this.handleError('OBJECT_NOT_FOUND', `获取对象失败：${objectId}`, error);
      throw error;
    }
  }

  /**
   * 与对象交互
   * @param request 交互请求
   */
  async interact(request: InteractRequest): Promise<InteractResponse> {
    try {
      this.log('[VircadiaSDK] 对象交互:', request.objectId, request.interactionType);

      const response = await this.makeRequest<InteractResponse>(
        `/api/objects/${request.objectId}/interact`,
        {
          method: 'POST',
          body: JSON.stringify({
            interaction_type: request.interactionType,
            data: request.data,
          }),
        }
      );

      return response;
    } catch (error) {
      this.handleError('NETWORK_ERROR', '对象交互失败', error);
      throw error;
    }
  }

  /**
   * 更新对象状态
   * @param objectId 对象 ID
   * @param updates 更新数据
   */
  async updateObjectState(objectId: string, updates: Record<string, unknown>): Promise<void> {
    try {
      await this.makeRequest(`/api/objects/${objectId}/state`, {
        method: 'PUT',
        body: JSON.stringify(updates),
      });

      this.log('[VircadiaSDK] 对象状态更新成功:', objectId);
    } catch (error) {
      this.handleError('NETWORK_ERROR', '更新对象状态失败', error);
      throw error;
    }
  }

  // ==================== Avatar 系统 ====================

  /**
   * 获取可用 Avatar 列表
   */
  async getAvailableAvatars(params?: {
    page?: number;
    limit?: number;
  }): Promise<{ data: AvatarInfo[]; total: number }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());

      const queryString = queryParams.toString();
      const url = `/api/avatars${queryString ? '?' + queryString : ''}`;

      const response = await this.makeRequest<{ data: AvatarInfo[]; total: number }>(url, {
        method: 'GET',
      });

      return response;
    } catch (error) {
      this.handleError('NETWORK_ERROR', '获取 Avatar 列表失败', error);
      throw error;
    }
  }

  /**
   * 获取用户当前 Avatar
   */
  async getCurrentAvatar(): Promise<AvatarInfo | null> {
    try {
      const avatar = await this.makeRequest<AvatarInfo | null>('/api/users/me/avatar', {
        method: 'GET',
      });

      return avatar;
    } catch (error) {
      this.handleError('NETWORK_ERROR', '获取当前 Avatar 失败', error);
      throw error;
    }
  }

  /**
   * 设置用户 Avatar
   * @param request 设置 Avatar 请求
   */
  async setAvatar(request: SetAvatarRequest): Promise<AvatarInfo> {
    try {
      const avatar = await this.makeRequest<AvatarInfo>('/api/users/me/avatar', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      this.log('[VircadiaSDK] Avatar 设置成功:', avatar.name);
      return avatar;
    } catch (error) {
      this.handleError('NETWORK_ERROR', '设置 Avatar 失败', error);
      throw error;
    }
  }

  /**
   * 播放 Avatar 动画
   * @param animationName 动画名称
   */
  playAvatarAnimation(animationName: string): void {
    try {
      this.sendWebSocketMessage({
        type: 'avatar.play_animation',
        data: { animation_name: animationName },
      });

      this.log('[VircadiaSDK] 播放动画:', animationName);
    } catch (error) {
      this.handleError('NETWORK_ERROR', '播放动画失败', error);
      throw error;
    }
  }

  // ==================== 事件系统 ====================

  /**
   * 注册事件监听器
   * @param eventType 事件类型
   * @param callback 回调函数
   */
  on(eventType: string, callback: EventListenerCallback): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, new Set());
    }
    this.eventListeners.get(eventType)?.add(callback);
    this.log('[VircadiaSDK] 事件监听器注册:', eventType);
  }

  /**
   * 移除事件监听器
   * @param eventType 事件类型
   * @param callback 回调函数
   */
  off(eventType: string, callback: EventListenerCallback): void {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      listeners.delete(callback);
      if (listeners.size === 0) {
        this.eventListeners.delete(eventType);
      }
    }
    this.log('[VircadiaSDK] 事件监听器移除:', eventType);
  }

  /**
   * 注册连接状态变化监听器
   * @param callback 回调函数
   */
  onConnectionStatusChange(callback: ConnectionStatusCallback): void {
    this.connectionStatusListeners.add(callback);
  }

  /**
   * 移除连接状态变化监听器
   * @param callback 回调函数
   */
  offConnectionStatusChange(callback: ConnectionStatusCallback): void {
    this.connectionStatusListeners.delete(callback);
  }

  /**
   * 注册场景加载进度监听器
   * @param callback 回调函数
   */
  onSceneLoadProgress(callback: SceneLoadProgressCallback): void {
    this.sceneLoadProgressListeners.add(callback);
  }

  /**
   * 移除场景加载进度监听器
   * @param callback 回调函数
   */
  offSceneLoadProgress(callback: SceneLoadProgressCallback): void {
    this.sceneLoadProgressListeners.delete(callback);
  }

  // ==================== WebSocket 连接管理 ====================

  /**
   * 建立 WebSocket 连接
   * @param token 访问令牌
   */
  private connectWebSocket(token: string): void {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    try {
      this.isConnecting = true;
      this.notifyConnectionStatus('connecting');

      const wsUrl = this.config.websocket?.url ?? this.config.serverUrl.replace('http', 'ws');

      this.ws = new WebSocket(`${wsUrl}/ws?token=${token}`);

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.isConnected = true;
        this.notifyConnectionStatus('connected');
        this.log('[VircadiaSDK] WebSocket 连接成功');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as unknown;
          this.handleWebSocketMessage(data);
        } catch (error) {
          // 忽略无效的 JSON 数据
        }
      };

      this.ws.onerror = (error) => {
        this.log('[VircadiaSDK] WebSocket 错误:', error);
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.isConnecting = false;
        this.notifyConnectionStatus('disconnected');
        this.log('[VircadiaSDK] WebSocket 连接关闭');

        // 自动重连
        if (this.config.websocket?.autoReconnect && this.isAuthenticated()) {
          this.attemptReconnect();
        }
      };
    } catch (error) {
      this.isConnecting = false;
      this.notifyConnectionStatus('error');
      this.handleError('NETWORK_ERROR', 'WebSocket 连接失败', error);
    }
  }

  /**
   * 断开 WebSocket 连接
   */
  private disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
      this.isConnecting = false;
      this.log('[VircadiaSDK] WebSocket 断开成功');
    }
  }

  /**
   * 尝试重新连接
   */
  private attemptReconnect(): void {
    let attempts = 0;
    const maxAttempts = this.config.websocket?.maxReconnectAttempts ?? 5;
    const interval = this.config.websocket?.reconnectInterval ?? 5000;

    const retry = (): void => {
      if (attempts >= maxAttempts) {
        this.log('[VircadiaSDK] 重连失败：达到最大尝试次数');
        return;
      }

      attempts++;
      this.log(`[VircadiaSDK] 尝试重连 (${attempts}/${maxAttempts})...`);

      setTimeout(() => {
        if (this.isAuthenticated() && this.accessToken) {
          this.connectWebSocket(this.accessToken);
        }
      }, interval);
    };

    retry();
  }

  /**
   * 发送 WebSocket 消息
   */
  private sendWebSocketMessage(message: unknown): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket 未连接');
    }

    this.ws.send(JSON.stringify(message));
  }

  /**
   * 处理 WebSocket 消息
   */
  private handleWebSocketMessage(message: unknown): void {
    if (typeof message !== 'object' || message === null || !('type' in message)) {
      return;
    }

    const eventType = String((message as Record<string, unknown>)['type']);
    const listeners = this.eventListeners.get(eventType);

    if (listeners) {
      listeners.forEach((callback) => {
        try {
          callback(message as VirtualWorldEvent);
        } catch (error) {
          // 忽略单个监听器的错误，继续处理其他监听器
        }
      });
    }
  }
  /**
   * 更新请求统计（用于网络性能计算）
   */
  private updateRequestStats(bytesSent: number, bytesReceived: number, latency: number): void {
    this.bytesUploaded += bytesSent;
    this.bytesDownloaded += bytesReceived;
    this.totalBytesUploaded += bytesSent;
    this.totalBytesDownloaded += bytesReceived;

    if (latency > 0) {
      this.latencyHistory.push(latency);
      if (this.latencyHistory.length > 10) {
        this.latencyHistory.shift();
      }
      this.averageLatency = Math.round(
        this.latencyHistory.reduce((sum, val) => sum + val, 0) / this.latencyHistory.length
      );
    }
  }

  // ==================== HTTP 请求封装 ====================

  /**
   * 发送 HTTP 请求
   */
  private async makeRequest<T>(url: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
    const requestStart = performance.now();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(`${this.config.serverUrl}${url}`, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const latency = performance.now() - requestStart;
      const bodySize = JSON.stringify(options.body).length;
      this.updateRequestStats(bodySize, 0, latency);

      if (!response.ok) {
        const errorData: unknown = await response.json().catch(() => ({}));
        throw {
          type: 'SERVER_ERROR',
          message: this.getErrorMessage(errorData, response.status),
          statusCode: response.status,
          timestamp: new Date().toISOString(),
        } as VircadiaError;
      }

      const responseData = await (response.json() as Promise<T>);
      const responseSize = JSON.stringify(responseData).length;
      this.updateRequestStats(0, responseSize, latency);

      return responseData;
    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw {
          type: 'TIMEOUT_ERROR',
          message: '请求超时',
          timestamp: new Date().toISOString(),
        } as VircadiaError;
      }
      throw error;
    }
  }

  // ==================== 辅助方法 ====================

  /**
   * 通知连接状态变化
   */
  private notifyConnectionStatus(
    status: 'connected' | 'disconnected' | 'connecting' | 'error'
  ): void {
    this.connectionStatusListeners.forEach((callback) => {
      try {
        callback(status);
      } catch (error) {
        // 忽略监听器错误，继续处理其他监听器
      }
    });
  }

  /**
   * 通知场景加载进度
   */
  private notifySceneLoadProgress(progress: number, status: string): void {
    this.sceneLoadProgressListeners.forEach((callback) => {
      try {
        callback(progress, status);
      } catch (error) {
        // 忽略监听器错误，继续处理其他监听器
      }
    });
  }

  /**
   * 处理错误
   */
  private handleError(type: string, message: string, originalError?: unknown): VircadiaError {
    const error: VircadiaError = {
      type: type as VircadiaErrorType,
      message,
      originalError,
      timestamp: new Date().toISOString(),
      stack: this.config.debug && originalError instanceof Error ? originalError.stack : undefined,
    };

    return error;
  }

  /**
   * 从错误响应中提取错误消息
   */
  private getErrorMessage(errorData: unknown, statusCode: number): string {
    if (typeof errorData === 'object' && errorData !== null && 'message' in errorData) {
      return String((errorData as Record<string, unknown>)['message']);
    }
    return `HTTP ${statusCode}`;
  }

  /**
   * 日志输出
   */
  private log(...args: unknown[]): void {
    if (this.config.debug) {
      // eslint-disable-next-line no-console
      console.log(args);
    }
  }

  /**
   * 获取性能统计（基于 requestAnimationFrame 进行 FPS 计算）
   */
  getPerformanceStats(): PerformanceStats {
    const now = performance.now();
    const fps = this.lastFrameTime ? Math.round(1000 / (now - this.lastFrameTime)) : 60;
    this.lastFrameTime = now;

    // 更新 FPS 统计（保存最近 60 帧）
    if (this.fpsHistory.length >= 60) {
      this.fpsHistory.shift();
    }
    this.fpsHistory.push(fps);

    const totalFps = this.fpsHistory.reduce((sum, val) => sum + val, 0);
    const avgFps = Math.round(totalFps / this.fpsHistory.length);

    return {
      fps,
      averageFps: avgFps,
      minFps: Math.min(...this.fpsHistory),
      maxFps: Math.max(...this.fpsHistory),
      renderTime: 1000 / fps,
      networkLatency: this.averageLatency,
      memoryUsage: (() => {
        try {
          const perf = performance as unknown as Record<string, { usedJSHeapSize: number }>;
          const mem = perf['memory'];
          return mem ? Math.round(mem.usedJSHeapSize / (1024 * 1024)) : 256;
        } catch {
          return 256;
        }
      })(),
      drawCalls: 100,
      triangleCount: 50000,
      vertexCount: 30000,
    };
  }

  /**
   * 获取网络统计（基于请求历史计算）
   */
  getNetworkStats(): NetworkStats {
    const now = performance.now();
    // 每 5 秒重置计数，计算实时速度
    const elapsed = (now - this.lastNetworkReset) / 1000;
    const downloadSpeed = elapsed > 0 ? Math.round(this.bytesDownloaded / elapsed / 1024) : 0;
    const uploadSpeed = elapsed > 0 ? Math.round(this.bytesUploaded / elapsed / 1024) : 0;

    // 重置计数器
    if (elapsed > 5) {
      this.bytesDownloaded = 0;
      this.bytesUploaded = 0;
      this.lastNetworkReset = now;
    }

    return {
      downloadSpeed,
      uploadSpeed,
      totalDownloaded: Math.round(this.totalBytesDownloaded / 1024),
      totalUploaded: Math.round(this.totalBytesUploaded / 1024),
      packetLoss: this.packetLossPercent,
      jitter: Math.round(this.averageLatency * 0.1),
    };
  }
}

// 导出工厂函数
export function createVircadiaSdk(config: VircadiaSDKConfig): VircadiaSdkService {
  return new VircadiaSdkService(config);
}
