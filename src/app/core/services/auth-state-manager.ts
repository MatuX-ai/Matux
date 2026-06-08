/**
 * 通用认证状态管理器
 * 可以在任何前端框架中使用
 *
 * @deprecated 此模块已被 auth.service.ts 替代。
 *             请使用 AuthService（基于 Angular 响应式模式）替代此模块。
 *             主要差异：
 *             1. AuthService 使用 RxJS Observable 而非回调模式
 *             2. AuthService 支持 sessionStorage/localStorage 双存储
 *             3. AuthService 提供更好的 TypeScript 类型安全
 *
 * @example
 * // 旧代码 (废弃)
 * import { AuthStateManager } from './auth-state-manager';
 * const auth = AuthStateManager.getInstance();
 *
 * // 新代码
 * import { AuthService } from './auth.service';
 * constructor(private authService: AuthService) {}
 * this.authService.isAuthenticated$.subscribe(...);
 */

/* eslint-disable @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
import { AuthResponse, OAuthProvider, OAuthState, User } from '../models/auth.models';

export type AuthStateChangeListener = (isAuthenticated: boolean, user: User | null) => void;

/**
 * 认证状态管理器
 * 管理用户的认证状态、令牌存储和事件监听
 */
export class AuthStateManager {
  private static instance: AuthStateManager;
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'user_data';

  private currentUser: User | null = null;
  private isAuthenticated = false;
  private listeners: AuthStateChangeListener[] = [];

  private constructor() {
    this.initializeAuthState();
  }

  /**
   * 获取单例实例
   */
  static getInstance(): AuthStateManager {
    if (!AuthStateManager.instance) {
      AuthStateManager.instance = new AuthStateManager();
    }
    return AuthStateManager.instance;
  }

  /**
   * 初始化认证状态
   */
  private initializeAuthState(): void {
    const storedUser = localStorage.getItem(this.USER_KEY);
    if (storedUser && this.hasToken()) {
      try {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        this.currentUser = JSON.parse(storedUser);
        this.isAuthenticated = true;
        this.notifyListeners();
      } catch (error) {
        this.clearAuthData();
      }
    }
  }

  /**
   * 检查是否存在访问令牌
   */
  private hasToken(): boolean {
    return !!localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * 存储认证数据
   */
  storeAuthData(response: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refreshToken);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    this.currentUser = response.user;
    this.isAuthenticated = true;
    this.notifyListeners();
  }

  /**
   * 清除认证数据
   */
  clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUser = null;
    this.isAuthenticated = false;
    this.notifyListeners();
  }

  /**
   * 添加状态变化监听器
   */
  addListener(listener: AuthStateChangeListener): void {
    this.listeners.push(listener);
  }

  /**
   * 移除状态变化监听器
   */
  removeListener(listener: AuthStateChangeListener): void {
    this.listeners = this.listeners.filter((l) => l !== listener);
  }

  /**
   * 通知所有监听器
   */
  private notifyListeners(): void {
    this.listeners.forEach((listener) => listener(this.isAuthenticated, this.currentUser));
  }

  /**
   * 获取当前用户
   */
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  /**
   * 检查是否已认证
   */
  isAuthenticatedUser(): boolean {
    return this.isAuthenticated;
  }

  /**
   * 获取访问令牌
   */
  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * 获取刷新令牌
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * 设置用户信息（用于手动更新用户数据）
   */
  setUser(user: User): void {
    this.currentUser = user;
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    this.notifyListeners();
  }
}

/**
 * OAuth状态管理器
 * 管理第三方认证的状态和流程
 */
export class OAuthManager {
  private static instance: OAuthManager;
  private readonly STATE_KEY = 'oauth_state';

  private constructor() {}

  static getInstance(): OAuthManager {
    if (!OAuthManager.instance) {
      OAuthManager.instance = new OAuthManager();
    }
    return OAuthManager.instance;
  }

  /**
   * 生成随机state参数
   */
  generateState(): string {
    return (
      Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    );
  }

  /**
   * 存储OAuth状态
   */
  storeOAuthState(state: OAuthState): void {
    sessionStorage.setItem(this.STATE_KEY, JSON.stringify(state));
  }

  /**
   * 获取存储的OAuth状态
   */
  getStoredOAuthState(): OAuthState | null {
    const state = sessionStorage.getItem(this.STATE_KEY);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return
    return state ? JSON.parse(state) : null;
  }

  /**
   * 清除OAuth状态
   */
  clearOAuthState(): void {
    sessionStorage.removeItem(this.STATE_KEY);
  }

  /**
   * 验证state参数
   */
  validateState(receivedState: string): boolean {
    const storedState = this.getStoredOAuthState();
    return !!(storedState && storedState.state === receivedState);
  }

  /**
   * 获取 GitHub 客户端 ID
   * 在实际应用中应从环境变量获取
   */
  getGithubClientId(): string {
    // 这里应该从环境配置中获取
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return
    return (
      (typeof window !== 'undefined'
        ? (window as unknown as Record<string, string | undefined>)['NG_APP_GITHUB_CLIENT_ID']
        : undefined) ?? 'your_github_client_id'
    );
  }

  /**
   * 获取 Google 客户端 ID
   */
  getGoogleClientId(): string {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return
    return (
      (typeof window !== 'undefined'
        ? (window as unknown as Record<string, string | undefined>)['NG_APP_GOOGLE_CLIENT_ID']
        : undefined) ?? 'your_google_client_id'
    );
  }

  /**
   * 获取微信 AppID
   */
  getWeChatAppId(): string {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return
    return (
      (typeof window !== 'undefined'
        ? (window as unknown as Record<string, string | undefined>)['NG_APP_WECHAT_APP_ID']
        : undefined) ?? 'your_wechat_app_id'
    );
  }

  /**
   * 获取 QQ AppID
   */
  getQQAppId(): string {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return
    return (
      (typeof window !== 'undefined'
        ? (window as unknown as Record<string, string | undefined>)['NG_APP_QQ_APP_ID']
        : undefined) ?? 'your_qq_app_id'
    );
  }

  /**
   * 构建OAuth授权URL
   */
  buildAuthorizationUrl(
    provider: OAuthProvider,
    options: {
      redirectUri: string;
      scopes?: string[];
      state?: string;
      [key: string]: string | string[] | undefined; // 支持额外参数
    }
  ): string {
    const { redirectUri, scopes = [], state = this.generateState(), ...extraParams } = options;

    switch (provider) {
      case 'github':
        return (
          `https://github.com/login/oauth/authorize?` +
          `client_id=${this.getGithubClientId()}&` +
          `redirect_uri=${encodeURIComponent(redirectUri)}&` +
          `state=${state}&` +
          `scope=${scopes.join(' ') || 'user:email'}`
        );

      case 'google':
        return (
          `https://accounts.google.com/o/oauth2/v2/auth?` +
          `client_id=${this.getGoogleClientId()}&` +
          `redirect_uri=${encodeURIComponent(redirectUri)}&` +
          `response_type=code&` +
          `scope=${encodeURIComponent(scopes.join(' ') || 'openid email profile')}&` +
          `state=${state}`
        );

      case 'wechat':
        // 微信扫码登录
        return (
          `https://open.weixin.qq.com/connect/qrconnect?` +
          `appid=${this.getWeChatAppId()}&` +
          `redirect_uri=${encodeURIComponent(redirectUri)}&` +
          `response_type=code&` +
          `scope=${String(extraParams['scope'] ?? 'snsapi_login')}&` +
          `state=${state}#wechat_redirect`
        );

      case 'qq':
        // QQ互联登录
        return (
          `https://graph.qq.com/oauth2.0/authorize?` +
          `client_id=${this.getQQAppId()}&` +
          `redirect_uri=${encodeURIComponent(redirectUri)}&` +
          `response_type=code&` +
          `scope=${String(extraParams['scope'] ?? 'get_user_info')}&` +
          `state=${state}`
        );

      default:
        throw new Error(`Unsupported OAuth provider: ${provider}`);
    }
  }
}

/**
 * 令牌管理器
 * 处理JWT令牌的解析、验证和刷新
 */
export class TokenManager {
  private static instance: TokenManager;
  private refreshPromise: Promise<AuthResponse> | null = null;

  private constructor() {}

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  /**
   * 解析 JWT 令牌
   */
  parseJwt(token: string): unknown {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => `%${c.charCodeAt(0).toString(16).padStart(2, '0')}`)
          .join('')
      );

      return JSON.parse(jsonPayload);
    } catch (error) {
      return null;
    }
  }

  /**
   * 检查令牌是否即将过期
   */
  isTokenExpiringSoon(token: string, thresholdMinutes: number = 5): boolean {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const payload = this.parseJwt(token) as Record<string, unknown>;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    if (!payload?.['exp']) return true;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    const expirationTime = (payload['exp'] as number) * 1000; // JWT exp 是秒数
    const currentTime = Date.now();
    const thresholdMs = thresholdMinutes * 60 * 1000;

    return expirationTime - currentTime < thresholdMs;
  }

  /**
   * 检查令牌是否已过期
   */
  isTokenExpired(token: string): boolean {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const payload = this.parseJwt(token) as Record<string, unknown>;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    if (!payload?.['exp']) return true;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    const expirationTime = (payload['exp'] as number) * 1000;
    const currentTime = Date.now();

    return currentTime >= expirationTime;
  }

  /**
   * 获取令牌剩余有效时间（毫秒）
   */
  getTokenRemainingTime(token: string): number {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    const payload = this.parseJwt(token) as Record<string, unknown>;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    if (!payload?.['exp']) return 0;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    const expirationTime = (payload['exp'] as number) * 1000;
    const currentTime = Date.now();

    return Math.max(0, expirationTime - currentTime);
  }

  /**
   * 刷新令牌（防抖处理）
   */
  async refreshAuthToken(refreshFunction: () => Promise<AuthResponse>): Promise<AuthResponse> {
    // 如果已经有刷新请求在进行中，返回同一个Promise
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    try {
      this.refreshPromise = refreshFunction();
      const result = await this.refreshPromise;
      this.refreshPromise = null;
      return result;
    } catch (error) {
      this.refreshPromise = null;
      throw error;
    }
  }
}

// 导出单例实例
export const authStateManager = AuthStateManager.getInstance();
export const oauthManager = OAuthManager.getInstance();
export const tokenManager = TokenManager.getInstance();
