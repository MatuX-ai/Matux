/**
 * 诊断服务
 *
 * 封装 AI 学习诊断逻辑，提供：
 * - 学习问题诊断与分析
 * - 多维度学习健康评估
 * - 与 AITeacherService 深度集成
 * - 诊断历史追踪
 *
 * PRD F-08-AI.4：智能诊断引擎
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, combineLatest, of } from 'rxjs';
import { map, switchMap, catchError } from 'rxjs/operators';

import { AITeacherService } from './ai-teacher.service';
import type {
  StudentLearningProfile,
  KnowledgeStateItem,
  TeachingSuggestion,
  AbilityTrendPoint,
} from '../models/ai-teacher.models';

/** 诊断维度 */
export type DiagnosisDimension =
  | 'knowledge'       // 知识掌握
  | 'skill'           // 技能均衡
  | 'engagement'      // 学习投入
  | 'efficiency'      // 学习效率
  | 'independence';   // 独立学习

/** 诊断评分常量 */
const DIAGNOSIS_DEFAULT_SCORE = 50;          // 默认中等分数
const DIAGNOSIS_MAX_SCORE = 100;             // 最高分
const DIAGNOSIS_MIN_SCORE = 0;               // 最低分
const DIAGNOSIS_NOT_STARTED_PENALTY = 20;    // 未开始知识点扣分权重
const DIAGNOSIS_BALANCE_PENALTY_MAX = 30;    // 技能均衡最大惩罚分
const DIAGNOSIS_DISTRACTION_PENALTY_FACTOR = 10; // 分心惩罚因子
const DIAGNOSIS_COURSE_EFFICIENCY_FACTOR = 20;   // 课程效率因子
const DIAGNOSIS_QUESTION_EFFICIENCY_MAX = 50;    // 题目效率最高分
const DIAGNOSIS_QUESTION_EFFICIENCY_FACTOR = 10; // 题目效率因子
const DIAGNOSIS_BASE_EFFICIENCY_SCORE = 20;      // 效率基础分
const DIAGNOSIS_HISTORY_MAX_LENGTH = 20;     // 最大历史记录数
const DIAGNOSIS_TREND_THRESHOLD = 5;         // 趋势变化阈值

/** 诊断报告 */
export interface DiagnosisReport {
  userId: string;
  timestamp: string;
  overallHealth: number;           // 0-100
  dimensionScores: Record<DiagnosisDimension, number>;
  suggestions: TeachingSuggestion[];
  criticalIssues: TeachingSuggestion[];
  trends: {
    improving: string[];
    declining: string[];
    stable: string[];
  };
}

/** 学习健康评级 */
export type HealthRating = 'excellent' | 'good' | 'fair' | 'needs_attention' | 'critical';

@Injectable({
  providedIn: 'root',
})
export class DiagnosisService {
  private readonly STORAGE_KEY = 'imato_diagnosis_history';

  /** 当前诊断报告 */
  private reportSubject = new BehaviorSubject<DiagnosisReport | null>(null);
  public report$ = this.reportSubject.asObservable();

  /** 诊断历史 */
  private historySubject = new BehaviorSubject<DiagnosisReport[]>([]);
  public history$ = this.historySubject.asObservable();

  constructor(private aiTeacher: AITeacherService) {
    this.loadHistory();
  }

  /** 执行完整诊断分析 */
  runFullDiagnosis(userId: string): Observable<DiagnosisReport> {
    return combineLatest([
      this.aiTeacher.getProfile(userId).pipe(catchError(() => of({} as StudentLearningProfile))),
      this.aiTeacher.getKnowledgeState(userId).pipe(catchError(() => of([]))),
      this.aiTeacher.getGrowthTrajectory(userId).pipe(catchError(() => of({} as any))),
      this.aiTeacher.getTeachingSuggestions(userId).pipe(catchError(() => of([]))),
    ]).pipe(
      map(([profile, knowledgeState, growth, suggestions]) => {
        const report = this.buildReport(userId, profile, knowledgeState, growth, suggestions);
        this.reportSubject.next(report);
        this.saveToHistory(report);
        return report;
      }),
    );
  }

  /** 获取健康评级 */
  getHealthRating(score: number): HealthRating {
    if (score >= 85) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 55) return 'fair';
    if (score >= 35) return 'needs_attention';
    return 'critical';
  }

  /** 获取评级标签 */
  getHealthRatingLabel(rating: HealthRating): string {
    const labels: Record<HealthRating, string> = {
      excellent: '优秀',
      good: '良好',
      fair: '一般',
      needs_attention: '需关注',
      critical: '紧急',
    };
    return labels[rating];
  }

  /** 获取评级颜色 */
  getHealthRatingColor(rating: HealthRating): string {
    const colors: Record<HealthRating, string> = {
      excellent: '#22c55e',
      good: '#3b82f6',
      fair: '#f59e0b',
      needs_attention: '#f97316',
      critical: '#ef4444',
    };
    return colors[rating];
  }

  /** 获取诊断历史 */
  getHistory(): DiagnosisReport[] {
    return this.historySubject.getValue();
  }

  /** 清除诊断历史 */
  clearHistory(): void {
    this.historySubject.next([]);
    localStorage.removeItem(this.STORAGE_KEY);
  }

  // ==================== 私有方法 ====================

  private buildReport(
    userId: string,
    profile: StudentLearningProfile | null,
    knowledgeState: KnowledgeStateItem[],
    growth: any,
    suggestions: TeachingSuggestion[],
  ): DiagnosisReport {
    // 各维度评分
    const dimensionScores = {
      knowledge: this.scoreKnowledgeDimension(knowledgeState),
      skill: this.scoreSkillDimension(profile, growth),
      engagement: this.scoreEngagementDimension(profile),
      efficiency: this.scoreEfficiencyDimension(profile, growth),
      independence: this.scoreIndependenceDimension(profile),
    };

    const overallHealth = Math.round(
      Object.values(dimensionScores).reduce((sum, s) => sum + s, 0) / 5,
    );

    // 严重问题（高优先级）
    const criticalIssues = suggestions.filter((s) => s.severity === 'critical');

    // 趋势分析
    const trends = this.analyzeTrends(growth);

    return {
      userId,
      timestamp: new Date().toISOString(),
      overallHealth,
      dimensionScores,
      suggestions,
      criticalIssues,
      trends,
    };
  }

  private scoreKnowledgeDimension(state: KnowledgeStateItem[]): number {
    if (state.length === 0) return DIAGNOSIS_DEFAULT_SCORE;
    const mastered = state.filter((k) => k.status === 'mastered').length;
    const notStarted = state.filter((k) => k.status === 'not_started').length;
    const score = ((mastered / state.length) * DIAGNOSIS_MAX_SCORE) - (notStarted / state.length * DIAGNOSIS_NOT_STARTED_PENALTY);
    return Math.max(DIAGNOSIS_MIN_SCORE, Math.min(DIAGNOSIS_MAX_SCORE, Math.round(score)));
  }

  private scoreSkillDimension(
    profile: StudentLearningProfile | null,
    growth: any,
  ): number {
    if (!growth?.abilityTrend?.length) return DIAGNOSIS_DEFAULT_SCORE;
    const latest = growth.abilityTrend[growth.abilityTrend.length - 1] as AbilityTrendPoint;
    const values = [
      latest.programmingThinking,
      latest.algorithmAbility,
      latest.debuggingSkill,
      latest.projectPractice,
      latest.stemExperiment,
    ];
    const avg = values.reduce((s, v) => s + v, 0) / values.length;
    const variance = values.reduce((s, v) => s + Math.pow(v - avg, 2), 0) / values.length;
    const balancePenalty = Math.min(DIAGNOSIS_BALANCE_PENALTY_MAX, Math.sqrt(variance));
    return Math.max(DIAGNOSIS_MIN_SCORE, Math.min(DIAGNOSIS_MAX_SCORE, Math.round(avg - balancePenalty)));
  }

  private scoreEngagementDimension(profile: StudentLearningProfile | null): number {
    if (!profile?.attentionProfile) return DIAGNOSIS_DEFAULT_SCORE;
    const { averageFocusDurationMinutes, tabSwitchFrequency } = profile.attentionProfile;
    const focus = Math.min(DIAGNOSIS_MAX_SCORE, (averageFocusDurationMinutes / 60) * DIAGNOSIS_MAX_SCORE);
    const distraction = Math.max(DIAGNOSIS_MIN_SCORE, DIAGNOSIS_MAX_SCORE - tabSwitchFrequency * DIAGNOSIS_DISTRACTION_PENALTY_FACTOR);
    return Math.round((focus + distraction) / 2);
  }

  private scoreEfficiencyDimension(
    profile: StudentLearningProfile | null,
    growth: any,
  ): number {
    if (!growth?.statistics) return DIAGNOSIS_DEFAULT_SCORE;
    const { totalStudyHours, completedCourses, totalQuestions } = growth.statistics;
    if (totalStudyHours === 0) return DIAGNOSIS_DEFAULT_SCORE;
    const courseEfficiency = (completedCourses / Math.max(1, totalStudyHours / 10)) * DIAGNOSIS_COURSE_EFFICIENCY_FACTOR;
    const questionEfficiency = Math.min(DIAGNOSIS_QUESTION_EFFICIENCY_MAX, (totalQuestions / Math.max(1, totalStudyHours)) * DIAGNOSIS_QUESTION_EFFICIENCY_FACTOR);
    return Math.min(DIAGNOSIS_MAX_SCORE, Math.round(courseEfficiency + questionEfficiency + DIAGNOSIS_BASE_EFFICIENCY_SCORE));
  }

  /**
   * 独立学习能力评分
   *
   * 使用 abilityDimensions.independentCompletion：独立完成率越高，说明独立学习能力越强
   */
  private scoreIndependenceDimension(profile: StudentLearningProfile | null): number {
    if (!profile?.abilityDimensions) return DIAGNOSIS_DEFAULT_SCORE;
    return Math.round(profile.abilityDimensions.independentCompletion);
  }

  private analyzeTrends(growth: any): { improving: string[]; declining: string[]; stable: string[] } {
    const result = { improving: [] as string[], declining: [] as string[], stable: [] as string[] };
    if (!growth?.abilityTrend?.length || growth.abilityTrend.length < 2) return result;

    const first = growth.abilityTrend[0] as AbilityTrendPoint;
    const last = growth.abilityTrend[growth.abilityTrend.length - 1] as AbilityTrendPoint;

    const dimensions: { key: keyof AbilityTrendPoint; label: string }[] = [
      { key: 'programmingThinking', label: '编程思维' },
      { key: 'algorithmAbility', label: '算法能力' },
      { key: 'debuggingSkill', label: '调试技能' },
      { key: 'projectPractice', label: '项目实践' },
      { key: 'stemExperiment', label: 'STEM实验' },
      { key: 'independentCompletion', label: '独立完成' },
    ];

    for (const dim of dimensions) {
      const diff = (last[dim.key] as number) - (first[dim.key] as number);
      if (diff > DIAGNOSIS_TREND_THRESHOLD) {
        result.improving.push(dim.label);
      } else if (diff < -DIAGNOSIS_TREND_THRESHOLD) {
        result.declining.push(dim.label);
      } else {
        result.stable.push(dim.label);
      }
    }

    return result;
  }

  private saveToHistory(report: DiagnosisReport): void {
    const history = [...this.getHistory(), report];
    if (history.length > DIAGNOSIS_HISTORY_MAX_LENGTH) {
      const truncated = history.slice(history.length - DIAGNOSIS_HISTORY_MAX_LENGTH);
      this.historySubject.next(truncated);
      this.persistHistory(truncated);
      return;
    }
    this.historySubject.next(history);
    this.persistHistory(history);
  }

  private persistHistory(history: DiagnosisReport[]): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
    } catch {
      // 存储失败忽略
    }
  }

  private loadHistory(): void {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (data) {
        const history = JSON.parse(data) as DiagnosisReport[];
        this.historySubject.next(history);
      }
    } catch {
      // 加载失败忽略
    }
  }
}
