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
          </div>

          <div class="error-alert" *ngIf="errorMessage">
            {{ errorMessage }}
          </div>

          <button type="submit" class="login-button" [disabled]="loginForm.invalid || loading">
            <span *ngIf="!loading">登录</span>
            <span *ngIf="loading" class="loading-spinner"></span>
          </button>
        </form>

        <div class="signup-link">
          <span>还没有账号？</span>
          <a routerLink="/auth/register">立即注册</a>
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
        justify-content: flex-start;
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

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  onLogin(): void {
    if (this.loading) return;

    this.loading = true;
    this.errorMessage = '';

    this.authService.signIn(this.credentials).subscribe({
      next: () => {
        void this.router.navigate(['/user/dashboard']);
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

  get email(): { invalid: boolean; touched: boolean; errors: Record<string, unknown> } {
    return { invalid: false, touched: false, errors: {} };
  }

  get password(): { invalid: boolean; touched: boolean; errors: Record<string, unknown> } {
    return { invalid: false, touched: false, errors: {} };
  }
}
