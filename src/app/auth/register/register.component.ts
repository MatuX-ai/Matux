import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="register-container">
      <div class="register-card">
        <div class="register-header">
          <h1 class="register-title">创建账号</h1>
          <p class="register-subtitle">加入 MatuX 智能学习平台</p>
        </div>

        <!-- 邮箱注册表单 -->
        <form class="register-form" (ngSubmit)="onRegister()" #registerForm="ngForm">
          <!-- 用户名 -->
          <div class="form-group">
            <label class="form-label" for="username">用户名</label>
            <input
              type="text"
              id="username"
              name="username"
              class="form-input"
              [(ngModel)]="userData.username"
              required
              minlength="3"
              placeholder="请输入用户名（至少3个字符）"
            />
            <div class="error-message" *ngIf="username.invalid && username.touched">
              <span *ngIf="username.errors?.['required']">用户名不能为空</span>
              <span *ngIf="username.errors?.['minlength']">用户名至少3个字符</span>
            </div>
          </div>

          <!-- 邮箱 -->
          <div class="form-group">
            <label class="form-label" for="email">邮箱</label>
            <input
              type="email"
              id="email"
              name="email"
              class="form-input"
              [(ngModel)]="userData.email"
              required
              email
              placeholder="请输入邮箱地址"
            />
            <div class="error-message" *ngIf="email.invalid && email.touched">
              <span *ngIf="email.errors?.['required']">邮箱地址不能为空</span>
              <span *ngIf="email.errors?.['email']">请输入有效的邮箱地址</span>
            </div>
          </div>

          <!-- 密码 -->
          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <div class="password-input-wrapper">
              <input
                [type]="showPassword ? 'text' : 'password'"
                id="password"
                name="password"
                class="form-input"
                [(ngModel)]="userData.password"
                required
                minlength="6"
                placeholder="请输入密码（至少6位）"
              />
              <button
                type="button"
                class="toggle-password"
                (click)="showPassword = !showPassword"
                tabindex="-1"
              >
                {{ showPassword ? '🙈' : '👁️' }}
              </button>
            </div>
            <div class="error-message" *ngIf="password.invalid && password.touched">
              <span *ngIf="password.errors?.['required']">密码不能为空</span>
              <span *ngIf="password.errors?.['minlength']">密码至少6个字符</span>
            </div>
          </div>

          <!-- 确认密码 -->
          <div class="form-group">
            <label class="form-label" for="confirmPassword">确认密码</label>
            <div class="password-input-wrapper">
              <input
                [type]="showConfirmPassword ? 'text' : 'password'"
                id="confirmPassword"
                name="confirmPassword"
                class="form-input"
                [(ngModel)]="confirmPassword"
                required
                placeholder="请再次输入密码"
              />
              <button
                type="button"
                class="toggle-password"
                (click)="showConfirmPassword = !showConfirmPassword"
                tabindex="-1"
              >
                {{ showConfirmPassword ? '🙈' : '👁️' }}
              </button>
            </div>
            <div class="error-message" *ngIf="confirmPasswordMismatch && confirmPasswordTouched">
              两次输入的密码不一致
            </div>
          </div>

          <!-- 服务条款 -->
          <div class="terms-group">
            <label class="terms-label">
              <input
                type="checkbox"
                name="agreeTerms"
                [(ngModel)]="agreeTerms"
                required
                class="terms-checkbox"
              />
              <span class="terms-text">
                我已阅读并同意
                <a href="#" class="terms-link" (click)="$event.preventDefault()">《服务条款》</a>
                和
                <a href="#" class="terms-link" (click)="$event.preventDefault()">《隐私政策》</a>
              </span>
            </label>
          </div>

          <!-- 错误提示 -->
          <div class="error-alert" *ngIf="errorMessage">
            {{ errorMessage }}
          </div>

          <!-- 成功提示 -->
          <div class="success-alert" *ngIf="successMessage">
            {{ successMessage }}
          </div>

          <!-- 注册按钮 -->
          <button
            type="submit"
            class="register-button"
            [disabled]="registerForm.invalid || loading || !agreeTerms"
          >
            <span *ngIf="!loading">注册</span>
            <span *ngIf="loading" class="loading-spinner"></span>
          </button>
        </form>

        <!-- 已有账号 -->
        <div class="login-link">
          <span>已有账号？</span>
          <a routerLink="/auth/login">立即登录</a>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .register-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 16px;
      }

      .register-card {
        background: white;
        border-radius: 16px;
        padding: 48px;
        width: 100%;
        max-width: 460px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
      }

      .register-header {
        text-align: center;
        margin-bottom: 32px;
      }

      .register-title {
        font-size: 28px;
        font-weight: 700;
        color: #1d1d1f;
        margin-bottom: 8px;
      }

      .register-subtitle {
        font-size: 14px;
        color: #86868b;
      }

      .register-form {
        display: flex;
        flex-direction: column;
        gap: 16px;
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
        width: 100%;
        padding: 14px 16px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        font-size: 16px;
        transition: all 0.3s ease;
        background: white;
        box-sizing: border-box;
      }

      .form-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
      }

      .form-input::placeholder {
        color: #a0a0a7;
      }

      .password-input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
      }

      .password-input-wrapper .form-input {
        padding-right: 48px;
      }

      .toggle-password {
        position: absolute;
        right: 8px;
        background: none;
        border: none;
        cursor: pointer;
        padding: 8px;
        font-size: 18px;
        line-height: 1;
        color: #86868b;
      }

      .toggle-password:hover {
        color: #3a3a3c;
      }

      .error-message {
        font-size: 12px;
        color: #ff3b30;
      }

      .terms-group {
        margin: 4px 0;
      }

      .terms-label {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: #3a3a3c;
        cursor: pointer;
      }

      .terms-checkbox {
        width: 16px;
        height: 16px;
        cursor: pointer;
        flex-shrink: 0;
      }

      .terms-text {
        line-height: 1.4;
      }

      .terms-link {
        color: #667eea;
        text-decoration: none;
      }

      .terms-link:hover {
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

      .success-alert {
        padding: 12px 16px;
        background: #e8f5e8;
        border: 1px solid #c8e6c9;
        border-radius: 8px;
        color: #2e7d32;
        font-size: 14px;
      }

      .register-button {
        padding: 14px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .register-button:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
      }

      .register-button:disabled {
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

      .login-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
        color: #86868b;
      }

      .login-link a {
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
        margin-left: 4px;
      }

      .login-link a:hover {
        text-decoration: underline;
      }

      @media (max-width: 767px) {
        .register-card {
          padding: 32px 24px;
        }

        .register-container {
          padding: 12px;
        }

        .register-card {
          max-width: 100%;
        }

        .register-title {
          font-size: 24px;
        }
      }
    `,
  ],
})
export class RegisterComponent {
  showPassword = false;
  showConfirmPassword = false;
  confirmPassword = '';
  confirmPasswordTouched = false;
  agreeTerms = false;
  loading = false;
  errorMessage = '';
  successMessage = '';

  userData = {
    username: '',
    email: '',
    password: '',
  };

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  get confirmPasswordMismatch(): boolean {
    return this.confirmPassword !== this.userData.password;
  }

  get username() {
    return { invalid: false, touched: false, errors: {} as Record<string, unknown> };
  }

  get email() {
    return { invalid: false, touched: false, errors: {} as Record<string, unknown> };
  }

  get password() {
    return { invalid: false, touched: false, errors: {} as Record<string, unknown> };
  }

  onRegister(): void {
    if (this.userData.password !== this.confirmPassword) {
      this.confirmPasswordTouched = true;
      this.errorMessage = '两次输入的密码不一致';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.authService.signUp(this.userData).subscribe({
      next: () => {
        this.loading = false;
        this.successMessage = '注册成功！正在跳转...';
        setTimeout(() => {
          void this.router.navigate(['/user/dashboard']);
        }, 1500);
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage = (error as Error).message || '注册失败，请稍后重试';
      },
    });
  }
}
