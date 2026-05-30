import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map, tap } from 'rxjs/operators';

interface OAuth2TokenResponse {
  access_token: string;
  token_type: string;
}

interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AdminUser;
}

interface AdminUser {
  id: number;
  username: string;
  email: string;
  role: string;
  permissions?: string[];
  created_at?: string;
  organizationId?: number; // 机构 ID（仅对机构管理员有效）
  is_active?: boolean;
  is_superuser?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class AdminAuthService {
  private readonly ADMIN_TOKEN_KEY = 'admin_access_token';
  private readonly ADMIN_USER_KEY = 'admin_user_info';
  private readonly BASE_URL = '/api/v1'; // 使用通用认证 API

  private currentUserSubject = new BehaviorSubject<AdminUser | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    // 初始化时从localStorage恢复用户信息
    this.initializeAuthState();
  }

  /**
   * 管理员登录
   */
  login(
    username: string,
    password: string,
    rememberMe: boolean = false
  ): Observable<AdminLoginResponse> {
    // OAuth2 标准格式
    const formBody = new URLSearchParams();
    formBody.append('username', username);
    formBody.append('password', password);

    return this.http
      .post<OAuth2TokenResponse>(`${this.BASE_URL}/auth/token`, formBody.toString(), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      .pipe(
        map((response: OAuth2TokenResponse) => this.convertToAdminResponse(response, username)),
        tap((response: AdminLoginResponse) => {
          this.setAuthToken(response.access_token, rememberMe);
          this.setCurrentUser(response.user, rememberMe);

          // 登录成功后，调用/me 接口获取完整的用户信息（包括 organizationId）
          if (response.access_token) {
            this.fetchAndMergeUserInfo(rememberMe);
          }
        })
      );
  }

  /**
   * 将 OAuth2 响应转换为管理员响应格式
   */
  private convertToAdminResponse(
    response: OAuth2TokenResponse,
    username: string
  ): AdminLoginResponse {
    return {
      access_token: response.access_token,
      token_type: response.token_type,
      expires_in: 3600,
      user: {
        id: 0, // 临时值，需要通过/me 接口获取真实用户信息
        username,
        email: '',
        role: 'admin', // 临时值
        permissions: [],
        created_at: new Date().toISOString(),
      },
    };
  }

  /**
   * 获取并合并用户详细信息
   */
  private fetchAndMergeUserInfo(rememberMe: boolean): void {
    this.getMe().subscribe({
      next: (meUser) => {
        // 更新用户信息
        const currentUser = this.getCurrentUser();
        if (currentUser) {
          const updatedUser: AdminUser = {
            ...currentUser,
            ...meUser,
          };
          this.setCurrentUser(updatedUser, rememberMe);
        }
      },
      error: (err) => {
        console.error('获取用户信息失败:', err);
        // 不影响登录流程，继续
      },
    });
  }

  /**
   * 管理员登出
   */
  logout(): void {
    // 清除认证信息
    localStorage.removeItem(this.ADMIN_TOKEN_KEY);
    localStorage.removeItem(this.ADMIN_USER_KEY);
    sessionStorage.removeItem(this.ADMIN_TOKEN_KEY);
    sessionStorage.removeItem(this.ADMIN_USER_KEY);

    // 清除当前用户状态
    this.currentUserSubject.next(null);
  }

  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): AdminUser | null {
    return this.currentUserSubject.value;
  }

  /**
   * 获取认证token
   */
  getAuthToken(): string | null {
    return (
      localStorage.getItem(this.ADMIN_TOKEN_KEY) ?? sessionStorage.getItem(this.ADMIN_TOKEN_KEY)
    );
  }

  /**
   * 检查用户是否有特定权限
   */
  hasPermission(permission: string): boolean {
    const user = this.getCurrentUser();
    if (!user) return false;

    // 超级管理员拥有所有权限
    if (user.role === 'super_admin') return true;

    return user.permissions?.includes(permission) ?? false;
  }

  /**
   * 检查用户角色
   */
  hasRole(role: string): boolean {
    const user = this.getCurrentUser();
    return user ? user.role === role : false;
  }

  /**
   * 刷新认证状态
   */
  refreshToken(): Observable<AdminLoginResponse> {
    return this.http.post<AdminLoginResponse>(`${this.BASE_URL}/auth/refresh`, {}).pipe(
      tap((response: AdminLoginResponse) => {
        if (response.access_token) {
          this.setAuthToken(response.access_token, true);
        }
      })
    );
  }

  /**
   * 获取当前用户详细信息
   */
  getMe(): Observable<AdminUser> {
    return this.http.get<AdminUser>(`${this.BASE_URL}/auth/me`).pipe(
      tap((user: AdminUser) => {
        // 如果是机构管理员，需要从 user_organizations 中获取主组织 ID（已解耦到 OpenMTEduInst 项目）
        // if (user.role === 'org_admin' || user.role === 'organization_admin') {
        //   // 这里需要调用额外的 API 获取用户的主组织
        // }
        this.currentUserSubject.next(user);
      })
    );
  }

  /**
   * 验证当前 token 有效性
   */
  validateToken(): Observable<boolean> {
    return new Observable((observer) => {
      const token = this.getAuthToken();
      if (!token) {
        observer.next(false);
        observer.complete();
        return;
      }

      this.http.get<AdminUser>(`${this.BASE_URL}/auth/me`).subscribe({
        next: (user: AdminUser) => {
          this.setCurrentUser(user, true);
          observer.next(true);
          observer.complete();
        },
        error: () => {
          this.logout();
          observer.next(false);
          observer.complete();
        },
      });
    });
  }

  // 私有方法
  private setAuthToken(token: string, persistent: boolean): void {
    if (persistent) {
      localStorage.setItem(this.ADMIN_TOKEN_KEY, token);
    } else {
      sessionStorage.setItem(this.ADMIN_TOKEN_KEY, token);
    }
  }

  private setCurrentUser(user: AdminUser, persistent: boolean): void {
    this.currentUserSubject.next(user);

    if (persistent) {
      localStorage.setItem(this.ADMIN_USER_KEY, JSON.stringify(user));
    } else {
      sessionStorage.setItem(this.ADMIN_USER_KEY, JSON.stringify(user));
    }
  }

  private initializeAuthState(): void {
    const storedUser =
      localStorage.getItem(this.ADMIN_USER_KEY) ?? sessionStorage.getItem(this.ADMIN_USER_KEY);
    if (storedUser) {
      try {
        const user = JSON.parse(storedUser) as AdminUser;
        this.currentUserSubject.next(user);
      } catch (e) {
        // 如果解析失败，清除存储的数据
        this.clearStorage();
      }
    }
  }

  private clearStorage(): void {
    localStorage.removeItem(this.ADMIN_TOKEN_KEY);
    localStorage.removeItem(this.ADMIN_USER_KEY);
    sessionStorage.removeItem(this.ADMIN_TOKEN_KEY);
    sessionStorage.removeItem(this.ADMIN_USER_KEY);
  }
}
