import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router, RouterModule } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { LoginRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';

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
        void this.router.navigate(['/user/dashboard']);
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
   * 一键登录：使用 init_test_data 创建的测试管理员账号
   * 后端 OAuth2 token 端点：/api/v1/auth/token（form-urlencoded）
   * username: test_admin / password: TestAdmin123!
   * 仅在开发/演示环境使用
   */
  loginAsTestUser(): void {
    if (this.loading) return;
    this.loading = true;
    this.errorMessage = '';

    const body = new URLSearchParams();
    body.set('username', 'test_admin');
    body.set('password', 'TestAdmin123!');
    const headers = new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' });

    // Electron 桌面端使用完整 URL
    const API_BASE = 'http://localhost:8000';
    firstValueFrom(
      this.http.post<{ access_token: string; token_type: string }>(
        `${API_BASE}/api/v1/auth/token`,
        body.toString(),
        { headers }
      )
    )
      .then((res) => {
        // 写入 token + 触发 isAuthenticated$ = true
        this.authService.setAccessTokenForTesting(res.access_token);
        console.log('登录成功，token:', res.access_token);
        // 直接跳转仪表盘
        void this.router.navigate(['/user/dashboard']);
      })
      .catch((err: unknown) => {
        const e = err as { error?: { detail?: string }; message?: string };
        this.errorMessage = e?.error?.detail ?? e?.message ?? '测试账号登录失败';
        this.loading = false;
      });
  }
}
