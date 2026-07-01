/**
 * HTTP 认证拦截器
 *
 * 自动为所有 HTTP 请求注入 Authorization Bearer Token
 * 解决手动调用 getAuthHeaders() 容易遗漏的问题
 *
 * 安全设计：
 * - Token 为 null 时不设置 Authorization 头（避免发送 "Bearer null"）
 * - 白名单机制跳过公开端点（登录/注册/OAuth 回调等）
 * - 401 响应自动触发登出流程
 */

import {
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
  HttpErrorResponse,
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AuthService } from '../services/auth.service';

/**
 * 不需要认证头的公开端点白名单
 * 这些端点通常用于登录、注册、OAuth 回调等场景
 */
const PUBLIC_ENDPOINTS = [
  '/api/auth/login',
  '/api/auth/register',
  '/api/auth/refresh',
  '/api/auth/oauth',
  '/api/auth/verify-email',
  '/api/auth/forgot-password',
  '/api/auth/reset-password',
  '/api/public',
] as const;

/**
 * 检查 URL 是否为公开端点（不需要认证）
 */
function isPublicEndpoint(url: string): boolean {
  return PUBLIC_ENDPOINTS.some((endpoint) => url.includes(endpoint));
}

@Injectable()
export class HttpAuthInterceptor implements HttpInterceptor {
  constructor(
    private authService: AuthService,
  ) {}

  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    // 公开端点跳过认证头注入
    if (isPublicEndpoint(request.url)) {
      return next.handle(request).pipe(
        catchError((error: HttpErrorResponse) => this.handleError(error)),
      );
    }

    // 获取当前访问令牌
    const token = this.authService.getAccessToken();

    // Token 存在时注入 Authorization 头
    let authRequest = request;
    if (token) {
      authRequest = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      });
    }

    return next.handle(authRequest).pipe(
      catchError((error: HttpErrorResponse) => this.handleError(error)),
    );
  }

  /**
   * 统一错误处理
   * 401 未授权 → 自动清除认证数据并跳转登录页
   * 403 禁止访问 → 提示权限不足
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    if (error.status === 401) {
      // Token 过期或无效，调用登出清除数据并跳转登录
      this.authService.logout();
    }

    return throwError(() => error);
  }
}
