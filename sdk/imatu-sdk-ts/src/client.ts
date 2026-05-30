import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { SDKConfig, APIError, BaseResponse } from './types';

export class APIClient {
  private config: SDKConfig;
  private client: AxiosInstance;

  constructor(config: SDKConfig) {
    this.config = {
      retries: 3,
      retryDelay: 1000,
      ...config
    };
    
    this.client = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout || 10000,
      headers: {
        'Content-Type': 'application/json',
        ...this.config.headers
      }
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        if (this.config.accessToken) {
          config.headers = config.headers || {};
          config.headers.Authorization = `Bearer ${this.config.accessToken}`;
        }
        return config;
      },
      (error: any) => Promise.reject(this.handleError(error))
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: any) => {
        const handledError = this.handleError(error);
        
        // 处理401未授权错误
        if (handledError.status === 401) {
          this.handleUnauthorized();
        }
        
        return Promise.reject(handledError);
      }
    );
  }

  private handleError(error: AxiosError): APIError {
    let apiError: APIError = {
      code: 'UNKNOWN_ERROR',
      message: '发生未知错误',
      timestamp: new Date().toISOString()
    };

    if (error.response) {
      // 服务器返回错误响应
      const response = error.response;
      apiError.status = response.status;
      
      if (response.data && typeof response.data === 'object') {
        const errorData = response.data as any;
        apiError.code = errorData.code || `HTTP_${response.status}`;
        apiError.message = errorData.message || response.statusText;
        apiError.details = errorData.details;
      } else {
        apiError.code = `HTTP_${response.status}`;
        apiError.message = response.statusText;
      }
    } else if (error.request) {
      // 请求发出但没有收到响应
      apiError.code = 'NETWORK_ERROR';
      apiError.message = '网络连接失败，请检查网络连接';
    } else {
      // 请求配置出错
      apiError.code = 'REQUEST_ERROR';
      apiError.message = error.message || '请求配置错误';
    }

    return apiError;
  }

  private handleUnauthorized() {
    this.config.accessToken = undefined;
    if (this.config.onUnauthorized) {
      this.config.onUnauthorized();
    }
  }

  private async retryRequest<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    retries: number = this.config.retries || 3
  ): Promise<AxiosResponse<T>> {
    let lastError: any;
    
    for (let i = 0; i <= retries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        
        // 如果不是网络错误或者已经是最后一次重试，则不再重试
        if (i === retries || !(error instanceof Error && error.message.includes('Network Error'))) {
          throw lastError;
        }
        
        // 等待后重试
        await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
      }
    }
    
    throw lastError;
  }

  public setAccessToken(token: string) {
    this.config.accessToken = token;
  }

  public clearAccessToken() {
    this.config.accessToken = undefined;
  }

  public getConfig(): Readonly<SDKConfig> {
    return { ...this.config };
  }

  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<BaseResponse<T>>> {
    return this.retryRequest(() => this.client.get<BaseResponse<T>>(url, config));
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<BaseResponse<T>>> {
    return this.retryRequest(() => this.client.post<BaseResponse<T>>(url, data, config));
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<BaseResponse<T>>> {
    return this.retryRequest(() => this.client.put<BaseResponse<T>>(url, data, config));
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<BaseResponse<T>>> {
    return this.retryRequest(() => this.client.delete<BaseResponse<T>>(url, config));
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<BaseResponse<T>>> {
    return this.retryRequest(() => this.client.patch<BaseResponse<T>>(url, data, config));
  }
}