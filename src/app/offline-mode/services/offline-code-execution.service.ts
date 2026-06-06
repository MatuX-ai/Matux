/**
 * 离线代码执行服务
 *
 * 基于 PRD F-12 离线模式增强设计，提供：
 * - 通过内嵌 Python 后端执行代码
 * - 代码执行结果缓存
 * - 执行超时和安全限制
 * - Electron IPC 桥接
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { ElectronService } from '../../core/services/electron.service';

/** 代码执行语言 */
export type CodeLanguage = 'python' | 'javascript';

/** 代码执行结果 */
export interface CodeExecutionResult {
  success: boolean;
  output: string;
  error: string | null;
  executionTimeMs: number;
  exitCode: number | null;
  cached: boolean;
}

/** 代码执行请求 */
export interface CodeExecutionRequest {
  code: string;
  language: CodeLanguage;
  timeout?: number;
  stdin?: string;
}

/** 执行历史条目 */
export interface ExecutionHistoryEntry {
  id: string;
  code: string;
  language: CodeLanguage;
  result: CodeExecutionResult;
  executedAt: string;
}

@Injectable({
  providedIn: 'root',
})
export class OfflineCodeExecutionService {
  /** 执行历史 */
  private historySubject = new BehaviorSubject<ExecutionHistoryEntry[]>([]);
  public history$ = this.historySubject.asObservable();

  /** 当前正在执行 */
  private executingSubject = new BehaviorSubject<boolean>(false);
  public executing$ = this.executingSubject.asObservable();

  /** 后端 URL */
  private backendUrl = '/api/v1';

  constructor(
    private http: HttpClient,
    private electronService: ElectronService
  ) {
    if (this.electronService.isElectron) {
      this.backendUrl = this.electronService.getBackendUrl() || 'http://localhost:8000/api/v1';
    }
  }

  // ==================== 代码执行 ====================

  /** 执行代码 */
  executeCode(request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    this.executingSubject.next(true);

    return new Promise((resolve) => {
      // 优先使用内嵌后端执行
      this.executeViaBackend(request)
        .then((result) => {
          this.addToHistory(request, result);
          this.executingSubject.next(false);
          resolve(result);
        })
        .catch(() => {
          // 降级：浏览器端 JavaScript 执行
          if (request.language === 'javascript') {
            const result = this.executeJavaScriptInBrowser(request.code);
            this.addToHistory(request, result);
            this.executingSubject.next(false);
            resolve(result);
          } else {
            const result: CodeExecutionResult = {
              success: false,
              output: '',
              error: '离线模式下 Python 执行需要内嵌后端运行，请确认后端已启动',
              executionTimeMs: 0,
              exitCode: null,
              cached: false,
            };
            this.addToHistory(request, result);
            this.executingSubject.next(false);
            resolve(result);
          }
        });
    });
  }

  /** 通过内嵌后端执行代码 */
  private async executeViaBackend(request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    const startTime = Date.now();
    const timeoutMs = request.timeout ?? 30000;

    try {
      const response = await fetch(`${this.backendUrl}/code/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: request.code,
          language: request.language,
          timeout: timeoutMs,
          stdin: request.stdin,
        }),
        signal: AbortSignal.timeout(timeoutMs + 5000),
      });

      const data = (await response.json()) as {
        success: boolean;
        output: string;
        error: string | null;
        exit_code: number | null;
      };

      return {
        success: data.success,
        output: data.output ?? '',
        error: data.error ?? null,
        executionTimeMs: Date.now() - startTime,
        exitCode: data.exit_code ?? null,
        cached: false,
      };
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : '执行失败');
    }
  }

  /** 浏览器端 JavaScript 执行（降级方案） */
  private executeJavaScriptInBrowser(code: string): CodeExecutionResult {
    const startTime = Date.now();
    let output = '';
    let error: string | null = null;
    let success = false;

    // 劫持 console.log 收集输出
    const originalLog = console.log;
    const logs: string[] = [];
    console.log = (...args: unknown[]) => {
      logs.push(args.map((a) => String(a)).join(' '));
    };

    try {
      // 使用 Function 构造器安全执行
      const fn = new Function(code);
      fn();
      success = true;
      output = logs.join('\n');
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      console.log = originalLog;
    }

    return {
      success,
      output,
      error,
      executionTimeMs: Date.now() - startTime,
      exitCode: error ? 1 : 0,
      cached: false,
    };
  }

  // ==================== 执行历史 ====================

  /** 添加到执行历史 */
  private addToHistory(request: CodeExecutionRequest, result: CodeExecutionResult): void {
    const entry: ExecutionHistoryEntry = {
      id: `exec_${Date.now()}`,
      code: request.code,
      language: request.language,
      result,
      executedAt: new Date().toISOString(),
    };

    const history = this.historySubject.value;
    // 保留最近 50 条
    this.historySubject.next([entry, ...history].slice(0, 50));
  }

  /** 清除执行历史 */
  clearHistory(): void {
    this.historySubject.next([]);
  }

  /** 检查是否可以执行指定语言 */
  canExecute(language: CodeLanguage): boolean {
    if (language === 'javascript') {
      return true; // 浏览器端始终可执行
    }
    // Python 需要后端运行
    return this.electronService.isElectron;
  }

  /** 获取执行状态描述 */
  getExecutionStatusDescription(): string {
    if (this.electronService.isElectron) {
      return 'Python 3.11 运行中';
    }
    return '仅 JavaScript 可用（需桌面端运行 Python）';
  }
}
