/**
 * AI SDK HTTP 客户端
 *
 * 保持与原有 API 完全兼容，内部委托共享 HttpClient 执行实际请求。
 * 新代码请直接使用 src/shared/services/http-client.ts。
 */

import {
  HttpClient as SharedHttpClient,
  HttpRequestConfig as SharedHttpRequestConfig,
} from '../shared/services/http-client';
import type { HttpError } from './types';

// ============================================================
// 重新导出共享 HTTP 客户端中的枚举/接口（API 兼容）
// ============================================================

/**
 * HTTP 请求方法枚举
 * @deprecated 请统一使用 shared/services/http-client 中的 HttpMethod
 */
export enum HttpMethod {
  GET = 'GET',
  POST = 'POST',
  PUT = 'PUT',
  DELETE = 'DELETE',
  PATCH = 'PATCH',
}

/**
 * HTTP 请求配置接口
 */
export interface HttpRequestConfig {
  method: HttpMethod;
  url: string;
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  accessToken?: string;
}

/**
 * HTTP 响应接口
 */
export interface HttpResponse<T = any> {
  status: number;
  data: T;
  headers: Record<string, string>;
}

// ============================================================
// HttpClient — 兼容类，内部委托共享 HttpClient
// ============================================================

/**
 * @deprecated 请直接使用 src/shared/services/http-client 中的 HttpClient。
 * 此类仅保留以保持 ai-client / creativity-client 的向后兼容。
 */
export class HttpClient {
  private baseUrl: string;
  private defaultTimeout: number;
  /** 当前 accessToken（用于 tokenProvider） */
  private currentAccessToken?: string;
  /** 内部共享 HttpClient 实例 */
  private sharedClient: SharedHttpClient;

  constructor(
    baseUrl: string,
    defaultTimeout: number = 10000,
    defaultHeaders: Record<string, string> = {}
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.defaultTimeout = defaultTimeout;

    // 初始化 sharedHttpClient，并注册 token provider
    this.sharedClient = new SharedHttpClient({
      tokenProvider: {
        getToken: () => this.currentAccessToken ?? null,
        onUnauthorized: () => {
          this.currentAccessToken = undefined;
        },
      },
    });

    // 如果有默认 Authorization 头，同步到 currentAccessToken
    if (defaultHeaders['Authorization']) {
      this.currentAccessToken = defaultHeaders['Authorization'].replace(/^Bearer\s+/i, '');
    }
  }

  /**
   * 发送 HTTP 请求 — 委托给共享 HttpClient
   */
  async request<T = any>(config: HttpRequestConfig): Promise<HttpResponse<T>> {
    const { method, url, headers = {}, body, timeout = this.defaultTimeout } = config;

    const fullUrl = url.startsWith('http') ? url : `${this.baseUrl}${url}`;

    const mergedHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    // 合并 accessToken 到请求头
    if (config.accessToken) {
      mergedHeaders['Authorization'] = `Bearer ${config.accessToken}`;
    }

    // 构建共享配置
    const sharedConfig: SharedHttpRequestConfig = {
      url: fullUrl,
      method: method as string,
      headers: mergedHeaders,
      body: body ?? undefined,
      timeout,
      retries: 0,
      skipAuth: !mergedHeaders['Authorization'],
    };

    try {
      const response = await this.sharedClient.request<T>(sharedConfig);
      return {
        status: response.status,
        data: response.data as T,
        headers: response.headers,
      };
    } catch (err: unknown) {
      const error = err as any;
      if (error instanceof HttpErrorImpl) {
        throw error;
      }

      if (error?.name === 'HttpError') {
        throw new HttpErrorImpl(error.status, error.message, error.responseBody);
      }

      if (error instanceof Error && error.name === 'AbortError') {
        throw new HttpErrorImpl(408, 'Request timeout');
      }

      throw new HttpErrorImpl(0, error?.message || 'Network error');
    }
  }

  get<T = any>(
    url: string,
    config: Omit<HttpRequestConfig, 'method' | 'url'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: HttpMethod.GET });
  }

  post<T = any>(
    url: string,
    body?: any,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: HttpMethod.POST, body });
  }

  put<T = any>(
    url: string,
    body?: any,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: HttpMethod.PUT, body });
  }

  delete<T = any>(
    url: string,
    config: Omit<HttpRequestConfig, 'method' | 'url'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: HttpMethod.DELETE });
  }

  patch<T = any>(
    url: string,
    body?: any,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return this.request<T>({ ...config, url, method: HttpMethod.PATCH, body });
  }

  setAccessToken(token: string): void {
    this.currentAccessToken = token;
  }

  clearAccessToken(): void {
    this.currentAccessToken = undefined;
  }

  setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }
}

// ============================================================
// HttpErrorImpl — 保持与 ai-client / creativity-client 的兼容
// ============================================================

/**
 * @deprecated 请直接使用 src/shared/services/http-client 中的 HttpError。
 */
export class HttpErrorImpl extends Error implements HttpError {
  public status: number;
  public details?: any;

  constructor(status: number, message: string, details?: any) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
    this.details = details;
  }
}
