import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { RegisterRequest } from '../../core/models/auth.models';
import { USER_TYPE_CONFIG, UserType, UserTypeGroup } from '../../core/models/group.models';
import { AuthService } from '../../core/services/auth.service';
import { GroupService } from '../../core/services/group.service';

// 注册方式
type RegisterMethod = 'email' | 'phone' | 'social';

@Component({
  selector: 'app-register-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="modal-overlay" (click)="onClose()">
      <div class="modal-container" (click)="$event.stopPropagation()">
        <button class="close-btn" (click)="onClose()">×</button>

        <div class="modal-header">
          <h2 class="modal-title">注册 MatuX</h2>
          <p class="modal-subtitle">开启你的AI学习之旅</p>
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
            <span class="coming-soon">即将</span>
          </button>
          <button
            class="method-tab"
            [class.active]="registerMethod === 'social'"
            (click)="selectMethod('social')"
            [class.disabled]="true"
          >
            <span class="tab-icon">🔗</span>
            社交账号
            <span class="coming-soon">即将</span>
          </button>
        </div>

        <!-- 用户类型选择 -->
        <div class="user-type-selection" *ngIf="!userData.userType">
          <h3 class="selection-title">请选择您的身份</h3>

          <!-- 快速体验入口 - 可折叠 -->
          <div class="quick-experience" (click)="toggleQuickExperience()">
            <span class="quick-toggle-icon">{{ quickExperienceExpanded ? '▼' : '▶' }}</span>
            <span class="quick-hint">快速体验入口</span>
          </div>
          <div class="quick-accounts" *ngIf="quickExperienceExpanded">
            <button
              *ngFor="let account of mockAccounts"
              class="quick-account-btn"
              (click)="onMockLogin(account.type)"
            >
              <span class="quick-icon">{{ account.icon }}</span>
              <span class="quick-label">{{ account.label }}</span>
            </button>
          </div>

          <!-- 个人用户 -->
          <div class="type-group">
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
              <a (click)="$event.stopPropagation()" href="/marketing/terms" target="_blank"
                >服务条款</a
              >
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
          <p class="social-divider">或使用以下方式注册</p>
          <div class="social-buttons-grid">
            <!-- GitHub - 已支持 -->
            <button class="social-btn github" (click)="registerWithGitHub()" title="GitHub 注册">
              <svg class="social-icon" viewBox="0 0 24 24" width="18" height="18">
                <path
                  fill="currentColor"
                  d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
                />
              </svg>
            </button>
            <!-- 微信 - 预留 -->
            <button class="social-btn wechat disabled" title="微信注册即将上线" disabled>
              <svg class="social-icon" viewBox="0 0 24 24" width="18" height="18">
                <path
                  fill="currentColor"
                  d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.045c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.03-.406-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.969-.982z"
                />
              </svg>
              <span class="coming-soon">即将</span>
            </button>
            <!-- Google - 预留 -->
            <button class="social-btn google disabled" title="Google 注册即将上线" disabled>
              <svg class="social-icon" viewBox="0 0 24 24" width="18" height="18">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span class="coming-soon">即将</span>
            </button>
            <!-- Facebook - 预留 -->
            <button class="social-btn facebook disabled" title="Facebook 注册即将上线" disabled>
              <svg class="social-icon" viewBox="0 0 24 24" width="18" height="18">
                <path
                  fill="#1877F2"
                  d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
                />
              </svg>
              <span class="coming-soon">即将</span>
            </button>
            <!-- X (Twitter) - 预留 -->
            <button class="social-btn x disabled" title="X 注册即将上线" disabled>
              <svg class="social-icon" viewBox="0 0 24 24" width="18" height="18">
                <path
                  fill="currentColor"
                  d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
                />
              </svg>
              <span class="coming-soon">即将</span>
            </button>
          </div>
        </div>

        <div class="login-link" *ngIf="!successMessage">
          <span>已有账号？</span>
          <a (click)="$event.stopPropagation(); onLoginClick()">立即登录</a>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 400;
        padding: 16px;
        animation: fadeIn 0.3s ease;
      }
      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      .modal-container {
        background: white;
        border-radius: 16px;
        padding: 32px;
        width: 100%;
        max-width: 480px;
        max-height: 90vh;
        overflow-y: auto;
        position: relative;
        animation: slideUp 0.3s ease;
      }
      @keyframes slideUp {
        from {
          transform: translateY(20px);
          opacity: 0;
        }
        to {
          transform: translateY(0);
          opacity: 1;
        }
      }

      .close-btn {
        position: absolute;
        top: 16px;
        right: 16px;
        width: 32px;
        height: 32px;
        border: none;
        background: #f5f5f7;
        border-radius: 50%;
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #86868b;
        transition: all 0.3s;
      }
      .close-btn:hover {
        background: #e5e5ea;
        color: #1d1d1f;
      }

      .modal-header {
        text-align: center;
        margin-bottom: 24px;
      }
      .modal-title {
        font-size: 24px;
        font-weight: 700;
        color: #1d1d1f;
        margin-bottom: 8px;
      }
      .modal-subtitle {
        font-size: 14px;
        color: #86868b;
      }

      /* 注册方式标签 */
      .method-tabs {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
        border-bottom: 2px solid #f0f0f0;
        padding-bottom: 8px;
      }
      .method-tab {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        padding: 10px 6px;
        background: none;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        color: #86868b;
        position: relative;
        font-size: 12px;
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
        font-size: 18px;
      }
      .coming-soon {
        position: absolute;
        top: -4px;
        right: -4px;
        font-size: 9px;
        background: #ffa500;
        color: white;
        padding: 1px 4px;
        border-radius: 6px;
      }

      /* 用户类型选择 */
      .user-type-selection {
        margin-bottom: 16px;
        max-height: 280px;
        overflow-y: auto;
      }
      .selection-title {
        font-size: 14px;
        font-weight: 600;
        color: #3a3a3c;
        margin-bottom: 12px;
        text-align: center;
      }
      .type-group {
        margin-bottom: 12px;
      }
      .type-group-title {
        font-size: 12px;
        font-weight: 500;
        color: #86868b;
        margin-bottom: 8px;
      }
      .type-cards {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
      }
      .type-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 12px 8px;
        border: 2px solid #e5e5ea;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
      }
      .type-card:hover {
        border-color: #f5576c;
        background: #fff5f6;
      }
      .type-icon {
        font-size: 24px;
        margin-bottom: 4px;
      }
      .type-name {
        font-size: 13px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 2px;
      }
      .type-desc {
        font-size: 11px;
        color: #86868b;
      }

      /* 已选类型 */
      .selected-type {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 16px;
        padding: 10px;
        background: #f5f5f7;
        border-radius: 8px;
      }
      .selected-badge {
        padding: 4px 12px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
      }
      .change-type-btn {
        background: none;
        border: none;
        color: #f5576c;
        font-size: 12px;
        cursor: pointer;
        text-decoration: underline;
      }

      .register-form {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .form-label {
        font-size: 13px;
        font-weight: 500;
        color: #3a3a3c;
      }
      .required {
        color: #f5576c;
        margin-left: 2px;
      }
      .form-input,
      .form-select {
        padding: 12px 14px;
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        font-size: 14px;
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
        margin: 6px 0;
      }
      .checkbox-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #3a3a3c;
        cursor: pointer;
      }
      .checkbox-label a {
        color: #f5576c;
        text-decoration: none;
        cursor: pointer;
      }
      .error-alert,
      .success-alert {
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
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
        padding: 12px 20px;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .register-button:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
      }
      .register-button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .loading-spinner {
        width: 18px;
        height: 18px;
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

      /* 快速体验入口 */
      .quick-experience {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        cursor: pointer;
        user-select: none;
        margin-bottom: 16px;
        color: #007bff;
        font-size: 13px;
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
        gap: 6px;
        margin-bottom: 16px;
      }

      .quick-account-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 10px 6px;
        border: 1px solid #f5576c;
        border-radius: 8px;
        background: white;
        font-size: 11px;
        color: #3a3a3c;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      .quick-account-btn:hover {
        background: #f5576c;
        color: white;
        transform: translateY(-2px);
      }

      .quick-icon {
        font-size: 20px;
      }

      .quick-label {
        font-weight: 600;
      }

      /* 预留提示 */
      .reserved-notice {
        text-align: center;
        padding: 30px 15px;
      }
      .notice-icon {
        font-size: 36px;
        margin-bottom: 12px;
      }
      .reserved-notice h3 {
        font-size: 16px;
        color: #1d1d1f;
        margin-bottom: 6px;
      }
      .reserved-notice p {
        color: #86868b;
        font-size: 13px;
      }
      .social-preview {
        display: flex;
        justify-content: center;
        gap: 8px;
        margin-top: 16px;
        flex-wrap: wrap;
      }
      .social-badge {
        padding: 6px 12px;
        border-radius: 14px;
        font-size: 11px;
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
        margin-top: 16px;
      }
      .social-divider {
        text-align: center;
        color: #86868b;
        font-size: 12px;
        margin: 12px 0;
        position: relative;
      }
      .social-divider::before,
      .social-divider::after {
        content: '';
        position: absolute;
        top: 50%;
        width: 25%;
        height: 1px;
        background: #e5e5ea;
      }
      .social-divider::before {
        left: 0;
      }
      .social-divider::after {
        right: 0;
      }
      .social-buttons-grid {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
      }
      .social-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border: 1px solid #d2d2d7;
        border-radius: 10px;
        background: white;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
      }
      .social-btn:hover:not(.disabled) {
        background: #f5f5f7;
        border-color: #f5576c;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }
      .social-btn.disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background: #f9f9f9;
      }
      .social-btn .coming-soon {
        position: absolute;
        top: -6px;
        right: -6px;
        font-size: 8px;
        background: #ffa500;
        color: white;
        padding: 1px 4px;
        border-radius: 6px;
        white-space: nowrap;
      }
      .social-icon {
        color: #333;
      }
      .login-link {
        text-align: center;
        margin-top: 16px;
        font-size: 13px;
        color: #86868b;
      }
      .login-link a {
        color: #f5576c;
        text-decoration: none;
        font-weight: 500;
        margin-left: 4px;
        cursor: pointer;
      }

      @media (max-width: 767px) {
        .modal-container {
          max-width: 100%;
          padding: 24px 16px;
        }

        .modal-title {
          font-size: 20px;
        }

        .type-cards {
          grid-template-columns: repeat(2, 1fr);
        }
      }
    `,
  ],
})
export class RegisterModalComponent {
  @Output() close = new EventEmitter<void>();
  @Output() loginClick = new EventEmitter<void>();

  UserType = UserType;
  UserTypeGroup = UserTypeGroup;

  registerMethod: RegisterMethod = 'email';

  // 模拟账号列表
  mockAccounts = [
    { type: 'student', label: '学生', icon: '🎓', description: '体验学生端功能' },
    { type: 'parent', label: '家长', icon: '👨‍👩‍👧', description: '体验家长端功能' },
    { type: 'teacher', label: '教师', icon: '👨‍🏫', description: '体验教师端功能' },
  ];

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
    if (method === 'phone' || method === 'social') return;
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
        this.successMessage = '注册成功！';
        setTimeout(() => {
          this.onClose();
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
  loginWithMock(userType: 'student' | 'teacher' | 'parent'): void {
    this.loading = true;
    this.errorMessage = '';

    this.authService.mockLogin(userType).subscribe({
      next: () => {
        setTimeout(() => {
          this.loading = false;
          this.onClose();
          void this.router.navigate(['/user']);
        }, 500);
      },
      error: () => {
        this.errorMessage = '模拟登录失败';
        this.loading = false;
      },
    });
  }

  /**
   * 模板调用辅助方法 - 处理类型断言
   */
  onMockLogin(type: string): void {
    this.loginWithMock(type as 'student' | 'teacher' | 'parent');
  }

  onClose(): void {
    this.close.emit();
  }

  onLoginClick(): void {
    this.close.emit();
    this.loginClick.emit();
  }
}
