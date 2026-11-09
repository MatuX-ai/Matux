/**
 * 学习地图节点详情弹窗（P2-A）
 *
 * 显示节点的所有信息：
 * - 图标 / 名称 / 描述 / 状态 / 进度
 * - 前置技能列表
 * - 关联课程列表（点击跳转到课程）
 * - 关联成就列表（点击跳转到成就）
 * - 学习按钮 / 解锁提示
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  Inject,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import {
  MAT_DIALOG_DATA,
  MatDialogModule,
  MatDialogRef,
} from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import {
  LearningMapNode,
  LearningMapTrack,
  NODE_STATUS_CONFIG,
} from '../../../core/models/learning-map.model';

export interface LearningMapNodeDetailData {
  node: LearningMapNode;
  track: LearningMapTrack | null;
}

export interface LearningMapNodeDetailResult {
  action: 'learn' | 'achievement' | 'close';
  courseId?: string;
  courseTitle?: string;
  achievementId?: string;
}

@Component({
  selector: 'app-learning-map-node-detail',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  template: `
    <div class="dialog-wrapper" [class]="'status-' + node.status">
      <!-- 头部 -->
      <div class="dialog-header">
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>

        <div class="header-icon-wrap" [class]="getHeaderClass()">
          <span class="header-emoji">{{ node.icon }}</span>
          <span
            class="header-status"
            [style.background]="statusConfig[node.status].color"
          >
            {{ statusConfig[node.status].emoji }} {{ statusConfig[node.status].label }}
          </span>
        </div>

        <h3 class="header-name">{{ node.name }}</h3>
        <div class="header-meta">
          <span class="meta-item">
            <mat-icon>schedule</mat-icon>
            约 {{ node.estimatedMinutes }} 分钟
          </span>
          <span class="meta-item" *ngIf="node.tier">
            <mat-icon>military_tech</mat-icon>
            Tier {{ node.tier }}
          </span>
        </div>
      </div>

      <!-- 内容 -->
      <div class="dialog-body">
        <!-- 描述 -->
        <div class="section">
          <h4 class="section-label">技能描述</h4>
          <p class="section-text">{{ node.description }}</p>
        </div>

        <!-- 进度（未完成时） -->
        <div class="section" *ngIf="canShowProgress()">
          <div class="progress-box">
            <div class="progress-header">
              <span class="progress-label">完成进度</span>
              <span class="progress-value">
                {{ (node.progress * 100) | number: '1.0-0' }}%
              </span>
            </div>
            <mat-progress-bar
              mode="determinate"
              [value]="node.progress * 100"
              [color]="node.status === 'mastered' || node.status === 'legendary' ? 'accent' : 'primary'"
            ></mat-progress-bar>
          </div>
        </div>

        <!-- 前置技能 -->
        <div class="section" *ngIf="node.prerequisites?.length">
          <h4 class="section-label">
            <mat-icon class="label-icon">link</mat-icon>
            前置技能（{{ node.prerequisites.length }}）
          </h4>
          <div class="prereq-list">
            <div
              *ngFor="let pid of node.prerequisites"
              class="prereq-item"
              [class.completed]="isPrereqMastered(pid)"
            >
              <span class="prereq-icon">
                {{ isPrereqMastered(pid) ? '✅' : '⭕' }}
              </span>
              <span class="prereq-name">{{ getPrereqName(pid) }}</span>
              <span
                class="prereq-status"
                [style.color]="isPrereqMastered(pid) ? '#10b981' : '#94a3b8'"
              >
                {{ isPrereqMastered(pid) ? '已掌握' : '未完成' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 关联课程 -->
        <div class="section" *ngIf="node.relatedCourses?.length">
          <h4 class="section-label">
            <mat-icon class="label-icon">school</mat-icon>
            推荐课程（{{ node.relatedCourses.length }}）
          </h4>
          <div class="course-list">
            <div
              *ngFor="let course of node.relatedCourses"
              class="course-item"
              (click)="learnCourse(course.id, course.title)"
            >
              <mat-icon class="course-icon">play_circle_outline</mat-icon>
              <span class="course-title">{{ course.title }}</span>
              <mat-icon class="course-arrow">chevron_right</mat-icon>
            </div>
          </div>
        </div>

        <!-- 关联成就 -->
        <div class="section" *ngIf="node.relatedAchievementIds?.length">
          <h4 class="section-label">
            <mat-icon class="label-icon">emoji_events</mat-icon>
            完成可解锁成就
          </h4>
          <div class="achievement-chips">
            <button
              *ngFor="let aid of node.relatedAchievementIds"
              mat-stroked-button
              class="achievement-chip"
              (click)="viewAchievement(aid)"
              matTooltip="查看成就"
            >
              🏆 {{ aid }}
            </button>
          </div>
        </div>

        <!-- 锁定状态提示 -->
        <div class="locked-notice" *ngIf="node.status === 'locked'">
          <mat-icon class="notice-icon">info</mat-icon>
          <span>请先完成前置技能以解锁此节点</span>
        </div>

        <!-- 操作按钮 -->
        <div class="dialog-actions">
          <button mat-stroked-button class="action-btn" (click)="close()">
            关闭
          </button>
          <button
            *ngIf="canLearn()"
            mat-flat-button
            color="primary"
            class="action-btn primary"
            (click)="learn()"
          >
            <mat-icon>{{ node.status === 'in_progress' ? 'play_arrow' : 'auto_awesome' }}</mat-icon>
            {{ node.status === 'in_progress' ? '继续学习' : '开始学习' }}
          </button>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./learning-map-node-detail.component.scss'],
})
export class LearningMapNodeDetailComponent {
  readonly statusConfig = NODE_STATUS_CONFIG;
  readonly Math = Math;

  node: LearningMapNode;
  track: LearningMapTrack | null;

  private dialogRef = inject(MatDialogRef<LearningMapNodeDetailComponent>);

  constructor(@Inject(MAT_DIALOG_DATA) data: LearningMapNodeDetailData) {
    this.node = data.node;
    this.track = data.track;
  }

  // ============ 模板辅助 ============

  canLearn(): boolean {
    return this.node.status !== 'locked';
  }

  canShowProgress(): boolean {
    return ['in_progress', 'mastered', 'legendary'].includes(this.node.status);
  }

  isPrereqMastered(id: string): boolean {
    if (!this.track) return false;
    const prereq = this.track.nodes.find((n) => n.id === id);
    return prereq?.status === 'mastered' || prereq?.status === 'legendary';
  }

  getPrereqName(id: string): string {
    if (!this.track) return id;
    return this.track.nodes.find((n) => n.id === id)?.name ?? id;
  }

  getHeaderClass(): string {
    return `header-icon status-${this.node.status}`;
  }

  // ============ 操作 ============

  close(): void {
    this.dialogRef.close({ action: 'close' } as LearningMapNodeDetailResult);
  }

  learn(): void {
    if (this.node.relatedCourses?.length) {
      const course = this.node.relatedCourses[0];
      this.dialogRef.close({
        action: 'learn',
        courseId: course.id,
        courseTitle: course.title,
      } as LearningMapNodeDetailResult);
    } else {
      // 没有关联课程，模拟一个
      this.dialogRef.close({
        action: 'learn',
        courseId: this.node.id,
        courseTitle: this.node.name,
      } as LearningMapNodeDetailResult);
    }
  }

  learnCourse(courseId: string, courseTitle: string): void {
    this.dialogRef.close({
      action: 'learn',
      courseId,
      courseTitle,
    } as LearningMapNodeDetailResult);
  }

  viewAchievement(achievementId: string): void {
    this.dialogRef.close({
      action: 'achievement',
      achievementId,
    } as LearningMapNodeDetailResult);
  }
}