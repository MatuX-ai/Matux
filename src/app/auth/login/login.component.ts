import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

import { LoginRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1 class="login-title">登录 MatuX</h1>
          <p class="login-subtitle">欢迎回来，继续你的AI学习之旅</p>
        </div>

        <form class="login-form" (ngSubmit)="onLogin()" #loginForm="ngForm">
          <div class="form-group">
            <label class="form-label" for="email">邮箱地址</label>
            <input
              type="email"
              id="email"
              name="email"
              class="form-input"
              [(ngModel)]="credentials.email"
              required
              email
              placeholder="请输入邮箱地址"
            />
            <div class="error-message" *ngIf="email.invalid && email.touched">
              <span *ngIf="email.errors['required']">邮箱地址不能为空</span>
              <span *ngIf="email.errors['email']">请输入有效的邮箱地址</span>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <input
              type="password"
              id="password"
              name="password"
              class="form-input"
              [(ngModel)]="credentials.password"
              required
              minlength="6"
              placeholder="请输入密码"
            />
            <div class="error-message" *ngIf="password.invalid && password.touched">
              <span *ngIf="password.errors?.['required']">密码不能为空</span>
              <span *ngIf="password.errors?.['minlength']">密码至少6个字符</span>
            </div>
          </div>

          <div class="form-options">
            <label class="remember-me">
              <input type="checkbox" [(ngModel)]="rememberMe" name="rememberMe" />
              <span>记住我</span>
            </label>
            <span class="forgot-password" style="cursor:default;color:#999;">忘记密码？</span>
          </div>

          <div class="error-alert" *ngIf="errorMessage">
            {{ errorMessage }}
          </div>

          <button type="submit" class="login-button" [disabled]="loginForm.invalid || loading">
            <span *ngIf="!loading">登录</span>
            <span *ngIf="loading" class="loading-spinner"></span>
          </button>
        </form>

        <div class="divider">
          <span>或使用以下方式登录</span>
        </div>

        <div class="social-login">
          <button class="social-button github" (click)="loginWithGitHub()">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path
                d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
              />
            </svg>
            GitHub 登录
          </button>
        </div>

        <div class="signup-link">
          <span>还没有账号？</span>
          <a routerLink="/auth/register">立即注册</a>
        </div>

        <!-- 模拟登录区域 -->
        <div class="mock-login-section">
          <div class="mock-divider">
            <span>体验账号</span>
          </div>
          <p class="mock-hint">点击下方账号快速体验登录效果</p>
          <div class="mock-accounts">
            <button
              *ngFor="let account of mockAccounts"
              class="mock-account-btn"
              (click)="loginWithMock(account.type)"
              [title]="account.description"
            >
              <span class="mock-icon">{{ account.icon }}</span>
              <span class="mock-label">{{ account.label }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .login-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 16px;
      }

      .login-card {
        background: white;
        border-radius: 16px;
        padding: 48px;
        width: 100%;
        max-width: 440px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
      }

      .login-header {
        text-align: center;
        margin-bottom: 32px;
      }

      .login-title {
        font-size: 28px;
        font-weight: 700;
        color: #1d1d1f;
        margin-bottom: 8px;
      }

      .login-subtitle {
        font-size: 14px;
        color: #86868b;
      }

      .login-form {
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .form-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .form-label {
        font-size: 14px;
        font-weight: 500;
        color: #3a3a3c;
      }

      .form-input {
        padding: 14px 16px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        font-size: 16px;
        transition: all 0.3s ease;
      }

      .form-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
      }

      .form-input::placeholder {
        color: #a0a0a7;
      }

      .error-message {
        font-size: 12px;
        color: #ff3b30;
      }

      .form-options {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 8px 0;
      }

      .remember-me {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: #3a3a3c;
        cursor: pointer;
      }

      .forgot-password {
        font-size: 14px;
        color: #667eea;
        text-decoration: none;
        transition: color 0.3s ease;
      }

      .forgot-password:hover {
        color: #5568d3;
        text-decoration: underline;
      }

      .error-alert {
        padding: 12px 16px;
        background: #ffebee;
        border: 1px solid #ffcdd2;
        border-radius: 8px;
        color: #c62828;
        font-size: 14px;
      }

      .login-button {
        padding: 14px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .login-button:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
      }

      .login-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      .loading-spinner {
        width: 20px;
        height: 20px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      .divider {
        position: relative;
        text-align: center;
        margin: 24px 0;
      }

      .divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #e5e5ea;
      }

      .divider span {
        background: white;
        padding: 0 16px;
        color: #86868b;
        font-size: 14px;
        position: relative;
      }

      .social-login {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .social-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 12px 16px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        background: white;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .social-button:hover {
        background: #f5f5f7;
        border-color: #667eea;
      }

      .social-icon {
        width: 20px;
        height: 20px;
        fill: currentColor;
      }

      .signup-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
        color: #86868b;
      }

      .signup-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
        margin-left: 4px;
        transition: color 0.3s ease;
      }

      .signup-link a:hover {
        color: #5568d3;
        text-decoration: underline;
      }

      @media (max-width: 767px) {
        .login-card {
          padding: 32px 24px;
        }

        .form-options {
          flex-direction: column;
          gap: 12px;
          align-items: flex-start;
        }

        .login-container {
          padding: 12px;
        }

        .login-card {
          max-width: 100%;
        }

        .login-title {
          font-size: 24px;
        }
      }

      /* 模拟登录样式 */
      .mock-login-section {
        margin-top: 24px;
        padding-top: 24px;
        border-top: 1px dashed #e5e5ea;
      }

      .mock-divider {
        position: relative;
        text-align: center;
        margin-bottom: 12px;
      }

      .mock-divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #e5e5ea;
      }

      .mock-divider span {
        background: white;
        padding: 0 16px;
        color: #86868b;
        font-size: 13px;
        position: relative;
      }

      .mock-hint {
        text-align: center;
        color: #86868b;
        font-size: 13px;
        margin-bottom: 16px;
      }

      .mock-accounts {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
      }

      .mock-account-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 10px 12px;
        border: 1px solid #e5e5ea;
        border-radius: 8px;
        background: #fafafa;
        font-size: 13px;
        color: #3a3a3c;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .mock-account-btn:hover {
        border-color: #667eea;
        background: #f0f4ff;
        transform: translateY(-1px);
      }

      .mock-icon {
        font-size: 16px;
      }

      .mock-label {
        font-weight: 500;
      }
    `,
  ],
})
export class LoginComponent {
  credentials: LoginRequest = {
    email: '',
    password: '',
  };
  rememberMe = false;
  loading = false;
  errorMessage = '';

  // 模拟账号列表
  mockAccounts = [
    { type: 'student', label: '学生', icon: '🎓', description: '体验学生端功能' },
    { type: 'teacher', label: '教师', icon: '👨‍🏫', description: '体验教师端功能' },
    { type: 'parent', label: '家长', icon: '👨‍👩‍👧', description: '体验家长端功能' },
    { type: 'admin', label: '管理员', icon: '⚙️', description: '体验管理后台' },
  ];

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  /**
   * 模拟登录 - 快速体验登录效果
   */
  loginWithMock(userType: string): void {
    this.loading = true;
    this.errorMessage = '';

    this.authService.mockLogin(userType as 'student' | 'teacher' | 'parent' | 'admin').subscribe({
      next: () => {
        // 模拟登录成功，延迟一小段时间让用户看到加载效果
        setTimeout(() => {
          this.loading = false;
          this.redirectToUserCenter(userType);
        }, 500);
      },
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      error: (_error) => {
        this.errorMessage = '模拟登录失败';
        this.loading = false;
      },
    });
  }

  /**
   * 根据用户类型跳转到对应的用户中心
   */
  private redirectToUserCenter(userType: string): void {
    switch (userType) {
      case 'student':
        void this.router.navigate(['/user']);
        break;
      case 'teacher':
        void this.router.navigate(['/user']);
        break;
      case 'parent':
        void this.router.navigate(['/user']);
        break;
      case 'admin':
        void this.router.navigate(['/admin']);
        break;
      default:
        void this.router.navigate(['/dashboard']);
    }
  }

  onLogin(): void {
    if (this.loading) return;

    this.loading = true;
    this.errorMessage = '';

    this.authService.signIn(this.credentials).subscribe({
      next: (response) => {
        const userType = response.user?.userType;
        this.redirectToUserCenter(userType ?? '');
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      error: (error: any) => {
        const errorMessage =
          (error as { message?: string })?.message ?? '登录失败，请检查邮箱和密码';
        this.errorMessage = errorMessage;
        this.loading = false;
      },
    });
  }

  loginWithGitHub(): void {
    this.authService.signInWithGitHub();
  }

  get email(): { invalid: boolean; touched: boolean; errors: Record<string, unknown> } {
    // Access ngModel reference through template reference
    return { invalid: false, touched: false, errors: {} };
  }

  get password(): { invalid: boolean; touched: boolean; errors: Record<string, unknown> } {
    return { invalid: false, touched: false, errors: {} };
  }
}
