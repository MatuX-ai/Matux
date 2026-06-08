import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, of, throwError, firstValueFrom } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { ROUTES } from '../../routes.const';
import {
  AuthResponse,
  BindChildRequest,
  LoginRequest,
  OAuthState,
  PhoneLoginRequest,
  PhoneRegisterRequest,
  RegisterRequest,
  UnifiedTokenResponse,
  User,
} from '../models/auth.models';

import { ElectronService } from './electron.service';

/**
 * 用户认证服务
 * 处理用户登录、注册、OAuth认证、离线登录等核心功能
 *
 * 桌面端适配：
 * - OAuth 使用系统默认浏览器完成授权
 * - 支持「记住我」持久化登录态
 * - 离线登录：LocalStorage 缓存 Token
 */

/**
 * 环境配置扩展接口（定义 OAuth 配置结构）
 */
interface EnvironmentWithOAuth {
  oauth?: {
    github?: { clientId?: string };
    google?: { clientId?: string };
    wechat?: { appId?: string };
    qq?: { clientId?: string };
  };
  wsUrl?: string;
  production?: boolean;
  apiUrl?: string;
}

/**
 * 获取安全的环境配置
 */
function getSafeEnvironment(): EnvironmentWithOAuth {
  return environment as EnvironmentWithOAuth;
}

/**
 * 生成密码学安全的随机字符串
 * 使用 Web Crypto API 生成符合 RFC 4122 的 UUID v4
 */
function generateSecureState(): string {
  // 使用 crypto.getRandomValues 生成密码学安全的随机数
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  // RFC 4122 UUID v4 格式
  array[6] = (array[6] & 0x0f) | 0x40;
  array[8] = (array[8] & 0x3f) | 0x80;
  const hex = Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-4${hex.slice(13, 16)}-a${hex.slice(17, 20)}-${hex.slice(20, 32)}`;
}

/**
 * 验证 state 参数是否为有效的 UUID v4 格式
 */
function isValidStateFormat(state: string): boolean {
  const uuidV4Pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidV4Pattern.test(state);
}
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  // 获取 API Base URL（支持环境变量覆盖）
  private getApiBaseUrl(): string {
    // 使用安全的环境配置访问
    const env = getSafeEnvironment();

    // 优先使用 environment.apiUrl（已配置）
    const baseUrl = env.apiUrl;
    if (!baseUrl) {
      if (env.production) {
        console.error('[Auth] 生产环境未配置 apiUrl，请检查 environment.ts');
      }
      // 开发环境默认使用 localhost:8000
      return 'http://localhost:8000';
    }
    // 移除末尾斜杠，统一处理
    return baseUrl.replace(/\/$/, '');
  }

  // API 端点（动态获取 Base URL）
  private get API_BASE_URL(): string {
    return `${this.getApiBaseUrl()}/api/v1/auth`;
  }
  private get UNIFIED_AUTH_URL(): string {
    return `${this.getApiBaseUrl()}/api/v1/unified-auth`;
  }
  private get OAUTH_API_URL(): string {
    return `${this.getApiBaseUrl()}/api/v1/oauth`;
  }
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'user_data';
  private readonly REMEMBER_ME_KEY = 'remember_me';
  private readonly OFFLINE_CREDENTIALS_KEY = 'offline_credentials';

  // 用户认证状态
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  // 认证状态
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  // 是否"记住我"模式
  private rememberMeSubject = new BehaviorSubject<boolean>(this.isRememberMe());
  public rememberMe$ = this.rememberMeSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router,
    private electronService?: ElectronService
  ) {
    this.initializeAuthState();
  }

  /**
   * 是否在 Electron 桌面环境中运行
   */
  private get isElectron(): boolean {
    return this.electronService?.isElectron ?? false;
  }

  /**
   * 初始化认证状态
   */
  private initializeAuthState(): void {
    // 检查是否"记住我"模式
    if (this.isRememberMe()) {
      const storedUser = localStorage.getItem(this.USER_KEY);
      if (storedUser && this.hasToken()) {
        try {
          const user = JSON.parse(storedUser) as User;
          this.currentUserSubject.next(user);
          this.isAuthenticatedSubject.next(true);
        } catch {
          this.logout();
        }
      }
    } else {
      // 非记住我模式，检查会话级 token
      const sessionToken = sessionStorage.getItem(this.TOKEN_KEY);
      if (sessionToken) {
        const storedUser = sessionStorage.getItem(this.USER_KEY);
        if (storedUser) {
          try {
            const user = JSON.parse(storedUser) as User;
            this.currentUserSubject.next(user);
            this.isAuthenticatedSubject.next(true);
          } catch {
            this.clearSessionAuth();
          }
        }
      }
    }
  }

  /**
   * 检查是否存在访问令牌
   */
  private hasToken(): boolean {
    return !!(localStorage.getItem(this.TOKEN_KEY) ?? sessionStorage.getItem(this.TOKEN_KEY));
  }

  /**
   * 测试/调试用：手动写入 access_token 并触发 isAuthenticated$ = true
   * 正常登录流程应使用 signIn()，本方法仅用于绕过前端 signIn 直接用后端 token 的场景
   * @deprecated 仅供开发环境使用，已添加生产环境防护
   * @internal 开发/演示时使用，生产环境调用会被静默忽略
   * @param token 要设置的访问令牌
   * @param user 可选的预置用户信息，不提供则通过 /me 端点获取
   */
  setAccessTokenForTesting(token: string, user?: Partial<User>): void {
    // 双重防护：检查编译时常量 + 运行时标志
    if (!this.isDevelopmentEnvironment()) {
      // 生产环境静默失败，不输出日志避免信息泄露
      console.debug('[Auth] 拒绝在非开发环境设置测试Token');
      return;
    }

    // JWT Token 格式校验：header.payload.signature
    // signature部分可能使用标准Base64（包含+/）或Base64URL（不含+/但含_-）
    if (!token || !/^[A-Za-z0-9_+/=-]+\.[A-Za-z0-9_+/=-]+\.[A-Za-z0-9_+/=-]+$/.test(token)) {
      console.warn('[Auth] 无效的Token格式');
      return;
    }

    sessionStorage.setItem(this.TOKEN_KEY, token);

    // 如果提供了用户信息，直接使用；否则尝试获取
    if (user) {
      const fullUser: User = {
        id: user.id ?? 'test-user',
        username: user.username ?? '测试用户',
        email: user.email ?? '',
        userType: user.userType ?? 'student',
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      this.currentUserSubject.next(fullUser);
      sessionStorage.setItem(this.USER_KEY, JSON.stringify(fullUser));
    }

    this.isAuthenticatedSubject.next(true);
  }

  /**
   * 检查当前是否为开发环境
   * 同时检查 Angular environment 配置
   */
  private isDevelopmentEnvironment(): boolean {
    // 检查 environment 中的生产标志
    const isProd = (environment as { production?: boolean }).production;
    if (isProd) return false;

    // 检查环境变量
    const env = (window as unknown as { __env__?: { envName?: string } }).__env__;
    if (env?.envName === 'production') return false;

    // 检查 localhost
    return window.location.hostname === 'localhost' ||
           window.location.hostname === '127.0.0.1';
  }

  // Token 存储策略说明：
  // 短期：Token 存 sessionStorage（页面关闭即清除），降低 XSS 攻击面
  // 长期：后端需支持 httpOnly Cookie，参考 OWASP 存储指南
  // 注意："记住我"存 localStorage 是为了跨会话恢复，但 Token 有效期应限制（如 7 天）
  private readonly TOKEN_EXPIRY_KEY = 'token_expiry';
  private readonly DEFAULT_TOKEN_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 天

  /**
   * 检查 Token 是否过期
   */
  private isTokenExpired(): boolean {
    const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY) ?? sessionStorage.getItem(this.TOKEN_EXPIRY_KEY);
    if (!expiry) return false; // 无过期时间，信任 Token
    
    // 【安全】parseInt返回NaN时视为过期
    const expiryTime = parseInt(expiry, 10);
    if (isNaN(expiryTime)) {
      console.warn('[Auth] Token过期时间格式无效，清除认证数据');
      this.clearAuthData();
      return true;
    }
    return Date.now() > expiryTime;
  }

  /**
   * 存储 Token 到期时间
   */
  private setTokenExpiry(store: Storage): void {
    const expiry = Date.now() + this.DEFAULT_TOKEN_TTL_MS;
    store.setItem(this.TOKEN_EXPIRY_KEY, expiry.toString());
  }

  /**
   * 获取当前用户信息（用于 Electron 桌面端一键登录后）
   */
  public async fetchCurrentUser(): Promise<User | null> {
    try {
      // Token 过期检查
      if (this.isTokenExpired()) {
        console.warn('[Auth] Token 已过期，需要重新登录');
        this.clearAuthData();
        return null;
      }

      const headers = this.getAuthHeaders();
      const response = await firstValueFrom(
        this.http.get<User>(`${this.API_BASE_URL}/me`, { headers })
      );
      if (response) {
        this.currentUserSubject.next(response);
        this.getStore().setItem(this.USER_KEY, JSON.stringify(response));
      }
      return response;
    } catch (error) {
      console.error('[Auth] 获取用户信息失败:', error);
      // 区分不同错误类型
      const errorObj = error as { status?: number };
      if (errorObj.status === 401) {
        // Token 无效或过期，清理认证数据
        console.warn('[Auth] 认证过期，清理本地数据');
        this.clearAuthData();
      }
      return null;
    }
  }

  /**
   * 获取当前有效的 Token
   */
  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY) ?? sessionStorage.getItem(this.TOKEN_KEY) ?? null;
  }

  /**
   * 获取HTTP头部认证信息
   * 【安全】token为null时不设置Authorization头
   */
  private getAuthHeaders(): HttpHeaders {
    const token = this.getAccessToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return new HttpHeaders(headers);
  }

  /**
   * 获取存储后端（记住我 → localStorage，否则 → sessionStorage）
   */
  private getStore(): Storage {
    return this.rememberMeSubject.value ? localStorage : sessionStorage;
  }

  /**
   * 存储认证数据
   * @note Token 存储使用双重策略：
   * 1. 主 Token 存 sessionStorage（安全，会话结束即清除）
   * 2. "记住我"模式下 Token 同步到 localStorage + 设置过期时间
   */
  private storeAuthData(response: AuthResponse): void {
    const isRememberMe = this.rememberMeSubject.value;
    
    // 主存储：sessionStorage（安全优先）
    sessionStorage.setItem(this.TOKEN_KEY, response.accessToken);
    sessionStorage.setItem(this.REFRESH_TOKEN_KEY, response.refreshToken);
    sessionStorage.setItem(this.USER_KEY, JSON.stringify(response.user));

    // "记住我"模式：同步到 localStorage + 设置过期时间
    if (isRememberMe) {
      localStorage.setItem(this.TOKEN_KEY, response.accessToken);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refreshToken);
      localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
      this.setTokenExpiry(localStorage);
    } else {
      // 非记住我模式，清除 localStorage 中的旧 Token
      localStorage.removeItem(this.TOKEN_KEY);
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
      localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    }

    this.currentUserSubject.next(response.user);
    this.isAuthenticatedSubject.next(true);
  }

  /**
   * 清除认证数据
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
  }

  /**
   * 清除会话级认证
   */
  private clearSessionAuth(): void {
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
  }

  /**
   * 设置"记住我"
   */
  setRememberMe(remember: boolean): void {
    localStorage.setItem(this.REMEMBER_ME_KEY, JSON.stringify(remember));
    this.rememberMeSubject.next(remember);
  }

  /**
   * 是否"记住我"
   */
  isRememberMe(): boolean {
    try {
      const stored = localStorage.getItem(this.REMEMBER_ME_KEY);
      return stored ? Boolean(JSON.parse(stored)) : false;
    } catch {
      return false;
    }
  }

  /**
   * 用户注册
   */
  signUp(userData: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.API_BASE_URL}/signup`, userData).pipe(
      tap((response) => this.storeAuthData(response)),
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * 用户登录
   */
  signIn(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.API_BASE_URL}/signin`, credentials).pipe(
      tap((response) => {
        this.storeAuthData(response);
        // 【安全】验证email存在后再缓存离线凭据
        if (credentials.email) {
          this.cacheOfflineCredentials(credentials.email, response.accessToken);
        }
      }),
      catchError((error) => this.handleError(error))
    );
  }

  // ============ 统一认证 API（手机号登录/注册）============

  /**
   * 手机号登录
   */
  phoneLogin(req: PhoneLoginRequest): Observable<UnifiedTokenResponse> {
    return this.http.post<UnifiedTokenResponse>(`${this.UNIFIED_AUTH_URL}/login/phone`, req).pipe(
      tap((response) => {
        this.storeUnifiedAuthData(response);
        this.cacheOfflineCredentials(req.phone, response.access_token);
      }),
      catchError((error) => this.handleError(error))
    );
  }

  /**
   * 手机号注册
   */
  phoneRegister(req: PhoneRegisterRequest): Observable<UnifiedTokenResponse> {
    return this.http
      .post<UnifiedTokenResponse>(`${this.UNIFIED_AUTH_URL}/register/phone`, req)
      .pipe(
        tap((response) => this.storeUnifiedAuthData(response)),
        catchError((error) => this.handleError(error))
      );
  }

  /**
   * 家长绑定学生
   */
  bindChild(req: BindChildRequest): Observable<unknown> {
    return this.http.post(`${this.UNIFIED_AUTH_URL}/bind-child`, req, {
      headers: this.getAuthHeaders(),
    });
  }

  /**
   * 获取绑定的学生列表
   */
  getChildren(): Observable<unknown> {
    return this.http.get(`${this.UNIFIED_AUTH_URL}/children`, {
      headers: this.getAuthHeaders(),
    });
  }

  /**
   * 存储统一认证数据（映射后端 snake_case 到前端 camelCase）
   */
  private storeUnifiedAuthData(response: UnifiedTokenResponse): void {
    // 【安全】验证用户ID存在且有效
    if (response.user.id === null || response.user.id === undefined) {
      console.error('[Auth] 统一认证响应缺少用户ID');
      throw new Error('Invalid user data: missing user ID');
    }
    
    const user: User = {
      id: String(response.user.id),
      email: response.user.email ?? '',
      username: response.user.username,
      phone: response.user.phone,
      userType: response.user.role,
      createdAt: new Date(response.user.created_at ?? Date.now()),
      updatedAt: new Date(response.user.updated_at ?? Date.now()),
    };

    const authResponse: AuthResponse = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      user,
    };

    this.storeAuthData(authResponse);
  }

  /**
   * OAuth 登录（桌面端：使用系统浏览器；Web 端：页面跳转）
   * 通过后端 API 获取授权 URL，支持 CSRF 保护
   */
  signInWithOAuth(provider: 'github' | 'google' | 'wechat' | 'qq'): void {
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);

    // 从后端获取授权 URL
    this.http
      .get<{
        authorize_url: string;
        state: string;
      }>(`${this.OAUTH_API_URL}/${provider}/authorize`, { params: { redirect_uri: redirectUri } })
      .subscribe({
        next: (response) => {
          this.storeOAuthState({
            provider,
            state: response.state,
            redirectUrl: this.router.url,
          });

          if (this.isElectron && this.electronService) {
            // 桌面端：使用系统默认浏览器完成授权
            this.electronService.openExternal(response.authorize_url).subscribe({
              error: (err) => console.error('[Auth] 打开浏览器失败:', err)
            });
            console.warn('[Auth] 已打开系统浏览器进行 OAuth 授权');
          } else {
            // Web 端：页面跳转
            window.location.href = response.authorize_url;
          }
        },
        error: (err) => {
          console.error('[Auth] 获取 OAuth 授权 URL 失败:', err);

          // 检查 Client ID 是否配置
          const clientId = this.getOAuthClientId(provider);
          if (!clientId) {
            console.error(`[Auth] ${provider} OAuth Client ID 未配置，无法进行授权`);
            // 可以触发 UI 提示用户配置
            return;
          }

          // 降级：使用本地构建的 URL（仅在配置存在时）
          const state = this.generateState();
          const authUrl = this.buildOAuthUrl(provider, redirectUri, state);
          this.storeOAuthState({ provider, state, redirectUrl: this.router.url });

          console.warn(`[Auth] 降级到本地 OAuth URL: ${provider}`);
          if (this.isElectron && this.electronService) {
            this.electronService.openExternal(authUrl).subscribe({
              error: (openErr) => console.error('[Auth] 打开浏览器失败:', openErr)
            });
          } else {
            window.location.href = authUrl;
          }
        },
      });
  }

  /**
   * 构建 OAuth 授权 URL
   */
  private buildOAuthUrl(provider: string, redirectUri: string, state: string): string {
    const clientId = this.getOAuthClientId(provider);
    
    switch (provider) {
      case 'github':
        return (
          `https://github.com/login/oauth/authorize?` +
          `client_id=${clientId}&` +
          `redirect_uri=${redirectUri}&` +
          `state=${state}&` +
          `scope=user:email`
        );
      case 'google':
        return (
          `https://accounts.google.com/o/oauth2/v2/auth?` +
          `client_id=${clientId}&` +
          `redirect_uri=${redirectUri}&` +
          `response_type=code&` +
          `state=${state}&` +
          `scope=openid%20email%20profile`
        );
      case 'wechat':
        return (
          `https://open.weixin.qq.com/connect/qrconnect?` +
          `appid=${clientId}&` +
          `redirect_uri=${redirectUri}&` +
          `response_type=code&` +
          `state=${state}&` +
          `scope=snsapi_login`
        );
      case 'qq':
        return (
          `https://graph.qq.com/oauth2.0/authorize?` +
          `client_id=${clientId}&` +
          `redirect_uri=${redirectUri}&` +
          `response_type=code&` +
          `state=${state}&` +
          `scope=get_user_info`
        );
      default:
        return `#`;
    }
  }

  /**
   * 获取 OAuth Client ID
   * 配置来源：environment.ts 中的 oauth 配置
   */
  private getOAuthClientId(provider: string): string {
    // 【安全】验证provider不是危险属性名，防止原型链污染
    const dangerousProps = ['__proto__', 'constructor', 'prototype', 'hasOwnProperty', 'isPrototypeOf'];
    if (dangerousProps.includes(provider)) {
      console.error('[Auth] 无效的 OAuth provider:', provider);
      return '';
    }
    
    // 使用安全的环境配置访问
    const env = getSafeEnvironment();
    const oauthConfig = env.oauth;
    if (!oauthConfig) {
      if (!env.production) {
        console.warn(`[Auth] OAuth 配置缺失，请在 environment.ts 中设置 oauth`);
      }
      return '';
    }

    // 【安全】使用类型断言安全访问 provider 配置
    const config = (oauthConfig as Record<string, { clientId?: string; appId?: string } | undefined>)?.[provider];
    if (config?.clientId) {
      return config.clientId;
    }
    // 微信使用 appId
    if (config?.appId) {
      return config.appId;
    }
    // 兜底：开发环境警告，生产环境返回空字符串
    if (!env.production) {
      console.warn(`[Auth] ${provider} OAuth Client ID 未配置，请在 environment.ts 中设置`);
    }
    return '';
  }

  /**
   * GitHub OAuth 登录
   */
  signInWithGitHub(): void {
    this.signInWithOAuth('github');
  }

  /**
   * Google OAuth 登录
   */
  signInWithGoogle(): void {
    this.signInWithOAuth('google');
  }

  /**
   * WeChat OAuth 登录
   */
  signInWithWeChat(): void {
    this.signInWithOAuth('wechat');
  }

  /**
   * QQ OAuth 登录
   */
  signInWithQQ(): void {
    this.signInWithOAuth('qq');
  }

  /**
   * 处理OAuth回调
   * 发送 code 和 state 到后端完成登录流程
   */
  handleOAuthCallback(
    provider: string,
    code: string,
    state: string,
    redirectUri: string
  ): Observable<AuthResponse> {
    // 【安全】验证provider是有效值
    const validProviders = ['github', 'google', 'wechat', 'qq'];
    if (!validProviders.includes(provider)) {
      console.error('[Auth] OAuth provider 无效:', provider);
      return throwError(() => new Error('Invalid OAuth provider'));
    }
    
    // 验证state参数格式（防止注入攻击）
    if (!this.validateStateFormat(state)) {
      console.error('[Auth] OAuth state 格式无效，可能存在安全风险');
      return throwError(() => new Error('Invalid OAuth state format'));
    }

    // 验证state值
    const storedState = this.getStoredOAuthState();
    if (!storedState || storedState.state !== state) {
      console.error('[Auth] OAuth state 不匹配，可能存在CSRF攻击');
      return throwError(() => new Error('Invalid OAuth state'));
    }

    // 调用后端 OAuth 回调 API
    return this.http
      .post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        user: {
          id: string | number;
          email?: string;
          username: string;
          role: string;
          created_at?: string;
          updated_at?: string;
        };
      }>(`${this.OAUTH_API_URL}/${provider}/callback`, {
        code,
        state,
        redirect_uri: redirectUri,
      })
      .pipe(
        map((response) => {
          const user: User = {
            id: String(response.user.id),
            email: response.user.email ?? '',
            username: response.user.username,
            userType: response.user.role,
            createdAt: response.user.created_at ? new Date(response.user.created_at) : new Date(),
            updatedAt: response.user.updated_at ? new Date(response.user.updated_at) : new Date(),
          };
          const authResponse: AuthResponse = {
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            user,
          };
          this.storeAuthData(authResponse);
          this.clearOAuthState();
          return authResponse;
        }),
        catchError((error) => this.handleError(error))
      );
  }

  /**
   * GitHub回调处理
   */
  private handleGithubCallback(code: string, stateInfo: OAuthState): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.API_BASE_URL}/github/callback`, { code, state: stateInfo.state })
      .pipe(
        tap((response) => {
          this.storeAuthData(response);
          this.clearOAuthState();
        }),
        catchError((error) => this.handleError(error))
      );
  }

  /**
   * 微信OAuth回调处理
   * 微信回调返回 code，后端通过 code 换取 access_token 和 openid
   */
  private handleWechatCallback(code: string, stateInfo: OAuthState): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.API_BASE_URL}/wechat/callback`, { code, state: stateInfo.state })
      .pipe(
        tap((response) => {
          this.storeAuthData(response);
          this.clearOAuthState();
        }),
        catchError((error) => this.handleError(error))
      );
  }

  /**
   * QQ OAuth回调处理
   * QQ回调返回 code，后端通过 code 换取 access_token 和 openid
   */
  private handleQQCallback(code: string, stateInfo: OAuthState): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.API_BASE_URL}/qq/callback`, { code, state: stateInfo.state })
      .pipe(
        tap((response) => {
          this.storeAuthData(response);
          this.clearOAuthState();
        }),
        catchError((error) => this.handleError(error))
      );
  }

  /**
   * 刷新访问令牌
   */
  refreshToken(): Observable<AuthResponse> {
    // 使用 getStore() 获取正确的存储后端（支持"记住我"模式）
    const refreshToken = this.getStore().getItem(this.REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }

    return this.http
      .post<AuthResponse>(
        `${this.API_BASE_URL}/refresh`,
        { refreshToken },
        { headers: new HttpHeaders({ 'Content-Type': 'application/json' }) }
      )
      .pipe(
        tap((response) => this.storeAuthData(response)),
        catchError((error: unknown) => {
          // 刷新失败则登出
          this.logout();
          return throwError(() => error);
        })
      );
  }

  /**
   * 模拟登录 - 用于演示和测试
   * 无需真实后端，直接设置本地认证状态
   * 
   * @deprecated 仅供开发/演示环境使用，生产环境调用会返回错误
   * @param userType 用户类型
   * @returns Mock 认证响应
   */
  mockLogin(
    userType: 'student' | 'teacher' | 'parent' | 'admin' = 'student'
  ): Observable<AuthResponse> {
    // 生产环境禁用
    if (environment.production) {
      console.error('[Auth] mockLogin 在生产环境不可用');
      return throwError(() => new Error('Mock 登录在生产环境不可用'));
    }
    
    const mockUser = this.createMockUser(userType);
    const mockResponse = this.createMockResponse(mockUser, 'mock');

    // 直接存储认证数据
    this.storeAuthData(mockResponse);

    return new Observable((observer) => {
      observer.next(mockResponse);
      observer.complete();
    });
  }

  /**
   * 创建模拟用户数据
   */
  private createMockUser(userType: 'student' | 'teacher' | 'parent' | 'admin'): User {
    const now = new Date().toISOString();
    const mockUsers = {
      student: {
        id: 'mock-student-001',
        username: '小明同学',
        email: 'demo@matux.ai',
        userType: 'student' as const,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=student',
        grade: '高中一年级',
        createdAt: now,
        updatedAt: now,
      },
      teacher: {
        id: 'mock-teacher-001',
        username: '李老师',
        email: 'teacher@matux.ai',
        userType: 'teacher' as const,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=teacher',
        organizationName: 'MatuX 教育机构',
        createdAt: now,
        updatedAt: now,
      },
      parent: {
        id: 'mock-parent-001',
        username: '家长代表',
        email: 'parent@matux.ai',
        userType: 'parent' as const,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=parent',
        children: ['小明同学'],
        createdAt: now,
        updatedAt: now,
      },
      admin: {
        id: 'mock-admin-001',
        username: '管理员',
        email: 'admin@matux.ai',
        userType: 'org_admin' as const,
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=admin',
        organizationName: 'MatuX 平台',
        createdAt: now,
        updatedAt: now,
      },
    };

    // mockUsers 的 createdAt/updatedAt 是 string，User 接口是 Date，需要双重断言
    return mockUsers[userType] as unknown as User;
  }

  /**
   * 创建模拟响应数据
   */
  private createMockResponse(user: User, prefix: string): AuthResponse {
    const timestamp = Date.now();
    return {
      accessToken: `mock_${prefix}_access_token_${timestamp}`,
      refreshToken: `mock_${prefix}_refresh_token_${timestamp}`,
      user,
    };
  }

  /**
   * 获取可用的模拟账号列表
   */
  getMockAccounts(): Array<{ type: string; label: string; description: string }> {
    return [
      { type: 'student', label: '学生账号', description: '体验学生端功能' },
      { type: 'teacher', label: '教师账号', description: '体验教师端功能' },
      { type: 'parent', label: '家长账号', description: '体验家长端功能' },
    ];
  }

  /**
   * 用户登出
   * @note 服务器撤销令牌请求失败不影响本地登出流程
   */
  logout(): void {
    const refreshToken =
      localStorage.getItem(this.REFRESH_TOKEN_KEY) ??
      sessionStorage.getItem(this.REFRESH_TOKEN_KEY);

    // 可选：通知服务器撤销令牌（不阻塞本地登出）
    if (refreshToken) {
      this.http.post(`${this.API_BASE_URL}/logout`, { refreshToken })
        .pipe(
          catchError((err) => {
            // 服务器撤销失败不影响本地登出，仅记录日志
            const errorMsg = err?.error?.message ?? err?.message ?? String(err);
            console.warn('[Auth] Token 撤销请求失败:', errorMsg);
            return of(null);
          })
        )
        .subscribe();
    }

    // 本地清理不受服务器请求影响
    this.clearAuthData();
    this.clearOfflineCredentials();
    this.setRememberMe(false);
    void this.router.navigate([ROUTES.AUTH.LOGIN]);
  }

  /**
   * 根据用户角色获取默认跳转路径
   * MatuX 桌面端仅有学生角色，其他角色已解耦至 OpenMTEduInst 项目
   */
  getRoleDefaultPath(userType: string | undefined): string {
    if (!userType) return '/';

    // 学生端直接跳转到学习仪表板
    if (userType === 'student') {
      return ROUTES.USER.DASHBOARD;
    }

    // 其他角色已解耦，统一跳转到欢迎页
    return '/';
  }

  /**
   * 根据用户角色自动跳转
   * 登录成功后调用此方法进行页面跳转
   */
  redirectByRole(returnUrl?: string): void {
    const user = this.getCurrentUser();
    const userType = user?.userType;

    // 优先使用传入的返回 URL
    if (returnUrl && returnUrl !== '/auth/login') {
      void this.router.navigateByUrl(returnUrl);
      return;
    }

    // 根据角色跳转到对应仪表板
    const defaultPath = this.getRoleDefaultPath(userType);
    void this.router.navigate([defaultPath]);
  }

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * 检查用户是否已认证
   */
  isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  // 私有辅助方法

  /**
   * 生成随机state参数（密码学安全版本）
   */
  private generateState(): string {
    return generateSecureState();
  }

  /**
   * 验证 state 参数格式（防止注入攻击）
   */
  private validateStateFormat(state: string): boolean {
    return isValidStateFormat(state);
  }

  // ==================== 离线登录 ====================

  /**
   * 离线登录
   * 使用本地缓存的凭据登录，无需网络
   */
  offlineLogin(): Observable<AuthResponse | null> {
    const cachedCredentials = this.getOfflineCredentials();
    if (!cachedCredentials) {
      return of(null);
    }

    // 尝试使用缓存 token 恢复登录态
    const storedToken = this.getAccessToken();
    const storedUser = this.getStore().getItem(this.USER_KEY);

    if (storedToken && storedUser) {
      try {
        const user = JSON.parse(storedUser) as User;
        this.currentUserSubject.next(user);
        this.isAuthenticatedSubject.next(true);
        return of({
          accessToken: storedToken,
          refreshToken: this.getStore().getItem(this.REFRESH_TOKEN_KEY) ?? '',
          user,
        });
      } catch {
        // 数据损坏，清除缓存
        this.clearOfflineCredentials();
      }
    }

    return of(null);
  }

  /**
   * 缓存离线登录凭据
   */
  cacheOfflineCredentials(username: string, token: string): void {
    try {
      const credentials = {
        username,
        token,
        cachedAt: Date.now(),
      };
      localStorage.setItem(this.OFFLINE_CREDENTIALS_KEY, JSON.stringify(credentials));
    } catch {
      console.warn('[Auth] 无法缓存离线凭据');
    }
  }

  /**
   * 获取离线登录凭据
   */
  private getOfflineCredentials(): { username: string; token: string; cachedAt: number } | null {
    try {
      const raw = localStorage.getItem(this.OFFLINE_CREDENTIALS_KEY);
      if (!raw) return null;
      const credentials = JSON.parse(raw) as { username: string; token: string; cachedAt: number };
      if (!credentials) return null;
      // 凭据有效期 30 天
      if (Date.now() - credentials.cachedAt > 30 * 24 * 60 * 60 * 1000) {
        this.clearOfflineCredentials();
        return null;
      }
      return credentials;
    } catch {
      return null;
    }
  }

  /**
   * 清除离线登录凭据
   */
  clearOfflineCredentials(): void {
    localStorage.removeItem(this.OFFLINE_CREDENTIALS_KEY);
  }

  /**
   * 检查是否可以进行离线登录
   */
  canOfflineLogin(): boolean {
    return !!this.getOfflineCredentials();
  }

  /**
   * 存储OAuth状态
   */
  private storeOAuthState(state: OAuthState): void {
    sessionStorage.setItem('oauth_state', JSON.stringify(state));
  }

  /**
   * 获取存储的OAuth状态
   * 【安全】JSON.parse可能抛异常，需要捕获
   */
  private getStoredOAuthState(): OAuthState | null {
    const state = sessionStorage.getItem('oauth_state');
    if (!state) return null;
    try {
      return JSON.parse(state) as OAuthState;
    } catch (error) {
      console.warn('[Auth] OAuth状态解析失败:', error);
      this.clearOAuthState();
      return null;
    }
  }

  /**
   * 清除OAuth状态
   */
  private clearOAuthState(): void {
    sessionStorage.removeItem('oauth_state');
  }

  /**
   * 统一错误处理
   * 优先级：后端消息 > HTTP状态码消息 > 默认消息
   */
  private handleError(error: unknown): Observable<never> {
    let errorMessage = '认证失败';
    let httpStatus: number | null = null;

    // 提取HTTP状态码
    if (typeof error === 'object' && error !== null && 'status' in error) {
      const errorObj = error as { status?: number };
      httpStatus = errorObj.status ?? null;
    }

    // 网络错误（status === 0 或 -1）
    if (httpStatus === 0 || httpStatus === -1) {
      errorMessage = '网络连接失败，请检查网络设置';
      return throwError(() => new Error(errorMessage));
    }

    // 优先使用后端返回的错误消息
    if (typeof error === 'object' && error !== null && 'error' in error) {
      const errorObj = error as { error?: { message?: string } };
      if (errorObj.error?.message) {
        errorMessage = errorObj.error.message;
        return throwError(() => new Error(errorMessage));
      }
    }

    // 使用 HTTP 状态码对应的消息
    if (httpStatus !== null) {
      if (httpStatus === 401) {
        errorMessage = '用户名或密码错误';
      } else if (httpStatus === 409) {
        errorMessage = '用户已存在';
      } else if (httpStatus === 403) {
        errorMessage = '权限不足';
      } else if (httpStatus === 404) {
        errorMessage = '请求的资源不存在';
      } else if (httpStatus === 429) {
        errorMessage = '请求过于频繁，请稍后再试';
      } else if (httpStatus === 500) {
        errorMessage = '服务器内部错误，请稍后重试';
      } else if (httpStatus === 503) {
        errorMessage = '服务暂不可用，请稍后再试';
      }
    }

    // 捕获非 HTTP 错误的通用错误
    if (typeof error === 'object' && error !== null && 'message' in error) {
      const errorObj = error as { message?: string };
      if (errorObj.message) {
        errorMessage = errorObj.message;
      }
    }

    return throwError(() => new Error(errorMessage));
  }
}
