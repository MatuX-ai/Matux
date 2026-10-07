/**
 * K12 STEM 设计系统 - 组件示例
 * 基于 design-system.json 的统一设计系统
 *
 * 使用说明：
 * 1. 引入设计令牌: @import 'styles/design-tokens/stem-tokens';
 * 2. 引入主题样式: @import 'styles/themes/stem-theme';
 * 3. 使用下方示例组件
 */

/* eslint-disable @typescript-eslint/explicit-function-return-type, @typescript-eslint/explicit-module-boundary-types */
import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

// =============================================================================
// 设计令牌变量 (参考 stem-tokens.scss)
// =============================================================================

/*
// 品牌色彩
$stem-primary: #059669;      // 探索绿主色
$stem-secondary: #0ea5e9;   // 科技蓝辅助色

// 学科主题色
$stem-subject-science: #059669;     // 科学
$stem-subject-technology: #2563eb;   // 技术
$stem-subject-engineering: #f59e0b; // 工程
$stem-subject-math: #8b5cf6;        // 数学
$stem-subject-arts: #ec4899;        // 艺术

// 功能色
$stem-success: #059669;
$stem-warning: #f59e0b;
$stem-error: #ef4444;

// 圆角
$stem-card-radius: 1.25rem;  // 20px
$stem-btn-radius: 9999px;     // 完全圆角
$stem-input-radius: 1rem;     // 16px

// 阴影
$stem-shadow-card: 0 1px 3px 0 rgba(5, 150, 105, 0.08);
$stem-shadow-card-hover: 0 14px 28px rgba(5, 150, 105, 0.12);

// 动画
$stem-transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
*/

// =============================================================================
// 示例组件接口
// =============================================================================

export interface StemCourse {
  id: string;
  title: string;
  description: string;
  subject: 'science' | 'technology' | 'engineering' | 'math' | 'arts';
  level: 'beginner' | 'intermediate' | 'advanced';
  progress: number;
  duration: string;
  lessons: number;
  imageUrl?: string;
  isLocked?: boolean;
  isMastered?: boolean;
}

// =============================================================================
// 示例组件代码
// =============================================================================

/**
 * STEMCourseCardComponent - 课程卡片组件
 *
 * 使用示例:
 * <app-stem-course-card
 *   [course]="courseData"
 *   (cardClick)="onCourseClick($event)">
 * </app-stem-course-card>
 */
@Component({
  selector: 'app-stem-course-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div
      class="stem-card"
      [class.locked]="course.isLocked"
      [class.mastered]="course.isMastered"
      (click)="!course.isLocked && handleCardClick()"
    >
      <!-- 学科标签 -->
      <div class="stem-card__subject-badge" [ngClass]="'subject--' + course.subject">
        <span class="subject-icon">{{ getSubjectIcon(course.subject) }}</span>
        <span class="subject-name">{{ getSubjectName(course.subject) }}</span>
      </div>

      <!-- 课程封面 -->
      <div class="stem-card__cover">
        <img *ngIf="course.imageUrl" [src]="course.imageUrl" [alt]="course.title" />
        <div *ngIf="!course.imageUrl" class="stem-card__cover-placeholder">
          {{ getSubjectIcon(course.subject) }}
        </div>

        <!-- 锁定状态遮罩 -->
        <div *ngIf="course.isLocked" class="stem-card__locked-overlay">
          <span class="lock-icon">🔒</span>
        </div>
      </div>

      <!-- 课程内容 -->
      <div class="stem-card__content">
        <h3 class="stem-card__title">{{ course.title }}</h3>
        <p class="stem-card__description">{{ course.description }}</p>

        <!-- 课程信息 -->
        <div class="stem-card__meta">
          <span class="meta-item">
            <span class="meta-icon">⏱️</span>
            {{ course.duration }}
          </span>
          <span class="meta-item">
            <span class="meta-icon">📚</span>
            {{ course.lessons }} 课时
          </span>
        </div>

        <!-- 学习进度 -->
        <div *ngIf="!course.isLocked" class="stem-card__progress">
          <div class="progress-bar">
            <div class="progress-fill" [style.width.%]="course.progress"></div>
          </div>
          <span class="progress-text">{{ course.progress }}%</span>
        </div>

        <!-- 等级标签 -->
        <div class="stem-card__level" [ngClass]="'level--' + course.level">
          {{ getLevelName(course.level) }}
        </div>
      </div>

      <!-- 操作按钮 -->
      <button
        *ngIf="!course.isLocked"
        class="stem-card__action-btn"
        (click)="onActionClick($event)"
      >
        {{ course.progress > 0 ? '继续学习' : '开始学习' }}
      </button>
    </div>
  `,
  styles: [
    `
      // STEM 卡片基础样式
      .stem-card {
        // 圆角 - 使用设计令牌
        border-radius: 20px;
        padding: 24px;
        background: #ffffff;
        box-shadow: 0 1px 3px 0 rgba(5, 150, 105, 0.08);
        border: 1px solid rgba(5, 150, 105, 0.1);
        cursor: pointer;
        transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);

        &:hover {
          transform: translateY(-4px);
          box-shadow:
            0 14px 28px rgba(5, 150, 105, 0.12),
            0 10px 10px rgba(5, 150, 105, 0.06);
        }

        &.locked {
          opacity: 0.7;
          cursor: not-allowed;

          &:hover {
            transform: none;
            box-shadow: 0 1px 3px 0 rgba(5, 150, 105, 0.08);
          }
        }

        &.mastered {
          border-color: rgba(245, 158, 11, 0.3);
          background: linear-gradient(135deg, #ffffff 0%, #fef3c7 100%);
        }
      }

      // 学科标签
      .stem-card__subject-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 12px;

        &.subject--science {
          background: #d1fae5;
          color: #065f46;
        }
        &.subject--technology {
          background: #dbeafe;
          color: #1e40af;
        }
        &.subject--engineering {
          background: #fef3c7;
          color: #92400e;
        }
        &.subject--math {
          background: #ede9fe;
          color: #5b21b6;
        }
        &.subject--arts {
          background: #fce7f3;
          color: #9d174d;
        }
      }

      // 课程封面
      .stem-card__cover {
        position: relative;
        width: 100%;
        aspect-ratio: 16 / 9;
        border-radius: 12px;
        overflow: hidden;
        margin-bottom: 16px;
        background: linear-gradient(135deg, #059669 0%, #0ea5e9 100%);

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .stem-card__cover-placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
        font-size: 48px;
      }

      .stem-card__locked-overlay {
        position: absolute;
        inset: 0;
        background: rgba(15, 23, 42, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;

        .lock-icon {
          font-size: 32px;
        }
      }

      // 课程内容
      .stem-card__content {
        margin-bottom: 16px;
      }

      .stem-card__title {
        font-size: 18px;
        font-weight: 700;
        color: #1c1917;
        margin: 0 0 8px 0;
        line-height: 1.3;
      }

      .stem-card__description {
        font-size: 14px;
        color: #57534e;
        margin: 0 0 12px 0;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      // 课程元信息
      .stem-card__meta {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;
      }

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: #78716c;
      }

      // 学习进度
      .stem-card__progress {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
      }

      .progress-bar {
        flex: 1;
        height: 8px;
        background: #e7e5e4;
        border-radius: 9999px;
        overflow: hidden;
      }

      .progress-fill {
        height: 100%;
        background: linear-gradient(135deg, #059669 0%, #0ea5e9 100%);
        border-radius: 9999px;
        transition: width 300ms ease;
      }

      .progress-text {
        font-size: 12px;
        font-weight: 600;
        color: #059669;
        min-width: 40px;
      }

      // 等级标签
      .stem-card__level {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 500;

        &.level--beginner {
          background: #d1fae5;
          color: #065f46;
        }
        &.level--intermediate {
          background: #fef3c7;
          color: #92400e;
        }
        &.level--advanced {
          background: #fee2e2;
          color: #991b1b;
        }
      }

      // 操作按钮
      .stem-card__action-btn {
        width: 100%;
        height: 44px;
        border: none;
        border-radius: 9999px;
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #ffffff;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.15);

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.2);
        }

        &:active {
          transform: translateY(0);
        }
      }
    `,
  ],
})
export class StemCourseCardComponent {
  @Input() course!: StemCourse;
  @Input() cardClickHandler?: () => void;
  @Input() actionClickHandler?: (event: Event) => void;

  getSubjectIcon(subject: string): string {
    const icons: Record<string, string> = {
      science: '🔬',
      technology: '💻',
      engineering: '⚙️',
      math: '📐',
      arts: '🎨',
    };
    return icons[subject] || '📚';
  }

  getSubjectName(subject: string): string {
    const names: Record<string, string> = {
      science: '科学',
      technology: '技术',
      engineering: '工程',
      math: '数学',
      arts: '艺术',
    };
    return names[subject] || subject;
  }

  getLevelName(level: string): string {
    const names: Record<string, string> = {
      beginner: '入门',
      intermediate: '进阶',
      advanced: '高级',
    };
    return names[level] || level;
  }

  handleCardClick() {
    this.cardClickHandler?.();
  }

  handleActionClick(event: Event) {
    event.stopPropagation();
    this.actionClickHandler?.(event);
  }
}

/**
 * StemProgressRingComponent - 进度环组件
 *
 * 使用示例:
 * <app-stem-progress-ring
 *   [progress]="75"
 *   [size]="120"
 *   [subject]="'science'">
 * </app-stem-progress-ring>
 */
@Component({
  selector: 'app-stem-progress-ring',
  template: `
    <div class="stem-progress-ring" [style.width.px]="size" [style.height.px]="size">
      <svg [attr.viewBox]="'0 0 ' + size + ' ' + size">
        <!-- 背景环 -->
        <circle
          class="ring-bg"
          [attr.cx]="size / 2"
          [attr.cy]="size / 2"
          [attr.r]="radius"
          fill="none"
          [attr.stroke-width]="strokeWidth"
        />
        <!-- 进度环 -->
        <circle
          class="ring-progress"
          [attr.cx]="size / 2"
          [attr.cy]="size / 2"
          [attr.r]="radius"
          fill="none"
          [attr.stroke-width]="strokeWidth"
          [attr.stroke-dasharray]="circumference"
          [attr.stroke-dashoffset]="strokeDashoffset"
          [style.stroke]="getSubjectColor()"
        />
      </svg>
      <div class="ring-content">
        <span class="ring-value">{{ progress }}%</span>
        <span class="ring-label">完成</span>
      </div>
    </div>
  `,
  styles: [
    `
      .stem-progress-ring {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
      }

      svg {
        transform: rotate(-90deg);
      }

      .ring-bg {
        stroke: #e7e5e4;
      }

      .ring-progress {
        transition: stroke-dashoffset 500ms ease;
        stroke-linecap: round;
      }

      .ring-content {
        position: absolute;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }

      .ring-value {
        font-size: 24px;
        font-weight: 700;
        color: #1c1917;
      }

      .ring-label {
        font-size: 12px;
        color: #57534e;
      }
    `,
  ],
})
export class StemProgressRingComponent {
  @Input() progress = 0;
  @Input() size = 120;
  @Input() strokeWidth = 8;
  @Input() subject: 'science' | 'technology' | 'engineering' | 'math' | 'arts' = 'science';

  get radius(): number {
    return (this.size - this.strokeWidth) / 2;
  }

  get circumference(): number {
    return 2 * Math.PI * this.radius;
  }

  get strokeDashoffset(): number {
    const progressValue = Math.min(Math.max(this.progress, 0), 100);
    return this.circumference * (1 - progressValue / 100);
  }

  getSubjectColor(): string {
    const colors: Record<string, string> = {
      science: '#059669',
      technology: '#0ea5e9',
      engineering: '#f59e0b',
      math: '#8b5cf6',
      arts: '#ec4899',
    };
    return colors[this.subject] || '#059669';
  }
}

/**
 * StemAchievementBadgeComponent - 成就徽章组件
 *
 * 使用示例:
 * <app-stem-achievement-badge
 *   [badge]="achievementData"
 *   [size]="'large'">
 * </app-stem-achievement-badge>
 */
@Component({
  selector: 'app-stem-achievement-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="stem-badge" [ngClass]="'badge--' + size" [class.earned]="badge.earned">
      <div class="badge__icon" [style.background]="getBadgeGradient()">
        {{ badge.icon }}
      </div>
      <div class="badge__info">
        <span class="badge__name">{{ badge.name }}</span>
        <span class="badge__desc">{{ badge.description }}</span>
      </div>
      <div *ngIf="badge.earned" class="badge__check">✓</div>
    </div>
  `,
  styles: [
    `
      .stem-badge {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 1px 3px 0 rgba(5, 150, 105, 0.08);
        transition: all 250ms ease;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.12);
        }

        &.earned {
          background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
          border: 1px solid rgba(5, 150, 105, 0.2);

          .badge__icon {
            animation: pulse-glow 2s ease-in-out infinite;
          }
        }

        &.badge--small {
          padding: 8px 12px;
          .badge__icon {
            width: 32px;
            height: 32px;
            font-size: 16px;
          }
          .badge__name {
            font-size: 12px;
          }
          .badge__desc {
            font-size: 10px;
          }
        }

        &.badge--medium {
          .badge__icon {
            width: 48px;
            height: 48px;
            font-size: 24px;
          }
          .badge__name {
            font-size: 14px;
          }
          .badge__desc {
            font-size: 12px;
          }
        }

        &.badge--large {
          padding: 16px 20px;
          .badge__icon {
            width: 64px;
            height: 64px;
            font-size: 32px;
          }
          .badge__name {
            font-size: 16px;
          }
          .badge__desc {
            font-size: 14px;
          }
        }
      }

      .badge__icon {
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        font-size: 24px;
        box-shadow: 0 0 10px rgba(5, 150, 105, 0.2);
      }

      .badge__info {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .badge__name {
        font-weight: 600;
        color: #1c1917;
      }

      .badge__desc {
        color: #57534e;
      }

      .badge__check {
        margin-left: auto;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #059669;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
      }

      @keyframes pulse-glow {
        0%,
        100% {
          box-shadow: 0 0 10px rgba(5, 150, 105, 0.3);
        }
        50% {
          box-shadow: 0 0 20px rgba(5, 150, 105, 0.5);
        }
      }
    `,
  ],
})
export class StemAchievementBadgeComponent {
  @Input() badge!: { icon: string; name: string; description: string; earned: boolean };
  @Input() size: 'small' | 'medium' | 'large' = 'medium';

  getBadgeGradient(): string {
    if (!this.badge.earned) {
      return '#e7e5e4';
    }
    return 'linear-gradient(135deg, #059669 0%, #0ea5e9 100%)';
  }
}

// =============================================================================
// 使用指南
// =============================================================================

/**
 * 如何在 Angular 项目中使用 K12 STEM 设计系统:
 *
 * 1. 引入样式文件
 *    在 angular.json 或 styles.scss 中添加:
 *    @import 'styles/design-tokens/stem-tokens';
 *    @import 'styles/themes/stem-theme';
 *
 * 2. 使用组件
 *    import { StemCourseCardComponent } from './components/stem-course-card';
 *
 * 3. 应用设计令牌
 *    在 SCSS 中使用 $stem-primary 等变量
 *
 * 4. 查看设计文档
 *    参考 docs/design-system.json 获取完整设计规范
 */
