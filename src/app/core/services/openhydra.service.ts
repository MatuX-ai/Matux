import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

import { AuthService } from './auth.service';

export interface ContainerConfig {
  cpu?: number;
  memory?: string;
  gpu?: number;
  image?: string;
  volumes?: string[];
}

export interface ContainerResponse {
  container_id: string;
  user_id: string;
  status: string;
  jupyter_url: string;
  created_at: string;
  expires_at: string;
  resources: {
    cpu: number;
    memory: string;
    gpu: number;
  };
}

export interface EnterLabResponse {
  success: boolean;
  container_id: string;
  jupyter_url: string;
  access_token: string;
  message: string;
}

export interface ContainerStatusResponse {
  container_id: string;
  status: string;
  is_running: boolean;
  jupyter_accessible: boolean;
  resource_usage: {
    cpu?: number;
    memory?: number;
    disk?: number;
  };
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  details?: unknown;
  error?: string;
}

/**
 * OpenHydra AI 实验室服务
 * 提供容器管理、Jupyter 环境访问等功能
 */
@Injectable({
  providedIn: 'root',
})
export class OpenHydraService {
  private readonly apiUrl = `${environment.apiUrl}/api/v1`;

  /**
   * Jupyter 访问令牌（内存存储，更安全）
   * 注意：页面刷新后会丢失，需要重新进入实验室
   */
  private jupyterAccessToken: string | null = null;

  /**
   * 容器 ID（内存存储）
   */
  private containerId: string | null = null;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  /**
   * 获取 Jupyter 访问令牌
   * @returns 令牌或 null（如果未进入实验室或会话已过期）
   */
  getJupyterAccessToken(): string | null {
    return this.jupyterAccessToken;
  }

  /**
   * 获取容器 ID
   */
  getContainerId(): string | null {
    return this.containerId;
  }

  /**
   * 检查是否已登录 Jupyter 环境
   */
  isLoggedIn(): boolean {
    return this.jupyterAccessToken !== null;
  }

  /**
   * 获取当前用户所属组织ID
   * 优先从用户上下文获取，若用户未登录则默认使用1
   */
  private getOrgId(): number {
    const user = this.authService.getCurrentUser();
    return user?.orgIds?.[0] ?? 1;
  }

  /**
   * 进入 AI 实验室
   * 一键创建或恢复专属 AI 实训环境
   */
  enterLab(config?: ContainerConfig): Observable<EnterLabResponse> {
    const url = `${this.apiUrl}/org/${this.getOrgId()}/ai-lab/enter`;

    return this.http.post<EnterLabResponse>(url, config ?? {}).pipe(
      tap((response) => {
        // 保存到内存存储（更安全，页面刷新后需重新登录）
        if (response.access_token) {
          this.jupyterAccessToken = response.access_token;
          this.containerId = response.container_id;
        }
      }),
      catchError((error) => {
        throw error;
      })
    );
  }

  /**
   * 获取容器状态
   */
  getContainerStatus(): Observable<ContainerStatusResponse> {
    const url = `${this.apiUrl}/org/${this.getOrgId()}/ai-lab/container/status`;

    return this.http.get<ContainerStatusResponse>(url).pipe(
      catchError((error) => {
        throw error;
      })
    );
  }

  /**
   * 停止容器
   */
  stopContainer(): Observable<{ success: boolean; message: string; container_id: string }> {
    const url = `${this.apiUrl}/org/${this.getOrgId()}/ai-lab/container/stop`;

    return this.http
      .post<{ success: boolean; message: string; container_id: string }>(url, {})
      .pipe(
        tap(() => {
          // 清除本地存储
          localStorage.removeItem('jupyter_access_token');
          localStorage.removeItem('jupyter_container_id');
        }),
        catchError((error) => {
          throw error;
        })
      );
  }

  /**
   * 延长容器有效期
   * @param hours 延长的时间（小时）
   */
  extendContainer(hours: number = 4): Observable<{
    success: boolean;
    message: string;
    new_expiry: string;
    container_id: string;
  }> {
    const url = `${this.apiUrl}/org/${this.getOrgId()}/ai-lab/container/extend?hours=${hours}`;

    return this.http
      .post<{
        success: boolean;
        message: string;
        new_expiry: string;
        container_id: string;
      }>(url, { hours });
  }

  /**
   * 健康检查
   */
  healthCheck(): Observable<
    HealthCheckResponse | { status: string; service: string; error: string }
  > {
    const url = `${this.apiUrl}/org/${this.getOrgId()}/ai-lab/health`;

    return this.http.get<HealthCheckResponse>(url).pipe(
      catchError((error: Error) => {
        return of({
          status: 'unhealthy' as const,
          service: 'openhydra',
          error: error.message || '服务不可用',
        });
      })
    );
  }

  /**
   * 打开 Jupyter 环境
   * @param token 访问令牌
   * @param jupyterUrl Jupyter URL
   */
  openJupyterEnvironment(token: string, jupyterUrl: string): void {
    const fullUrl = `${jupyterUrl}?token=${token}`;
    window.open(fullUrl, '_blank');
  }

  /**
   * 获取存储的访问令牌
   */
  getStoredToken(): string | null {
    return localStorage.getItem('jupyter_access_token');
  }

  /**
   * 获取存储的容器 ID
   */
  getStoredContainerId(): string | null {
    return localStorage.getItem('jupyter_container_id');
  }

  /**
   * 清除本地存储的令牌
   */
  clearStoredToken(): void {
    localStorage.removeItem('jupyter_access_token');
    localStorage.removeItem('jupyter_container_id');
  }
}
