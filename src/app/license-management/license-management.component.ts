import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';

import {
  CreateLicenseRequest,
  License,
  LicenseService,
  LicenseStatus,
  LicenseType,
  Organization,
} from '../core/services/license.service';

@Component({
  selector: 'app-license-management',
  standalone: false,
  templateUrl: './license-management.component.html',
  styleUrls: ['./license-management.component.scss'],
})
export class LicenseManagementComponent implements OnInit {
  // 数据
  organizations: Organization[] = [];
  licenses: License[] = [];
  selectedOrganization: Organization | null = null;

  // 表单
  orgForm!: FormGroup;
  licenseForm!: FormGroup;

  // 状态
  isLoading = false;
  isCreatingOrg = false;
  isGeneratingLicense = false;

  // 计算属性
  get activeLicensesCount(): number {
    return this.licenses.filter((l) => l.status === LicenseStatus.ACTIVE).length;
  }

  // 枚举引用
  LicenseType = LicenseType;
  LicenseStatus = LicenseStatus;

  constructor(
    private fb: FormBuilder,
    private licenseService: LicenseService,
    private snackBar: MatSnackBar
  ) {
    this.initForms();
  }

  async ngOnInit(): Promise<void> {
    await this.loadOrganizations();
    await this.loadLicenses();
  }

  private initForms(): void {
    // 组织表单
    this.orgForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(2)]],
      contact_email: ['', [Validators.required, Validators.email]],
      phone: [''],
      address: [''],
      website: [''],
      max_users: [100, [Validators.min(1), Validators.max(100000)]],
    });

    // 许可证表单
    this.licenseForm = this.fb.group({
      organization_id: ['', Validators.required],
      license_type: [LicenseType.COMMERCIAL],
      duration_days: [365, [Validators.min(1), Validators.max(3650)]],
      max_users: [1, [Validators.min(1), Validators.max(100000)]],
      max_devices: [1, [Validators.min(1), Validators.max(100000)]],
      features: [[]],
      notes: [''],
    });
  }

  // 加载组织列表
  async loadOrganizations(): Promise<void> {
    this.isLoading = true;
    try {
      const orgs = await this.licenseService.getOrganizations(0, 100, true);
      this.organizations = orgs;
    } catch (error) {
      this.showError('加载组织列表失败');
    } finally {
      this.isLoading = false;
    }
  }

  // 加载许可证列表
  async loadLicenses(organizationId?: number): Promise<void> {
    this.isLoading = true;
    try {
      const licenses = await this.licenseService.getLicenses(0, 100, organizationId);
      this.licenses = licenses;
    } catch (error) {
      this.showError('加载许可证列表失败');
    } finally {
      this.isLoading = false;
    }
  }

  // 创建组织
  async createOrganization(): Promise<void> {
    if (this.orgForm.invalid) {
      this.showWarning('请填写正确的组织信息');
      return;
    }

    this.isCreatingOrg = true;
    const orgData = this.orgForm.value;

    try {
      const organization = await this.licenseService.createOrganization(orgData);
      this.organizations.push(organization);
      this.orgForm.reset({
        max_users: 100,
      });
      this.showSuccess('组织创建成功');
    } catch (error: any) {
      this.showError('创建组织失败：' + error.message);
    } finally {
      this.isCreatingOrg = false;
    }
  }

  // 生成许可证
  async generateLicense(): Promise<void> {
    if (this.licenseForm.invalid) {
      this.showWarning('请填写正确的许可证信息');
      return;
    }

    this.isGeneratingLicense = true;
    const formValue = this.licenseForm.getRawValue() as CreateLicenseRequest;
    const licenseData: CreateLicenseRequest = {
      organization_id: formValue.organization_id,
      license_type: formValue.license_type,
      duration_days: formValue.duration_days,
      max_users: formValue.max_users,
      max_devices: formValue.max_devices,
      features: formValue.features,
      notes: formValue.notes,
    };

    try {
      const license = await this.licenseService.generateLicense(licenseData);
      this.licenses.unshift(license);
      this.licenseForm.reset({
        license_type: LicenseType.COMMERCIAL,
        duration_days: 365,
        max_users: 1,
        max_devices: 1,
        features: [],
      });
      this.showSuccess('许可证生成成功');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      this.showError('生成许可证失败：' + errorMessage);
    } finally {
      this.isGeneratingLicense = false;
    }
  }

  // 验证许可证
  async validateLicense(licenseKey: string): Promise<void> {
    try {
      const result = await this.licenseService.validateLicense(licenseKey);
      if (result.valid) {
        this.showSuccess(`许可证验证成功，剩余${result.license_info?.days_until_expiry}天`);
      } else {
        this.showError(`许可证验证失败：${result.error}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      this.showError('许可证验证失败：' + errorMessage);
    }
  }

  // 撤销许可证
  async revokeLicense(licenseKey: string): Promise<void> {
    if (!confirm('确定要撤销此许可证吗？此操作不可恢复。')) {
      return;
    }

    try {
      await this.licenseService.revokeLicense(licenseKey, '管理员手动撤销');
      // 更新本地数据
      const license = this.licenses.find((l) => l.license_key === licenseKey);
      if (license) {
        license.status = LicenseStatus.REVOKED;
        license.is_active = false;
      }
      this.showSuccess('许可证已撤销');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      this.showError('撤销许可证失败：' + errorMessage);
    }
  }

  // 更新许可证状态
  async updateLicenseStatus(licenseKey: string, status: LicenseStatus): Promise<void> {
    try {
      const updatedLicense = await this.licenseService.updateLicense(licenseKey, { status });
      // 更新本地数据
      const index = this.licenses.findIndex((l) => l.license_key === licenseKey);
      if (index !== -1) {
        this.licenses[index] = updatedLicense;
      }
      this.showSuccess('许可证状态已更新');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      this.showError('更新许可证状态失败：' + errorMessage);
    }
  }

  // 选择组织
  selectOrganization(org: Organization): void {
    this.selectedOrganization = org;
    this.licenseForm.patchValue({ organization_id: org.id });
    void this.loadLicenses(org.id);
  }

  // 获取状态标签类
  getStatusClass(status: LicenseStatus): string {
    switch (status) {
      case LicenseStatus.ACTIVE:
        return 'status-active';
      case LicenseStatus.EXPIRED:
        return 'status-expired';
      case LicenseStatus.REVOKED:
        return 'status-revoked';
      case LicenseStatus.PENDING:
        return 'status-pending';
      default:
        return '';
    }
  }

  // 格式化日期
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('zh-CN');
  }

  // 显示成功消息
  private showSuccess(message: string): void {
    this.snackBar.open(message, '关闭', {
      duration: 3000,
      panelClass: ['success-snackbar'],
    });
  }

  // 显示错误消息
  private showError(message: string): void {
    this.snackBar.open(message, '关闭', {
      duration: 5000,
      panelClass: ['error-snackbar'],
    });
  }

  // 显示警告消息
  private showWarning(message: string): void {
    this.snackBar.open(message, '关闭', {
      duration: 3000,
      panelClass: ['warning-snackbar'],
    });
  }

  // 检查表单是否有效
  isFormValid(form: FormGroup): boolean {
    return form.valid && !form.pristine;
  }
}
