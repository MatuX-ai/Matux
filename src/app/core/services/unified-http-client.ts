/**
 * 统一HTTP客户端
 * 基于原生fetch API，提供统一的HTTP请求处理、认证、重试等功能
 */

import { AuthResponse } from '../models/auth.models';

import { authStateManager, tokenManager } from './auth-state-manager';

/**
 * HTTP请求配置接口
 */
export interface HttpRequestConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  skipAuth?: boolean;
}

/**
 * HTTP 响应接口
 */
export interface HttpResponse<T = unknown> {
  data: T;
  status: number;
  headers: Record<string, string>;
}

/**
 * HTTP客户端配置
 */
export interface HttpClientConfig {
  baseUrl?: string;
  defaultTimeout?: number;
  defaultRetries?: number;
  defaultRetryDelay?: number;
  interceptors?: {
    request?: (config: HttpRequestConfig) => HttpRequestConfig | Promise<HttpRequestConfig>;
    response?: (response: HttpResponse) => HttpResponse | Promise<HttpResponse>;
  };
}

/**
 * 统一HTTP客户端类
 */
export class UnifiedHttpClient {
  private static instance: UnifiedHttpClient;
  private config: Required<HttpClientConfig>;
  private baseUrl: string = '';
  private defaultTimeout: number = 10000;
  private defaultRetries: number = 3;
  private defaultRetryDelay: number = 1000;

  private constructor(config?: HttpClientConfig) {
    this.config = {
      baseUrl: '',
      defaultTimeout: 10000,
      defaultRetries: 3,
      defaultRetryDelay: 1000,
      interceptors: {},
      ...config,
    };

    this.baseUrl = this.config.baseUrl.replace(/\/$/, '');
    this.defaultTimeout = this.config.defaultTimeout;
    this.defaultRetries = this.config.defaultRetries;
    this.defaultRetryDelay = this.config.defaultRetryDelay;
  }

  /**
   * 获取单例实例
   */
  static getInstance(config?: HttpClientConfig): UnifiedHttpClient {
    if (!UnifiedHttpClient.instance) {
      UnifiedHttpClient.instance = new UnifiedHttpClient(config);
    }
    return UnifiedHttpClient.instance;
  }

  /**
   * 设置基础URL
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, '');
  }

  /**
   * 设置默认超时时间
   */
  setDefaultTimeout(timeout: number): void {
    this.defaultTimeout = timeout;
  }

  /**
   * 设置默认重试次数
   */
  setDefaultRetries(retries: number): void {
    this.defaultRetries = retries;
  }

  /**
   * 设置默认重试延迟
   */
  setDefaultRetryDelay(delay: number): void {
    this.defaultRetryDelay = delay;
  }

  /**
   * 发送 HTTP请求
   */
  async request<T = unknown>(config: HttpRequestConfig): Promise<HttpResponse<T>> {
    // 应用请求拦截器
    const processedConfig = await this.applyRequestInterceptors(config);

    // 处理URL
    const fullUrl = this.buildFullUrl(processedConfig.url);

    // 处理头部
    const headers = this.buildHeaders(processedConfig);

    // 处理请求体
    const body = this.buildRequestBody(processedConfig);

    // 执行带重试的请求
    const response = await this.executeRequestWithRetry<T>(
      fullUrl,
      processedConfig.method,
      headers,
      body,
      processedConfig
    );

    // 应用响应拦截器
    return await this.applyResponseInterceptors(response);
  }

  /**
   * GET 请求
   */
  get<T = unknown>(
    url: string,
    config: Omit<HttpRequestConfig, 'method' | 'url'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: 'GET' });
  }

  /**
   * POST 请求
   */
  post<T = unknown, B = unknown>(
    url: string,
    body?: B,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: 'POST', body });
  }

  /**
   * PUT 请求
   */
  put<T = unknown, B = unknown>(
    url: string,
    body?: B,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: 'PUT', body });
  }

  /**
   * DELETE 请求
   */
  delete<T = unknown>(
    url: string,
    config: Omit<HttpRequestConfig, 'method' | 'url'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: 'DELETE' });
  }

  /**
   * PATCH 请求
   */
  patch<T = unknown, B = unknown>(
    url: string,
    body?: B,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: 'PATCH', body });
  }

  /**
   * 构建完整URL
   */
  private buildFullUrl(url: string): string {
    if (url.startsWith('http')) {
      return url;
    }
    return `${this.baseUrl}${url}`;
  }

  /**
   * 构建请求头
   */
  private buildHeaders(config: HttpRequestConfig): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config.headers,
    };

    // 添加认证头（除非明确跳过）
    if (!config.skipAuth) {
      const token = authStateManager.getAccessToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  /**
   * 构建请求体
   */
  private buildRequestBody(config: HttpRequestConfig): string | undefined {
    if (config.body && config.method !== 'GET') {
      return typeof config.body === 'string' ? config.body : JSON.stringify(config.body);
    }
    return undefined;
  }

  /**
   * 执行带重试机制的请求
   */
  private async executeRequestWithRetry<T>(
    url: string,
    method: string,
    headers: Record<string, string>,
    body: string | undefined,
    config: HttpRequestConfig
  ): Promise<HttpResponse<T>> {
    const maxRetries = config.retries ?? this.defaultRetries;
    const retryDelay = config.retryDelay ?? this.defaultRetryDelay;

    let lastError: unknown;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.executeSingleRequestAttempt<T>(url, method, headers, body, config);
      } catch (error) {
        lastError = error;

        // 检查是否应该重试
        if (attempt < maxRetries && this.shouldRetry(error)) {
          await this.delay(retryDelay * Math.pow(2, attempt)); // 指数退避
          continue;
        }

        throw error;
      }
    }

    throw lastError;
  }

  /**
   * 执行单次请求尝试
   */
  private async executeSingleRequestAttempt<T>(
    url: string,
    method: string,
    headers: Record<string, string>,
    body: string | undefined,
    config: HttpRequestConfig
  ): Promise<HttpResponse<T>> {
    // 检查并刷新令牌
    if (!config.skipAuth) {
      await this.checkAndRefreshToken();
    }

    const response = await this.makeFetchRequest<T>(url, method, headers, body, config.timeout);

    // 处理 401 未授权错误
    if (response.status === 401 && !config.skipAuth) {
      return await this.handle401Response<T>(url, method, headers, body, config);
    }

    return response;
  }

  /**
   * 处理 401 未授权响应
   */
  private async handle401Response<T>(
    url: string,
    method: string,
    headers: Record<string, string>,
    body: string | undefined,
    config: HttpRequestConfig
  ): Promise<HttpResponse<T>> {
    const refreshed = await this.handleTokenRefresh();
    if (refreshed) {
      // 使用新令牌重新发送请求
      const newHeaders = this.buildHeaders({ ...config, skipAuth: false });
      return await this.makeFetchRequest<T>(url, method, newHeaders, body, config.timeout);
    }
    throw new HttpError(401, 'Unauthorized and token refresh failed');
  }

  /**
   * 执行实际的 fetch 请求
   */
  private async makeFetchRequest<T>(
    url: string,
    method: string,
    headers: Record<string, string>,
    body: string | undefined,
    timeout: number = this.defaultTimeout
  ): Promise<HttpResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        method,
        headers,
        body,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // 解析响应头和响应体
      const responseHeaders = this.parseResponseHeaders(response);
      const responseData = await this.parseResponseBody<Record<string, unknown>>(response);

      // 检查 HTTP 状态
      if (!response.ok) {
        const message =
          typeof responseData['message'] === 'string'
            ? responseData['message']
            : typeof responseData['detail'] === 'string'
              ? responseData['detail']
              : `HTTP ${response.status}`;
        throw new HttpError(response.status, message, responseData);
      }

      return {
        data: responseData as unknown as T,
        status: response.status,
        headers: responseHeaders,
      };
    } catch (error) {
      clearTimeout(timeoutId);
      return this.handleFetchError(error, timeout);
    }
  }

  /**
   * 解析响应头
   */
  private parseResponseHeaders(response: Response): Record<string, string> {
    const responseHeaders: Record<string, string> = {};
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value;
    });
    return responseHeaders;
  }

  /**
   * 解析响应体
   */
  private async parseResponseBody<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');

    if (contentType?.includes('application/json')) {
      return (await response.json()) as T;
    } else {
      return (await response.text()) as T;
    }
  }

  /**
   * 处理 fetch 错误
   */
  private handleFetchError(error: unknown, timeout: number): never {
    if (error instanceof HttpError) {
      throw error;
    }

    if (error instanceof Error && error.name === 'AbortError') {
      throw new HttpError(408, `Request timeout after ${timeout}ms`);
    }

    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new HttpError(0, `Network error: ${errorMessage}`);
  }

  /**
   * 检查并刷新令牌
   */
  private async checkAndRefreshToken(): Promise<void> {
    const accessToken = authStateManager.getAccessToken();
    if (accessToken && tokenManager.isTokenExpiringSoon(accessToken)) {
      await this.handleTokenRefresh();
    }
  }

  /**
   * 处理令牌刷新
   */
  private async handleTokenRefresh(): Promise<boolean> {
    const refreshToken = authStateManager.getRefreshToken();
    if (!refreshToken) {
      authStateManager.clearAuthData();
      this.dispatchLogoutEvent();
      return false;
    }

    try {
      const refreshResult = await tokenManager.refreshAuthToken(async () => {
        const response = await this.post<AuthResponse>(
          '/api/auth/refresh',
          {
            refreshToken,
          },
          { skipAuth: true }
        );
        return response.data;
      });

      // 更新认证数据
      authStateManager.storeAuthData(refreshResult);
      return true;
    } catch (error) {
      authStateManager.clearAuthData();
      this.dispatchLogoutEvent();
      return false;
    }
  }

  /**
   * 判断是否应该重试
   */
  private shouldRetry(error: unknown): boolean {
    // 网络错误或 5xx 服务器错误时重试
    if (error instanceof TypeError || (error instanceof Error && error.message.includes('fetch'))) {
      return true;
    }

    // 服务器错误时重试
    if (error && typeof error === 'object' && 'status' in error) {
      const status = (error as { status: number }).status;
      if (status && status >= 500 && status < 600) {
        return true;
      }
    }

    return false;
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * 应用请求拦截器
   */
  private async applyRequestInterceptors(config: HttpRequestConfig): Promise<HttpRequestConfig> {
    if (this.config.interceptors?.request) {
      return await this.config.interceptors.request(config);
    }
    return config;
  }

  /**
   * 应用响应拦截器
   */
  private async applyResponseInterceptors<T>(response: HttpResponse<T>): Promise<HttpResponse<T>> {
    if (this.config.interceptors?.response) {
      const interceptedResponse = await this.config.interceptors.response(response as HttpResponse);
      return interceptedResponse as HttpResponse<T>;
    }
    return response;
  }

  /**
   * 触发登出事件
   */
  private dispatchLogoutEvent(): void {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
  }
}

/**
 * HTTP 错误类
 */
export class HttpError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

// 导出单例实例
export const unifiedHttpClient = UnifiedHttpClient.getInstance();

// 导出类型 (避免重复导出)
// export type { HttpRequestConfig, HttpResponse, HttpClientConfig };
