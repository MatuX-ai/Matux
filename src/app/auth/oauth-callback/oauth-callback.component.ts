import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { catchError, finalize, of, switchMap } from 'rxjs';

import { AuthService } from '../../core/services/auth.service';
import { ROUTES } from '../../routes.const';

/** OAuth 状态信息 */
interface OAuthState {
  state: string;
  provider: string;
  redirectUrl?: string;
}

/**
 * OAuth 回调处理组件
 *
 * 处理第三方登录的回调：
 * 1. 从 URL 参数中提取 code 和 state
 * 2. 调用后端 OAuth 回调 API 完成登录
 * 3. 根据结果跳转到对应页面
 */
@Component({
  selector: 'app-oauth-callback',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="oauth-callback-container">
      <div class="callback-card">
        <div *ngIf="loading" class="loading-state">
          <div class="spinner"></div>
          <h2>正在处理登录...</h2>
          <p>请稍候，正在完成第三方账号登录</p>
        </div>

        <div *ngIf="!loading && success" class="success-state">
          <div class="success-icon">&#10003;</div>
          <h2>登录成功！</h2>
          <p>即将跳转到首页...</p>
        </div>

        <div *ngIf="!loading && error" class="error-state">
          <div class="error-icon">&#10007;</div>
          <h2>登录失败</h2>
          <p class="error-message">{{ errorMessage }}</p>

          <!-- 【P3 修复】失败原因展开面板 -->
          <details class="error-details">
            <summary>查看可能原因</summary>
            <ul class="error-reasons">
              <li>授权码 (code) 已过期（通常 5 分钟内有效）</li>
              <li>state 参数与登录时不一致（CSRF 防护触发）</li>
              <li>第三方服务 (GitHub/Google/微信/QQ) 临时不可用</li>
              <li>浏览器拦截了第三方 Cookie</li>
              <li>网络连接中断</li>
            </ul>
            <p class="error-troubleshoot">
              <strong>建议操作:</strong>
              点击下方"重新尝试"按钮重新发起授权；若持续失败， 请<a
                [routerLink]="ROUTES.USER.SETTINGS"
                >检查账号设置</a
              >
              或切换其他登录方式。
            </p>
          </details>

          <button class="retry-button" (click)="retry()">重新尝试</button>
          <a class="back-link" [routerLink]="ROUTES.AUTH.LOGIN">返回登录页</a>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .oauth-callback-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        padding: 16px;
      }

      .callback-card {
        background: white;
        border-radius: 16px;
        padding: 48px;
        width: 100%;
        max-width: 400px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
      }

      .spinner {
        width: 48px;
        height: 48px;
        border: 4px solid var(--matux-color-divider, #e2e8f0);
        border-top-color: var(--matux-color-primary, #3b82f6);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto 24px;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      .loading-state h2,
      .success-state h2,
      .error-state h2 {
        font-size: 22px;
        margin-bottom: 8px;
        color: var(--matux-color-text-primary, #1c1917);
      }

      .loading-state p,
      .success-state p {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 14px;
      }

      .success-icon {
        width: 56px;
        height: 56px;
        background: var(--stem-success, #059669);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        margin: 0 auto 20px;
      }

      .error-icon {
        width: 56px;
        height: 56px;
        background: var(--stem-error, #ef4444);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        margin: 0 auto 20px;
      }

      .error-message {
        color: var(--stem-error, #ef4444);
        font-size: 14px;
        margin: 12px 0 16px;
        font-weight: 600;
      }

      /* 【P3 修复】失败原因展开面板样式 */
      .error-details {
        margin: 12px 0 20px;
        padding: 12px 16px;
        border: 1px solid var(--matux-color-divider, #e2e8f0);
        border-radius: 10px;
        background: var(--matux-color-background, #f8fafc);
        text-align: left;
      }

      .error-details summary {
        cursor: pointer;
        color: var(--matux-color-text-secondary, #475569);
        font-size: 13px;
        font-weight: 600;
        user-select: none;
        outline: none;
      }

      .error-details summary::-webkit-details-marker {
        color: var(--matux-color-primary, #3b82f6);
      }

      .error-reasons {
        margin: 12px 0 8px;
        padding-left: 18px;
        color: var(--matux-color-text-secondary, #475569);
        font-size: 12px;
        line-height: 1.8;
      }

      .error-reasons li {
        list-style: disc;
      }

      .error-troubleshoot {
        margin: 8px 0 0;
        padding-top: 8px;
        border-top: 1px dashed var(--matux-color-divider, #e2e8f0);
        color: var(--matux-color-text-secondary, #475569);
        font-size: 12px;
        line-height: 1.6;
      }

      .error-troubleshoot a {
        color: var(--matux-color-primary, #3b82f6);
        text-decoration: none;
        font-weight: 600;
      }

      .error-troubleshoot a:hover {
        text-decoration: underline;
      }

      .retry-button {
        display: inline-block;
        padding: 12px 32px;
        background: var(--matux-color-primary, #3b82f6);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
        margin-bottom: 12px;
      }

      .retry-button:hover {
        background: #5a6fd6;
      }

      .back-link {
        display: block;
        color: var(--matux-color-primary, #3b82f6);
        text-decoration: none;
        font-size: 14px;
      }

      .back-link:hover {
        text-decoration: underline;
      }
    `,
  ],
})
export class OAuthCallbackComponent implements OnInit {
  loading = true;
  success = false;
  error = false;
  errorMessage = '';

  // 路由常量供模板使用
  readonly ROUTES = ROUTES;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.processCallback();
  }

  // eslint-disable-next-line max-lines-per-function
  private processCallback(): void {
    // 从 URL 参数中提取 code 和 state
    const code = this.route.snapshot.queryParamMap.get('code');
    const state = this.route.snapshot.queryParamMap.get('state');

    if (!code || !state) {
      this.loading = false;
      this.error = true;
      this.errorMessage = '缺少授权参数（code 或 state）';
      return;
    }

    // 从 sessionStorage 获取存储的 OAuth state 信息
    const storedState = sessionStorage.getItem('oauth_state');
    if (!storedState) {
      this.loading = false;
      this.error = true;
      this.errorMessage = 'OAuth 状态已过期，请重新登录';
      return;
    }

    const oauthState = JSON.parse(storedState) as OAuthState;

    // 验证 state 参数（防 CSRF）
    if (oauthState.state !== state) {
      this.loading = false;
      this.error = true;
      this.errorMessage = '安全验证失败（state 不匹配），请重新登录';
      sessionStorage.removeItem('oauth_state');
      return;
    }

    const provider = oauthState.provider;
    const redirectUri = `${window.location.origin}/auth/callback`;

    // 调用后端 OAuth 回调 API
    this.authService
      .handleOAuthCallback(provider, code, state, redirectUri)
      .pipe(
        switchMap(() => {
          // 清除存储的 OAuth 状态
          sessionStorage.removeItem('oauth_state');
          this.success = true;
          this.loading = false;
          // 延迟后跳转
          return of(null);
        }),
        catchError((err: Error) => {
          this.loading = false;
          this.error = true;
          this.errorMessage = err.message || 'OAuth 登录失败，请重试';
          return of(null);
        }),
        finalize(() => {
          // 3 秒后跳转
          setTimeout(() => {
            if (this.success) {
              // 【P1 修复】优先级: 1) 登录前 returnUrl; 2) OAuth state.redirectUrl; 3) dashboard
              const sessionReturnUrl = sessionStorage.getItem('pre_login_return_url');
              const returnUrl = sessionReturnUrl ?? oauthState.redirectUrl ?? '/user/dashboard';
              // 清理已使用的 returnUrl,避免污染下次登录
              sessionStorage.removeItem('pre_login_return_url');
              void this.router.navigateByUrl(returnUrl);
            }
          }, 3000);
        })
      )
      .subscribe();
  }

  retry(): void {
    // 【P1 修复】使用 Router.navigate 而非 window.location.href，避免完整页面刷新丢失 SPA 状态
    void this.router.navigateByUrl(ROUTES.AUTH.LOGIN);
  }
}
