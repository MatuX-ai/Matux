import { CommonModule } from '@angular/common';
import { Component, inject, Input } from '@angular/core';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Achievement, AchievementTemplate } from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-display',
  standalone: true,
  imports: [CommonModule, MatDialogModule],
  templateUrl: './achievement-display.component.html',
  styleUrls: ['./achievement-display.component.scss'],
})
export class AchievementDisplayComponent {
  @Input() achievement!: Achievement;
  @Input() template?: AchievementTemplate;
  @Input() layout: 'card' | 'detail' = 'card';
  @Input() interactive = true;

  private achievementService = inject(AchievementService);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  // 模板默认配置
  private defaultTemplate = {
    id: 0,
    name: 'default',
    type: this.achievement?.type || 'project',
    layout: 'card' as 'card' | 'grid' | 'timeline' | 'masonry' | 'detail',
    styles: {
      backgroundColor: '#ffffff',
      textColor: '#333333',
      accentColor: '#4285f4',
      cardStyle: 'elevated',
      borderRadius: 12,
      showProgress: true,
      showTags: true,
      showDate: true,
    },
    fields: [
      {
        key: 'title',
        label: '标题',
        type: 'text',
        required: true,
        displayInCard: true,
        displayInDetail: true,
      },
      {
        key: 'description',
        label: '描述',
        type: 'text',
        required: true,
        displayInCard: true,
        displayInDetail: true,
      },
      {
        key: 'files',
        label: '文件',
        type: 'file',
        required: true,
        displayInCard: false,
        displayInDetail: true,
      },
      {
        key: 'score',
        label: '评分',
        type: 'rating',
        required: false,
        displayInCard: true,
        displayInDetail: true,
      },
      {
        key: 'tags',
        label: '标签',
        type: 'tags',
        required: false,
        displayInCard: true,
        displayInDetail: true,
      },
      {
        key: 'submittedAt',
        label: '提交时间',
        type: 'date',
        required: true,
        displayInCard: false,
        displayInDetail: true,
      },
    ],
  };

  /**
   * 获取当前模板
   */
  get currentTemplate(): AchievementTemplate | any {
    return this.template || this.defaultTemplate;
  }

  /**
   * 获取样式对象
   */
  get cardStyles(): { [key: string]: string } {
    const styles = this.currentTemplate.styles;
    return {
      'background-color': styles.backgroundColor,
      color: styles.textColor,
      'border-radius': `${styles.borderRadius}px`,
    };
  }

  /**
   * 获取卡片类名
   */
  get cardClass(): string {
    return `achievement-card achievement-card--${this.currentTemplate.styles.cardStyle}`;
  }

  /**
   * 获取布局类名
   */
  get layoutClass(): string {
    return `achievement-display achievement-display--${this.currentTemplate.layout}`;
  }

  /**
   * 判断是否显示字段
   */
  shouldDisplayField(key: string, location: 'card' | 'detail'): boolean {
    const field = this.currentTemplate.fields.find((f: any) => f.key === key);
    if (!field) return false;

    if (location === 'card') return field.displayInCard;
    return field.displayInDetail;
  }

  /**
   * 获取成果类型标签
   */
  getTypeLabel(): string {
    const typeLabels: Record<string, string> = {
      project: '🚀 项目案例',
      certificate: '🎓 证书',
      assignment: '📝 作业',
      portfolio: '🎨 作品集',
      case_study: '📊 案例研究',
      other: '📎 其他',
    };
    return typeLabels[this.achievement.type] || this.achievement.type;
  }

  /**
   * 获取状态标签
   */
  getStatusLabel(): string {
    const statusLabels: Record<string, string> = {
      pending: '⏳ 待审核',
      approved: '✅ 已通过',
      rejected: '❌ 已拒绝',
      revision: '🔄 需修改',
    };
    return statusLabels[this.achievement.status] || this.achievement.status;
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(): string {
    const statusColors: Record<string, string> = {
      pending: '#ff9800',
      approved: '#4caf50',
      rejected: '#f44336',
      revision: '#ff9800',
    };
    return statusColors[this.achievement.status] || '#757575';
  }

  /**
   * 获取分数星级
   */
  getStarRating(): string {
    if (!this.achievement.score) return '';
    const fullStars = Math.floor(this.achievement.score);
    const hasHalfStar = this.achievement.score - fullStars >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    return '⭐'.repeat(fullStars) + (hasHalfStar ? '½' : '') + '☆'.repeat(emptyStars);
  }

  /**
   * 查看详情
   */
  viewDetails(): void {
    // TODO: 实现查看详情逻辑
    console.log('View details:', this.achievement);
  }

  /**
   * 获取摘要
   */
  getSummary(maxLength = 120): string {
    const description = this.achievement.description || '';
    if (description.length <= maxLength) return description;
    return description.substring(0, maxLength) + '...';
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

  /**
   * 格式化日期
   */
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('zh-CN');
  }

  /**
   * 下载文件
   */
  downloadFile(file: { fileName: string; fileUrl: string }): void {
    const link = document.createElement('a');
    link.href = file.fileUrl;
    link.download = file.fileName;
    link.click();
  }

  /**
   * 分享成果
   */
  shareAchievement(): void {
    const shareData = {
      title: this.achievement.title,
      text: this.getSummary(),
      url: window.location.href,
    };

    if (navigator.share) {
      navigator.share(shareData).catch(() => {
        this.copyShareLink();
      });
    } else {
      this.copyShareLink();
    }
  }

  /**
   * 复制分享链接
   */
  private copyShareLink(): void {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(
      () => {
        this.snackBar.open('✅ 链接已复制到剪贴板', '关闭', { duration: 3000 });
      },
      () => {
        this.snackBar.open('❌ 复制失败', '关闭', { duration: 3000 });
      }
    );
  }

  /**
   * 点赞成果
   */
  likeAchievement(): void {
    this.snackBar.open('👍 感谢点赞！', '关闭', { duration: 2000 });
  }

  /**
   * 打开详情对话框
   */
  openDetailDialog(): void {
    // 可以在这里打开一个详细的对话框
  }
}
