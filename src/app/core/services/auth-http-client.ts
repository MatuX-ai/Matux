/**
 * 认证HTTP客户端（已重构为使用统一HTTP客户端）
 * 保持向后兼容性的包装器
 */

import { HttpRequestConfig, HttpResponse, unifiedHttpClient } from './unified-http-client';

/**
 * 认证HTTP客户端 - 向后兼容的包装器
 * 实际委托给统一HTTP客户端处理
 */
export class AuthHttpClient {
  private static instance: AuthHttpClient;

  private constructor() {}

  static getInstance(): AuthHttpClient {
    if (!AuthHttpClient.instance) {
      AuthHttpClient.instance = new AuthHttpClient();
    }
    return AuthHttpClient.instance;
  }

  /**
   * 设置基础URL
   */
  setBaseUrl(url: string): void {
    unifiedHttpClient.setBaseUrl(url);
  }

  /**
   * 设置默认超时时间
   */
  setDefaultTimeout(timeout: number): void {
    unifiedHttpClient.setDefaultTimeout(timeout);
  }

  /**
   * 发送HTTP请求
   */
  async request<T = unknown>(config: HttpRequestConfig): Promise<HttpResponse<T>> {
    return unifiedHttpClient.request<T>(config);
  }

  /**
   * GET请求
   */
  get<T = unknown>(
    url: string,
    config: Omit<HttpRequestConfig, 'method' | 'url'> = {}
  ): Promise<HttpResponse<T>> {
    return unifiedHttpClient.get<T>(url, config);
  }

  /**
   * POST请求
   */
  post<T = unknown>(
    url: string,
    body?: unknown,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return unifiedHttpClient.post<T>(url, body, config);
  }

  /**
   * PUT请求
   */
  put<T = unknown>(
    url: string,
    body?: unknown,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return unifiedHttpClient.put<T>(url, body, config);
  }

  /**
   * DELETE请求
   */
  delete<T = unknown>(
    url: string,
    config: Omit<HttpRequestConfig, 'method' | 'url'> = {}
  ): Promise<HttpResponse<T>> {
    return unifiedHttpClient.delete<T>(url, config);
  }

  /**
   * PATCH请求
   */
  patch<T = unknown>(
    url: string,
    body?: unknown,
    config: Omit<HttpRequestConfig, 'method' | 'url' | 'body'> = {}
  ): Promise<HttpResponse<T>> {
    return unifiedHttpClient.patch<T>(url, body, config);
  }
}

/**
 * 带重试机制的HTTP请求函数（已整合到统一客户端中）
 * 保持向后兼容性
 */
async function requestWithRetry<T = unknown>(
  client: AuthHttpClient,
  config: HttpRequestConfig,
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<HttpResponse<T>> {
  // 统一客户端已经内置了重试机制，直接调用即可
  return client.request<T>({
    ...config,
    retries: maxRetries,
    retryDelay,
  });
}

/**
 * 判断是否应该重试（已整合到统一客户端中）
 */
function shouldRetry(_error: unknown, _retries: number, _maxRetries: number): boolean {
  // 此函数现在由统一客户端内部处理
  return false;
}

/**
 * 延迟函数（已整合到统一客户端中）
 */
function delay(_ms: number): Promise<void> {
  // 此函数现在由统一客户端内部处理
  return Promise.resolve();
}

// 导出实例
export const authHttpClient = AuthHttpClient.getInstance();

// 导出重试功能
export { delay, requestWithRetry, shouldRetry };
