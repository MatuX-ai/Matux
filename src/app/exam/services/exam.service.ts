/* eslint-disable no-console */
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface Exam {
  id: number;
  title: string;
  description?: string;
  course_id?: number;
  difficulty: string;
  status: string;
  duration_minutes: number;
  start_time?: string;
  end_time?: string;
  passing_score: number;
  max_attempts: number;
  shuffle_questions: boolean;
  anti_cheat_enabled: boolean;
  total_questions: number;
  total_score: number;
  attempt_count?: number;
  created_at: string;
  questions?: Question[];
}

export interface Question {
  id: number;
  exam_id: number;
  question_type: 'single_choice' | 'multiple_choice' | 'true_false' | 'short_answer' | 'coding';
  title: string;
  description?: string;
  options?: string[];
  correct_answer?: string;
  score: number;
  order_index: number;
  explanation?: string;
  difficulty: string;
}

export interface ExamAttempt {
  id: number;
  exam_id: number;
  user_id: number;
  status: string;
  score?: number;
  total_score?: number;
  percentage?: number;
  started_at: string;
  submitted_at?: string;
  time_spent_seconds?: number;
  answers?: Record<string, unknown>;
  cheat_events?: CheatEvent[];
}

export interface CheatEvent {
  id: number;
  attempt_id: number;
  cheat_type: string;
  severity: number;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface ExamStatistics {
  total_attempts: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  pass_rate: number;
  average_time_spent: number;
}

/**
 * 【P2修复】统一错误处理函数
 */
function handleExamError(error: HttpErrorResponse): Observable<never> {
  let errorMessage = '操作失败，请稍后重试';

  if (error.status === 0) {
    errorMessage = '网络连接失败，请检查网络设置';
  } else if (error.status === 401) {
    errorMessage = '登录已过期，请重新登录';
  } else if (error.status === 403) {
    errorMessage = '您没有权限执行此操作';
  } else if (error.status === 404) {
    errorMessage = '请求的资源不存在';
  } else if (error.status === 429) {
    errorMessage = '请求过于频繁，请稍后再试';
  } else if (error.status >= 500) {
    errorMessage = '服务器错误，请稍后重试';
  } else if ((error.error as { detail?: string })?.detail) {
    // 后端返回的详细错误信息
    errorMessage = (error.error as { detail: string }).detail;
  }

  console.error('[ExamService] Error:', errorMessage, error);
  return throwError(() => new Error(errorMessage));
}

@Injectable({
  providedIn: 'root',
})
export class ExamService {
  private readonly API_URL = '/api/v1/exams';

  constructor(private http: HttpClient) {}

  /** 获取测验列表 */
  getExams(
    status?: string,
    courseId?: number,
    page = 1,
    pageSize = 20
  ): Observable<{ exams: Exam[]; total: number; page: number; page_size: number }> {
    const params: Record<string, string | number> = { page, page_size: pageSize };
    if (status) params['status'] = status;
    if (courseId) params['course_id'] = courseId;
    return this.http
      .get<{ exams: Exam[]; total: number; page: number; page_size: number }>(this.API_URL, {
        params,
      })
      .pipe(catchError(handleExamError));
  }

  /** 获取测验详情（含题目） */
  getExam(examId: number): Observable<Exam> {
    return this.http.get<Exam>(`${this.API_URL}/${examId}`).pipe(catchError(handleExamError));
  }

  /** 开始考试 */
  startExam(
    examId: number
  ): Observable<{ attempt_id: number; started_at: string; questions: Question[] }> {
    return this.http
      .post<{
        attempt_id: number;
        started_at: string;
        questions: Question[];
      }>(`${this.API_URL}/${examId}/start`, {})
      .pipe(catchError(handleExamError));
  }

  /** 提交答案 */
  submitExam(attemptId: number, answers: Record<string, unknown>): Observable<ExamAttempt> {
    return this.http
      .post<ExamAttempt>(`${this.API_URL}/attempts/${attemptId}/submit`, { answers })
      .pipe(catchError(handleExamError));
  }

  /** 获取答题记录 */
  getAttempt(attemptId: number): Observable<ExamAttempt> {
    return this.http
      .get<ExamAttempt>(`${this.API_URL}/attempts/${attemptId}`)
      .pipe(catchError(handleExamError));
  }

  /** 获取我的答题记录 */
  getMyAttempts(examId: number): Observable<{ attempts: ExamAttempt[] }> {
    return this.http
      .get<{ attempts: ExamAttempt[] }>(`${this.API_URL}/${examId}/my-attempts`)
      .pipe(catchError(handleExamError));
  }

  /** 获取测验统计 */
  getStatistics(examId: number): Observable<ExamStatistics> {
    return this.http
      .get<ExamStatistics>(`${this.API_URL}/${examId}/statistics`)
      .pipe(catchError(handleExamError));
  }

  /** 防作弊心跳上报 */
  reportCheatEvent(
    attemptId: number,
    cheatType: string,
    details?: Record<string, unknown>,
    severity = 1
  ): Observable<unknown> {
    return this.http
      .post(`${this.API_URL}/attempts/${attemptId}/heartbeat`, {
        cheat_type: cheatType,
        details,
        severity,
      })
      .pipe(
        catchError((error: HttpErrorResponse) => {
          // 心跳上报失败不应阻塞用户，可降级处理
          console.warn('[ExamService] 心跳上报失败:', error);
          return throwError(() => new Error('心跳上报失败'));
        })
      );
  }
}
