/**
 * 学习画像页面
 *
 * PRD 6.6 关键页面线框 - "我的学习画像"
 * 展示：AI教师摘要、能力雷达图、技能树、薄弱环节诊断
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NgxEchartsModule } from 'ngx-echarts';
import type { EChartsOption } from 'echarts';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import type { StudentLearningProfile, SkillTreeNode } from '../../../core/models/ai-teacher.models';
import type { User } from '../../../core/models/auth.models';

@Component({
  selector: 'app-learning-profile',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatTooltipModule,
    NgxEchartsModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="profile-container">
      <div class="page-header">
        <h1 class="page-title">我的学习画像</h1>
        <span class="update-time" *ngIf="profile?.updatedAt">
          最后更新：{{ profile!.updatedAt | date:'yyyy-MM-dd HH:mm' }}
        </span>
      </div>

      <!-- AI教师摘要 + 能力雷达图 双栏 -->
      <div class="dual-column-section">
        <!-- AI 教师眼中的你 -->
        <mat-card class="teacher-summary-card">
          <mat-card-header>
            <mat-icon mat-card-avatar class="ai-avatar">smart_toy</mat-icon>
            <mat-card-title>🤖 AI 教师眼中的你</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="profile-summary-text" *ngIf="profile">
              <p class="summary-quote">"{{ teacherSummary }}"</p>
              <div class="summary-meta">
                <div class="meta-item">
                  <mat-icon>favorite</mat-icon>
                  <span>最喜欢的领域：{{ getTopInterest() }}</span>
                </div>
                <div class="meta-item">
                  <mat-icon>schedule</mat-icon>
                  <span>最佳学习时段：下午 3-5 点</span>
                </div>
                <div class="meta-item">
                  <mat-icon>local_fire_department</mat-icon>
                  <span>连续学习：{{ profile.currentStreakDays }} 天 🔥</span>
                </div>
              </div>
            </div>
            <div class="profile-empty" *ngIf="!profile">
              <mat-icon>hourglass_empty</mat-icon>
              <p>正在生成你的学习画像...</p>
            </div>
          </mat-card-content>
        </mat-card>

        <!-- 能力雷达图 -->
        <mat-card class="radar-card">
          <mat-card-header>
            <mat-card-title>能力雷达图</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div echarts [options]="radarOption" class="radar-chart"></div>
            <div class="radar-legend">
              <span class="legend-item current">
                <span class="dot"></span> 本月
              </span>
              <span class="legend-item previous">
                <span class="dot"></span> 上月
              </span>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- 技能树 -->
      <mat-card class="skill-tree-card">
        <mat-card-header>
          <mat-card-title>技能树</mat-card-title>
          <button mat-button color="primary" (click)="expandAll = !expandAll">
            {{ expandAll ? '收起全部' : '展开全部' }}
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="skill-tree">
            <div *ngFor="let category of skillTreeCategories" class="skill-category">
              <div class="category-header" (click)="toggleCategory(category.id)">
                <mat-icon>{{ expandAll ? 'expand_more' : 'chevron_right' }}</mat-icon>
                <span class="category-name">{{ category.name }}</span>
                <span class="category-progress">{{ getCategoryProgress(category.id) }}%</span>
                <mat-progress-bar
                  mode="determinate"
                  [value]="getCategoryProgress(category.id)"
                  class="category-progress-bar"
                ></mat-progress-bar>
              </div>
              <div class="skill-children" *ngIf="expandAll || expandedCategories.has(category.id)">
                <div *ngFor="let skill of category.children" class="skill-item"
                  [class.mastered]="skill.status === 'mastered'"
                  [class.learning]="skill.status === 'learning'"
                  [class.locked]="skill.status === 'not_started'">
                  <span class="skill-status-icon">
                    {{ skill.status === 'mastered' ? '✅' : skill.status === 'learning' ? '🔄' : '🔒' }}
                  </span>
                  <span class="skill-name">{{ skill.name }}</span>
                  <span class="skill-progress" *ngIf="skill.status !== 'not_started'">
                    ({{ Math.round(skill.progress * 100) }}%)
                  </span>
                  <span class="skill-badge current-badge" *ngIf="skill.status === 'learning'">当前学习</span>
                  <span class="skill-badge locked-badge" *ngIf="skill.status === 'not_started' && skill.unlockRequirement">
                    需解锁：{{ skill.unlockRequirement }}
                  </span>
                  <mat-progress-bar
                    mode="determinate"
                    [value]="skill.progress * 100"
                    class="skill-progress-bar"
                  ></mat-progress-bar>
                </div>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 薄弱环节诊断 -->
      <mat-card class="weak-points-card" *ngIf="profile?.weakPoints?.length">
        <mat-card-header>
          <mat-icon mat-card-avatar class="warn-avatar">warning_amber</mat-icon>
          <mat-card-title>薄弱环节（AI 教师诊断）</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="weak-points-list">
            <div *ngFor="let wp of profile!.weakPoints" class="weak-point-item">
              <div class="wp-header">
                <span class="wp-icon">⚠</span>
                <span class="wp-name">{{ wp.knowledgePoint }}</span>
                <span class="wp-mastery" [class.low]="wp.mastery < 0.5">
                  正确率 {{ Math.round(wp.mastery * 100) }}%
                </span>
              </div>
              <mat-progress-bar
                mode="determinate"
                [value]="(1 - wp.errorRate) * 100"
                [color]="wp.mastery < 0.5 ? 'warn' : 'accent'"
              ></mat-progress-bar>
              <p class="wp-suggestion">💡 建议：{{ wp.suggestion }}</p>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .profile-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .page-title {
      font-size: 28px;
      font-weight: 700;
      color: #0f172a;
      margin: 0;
    }
    .update-time {
      font-size: 13px;
      color: #94a3b8;
    }

    /* 双栏布局 */
    .dual-column-section {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }

    /* AI 教师摘要卡片 */
    .teacher-summary-card { }
    .ai-avatar {
      font-size: 40px;
      background: linear-gradient(135deg, #dbeafe, #ede9fe);
      border-radius: 50%;
      padding: 8px;
      color: #3b82f6;
    }
    .summary-quote {
      font-size: 14px;
      line-height: 1.8;
      color: #334155;
      padding: 16px;
      background: #f8fafc;
      border-radius: 12px;
      border-left: 4px solid #8b5cf6;
    }
    .summary-meta {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-top: 16px;
    }
    .meta-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: #475569;
    }
    .meta-item mat-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      color: #64748b;
    }
    .profile-empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 48px;
      color: #94a3b8;
    }
    .profile-empty mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      margin-bottom: 12px;
    }

    /* 雷达图 */
    .radar-card { }
    .radar-chart {
      width: 100%;
      height: 300px;
    }
    .radar-legend {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 8px;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: #64748b;
    }
    .legend-item .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .legend-item.current .dot { background: #3b82f6; }
    .legend-item.previous .dot { background: #94a3b8; }

    /* 技能树 */
    .skill-tree-card { }
    .skill-tree { }
    .skill-category {
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      margin-bottom: 12px;
      overflow: hidden;
    }
    .category-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: #f8fafc;
      cursor: pointer;
      transition: background 0.2s;
    }
    .category-header:hover { background: #f1f5f9; }
    .category-name {
      font-size: 15px;
      font-weight: 600;
      color: #0f172a;
      flex: 1;
    }
    .category-progress {
      font-size: 13px;
      font-weight: 600;
      color: #3b82f6;
      margin-right: 8px;
    }
    .category-progress-bar {
      width: 80px;
      height: 6px;
    }
    .skill-children {
      padding: 8px 16px 8px 44px;
    }
    .skill-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 6px;
      margin-bottom: 4px;
      transition: background 0.2s;
    }
    .skill-item:hover { background: #f8fafc; }
    .skill-item.locked { opacity: 0.5; }
    .skill-status-icon { font-size: 16px; }
    .skill-name {
      font-size: 14px;
      color: #334155;
      font-weight: 500;
      min-width: 120px;
    }
    .skill-progress {
      font-size: 12px;
      color: #64748b;
    }
    .skill-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      font-weight: 500;
    }
    .current-badge {
      background: #dbeafe;
      color: #2563eb;
    }
    .locked-badge {
      background: #f1f5f9;
      color: #94a3b8;
    }
    .skill-progress-bar {
      flex: 1;
      height: 4px;
      max-width: 100px;
    }

    /* 薄弱环节 */
    .weak-points-card { }
    .warn-avatar {
      font-size: 40px;
      background: linear-gradient(135deg, #fef3c7, #fde68a);
      border-radius: 50%;
      padding: 8px;
      color: #f59e0b;
    }
    .weak-points-list { }
    .weak-point-item {
      padding: 16px;
      border: 1px solid #f1f5f9;
      border-radius: 8px;
      margin-bottom: 12px;
    }
    .wp-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }
    .wp-icon { font-size: 16px; }
    .wp-name {
      font-size: 14px;
      font-weight: 600;
      color: #0f172a;
      flex: 1;
    }
    .wp-mastery {
      font-size: 13px;
      font-weight: 600;
      color: #22c55e;
    }
    .wp-mastery.low { color: #ef4444; }
    .wp-suggestion {
      font-size: 13px;
      color: #64748b;
      margin-top: 8px;
    }

    @media (max-width: 768px) {
      .dual-column-section {
        grid-template-columns: 1fr;
      }
      .radar-chart { height: 250px; }
    }
  `],
})
export class LearningProfileComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  profile: StudentLearningProfile | null = null;
  teacherSummary = '';
  expandAll = false;
  expandedCategories = new Set<string>();

  // 技能树分类
  skillTreeCategories: Array<{ id: string; name: string; children: SkillTreeNode[] }> = [];

  // 雷达图配置
  radarOption: EChartsOption = {};

  currentUser: User | null = null;

  // 供模板使用的 Math
  readonly Math = Math;

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      if (user?.id) {
        this.loadProfile(Number(user.id));
      }
    });
  }

  private loadProfile(userId: number): void {
    this.aiTeacherService.getProfile(String(userId)).pipe(
      takeUntil(this.destroy$),
    ).subscribe((profile) => {
      this.profile = profile;
      this.teacherSummary = this.aiTeacherService.generatePersonaSeed(profile);
      this.buildSkillTree(profile);
      this.buildRadarChart(profile);
      this.cdr.markForCheck();
    });
  }

  private buildRadarChart(profile: StudentLearningProfile): void {
    this.radarOption = {
      radar: {
        indicator: [
          { name: '编程思维', max: 100 },
          { name: '算法能力', max: 100 },
          { name: '调试能力', max: 100 },
          { name: '项目实践', max: 100 },
          { name: 'STEM实验', max: 100 },
        ],
        shape: 'circle',
        splitNumber: 4,
        name: {
          textStyle: {
            color: '#334155',
            fontSize: 12,
          },
        },
        splitLine: {
          lineStyle: {
            color: '#e2e8f0',
          },
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(59,130,246,0.02)', 'rgba(59,130,246,0.04)'],
          },
        },
        axisLine: {
          lineStyle: {
            color: '#e2e8f0',
          },
        },
      },
      series: [
        {
          type: 'radar',
          symbol: 'circle',
          symbolSize: 6,
          data: [
            {
              value: [
                profile.abilityDimensions.programmingThinking,
                profile.abilityDimensions.algorithmAbility,
                profile.abilityDimensions.debuggingSkill,
                profile.abilityDimensions.projectPractice,
                profile.abilityDimensions.stemExperiment,
              ],
              name: '本月',
              areaStyle: {
                color: 'rgba(59,130,246,0.15)',
              },
              lineStyle: {
                color: '#3b82f6',
                width: 2,
              },
              itemStyle: {
                color: '#3b82f6',
              },
            },
            {
              value: [
                Math.max(0, profile.abilityDimensions.programmingThinking - 15),
                Math.max(0, profile.abilityDimensions.algorithmAbility - 15),
                Math.max(0, profile.abilityDimensions.debuggingSkill - 12),
                Math.max(0, profile.abilityDimensions.projectPractice - 15),
                Math.max(0, profile.abilityDimensions.stemExperiment - 15),
              ],
              name: '上月',
              areaStyle: {
                color: 'rgba(148,163,184,0.1)',
              },
              lineStyle: {
                color: '#94a3b8',
                width: 1.5,
                type: 'dashed',
              },
              itemStyle: {
                color: '#94a3b8',
              },
            },
          ],
        },
      ],
      tooltip: {
        trigger: 'item',
      },
      color: ['#3b82f6', '#94a3b8'],
    };
  }

  private buildSkillTree(profile: StudentLearningProfile): void {
    const pythonSkills = profile.skillTree.find(t => t.id === 'python_basics');
    const stemSkills = profile.skillTree.find(t => t.id === 'stem_basics');

    this.skillTreeCategories = [
      {
        id: 'python',
        name: pythonSkills?.name || 'Python 基础',
        children: pythonSkills?.children ?? [],
      },
      {
        id: 'stem',
        name: stemSkills?.name || 'STEM 实验',
        children: stemSkills?.children ?? [],
      },
    ];
  }

  getCategoryProgress(categoryId: string): number {
    const cat = this.skillTreeCategories.find(c => c.id === categoryId);
    if (!cat || cat.children.length === 0) return 0;
    const total = cat.children.reduce((sum, skill) => sum + skill.progress * 100, 0);
    return Math.round(total / cat.children.length);
  }

  toggleCategory(categoryId: string): void {
    if (this.expandedCategories.has(categoryId)) {
      this.expandedCategories.delete(categoryId);
    } else {
      this.expandedCategories.add(categoryId);
    }
    this.cdr.markForCheck();
  }

  getTopInterest(): string {
    if (!this.profile?.interestPreferences?.length) return '未知';
    const map: Record<string, string> = {
      game_development: '游戏开发',
      robotics: '机器人',
      '3d_modeling': '3D建模',
    };
    return this.profile.interestPreferences.map(k => map[k] || k).join('、');
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
