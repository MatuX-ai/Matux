/**
 * 共享 HTTP 客户端
 * 基于原生 fetch API，框架无关，供多端复用
 */

/**
 * HTTP 请求方法枚举
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
  url: string;
  method: HttpMethod | string;
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
 * HTTP 错误类
 */
export class HttpError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string,
    public responseBody?: unknown
  ) {
    super(message);
    this.name = 'HttpError';
  }
}

/**
 * HTTP 请求拦截器
 */
export interface HttpInterceptor {
  request?: (config: HttpRequestConfig) => HttpRequestConfig | Promise<HttpRequestConfig>;
  response?: (response: HttpResponse) => HttpResponse | Promise<HttpResponse>;
  error?: (error: HttpError) => HttpError | Promise<HttpError>;
}

/**
 * Token 提供器
 */
export interface TokenProvider {
  getToken: () => string | null;
  onUnauthorized?: () => void;
}

/**
 * 默认超时时间（毫秒）
 */
const DEFAULT_TIMEOUT = 30000;

/**
 * 默认重试次数
 */
const DEFAULT_RETRIES = 0;

/**
 * 默认重试延迟（毫秒）
 */
const DEFAULT_RETRY_DELAY = 1000;

/**
 * 创建请求头
 */
function createHeaders(
  config: HttpRequestConfig,
  tokenProvider?: TokenProvider
): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...config.headers,
  };

  if (!config.skipAuth && tokenProvider) {
    const token = tokenProvider.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * 执行 HTTP 请求
 */
async function executeRequest(
  config: HttpRequestConfig,
  tokenProvider?: TokenProvider,
  interceptors: HttpInterceptor[] = []
): Promise<HttpResponse> {
  const { url, body, timeout = DEFAULT_TIMEOUT } = config;

  const headers = createHeaders(config, tokenProvider);

  // 应用请求拦截器
  let processedConfig: HttpRequestConfig = { ...config, headers };
  for (const interceptor of interceptors) {
    if (interceptor.request) {
      processedConfig = await interceptor.request(processedConfig);
    }
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method: processedConfig.method,
      headers: processedConfig.headers as Record<string, string>,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    let responseData: unknown;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      responseData = await response.text();
    }

    const httpResponse: HttpResponse = {
      data: responseData,
      status: response.status,
      headers: (() => {
        const h: Record<string, string> = {};
        response.headers.forEach((value: string, key: string) => {
          h[key] = value;
        });
        return h;
      })(),
    };

    // 应用响应拦截器
    let processedResponse = httpResponse;
    for (const interceptor of interceptors) {
      if (interceptor.response) {
        processedResponse = await interceptor.response(processedResponse);
      }
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      if (typeof responseData === 'object' && responseData !== null) {
        const errorObj = responseData as Record<string, unknown>;
        errorMessage =
          (errorObj['message'] as string) || (errorObj['error'] as string) || errorMessage;
      }

      const httpError = new HttpError(
        errorMessage,
        response.status,
        response.statusText,
        responseData
      );

      if (response.status === 401 && tokenProvider?.onUnauthorized) {
        tokenProvider.onUnauthorized();
      }

      // 应用错误拦截器
      let processedError: HttpError = httpError;
      for (const interceptor of interceptors) {
        if (interceptor.error) {
          processedError = await interceptor.error(processedError);
        }
      }

      throw processedError;
    }

    return processedResponse;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof HttpError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new HttpError('请求超时', 408, 'Request Timeout');
    }

    throw new HttpError(
      error instanceof Error ? error.message : '网络请求失败',
      0,
      'Network Error'
    );
  }
}

/**
 * 带重试的请求执行
 */
async function executeWithRetry(
  config: HttpRequestConfig,
  tokenProvider?: TokenProvider,
  interceptors: HttpInterceptor[] = []
): Promise<HttpResponse> {
  const retries = config.retries ?? DEFAULT_RETRIES;
  const retryDelay = config.retryDelay ?? DEFAULT_RETRY_DELAY;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await executeRequest(config, tokenProvider, interceptors);
    } catch (error) {
      lastError = error as Error;
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
      }
    }
  }

  throw lastError;
}

/**
 * HTTP 客户端类
 */
export class HttpClient {
  private tokenProvider?: TokenProvider;
  private interceptors: HttpInterceptor[] = [];

  constructor(options?: { tokenProvider?: TokenProvider; interceptors?: HttpInterceptor[] }) {
    this.tokenProvider = options?.tokenProvider;
    this.interceptors = options?.interceptors || [];
  }

  setTokenProvider(provider: TokenProvider): void {
    this.tokenProvider = provider;
  }

  addInterceptor(interceptor: HttpInterceptor): void {
    this.interceptors.push(interceptor);
  }

  async request<T = unknown>(config: HttpRequestConfig): Promise<HttpResponse<T>> {
    const response = await executeWithRetry(config, this.tokenProvider, this.interceptors);
    return response as HttpResponse<T>;
  }

  async get<T = unknown>(
    url: string,
    config?: Partial<HttpRequestConfig>
  ): Promise<HttpResponse<T>> {
    return this.request<T>({
      url,
      method: HttpMethod.GET,
      ...config,
    });
  }

  async post<T = unknown>(
    url: string,
    body?: unknown,
    config?: Partial<HttpRequestConfig>
  ): Promise<HttpResponse<T>> {
    return this.request<T>({
      url,
      method: HttpMethod.POST,
      body,
      ...config,
    });
  }

  async put<T = unknown>(
    url: string,
    body?: unknown,
    config?: Partial<HttpRequestConfig>
  ): Promise<HttpResponse<T>> {
    return this.request<T>({
      url,
      method: HttpMethod.PUT,
      body,
      ...config,
    });
  }

  async patch<T = unknown>(
    url: string,
    body?: unknown,
    config?: Partial<HttpRequestConfig>
  ): Promise<HttpResponse<T>> {
    return this.request<T>({
      url,
      method: HttpMethod.PATCH,
      body,
      ...config,
    });
  }

  async delete<T = unknown>(
    url: string,
    config?: Partial<HttpRequestConfig>
  ): Promise<HttpResponse<T>> {
    return this.request<T>({
      url,
      method: HttpMethod.DELETE,
      ...config,
    });
  }
}

/** 创建默认 HTTP 客户端实例 */
export function createHttpClient(options?: {
  tokenProvider?: TokenProvider;
  interceptors?: HttpInterceptor[];
}): HttpClient {
  return new HttpClient(options);
}

/** 默认导出 */
export default HttpClient;
