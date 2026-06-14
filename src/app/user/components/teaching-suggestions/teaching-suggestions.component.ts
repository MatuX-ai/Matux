/**
 * 智能教学建议组件
 *
 * PRD F-08-AI.5：智能教学建议
 * 展示 DiagnosisService 的诊断结果：
 * - 总体学习健康评分
 * - 多维度得分（知识掌握、技能均衡、学习投入、学习效率、独立学习）
 * - 教学建议列表（按严重程度排序）
 * - 一键重新诊断
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import {
  DiagnosisDimension,
  DiagnosisReport,
  DiagnosisService,
  HealthRating,
} from '../../../core/services/diagnosis.service';

@Component({
  selector: 'app-teaching-suggestions',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatProgressBarModule],
  templateUrl: './teaching-suggestions.component.html',
  styleUrls: ['./teaching-suggestions.component.scss'],
})
export class TeachingSuggestionsComponent implements OnInit, OnDestroy {
  report: DiagnosisReport | null = null;
  history: DiagnosisReport[] = [];
  isDiagnosing = false;

  dimensionList: { key: DiagnosisDimension; label: string; score: number; description: string }[] =
    [];

  private userId = '';
  private destroy$ = new Subject<void>();

  constructor(
    private diagnosisService: DiagnosisService,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    const user = this.authService.getCurrentUser();
    this.userId = user?.id ?? 'default_user';

    // 订阅诊断报告
    this.diagnosisService.report$.pipe(takeUntil(this.destroy$)).subscribe((r) => {
      if (r) {
        this.report = r;
        this.history = this.diagnosisService.getHistory();
        this.buildDimensionList(r);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  get healthRating(): HealthRating {
    if (!this.report) return 'fair';
    return this.diagnosisService.getHealthRating(this.report.overallHealth);
  }

  get healthLabel(): string {
    return this.diagnosisService.getHealthRatingLabel(this.healthRating);
  }

  get healthColor(): string {
    return this.diagnosisService.getHealthRatingColor(this.healthRating);
  }

  runDiagnosis(): void {
    this.isDiagnosing = true;
    this.diagnosisService.runFullDiagnosis(this.userId).subscribe({
      complete: () => {
        this.isDiagnosing = false;
      },
      error: () => {
        this.isDiagnosing = false;
      },
    });
  }

  getScoreColor(score: number): string {
    // 【对比度修复 #25】三个分位颜色全部统一为 AA 认证值
    // 原色 vs #fff 背景: #22c55e 2.28:1、#f59e0b 2.15:1、#ef4444 3.77:1 - 全部未达 4.5:1
    if (score >= 70) return '#15803d'; // 5.13:1 AA
    if (score >= 45) return '#b45309'; // 4.62:1 AA
    return '#dc2626';                  // 4.83:1 AA
  }

  getScoreLevel(score: number): string {
    if (score >= 70) return 'high';
    if (score >= 45) return 'medium';
    return 'low';
  }

  private buildDimensionList(report: DiagnosisReport): void {
    const meta: { key: DiagnosisDimension; label: string; description: string }[] = [
      { key: 'knowledge', label: '知识掌握', description: '基础知识点掌握程度' },
      { key: 'skill', label: '技能均衡', description: '各项技能发展均衡性' },
      { key: 'engagement', label: '学习投入', description: '学习专注度和持续性' },
      { key: 'efficiency', label: '学习效率', description: '单位时间学习产出' },
      { key: 'independence', label: '独立学习', description: '自主学习能力评估' },
    ];
    this.dimensionList = meta.map((m) => ({
      key: m.key,
      label: m.label,
      score: report.dimensionScores[m.key] ?? 50,
      description: m.description,
    }));
  }
}
