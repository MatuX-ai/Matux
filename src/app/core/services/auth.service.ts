import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

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
@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly API_BASE_URL = '/api/auth';
  private readonly UNIFIED_AUTH_URL = '/api/v1/unified-auth';
  private readonly OAUTH_API_URL = '/api/v1/oauth';
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
    return !!(
      localStorage.getItem(this.TOKEN_KEY) ||
      sessionStorage.getItem(this.TOKEN_KEY)
    );
  }

  /**
   * 获取当前有效的 Token
   */
  getAccessToken(): string | null {
    return (
      localStorage.getItem(this.TOKEN_KEY) ||
      sessionStorage.getItem(this.TOKEN_KEY) ||
      null
    );
  }

  /**
   * 获取HTTP头部认证信息
   */
  private getAuthHeaders(): HttpHeaders {
    const token = this.getAccessToken();
    return new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    });
  }

  /**
   * 获取存储后端（记住我 → localStorage，否则 → sessionStorage）
   */
  private getStore(): Storage {
    return this.rememberMeSubject.value ? localStorage : sessionStorage;
  }

  /**
   * 存储认证数据
   */
  private storeAuthData(response: AuthResponse): void {
    const store = this.getStore();
    store.setItem(this.TOKEN_KEY, response.accessToken);
    store.setItem(this.REFRESH_TOKEN_KEY, response.refreshToken);
    store.setItem(this.USER_KEY, JSON.stringify(response.user));

    // 如果记住我，同步到 localStorage
    if (this.rememberMeSubject.value && store === sessionStorage) {
      localStorage.setItem(this.TOKEN_KEY, response.accessToken);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refreshToken);
      localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
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
      return JSON.parse(localStorage.getItem(this.REMEMBER_ME_KEY) || 'false');
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
        // 缓存离线凭据
        this.cacheOfflineCredentials(credentials.email, response.accessToken);
      }),
      catchError((error) => this.handleError(error))
    );
  }

  // ============ 统一认证 API（手机号登录/注册）============

  /**
   * 手机号登录
   */
  phoneLogin(req: PhoneLoginRequest): Observable<UnifiedTokenResponse> {
    return this.http
      .post<UnifiedTokenResponse>(`${this.UNIFIED_AUTH_URL}/login/phone`, req)
      .pipe(
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
  bindChild(req: BindChildRequest): Observable<any> {
    return this.http.post(`${this.UNIFIED_AUTH_URL}/bind-child`, req, {
      headers: this.getAuthHeaders(),
    });
  }

  /**
   * 获取绑定的学生列表
   */
  getChildren(): Observable<any> {
    return this.http.get(`${this.UNIFIED_AUTH_URL}/children`, {
      headers: this.getAuthHeaders(),
    });
  }

  /**
   * 存储统一认证数据（映射后端 snake_case 到前端 camelCase）
   */
  private storeUnifiedAuthData(response: UnifiedTokenResponse): void {
    const user: User = {
      id: String(response.user.id),
      email: response.user.email || '',
      username: response.user.username,
      phone: response.user.phone,
      userType: response.user.role,
      createdAt: new Date(response.user.created_at || Date.now()),
      updatedAt: new Date(response.user.updated_at || Date.now()),
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
      .get<{ authorize_url: string; state: string }>(
        `${this.OAUTH_API_URL}/${provider}/authorize`,
        { params: { redirect_uri: redirectUri } }
      )
      .subscribe({
        next: (response) => {
          this.storeOAuthState({
            provider,
            state: response.state,
            redirectUrl: this.router.url,
          });

          if (this.isElectron && this.electronService) {
            // 桌面端：使用系统默认浏览器完成授权
            this.electronService.openExternal(response.authorize_url).subscribe();
            console.log('[Auth] 已打开系统浏览器进行 OAuth 授权');
          } else {
            // Web 端：页面跳转
            window.location.href = response.authorize_url;
          }
        },
        error: (err) => {
          console.error('[Auth] 获取 OAuth 授权 URL 失败:', err);
          // 降级：使用本地构建的 URL
          const state = this.generateState();
          const authUrl = this.buildOAuthUrl(provider, decodeURIComponent(redirectUri), state);
          this.storeOAuthState({ provider, state, redirectUrl: this.router.url });
          if (this.isElectron && this.electronService) {
            this.electronService.openExternal(authUrl).subscribe();
          } else {
            window.location.href = authUrl;
          }
        }
      });
  }

  /**
   * 构建 OAuth 授权 URL
   */
  private buildOAuthUrl(provider: string, redirectUri: string, state: string): string {
    switch (provider) {
      case 'github':
        return (
          `https://github.com/login/oauth/authorize?` +
          `client_id=${this.getGithubClientId()}&` +
          `redirect_uri=${redirectUri}&` +
          `state=${state}&` +
          `scope=user:email`
        );
      case 'google':
        return (
          `https://accounts.google.com/o/oauth2/v2/auth?` +
          `client_id=${this.getGoogleClientId()}&` +
          `redirect_uri=${redirectUri}&` +
          `response_type=code&` +
          `state=${state}&` +
          `scope=openid%20email%20profile`
        );
      case 'wechat':
        return (
          `https://open.weixin.qq.com/connect/qrconnect?` +
          `appid=${this.getWechatAppId()}&` +
          `redirect_uri=${redirectUri}&` +
          `response_type=code&` +
          `state=${state}&` +
          `scope=snsapi_login`
        );
      case 'qq':
        return (
          `https://graph.qq.com/oauth2.0/authorize?` +
          `client_id=${this.getQQAppId()}&` +
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
    // 验证state参数
    const storedState = this.getStoredOAuthState();
    if (!storedState || storedState.state !== state) {
      return throwError(() => new Error('Invalid OAuth state'));
    }

    // 调用后端 OAuth 回调 API
    return this.http
      .post<{
        access_token: string;
        refresh_token: string;
        token_type: string;
        user: any;
      }>(`${this.OAUTH_API_URL}/${provider}/callback`, {
        code,
        state,
        redirect_uri: redirectUri,
      })
      .pipe(
        map((response) => {
          const user: User = {
            id: String(response.user.id),
            email: response.user.email || '',
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
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
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
        catchError((error) => {
          // 刷新失败则登出
          this.logout();
          return throwError(() => error);
        })
      );
  }

  /**
   * 模拟登录 - 用于演示和测试
   * 无需真实后端，直接设置本地认证状态
   */
  mockLogin(
    userType: 'student' | 'teacher' | 'parent' | 'admin' = 'student'
  ): Observable<AuthResponse> {
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
   */
  logout(): void {
    const refreshToken =
      localStorage.getItem(this.REFRESH_TOKEN_KEY) ||
      sessionStorage.getItem(this.REFRESH_TOKEN_KEY);

    // 可选：通知服务器撤销令牌
    if (refreshToken) {
      this.http.post(`${this.API_BASE_URL}/logout`, { refreshToken }).subscribe();
    }

    this.clearAuthData();
    this.clearOfflineCredentials();
    this.setRememberMe(false);
    void this.router.navigate(['/auth/login']);
  }

  /**
   * 根据用户角色获取默认跳转路径
   */
  getRoleDefaultPath(userType: string | undefined): string {
    if (!userType) return '/';

    const rolePaths: Record<string, string> = {
      student: '/ai-edu',
      teacher: '/teacher/dashboard',
      parent: '/parent/dashboard',
      admin: '/admin/dashboard',
      super_admin: '/admin/dashboard',
    };

    return rolePaths[userType] || '/';
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
   * 生成随机state参数
   */
  private generateState(): string {
    return (
      Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
    );
  }

  /**
   * 获取GitHub客户端ID
   */
  private getGithubClientId(): string {
    return 'your_github_client_id';
  }

  /**
   * 获取Google客户端ID
   */
  private getGoogleClientId(): string {
    return 'your_google_client_id';
  }

  /**
   * 获取微信开放平台 AppID
   * 需要在微信开放平台 (open.weixin.qq.com) 注册应用获取
   */
  private getWechatAppId(): string {
    return 'your_wechat_app_id';
  }

  /**
   * 获取QQ互联 AppID
   * 需要在QQ互联 (connect.qq.com) 注册应用获取
   */
  private getQQAppId(): string {
    return 'your_qq_app_id';
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
          refreshToken: this.getStore().getItem(this.REFRESH_TOKEN_KEY) || '',
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
      const credentials = JSON.parse(raw);
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
   */
  private getStoredOAuthState(): OAuthState | null {
    const state = sessionStorage.getItem('oauth_state');
    return state ? (JSON.parse(state) as OAuthState) : null;
  }

  /**
   * 清除OAuth状态
   */
  private clearOAuthState(): void {
    sessionStorage.removeItem('oauth_state');
  }

  /**
   * 统一错误处理
   */
  private handleError(error: unknown): Observable<never> {
    let errorMessage = '认证失败';
    if (typeof error === 'object' && error !== null && 'error' in error) {
      const errorObj = error as { error?: { message?: string } };
      if (errorObj.error?.message) {
        errorMessage = errorObj.error.message;
      }
    }
    if (typeof error === 'object' && error !== null && 'status' in error) {
      const errorObj = error as { status?: number };
      if (errorObj.status === 401) {
        errorMessage = '用户名或密码错误';
      } else if (errorObj.status === 409) {
        errorMessage = '用户已存在';
      }
    }

    return throwError(() => new Error(errorMessage));
  }
}
