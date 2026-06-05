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

import { EmotionalCompanionService, EmotionState, EmotionSummary, EmotionLogEntry } from '../../../core/services/emotional-companion.service';

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
  template: `
    <div class="companion-container">
      <div class="page-header">
        <h1 class="page-title">🤗 情感陪伴</h1>
      </div>

      <!-- 陪伴模式开关 -->
      <mat-card class="companion-mode-card">
        <mat-card-content>
          <div class="companion-mode-header">
            <h2 class="companion-mode-title">🤖 AI 陪伴模式</h2>
            <mat-slide-toggle
              [checked]="companionModeEnabled"
              (change)="toggleCompanionMode()"
              color="primary"
            >
              {{ companionModeEnabled ? '已开启' : '已关闭' }}
            </mat-slide-toggle>
          </div>
          <p class="companion-mode-desc">
            开启后，AI 教师会在对话中自动感知你的情绪状态并调整回应方式
          </p>
        </mat-card-content>
      </mat-card>

      <!-- 今日心情记录 -->
      <mat-card class="mood-card">
        <mat-card-content>
          <h2 class="mood-title">今天的心情怎么样？</h2>
          <div class="mood-picker">
            <button
              *ngFor="let m of moodOptions"
              type="button"
              class="mood-btn"
              [class.selected]="selectedMood === m.emotion"
              (click)="recordMood(m.emotion)"
              [style.--mood-color]="m.color"
            >
              <span class="mood-emoji">{{ m.emoji }}</span>
              <span class="mood-label">{{ m.label }}</span>
            </button>
          </div>
          <div *ngIf="lastLog" class="mood-reply">
            <mat-icon>reply</mat-icon>
            <p>{{ lastLog.companionReply }}</p>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 情绪趋势摘要 -->
      <mat-card class="summary-card" *ngIf="logCount > 0">
        <mat-card-header>
          <mat-card-title>📊 近期情绪趋势</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="summary-grid">
            <div class="summary-item">
              <span class="summary-value summary-dominant">{{ summaryEmoji }} {{ summaryLabel }}</span>
              <span class="summary-label">主导情绪</span>
            </div>
            <div class="summary-item">
              <span class="summary-value" [style.color]="(summary?.positivityRatio ?? 0) >= 0.6 ? '#22c55e' : '#f59e0b'">
                {{ summary?.positivityRatio | percent:'1.0-0' }}
              </span>
              <span class="summary-label">积极比例</span>
            </div>
            <div class="summary-item">
              <span class="summary-value" [style.color]="(summary?.volatility ?? 0) < 0.3 ? '#22c55e' : (summary?.volatility ?? 0) < 0.6 ? '#f59e0b' : '#ef4444'">
                {{ summary?.volatility | percent:'1.0-0' }}
              </span>
              <span class="summary-label">情绪波动</span>
            </div>
          </div>
          <p class="encouragement-text">{{ summary?.encouragement || '' }}</p>
        </mat-card-content>
      </mat-card>

      <!-- 情绪分布 -->
      <mat-card *ngIf="logCount > 0" class="distribution-card">
        <mat-card-header>
          <mat-card-title>📈 情绪分布</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div *ngFor="let item of distributionList" class="dist-item">
            <span class="dist-emoji">{{ getMoodEmoji(item.emotion) }}</span>
            <span class="dist-label">{{ getMoodLabel(item.emotion) }}</span>
            <mat-progress-bar mode="determinate" [value]="item.percentage * 100" class="dist-bar"></mat-progress-bar>
            <span class="dist-count">{{ item.count }}次</span>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 历史记录 -->
      <mat-card *ngIf="logCount > 0" class="history-card">
        <mat-card-header>
          <mat-card-title>📋 心情记录</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div *ngFor="let entry of recentLogs" class="history-entry">
            <span class="history-emoji">{{ getMoodEmoji(entry.emotion) }}</span>
            <div class="history-info">
              <span class="history-emotion">{{ getMoodLabel(entry.emotion) }}</span>
              <span class="history-time">{{ entry.timestamp | date:'MM/dd HH:mm' }}</span>
              <span *ngIf="entry.trigger" class="history-trigger">· {{ entry.trigger }}</span>
            </div>
            <div class="history-intensity">
              <span *ngFor="let _ of intensityStars(entry.intensity)" class="intensity-star">⭐</span>
            </div>
          </div>
          <div *ngIf="recentLogs.length === 0" class="no-history">
            <p>还没有心情记录，点击上方表情开始记录吧！</p>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 空状态 -->
      <div *ngIf="logCount === 0" class="empty-section">
        <mat-icon class="empty-icon">favorite</mat-icon>
        <h3>欢迎来到情感陪伴空间</h3>
        <p>在这里可以记录你的学习心情<br>AI 会为你送上温暖的鼓励和陪伴 💗</p>
      </div>
    </div>
  `,
  styles: [`
    .companion-container {
      padding: 24px;
      max-width: 800px;
      margin: 0 auto;
    }
    .page-header { margin-bottom: 24px; }
    .page-title {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--color-text-primary);
    }

    /* 陪伴模式开关 */
    .companion-mode-card {
      border-radius: 16px;
      margin-bottom: 16px;
      background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    }
    .companion-mode-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .companion-mode-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--color-text-primary);
    }
    .companion-mode-desc {
      margin: 0;
      font-size: 13px;
      color: var(--color-text-secondary);
      line-height: 1.5;
    }

    /* 心情选择 */
    .mood-card {
      border-radius: 16px;
      margin-bottom: 16px;
      background: linear-gradient(135deg, #fdf2f8, #fce7f3);
    }
    .mood-title {
      margin: 0 0 16px;
      font-size: 18px;
      color: #831843;
    }
    .mood-picker {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .mood-btn {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 12px 16px;
      border: 2px solid transparent;
      border-radius: 16px;
      background: rgba(255,255,255,0.7);
      cursor: pointer;
      transition: all 0.2s;
      min-width: 64px;
    }
    .mood-btn:hover {
      background: white;
      border-color: var(--mood-color, #d1d5db);
      transform: translateY(-2px);
    }
    .mood-btn.selected {
      background: white;
      border-color: var(--mood-color, #6366f1);
      box-shadow: 0 2px 12px rgba(99,102,241,0.2);
    }
    .mood-emoji { font-size: 28px; }
    .mood-label { font-size: 11px; color: var(--color-text-secondary); }

    .mood-reply {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      margin-top: 16px;
      padding: 12px 16px;
      background: rgba(255,255,255,0.8);
      border-radius: 12px;
      font-size: 14px;
      color: var(--color-text-secondary);
      line-height: 1.5;
    }
    .mood-reply mat-icon { color: #ec4899; margin-top: 2px; }
    .mood-reply p { margin: 0; }

    /* 摘要 */
    .summary-card { border-radius: 16px; margin-bottom: 16px; }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 16px;
    }
    .summary-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      padding: 16px;
      background: var(--color-background);
      border-radius: 12px;
    }
    .summary-value { font-size: 24px; font-weight: 700; }
    .summary-dominant { font-size: 20px; }
    .summary-label { font-size: 12px; color: var(--color-text-secondary); }

    .encouragement-text {
      margin: 0;
      text-align: center;
      color: #ec4899;
      font-size: 15px;
      font-weight: 500;
      padding: 12px;
      background: #fdf2f8;
      border-radius: 12px;
    }

    /* 分布 */
    .distribution-card { border-radius: 16px; margin-bottom: 16px; }
    .dist-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
    }
    .dist-emoji { font-size: 18px; min-width: 24px; }
    .dist-label { font-size: 13px; color: var(--color-text-secondary); min-width: 48px; }
    .dist-bar { flex: 1; }
    .dist-count { font-size: 12px; color: var(--color-text-disabled); min-width: 32px; text-align: right; }

    /* 历史 */
    .history-card { border-radius: 16px; margin-bottom: 16px; }
    .history-entry {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid var(--color-divider);
    }
    .history-entry:last-child { border-bottom: none; }
    .history-emoji { font-size: 20px; }
    .history-info {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .history-emotion { font-size: 14px; font-weight: 500; color: var(--color-text-primary); }
    .history-time { font-size: 12px; color: var(--color-text-disabled); }
    .history-trigger { font-size: 12px; color: var(--color-text-disabled); }
    .history-intensity { display: flex; gap: 2px; }
    .intensity-star { font-size: 10px; }

    .no-history {
      text-align: center;
      color: var(--color-text-disabled);
      padding: 24px;
    }

    /* 空状态 */
    .empty-section {
      text-align: center;
      padding: 64px 16px;
    }
    .empty-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      color: var(--color-info);
      margin-bottom: 16px;
    }
    .empty-section h3 {
      margin: 0 0 8px;
      color: var(--color-text-primary);
    }
    .empty-section p {
      color: var(--color-text-secondary);
      margin: 0;
      line-height: 1.8;
    }
  `],
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

  moodOptions: { emotion: EmotionState; emoji: string; label: string; color: string }[] = [
    { emotion: 'very_happy', emoji: '😄', label: '很开心', color: '#22c55e' },
    { emotion: 'happy', emoji: '🙂', label: '开心', color: '#86efac' },
    { emotion: 'neutral', emoji: '😐', label: '一般', color: '#94a3b8' },
    { emotion: 'confused', emoji: '🤔', label: '困惑', color: '#f59e0b' },
    { emotion: 'sad', emoji: '😢', label: '难过', color: '#6366f1' },
    { emotion: 'frustrated', emoji: '😫', label: '沮丧', color: '#f97316' },
    { emotion: 'anxious', emoji: '😰', label: '焦虑', color: '#ef4444' },
    { emotion: 'bored', emoji: '😴', label: '无聊', color: '#a1a1aa' },
    { emotion: 'angry', emoji: '😠', label: '生气', color: '#dc2626' },
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
    return Array(Math.min(5, Math.max(1, intensity))).fill(0);
  }

  private refreshData(): void {
    this.companionService.emotionLog$
      .pipe(take(1))
      .subscribe((log) => {
        this.logCount = log.length;
        this.recentLogs = log.slice(-20).reverse();

        if (log.length > 0) {
          this.lastLog = log[log.length - 1];
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
      });
  }

  /** 响应式订阅 AI 教师自动记录的情绪更新 */
  private subscribeToEmotionUpdates(): void {
    this.companionService.emotionLog$
      .pipe(takeUntil(this.destroy$))
      .subscribe((log) => {
        this.logCount = log.length;
        this.recentLogs = log.slice(-20).reverse();

        if (log.length > 0) {
          this.lastLog = log[log.length - 1];
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
      });
  }
}
