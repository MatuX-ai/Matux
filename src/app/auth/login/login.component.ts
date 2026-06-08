import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSelectModule } from '@angular/material/select';
import { Router, RouterModule } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LoginRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { ROUTES } from '../../routes.const';

// 测试账号配置（仅用于演示，敏感信息不应在前端硬编码）
interface TestAccount {
  username: string;
  password: string;
  role: string;
  description: string;
  icon: string;
}

const TEST_ACCOUNTS: TestAccount[] = [
  {
    username: 'test_admin',
    password: 'TestAdmin123!',
    role: '管理员',
    description: '完整管理权限',
    icon: 'admin_panel_settings',
  },
  {
    username: 'test_teacher',
    password: 'TestTeacher123!',
    role: '教师',
    description: '教学管理权限',
    icon: 'school',
  },
  {
    username: 'test_student',
    password: 'TestStudent123!',
    role: '学生',
    description: '学习体验权限',
    icon: 'person',
  },
];

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCheckboxModule,
    MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  credentials: LoginRequest = {
    email: '',
    password: '',
  };
  rememberMe = false;
  loading = false;
  errorMessage = '';
  hidePassword = true;

  // 路由常量供模板使用
  readonly ROUTES = ROUTES;

  constructor(
    private authService: AuthService,
    private router: Router,
    private http: HttpClient
  ) {
    // 恢复记住我的设置
    this.rememberMe = this.authService.isRememberMe();
  }

  onLogin(): void {
    if (this.loading) return;

    this.loading = true;
    this.errorMessage = '';

    this.authService.setRememberMe(this.rememberMe);

    this.authService.signIn(this.credentials).subscribe({
      next: () => {
        void this.router.navigate([ROUTES.USER.DASHBOARD]);
      },
      error: (error: unknown) => {
        const errMsg = (error as { message?: string })?.message ?? '登录失败，请检查邮箱和密码';
        this.errorMessage = errMsg;
        this.loading = false;
      },
    });
  }

  // OAuth 登录方法
  loginWithQQ(): void {
    this.authService.signInWithQQ();
  }

  loginWithWechat(): void {
    this.authService.signInWithWeChat();
  }

  loginWithGoogle(): void {
    this.authService.signInWithGoogle();
  }

  loginWithGithub(): void {
    this.authService.signInWithGitHub();
  }

  /**
   * 一键登录：使用测试学生账号快速登录
   * 仅在开发/演示环境可用
   * 
   * @deprecated 生产环境应禁用此功能
   */
  loginAsTestUser(): void {
    // 生产环境禁用
    if (environment.production) {
      this.errorMessage = '演示功能在生产环境不可用';
      return;
    }

    if (this.loading) return;
    this.loading = true;
    this.errorMessage = '';

    // 使用 TEST_ACCOUNTS 中的学生账号
    const studentAccount = TEST_ACCOUNTS.find((a) => a.role === '学生') ?? TEST_ACCOUNTS[2];
    
    const body = new URLSearchParams();
    body.set('username', studentAccount.username);
    body.set('password', studentAccount.password);
    const headers = new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' });

    // 使用 environment 配置的 API URL
    const API_BASE = environment.apiUrl || 'http://localhost:8000';
    
    // 并行执行：获取 token + 获取用户信息
    firstValueFrom(
      this.http.post<{ access_token: string; token_type: string }>(
        `${API_BASE}/api/v1/auth/token`,
        body.toString(),
        { headers }
      )
    )
      .then(async (res) => {
        // 使用标准登录流程
        this.authService.signIn({
          email: studentAccount.username,
          password: studentAccount.password,
        }).subscribe({
          next: () => {
            void this.router.navigate([ROUTES.USER.DASHBOARD]);
          },
          error: () => {
            // signIn 失败时使用 token 直接登录（仅开发环境）
            console.warn('[Dev] 标准登录失败，尝试 token 直接登录');
            this.authService.setAccessTokenForTesting(res.access_token);
            void this.router.navigate([ROUTES.USER.DASHBOARD]);
          },
        });
        this.loading = false;
      })
      .catch((err: unknown) => {
        const e = err as { error?: { detail?: string }; message?: string };
        this.errorMessage = e?.error?.detail ?? e?.message ?? '测试账号登录失败';
        this.loading = false;
      });
  }
}
