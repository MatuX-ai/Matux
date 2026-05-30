/**
 * 批量上传对话框组件 - Excel 文件上传和解析
 */

import { CdkDragDrop, CdkDropList } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatStepperModule } from '@angular/material/stepper';
import { MatTableModule } from '@angular/material/table';

export interface ImportPreviewData {
  fileName: string;
  totalRows: number;
  validRows: number;
  invalidRows: number;
  data: unknown[];
  errors: ImportError[];
}

export interface ImportError {
  row: number;
  message: string;
  data?: unknown;
}

@Component({
  selector: 'app-batch-upload-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatStepperModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatCardModule,
    MatListModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    CdkDropList,
  ],
  templateUrl: './batch-upload-dialog.component.html',
  styleUrls: ['./batch-upload-dialog.component.scss'],
})
export class BatchUploadDialogComponent {
  // 步骤控制
  stepIndex = 0;

  // 上传状态
  selectedFile: File | null = null;
  isUploading = false;
  uploadProgress = 0;

  // 预览数据
  previewData: ImportPreviewData | null = null;
  importResult: ImportResult | null = null;

  // 暴露 document 对象供模板使用
  get document(): Document {
    return window.document;
  }

  constructor(
    public dialogRef: MatDialogRef<BatchUploadDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { title: string }
  ) {}

  /**
   * 处理文件选择
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      this.selectedFile = file;
    } else {
      alert('请选择 Excel 文件 (.xlsx 或 .xls)');
    }
  }

  /**
   * 处理拖拽文件
   */
  onDrop(_event: CdkDragDrop<File[], any, File[]>): void {
    // TODO: 实现拖拽上传逻辑
  }

  /**
   * 下载模板
   */
  downloadTemplate(): void {
    // TODO: 调用 API 下载模板
    console.log('下载模板');
  }

  /**
   * 上传并解析文件
   */
  uploadAndParse(): void {
    if (!this.selectedFile) return;

    this.isUploading = true;
    this.stepIndex = 1;

    // 模拟上传进度
    const interval = setInterval(() => {
      this.uploadProgress += 20;
      if (this.uploadProgress >= 100) {
        clearInterval(interval);
        this.isUploading = false;

        // 模拟解析结果
        this.previewData = {
          fileName: this.selectedFile!.name,
          totalRows: 50,
          validRows: 48,
          invalidRows: 2,
          data: [],
          errors: [
            { row: 5, message: '手机号格式不正确', data: { phone: '123' } },
            { row: 12, message: '身份证号格式错误', data: { idCardNumber: '123456' } },
          ],
        };
      }
    }, 500);
  }

  /**
   * 确认导入
   */
  confirmImport(): void {
    this.stepIndex = 2;

    // TODO: 调用批量导入 API
    setTimeout(() => {
      this.importResult = {
        success: 48,
        failed: 2,
        errors: this.previewData?.errors || [],
      };
    }, 1000);
  }

  /**
   * 关闭对话框
   */
  close(): void {
    this.dialogRef.close(this.importResult);
  }
}

interface ImportResult {
  success: number;
  failed: number;
  errors: ImportError[];
}
