/**
 * 里程碑服务
 *
 * 管理学习里程碑的定义、追踪和成就系统：
 * - 里程碑进度追踪
 * - 成就解锁通知
 * - 下一里程碑预测
 * - 里程碑统计
 *
 * PRD 6.6 - "我的成长" / 学习里程碑
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import type { GrowthTrajectory, LearningMilestone } from '../models/ai-teacher.models';

import { AITeacherService } from './ai-teacher.service';

/** 里程碑模板定义 */
export interface MilestoneTemplate {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: MilestoneCategory;
  /** 解锁条件 */
  requirements: {
    type:
      | 'study_hours'
      | 'completed_courses'
      | 'completed_projects'
      | 'streak_days'
      | 'questions_asked'
      | 'mastery_level'
      | 'skill_level'
      | 'custom';
    threshold: number;
    description: string;
  };
  /** 预估难度 (1-5) */
  difficulty: number;
  /** XP 奖励 */
  xpReward: number;
}

/** 里程碑分类 */
export type MilestoneCategory =
  | 'onboarding' // 入门
  | 'skill' // 技能
  | 'persistence' // 坚持
  | 'exploration' // 探索
  | 'achievement' // 成就
  | 'project'; // 项目

/** 里程碑进度 */
export interface MilestoneProgress {
  template: MilestoneTemplate;
  progress: number; // 0-100
  isUnlocked: boolean;
  unlockedAt?: string;
  currentValue: number;
  targetValue: number;
}

/** 里程碑统计 */
export interface MilestoneStats {
  totalTemplates: number;
  unlockedCount: number;
  lockedCount: number;
  recentUnlocks: LearningMilestone[];
  nextPredictedMilestone: MilestoneProgress | null;
  totalXPEarned: number;
}

@Injectable({
  providedIn: 'root',
})
export class MilestoneService {
  /** 里程碑模板定义 */
  readonly milestoneTemplates: MilestoneTemplate[] = [
    {
      id: 'first_login',
      title: '第一步',
      description: '完成首次登录并开始学习之旅',
      icon: 'login',
      category: 'onboarding',
      requirements: { type: 'study_hours', threshold: 1, description: '完成1小时学习' },
      difficulty: 1,
      xpReward: 50,
    },
    {
      id: 'first_blockly',
      title: '积木大师',
      description: '完成第一个 Blockly 编程项目',
      icon: 'widgets',
      category: 'onboarding',
      requirements: { type: 'completed_projects', threshold: 1, description: '完成1个项目' },
      difficulty: 1,
      xpReward: 100,
    },
    {
      id: 'python_intro',
      title: 'Python 入门',
      description: '完成 Python 入门课程',
      icon: 'code',
      category: 'skill',
      requirements: { type: 'completed_courses', threshold: 5, description: '完成5门课程' },
      difficulty: 2,
      xpReward: 200,
    },
    {
      id: 'streak_7',
      title: '坚持一周',
      description: '连续学习7天',
      icon: 'local_fire_department',
      category: 'persistence',
      requirements: { type: 'streak_days', threshold: 7, description: '连续学习7天' },
      difficulty: 2,
      xpReward: 150,
    },
    {
      id: 'streak_30',
      title: '月度之星',
      description: '连续学习30天',
      icon: 'whatshot',
      category: 'persistence',
      requirements: { type: 'streak_days', threshold: 30, description: '连续学习30天' },
      difficulty: 3,
      xpReward: 500,
    },
    {
      id: 'first_debug',
      title: 'Bug 猎人',
      description: '独立解决第一个程序 bug',
      icon: 'bug_report',
      category: 'skill',
      requirements: { type: 'skill_level', threshold: 1, description: '调试技能达到初级' },
      difficulty: 2,
      xpReward: 200,
    },
    {
      id: 'first_independent_project',
      title: '独立项目',
      description: '独立完成一个编程项目',
      icon: 'construction',
      category: 'project',
      requirements: { type: 'completed_projects', threshold: 3, description: '完成3个项目' },
      difficulty: 3,
      xpReward: 300,
    },
    {
      id: 'circuit_master',
      title: '电路达人',
      description: '掌握基础电路实验',
      icon: 'bolt',
      category: 'exploration',
      requirements: { type: 'completed_courses', threshold: 10, description: '完成10门课程' },
      difficulty: 3,
      xpReward: 300,
    },
    {
      id: 'algorithm_starter',
      title: '算法入门',
      description: '开始学习基础算法',
      icon: 'account_tree',
      category: 'skill',
      requirements: { type: 'mastery_level', threshold: 60, description: '算法掌握度达到60%' },
      difficulty: 4,
      xpReward: 400,
    },
    {
      id: 'project_master',
      title: '项目大师',
      description: '完成10个独立项目',
      icon: 'rocket_launch',
      category: 'project',
      requirements: { type: 'completed_projects', threshold: 10, description: '完成10个项目' },
      difficulty: 5,
      xpReward: 1000,
    },
    {
      id: 'breakthrough',
      title: '突破时刻',
      description: '在某个难点上取得重大突破',
      icon: 'emoji_events',
      category: 'achievement',
      requirements: { type: 'mastery_level', threshold: 80, description: '单知识点掌握度达80%' },
      difficulty: 4,
      xpReward: 500,
    },
    {
      id: 'ai_master',
      title: 'AI 协作大师',
      description: '学会高效使用 AI 老师学习',
      icon: 'smart_toy',
      category: 'achievement',
      requirements: { type: 'questions_asked', threshold: 100, description: '提问100次' },
      difficulty: 3,
      xpReward: 350,
    },
  ];

  private progressSubject = new BehaviorSubject<MilestoneProgress[]>([]);
  public progress$ = this.progressSubject.asObservable();

  private statsSubject = new BehaviorSubject<MilestoneStats>({
    totalTemplates: 0,
    unlockedCount: 0,
    lockedCount: 0,
    recentUnlocks: [],
    nextPredictedMilestone: null,
    totalXPEarned: 0,
  });
  public stats$ = this.statsSubject.asObservable();

  constructor(private aiTeacher: AITeacherService) {}

  /** 加载里程碑进度 */
  loadProgress(userId: string): void {
    this.aiTeacher
      .getGrowthTrajectory(userId)
      .pipe(
        map((growth) => {
          const achieved = growth.milestones ?? [];
          const progress = this.milestoneTemplates.map((template) => {
            const isUnlocked = achieved.some((m) => m.type === template.id);
            const currentValue = this.estimateCurrentValue(template, growth);
            const targetValue = template.requirements.threshold;
            const pct = Math.min(100, Math.round((currentValue / targetValue) * 100));

            return {
              template,
              progress: isUnlocked ? 100 : pct,
              isUnlocked,
              unlockedAt: achieved.find((m) => m.type === template.id)?.achievedAt,
              currentValue,
              targetValue,
            } as MilestoneProgress;
          });

          this.progressSubject.next(progress);
          this.updateStats(progress, achieved);
        }),
        catchError(() => {
          // 使用默认进度
          const progress = this.milestoneTemplates.map((t) => ({
            template: t,
            progress: 0,
            isUnlocked: false,
            currentValue: 0,
            targetValue: t.requirements.threshold,
          }));
          this.progressSubject.next(progress);
          return of(null);
        })
      )
      .subscribe();
  }

  /** 获取待解锁的下一里程碑 */
  getNextMilestone(): MilestoneProgress | null {
    const list = this.progressSubject.getValue();
    return list.filter((m) => !m.isUnlocked).sort((a, b) => b.progress - a.progress)?.[0] ?? null;
  }

  /** 按分类获取里程碑 */
  getMilestonesByCategory(category: MilestoneCategory): MilestoneProgress[] {
    return this.progressSubject.getValue().filter((m) => m.template.category === category);
  }

  /** 获取已解锁里程碑 */
  getUnlockedMilestones(): MilestoneProgress[] {
    return this.progressSubject.getValue().filter((m) => m.isUnlocked);
  }

  private updateStats(progress: MilestoneProgress[], achieved: LearningMilestone[]): void {
    const unlocked = progress.filter((m) => m.isUnlocked);
    this.statsSubject.next({
      totalTemplates: this.milestoneTemplates.length,
      unlockedCount: unlocked.length,
      lockedCount: progress.length - unlocked.length,
      recentUnlocks: achieved.slice(-5).reverse(),
      nextPredictedMilestone: this.getNextMilestone(),
      totalXPEarned: unlocked.reduce((sum, m) => sum + m.template.xpReward, 0),
    });
  }

  // eslint-disable-next-line complexity
  private estimateCurrentValue(
    template: MilestoneTemplate,
    growth: GrowthTrajectory | null
  ): number {
    const stats = growth?.statistics;
    if (!stats) return 0;

    const { type } = template.requirements;
    switch (type) {
      case 'study_hours':
        return stats.totalStudyHours ?? 0;
      case 'completed_courses':
        return stats.completedCourses ?? 0;
      case 'completed_projects':
        return stats.completedProjects ?? 0;
      case 'questions_asked':
        return stats.totalQuestions ?? 0;
      case 'streak_days':
        return 5; // 示例值
      case 'mastery_level':
        return 55; // 示例值
      case 'skill_level':
        return 1;
      default:
        return 0;
    }
  }
}
