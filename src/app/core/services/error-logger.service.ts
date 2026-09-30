/**
 * 前端错误日志服务
 *
 * 负责:
 * 1. 监听 window.onerror / unhandledrejection
 * 2. 暴露手动 logError() 供业务代码调用
 * 3. 批量上报 (10 条阈值 / 30 秒定时) 到后端 `/api/v1/org/{org_id}/logs/error`
 * 4. localStorage 暂存失败日志,下次启动重试
 *
 * 后端 API 文档: backend/routes/error_log_routes.py
 */

import { HttpClient } from '@angular/common/http';
import { Injectable, isDevMode } from '@angular/core';
import { fromEvent, merge, of, Subject, timer } from 'rxjs';
import { auditTime, catchError, take } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

interface FrontendErrorLog {
  message: string;
  stack?: string;
  url: string;
  userAgent: string;
  userId?: string;
  timestamp: string;
  source: 'window.error' | 'unhandledrejection' | 'manual';
}

@Injectable({
  providedIn: 'root',
})
export class ErrorLoggerService {
  private readonly STORAGE_KEY = 'pending_error_logs';
  private readonly BATCH_THRESHOLD = 10;
  private readonly FLUSH_INTERVAL_MS = 30_000;
  private readonly ORG_ID = 1; // 默认 org,MatuX 自有学生端

  private readonly errorSubject = new Subject<FrontendErrorLog>();
  private buffer: FrontendErrorLog[] = [];

  constructor(private http: HttpClient) {
    this.initializeListeners();
    this.startAutoFlush();
    this.replayPending();
  }

  /**
   * 初始化全局错误监听
   */
  private initializeListeners(): void {
    if (typeof window === 'undefined') return;

    // JS 运行时错误
    fromEvent<ErrorEvent>(window, 'error')
      .pipe(take(1))
      .subscribe((event: ErrorEvent) => {
        const errObj = event.error as { message?: string; stack?: string } | undefined;
        this.logError({
          message: event.message ?? 'Unknown error',
          stack: errObj?.stack,
          url: event.filename ?? window.location.href,
          source: 'window.error',
        });
      });

    // Promise 未捕获
    fromEvent<PromiseRejectionEvent>(window, 'unhandledrejection')
      .pipe(take(1))
      .subscribe((event: PromiseRejectionEvent) => {
        const reason = event.reason as Error | string | undefined;
        const isError = reason instanceof Error;
        this.logError({
          message: (isError ? reason.message : String(reason)) ?? 'Unknown rejection',
          stack: isError ? reason.stack : undefined,
          url: window.location.href,
          source: 'unhandledrejection',
        });
      });
  }

  /**
   * 业务代码手动上报
   */
  logError(
    error: Partial<FrontendErrorLog> & { message: string; source: FrontendErrorLog['source'] }
  ): void {
    const entry: FrontendErrorLog = {
      message: error.message,
      stack: error.stack,
      url: error.url ?? (typeof window !== 'undefined' ? window.location.href : 'unknown'),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown',
      timestamp: new Date().toISOString(),
      source: error.source,
    };

    // 开发模式仅 console,生产模式进入上报队列
    if (isDevMode()) {
      console.error('[ErrorLogger]', entry);
    } else {
      this.errorSubject.next(entry);
      this.buffer.push(entry);
      if (this.buffer.length >= this.BATCH_THRESHOLD) {
        this.flush();
      }
    }
  }

  /**
   * 启动定时上报 (30 秒)
   */
  private startAutoFlush(): void {
    merge(this.errorSubject, timer(0, this.FLUSH_INTERVAL_MS))
      .pipe(auditTime(this.FLUSH_INTERVAL_MS))
      .subscribe(() => this.flush());
  }

  /**
   * 上报到后端
   */
  private flush(): void {
    if (this.buffer.length === 0) return;

    const payload = [...this.buffer];
    this.buffer = [];

    const url = `${environment.apiUrl ?? 'http://localhost:8002'}/api/v1/org/${this.ORG_ID}/logs/error`;
    this.http
      .post(url, { logs: payload })
      .pipe(
        catchError((err) => {
          // 上报失败 → 暂存到 localStorage,下次启动重试
          this.persistPending(payload);
          console.warn('[ErrorLogger] 上报失败,本地暂存', err);
          return of(null);
        }),
        take(1)
      )
      .subscribe();
  }

  /**
   * 持久化失败日志到 localStorage
   */
  private persistPending(logs: FrontendErrorLog[]): void {
    try {
      const existing = JSON.parse(
        localStorage.getItem(this.STORAGE_KEY) ?? '[]'
      ) as FrontendErrorLog[];
      const merged = [...existing, ...logs].slice(-100); // 最多保留 100 条
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(merged));
    } catch {
      // localStorage 不可用,静默失败
    }
  }

  /**
   * 启动时重放已暂存的日志
   */
  private replayPending(): void {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (!raw) return;
      const logs = JSON.parse(raw) as FrontendErrorLog[];
      if (logs.length > 0) {
        this.buffer.push(...logs);
        localStorage.removeItem(this.STORAGE_KEY);
        // 触发一次上报
        setTimeout(() => this.flush(), 5_000);
      }
    } catch {
      // 损坏的存储直接清掉
      localStorage.removeItem(this.STORAGE_KEY);
    }
  }
}
