import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';

import { RegisterRequest } from '../../core/models/auth.models';
import { USER_TYPE_CONFIG, UserType, UserTypeGroup } from '../../core/models/group.models';
import { AuthService } from '../../core/services/auth.service';
import { GroupService } from '../../core/services/group.service';
import {
  AdminMockDialogComponent,
  AdminType,
} from '../admin-mock-dialog/admin-mock-dialog.component';

// 注册方式
type RegisterMethod = 'email' | 'phone' | 'social';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, AdminMockDialogComponent],
  template: `
    <div class="register-container">
      <div class="register-card">
        <div class="register-header">
          <h1 class="register-title">注册 MatuX</h1>
          <p class="register-subtitle">开启你的AI学习之旅</p>
        </div>

        <!-- 注册方式选择 -->
        <div class="method-tabs" *ngIf="!userData.userType">
          <button
            class="method-tab"
            [class.active]="registerMethod === 'email'"
            (click)="selectMethod('email')"
          >
            <span class="tab-icon">📧</span>
            邮箱注册
          </button>
          <button
            class="method-tab"
            [class.active]="registerMethod === 'phone'"
            (click)="selectMethod('phone')"
            [class.disabled]="true"
          >
            <span class="tab-icon">📱</span>
            手机注册
            <span class="coming-soon">即将上线</span>
          </button>
          <button
            class="method-tab"
            [class.active]="registerMethod === 'social'"
            (click)="selectMethod('social')"
            [class.disabled]="true"
          >
            <span class="tab-icon">🔗</span>
            社交账号
            <span class="coming-soon">即将上线</span>
          </button>
        </div>

        <!-- 用户类型选择 -->
        <div class="user-type-selection">
          <h3 class="selection-title">请选择您的身份</h3>

          <!-- 快速体验入口 - 可折叠（始终显示） -->
          <div class="quick-experience" (click)="$event.stopPropagation(); toggleQuickExperience()">
            <span class="quick-toggle-icon">{{ quickExperienceExpanded ? '▼' : '▶' }}</span>
            <span class="quick-hint">快速体验入口</span>
          </div>
          <div class="quick-accounts" *ngIf="quickExperienceExpanded">
            <button
              *ngFor="let account of mockAccounts"
              class="quick-account-btn"
              (click)="$event.stopPropagation(); onMockLogin(account.type)"
            >
              <span class="quick-icon">{{ account.icon }}</span>
              <span class="quick-label">{{ account.label }}</span>
            </button>
          </div>

          <!-- 个人用户 -->
          <div class="type-group" *ngIf="!userData.userType">
            <h4 class="type-group-title">个人用户</h4>
            <div class="type-cards">
              <div class="type-card" (click)="selectUserType(UserType.STUDENT)">
                <span class="type-icon">🎓</span>
                <span class="type-name">学生</span>
                <span class="type-desc">开始学习AI课程</span>
              </div>
              <div class="type-card" (click)="selectUserType(UserType.PARENT)">
                <span class="type-icon">👨‍👩‍👧</span>
                <span class="type-name">家长</span>
                <span class="type-desc">陪伴孩子学习</span>
              </div>
            </div>
          </div>

          <!-- 机构用户 -->
          <div class="type-group">
            <h4 class="type-group-title">机构用户</h4>
            <div class="type-cards">
              <div class="type-card" (click)="selectUserType(UserType.TEACHER)">
                <span class="type-icon">👨‍🏫</span>
                <span class="type-name">教师</span>
                <span class="type-desc">教授AI课程</span>
              </div>
              <div class="type-card" (click)="selectUserType(UserType.ORG_ADMIN)">
                <span class="type-icon">🏢</span>
                <span class="type-name">机构负责人</span>
                <span class="type-desc">管理培训机构</span>
              </div>
            </div>
          </div>

          <!-- 教育机构 -->
          <div class="type-group">
            <h4 class="type-group-title">教育机构</h4>
            <div class="type-cards">
              <div class="type-card" (click)="selectUserType(UserType.SCHOOL_ADMIN)">
                <span class="type-icon">🏫</span>
                <span class="type-name">学校管理员</span>
                <span class="type-desc">管理学校账号</span>
              </div>
              <div class="type-card" (click)="selectUserType(UserType.EDUCATION_BUREAU)">
                <span class="type-icon">🏛️</span>
                <span class="type-name">教育局</span>
                <span class="type-desc">教育监管部门</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 邮箱注册表单 -->
        <form
          class="register-form"
          (ngSubmit)="onRegister()"
          #registerForm="ngForm"
          *ngIf="userData.userType && registerMethod === 'email'"
        >
          <div class="selected-type">
            <span class="selected-badge">{{ getSelectedTypeLabel() }}</span>
            <button type="button" class="change-type-btn" (click)="clearUserType()">更改</button>
          </div>

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
              maxlength="20"
              placeholder="请输入用户名"
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="email">邮箱地址 <span class="required">*</span></label>
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
          </div>

          <div class="form-group">
            <label class="form-label" for="password">密码 <span class="required">*</span></label>
            <input
              type="password"
              id="password"
              name="password"
              class="form-input"
              [(ngModel)]="userData.password"
              required
              minlength="6"
              placeholder="请输入密码（至少6位）"
            />
          </div>

          <div class="form-group">
            <label class="form-label" for="confirmPassword"
              >确认密码 <span class="required">*</span></label
            >
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              class="form-input"
              [(ngModel)]="confirmPassword"
              required
              placeholder="请再次输入密码"
            />
          </div>

          <!-- 学生/家长 - 年级选择 -->
          <div class="form-group" *ngIf="isPersonalUser()">
            <label class="form-label" for="grade">年级</label>
            <select
              id="grade"
              name="grade"
              class="form-select"
              [(ngModel)]="userData.grade"
              required
            >
              <option value="">请选择年级</option>
              <option value="小学一年级">小学一年级</option>
              <option value="小学二年级">小学二年级</option>
              <option value="小学三年级">小学三年级</option>
              <option value="小学四年级">小学四年级</option>
              <option value="小学五年级">小学五年级</option>
              <option value="小学六年级">小学六年级</option>
              <option value="初中一年级">初中一年级</option>
              <option value="初中二年级">初中二年级</option>
              <option value="初中三年级">初中三年级</option>
              <option value="高中一年级">高中一年级</option>
              <option value="高中二年级">高中二年级</option>
              <option value="高中三年级">高中三年级</option>
              <option value="大学">大学</option>
              <option value="在职">在职</option>
            </select>
          </div>

          <!-- 机构/学校用户 - 机构信息 -->
          <div class="form-group" *ngIf="isOrganizationUser()">
            <label class="form-label" for="organizationName"
              >{{ isEducationUser() ? '教育局/部门名称' : '机构名称' }}
              <span class="required">*</span></label
            >
            <input
              type="text"
              id="organizationName"
              name="organizationName"
              class="form-input"
              [(ngModel)]="userData.organizationName"
              [required]="isOrganizationUser()"
              [placeholder]="isEducationUser() ? '请输入教育局/部门名称' : '请输入机构名称'"
            />
          </div>

          <!-- 教师 - 机构选择 -->
          <div class="form-group" *ngIf="userData.userType === UserType.TEACHER">
            <label class="form-label" for="orgCode">机构邀请码（可选）</label>
            <input
              type="text"
              id="orgCode"
              name="orgCode"
              class="form-input"
              [(ngModel)]="userData.inviteCode"
              placeholder="如果有机构邀请码请填写"
            />
          </div>

          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" name="agreeTerms" [(ngModel)]="agreeTerms" required />
              <span>我已阅读并同意</span>
              <a routerLink="/marketing/terms" target="_blank">服务条款</a>
            </label>
          </div>

          <div class="error-alert" *ngIf="errorMessage">
            {{ errorMessage }}
          </div>

          <div class="success-alert" *ngIf="successMessage">
            {{ successMessage }}
          </div>

          <button
            type="submit"
            class="register-button"
            [disabled]="
              registerForm.invalid ||
              loading ||
              !agreeTerms ||
              userData.password !== confirmPassword
            "
          >
            <span *ngIf="!loading">立即注册</span>
            <span *ngIf="loading" class="loading-spinner"></span>
          </button>
        </form>

        <!-- 手机注册（预留） -->
        <div class="reserved-notice" *ngIf="registerMethod === 'phone' && !userData.userType">
          <div class="notice-icon">📱</div>
          <h3>手机注册即将上线</h3>
          <p>我们正在紧张开发中，敬请期待！</p>
          <p class="notice-hint">手机注册将支持快速登录、验证码登录等功能</p>
        </div>

        <!-- 社交账号注册（预留） -->
        <div class="reserved-notice" *ngIf="registerMethod === 'social' && !userData.userType">
          <div class="notice-icon">🔗</div>
          <h3>社交账号注册即将上线</h3>
          <p>我们正在紧张开发中，敬请期待！</p>
          <div class="social-preview">
            <span class="social-badge github">GitHub</span>
            <span class="social-badge google">Google</span>
            <span class="social-badge wechat">微信</span>
            <span class="social-badge qq">QQ</span>
          </div>
        </div>

        <!-- 社交登录按钮 -->
        <div class="social-login" *ngIf="!userData.userType && registerMethod === 'email'">
          <p class="social-divider">或</p>
          <button class="social-button github" (click)="registerWithGitHub()">
            <svg class="social-icon" viewBox="0 0 24 24">
              <path
                d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
              />
            </svg>
            GitHub 登录
          </button>
        </div>

        <div class="login-link">
          <span>已有账号？</span>
          <a routerLink="/auth/login">立即登录</a>
        </div>

        <!-- 模拟登录区域 -->
        <div class="mock-login-section" *ngIf="!userData.userType">
          <div class="mock-divider">
            <span>快速体验</span>
          </div>
          <p class="mock-hint">不想注册？直接点击下方账号体验</p>
          <div class="mock-accounts">
            <button
              *ngFor="let account of mockAccounts"
              class="mock-account-btn"
              (click)="onMockLogin(account.type)"
              [title]="account.description"
            >
              <span class="mock-icon">{{ account.icon }}</span>
              <span class="mock-label">{{ account.label }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 管理员模拟登录对话框 -->
    <app-admin-mock-dialog
      *ngIf="showAdminDialog"
      (close)="showAdminDialog = false"
      (loginSuccess)="onAdminLoginSuccess($event)"
    ></app-admin-mock-dialog>
  `,
  styles: [
    `
      .register-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 16px;
      }
      .register-card {
        background: white;
        border-radius: 16px;
        padding: 48px;
        width: 100%;
        max-width: 520px;
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

      /* 注册方式标签 */
      .method-tabs {
        display: flex;
        gap: 8px;
        margin-bottom: 24px;
        border-bottom: 2px solid #f0f0f0;
        padding-bottom: 12px;
      }
      .method-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 12px 8px;
        background: none;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #86868b;
        position: relative;
      }
      .method-tab:hover:not(.disabled) {
        background: #f5f5f7;
      }
      .method-tab.active {
        background: #fff5f6;
        color: #f5576c;
      }
      .method-tab.disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .tab-icon {
        font-size: 20px;
      }
      .method-tab span:not(.tab-icon):not(.coming-soon) {
        font-size: 13px;
        font-weight: 500;
      }
      .coming-soon {
        position: absolute;
        top: -6px;
        right: -4px;
        font-size: 10px;
        background: #ffa500;
        color: white;
        padding: 2px 6px;
        border-radius: 8px;
      }

      /* 用户类型选择 */
      .user-type-selection {
        margin-bottom: 24px;
      }
      .selection-title {
        font-size: 16px;
        font-weight: 600;
        color: #3a3a3c;
        margin-bottom: 20px;
        text-align: center;
      }
      .type-group {
        margin-bottom: 20px;
      }
      .type-group-title {
        font-size: 13px;
        font-weight: 500;
        color: #86868b;
        margin-bottom: 12px;
      }
      .type-cards {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
      }
      .type-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px 12px;
        border: 2px solid #e5e5ea;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
      }
      .type-card:hover {
        border-color: #f5576c;
        background: #fff5f6;
      }
      .type-icon {
        font-size: 28px;
        margin-bottom: 8px;
      }
      .type-name {
        font-size: 14px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 4px;
      }
      .type-desc {
        font-size: 12px;
        color: #86868b;
      }

      /* 已选类型 */
      .selected-type {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 20px;
        padding: 12px;
        background: #f5f5f7;
        border-radius: 8px;
      }
      .selected-badge {
        padding: 6px 16px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
      }
      .change-type-btn {
        background: none;
        border: none;
        color: #f5576c;
        font-size: 14px;
        cursor: pointer;
        text-decoration: underline;
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
      .required {
        color: #f5576c;
        margin-left: 2px;
      }
      .form-input,
      .form-select {
        padding: 14px 16px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        font-size: 16px;
        transition: all 0.3s ease;
        background: white;
      }
      .form-input:focus,
      .form-select:focus {
        outline: none;
        border-color: #f5576c;
        box-shadow: 0 0 0 3px rgba(245, 87, 108, 0.1);
      }
      .checkbox-group {
        margin: 8px 0;
      }
      .checkbox-label {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: #3a3a3c;
        cursor: pointer;
      }
      .checkbox-label a {
        color: #f5576c;
        text-decoration: none;
      }
      .checkbox-label a:hover {
        text-decoration: underline;
      }
      .error-alert,
      .success-alert {
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 14px;
      }
      .error-alert {
        background: #ffebee;
        border: 1px solid #ffcdd2;
        color: #c62828;
      }
      .success-alert {
        background: #e8f5e8;
        border: 1px solid #c8e6c9;
        color: #2e7d32;
      }
      .register-button {
        padding: 14px 24px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
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

      /* 预留提示 */
      .reserved-notice {
        text-align: center;
        padding: 40px 20px;
      }
      .notice-icon {
        font-size: 48px;
        margin-bottom: 16px;
      }
      .reserved-notice h3 {
        font-size: 18px;
        color: #1d1d1f;
        margin-bottom: 8px;
      }
      .reserved-notice p {
        color: #86868b;
        font-size: 14px;
      }
      .notice-hint {
        margin-top: 12px;
        padding: 12px;
        background: #f5f5f7;
        border-radius: 8px;
        font-size: 13px;
      }
      .social-preview {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-top: 20px;
        flex-wrap: wrap;
      }
      .social-badge {
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 500;
      }
      .social-badge.github {
        background: #24292e;
        color: white;
      }
      .social-badge.google {
        background: #4285f4;
        color: white;
      }
      .social-badge.wechat {
        background: #07c160;
        color: white;
      }
      .social-badge.qq {
        background: #12b7f5;
        color: white;
      }

      .social-login {
        margin-top: 20px;
      }
      .social-divider {
        text-align: center;
        color: #86868b;
        font-size: 14px;
        margin: 16px 0;
        position: relative;
      }
      .social-divider::before,
      .social-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 40%;
        height: 1px;
        background: #e5e5ea;
      }
      .social-divider::before {
        left: 0;
      }
      .social-divider::after {
        right: 0;
      }
      .social-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 12px 16px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        background: white;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
      }
      .social-button:hover {
        background: #f5f5f7;
        border-color: #f5576c;
      }
      .login-link {
        text-align: center;
        margin-top: 24px;
        font-size: 14px;
        color: #86868b;
      }
      .login-link a {
        color: #f5576c;
        text-decoration: none;
        font-weight: 500;
        margin-left: 4px;
      }
      @media (max-width: 767px) {
        .register-card {
          padding: 32px 24px;
        }
        .type-cards {
          grid-template-columns: 1fr;
        }
        .method-tabs {
          flex-direction: column;
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

      /* 快速体验入口 - 放在角色选择标题下 */
      .quick-experience {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        user-select: none;
        margin-bottom: 20px;
        color: #007bff;
        font-size: 14px;
      }

      .quick-experience:hover {
        text-decoration: underline;
      }

      .quick-toggle-icon {
        font-size: 10px;
      }

      .quick-hint {
        font-weight: 500;
      }

      .quick-accounts {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-bottom: 20px;
      }

      .quick-account-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 12px 8px;
        border: 1px solid #f5576c;
        border-radius: 8px;
        background: white;
        font-size: 12px;
        color: #3a3a3c;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .quick-account-btn:hover {
        background: #f5576c;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
      }

      .quick-icon {
        font-size: 24px;
      }

      .quick-label {
        font-weight: 600;
      }

      /* 模拟登录样式 */
      .mock-login-section {
        margin-top: 24px;
        padding-top: 24px;
        border-top: 1px dashed #e5e5ea;
      }

      .mock-divider {
        position: relative;
        text-align: center;
        margin-bottom: 12px;
      }

      .mock-divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #e5e5ea;
      }

      .mock-divider span {
        background: white;
        padding: 0 16px;
        color: #86868b;
        font-size: 13px;
        position: relative;
      }

      .mock-hint {
        text-align: center;
        color: #86868b;
        font-size: 13px;
        margin-bottom: 16px;
      }

      .mock-accounts {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
      }

      .mock-account-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 10px 12px;
        border: 1px solid #e5e5ea;
        border-radius: 8px;
        background: #fafafa;
        font-size: 13px;
        color: #3a3a3c;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .mock-account-btn:hover {
        border-color: #f5576c;
        background: #fff0f1;
        transform: translateY(-1px);
      }

      .mock-icon {
        font-size: 16px;
      }

      .mock-label {
        font-weight: 500;
      }

      @media (max-width: 767px) {
        .quick-accounts {
          grid-template-columns: repeat(2, 1fr);
        }
      }
    `,
  ],
})
export class RegisterComponent {
  UserType = UserType;
  UserTypeGroup = UserTypeGroup;

  registerMethod: RegisterMethod = 'email';

  // 模拟账号列表
  mockAccounts = [
    { type: 'student', label: '学生', icon: '🎓', description: '体验学生端功能' },
    { type: 'parent', label: '家长', icon: '👨‍👩‍👧', description: '体验家长端功能' },
    { type: 'teacher', label: '教师', icon: '👨‍🏫', description: '体验教师端功能' },
    { type: 'admin', label: '管理员', icon: '⚙️', description: '体验管理后台（多角色）' },
  ];

  // 显示管理员选择对话框
  showAdminDialog = false;

  // 快速体验入口展开状态
  quickExperienceExpanded = false;

  toggleQuickExperience(): void {
    this.quickExperienceExpanded = !this.quickExperienceExpanded;
  }

  userData: RegisterRequest & {
    userType?: UserType;
    userTypeGroup?: UserTypeGroup;
    grade?: string;
    organizationName?: string;
    inviteCode?: string;
  } = {
    username: '',
    email: '',
    password: '',
    grade: '',
  };
  confirmPassword = '';
  agreeTerms = false;
  loading = false;
  errorMessage = '';
  successMessage = '';

  constructor(
    private authService: AuthService,
    private groupService: GroupService,
    private router: Router
  ) {}

  selectMethod(method: RegisterMethod): void {
    if (method === 'phone' || method === 'social') {
      return; // 预留功能，暂不可用
    }
    this.registerMethod = method;
  }

  selectUserType(type: UserType): void {
    const config = USER_TYPE_CONFIG[type];
    this.userData.userType = type;
    this.userData.userTypeGroup = config.group;
  }

  clearUserType(): void {
    this.userData.userType = undefined;
    this.userData.userTypeGroup = undefined;
    this.userData.organizationName = undefined;
  }

  getSelectedTypeLabel(): string {
    if (!this.userData.userType) return '';
    return USER_TYPE_CONFIG[this.userData.userType]?.label || '';
  }

  isPersonalUser(): boolean {
    return this.userData.userTypeGroup === UserTypeGroup.PERSONAL;
  }

  isOrganizationUser(): boolean {
    return (
      this.userData.userTypeGroup === UserTypeGroup.ORGANIZATION ||
      this.userData.userTypeGroup === UserTypeGroup.EDUCATION
    );
  }

  isEducationUser(): boolean {
    return this.userData.userTypeGroup === UserTypeGroup.EDUCATION;
  }

  onRegister(): void {
    if (this.userData.password !== this.confirmPassword) {
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
          void this.router.navigate(['/dashboard']);
        }, 1500);
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage = (error as Error).message || '注册失败，请稍后重试';
      },
    });
  }

  registerWithGitHub(): void {
    void this.authService.signInWithGitHub();
  }

  /**
   * 模拟登录 - 快速体验登录效果
   */
  loginWithMock(userType: 'student' | 'parent' | 'teacher' | 'admin'): void {
    // 如果是管理员，显示选择对话框
    if (userType === 'admin') {
      this.showAdminDialog = true;
      return;
    }

    this.loading = true;
    this.errorMessage = '';

    this.authService.mockLogin(userType).subscribe({
      next: () => {
        setTimeout(() => {
          this.loading = false;
          this.redirectToUserCenter(userType);
        }, 500);
      },
      error: (_error) => {
        this.errorMessage = '模拟登录失败';
        this.loading = false;
      },
    });
  }

  /**
   * 模板调用辅助方法 - 处理类型断言
   */
  onMockLogin(type: string): void {
    if (type === 'admin') {
      // 管理员账号显示选择对话框
      this.showAdminDialog = true;
    } else {
      // 其他账号直接登录
      this.authService.mockLogin(type as 'student' | 'teacher' | 'parent').subscribe({
        next: () => {
          setTimeout(() => {
            void this.router.navigate(['/user']);
          }, 500);
        },
        error: (_error) => {
          console.error('模拟登录失败');
        },
      });
    }
  }

  /**
   * 根据用户类型跳转到对应的用户中心（已废弃，统一使用 onMockLogin）
   * @deprecated 使用 onMockLogin 代替
   */
  private redirectToUserCenter(_userType: 'student' | 'parent' | 'teacher' | 'admin'): void {
    // 所有用户都跳转到 /user，由 UserCenter 根据 userType 分发
    void this.router.navigate(['/user']);
  }

  /**
   * 处理管理员模拟登录成功
   */
  onAdminLoginSuccess(adminType: AdminType): void {
    // 关闭对话框
    this.showAdminDialog = false;
    // 显示成功提示
    const adminTypeLabel = this.getAdminTypeLabel(adminType);
    this.successMessage = `已使用${adminTypeLabel}账号登录成功！`;
    setTimeout(() => {
      this.successMessage = '';
      // ✅ 不再跳转到用户中心，由 AdminMockDialog 直接跳转到对应管理页面
    }, 1000);
  }

  /**
   * 获取管理员类型标签
   */
  private getAdminTypeLabel(type: AdminType): string {
    const labels: Record<AdminType, string> = {
      organization: '机构管理员',
      school: '学校管理员',
      education_bureau: '教育局管理员',
    };
    return labels[type] || '';
  }
}
