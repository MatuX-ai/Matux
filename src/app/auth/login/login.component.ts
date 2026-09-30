import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { environment } from '../../../environments/environment';
import { LoginRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
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

  /** 生产环境标志：从 environment.production 读取，模板用于隐藏测试按钮 */
  readonly isProduction = environment.production;

  // 路由常量供模板使用
  readonly ROUTES = ROUTES;

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    public i18n: I18nService
  ) {
    // 恢复记住我的设置
    this.rememberMe = this.authService.isRememberMe();

    // 【P1 修复】从 URL ?returnUrl=xxx 中读取并暂存,登录成功后回跳
    const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
    if (returnUrl && returnUrl !== '/auth/login') {
      try {
        sessionStorage.setItem('pre_login_return_url', returnUrl);
      } catch {
        // sessionStorage 不可用时静默失败
      }
    }
  }

  /**
   * 【P1 修复】登录成功后跳转: 优先 returnUrl,否则 dashboard
   */
  private navigateAfterLogin(): void {
    const sessionReturnUrl = sessionStorage.getItem('pre_login_return_url');
    if (sessionReturnUrl) {
      sessionStorage.removeItem('pre_login_return_url');
      void this.router.navigateByUrl(sessionReturnUrl);
    } else {
      void this.router.navigate([ROUTES.USER.DASHBOARD]);
    }
  }

  onLogin(): void {
    if (this.loading) return;

    this.loading = true;
    this.errorMessage = '';

    this.authService.setRememberMe(this.rememberMe);

    this.authService.signIn(this.credentials).subscribe({
      next: () => {
        this.navigateAfterLogin();
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

    // 直接调用标准登录流程（单次 HTTP 请求）
    this.authService.setRememberMe(true);
    this.authService
      .signIn({
        email: studentAccount.username,
        password: studentAccount.password,
      })
      .subscribe({
        next: () => {
          this.loading = false;
          this.navigateAfterLogin();
        },
        error: (error: unknown) => {
          const errMsg = (error as { message?: string })?.message ?? '测试账号登录失败';
          this.errorMessage = errMsg;
          this.loading = false;
        },
      });
  }
}
