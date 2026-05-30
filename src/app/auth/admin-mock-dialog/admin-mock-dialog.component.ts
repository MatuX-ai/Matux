import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

export type AdminType = 'organization' | 'school' | 'education_bureau';

@Component({
  selector: 'app-admin-mock-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="dialog-overlay" (click)="onClose()">
      <div class="dialog-container" (click)="$event.stopPropagation()">
        <button class="close-btn" (click)="onClose()">×</button>

        <div class="dialog-header">
          <h2 class="dialog-title">选择管理员类型</h2>
          <p class="dialog-subtitle">请选择您要模拟的管理员角色</p>
        </div>

        <!-- 管理员类型选择 -->
        <div class="admin-type-selection">
          <div
            *ngFor="let admin of adminTypes"
            class="admin-type-card"
            [class.selected]="selectedAdminType === admin.type"
            (click)="selectAdminType(admin.type)"
          >
            <span class="admin-icon">{{ admin.icon }}</span>
            <div class="admin-info">
              <h3 class="admin-name">{{ admin.label }}</h3>
              <p class="admin-desc">{{ admin.description }}</p>
            </div>
            <div class="radio-indicator" *ngIf="selectedAdminType === admin.type">✓</div>
          </div>
        </div>

        <!-- 测试账号信息展示 -->
        <div class="test-account-section" *ngIf="selectedAdminType">
          <div class="section-divider"></div>

          <h3 class="section-title">测试账号信息</h3>

          <div class="account-info-card">
            <div class="info-row">
              <span class="info-label">📧 邮箱/用户名：</span>
              <code class="info-value">{{ testAccount.email }}</code>
            </div>
            <div class="info-row">
              <span class="info-label">🔑 密码：</span>
              <code class="info-value">{{ testAccount.password }}</code>
            </div>
            <div class="info-row">
              <span class="info-label">🏢 所属组织：</span>
              <span class="info-value">{{ testAccount.organization }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">🎫 许可证类型：</span>
              <span class="info-value badge cloud-hosted">{{ testAccount.licenseType }}</span>
            </div>
          </div>

          <div class="warning-notice">
            <span class="warning-icon">⚠️</span>
            <span class="warning-text">该测试账号仅用于开发测试环境，生产环境应禁用</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="dialog-actions">
          <button class="btn btn-cancel" (click)="onClose()">取消</button>
          <button
            class="btn btn-primary"
            (click)="onMockLogin()"
            [disabled]="!selectedAdminType || loading"
          >
            <span *ngIf="!loading">模拟登录</span>
            <span *ngIf="loading" class="loading-spinner"></span>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .dialog-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
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

      .dialog-container {
        background: white;
        border-radius: 16px;
        padding: 32px;
        width: 100%;
        max-width: 520px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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
        color: #86868b;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
      }

      .close-btn:hover {
        background: #e5e5ea;
        color: #1d1d1f;
      }

      .dialog-header {
        text-align: center;
        margin-bottom: 24px;
      }

      .dialog-title {
        font-size: 24px;
        font-weight: 700;
        color: #1d1d1f;
        margin-bottom: 8px;
      }

      .dialog-subtitle {
        font-size: 14px;
        color: #86868b;
      }

      .admin-type-selection {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 24px;
      }

      .admin-type-card {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        border: 2px solid #e5e5ea;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
      }

      .admin-type-card:hover {
        border-color: #f5576c;
        background: #fff5f6;
      }

      .admin-type-card.selected {
        border-color: #f5576c;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
      }

      .admin-type-card.selected .admin-name,
      .admin-type-card.selected .admin-desc {
        color: white;
      }

      .admin-icon {
        font-size: 32px;
        flex-shrink: 0;
      }

      .admin-info {
        flex: 1;
      }

      .admin-name {
        font-size: 16px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 4px;
      }

      .admin-desc {
        font-size: 13px;
        color: #86868b;
      }

      .radio-indicator {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #f5576c;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 16px;
        flex-shrink: 0;
      }

      .section-divider {
        height: 1px;
        background: #e5e5ea;
        margin: 24px 0;
      }

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #1d1d1f;
        margin-bottom: 16px;
      }

      .account-info-card {
        background: #f9fafb;
        border: 1px solid #e5e5ea;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
      }

      .info-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 12px;
        font-size: 14px;
      }

      .info-row:last-child {
        margin-bottom: 0;
      }

      .info-label {
        font-weight: 500;
        color: #3a3a3c;
        flex-shrink: 0;
        min-width: 120px;
      }

      .info-value {
        color: #1d1d1f;
        word-break: break-all;
      }

      .info-value code {
        background: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        border: 1px solid #e5e5ea;
      }

      .info-value.badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
      }

      .info-value.badge.cloud-hosted {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .warning-notice {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        font-size: 13px;
        color: #856404;
      }

      .warning-icon {
        font-size: 20px;
        flex-shrink: 0;
      }

      .dialog-actions {
        display: flex;
        gap: 12px;
        margin-top: 24px;
      }

      .btn {
        flex: 1;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .btn-cancel {
        background: #f5f5f7;
        color: #3a3a3c;
      }

      .btn-cancel:hover {
        background: #e5e5ea;
      }

      .btn-primary {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
      }

      .btn-primary:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
      }

      .btn-primary:disabled {
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

      @media (max-width: 767px) {
        .dialog-container {
          padding: 24px 20px;
        }

        .dialog-title {
          font-size: 20px;
        }

        .admin-type-card {
          padding: 12px;
        }

        .admin-icon {
          font-size: 28px;
        }

        .admin-name {
          font-size: 14px;
        }

        .admin-desc {
          font-size: 12px;
        }
      }
    `,
  ],
})
export class AdminMockDialogComponent {
  @Output() close = new EventEmitter<void>();
  @Output() loginSuccess = new EventEmitter<AdminType>();

  selectedAdminType: AdminType | null = null;
  loading = false;

  adminTypes: Array<{
    type: AdminType;
    label: string;
    icon: string;
    description: string;
  }> = [
    {
      type: 'organization',
      label: '机构管理员',
      icon: '🏢',
      description: '管理培训机构（云托管版）',
    },
    {
      type: 'school',
      label: '学校管理员',
      icon: '🏫',
      description: '管理学校课程与教学',
    },
    {
      type: 'education_bureau',
      label: '教育局管理员',
      icon: '🏛️',
      description: '教育监管部门',
    },
  ];

  // 不同管理员类型的测试账号配置
  testAccounts = {
    organization: {
      email: 'org_admin@testorg.com',
      password: 'OrgAdmin123!',
      organization: 'Test Organization',
      licenseType: '云托管版 CLOUD_HOSTED',
      // redirectPath: '/management/organization/1/dashboard',  // 已解耦到 OpenMTEduInst 项目
      redirectPath: '/admin/dashboard',
    },
    school: {
      email: 'school_admin@testschool.com',
      password: 'SchoolAdmin123!',
      organization: 'Test School',
      licenseType: '校本课程版 SCHOOL_EDITION',
      redirectPath: '/management/school/1/dashboard', // ✅ 已修正为带 ID 的路径
    },
    education_bureau: {
      email: 'edu_bureau@testedu.gov.cn',
      password: 'EduBureau123!',
      organization: 'Test Education Bureau',
      licenseType: '区域监管版 REGION_SUPERVISION',
      redirectPath: '/management/education-bureau/1/dashboard', // ✅ 已修正为带 ID 的路径
    },
  };

  get testAccount(): {
    email: string;
    password: string;
    organization: string;
    licenseType: string;
    redirectPath: string;
  } {
    return this.selectedAdminType
      ? this.testAccounts[this.selectedAdminType]
      : this.testAccounts.organization;
  }

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  selectAdminType(type: AdminType): void {
    this.selectedAdminType = type;
  }

  onClose(): void {
    this.close.emit();
  }

  onMockLogin(): void {
    if (!this.selectedAdminType) return;

    this.loading = true;

    // 使用 AuthService 的 mockAdminLogin 方法
    this.authService.mockAdminLogin(this.selectedAdminType).subscribe({
      next: () => {
        setTimeout(() => {
          this.loading = false;
          if (this.selectedAdminType) {
            this.loginSuccess.emit(this.selectedAdminType);
            // 根据管理员类型直接跳转到对应的管理页面
            const redirectPath = this.testAccounts[this.selectedAdminType].redirectPath;
            void this.router.navigate([redirectPath]);
          }
        }, 500);
      },
      error: (_error) => {
        this.loading = false;
        alert('模拟登录失败，请重试');
      },
    });
  }
}
