import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { catchError, finalize, of } from 'rxjs';

import { ExamAttempt, ExamService } from '../../services/exam.service';

@Component({
  selector: 'app-exam-result',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="result-container" *ngIf="!loading && !error && attempt">
      <div class="result-card" [class.passed]="passed" [class.failed]="!passed">
        <div class="result-icon">{{ passed ? '🎉' : '😅' }}</div>
        <h2>{{ passed ? '恭喜通过！' : '未通过' }}</h2>
        <div class="score-section">
          <div class="score-circle">
            <span class="score-value">{{ attempt.percentage ?? 0 }}%</span>
          </div>
          <div class="score-detail">
            <p>得分：{{ attempt.score }} / {{ attempt.total_score }}</p>
            <p>状态：{{ statusLabel(attempt.status) }}</p>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">用时</span>
            <span class="stat-value">{{ formatTime(attempt.time_spent_seconds || 0) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">提交时间</span>
            <span class="stat-value">{{
              attempt.submitted_at || attempt.started_at | date: 'short'
            }}</span>
          </div>
        </div>

        <div *ngIf="attempt.cheat_events?.length" class="cheat-warning">
          ⚠️ 检测到 {{ attempt.cheat_events?.length }} 次可疑操作
        </div>

        <div class="action-buttons">
          <button class="btn-secondary" (click)="goBack()">返回列表</button>
        </div>
      </div>
    </div>

    <div *ngIf="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    <div *ngIf="error" class="error-state">
      <p>{{ errorMessage }}</p>
      <button (click)="loadResult()">重试</button>
    </div>
  `,
  styles: [
    `
      .result-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 32px 16px;
      }
      .result-card {
        background: white;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
      }
      .result-card.passed {
        border-top: 4px solid #34c759;
      }
      .result-card.failed {
        border-top: 4px solid #ff3b30;
      }
      .result-icon {
        font-size: 56px;
        margin-bottom: 16px;
      }
      h2 {
        font-size: 24px;
        margin-bottom: 24px;
      }
      .passed h2 {
        color: #2e7d32;
      }
      .failed h2 {
        color: #c62828;
      }
      .score-section {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
        margin-bottom: 32px;
      }
      .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #3b82f6, #2563eb);
      }
      .score-value {
        font-size: 28px;
        font-weight: 700;
        color: white;
      }
      .score-detail {
        text-align: left;
      }
      .score-detail p {
        margin: 4px 0;
        color: #666;
        font-size: 15px;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 24px;
      }
      .stat-item {
        padding: 16px;
        background: #f8f9fa;
        border-radius: 8px;
      }
      .stat-label {
        display: block;
        font-size: 12px;
        color: #86868b;
        margin-bottom: 4px;
      }
      .stat-value {
        font-size: 16px;
        font-weight: 600;
        color: #1d1d1f;
      }
      .cheat-warning {
        padding: 12px;
        background: #fff3e0;
        border-radius: 8px;
        color: #ef6c00;
        font-size: 14px;
        margin-bottom: 24px;
      }
      .action-buttons {
        display: flex;
        gap: 12px;
        justify-content: center;
      }
      .btn-secondary {
        padding: 12px 32px;
        border: 2px solid #3b82f6;
        background: white;
        color: #3b82f6;
        border-radius: 8px;
        font-size: 15px;
        cursor: pointer;
        transition: all 0.2s;
      }
      .btn-secondary:hover {
        background: #f5f7ff;
      }
      .spinner {
        width: 40px;
        height: 40px;
        border: 3px solid #e0e0e0;
        border-top-color: #3b82f6;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 40px auto;
      }
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
      .loading-state,
      .error-state {
        text-align: center;
        padding: 60px 0;
      }
    `,
  ],
})
export class ExamResultComponent implements OnInit {
  attempt: ExamAttempt | null = null;
  loading = true;
  error = false;
  errorMessage = '';
  passed = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private examService: ExamService
  ) {}

  ngOnInit(): void {
    this.loadResult();
  }

  loadResult(): void {
    this.loading = true;
    this.error = false;
    const attemptId = Number(this.route.snapshot.paramMap.get('attemptId'));

    this.examService
      .getAttempt(attemptId)
      .pipe(
        catchError((err: Error) => {
          this.error = true;
          this.errorMessage = err.message || '加载失败';
          return of(null);
        }),
        finalize(() => (this.loading = false))
      )
      .subscribe((attempt) => {
        if (attempt) {
          this.attempt = attempt;
          // 获取测验详情确认及格分
          this.examService.getExam(attempt.exam_id).subscribe((exam) => {
            this.passed = (attempt.percentage ?? 0) >= exam.passing_score;
          });
        }
      });
  }

  goBack(): void {
    void this.router.navigate(['/exam']);
  }

  formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}分${s}秒`;
  }

  statusLabel(s: string): string {
    const labels: Record<string, string> = {
      in_progress: '进行中',
      submitted: '待评分',
      graded: '已评分',
      timed_out: '超时',
      voided: '作废',
    };
    return labels[s] || s;
  }
}
