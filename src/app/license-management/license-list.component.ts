import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { LicenseDetail, LicenseStatus, LicenseType } from '../models/license.models';
import { LicenseManagementService } from '../services/license-management.service';

import { LicenseAssignDialogComponent } from './license-assign-dialog.component';

interface LicenseDisplay extends LicenseDetail {
  statusColor: 'primary' | 'accent' | 'warn';
  statusLabel: string;
  usagePercent: number;
}

@Component({
  selector: 'app-license-list',
  standalone: false,
  templateUrl: './license-list.component.html',
  styleUrls: ['./license-list.component.scss'],
})
export class LicenseListComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  licenses: LicenseDisplay[] = [];
  filteredLicenses: LicenseDisplay[] = [];
  isLoading = true;

  // 筛选条件
  filterStatus: LicenseStatus | 'all' = 'all';
  filterType: LicenseType | 'all' = 'all';
  searchText = '';

  // 表格列定义
  displayedColumns: string[] = [
    'licenseKey',
    'type',
    'status',
    'users',
    'features',
    'expiresAt',
    'actions',
  ];

  // 统计信息
  stats = {
    total: 0,
    active: 0,
    expiring: 0,
    expired: 0,
  };

  constructor(
    private licenseService: LicenseManagementService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadLicenses();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadLicenses(): void {
    this.isLoading = true;
    this.licenseService
      .getLicenseList()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.licenses = data.map((license) => ({
            ...license,
            statusColor: this.getStatusColor(license.status),
            statusLabel: this.getStatusLabel(license.status),
            usagePercent: Math.round((license.current_users / license.max_users) * 100),
          }));

          this.updateStats();
          this.applyFilters();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('加载许可证列表失败:', error);
          this.snackBar.open('加载许可证列表失败，请稍后重试', '关闭', {
            duration: 3000,
          });
          this.isLoading = false;
        },
      });
  }

  private getStatusColor(status: LicenseStatus): 'primary' | 'accent' | 'warn' {
    switch (status) {
      case 'active':
        return 'primary';
      case 'expiring':
        return 'accent';
      case 'expired':
      case 'revoked':
        return 'warn';
      default:
        return 'primary';
    }
  }

  private getStatusLabel(status: LicenseStatus): string {
    const labels: Record<LicenseStatus, string> = {
      active: '活跃',
      expiring: '即将过期',
      expired: '已过期',
      revoked: '已撤销',
    };
    return labels[status];
  }

  private updateStats(): void {
    this.stats.total = this.licenses.length;
    this.stats.active = this.licenses.filter((l) => l.status === 'active').length;
    this.stats.expiring = this.licenses.filter((l) => l.status === 'expiring').length;
    this.stats.expired = this.licenses.filter(
      (l) => l.status === 'expired' || l.status === 'revoked'
    ).length;
  }

  applyFilters(): void {
    this.filteredLicenses = this.licenses.filter((license) => {
      const matchStatus = this.filterStatus === 'all' || license.status === this.filterStatus;
      const matchType = this.filterType === 'all' || license.license_type === this.filterType;
      const matchSearch =
        !this.searchText ||
        license.id.toString().includes(this.searchText) ||
        license.license_key.toLowerCase().includes(this.searchText.toLowerCase()) ||
        license.organization_name.toLowerCase().includes(this.searchText.toLowerCase());

      return matchStatus && matchType && matchSearch;
    });
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  openAssignDialog(license: LicenseDisplay | null): void {
    if (!license) {
      return;
    }
    const dialogRef = this.dialog.open(LicenseAssignDialogComponent, {
      width: '600px',
      data: { licenseId: license.id },
    });

    dialogRef
      .afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe((result) => {
        if (result) {
          this.snackBar.open('许可证分配成功', '关闭', { duration: 2000 });
          this.loadLicenses();
        }
      });
  }

  viewDetails(license: LicenseDisplay): void {
    this.snackBar.open(`查看许可证详情：${license.license_key}`, '关闭', { duration: 2000 });
    // TODO: 实现详情对话框
  }

  revokeLicense(license: LicenseDisplay): void {
    if (!confirm(`确定要撤销许可证 ${license.license_key} 吗？此操作不可恢复。`)) {
      return;
    }

    this.licenseService
      .revokeLicense(license.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.snackBar.open('许可证已撤销', '关闭', { duration: 2000 });
          this.loadLicenses();
        },
        error: (error) => {
          console.error('撤销许可证失败:', error);
          this.snackBar.open('撤销许可证失败', '关闭', { duration: 3000 });
        },
      });
  }

  exportToExcel(): void {
    this.licenseService.exportLicensesToExcel(this.filteredLicenses).subscribe({
      next: () => {
        this.snackBar.open('导出成功', '关闭', { duration: 2000 });
      },
      error: (error) => {
        console.error('导出失败:', error);
        this.snackBar.open('导出失败', '关闭', { duration: 3000 });
      },
    });
  }

  getUsageBarColor(percent: number): 'primary' | 'accent' | 'warn' {
    if (percent < 50) {
      return 'primary';
    } else if (percent < 80) {
      return 'accent';
    } else {
      return 'warn';
    }
  }

  getLicenseTypeLabel(type: LicenseType): string {
    const labels: Record<LicenseType, string> = {
      cloud_hosted: '云托管版',
      enterprise: '企业版',
      education: '教育版',
      trial: '试用版',
    };
    return labels[type] || type;
  }
}
