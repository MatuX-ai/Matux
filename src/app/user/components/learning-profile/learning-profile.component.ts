/**
 * 学习画像页面
 *
 * PRD 6.6 关键页面线框 - "我的学习画像"
 * 展示：AI教师摘要、能力雷达图、技能树、薄弱环节诊断
 */

// ECharts 颜色令牌: 与设计系统主色保持一致
// 与 _stem-tokens.scss / _css-variables.scss 中令牌值同步
const ECHARTS_COLORS = {
  textSecondary: '#334155',     // 对应 --matux-color-text-secondary
  divider: '#e2e8f0',           // 对应 --matux-color-divider
  primary: '#2563eb',           // 【对比度修复 #11】原 #3b82f6 (3.68:1) → #2563eb (4.62:1) AA
  primaryFaded02: 'rgba(37, 99, 235, 0.02)',  // primary @ 2% alpha
  primaryFaded04: 'rgba(37, 99, 235, 0.04)',  // primary @ 4% alpha
  primaryFaded15: 'rgba(37, 99, 235, 0.15)',  // primary @ 15% alpha
  secondary: '#64748b',         // 【对比度修复 #12】原 #94a3b8 (2.56:1) → #64748b (4.92:1) AA
  secondaryFaded10: 'rgba(100, 116, 139, 0.1)', // secondary @ 10% alpha
} as const;

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NgxEchartsModule } from 'ngx-echarts';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import type { SkillTreeNode, StudentLearningProfile } from '../../../core/models/ai-teacher.models';
import type { User } from '../../../core/models/auth.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';

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
  templateUrl: './learning-profile.component.html',
  styleUrls: ['./learning-profile.component.scss'],
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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  radarOption: any = {};

  currentUser: User | null = null;

  // 供模板使用的 Math
  readonly Math = Math;

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
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
    this.aiTeacherService
      .getProfile(String(userId))
      .pipe(takeUntil(this.destroy$))
      .subscribe((profile) => {
        this.profile = profile;
        this.teacherSummary = this.aiTeacherService.generatePersonaSeed(profile);
        this.buildSkillTree(profile);
        this.buildRadarChart(profile);
        this.cdr.markForCheck();
      });
  }

  // eslint-disable-next-line max-lines-per-function
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
            color: ECHARTS_COLORS.textSecondary,
            fontSize: 12,
          },
        },
        splitLine: {
          lineStyle: {
            color: ECHARTS_COLORS.divider,
          },
        },
        splitArea: {
          areaStyle: {
            color: [ECHARTS_COLORS.primaryFaded02, ECHARTS_COLORS.primaryFaded04],
          },
        },
        axisLine: {
          lineStyle: {
            color: ECHARTS_COLORS.divider,
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
                color: ECHARTS_COLORS.primaryFaded15,
              },
              lineStyle: {
                color: ECHARTS_COLORS.primary,
                width: 2,
              },
              itemStyle: {
                color: ECHARTS_COLORS.primary,
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
                color: ECHARTS_COLORS.secondaryFaded10,
              },
              lineStyle: {
                color: ECHARTS_COLORS.secondary,
                width: 1.5,
                type: 'dashed',
              },
              itemStyle: {
                color: ECHARTS_COLORS.secondary,
              },
            },
          ],
        },
      ],
      tooltip: {
        trigger: 'item',
      },
      color: [ECHARTS_COLORS.primary, ECHARTS_COLORS.secondary],
    };
  }

  private buildSkillTree(profile: StudentLearningProfile): void {
    const pythonSkills = profile.skillTree.find((t) => t.id === 'python_basics');
    const stemSkills = profile.skillTree.find((t) => t.id === 'stem_basics');

    this.skillTreeCategories = [
      {
        id: 'python',
        name: pythonSkills?.name ?? 'Python 基础',
        children: pythonSkills?.children ?? [],
      },
      {
        id: 'stem',
        name: stemSkills?.name ?? 'STEM 实验',
        children: stemSkills?.children ?? [],
      },
    ];
  }

  getCategoryProgress(categoryId: string): number {
    const cat = this.skillTreeCategories.find((c) => c.id === categoryId);
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
    return this.profile.interestPreferences.map((k) => map[k] || k).join('、');
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
