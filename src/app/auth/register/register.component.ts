import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { Router, RouterModule } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

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
