import { CommonModule } from '@angular/common';
import { Component, ViewChild } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { Router, RouterModule } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ROUTES } from '../../routes.const';

/** 密码规则：与后端 auth_routes.RegisterRequest.validate_password_strength 对齐 */
const PASSWORD_MIN_LENGTH = 8;
const USERNAME_MIN_LENGTH = 3;

/**
 * 校验密码强度：至少 8 字符，包含字母和数字
 * 与后端 `backend/routes/auth_routes.py` 中 Pydantic validator 一致
 */
function validatePasswordStrength(pwd: string): string | null {
  if (!pwd) return '密码不能为空';
  if (pwd.length < PASSWORD_MIN_LENGTH) return `密码至少需要 ${PASSWORD_MIN_LENGTH} 个字符`;
  if (!/[A-Za-z]/.test(pwd)) return '密码必须包含字母';
  if (!/\d/.test(pwd)) return '密码必须包含数字';
  return null;
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, RouterModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
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

  // 模板驱动表单校验状态
  usernameInvalid = false;
  emailInvalid = false;
  passwordInvalid = false;
  usernameError = '';
  emailError = '';
  passwordError = '';

  // 路由常量供模板使用
  readonly ROUTES = ROUTES;

  userData = {
    username: '',
    email: '',
    password: '',
  };

  @ViewChild('registerForm') registerForm?: NgForm;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  get confirmPasswordMismatch(): boolean {
    return this.confirmPasswordTouched && this.confirmPassword !== this.userData.password;
  }

  get isFormValid(): boolean {
    return (
      !!this.userData.username &&
      this.userData.username.length >= USERNAME_MIN_LENGTH &&
      !!this.userData.email &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.userData.email) &&
      validatePasswordStrength(this.userData.password) === null &&
      this.confirmPassword === this.userData.password &&
      this.agreeTerms
    );
  }

  /** 校验用户名（模板失焦时调用） */
  validateUsername(): void {
    this.usernameInvalid = !this.userData.username;
    if (!this.userData.username) {
      this.usernameError = '用户名不能为空';
    } else if (this.userData.username.length < USERNAME_MIN_LENGTH) {
      this.usernameError = `用户名至少 ${USERNAME_MIN_LENGTH} 个字符`;
    } else {
      this.usernameError = '';
      this.usernameInvalid = false;
    }
  }

  /** 校验邮箱（模板失焦时调用） */
  validateEmail(): void {
    if (!this.userData.email) {
      this.emailInvalid = true;
      this.emailError = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.userData.email)) {
      this.emailInvalid = true;
      this.emailError = '请输入有效的邮箱地址';
    } else {
      this.emailInvalid = false;
      this.emailError = '';
    }
  }

  /** 校验密码（模板失焦或注册时调用） */
  validatePassword(): void {
    const err = validatePasswordStrength(this.userData.password);
    if (err) {
      this.passwordInvalid = true;
      this.passwordError = err;
    } else {
      this.passwordInvalid = false;
      this.passwordError = '';
    }
  }

  onRegister(): void {
    this.usernameInvalid = !this.userData.username;
    this.validateUsername();
    this.validateEmail();
    this.validatePassword();

    if (
      this.usernameInvalid ||
      this.emailInvalid ||
      this.passwordInvalid ||
      this.userData.password !== this.confirmPassword ||
      !this.agreeTerms
    ) {
      this.confirmPasswordTouched = true;
      if (this.userData.password !== this.confirmPassword) {
        this.errorMessage = '两次输入的密码不一致';
      } else {
        this.errorMessage = '请检查表单填写';
      }
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
          void this.router.navigate([ROUTES.USER.DASHBOARD]);
        }, 1500);
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage = (error as Error).message || '注册失败，请稍后重试';
      },
    });
  }
}
