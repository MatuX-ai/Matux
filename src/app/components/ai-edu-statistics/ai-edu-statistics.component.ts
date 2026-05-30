/**
 * AI 课程学习统计组件
 * 显示用户的学习数据统计
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';

import { AIEduService } from '../../core/services/ai-edu.service';
import { LearningStatistics } from '../../models/ai-edu.models';

@Component({
  selector: 'app-ai-edu-statistics',
  standalone: true,
    imports: [CommonModule],
  template: `
    <div class="statistics-card">
      <h3>📊 学习统计</h3>

      <div class="stats-grid" *ngIf="statistics">
        <div class="stat-item">
          <div class="stat-icon">📚</div>
          <div class="stat-value">{{ statistics.total_courses }}</div>
          <div class="stat-label">总课程数</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">✅</div>
          <div class="stat-value">{{ statistics.completed_courses }}</div>
          <div class="stat-label">已完成</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">⏳</div>
          <div class="stat-value">{{ statistics.in_progress_courses }}</div>
          <div class="stat-label">进行中</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">🎯</div>
          <div class="stat-value">{{ statistics!.completion_rate | number: '1.0-0' }}%</div>
          <div class="stat-label">完成率</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">⏱️</div>
          <div class="stat-value">{{ statistics!.total_time_hours | number: '1.1-2' }}</div>
          <div class="stat-label">学习时长 (小时)</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">🏆</div>
          <div class="stat-value">{{ statistics.total_points }}</div>
          <div class="stat-label">总积分</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">📝</div>
          <div class="stat-value">{{ statistics!.average_quiz_score | number: '1.0-0' }}</div>
          <div class="stat-label">平均测验分</div>
        </div>

        <div class="stat-item">
          <div class="stat-icon">💻</div>
          <div class="stat-value">{{ statistics!.average_code_score | number: '1.0-0' }}</div>
          <div class="stat-label">平均代码分</div>
        </div>
      </div>

      <div class="loading" *ngIf="loading">
        <span>加载中...</span>
      </div>

      <div class="error" *ngIf="error && !loading">
        {{ error }}
      </div>
    </div>
  `,
  styles: [
    `
      .statistics-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
      }

      h3 {
        margin: 0 0 20px 0;
        color: #333;
        font-size: 18px;
      }

      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
      }

      .stat-item {
        text-align: center;
        padding: 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        color: white;
      }

      .stat-icon {
        font-size: 24px;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 4px;
      }

      .stat-label {
        font-size: 12px;
        opacity: 0.9;
      }

      .loading,
      .error {
        text-align: center;
        padding: 20px;
        color: #666;
      }

      .error {
        color: #f44336;
      }
    `,
  ],
})
export class AIEduStatisticsComponent implements OnInit {
  @Input() orgId: number = 1;
  @Input() userId: number = 1;

  statistics: LearningStatistics | null = null;
  loading = false;
  error: string | null = null;

  constructor(private aiEduService: AIEduService) {}

  ngOnInit(): void {
    this.loadStatistics();
  }

  loadStatistics(): void {
    this.loading = true;
    this.error = null;

    this.aiEduService.getStatistics(this.orgId).subscribe({
      next: (stats) => {
        this.statistics = stats;
        this.loading = false;
      },
      error: (error) => {
        this.error = '加载统计数据失败，请稍后重试';
        this.loading = false;
      },
    });
  }
}
