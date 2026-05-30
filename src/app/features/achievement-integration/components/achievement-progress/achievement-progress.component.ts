import { CommonModule } from '@angular/common';
import { Component, inject, Input, OnInit } from '@angular/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AchievementProgress, ProgressMilestone } from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-progress',
  standalone: true,
  imports: [CommonModule, MatProgressBarModule, MatProgressSpinnerModule],
  templateUrl: './achievement-progress.component.html',
  styleUrls: ['./achievement-progress.component.scss'],
})
export class AchievementProgressComponent implements OnInit {
  @Input() userId!: number;
  @Input() courseId?: number;
  @Input() moduleId?: number;
  @Input() displayMode: 'full' | 'compact' = 'full';

  private achievementService = inject(AchievementService);

  progress: AchievementProgress | null = null;
  loading = false;

  ngOnInit(): void {
    this.loadProgress();
  }

  /**
   * 加载进度数据
   */
  loadProgress(): void {
    this.loading = true;

    this.achievementService
      .getUserAchievementProgress(this.userId, this.courseId, this.moduleId)
      .subscribe({
        next: (data: AchievementProgress) => {
          this.progress = data;
          this.loading = false;
        },
        error: () => {
          this.loading = false;
        },
      });
  }

  /**
   * 获取进度百分比
   */
  getCompletionPercentage(): number {
    return this.progress?.completionPercentage || 0;
  }

  /**
   * 获取进度颜色
   */
  getProgressColor(): string {
    const percentage = this.getCompletionPercentage();
    if (percentage < 30) return '#f44336';
    if (percentage < 60) return '#ff9800';
    if (percentage < 90) return '#2196f3';
    return '#4caf50';
  }

  /**
   * 获取平均分数星级
   */
  getAverageStarRating(): string {
    const score = this.progress?.averageScore || 0;
    const fullStars = Math.floor(score);
    const hasHalfStar = score - fullStars >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    return '⭐'.repeat(fullStars) + (hasHalfStar ? '½' : '') + '☆'.repeat(emptyStars);
  }

  /**
   * 获取里程碑状态
   */
  getMilestoneStatus(milestone: ProgressMilestone): 'completed' | 'in-progress' | 'pending' {
    if (milestone.achievedAt) return 'completed';
    const totalAchievements = this.progress?.totalAchievements || 0;
    const completedAchievements = this.progress?.completedAchievements || 0;
    const milestoneAchievementCount = milestone.achievementIds.length;

    // 如果已完成的成果数大于等于里程碑的成果数，则认为在进行中
    if (completedAchievements >= milestoneAchievementCount) {
      return 'in-progress';
    }
    return 'pending';
  }

  /**
   * 获取里程碑进度
   */
  getMilestoneProgress(milestone: ProgressMilestone): number {
    const totalAchievements = this.progress?.totalAchievements || 0;
    const completedAchievements = this.progress?.completedAchievements || 0;
    const milestoneAchievementCount = milestone.achievementIds.length;

    if (totalAchievements === 0) return 0;

    // 计算该里程碑的完成比例
    const milestoneCompleted = Math.min(completedAchievements, milestoneAchievementCount);
    return (milestoneCompleted / milestoneAchievementCount) * 100;
  }

  /**
   * 格式化日期
   */
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('zh-CN');
  }

  /**
   * 重新加载
   */
  refresh(): void {
    this.loadProgress();
  }
}
