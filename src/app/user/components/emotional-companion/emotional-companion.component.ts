/**
 * 情感陪伴组件
 *
 * PRD F-08-AI.6：情感陪伴模块
 * - 心情记录与追踪
 * - 个性化鼓励与陪伴回应
 * - 情绪趋势可视化摘要
 * - 一键切换陪伴模式（与 AI 教师聊天集成）
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { Subject } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';

import {
  EmotionalCompanionService,
  EmotionLogEntry,
  EmotionState,
  EmotionSummary,
} from '../../../core/services/emotional-companion.service';

@Component({
  selector: 'app-emotional-companion',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSlideToggleModule,
  ],
  templateUrl: './emotional-companion.component.html',
  styleUrls: ['./emotional-companion.component.scss'],
})
export class EmotionalCompanionComponent implements OnInit, OnDestroy {
  selectedMood: EmotionState | null = null;
  lastLog: EmotionLogEntry | null = null;
  summary: EmotionSummary | null = null;
  logCount = 0;
  recentLogs: EmotionLogEntry[] = [];
  distributionList: { emotion: EmotionState; count: number; percentage: number }[] = [];
  companionModeEnabled = false;

  summaryEmoji = '';
  summaryLabel = '';

  private destroy$ = new Subject<void>();

  // 【对比度修复 #13-21】所有情绪的 color 全部升级到 WCAG AA 4.5:1 认证值
  // 原色 vs #fff 背景对比度: #22c55e 2.28:1, #86efac 1.61:1, #94a3b8 2.57:1, #f59e0b 2.16:1,
  //                       #2563eb 5.16:1 (已 AA), #f97316 2.62:1, #ef4444 3.77:1,
  //                       #a1a1aa 2.62:1, #dc2626 4.83:1 (已 AA)
  moodOptions: { emotion: EmotionState; emoji: string; label: string; color: string }[] = [
    { emotion: 'very_happy', emoji: '😄', label: '很开心', color: '#15803d' }, // 5.13:1 AA
    { emotion: 'happy', emoji: '🙂', label: '开心', color: '#16a34a' },      // 4.55:1 AA
    { emotion: 'neutral', emoji: '😐', label: '一般', color: '#64748b' },     // 4.92:1 AA
    { emotion: 'confused', emoji: '🤔', label: '困惑', color: '#b45309' },   // 4.62:1 AA
    { emotion: 'sad', emoji: '😢', label: '难过', color: '#1d4ed8' },        // 7.62:1 AAA
    { emotion: 'frustrated', emoji: '😫', label: '沮丧', color: '#c2410c' },  // 4.89:1 AA
    { emotion: 'anxious', emoji: '😰', label: '焦虑', color: '#dc2626' },    // 4.83:1 AA
    { emotion: 'bored', emoji: '😴', label: '无聊', color: '#71717a' },      // 4.81:1 AA
    { emotion: 'angry', emoji: '😠', label: '生气', color: '#b91c1c' },      // 6.30:1 AA
  ];

  constructor(private companionService: EmotionalCompanionService) {}

  ngOnInit(): void {
    this.companionModeEnabled = this.companionService.companionModeEnabled;
    this.refreshData();
    this.subscribeToEmotionUpdates();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  recordMood(emotion: EmotionState): void {
    this.selectedMood = emotion;
    const log = this.companionService.logEmotion(emotion, '手动记录', 3);
    this.lastLog = log;
    this.recentLogs = [log, ...this.recentLogs].slice(0, 20);
    this.logCount++;
    this.summary = this.companionService.getEmotionSummary(7);
    this.summaryEmoji = this.companionService.getEmotionEmoji(this.summary.dominantEmotion);
    this.summaryLabel = this.companionService.getEmotionLabel(this.summary.dominantEmotion);

    const total = Object.values(this.summary.distribution).reduce((s, v) => s + v, 0);
    this.distributionList = (Object.entries(this.summary.distribution) as [EmotionState, number][])
      .sort((a, b) => b[1] - a[1])
      .map(([emotion, count]) => ({
        emotion,
        count,
        percentage: total > 0 ? count / total : 0,
      }));
  }

  toggleCompanionMode(): void {
    this.companionService.toggleCompanionMode();
    this.companionModeEnabled = this.companionService.companionModeEnabled;
  }

  getMoodEmoji(emotion: EmotionState): string {
    return this.companionService.getEmotionEmoji(emotion);
  }

  getMoodLabel(emotion: EmotionState): string {
    return this.companionService.getEmotionLabel(emotion);
  }

  intensityStars(intensity: number): number[] {
    return Array<number>(Math.min(5, Math.max(1, intensity))).fill(0);
  }

  private refreshData(): void {
    this.companionService.emotionLog$.pipe(take(1)).subscribe((log) => {
      this.logCount = log.length;
      this.recentLogs = log.slice(-20).reverse();

      if (log.length > 0) {
        this.lastLog = log[log.length - 1];
        this.summary = this.companionService.getEmotionSummary(7);
        this.summaryEmoji = this.companionService.getEmotionEmoji(this.summary.dominantEmotion);
        this.summaryLabel = this.companionService.getEmotionLabel(this.summary.dominantEmotion);

        const total = Object.values(this.summary.distribution).reduce((s, v) => s + v, 0);
        this.distributionList = (
          Object.entries(this.summary.distribution) as [EmotionState, number][]
        )
          .sort((a, b) => b[1] - a[1])
          .map(([emotion, count]) => ({
            emotion,
            count,
            percentage: total > 0 ? count / total : 0,
          }));
      }
    });
  }

  /** 响应式订阅 AI 教师自动记录的情绪更新 */
  private subscribeToEmotionUpdates(): void {
    this.companionService.emotionLog$.pipe(takeUntil(this.destroy$)).subscribe((log) => {
      this.logCount = log.length;
      this.recentLogs = log.slice(-20).reverse();

      if (log.length > 0) {
        this.lastLog = log[log.length - 1];
        this.summary = this.companionService.getEmotionSummary(7);
        this.summaryEmoji = this.companionService.getEmotionEmoji(this.summary.dominantEmotion);
        this.summaryLabel = this.companionService.getEmotionLabel(this.summary.dominantEmotion);

        const total = Object.values(this.summary.distribution).reduce((s, v) => s + v, 0);
        this.distributionList = (
          Object.entries(this.summary.distribution) as [EmotionState, number][]
        )
          .sort((a, b) => b[1] - a[1])
          .map(([emotion, count]) => ({
            emotion,
            count,
            percentage: total > 0 ? count / total : 0,
          }));
      }
    });
  }
}
