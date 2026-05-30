import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { LicenseManagementService } from '../services/license-management.service';

export interface LicenseAssignDialogData {
  licenseId?: number;
}

@Component({
  selector: 'app-license-assign-dialog',
  standalone: false,
  templateUrl: './license-assign-dialog.component.html',
  styleUrls: ['./license-assign-dialog.component.scss'],
})
export class LicenseAssignDialogComponent implements OnInit {
  assignForm: FormGroup;
  selectedUserIds: number[] = [];
  role: 'admin' | 'user' = 'user';
  notes = '';
  isSubmitting = false;

  // Mock 用户列表（实际应从 API 获取）
  availableUsers = [
    { id: 1, name: '张三', email: 'zhangsan@example.com', currentLicenses: 0 },
    { id: 2, name: '李四', email: 'lisi@example.com', currentLicenses: 1 },
    { id: 3, name: '王五', email: 'wangwu@example.com', currentLicenses: 2 },
    { id: 4, name: '赵六', email: 'zhaoliu@example.com', currentLicenses: 0 },
    { id: 5, name: '钱七', email: 'qianqi@example.com', currentLicenses: 1 },
  ];

  constructor(
    public dialogRef: MatDialogRef<LicenseAssignDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: LicenseAssignDialogData,
    private fb: FormBuilder,
    private licenseService: LicenseManagementService
  ) {
    this.assignForm = this.fb.group({
      role: ['user'],
      notes: [''],
    });
  }

  ngOnInit(): void {
    // TODO: 从 API 加载用户列表
  }

  onToggleUser(userId: number): void {
    const index = this.selectedUserIds.indexOf(userId);
    if (index > -1) {
      this.selectedUserIds.splice(index, 1);
    } else {
      this.selectedUserIds.push(userId);
    }
  }

  onSelectAll(): void {
    if (this.selectedUserIds.length === this.availableUsers.length) {
      this.selectedUserIds = [];
    } else {
      this.selectedUserIds = this.availableUsers.map((u) => u.id);
    }
  }

  onSubmit(): void {
    if (this.selectedUserIds.length === 0) {
      return;
    }

    this.isSubmitting = true;

    // TODO: 调用真实 API
    this.licenseService
      .assignLicense(this.data.licenseId ?? 1, this.selectedUserIds, this.role)
      .subscribe({
        next: () => {
          this.dialogRef.close(true);
        },
        error: (error) => {
          console.error('分配许可证失败:', error);
          this.isSubmitting = false;
        },
      });
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }
}
