// Auto-generated Authentication API Client

import { APIClient } from '../client';
import { BaseResponse, LoginRequest, RegisterRequest, AuthResponse, RefreshTokenRequest } from '../types';

export class AuthAPI {
  constructor(private client: APIClient) {}

  // 用户登录
  async login(credentials: LoginRequest): Promise<BaseResponse<AuthResponse>> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/login', credentials);
    return response.data;
  }

  // 用户注册
  async register(userData: RegisterRequest): Promise<BaseResponse<AuthResponse>> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/register', userData);
    return response.data;
  }

  // 刷新令牌
  async refreshToken(refreshData: RefreshTokenRequest): Promise<BaseResponse<AuthResponse>> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/refresh', refreshData);
    return response.data;
  }

  // 登出
  async logout(): Promise<BaseResponse<void>> {
    const response = await this.client.post<void>('/api/v1/auth/logout');
    return response.data;
  }

  // 验证令牌
  async verifyToken(): Promise<BaseResponse<boolean>> {
    const response = await this.client.get<boolean>('/api/v1/auth/verify');
    return response.data;
  }
}

// 导出实例创建函数
export function createAuthAPI(client: APIClient) {
  return new AuthAPI(client);
}