import { Component, NgZone } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';

import { AdminAuthService } from './admin-auth.service';

@Component({
  selector: 'app-admin-login',
  standalone: false,
  templateUrl: './admin-login.component.html',
  styleUrls: ['./admin-login.component.scss'],
})
export class AdminLoginComponent {
  loginForm: FormGroup;
  isLoading = false;
  useTestAccount = false; // 默认不使用测试账号，需要手动输入

  // 测试账号信息
  readonly TEST_ACCOUNT = {
    username: 'admin@testorg.com',
    password: 'TestAdmin123!',
    label: '测试专用账号',
  };

  constructor(
    private fb: FormBuilder,
    private adminAuthService: AdminAuthService,
    private router: Router,
    private snackBar: MatSnackBar,
    private ngZone: NgZone
  ) {
    // 从 localStorage 读取上次保存的凭据
    const savedUsername = localStorage.getItem('admin_username');
    const savedPassword = localStorage.getItem('admin_password');

    this.loginForm = this.fb.group({
      // eslint-disable-next-line @typescript-eslint/unbound-method
      username: [savedUsername ?? '', [Validators.required]],
      // eslint-disable-next-line @typescript-eslint/unbound-method
      password: [savedPassword ?? '', [Validators.required]],
      rememberMe: [!!savedUsername], // 如果有保存的用户名则勾选
      useTestAccount: [this.useTestAccount], // 测试账号选项（默认禁用）
    });

    // 监听测试账号选项变化
    this.loginForm.get('useTestAccount')?.valueChanges.subscribe((useTest: boolean) => {
      if (useTest) {
        this.loginForm.patchValue({
          username: this.TEST_ACCOUNT.username,
          password: this.TEST_ACCOUNT.password,
        });
      }
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.isLoading = true;
    const { username, password, rememberMe } = this.loginForm.value as {
      username: string;
      password: string;
      rememberMe: boolean;
    };

    this.adminAuthService.login(username, password, rememberMe).subscribe({
      next: () => {
        // 如果勾选了记住我，保存凭据
        if (rememberMe) {
          localStorage.setItem('admin_username', username);
          localStorage.setItem('admin_password', password);
        } else {
          // 否则清除保存的凭据
          localStorage.removeItem('admin_username');
          localStorage.removeItem('admin_password');
        }

        this.snackBar.open('登录成功！', '关闭', {
          duration: 2000,
          panelClass: ['success-snackbar'],
        });

        // ✅ 等待 500ms 确保用户信息已加载完成后再跳转
        setTimeout(() => {
          this.navigateToDashboard();
        }, 500);
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      error: (error: any) => {
        this.isLoading = false;
        const errorMessage: string =
          (error as { error?: { message?: string } })?.error?.message ??
          '登录失败，请检查用户名和密码';
        this.snackBar.open(errorMessage, '关闭', {
          duration: 4000,
          panelClass: ['error-snackbar'],
        });
      },
    });
  }

  /**
   * 根据用户角色跳转到对应的仪表板
   */
  private navigateToDashboard(): void {
    // 获取当前用户信息 (从 adminAuthService)
    const adminUser = this.adminAuthService.getCurrentUser();

    // 根据角色跳转到不同的仪表板
    if (
      adminUser?.role === 'manager'
      // || adminUser?.role === 'organization_admin' || adminUser?.role === 'org_admin'  // 已解耦到 OpenMTEduInst 项目
    ) {
      // 机构管理员跳转到机构管理后台（已解耦）
      // const organizationId =
      //   (adminUser as unknown as { organization_id?: number }).organization_id ??
      //   (adminUser as { organizationId?: number }).organizationId;
      // if (organizationId) {
      //   void this.router.navigate(['/management/organization', organizationId, 'dashboard']);
      // } else {
      //   void this.router.navigate(['/management/organization', 1, 'dashboard']);
      // }
      void this.router.navigate(['/admin/dashboard']);
    } else {
      // 其他管理员跳转到 admin dashboard
      void this.router.navigate(['/admin/dashboard']);
    }
  }
}
