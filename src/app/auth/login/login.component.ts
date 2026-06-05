import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

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
    private router: Router
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
        const errMsg =
          (error as { message?: string })?.message ?? '登录失败，请检查邮箱和密码';
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
}
