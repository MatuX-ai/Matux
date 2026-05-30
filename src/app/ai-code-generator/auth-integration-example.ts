/**
 * 认证集成示例 - 展示如何将 AI 服务与认证系统集成
 *
 * 注意：这是一个示例文件，用于演示和参考，不是生产代码。
 * 某些 TypeScript 错误是预期的，因为它们是为了示例目的而简化的。
 */

import { CommonModule } from '@angular/common';
import { Component, Injectable, OnDestroy } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, Subscription } from 'rxjs';

// 模拟导入现有认证服务
// import { AuthService, User, UserRole } from '../core/services/auth.service';
// import { AngularAIService } from '../../ai-sdk/angular-wrapper';

// 模拟类型定义
interface User {
  id: number;
  username: string;
  email: string;
  role: string;
}

enum UserRole {
  USER = 'user',
  PREMIUM = 'premium',
  ADMIN = 'admin',
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  accessToken: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class MockAuthService {
  private authStateSubject = new BehaviorSubject<AuthState>({
    isAuthenticated: false,
    user: null,
    accessToken: null,
  });

  public authState$ = this.authStateSubject.asObservable();
  public isAuthenticated$ = this.authState$
    .pipe
    // 模拟 map 操作符
    // map(state => state.isAuthenticated)
    ();
  public currentUser$ = this.authState$
    .pipe
    // 模拟 map 操作符
    // map(state => state.user)
    ();

  login(credentials: { username: string; password: string }): Observable<any> {
    // 模拟登录逻辑
    return new Observable((observer) => {
      setTimeout(() => {
        const mockUser: User = {
          id: 1,
          username: credentials.username,
          email: `${credentials.username}@example.com`,
          role: UserRole.USER,
        };

        const mockToken = 'mock-jwt-token-' + Date.now();

        this.authStateSubject.next({
          isAuthenticated: true,
          user: mockUser,
          accessToken: mockToken,
        });

        observer.next({
          user: mockUser,
          accessToken: mockToken,
        });
        observer.complete();
      }, 1000);
    });
  }

  logout(): void {
    this.authStateSubject.next({
      isAuthenticated: false,
      user: null,
      accessToken: null,
    });
  }

  getAccessToken(): string | null {
    return this.authStateSubject.value.accessToken;
  }

  getCurrentUser(): User | null {
    return this.authStateSubject.value.user;
  }
}

// AI 服务包装器 - 集成认证
@Injectable({
  providedIn: 'root',
})
export class AuthenticatedAIService implements OnDestroy {
  private authSubscription?: Subscription;
  private currentUser: User | null = null;
  private isAuthenticated = false;

  constructor(
    private mockAuthService: MockAuthService,
    private router: Router
    // private aiService: AngularAIService  // 实际使用时注入真实的 AI 服务
  ) {
    this.initializeAuthIntegration();
  }

  private initializeAuthIntegration(): void {
    // 订阅认证状态变化
    this.authSubscription = this.mockAuthService.authState$.subscribe((state) => {
      this.isAuthenticated = state.isAuthenticated;
      this.currentUser = state.user;

      // 根据认证状态更新 AI 服务
      if (state.isAuthenticated && state.accessToken) {
        // 实际使用时：this.aiService.setAccessToken(state.accessToken);
      } else {
        // 实际使用时：this.aiService.clearAccessToken();
      }
    });
  }

  ngOnDestroy(): void {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  // 代理 AI 服务方法，添加认证检查
  async generateCode(_request: any): Promise<any> {
    if (!this.isAuthenticated) {
      throw new Error('请先登录以使用 AI 代码生成功能');
    }

    // 检查用户配额
    if (this.currentUser && !this.checkUserQuota(this.currentUser)) {
      throw new Error('您的 AI 使用配额已用完，请升级账户或明天再试');
    }

    // 实际使用时调用真实的 AI 服务
    // return await this.aiService.generateCode(request);

    // 模拟 AI 响应
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          code: `// 生成的代码示例\nfunction helloWorld() {\n  console.log('Hello, World!');\n}`,
          provider: 'openai',
          model: 'gpt-4-turbo',
          tokensUsed: 42,
          processingTime: 1.25,
        });
      }, 2000);
    });
  }

  private checkUserQuota(user: User): boolean {
    // 模拟配额检查逻辑
    const quotaLimits = {
      [UserRole.USER]: 10,
      [UserRole.PREMIUM]: 100,
      [UserRole.ADMIN]: 1000,
    };

    const usedToday = Math.floor(Math.random() * 5); // 模拟今日使用量
    const limit = quotaLimits[user.role as UserRole] || 10;

    return usedToday < limit;
  }

  // 获取用户配额信息
  getUserQuotaInfo(): { used: number; limit: number; remaining: number } | null {
    if (!this.currentUser) {
      return null;
    }

    const quotaLimits = {
      [UserRole.USER]: 10,
      [UserRole.PREMIUM]: 100,
      [UserRole.ADMIN]: 1000,
    };

    const used = Math.floor(Math.random() * 5);
    const limit = quotaLimits[this.currentUser.role as UserRole] || 10;

    return {
      used,
      limit,
      remaining: Math.max(0, limit - used),
    };
  }

  // 检查是否有足够配额
  hasSufficientQuota(): boolean {
    const quotaInfo = this.getUserQuotaInfo();
    return quotaInfo ? quotaInfo.remaining > 0 : false;
  }
}

// 增强的 AI 代码生成器组件
@Component({
  selector: 'app-enhanced-ai-generator',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
  template: `
    <div class="enhanced-ai-generator">
      <!-- 认证状态显示 -->
      <div class="auth-status" *ngIf="authState$ | async as authState">
        <div *ngIf="authState.isAuthenticated" class="logged-in">
          <span>欢迎，{{ authState.user?.username }}!</span>
          <button (click)="logout()" class="btn-logout">退出登录</button>
        </div>
        <div *ngIf="!authState.isAuthenticated" class="logged-out">
          <button (click)="login()" class="btn-login">登录使用 AI 功能</button>
        </div>
      </div>

      <!-- 配额信息 -->
      <div class="quota-info" *ngIf="isAuthenticated && currentUser">
        <div class="quota-display" *ngIf="quotaInfo">
          <div class="quota-bar">
            <div
              class="quota-fill"
              [style.width.%]="(quotaInfo!.used / quotaInfo!.limit) * 100"
            ></div>
          </div>
          <div class="quota-text">
            今日使用：{{ quotaInfo!.used }}/{{ quotaInfo!.limit }} (剩余：{{
              quotaInfo!.remaining
            }})
          </div>
        </div>

        <div *ngIf="quotaInfo?.remaining === 0" class="quota-exceeded">
          <p>⚠️ 您的今日配额已用完</p>
          <button class="btn-upgrade" (click)="upgradeAccount()">升级账户获取更多配额</button>
        </div>
      </div>

      <!-- AI 代码生成表单 -->
      <div class="ai-form-container" *ngIf="isAuthenticated">
        <form (ngSubmit)="generateCode()" [formGroup]="generationForm">
          <div class="form-group">
            <label>代码需求描述:</label>
            <textarea
              formControlName="prompt"
              placeholder="描述您想要生成的代码..."
              [disabled]="!hasSufficientQuota"
            >
            </textarea>
          </div>

          <div class="form-actions">
            <button
              type="submit"
              class="btn-generate"
              [disabled]="!generationForm.valid || isGenerating || !hasSufficientQuota"
            >
              <span *ngIf="!isGenerating">✨ 生成代码</span>
              <span *ngIf="isGenerating">⏳ 生成中...</span>
            </button>

            <button
              type="button"
              class="btn-clear"
              (click)="clearResults()"
              [disabled]="isGenerating"
            >
              清除结果
            </button>
          </div>
        </form>
      </div>

      <!-- 错误和成功消息 -->
      <div class="messages">
        <div *ngIf="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
        <div *ngIf="successMessage" class="success-message">
          {{ successMessage }}
        </div>
      </div>

      <!-- 生成结果 -->
      <div class="results" *ngIf="generatedCode">
        <h3>生成的代码:</h3>
        <pre><code>{{ generatedCode }}</code></pre>
        <div class="result-actions">
          <button (click)="copyCode()">📋 复制代码</button>
          <button (click)="downloadCode()">💾 下载代码</button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .enhanced-ai-generator {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
      }

      .auth-status {
        margin-bottom: 20px;
        padding: 15px;
        border-radius: 8px;
        background: #f5f5f5;
      }

      .logged-in {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .quota-info {
        margin-bottom: 20px;
      }

      .quota-bar {
        width: 100%;
        height: 20px;
        background: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 10px;
      }

      .quota-fill {
        height: 100%;
        background: linear-gradient(90deg, #4caf50, #8bc34a);
        transition: width 0.3s ease;
      }

      .quota-exceeded {
        background: #ffebee;
        color: #c62828;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
      }

      .ai-form-container {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      }

      .form-group {
        margin-bottom: 20px;
      }

      textarea {
        width: 100%;
        min-height: 120px;
        padding: 12px;
        border: 2px solid #ddd;
        border-radius: 4px;
        font-family: monospace;
      }

      .form-actions {
        display: flex;
        gap: 10px;
      }

      .btn-generate {
        background: #2196f3;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 4px;
        cursor: pointer;
      }

      .btn-generate:disabled {
        background: #bdbdbd;
        cursor: not-allowed;
      }

      .error-message {
        background: #ffebee;
        color: #c62828;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
      }

      .success-message {
        background: #e8f5e8;
        color: #2e7d32;
        padding: 15px;
        border-radius: 4px;
        margin: 10px 0;
      }

      .results {
        margin-top: 20px;
        background: #2d2d2d;
        color: #f8f8f2;
        padding: 20px;
        border-radius: 8px;
      }

      .results pre {
        background: none;
        padding: 0;
        margin: 10px 0;
        overflow-x: auto;
      }

      .result-actions {
        margin-top: 15px;
        display: flex;
        gap: 10px;
      }

      button {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }

      .btn-login {
        background: #4caf50;
        color: white;
      }

      .btn-logout {
        background: #f44336;
        color: white;
      }

      .btn-upgrade {
        background: #ff9800;
        color: white;
      }
    `,
  ],
})
export class EnhancedAIGeneratorComponent implements OnDestroy {
  generationForm: any; // 实际使用 FormGroup
  isGenerating = false;
  generatedCode = '';
  errorMessage = '';
  successMessage = '';
  quotaInfo: { used: number; limit: number; remaining: number } | null = null;

  authState$: Observable<any> = this.mockAuthService.authState$;
  isAuthenticated = false;
  currentUser: User | null = null;

  private subscriptions: Subscription[] = [];

  constructor(
    private authenticatedAIService: AuthenticatedAIService,
    private mockAuthService: MockAuthService
  ) {
    this.initializeComponent();
  }

  private initializeComponent(): void {
    // 初始化表单（实际使用 FormBuilder）
    this.generationForm = {
      valid: true,
      value: { prompt: '' },
    };

    // 订阅认证状态
    const authSub = this.mockAuthService.authState$.subscribe((state) => {
      this.isAuthenticated = state.isAuthenticated;
      this.currentUser = state.user;

      if (this.isAuthenticated) {
        this.loadUserQuota();
      }
    });

    this.subscriptions.push(authSub);

    // 获取初始认证状态
    this.authState$ = this.mockAuthService.authState$;
  }

  get hasSufficientQuota(): boolean {
    return this.quotaInfo ? this.quotaInfo.remaining > 0 : false;
  }

  async generateCode(): Promise<void> {
    if (!this.generationForm.value.prompt.trim()) {
      this.errorMessage = '请输入代码需求描述';
      return;
    }

    this.isGenerating = true;
    this.errorMessage = '';
    this.successMessage = '';

    try {
      const response = await this.authenticatedAIService.generateCode({
        prompt: this.generationForm.value.prompt,
      });

      this.generatedCode = response.code;
      this.successMessage = `代码生成成功！耗时 ${response.processingTime.toFixed(2)} 秒`;

      // 更新配额显示
      this.loadUserQuota();
    } catch (error: any) {
      this.errorMessage = error.message || '代码生成失败';
    } finally {
      this.isGenerating = false;
    }
  }

  private loadUserQuota(): void {
    this.quotaInfo = this.authenticatedAIService.getUserQuotaInfo();
  }

  async login(): Promise<void> {
    // 模拟登录流程
    try {
      await this.mockAuthService
        .login({
          username: 'testuser',
          password: 'password',
        })
        .toPromise()
        .catch((error) => {
          // 处理 Observable 转 Promise 后的错误
          throw error;
        });

      this.successMessage = '登录成功！现在可以使用 AI 代码生成功能了。';
    } catch (error) {
      this.errorMessage = '登录失败';
    }
  }

  logout(): void {
    this.mockAuthService.logout();
    this.clearResults();
    this.successMessage = '已退出登录';
  }

  upgradeAccount(): void {
    alert('账户升级功能即将上线！');
  }

  clearResults(): void {
    this.generatedCode = '';
    this.errorMessage = '';
    this.successMessage = '';
    // 实际使用时重置表单
    // this.generationForm.reset();
  }

  copyCode(): void {
    void navigator.clipboard
      .writeText(this.generatedCode)
      .then(() => {
        this.successMessage = '代码已复制到剪贴板';
      })
      .catch((error) => {
        this.errorMessage = '复制失败：' + (error as Error).message;
      });
  }

  downloadCode(): void {
    const blob = new Blob([this.generatedCode], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `generated_code_${Date.now()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }
}
