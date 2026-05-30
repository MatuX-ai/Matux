import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';

import { UserBulkImportService } from './user-bulk-import.service';

interface ImportResult {
  success_count: number;
  failed_count: number;
  conflicts_count: number;
  errors: string[];
  conflicts: Record<string, unknown>;
  imported_users: Array<{ [key: string]: unknown }>;
}

@Component({
  selector: 'app-user-bulk-import',
  standalone: false,
  templateUrl: './bulk-import.component.html',
  styleUrls: ['./bulk-import.component.scss'],
})
export class UserBulkImportComponent implements OnInit {
  // 表单组
  importForm: FormGroup;

  // 状态变量
  selectedFile: File | null = null;
  isImporting = false;
  importProgress = 0;
  importResults: ImportResult | null = null;
  isDragOver = false;

  // 配置选项
  conflictResolutionOptions = [
    { value: 'skip', label: '跳过重复项' },
    { value: 'update', label: '更新现有用户' },
    { value: 'overwrite', label: '完全覆盖' },
    { value: 'error', label: '发现冲突时停止' },
  ];

  // 字段映射数据
  fieldMappingData = [
    { target: '用户名', source: 'username, Username, 用户名' },
    { target: '邮箱', source: 'email, Email, 邮箱' },
    { target: '角色', source: 'role, Role, 角色 (可选)' },
  ];

  constructor(
    private fb: FormBuilder,
    private bulkImportService: UserBulkImportService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {
    this.importForm = this.fb.group({
      conflictResolution: ['skip', Validators.required.bind(Validators)],
      generatePassword: [true],
    });
  }

  ngOnInit(): void {}

  /**
   * 处理文件选择
   */
  onFileSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
      this.validateAndSetFile(file);
    }
  }

  /**
   * 处理文件拖拽
   */
  onFileDropped(files: FileList): void {
    if (files.length > 0) {
      this.validateAndSetFile(files[0]);
    }
  }

  /**
   * 拖拽事件处理
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;

    if (event.dataTransfer?.files.length) {
      this.validateAndSetFile(event.dataTransfer.files[0]);
    }
  }

  /**
   * 验证并设置文件
   */
  private validateAndSetFile(file: File): void {
    // 验证文件类型
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ];

    if (!validTypes.includes(file.type)) {
      this.snackBar.open('请选择有效的CSV或Excel文件', '关闭', {
        duration: 3000,
        panelClass: ['error-snackbar'],
      });
      return;
    }

    // 验证文件大小 (10MB限制)
    if (file.size > 10 * 1024 * 1024) {
      this.snackBar.open('文件大小不能超过10MB', '关闭', {
        duration: 3000,
        panelClass: ['error-snackbar'],
      });
      return;
    }

    this.selectedFile = file;
    this.importResults = null; // 清除之前的导入结果
  }

  /**
   * 执行批量导入
   */
  importUsers(): void {
    if (!this.validateImportRequest()) {
      return;
    }

    this.initializeImportState();
    this.startProgressSimulation();

    const conflictResolution = this.getConflictResolution();
    const generatePassword = this.getGeneratePasswordOption();

    this.executeImport(conflictResolution, generatePassword);
  }

  /**
   * 验证导入请求
   */
  private validateImportRequest(): boolean {
    if (!this.selectedFile) {
      this.snackBar.open('请先选择要导入的文件', '关闭', {
        duration: 3000,
        panelClass: ['error-snackbar'],
      });
      return false;
    }

    if (this.importForm.invalid) {
      this.snackBar.open('请完善导入配置', '关闭', {
        duration: 3000,
        panelClass: ['error-snackbar'],
      });
      return false;
    }

    return true;
  }

  /**
   * 初始化导入状态
   */
  private initializeImportState(): void {
    this.isImporting = true;
    this.importProgress = 0;
    this.importResults = null;
  }

  /**
   * 获取冲突解决策略
   */
  private getConflictResolution(): string {
    return (this.importForm.get('conflictResolution')?.value as string) || 'skip';
  }

  /**
   * 获取生成密码选项
   */
  private getGeneratePasswordOption(): boolean {
    return (this.importForm.get('generatePassword')?.value as boolean) ?? true;
  }

  /**
   * 执行导入操作
   */
  private executeImport(conflictResolution: string, generatePassword: boolean): void {
    if (!this.selectedFile) {
      return;
    }

    this.bulkImportService
      .importUsers(this.selectedFile, conflictResolution, generatePassword)
      .subscribe({
        next: (result) => {
          this.importResults = result;
          this.showSuccessMessages(result);
          this.isImporting = false;
          this.importProgress = 100;
        },
        error: (error: Error) => {
          this.snackBar.open(`导入失败：${error.message || '未知错误'}`, '关闭', {
            duration: 5000,
            panelClass: ['error-snackbar'],
          });
          this.isImporting = false;
          this.importProgress = 100;
        },
      });
  }

  /**
   * 显示成功消息
   */
  private showSuccessMessages(result: ImportResult): void {
    if (result.success_count > 0) {
      this.snackBar.open(`成功导入 ${result.success_count} 个用户`, '关闭', {
        duration: 5000,
        panelClass: ['success-snackbar'],
      });
    }

    if (result.failed_count > 0 || result.conflicts_count > 0) {
      this.snackBar
        .open(
          `导入完成，但有 ${result.failed_count + result.conflicts_count} 条记录存在问题`,
          '查看详情',
          {
            duration: 10000,
            panelClass: ['warning-snackbar'],
          }
        )
        .onAction()
        .subscribe(() => {
          // 用户点击查看详情时的处理
        });
    }
  }

  /**
   * 模拟导入进度
   */
  private startProgressSimulation(): void {
    const interval = setInterval(() => {
      if (this.importProgress < 90) {
        this.importProgress += 10;
      } else {
        clearInterval(interval);
      }
    }, 200);
  }

  /**
   * 取消导入
   */
  cancelImport(): void {
    void this.router.navigate(['/admin/users']);
  }

  /**
   * 下载模板文件
   */
  downloadTemplate(): void {
    this.bulkImportService.downloadTemplate();
  }

  /**
   * 获取冲突类型的显示文本
   */
  getConflictTypeLabel(type: string): string {
    switch (type) {
      case 'email_conflicts':
        return '邮箱冲突';
      case 'username_conflicts':
        return '用户名冲突';
      case 'invalid_data':
        return '数据验证失败';
      default:
        return type;
    }
  }

  /**
   * 获取所有冲突键
   */
  getConflictKeys(): string[] {
    if (!this.importResults?.conflicts) return [];
    return Object.keys(this.importResults.conflicts);
  }

  /**
   * 获取指定键的冲突数量
   */
  getConflictCount(key: string): number {
    if (!this.importResults?.conflicts) return 0;
    const conflicts = this.importResults.conflicts[key];
    return Array.isArray(conflicts) ? conflicts.length : 0;
  }

  /**
   * 根据键获取冲突数据
   */
  getConflictsByKey(key: string): unknown[] {
    if (!this.importResults?.conflicts) return [];
    const conflicts = this.importResults.conflicts[key];
    return Array.isArray(conflicts) ? conflicts : [];
  }

  /**
   * 获取导入统计摘要
   */
  getImportSummary(): string {
    if (!this.importResults) return '';

    const parts = [];
    if (this.importResults.success_count > 0) {
      parts.push(`${this.importResults.success_count}个成功`);
    }
    if (this.importResults.failed_count > 0) {
      parts.push(`${this.importResults.failed_count}个失败`);
    }
    if (this.importResults.conflicts_count > 0) {
      parts.push(`${this.importResults.conflicts_count}个冲突`);
    }

    return parts.join('，');
  }

  /**
   * 获取冲突条目数组（保留向后兼容）
   */
  getConflictEntries(): Array<{ key: string; value: unknown[] }> {
    if (!this.importResults?.conflicts) return [];

    return Object.entries(this.importResults.conflicts).map(([key, value]) => ({
      key,
      value: Array.isArray(value) ? value : [],
    }));
  }
}
