// Auto-generated Users API Client

import { APIClient } from '../client';
import { BaseResponse, PaginatedResponse, User, CreateUserRequest, UpdateUserRequest, SearchParams } from '../types';

export class UsersAPI {
  constructor(private client: APIClient) {}

  // 获取用户列表
  async getUsers(params?: SearchParams): Promise<BaseResponse<PaginatedResponse<User>>> {
    const response = await this.client.get<PaginatedResponse<User>>('/api/v1/users', { params });
    return response.data;
  }

  // 获取单个用户
  async getUserById(id: string): Promise<BaseResponse<User>> {
    const response = await this.client.get<User>(`/api/v1/users/${id}`);
    return response.data;
  }

  // 创建用户
  async createUser(userData: CreateUserRequest): Promise<BaseResponse<User>> {
    const response = await this.client.post<User>('/api/v1/users', userData);
    return response.data;
  }

  // 更新用户
  async updateUser(id: string, userData: UpdateUserRequest): Promise<BaseResponse<User>> {
    const response = await this.client.put<User>(`/api/v1/users/${id}`, userData);
    return response.data;
  }

  // 删除用户
  async deleteUser(id: string): Promise<BaseResponse<void>> {
    const response = await this.client.delete<void>(`/api/v1/users/${id}`);
    return response.data;
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<BaseResponse<User>> {
    const response = await this.client.get<User>('/api/v1/users/me');
    return response.data;
  }

  // 搜索用户
  async searchUsers(query: string, params?: Omit<SearchParams, 'q'>): Promise<BaseResponse<PaginatedResponse<User>>> {
    const searchParams = { ...params, q: query };
    const response = await this.client.get<PaginatedResponse<User>>('/api/v1/users/search', { params: searchParams });
    return response.data;
  }
}

// 导出实例创建函数
export function createUsersAPI(client: APIClient) {
  return new UsersAPI(client);
}