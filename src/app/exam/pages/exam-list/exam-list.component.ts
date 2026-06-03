import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { catchError, finalize, of } from 'rxjs';

import { Exam, ExamService } from '../../services/exam.service';

@Component({
  selector: 'app-exam-list',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="exam-list-container">
      <header class="page-header">
        <h1>在线测验</h1>
        <p>检验你的学习成果</p>
      </header>

      <div *ngIf="loading" class="loading-state">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <div *ngIf="error" class="error-state">
        <p>{{ errorMessage }}</p>
        <button (click)="loadExams()">重试</button>
      </div>

      <div *ngIf="!loading && !error" class="exam-grid">
        <div *ngFor="let exam of exams" class="exam-card" (click)="startExam(exam)">
          <div class="exam-header">
            <span class="difficulty-badge" [class]="exam.difficulty">
              {{ difficultyLabel(exam.difficulty) }}
            </span>
            <span class="question-count">{{ exam.total_questions }} 题</span>
          </div>
          <h3 class="exam-title">{{ exam.title }}</h3>
          <p class="exam-desc">{{ exam.description || '暂无描述' }}</p>
          <div class="exam-meta">
            <span>⏱ {{ exam.duration_minutes }} 分钟</span>
            <span>📊 {{ exam.passing_score }} 分及格</span>
          </div>
          <div *ngIf="exam.attempt_count > 0" class="attempt-info">
            已有 {{ exam.attempt_count }} 人参加
          </div>
          <button class="start-button">
            {{ exam.status === 'published' ? '开始答题' : '未发布' }}
          </button>
        </div>

        <div *ngIf="exams.length === 0" class="empty-state">
          <p>暂无可用测验</p>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .exam-list-container { max-width: 1200px; margin: 0 auto; padding: 32px 16px; }
      .page-header { margin-bottom: 32px; }
      .page-header h1 { font-size: 28px; color: #1d1d1f; margin-bottom: 8px; }
      .page-header p { color: #86868b; font-size: 16px; }
      .spinner { width: 40px; height: 40px; border: 3px solid #e0e0e0; border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 40px auto; }
      @keyframes spin { to { transform: rotate(360deg); } }
      .loading-state, .error-state, .empty-state { text-align: center; padding: 60px 0; color: #86868b; }
      .exam-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; }
      .exam-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
      .exam-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
      .exam-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
      .difficulty-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: capitalize; }
      .difficulty-badge.easy { background: #e8f5e9; color: #2e7d32; }
      .difficulty-badge.medium { background: #fff3e0; color: #ef6c00; }
      .difficulty-badge.hard { background: #ffebee; color: #c62828; }
      .question-count { font-size: 13px; color: #86868b; }
      .exam-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #1d1d1f; }
      .exam-desc { font-size: 14px; color: #86868b; margin-bottom: 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      .exam-meta { display: flex; gap: 16px; font-size: 13px; color: #666; margin-bottom: 12px; }
      .attempt-info { font-size: 12px; color: #667eea; margin-bottom: 12px; }
      .start-button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
      .start-button:hover { background: #5a6fd6; }
    `,
  ],
})
export class ExamListComponent implements OnInit {
  exams: Exam[] = [];
  loading = false;
  error = false;
  errorMessage = '';

  constructor(
    private examService: ExamService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadExams();
  }

  loadExams(): void {
    this.loading = true;
    this.error = false;
    this.examService.getExams('published')
      .pipe(
        catchError((err) => {
          this.error = true;
          this.errorMessage = err.message || '加载失败';
          return of({ exams: [], total: 0, page: 1, page_size: 20 });
        }),
        finalize(() => this.loading = false)
      )
      .subscribe((response) => {
        this.exams = response.exams;
      });
  }

  startExam(exam: Exam): void {
    if (exam.status !== 'published') return;
    void this.router.navigate(['/exam', exam.id, 'take']);
  }

  difficultyLabel(d: string): string {
    const labels: Record<string, string> = { easy: '简单', medium: '中等', hard: '困难' };
    return labels[d] || d;
  }
}
