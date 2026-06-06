import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { catchError, finalize, of, switchMap } from 'rxjs';

import { AntiCheatService } from '../../services/anti-cheat.service';
import { ExamService, Question } from '../../services/exam.service';

@Component({
  selector: 'app-exam-taking',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="exam-taking-container" *ngIf="!loading && !error && attemptId">
      <!-- 顶部导航栏 -->
      <div class="exam-header-bar">
        <div class="exam-info">
          <h2>{{ examTitle }}</h2>
          <span class="timer" [class.timer-warning]="timeRemaining < 300">
            {{ formatTime(timeRemaining) }}
          </span>
        </div>
        <div class="progress-info">第 {{ currentIndex + 1 }} / {{ questions.length }} 题</div>
      </div>

      <!-- 题目内容 -->
      <div class="question-area">
        <div class="question-card">
          <div class="question-header">
            <span class="question-type-badge" [class]="currentQuestion.question_type">
              {{ typeLabel(currentQuestion.question_type) }}
            </span>
            <span class="question-score">{{ currentQuestion.score }} 分</span>
          </div>

          <h3 class="question-title">
            {{ currentQuestion.question_type === 'true_false' ? '' : ''
            }}{{ currentQuestion.title }}
          </h3>

          <!-- 单选题 -->
          <div *ngIf="currentQuestion.question_type === 'single_choice'" class="options-list">
            <label
              *ngFor="let option of currentQuestion.options; let i = index"
              class="option-item"
              [class.selected]="answers[currentQuestion.id] === option"
            >
              <input
                type="radio"
                [name]="'q_' + currentQuestion.id"
                [value]="option"
                [checked]="answers[currentQuestion.id] === option"
                (change)="selectAnswer(currentQuestion.id, option)"
              />
              <span class="option-text">{{ option }}</span>
            </label>
          </div>

          <!-- 多选题 -->
          <div *ngIf="currentQuestion.question_type === 'multiple_choice'" class="options-list">
            <label
              *ngFor="let option of currentQuestion.options; let i = index"
              class="option-item"
              [class.selected]="isMultipleSelected(currentQuestion.id, option)"
            >
              <input
                type="checkbox"
                [name]="'q_' + currentQuestion.id + '_' + i"
                [value]="option"
                [checked]="isMultipleSelected(currentQuestion.id, option)"
                (change)="toggleMultipleAnswer(currentQuestion.id, option)"
              />
              <span class="option-text">{{ option }}</span>
            </label>
          </div>

          <!-- 判断题 -->
          <div
            *ngIf="currentQuestion.question_type === 'true_false'"
            class="options-list true-false"
          >
            <label class="option-item" [class.selected]="answers[currentQuestion.id] === 'true'">
              <input
                type="radio"
                [name]="'tf_' + currentQuestion.id"
                value="true"
                [checked]="answers[currentQuestion.id] === 'true'"
                (change)="selectAnswer(currentQuestion.id, 'true')"
              />
              正确
            </label>
            <label class="option-item" [class.selected]="answers[currentQuestion.id] === 'false'">
              <input
                type="radio"
                [name]="'tf_' + currentQuestion.id"
                value="false"
                [checked]="answers[currentQuestion.id] === 'false'"
                (change)="selectAnswer(currentQuestion.id, 'false')"
              />
              错误
            </label>
          </div>

          <!-- 简答题 -->
          <div *ngIf="currentQuestion.question_type === 'short_answer'" class="text-answer">
            <textarea
              [(ngModel)]="answers[currentQuestion.id]"
              placeholder="请输入你的答案..."
              rows="6"
              class="answer-textarea"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <button class="nav-button" (click)="prevQuestion()" [disabled]="currentIndex === 0">
          上一题
        </button>
        <div class="question-dots">
          <span
            *ngFor="let q of questions; let i = index"
            class="dot"
            [class.active]="i === currentIndex"
            [class.answered]="answers[q.id]"
            (click)="goToQuestion(i)"
            >{{ i + 1 }}</span
          >
        </div>
        <button
          *ngIf="currentIndex < questions.length - 1"
          class="nav-button"
          (click)="nextQuestion()"
        >
          下一题
        </button>
        <button
          *ngIf="currentIndex === questions.length - 1"
          class="submit-button"
          (click)="submitExam()"
        >
          提交答卷
        </button>
      </div>
    </div>

    <!-- 加载/错误状态 -->
    <div *ngIf="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    <div *ngIf="error" class="error-state">
      <p>{{ errorMessage }}</p>
    </div>
  `,
  styles: [
    `
      .exam-taking-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 16px;
      }
      .exam-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 24px;
      }
      .exam-info h2 {
        font-size: 18px;
        margin: 0;
        color: #1d1d1f;
      }
      .timer {
        font-size: 20px;
        font-weight: 700;
        color: #333;
        font-variant-numeric: tabular-nums;
      }
      .timer-warning {
        color: #ff3b30;
        animation: pulse 1s infinite;
      }
      @keyframes pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }
      .progress-info {
        font-size: 14px;
        color: #86868b;
      }
      .question-card {
        background: white;
        border-radius: 12px;
        padding: 32px;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        min-height: 300px;
      }
      .question-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 16px;
      }
      .question-type-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
      }
      .question-type-badge.single_choice {
        background: #e3f2fd;
        color: #1565c0;
      }
      .question-type-badge.multiple_choice {
        background: #fce4ec;
        color: #c62828;
      }
      .question-type-badge.true_false {
        background: #e8f5e9;
        color: #2e7d32;
      }
      .question-type-badge.short_answer {
        background: #fff3e0;
        color: #ef6c00;
      }
      .question-score {
        font-size: 14px;
        color: #86868b;
      }
      .question-title {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 24px;
        line-height: 1.6;
        color: #1d1d1f;
      }
      .options-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .option-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 16px;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s;
      }
      .option-item:hover {
        border-color: #3b82f6;
        background: #f5f7ff;
      }
      .option-item.selected {
        border-color: #3b82f6;
        background: #eef0ff;
      }
      .option-item input {
        display: none;
      }
      .option-text {
        font-size: 15px;
      }
      .true-false {
        flex-direction: row;
        gap: 20px;
      }
      .true-false .option-item {
        flex: 1;
        justify-content: center;
        font-size: 16px;
        font-weight: 500;
      }
      .text-answer {
        margin-top: 16px;
      }
      .answer-textarea {
        width: 100%;
        padding: 16px;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        font-size: 15px;
        line-height: 1.6;
        resize: vertical;
        transition: border-color 0.2s;
      }
      .answer-textarea:focus {
        outline: none;
        border-color: #3b82f6;
      }
      .action-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        gap: 16px;
      }
      .nav-button {
        padding: 12px 28px;
        border: 2px solid #3b82f6;
        background: white;
        color: #3b82f6;
        border-radius: 8px;
        font-size: 15px;
        cursor: pointer;
        transition: all 0.2s;
      }
      .nav-button:hover:not(:disabled) {
        background: #3b82f6;
        color: white;
      }
      .nav-button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }
      .submit-button {
        padding: 12px 28px;
        background: #34c759;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      .submit-button:hover {
        background: #2db84e;
      }
      .question-dots {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        justify-content: center;
      }
      .dot {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-size: 12px;
        cursor: pointer;
        background: #f0f0f0;
        color: #666;
      }
      .dot.active {
        background: #3b82f6;
        color: white;
        font-weight: 600;
      }
      .dot.answered {
        background: #e8f5e9;
        color: #2e7d32;
      }
      .dot.answered.active {
        background: #3b82f6;
        color: white;
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
export class ExamTakingComponent implements OnInit, OnDestroy {
  examId = 0;
  attemptId = 0;
  questions: Question[] = [];
  currentIndex = 0;
  answers: Record<string, string | string[]> = {};
  examTitle = '';
  timeRemaining = 0;
  private timerInterval: ReturnType<typeof setInterval> | null = null;

  loading = true;
  error = false;
  errorMessage = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private examService: ExamService,
    private antiCheatService: AntiCheatService
  ) {}

  get currentQuestion(): Question {
    return this.questions[this.currentIndex];
  }

  ngOnInit(): void {
    this.examId = Number(this.route.snapshot.paramMap.get('examId'));
    this.startExam();
  }

  ngOnDestroy(): void {
    this.antiCheatService.stopMonitoring();
    if (this.timerInterval) clearInterval(this.timerInterval);
  }

  private startExam(): void {
    this.loading = true;
    this.examService
      .startExam(this.examId)
      .pipe(
        switchMap((response) => {
          this.attemptId = response.attempt_id;
          this.questions = response.questions;
          this.examTitle = '测验';

          // 启动防作弊监控
          this.antiCheatService.startMonitoring(this.attemptId, {
            fullscreenRequired: true,
            restrictPaste: true,
            restrictCopy: true,
          });

          // 获取测验详情获取标题和时间
          return this.examService.getExam(this.examId);
        }),
        catchError((err: Error) => {
          this.error = true;
          this.errorMessage = err.message || '加载失败';
          return of(null);
        }),
        finalize(() => (this.loading = false))
      )
      .subscribe((exam) => {
        if (exam) {
          this.examTitle = exam.title;
          // 如果启用了随机排序，打乱题目顺序
          if (exam.shuffle_questions) {
            this.questions = this.shuffleArray(this.questions);
          }
          this.timeRemaining = exam.duration_minutes * 60;
          this.startTimer();
        }
      });
  }

  private startTimer(): void {
    this.timerInterval = setInterval(() => {
      this.timeRemaining--;
      if (this.timeRemaining <= 0) {
        this.submitExam();
      }
    }, 1000);
  }

  selectAnswer(questionId: number, answer: string): void {
    this.answers[questionId] = answer;
  }

  isMultipleSelected(questionId: number, option: string): boolean {
    const selected = this.answers[questionId] as string[] | undefined;
    return Array.isArray(selected) && selected.includes(option);
  }

  toggleMultipleAnswer(questionId: number, option: string): void {
    if (!Array.isArray(this.answers[questionId])) {
      this.answers[questionId] = [];
    }
    const arr = this.answers[questionId];
    const index = arr.indexOf(option);
    if (index >= 0) {
      arr.splice(index, 1);
    } else {
      arr.push(option);
    }
  }

  nextQuestion(): void {
    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++;
    }
  }

  prevQuestion(): void {
    if (this.currentIndex > 0) {
      this.currentIndex--;
    }
  }

  goToQuestion(index: number): void {
    if (index >= 0 && index < this.questions.length) {
      this.currentIndex = index;
    }
  }

  submitExam(): void {
    if (!confirm('确定要提交答卷吗？提交后不可修改。')) return;

    this.loading = true;
    this.antiCheatService.stopMonitoring();
    if (this.timerInterval) clearInterval(this.timerInterval);

    this.examService
      .submitExam(this.attemptId, this.answers)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: () => {
          void this.router.navigate(['/exam/attempts', this.attemptId, 'result']);
        },
        error: (err: Error) => {
          this.error = true;
          this.errorMessage = err.message || '提交失败';
        },
      });
  }

  formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  typeLabel(t: string): string {
    const labels: Record<string, string> = {
      single_choice: '单选题',
      multiple_choice: '多选题',
      true_false: '判断题',
      short_answer: '简答题',
      coding: '编程题',
    };
    return labels[t] || t;
  }

  private shuffleArray<T>(arr: T[]): T[] {
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }
}
