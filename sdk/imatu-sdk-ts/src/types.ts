export interface SDKConfig {
  baseURL: string;
  accessToken?: string;
  timeout?: number;
  headers?: Record<string, string>;
  onUnauthorized?: () => void;
  retries?: number;
  retryDelay?: number;
}

export interface APIError {
  code: string;
  message: string;
  details?: any;
  status?: number;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 基础响应类型
export interface BaseResponse<T = any> {
  success: boolean;
  data?: T;
  error?: APIError;
  timestamp: string;
}

// 认证相关类型
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// 用户相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role?: string;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
}

// AI相关类型
export interface CodeGenerationRequest {
  prompt: string;
  language?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface CodeGenerationResponse {
  code: string;
  explanation: string;
  language: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface TextGenerationRequest {
  prompt: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
}

export interface ImageGenerationRequest {
  prompt: string;
  model?: string;
  size?: string;
  quality?: string;
}

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  capabilities: string[];
  is_available: boolean;
}

// 课程相关类型
export interface Course {
  id: number;
  title: string;
  description: string;
  category: string;
  level: string;
  duration: number;
  instructor_id: number;
  thumbnail?: string;
  price?: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCourseRequest {
  title: string;
  description: string;
  category: string;
  level: string;
  duration: number;
  price?: number;
  thumbnail?: string;
}

export interface UpdateCourseRequest {
  title?: string;
  description?: string;
  category?: string;
  level?: string;
  duration?: number;
  price?: number;
  thumbnail?: string;
  is_published?: boolean;
}

export interface Chapter {
  id: number;
  course_id: number;
  title: string;
  order: number;
  content?: string;
  video_url?: string;
  duration: number;
  created_at: string;
}

// 分页参数
export interface PaginationParams {
  page?: number;
  limit?: number;
  skip?: number;
}

// 排序参数
export interface SortParams {
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 搜索参数
export interface SearchParams extends PaginationParams, SortParams {
  q?: string;
  filters?: Record<string, any>;
}

// HTTP客户端选项
export interface HttpClientOptions {
  timeout?: number;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
}

// SDK实例配置
export interface SDKInstance {
  auth: any;
  users: any;
  ai: any;
  courses: any;
  setAccessToken: (token: string) => void;
  clearAccessToken: () => void;
}