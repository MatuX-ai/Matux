import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  inject,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { finalize } from 'rxjs/operators';

import { Achievement, AchievementType } from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';
// import { AchievementFilePreviewComponent } from './achievement-file-preview/achievement-file-preview.component';

@Component({
  selector: 'app-achievement-upload',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule],
  templateUrl: './achievement-upload.component.html',
  styleUrls: ['./achievement-upload.component.scss'],
})
export class AchievementUploadComponent {
  @ViewChild('fileInput') fileInput!: ElementRef;
  nativeFileInput!: HTMLInputElement;

  ngAfterViewInit(): void {
    this.nativeFileInput = this.fileInput.nativeElement;
  }
  @Input() moduleId?: number;
  @Input() lessonId?: number;
  @Input() userId?: number;
  @Output() uploadSuccess = new EventEmitter<Achievement>();

  private achievementService = inject(AchievementService);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  uploadForm: FormGroup;
  uploading = false;
  uploadProgress = 0;
  uploadedFiles: File[] = [];
  achievementTypes: { value: AchievementType; label: string }[] = [
    { value: 'project', label: '🚀 项目案例' },
    { value: 'certificate', label: '🎓 证书' },
    { value: 'assignment', label: '📝 作业' },
    { value: 'portfolio', label: '🎨 作品集' },
    { value: 'case_study', label: '📊 案例研究' },
    { value: 'other', label: '📎 其他' },
  ];
  tagInput = '';
  selectedTags: string[] = [];

  allowedFileTypes = [
    'image/*',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/zip',
    'application/x-zip-compressed',
    'video/*',
  ];

  constructor() {
    this.uploadForm = this.fb.group({
      type: ['project', Validators.required],
      title: ['', [Validators.required, Validators.maxLength(100)]],
      description: ['', [Validators.required, Validators.maxLength(500)]],
      files: [[], [Validators.required, Validators.minLength(1)]],
      isPublic: [true],
    });
  }

  /**
   * 处理文件选择
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const files = Array.from(input.files);
      this.validateAndAddFiles(files);
    }
  }

  /**
   * 拖拽上传
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      const files = Array.from(event.dataTransfer.files);
      this.validateAndAddFiles(files);
    }
  }

  /**
   * 验证并添加文件
   */
  private validateAndAddFiles(files: File[]): void {
    for (const file of files) {
      if (!this.isFileTypeAllowed(file)) {
        this.snackBar.open(`文件类型不支持: ${file.name}`, '关闭', { duration: 3000 });
        continue;
      }

      if (file.size > 50 * 1024 * 1024) {
        // 50MB limit
        this.snackBar.open(`文件大小超过限制 (最大50MB): ${file.name}`, '关闭', { duration: 3000 });
        continue;
      }

      this.uploadedFiles.push(file);
    }

    this.uploadForm.patchValue({ files: this.uploadedFiles });
  }

  /**
   * 检查文件类型是否允许
   */
  private isFileTypeAllowed(file: File): boolean {
    return this.allowedFileTypes.some((type) => {
      if (type.endsWith('/*')) {
        const mimeType = type.replace('*', '');
        return file.type.startsWith(mimeType);
      }
      return file.type === type;
    });
  }

  /**
   * 触发文件选择
   */
  triggerFileInput(): void {
    this.nativeFileInput.click();
  }

  /**
   * 移除文件
   */
  removeFile(index: number): void {
    this.uploadedFiles.splice(index, 1);
    this.uploadForm.patchValue({ files: this.uploadedFiles });
  }

  /**
   * 预览文件
   */
  previewFile(file: File): void {
    const reader = new FileReader();
    reader.onload = () => {
      // TODO: 创建文件预览组件
      // this.dialog.open(AchievementFilePreviewComponent, {
      //   data: { file: file, previewUrl: reader.result as string },
      //   maxWidth: '80vw',
      //   maxHeight: '80vh',
      // });
    };
    reader.readAsDataURL(file);
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * 添加标签
   */
  addTag(): void {
    const tag = this.tagInput.trim().toLowerCase();
    if (tag && !this.selectedTags.includes(tag)) {
      this.selectedTags.push(tag);
      this.tagInput = '';
    }
  }

  /**
   * 移除标签
   */
  removeTag(index: number): void {
    this.selectedTags.splice(index, 1);
  }

  /**
   * 提交表单
   */
  onSubmit(): void {
    if (this.uploadForm.invalid || this.uploadedFiles.length === 0) {
      this.markFormGroupTouched(this.uploadForm);
      return;
    }

    this.uploading = true;
    this.uploadProgress = 0;

    const formValue = this.uploadForm.value;

    // 先创建成果记录
    const achievementData = {
      type: formValue.type,
      title: formValue.title,
      description: formValue.description,
      moduleId: this.moduleId,
      lessonId: this.lessonId,
      userId: this.userId,
      tags: this.selectedTags,
      isPublic: formValue.isPublic,
    };

    this.achievementService
      .createAchievement(achievementData)
      .pipe(
        finalize(() => {
          this.uploading = false;
        })
      )
      .subscribe({
        next: (achievement: Achievement) => {
          this.uploadFiles(achievement.id);
        },
        error: (error: any) => {
          this.snackBar.open(`创建失败: ${error.error?.message || error.message}`, '关闭', {
            duration: 5000,
          });
        },
      });
  }

  /**
   * 上传文件
   */
  private uploadFiles(achievementId: number): void {
    const totalFiles = this.uploadedFiles.length;
    let uploadedCount = 0;

    const uploadPromises = this.uploadedFiles.map((file) => {
      return new Promise<void>((resolve, reject) => {
        this.achievementService.uploadAchievementFile(achievementId, file).subscribe({
          next: () => {
            uploadedCount++;
            this.uploadProgress = (uploadedCount / totalFiles) * 100;
            resolve();
          },
          error: (error: any) => {
            reject(error);
          },
        });
      });
    });

    Promise.all(uploadPromises)
      .then(() => {
        // 提交审核
        this.achievementService.submitAchievement(achievementId).subscribe({
          next: (achievement: Achievement) => {
            this.snackBar.open('🎉 成果上传成功，已提交审核！', '关闭', { duration: 3000 });
            this.resetForm();
            this.uploadSuccess.emit(achievement);
          },
          error: () => {
            // 文件上传成功但提交失败
            this.snackBar.open('✅ 文件上传成功，但提交审核失败，请手动提交', '关闭', {
              duration: 5000,
            });
            this.resetForm();
          },
        });
      })
      .catch((error) => {
        this.snackBar.open(`文件上传失败: ${error.message}`, '关闭', { duration: 5000 });
      });
  }

  /**
   * 重置表单
   */
  resetForm(): void {
    this.uploadForm.reset({
      type: 'project',
      title: '',
      description: '',
      files: [],
      isPublic: true,
    });
    this.uploadedFiles = [];
    this.selectedTags = [];
    this.uploadProgress = 0;
  }

  /**
   * 标记所有表单字段为已触摸
   */
  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach((key) => {
      const control = formGroup.get(key);
      control?.markAsTouched();

      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  /**
   * 获取成果类型图标
   */
  getAchievementTypeIcon(type: AchievementType): string {
    const icons: Record<AchievementType, string> = {
      project: '🚀',
      certificate: '🎓',
      assignment: '📝',
      portfolio: '🎨',
      case_study: '📊',
      other: '📎',
    };
    return icons[type] || '📎';
  }
}
