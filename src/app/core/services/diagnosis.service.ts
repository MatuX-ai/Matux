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
    const criticalIssues = suggestions.filter((s) => s.severity === 'warning');

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
    if (state.length === 0) return 50; // 默认中等
    const mastered = state.filter((k) => k.status === 'mastered').length;
    const notStarted = state.filter((k) => k.status === 'not_started').length;
    const score = ((mastered / state.length) * 100) - (notStarted / state.length * 20);
    return Math.max(0, Math.min(100, Math.round(score)));
  }

  private scoreSkillDimension(
    profile: StudentLearningProfile | null,
    growth: any,
  ): number {
    if (!growth?.abilityTrend?.length) return 50;
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
    const balancePenalty = Math.min(30, Math.sqrt(variance));
    return Math.max(0, Math.min(100, Math.round(avg - balancePenalty)));
  }

  private scoreEngagementDimension(profile: StudentLearningProfile | null): number {
    if (!profile?.attentionProfile) return 50;
    const { averageFocusDurationMinutes, tabSwitchFrequency } = profile.attentionProfile;
    const focus = Math.min(100, (averageFocusDurationMinutes / 60) * 100);
    const distraction = Math.max(0, 100 - tabSwitchFrequency * 10);
    return Math.round((focus + distraction) / 2);
  }

  private scoreEfficiencyDimension(
    profile: StudentLearningProfile | null,
    growth: any,
  ): number {
    if (!growth?.statistics) return 50;
    const { totalStudyHours, completedCourses, totalQuestions } = growth.statistics;
    if (totalStudyHours === 0) return 50;
    const courseEfficiency = (completedCourses / Math.max(1, totalStudyHours / 10)) * 20;
    const questionEfficiency = Math.min(50, (totalQuestions / Math.max(1, totalStudyHours)) * 10);
    return Math.min(100, Math.round(courseEfficiency + questionEfficiency + 20));
  }

  private scoreIndependenceDimension(profile: StudentLearningProfile | null): number {
    if (!profile?.weakPoints?.length) return 50;
    const avgMastery = profile.weakPoints.reduce((s, w) => s + w.mastery, 0) / profile.weakPoints.length;
    return Math.round(avgMastery * 100);
  }

  private analyzeTrends(growth: any): { improving: string[]; declining: string[]; stable: string[] } {
    const result = { improving: [] as string[], declining: [] as string[], stable: [] as string[] };
    if (!growth?.abilityTrend?.length || growth.abilityTrend.length < 2) return result;
    return result;
  }

  private saveToHistory(report: DiagnosisReport): void {
    const history = this.getHistory();
    history.push(report);
    if (history.length > 20) history.shift();
    this.historySubject.next(history);
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
