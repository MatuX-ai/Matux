/**
 * 主认证服务
 * 整合所有认证功能，提供统一的API接口
 */

import {
  AuthResponse,
  LoginRequest,
  OAuthState,
  RegisterRequest,
  User,
} from '../models/auth.models';

import { authHttpClient, requestWithRetry } from './auth-http-client';
import { authStateManager, oauthManager, tokenManager } from './auth-state-manager';

export type AuthStateChangeListener = (isAuthenticated: boolean, user: User | null) => void;

/**
 * 认证服务配置
 */
export interface AuthServiceConfig {
  apiUrl?: string;
  timeout?: number;
  autoRefreshThreshold?: number; // 令牌自动刷新阈值（分钟）
  githubClientId?: string;
  googleClientId?: string;
}

/**
 * 主认证服务类
 */
export class AuthService {
  private config: Required<AuthServiceConfig>;
  private isInitialized = false;

  constructor(config: AuthServiceConfig = {}) {
    this.config = {
      apiUrl: '/api',
      timeout: 10000,
      autoRefreshThreshold: 5,
      githubClientId: '',
      googleClientId: '',
      ...config,
    };

    this.initialize();
  }

  /**
   * 初始化服务
   */
  private initialize(): void {
    if (this.isInitialized) return;

    // 配置HTTP客户端
    authHttpClient.setBaseUrl(this.config.apiUrl);
    authHttpClient.setDefaultTimeout(this.config.timeout);

    // 令牌管理器使用默认阈值

    this.isInitialized = true;
  }

  /**
   * 用户注册
   */
  async signUp(userData: RegisterRequest): Promise<AuthResponse> {
    try {
      const response = await authHttpClient.post<AuthResponse>('/auth/signup', userData);
      authStateManager.storeAuthData(response.data);
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 用户登录
   */
  async signIn(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await authHttpClient.post<AuthResponse>('/auth/signin', credentials);
      authStateManager.storeAuthData(response.data);
      return response.data;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * GitHub OAuth登录
   */
  signInWithGitHub(
    options: {
      redirectUri?: string;
      scopes?: string[];
      state?: string;
    } = {}
  ): void {
    const {
      redirectUri = `${window.location.origin}/auth/callback`,
      scopes = ['user:email'],
      state = oauthManager.generateState(),
    } = options;

    try {
      // 存储OAuth状态
      const oauthState: OAuthState = {
        provider: 'github',
        state,
        redirectUrl: window.location.pathname,
      };
      oauthManager.storeOAuthState(oauthState);

      // 构建授权URL
      const authUrl = oauthManager.buildAuthorizationUrl('github', {
        redirectUri,
        scopes,
        state,
      });

      // 跳转到授权页面
      window.location.href = authUrl;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * Google OAuth登录
   */
  signInWithGoogle(
    options: {
      redirectUri?: string;
      scopes?: string[];
      state?: string;
    } = {}
  ): void {
    const {
      redirectUri = `${window.location.origin}/auth/callback`,
      scopes = ['openid', 'email', 'profile'],
      state = oauthManager.generateState(),
    } = options;

    try {
      // 存储OAuth状态
      const oauthState: OAuthState = {
        provider: 'google',
        state,
        redirectUrl: window.location.pathname,
      };
      oauthManager.storeOAuthState(oauthState);

      // 构建授权URL
      const authUrl = oauthManager.buildAuthorizationUrl('google', {
        redirectUri,
        scopes,
        state,
      });

      // 跳转到授权页面
      window.location.href = authUrl;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 微信OAuth登录
   */
  signInWithWeChat(
    options: {
      redirectUri?: string;
      scope?: 'snsapi_login' | 'snsapi_userinfo';
      state?: string;
    } = {}
  ): void {
    const {
      redirectUri = `${window.location.origin}/auth/callback`,
      scope = 'snsapi_login',
      state = oauthManager.generateState(),
    } = options;

    try {
      // 存储OAuth状态
      const oauthState: OAuthState = {
        provider: 'wechat',
        state,
        redirectUrl: window.location.pathname,
      };
      oauthManager.storeOAuthState(oauthState);

      // 构建授权URL
      const authUrl = oauthManager.buildAuthorizationUrl('wechat', {
        redirectUri,
        scope,
        state,
      });

      // 跳转到授权页面
      window.location.href = authUrl;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * QQ OAuth登录
   */
  signInWithQQ(
    options: {
      redirectUri?: string;
      scope?: string;
      state?: string;
    } = {}
  ): void {
    const {
      redirectUri = `${window.location.origin}/auth/callback`,
      scope = 'get_user_info',
      state = oauthManager.generateState(),
    } = options;

    try {
      // 存储OAuth状态
      const oauthState: OAuthState = {
        provider: 'qq',
        state,
        redirectUrl: window.location.pathname,
      };
      oauthManager.storeOAuthState(oauthState);

      // 构建授权URL
      const authUrl = oauthManager.buildAuthorizationUrl('qq', {
        redirectUri,
        scope,
        state,
      });

      // 跳转到授权页面
      window.location.href = authUrl;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 处理OAuth回调
   */
  async handleOAuthCallback(code: string, state: string): Promise<AuthResponse> {
    try {
      // 验证state参数
      if (!oauthManager.validateState(state)) {
        throw new Error('Invalid OAuth state parameter');
      }

      const oauthState = oauthManager.getStoredOAuthState();
      if (!oauthState) {
        throw new Error('No OAuth state found');
      }

      // 根据提供商处理回调
      let response: AuthResponse;
      switch (oauthState.provider) {
        case 'github':
          response = await this.handleGithubCallback(code, state);
          break;
        case 'google':
          response = await this.handleGoogleCallback(code, state);
          break;
        case 'wechat':
          response = await this.handleWeChatCallback(code, state);
          break;
        case 'qq':
          response = await this.handleQQCallback(code, state);
          break;
        default:
          throw new Error(`Unsupported OAuth provider: ${oauthState.provider}`);
      }

      // 清除临时状态
      oauthManager.clearOAuthState();

      // 存储认证数据
      authStateManager.storeAuthData(response);

      return response;
    } catch (error) {
      oauthManager.clearOAuthState();
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 处理GitHub回调
   */
  private async handleGithubCallback(code: string, state: string): Promise<AuthResponse> {
    const response = await authHttpClient.post<AuthResponse>('/auth/github/callback', {
      code,
      state,
    });
    return response.data;
  }

  /**
   * 处理Google回调
   */
  private async handleGoogleCallback(code: string, state: string): Promise<AuthResponse> {
    const response = await authHttpClient.post<AuthResponse>('/auth/google/callback', {
      code,
      state,
    });
    return response.data;
  }

  /**
   * 处理微信回调
   */
  private async handleWeChatCallback(code: string, state: string): Promise<AuthResponse> {
    const response = await authHttpClient.post<AuthResponse>('/auth/wechat/callback', {
      code,
      state,
    });
    return response.data;
  }

  /**
   * 处理QQ回调
   */
  private async handleQQCallback(code: string, state: string): Promise<AuthResponse> {
    const response = await authHttpClient.post<AuthResponse>('/auth/qq/callback', {
      code,
      state,
    });
    return response.data;
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = authStateManager.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await authHttpClient.post<AuthResponse>('/auth/refresh', {
        refreshToken,
      });
      authStateManager.storeAuthData(response.data);
      return response.data;
    } catch (error) {
      // 刷新失败则登出
      void this.logout();
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    const refreshToken = authStateManager.getRefreshToken();

    try {
      // 通知服务器撤销令牌
      if (refreshToken) {
        await authHttpClient.post('/auth/logout', { refreshToken });
      }
    } catch (error) {
      // 即使服务器调用失败也要清除本地数据
    } finally {
      // 清除本地认证数据
      authStateManager.clearAuthData();

      // 触发登出事件
      this.dispatchLogoutEvent();
    }
  }

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): User | null {
    return authStateManager.getCurrentUser();
  }

  /**
   * 检查用户是否已认证
   */
  isAuthenticated(): boolean {
    return authStateManager.isAuthenticatedUser();
  }

  /**
   * 获取访问令牌
   */
  getAccessToken(): string | null {
    return authStateManager.getAccessToken();
  }

  /**
   * 添加认证状态监听器
   */
  addAuthStateListener(listener: AuthStateChangeListener): void {
    authStateManager.addListener(listener);
  }

  /**
   * 移除认证状态监听器
   */
  removeAuthStateListener(listener: AuthStateChangeListener): void {
    authStateManager.removeListener(listener);
  }

  /**
   * 更新用户信息
   */
  async updateUser(userData: Partial<User>): Promise<User> {
    try {
      const response = await authHttpClient.put<User>('/auth/user', userData);
      const updatedUser = response.data;

      // 更新本地用户数据
      const currentUser = this.getCurrentUser();
      if (currentUser) {
        const newUser = { ...currentUser, ...updatedUser };
        authStateManager.setUser(newUser);
      }

      return updatedUser;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 修改密码
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      await authHttpClient.post('/auth/change-password', {
        currentPassword,
        newPassword,
      });
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 请求密码重置
   */
  async requestPasswordReset(email: string): Promise<void> {
    try {
      await authHttpClient.post('/auth/forgot-password', { email });
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 重置密码
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    try {
      await authHttpClient.post('/auth/reset-password', {
        token,
        newPassword,
      });
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 验证邮箱
   */
  async verifyEmail(token: string): Promise<void> {
    try {
      await authHttpClient.post('/auth/verify-email', { token });
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 重新发送验证邮件
   */
  async resendVerificationEmail(): Promise<void> {
    try {
      await authHttpClient.post('/auth/resend-verification');
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 获取用户权限列表
   */
  async getUserPermissions(): Promise<string[]> {
    try {
      const response = await authHttpClient.get<{ permissions: string[] }>('/auth/permissions');
      return response.data.permissions;
    } catch (error) {
      this.handleError(error);
      throw error;
    }
  }

  /**
   * 检查用户是否有特定权限
   */
  async hasPermission(permission: string): Promise<boolean> {
    try {
      const permissions = await this.getUserPermissions();
      return permissions.includes(permission);
    } catch (error) {
      this.handleError(error);
      return false;
    }
  }

  /**
   * 统一错误处理
   */
  private handleError(error: unknown): void {
    // 可以在这里添加全局错误处理逻辑
    // 比如显示通知、记录日志等

    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('auth:error', {
          detail: { error },
        })
      );
    }
  }

  /**
   * 触发登出事件
   */
  private dispatchLogoutEvent(): void {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
  }

  /**
   * 获取服务配置
   */
  getConfig(): Required<AuthServiceConfig> {
    return { ...this.config };
  }

  /**
   * 更新服务配置
   */
  updateConfig(newConfig: Partial<AuthServiceConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.initialize();
  }
}

// 创建默认实例
let defaultAuthService: AuthService | null = null;

/**
 * 获取默认认证服务实例
 */
export function getDefaultAuthService(): AuthService {
  if (!defaultAuthService) {
    defaultAuthService = new AuthService();
  }
  return defaultAuthService;
}

/**
 * 设置默认认证服务配置
 */
export function configureAuthService(config: AuthServiceConfig): void {
  if (defaultAuthService) {
    defaultAuthService.updateConfig(config);
  } else {
    defaultAuthService = new AuthService(config);
  }
}

// 导出主要类型和函数
export { authHttpClient, authStateManager, oauthManager, requestWithRetry, tokenManager };
