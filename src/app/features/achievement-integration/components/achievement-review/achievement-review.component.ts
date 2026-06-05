import { CommonModule } from '@angular/common';
import { Component, EventEmitter, inject, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSliderModule } from '@angular/material/slider';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Achievement, AchievementReview, AchievementStatus } from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-review',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSliderModule,
  ],
  templateUrl: './achievement-review.component.html',
  styleUrls: ['./achievement-review.component.scss'],
})
export class AchievementReviewComponent implements OnInit {
  @Input() achievement!: Achievement;
  @Output() reviewComplete = new EventEmitter<Achievement>();

  private achievementService = inject(AchievementService);
  private snackBar = inject(MatSnackBar);
  private fb = inject(FormBuilder);

  reviewForm: FormGroup;
  reviewing = false;
  reviewHistory: AchievementReview[] = [];
  selectedScore = 0;
  scoreOptions = [
    { value: 1, label: '1分 - 不合格', description: '未能达到基本要求' },
    { value: 2, label: '2分 - 需改进', description: '基本框架存在，需完善' },
    { value: 3, label: '3分 - 合格', description: '达到预期要求' },
    { value: 4, label: '4分 - 优秀', description: '超出预期，质量良好' },
    { value: 5, label: '5分 - 卓越', description: '表现突出，可作为范例' },
  ];

  statusOptions: { value: AchievementStatus; label: string; color: string }[] = [
    { value: 'approved', label: '✅ 通过', color: 'green' },
    { value: 'rejected', label: '❌ 拒绝', color: 'red' },
    { value: 'revision', label: '🔄 需修改', color: 'orange' },
  ];

  constructor() {
    this.reviewForm = this.fb.group({
      status: ['approved', Validators.required],
      score: [3, [Validators.required, Validators.min(1), Validators.max(5)]],
      feedback: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(500)]],
    });

    this.selectedScore = 3;
  }

  ngOnInit(): void {
    this.loadReviewHistory();
    this.reviewForm.get('score')?.valueChanges.subscribe((value) => {
      this.selectedScore = value;
    });
  }

  /**
   * 加载审核历史
   */
  loadReviewHistory(): void {
    this.achievementService.getAchievementReviews(this.achievement.id).subscribe({
      next: (reviews: AchievementReview[]) => {
        this.reviewHistory = reviews;
      },
      error: () => {
        this.snackBar.open('加载审核历史失败', '关闭', { duration: 3000 });
      },
    });
  }

  /**
   * 提交审核
   */
  onSubmit(): void {
    if (this.reviewForm.invalid) {
      this.markFormGroupTouched(this.reviewForm);
      return;
    }

    this.reviewing = true;

    const reviewData = this.reviewForm.value;

    this.achievementService
      .reviewAchievement(this.achievement.id, {
        status: reviewData.status,
        score: reviewData.score,
        feedback: reviewData.feedback,
      })
      .subscribe({
        next: (updatedAchievement: Achievement) => {
          this.snackBar.open('✅ 审核完成', '关闭', { duration: 3000 });
          this.achievement = updatedAchievement;
          this.reviewComplete.emit(updatedAchievement);
          this.loadReviewHistory();
        },
        error: (error: any) => {
          this.snackBar.open(`审核失败: ${error.error?.message || error.message}`, '关闭', {
            duration: 5000,
          });
        },
      })
      .add(() => {
        this.reviewing = false;
      });
  }

  /**
   * 选择分数
   */
  selectScore(score: number): void {
    this.reviewForm.patchValue({ score });
    this.selectedScore = score;
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
   * 获取状态标签
   */
  getStatusLabel(status: AchievementStatus): string {
    const labels: Record<AchievementStatus, string> = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝',
      revision: '需修改',
    };
    return labels[status] || status;
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(status: AchievementStatus): string {
    const colors: Record<AchievementStatus, string> = {
      pending: '#f59e0b',
      approved: '#10b981',
      rejected: '#ef4444',
      revision: '#f59e0b',
    };
    return colors[status] || '#757575';
  }

  /**
   * 格式化日期
   */
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('zh-CN');
  }

  /**
   * 获取文件图标
   */
  getFileIcon(fileName: string): string {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const iconMap: { [key: string]: string } = {
      pdf: '📕',
      doc: '📘',
      docx: '📘',
      xls: '📗',
      xlsx: '📗',
      ppt: '📙',
      pptx: '📙',
      jpg: '🖼️',
      jpeg: '🖼️',
      png: '🖼️',
      gif: '🖼️',
      mp4: '🎬',
      mov: '🎬',
      avi: '🎬',
      zip: '📦',
      rar: '📦',
    };
    return iconMap[ext || ''] || '📄';
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }
}
