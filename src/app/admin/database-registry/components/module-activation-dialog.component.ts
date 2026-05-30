import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

export interface ModuleActivationDialogData {
  module: {
    name: string;
    table_name: string;
    category: string;
    version: string;
    description?: string;
    is_active: boolean;
  };
  action: 'activate' | 'deactivate';
}

@Component({
  selector: 'app-module-activation-dialog',
  standalone: false,
  templateUrl: './module-activation-dialog.component.html',
  styleUrls: ['./module-activation-dialog.component.scss'],
})
export class ModuleActivationDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<ModuleActivationDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ModuleActivationDialogData
  ) {}

  get actionText(): string {
    return this.data.action === 'activate' ? '激活' : '停用';
  }

  get actionIcon(): string {
    return this.data.action === 'activate' ? 'power_settings_new' : 'power_off';
  }

  get warningMessage(): string {
    if (this.data.action === 'deactivate') {
      return `停用模块 "${this.data.module.name}" 可能会影响依赖此模块的功能正常运行。`;
    } else {
      return `激活模块 "${this.data.module.name}" 将启用相关的数据库表和功能。`;
    }
  }

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }
}
