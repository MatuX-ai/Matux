/**
 * 学习画像展示组件
 *
 * PRD 6.6 关键页面线框 - "我的画像"
 * 展示：AI教师眼中的你、能力雷达图、技能树、薄弱环节
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import {
  AbilityDimensions,
  SkillTreeNode,
  StudentLearningProfile,
  WeakPoint,
} from '../../../core/models/ai-teacher.models';

@Component({
  selector: 'app-learning-profile',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="profile-container">
      <!-- AI 教师眼中的你 -->
      <mat-card class="ai-summary-card">
        <mat-card-header>
          <mat-icon mat-card-avatar class="ai-avatar">smart_toy</mat-icon>
          <mat-card-title>AI 教师眼中的你</mat-card-title>
          <mat-card-subtitle>基于你的学习数据自动生成</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p class="ai-summary-text">{{ personaSeed }}</p>
          <div class="quick-stats">
            <div class="stat-item">
              <mat-icon class="stat-icon">favorite</mat-icon>
              <span class="stat-label">最喜欢的领域</span>
              <span class="stat-value">{{ favoriteField }}</span>
            </div>
            <div class="stat-item">
              <mat-icon class="stat-icon">schedule</mat-icon>
              <span class="stat-label">最佳学习时段</span>
              <span class="stat-value">下午 3-5 点</span>
            </div>
            <div class="stat-item">
              <mat-icon class="stat-icon">local_fire_department</mat-icon>
              <span class="stat-label">连续学习</span>
              <span class="stat-value">{{ profile?.currentStreakDays ?? 0 }} 天 🔥</span>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 能力雷达图 -->
      <mat-card class="radar-card">
        <mat-card-header>
          <mat-card-title>能力雷达图</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="radar-chart-placeholder">
            <svg viewBox="0 0 300 300" class="radar-svg">
              <!-- 绘制雷达图背景 -->
              <polygon *ngFor="let level of radarLevels"
                [attr.points]="getRadarPoints(level)"
                fill="none"
                [attr.stroke]="level === 100 ? '#e0e0e0' : '#f0f0f0'"
                stroke-width="1"/>
              <!-- 绘制数据区域 -->
              <polygon [attr.points]="getAbilityRadarPoints()"
                fill="rgba(59,130,246,0.2)"
                stroke="#3b82f6"
                stroke-width="2"/>
              <!-- 绘制数据点标签 -->
              <text *ngFor="let dim of abilityDimensionList; let i = index"
                [attr.x]="getLabelX(i)"
                [attr.y]="getLabelY(i)"
                text-anchor="middle"
                font-size="12"
                fill="#64748b">{{ dim.label }}</text>
              <!-- 绘制数据点值 -->
              <text *ngFor="let dim of abilityDimensionList; let i = index"
                [attr.x]="getLabelX(i)"
                [attr.y]="getLabelY(i) + 14"
                text-anchor="middle"
                font-size="11"
                font-weight="bold"
                fill="#3b82f6">{{ dim.value }}</text>
            </svg>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 技能树 -->
      <mat-card class="skill-tree-card">
        <mat-card-header>
          <mat-card-title>技能树</mat-card-title>
          <button mat-button color="primary" class="expand-btn">展开全部</button>
        </mat-card-header>
        <mat-card-content>
          <div *ngFor="let tree of profile?.skillTree ?? []" class="skill-category">
            <h4 class="category-title">{{ tree.name }}</h4>
            <div class="skill-children">
              <div *ngFor="let child of tree.children ?? []"
                class="skill-item"
                [class.mastered]="child.status === 'mastered'"
                [class.learning]="child.status === 'learning'"
                [class.locked]="child.status === 'not_started'">
                <mat-icon class="skill-status-icon">
                  {{ child.status === 'mastered' ? 'check_circle' : child.status === 'learning' ? 'autorenew' : 'lock' }}
                </mat-icon>
                <span class="skill-name">{{ child.name }}</span>
                <span *ngIf="child.status !== 'not_started'" class="skill-progress-text">
                  ({{ child.progress * 100 | number:'1.0-0' }}%)
                </span>
                <span *ngIf="child.status === 'learning'" class="current-badge">← 当前学习</span>
                <mat-progress-bar *ngIf="child.status !== 'not_started'"
                  mode="determinate"
                  [value]="child.progress * 100"
                  class="skill-progress">
                </mat-progress-bar>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 薄弱环节 -->
      <mat-card class="weak-points-card">
        <mat-card-header>
          <mat-card-title>薄弱环节（AI 教师诊断）</mat-card-title>
          <button mat-button color="primary">查看详情</button>
        </mat-card-header>
        <mat-card-content>
          <div *ngFor="let wp of profile?.weakPoints ?? []" class="weak-point-item">
            <mat-icon class="warning-icon">warning</mat-icon>
            <div class="weak-point-info">
              <span class="wp-name">{{ wp.knowledgePoint }}</span>
              <span class="wp-mastery">正确率 {{ wp.mastery * 100 | number:'1.0-0' }}%</span>
              <span class="wp-suggestion">建议：{{ wp.suggestion }}</span>
            </div>
            <mat-progress-bar mode="determinate" [value]="wp.mastery * 100" class="wp-progress"></mat-progress-bar>
          </div>
          <div *ngIf="!(profile?.weakPoints?.length)" class="no-weak-points">
            <mat-icon>sentiment_very_satisfied</mat-icon>
            <span>暂无明显薄弱环节，继续保持！</span>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .profile-container {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      padding: 16px;
    }
    .ai-summary-card { grid-column: 1; }
    .radar-card { grid-column: 2; }
    .skill-tree-card { grid-column: 1 / -1; }
    .weak-points-card { grid-column: 1 / -1; }

    .ai-summary-text {
      font-size: 14px;
      line-height: 1.6;
      color: #334155;
      padding: 12px;
      background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
      border-radius: 12px;
      border-left: 4px solid #3b82f6;
    }
    .quick-stats {
      display: flex;
      gap: 24px;
      margin-top: 16px;
    }
    .stat-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
    }
    .stat-icon { color: #3b82f6; font-size: 20px; }
    .stat-label { font-size: 12px; color: #64748b; }
    .stat-value { font-size: 14px; font-weight: 600; color: #0f172a; }

    .ai-avatar {
      font-size: 40px;
      color: #3b82f6;
      background: linear-gradient(135deg, #dbeafe, #ede9fe);
      border-radius: 50%;
      padding: 8px;
    }

    .radar-chart-placeholder {
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .radar-svg { width: 100%; max-width: 300px; height: auto; }

    .skill-category { margin-bottom: 16px; }
    .category-title {
      font-size: 16px;
      font-weight: 600;
      color: #0f172a;
      margin-bottom: 8px;
      padding-left: 8px;
      border-left: 3px solid #3b82f6;
    }
    .skill-children { padding-left: 16px; }
    .skill-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      font-size: 14px;
    }
    .skill-status-icon { font-size: 18px; }
    .mastered .skill-status-icon { color: #22c55e; }
    .learning .skill-status-icon { color: #f59e0b; }
    .locked .skill-status-icon { color: #94a3b8; }
    .skill-name { color: #334155; }
    .skill-progress-text { color: #64748b; font-size: 12px; }
    .current-badge { color: #3b82f6; font-size: 12px; font-weight: 500; }
    .skill-progress { flex: 1; max-width: 120px; height: 4px; }
    .locked { color: #94a3b8; }
    .expand-btn { margin-left: auto; }

    .weak-point-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px;
      border-radius: 8px;
      margin-bottom: 8px;
      background: #fffbeb;
    }
    .warning-icon { color: #f59e0b; }
    .weak-point-info {
      display: flex;
      flex-direction: column;
      gap: 2px;
      flex: 1;
    }
    .wp-name { font-weight: 500; color: #0f172a; }
    .wp-mastery { font-size: 12px; color: #64748b; }
    .wp-suggestion { font-size: 12px; color: #3b82f6; }
    .wp-progress { width: 80px; height: 4px; }
    .no-weak-points {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #22c55e;
      padding: 16px;
      justify-content: center;
    }

    @media (max-width: 768px) {
      .profile-container { grid-template-columns: 1fr; }
      .ai-summary-card, .radar-card { grid-column: 1; }
      .quick-stats { flex-wrap: wrap; }
    }
  `],
})
export class LearningProfileComponent implements OnChanges {
  @Input() profile: StudentLearningProfile | null = null;

  personaSeed = '';
  favoriteField = '游戏开发';
  radarLevels = [20, 40, 60, 80, 100];

  abilityDimensionList: { label: string; value: number; key: keyof AbilityDimensions }[] = [
    { label: '编程思维', value: 0, key: 'programmingThinking' },
    { label: '算法能力', value: 0, key: 'algorithmAbility' },
    { label: '调试能力', value: 0, key: 'debuggingSkill' },
    { label: '项目实践', value: 0, key: 'projectPractice' },
    { label: 'STEM实验', value: 0, key: 'stemExperiment' },
    { label: '独立完成', value: 0, key: 'independentCompletion' },
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['profile'] && this.profile) {
      this.personaSeed = this.generatePersonaSeed(this.profile);
      this.favoriteField = this.getFavoriteField(this.profile);
      this.abilityDimensionList = this.abilityDimensionList.map((dim) => ({
        ...dim,
        value: this.profile?.abilityDimensions[dim.key] ?? 0,
      }));
    }
  }

  /** 生成画像摘要 */
  private generatePersonaSeed(profile: StudentLearningProfile): string {
    const styleMap = { visual: '视觉型', auditory: '听觉型', reading: '读写型', kinesthetic: '动觉型' };
    const weakStr = profile.weakPoints
      .slice(0, 2)
      .map((w) => w.knowledgePoint)
      .join('、');
    return `${profile.displayName}是一个${styleMap[profile.learningStyle]}学习者，擅长通过动画和图表理解概念。编程逻辑${profile.abilityDimensions.programmingThinking}/100，但在代码规范上还需要多加注意。最喜欢的领域：${this.getFavoriteField(profile)}。${weakStr ? '薄弱环节：' + weakStr : ''}。连续学习${profile.currentStreakDays}天 🔥`;
  }

  private getFavoriteField(profile: StudentLearningProfile): string {
    const fieldMap: Record<string, string> = {
      game_development: '游戏开发',
      robotics: '机器人',
      '3d_modeling': '3D建模',
      ai: '人工智能',
      hardware: '硬件',
    };
    return profile.interestPreferences[0]
      ? fieldMap[profile.interestPreferences[0]] ?? profile.interestPreferences[0]
      : '探索中';
  }

  /** 计算雷达图背景多边形顶点 */
  getRadarPoints(level: number): string {
    const n = this.abilityDimensionList.length;
    const cx = 150, cy = 150, maxR = 120;
    const r = (level / 100) * maxR;
    return Array.from({ length: n }, (_, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
    }).join(' ');
  }

  /** 计算能力数据多边形顶点 */
  getAbilityRadarPoints(): string {
    const n = this.abilityDimensionList.length;
    const cx = 150, cy = 150, maxR = 120;
    return this.abilityDimensionList.map((dim, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      const r = (dim.value / 100) * maxR;
      return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
    }).join(' ');
  }

  /** 标签位置X */
  getLabelX(index: number): number {
    const n = this.abilityDimensionList.length;
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
    return 150 + 145 * Math.cos(angle);
  }

  /** 标签位置Y */
  getLabelY(index: number): number {
    const n = this.abilityDimensionList.length;
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
    return 150 + 145 * Math.sin(angle);
  }
}
