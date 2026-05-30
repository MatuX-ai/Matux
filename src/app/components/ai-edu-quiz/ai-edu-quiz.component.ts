import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, Input, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

import { AIEduAntiCheatingService } from '../../core/services/ai-edu/ai-edu-anti-cheating.service';

import { QuizExplanationPanelComponent } from './components/quiz-explanation-panel/quiz-explanation-panel.component';
import { QuizQuestionDisplayComponent } from './components/quiz-question-display/quiz-question-display.component';
import { QuizResultPanelComponent } from './components/quiz-result-panel/quiz-result-panel.component';
import { QuizTimerComponent } from './components/quiz-timer/quiz-timer.component';

/**
 * 测验题目类型
 */
interface QuizQuestion {
  id: number;
  type: 'choice' | 'fill' | 'code' | 'matching';
  content: string;
  options?: string[]; // 选择题选项
  correct_answer?: string | string[];
  points: number;
  difficulty: number;
}

/**
 * 测验状态
 */
interface QuizState {
  quiz_id: number;
  lesson_id: number;
  questions: QuizQuestion[];
  current_question_index: number;
  answers: Map<number, unknown>;
  started_at: string;
  time_limit_minutes?: number;
}

interface CodeExecuteResponse {
  output: string;
  passed: boolean;
}

/**
 * 测验提交响应
 */
interface QuizSubmitResponse {
  score: number;
  points_earned: number;
}

/**
 * 答案解析响应
 */
interface QuizReviewResponse {
  result: {
    score: number;
    total_score: number;
    points_earned: number;
  };
  explanations: Array<{
    question_number: number;
    question_type: string;
    difficulty: number;
    question_content: string;
    options?: string[];
    correct_answer: number | string | string[];
    explanation?: string;
    knowledge_points?: string[];
    tips?: string[];
    general_feedback?: string;
  }>;
}

interface QuizSubmitResponse {
  score: number;
  points_earned: number;
}

@Component({
  selector: 'app-ai-edu-quiz',
  templateUrl: './ai-edu-quiz.component.html',
  styleUrls: ['./ai-edu-quiz.component.scss'],
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MonacoEditorModule,
    QuizQuestionDisplayComponent,
    QuizResultPanelComponent,
    QuizExplanationPanelComponent,
    QuizTimerComponent,
  ],
  providers: [AIEduAntiCheatingService],
})
export class AIEduQuizComponent implements OnInit {
  @Input() lessonId!: number;
  @Input() userId: number = 1;

  loading = false;
  error: string | null = null;
  quizState: QuizState | null = null;

  userAnswers: { [key: number]: string | number | string[] } = {};
  submitted = false;
  showResult = false;
  showCorrectAnswer = false;
  showWrongAnswer = false;
  finalScore = 0;
  totalPossibleScore = 0;
  earnedPoints = 0;

  remainingTime = 0;
  private timerInterval?: ReturnType<typeof setInterval>;

  codeOutput = '';
  testPassed = false;

  editorOptions = {
    theme: 'vs-dark',
    language: 'python',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    automaticLayout: true,
  };

  screenChangeWarning = 0;
  suspiciousActivity = false;

  // 答案解析相关
  showExplanationPanel = false;
  questionExplanations: Array<{
    question_number: number;
    question_type: string;
    difficulty: number;
    question_content: string;
    options?: string[];
    correct_answer: number | string | string[];
    explanation?: string;
    knowledge_points?: string[];
    tips?: string[];
    general_feedback?: string;
  }> = [];
  quizResult: { score: number; total_score: number; points_earned: number } | null = null;

  constructor(
    private http: HttpClient,
    private router: Router,
    private antiCheatingService: AIEduAntiCheatingService
  ) {}

  ngOnInit(): void {
    this.startQuiz();
    this.initAntiCheatingMonitoring();
  }

  /**
   * 开始测验
   */
  startQuiz(): void {
    this.loading = true;
    this.error = null;

    const API_BASE = 'http://localhost:8000/api/v1/org/1/ai-edu';

    this.http
      .post<QuizState>(`${API_BASE}/quiz/start`, {
        lesson_id: this.lessonId,
        user_id: this.userId,
      })
      .subscribe({
        next: (data: QuizState) => {
          this.quizState = data;
          this.totalPossibleScore = data.questions.reduce(
            (sum: number, q: QuizQuestion) => sum + q.points,
            0
          );
          this.remainingTime = data.time_limit_minutes ? data.time_limit_minutes * 60 : 9999;
          this.startTimer();
          this.loading = false;
        },
        error: (_error) => {
          this.error = '启动测验失败，请稍后重试';
          this.loading = false;
        },
      });
  }

  /**
   * 启动计时器
   */
  startTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }

    this.timerInterval = setInterval(() => {
      if (this.remainingTime > 0) {
        this.remainingTime--;
        if (this.remainingTime <= 0) {
          this.submitQuiz();
        }
      }
    }, 1000);
  }

  /**
   * 格式化时间
   */
  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }

  /**
   * 获取当前题目
   */
  get currentQuestion(): QuizQuestion {
    if (!this.quizState) {
      throw new Error('测验状态未初始化');
    }
    return this.quizState.questions[this.quizState.current_question_index];
  }

  /**
   * 获取题目类型标签
   */
  getQuestionTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      choice: '选择题',
      fill: '填空题',
      code: '编程题',
      matching: '匹配题',
    };
    return labels[type] || type;
  }

  /**
   * 获取选项标签 (A, B, C, D...)
   */
  getOptionLabel(index: number): string {
    return String.fromCharCode(65 + index);
  }

  /**
   * 初始化防作弊监控
   */
  initAntiCheatingMonitoring(): void {
    // 监听切屏事件
    this.antiCheatingService.getScreenChangeEvents().subscribe((event) => {
      if (!event.visible) {
        this.screenChangeWarning = event.count;
        this.suspiciousActivity = true;

        if (event.count >= 5) {
          alert(`⚠️ 警告：您已切屏${event.count}次，继续切屏可能会导致测验无效！`);
        }
      }
    });

    // 监听时间违规
    this.antiCheatingService.getTimeViolations().subscribe((event) => {
      if (event.violation) {
        // TODO: 处理时间违规事件，例如记录日志或警告用户
        console.warn('检测到时间违规事件:', event);
      }
    });
  }

  /**
   * 选择答案
   */
  selectChoice(optionIndex: number): void {
    if (this.submitted) return;
    this.userAnswers[this.currentQuestion.id] = optionIndex;
  }

  /**
   * 判断是否正确选项
   */
  isCorrectChoice(optionIndex: number): boolean {
    const correct = this.currentQuestion.correct_answer;
    if (Array.isArray(correct)) {
      // 将数字转换为字符串进行比较，因为数组包含的是字符串
      return correct.includes(optionIndex.toString());
    }
    // 将字符串转换为数字进行比较
    return Number(correct) === optionIndex;
  }

  /**
   * 是否已答题
   */
  hasAnswered(): boolean {
    return this.userAnswers[this.currentQuestion.id] !== undefined;
  }

  /**
   * 题目是否已回答
   */
  isQuestionAnswered(index: number): boolean {
    if (!this.quizState) return false;
    const question = this.quizState.questions[index];
    return this.userAnswers[question.id] !== undefined;
  }

  /**
   * 上一题
   */
  previousQuestion(): void {
    if (!this.quizState) return;
    if (this.quizState.current_question_index > 0) {
      this.quizState.current_question_index--;
    }
  }

  /**
   * 下一题
   */
  nextQuestion(): void {
    if (!this.quizState) return;
    if (this.quizState.current_question_index < this.quizState.questions.length - 1) {
      this.quizState.current_question_index++;
    }
  }

  /**
   * 跳转到指定题目
   */
  goToQuestion(index: number): void {
    if (!this.quizState) return;
    this.quizState.current_question_index = index;
  }

  /**
   * 运行代码
   */
  runCode(): void {
    const API_BASE = 'http://localhost:8000/api/v1/org/1/ai-edu';

    this.http
      .post<CodeExecuteResponse>(`${API_BASE}/execute-code`, {
        code: this.userAnswers[this.currentQuestion.id] as string,
        language: 'python',
      })
      .subscribe({
        next: (result: CodeExecuteResponse) => {
          this.codeOutput = result.output || '运行成功';
          this.testPassed = result.passed || false;
        },
        error: (_error) => {
          const errorMessage = (_error as Error).message || '未知错误';
          this.codeOutput = '运行失败：' + errorMessage;
          this.testPassed = false;
        },
      });
  }

  /**
   * 提交测验
   */
  submitQuiz(): void {
    if (this.submitted) return;
    if (!this.quizState) {
      console.error('测验状态未初始化，无法提交');
      return;
    }

    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }

    // 生成防作弊报告
    const antiCheatingReport = this.antiCheatingService.generateReport();

    const API_BASE = 'http://localhost:8000/api/v1/org/1/ai-edu';

    const answers = this.quizState.questions.map((q) => ({
      question_id: q.id,
      answer: this.userAnswers[q.id],
    }));

    this.http
      .post<QuizSubmitResponse>(`${API_BASE}/quiz/submit`, {
        quiz_id: this.quizState.quiz_id,
        answers,
        anti_cheating_report: antiCheatingReport, // 附加防作弊报告
      })
      .subscribe({
        next: (result: QuizSubmitResponse) => {
          this.submitted = true;
          this.finalScore = result.score;
          this.earnedPoints = result.points_earned;
          this.showResult = true;

          // 显示防作弊警告（如果有）
          if (antiCheatingReport.isSuspicious) {
            alert(
              `⚠️ 警告：检测到${antiCheatingReport.suspiciousActivities}次可疑活动，您的成绩可能受影响。\n\n切屏次数：${antiCheatingReport.totalScreenChanges}\n可疑活动：${antiCheatingReport.suspiciousActivities}`
            );
          }
        },
        error: (_error) => {
          alert('提交失败，请稍后重试');
        },
      });
  }

  /**
   * 关闭结果
   */
  async closeResult(): Promise<void> {
    this.showResult = false;
    await this.router.navigate(['/courses']);
  }

  /**
   * 查看解析
   */
  reviewAnswers(): void {
    const API_BASE = 'http://localhost:8000/api/v1/org/1/ai-edu';

    this.http
      .get<QuizReviewResponse>(`${API_BASE}/quiz/${this.quizState?.quiz_id}/review`)
      .subscribe({
        next: (data: QuizReviewResponse) => {
          this.quizResult = data.result;
          this.questionExplanations = data.explanations || [];
          this.showExplanationPanel = true;
        },
        error: (_error) => {
          alert('获取解析失败，请稍后重试');
        },
      });
  }

  /**
   * 关闭解析面板
   */
  closeExplanation(): void {
    this.showExplanationPanel = false;
  }

  /**
   * 判断是否是错误答案
   */
  isWrongAnswer(
    explanation: { correct_answer: number | string | string[] },
    optionIndex: number
  ): boolean {
    // 这里简化处理，实际应该根据用户答案来判断
    if (Array.isArray(explanation.correct_answer)) {
      return !explanation.correct_answer.includes(optionIndex.toString());
    }
    return Number(explanation.correct_answer) !== optionIndex;
  }

  /**
   * 格式化正确答案
   */
  formatCorrectAnswer(explanation: {
    question_type: string;
    correct_answer: number | string | string[];
  }): string {
    if (explanation.question_type === 'choice') {
      const answerIndex =
        typeof explanation.correct_answer === 'string'
          ? Number(explanation.correct_answer)
          : (explanation.correct_answer as number);
      return this.getOptionLabel(answerIndex);
    } else if (explanation.question_type === 'code') {
      return String(explanation.correct_answer);
    } else {
      return String(explanation.correct_answer);
    }
  }

  /**
   * 重新测验
   */
  retryQuiz(): void {
    this.showResult = false;
    this.submitted = false;
    this.userAnswers = {};
    this.startQuiz();
  }

  /**
   * 获取当前得分
   */
  get currentScore(): number {
    // 实时计算已答题目的得分 (简化版本)
    let score = 0;
    const quizState = this.quizState;
    if (!quizState) return 0;

    for (let i = 0; i <= quizState.current_question_index; i++) {
      const question = quizState.questions[i];
      const userAnswer = this.userAnswers[question.id];
      if (userAnswer !== undefined) {
        if (Array.isArray(question.correct_answer)) {
          if (JSON.stringify(userAnswer) === JSON.stringify(question.correct_answer)) {
            score += question.points;
          }
        } else {
          if (userAnswer === question.correct_answer) {
            score += question.points;
          }
        }
      }
    }
    return score;
  }

  /**
   * 得分率
   */
  get scorePercentage(): number {
    if (this.totalPossibleScore === 0) return 0;
    return Math.round((this.finalScore / this.totalPossibleScore) * 100);
  }

  /**
   * 正确率
   */
  get accuracyRate(): number {
    const answeredCount = Object.keys(this.userAnswers).length;
    if (answeredCount === 0 || !this.quizState) return 0;

    const correctCount = this.quizState.questions.filter((q) => {
      const userAnswer = this.userAnswers[q.id];
      if (Array.isArray(q.correct_answer)) {
        return JSON.stringify(userAnswer) === JSON.stringify(q.correct_answer);
      }
      return userAnswer === q.correct_answer;
    }).length;
    return Math.round((correctCount / answeredCount) * 100);
  }

  /**
   * 用时
   */
  get timeSpent(): string {
    const quizState = this.quizState;
    if (!quizState) return '0:00';

    const timeLimit = quizState.time_limit_minutes ?? 0;
    const totalSeconds = timeLimit * 60 - this.remainingTime;
    return this.formatTime(totalSeconds >= 0 ? totalSeconds : 0);
  }
}
