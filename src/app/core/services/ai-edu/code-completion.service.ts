import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { shareReplay, switchMap } from 'rxjs/operators';

import { environment } from '../../../../environments/environment';
import { unifiedHttpClient } from '../unified-http-client';

// DeepSeek模型标识
export const DEEPSEEK_PROVIDER = 'deepseek';
export const DEEPSEEK_MODEL = 'deepseek-chat';

// 数据模型接口
export interface CompletionSuggestion {
  text: string;
  confidence: number;
  relevanceScore: number;
  languageFeatures: string[];
  metadata: Record<string, unknown>;
}

export interface CompletionResponse {
  suggestions: CompletionSuggestion[];
  processingTime: number;
  tokensUsed: number;
  modelUsed: string;
  cacheHit: boolean;
  contextAnalyzed: boolean;
}

interface CachedResponse {
  response: CompletionResponse;
  timestamp: number;
}

export interface CompletionRequest {
  prefix: string;
  context: string[];
  language?: string;
  provider?: string;
  maxSuggestions?: number;
  temperature?: number;
  userId?: number;
}

// ========== DeepSeek 增强功能 ==========

/**
 * DeepSeek 代码解释请求
 */
export interface DeepSeekExplainRequest {
  code: string;
  language?: string;
  detailLevel?: 'brief' | 'normal' | 'detailed';
  userId?: number;
}

/**
 * DeepSeek 代码解释响应
 */
export interface DeepSeekExplainResponse {
  explanation: string;
  codeElements: CodeElement[];
  complexity: CodeComplexity;
  suggestions: string[];
  relatedConcepts: string[];
  modelUsed: string;
  processingTime: number;
}

/**
 * 代码元素
 */
export interface CodeElement {
  name: string;
  type: 'function' | 'class' | 'variable' | 'import' | 'keyword';
  description: string;
  lineStart: number;
  lineEnd: number;
}

/**
 * 代码复杂度
 */
export interface CodeComplexity {
  score: number;
  level: 'low' | 'medium' | 'high';
  factors: string[];
}

/**
 * DeepSeek 代码优化请求
 */
export interface DeepSeekOptimizeRequest {
  code: string;
  language?: string;
  optimizationGoals?: ('performance' | 'readability' | 'security' | 'best-practice')[];
  userId?: number;
}

/**
 * DeepSeek 代码优化响应
 */
export interface DeepSeekOptimizeResponse {
  originalCode: string;
  optimizedCode: string;
  improvements: OptimizationImprovement[];
  explanation: string;
  warnings: string[];
  modelUsed: string;
  processingTime: number;
}

/**
 * 优化改进项
 */
export interface OptimizationImprovement {
  type: 'performance' | 'readability' | 'security' | 'best-practice';
  description: string;
  originalSnippet: string;
  optimizedSnippet: string;
  impact: 'high' | 'medium' | 'low';
}

/**
 * DeepSeek 智能辅导请求
 */
export interface DeepSeekTutorRequest {
  code?: string;
  question: string;
  context?: string[];
  language?: string;
  userId?: number;
}

/**
 * DeepSeek 智能辅导响应
 */
export interface DeepSeekTutorResponse {
  answer: string;
  codeExamples: CodeExample[];
  relatedTopics: string[];
  nextSteps: string[];
  modelUsed: string;
  processingTime: number;
}

/**
 * 代码示例
 */
export interface CodeExample {
  title: string;
  code: string;
  language: string;
  explanation: string;
}

export interface ContextAnalysisResult {
  scopeLevel: string;
  syntaxContext: string;
  variableDeclarations: string[];
  functionSignatures: string[];
  importedModules: string[];
  currentIndentation: number;
}

export interface UserPattern {
  codeSnippet: string;
  context: string;
  usageCount: number;
  lastUsed: string;
}

@Injectable({
  providedIn: 'root',
})
export class CodeCompletionService {
  private readonly API_BASE_URL = `${environment.apiUrl}/api/v1/completion`;
  private readonly AI_TUTOR_BASE_URL = `${environment.apiUrl}/api/v1/ai-tutor`;
  private cache = new Map<string, CachedResponse>();
  private cacheTimeout = 300000; // 5分钟缓存

  // DeepSeek 配置
  private readonly DEEPSEEK_CONFIG = {
    provider: DEEPSEEK_PROVIDER,
    model: DEEPSEEK_MODEL,
    temperature: 0.7,
    maxTokens: 2000,
  };

  // WebSocket连接相关
  private websocket: WebSocket | null = null;
  private websocketSubject = new BehaviorSubject<unknown>(null);
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseDelay = 1000;
  private maxDelay = 30000;
  private jitterMax = 1000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingIntervalMs = 30000;
  private pongTimeoutMs = 10000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private pongTimeoutTimer: ReturnType<typeof setInterval> | null = null;
  private lastPongTime: number = 0;

  constructor() {}

  /**
   * 获取代码补全建议
   */
  getSuggestions(request: CompletionRequest): Observable<CompletionResponse> {
    const cacheKey = this.generateCacheKey(request);

    // 检查缓存
    const cachedData = this.cache.get(cacheKey);
    if (cachedData) {
      if (Date.now() - cachedData.timestamp < this.cacheTimeout) {
        return of(cachedData.response);
      } else {
        this.cache.delete(cacheKey);
      }
    }

    return of(null).pipe(
      // 使用Promise包装异步操作
      switchMap(async () => {
        try {
          const response = await unifiedHttpClient.post<CompletionResponse>(
            `${this.API_BASE_URL}/suggest`,
            request
          );

          // 缓存响应
          this.cache.set(cacheKey, {
            response: response.data,
            timestamp: Date.now(),
          });

          return response.data;
        } catch (error) {
          return {
            suggestions: [],
            processingTime: 0,
            tokensUsed: 0,
            modelUsed: 'error',
            cacheHit: false,
            contextAnalyzed: false,
          };
        }
      }),
      shareReplay(1)
    );
  }

  /**
   * 分析代码上下文
   */
  analyzeContext(
    codeLines: string[],
    cursorPosition: number,
    language: string = 'python'
  ): Observable<ContextAnalysisResult> {
    const params = {
      code_lines: JSON.stringify(codeLines),
      cursor_position: cursorPosition.toString(),
      language,
    };

    return of(null).pipe(
      switchMap(async () => {
        try {
          const response = await unifiedHttpClient.post<ContextAnalysisResult>(
            `${this.API_BASE_URL}/analyze-context`,
            params
          );
          return response.data;
        } catch (error) {
          return {
            scopeLevel: 'unknown',
            syntaxContext: 'unknown',
            variableDeclarations: [],
            functionSignatures: [],
            importedModules: [],
            currentIndentation: 0,
          };
        }
      })
    );
  }

  /**
   * 获取用户代码模式
   */
  getUserPatterns(language: string = 'python', limit: number = 10): Observable<UserPattern[]> {
    return of(null).pipe(
      switchMap(async () => {
        try {
          const url = `${this.API_BASE_URL}/user-patterns?language=${language}&limit=${limit}`;
          const response = await unifiedHttpClient.get<{ patterns: UserPattern[] }>(url);
          return response.data.patterns;
        } catch (error) {
          return [];
        }
      })
    );
  }

  /**
   * 建立WebSocket连接
   */
  connectWebSocket(): Observable<unknown> {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      return this.websocketSubject.asObservable();
    }

    const wsUrl = `${environment.wsUrl}/api/v1/completion/ws`;
    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = (event) => {
      this.reconnectAttempts = 0;
      this.lastPongTime = Date.now();
      this.websocketSubject.next({ type: 'connected', event });
      this.startPingInterval();
      this.startPongTimeout();
    };

    this.websocket.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data as string) as Record<string, unknown>;

        if (message['type'] === 'pong') {
          this.lastPongTime = Date.now();
        }

        this.websocketSubject.next(message);
      } catch {
        /* 忽略 WebSocket 消息解析错误 */
      }
    };

    this.websocket.onclose = (event) => {
      this.websocketSubject.next({ type: 'disconnected', event });
      this.stopPingInterval();
      this.stopPongTimeout();

      // 自动重连（code 1000=正常关闭不重连）
      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.websocket.onerror = (error) => {
      this.websocketSubject.next({ type: 'error', error });
    };

    return this.websocketSubject.asObservable();
  }

  /**
   * 通过WebSocket发送补全请求
   */
  sendCompletionRequest(request: CompletionRequest): void {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      return;
    }

    const message = {
      type: 'completion_request',
      data: request,
    };

    this.websocket.send(JSON.stringify(message));
  }

  /**
   * 通过WebSocket更新上下文
   */
  updateContext(codeLines: string[], language: string = 'python'): void {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      return;
    }

    const message = {
      type: 'context_update',
      data: {
        code_lines: codeLines,
        language,
      },
    };

    this.websocket.send(JSON.stringify(message));
  }

  /**
   * 断开WebSocket连接
   */
  disconnectWebSocket(): void {
    this.stopPingInterval();
    this.stopPongTimeout();
    this.clearReconnectTimer();

    if (this.websocket) {
      this.websocket.close(1000, 'User disconnected');
      this.websocket = null;
    }

    this.reconnectAttempts = 0;
  }

  // ========== WebSocket 重连与心跳 ==========

  /**
   * 计算指数退避延迟（带抖动）
   */
  private calculateBackoff(attempt: number): number {
    const exponentialDelay = Math.min(this.maxDelay, this.baseDelay * Math.pow(2, attempt - 1));
    const jitter = Math.random() * this.jitterMax;
    return Math.floor(exponentialDelay + jitter);
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.calculateBackoff(this.reconnectAttempts);

    this.clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.connectWebSocket();
    }, delay);
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * 启动心跳定时器
   */
  private startPingInterval(): void {
    this.stopPingInterval();

    this.pingInterval = setInterval(() => {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send(JSON.stringify({ type: 'ping' }));
      }
    }, this.pingIntervalMs);
  }

  /**
   * 停止心跳定时器
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * 启动 pong 超时检测
   */
  private startPongTimeout(): void {
    this.stopPongTimeout();

    this.pongTimeoutTimer = setInterval(
      () => {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
          return;
        }

        const elapsed = Date.now() - this.lastPongTime;
        if (elapsed > this.pongTimeoutMs) {
          this.forceReconnect();
        }
      },
      Math.min(this.pongTimeoutMs, 5000)
    );
  }

  /**
   * 停止 pong 超时检测
   */
  private stopPongTimeout(): void {
    if (this.pongTimeoutTimer) {
      clearInterval(this.pongTimeoutTimer);
      this.pongTimeoutTimer = null;
    }
  }

  /**
   * 强制重连
   */
  private forceReconnect(): void {
    if (this.websocket) {
      this.websocket.onclose = null;
      this.websocket.close(4001, 'Heartbeat timeout');
      this.websocket = null;
    }

    this.stopPingInterval();
    this.stopPongTimeout();

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }

  /**
   * 清理过期缓存
   */
  cleanupCache(): void {
    const now = Date.now();
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.cacheTimeout) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 获取服务健康状态
   */
  async getHealthStatus(): Promise<Record<string, unknown>> {
    try {
      const response = await unifiedHttpClient.get(`${this.API_BASE_URL}/health`);
      return response.data as Record<string, unknown>;
    } catch (error) {
      const err = error as Error;
      return { status: 'unhealthy', error: err.message };
    }
  }

  /**
   * 预取常用的补全建议
   */
  prefetchCompletions(commonPrefixes: string[], language: string = 'python'): void {
    commonPrefixes.forEach((prefix) => {
      const request: CompletionRequest = {
        prefix,
        context: [],
        language,
        maxSuggestions: 3,
      };

      // 不等待响应，只是预热缓存
      this.getSuggestions(request).subscribe();
    });
  }

  /**
   * 根据置信度过滤建议
   */
  filterSuggestions(
    suggestions: CompletionSuggestion[],
    minConfidence: number = 0.7
  ): CompletionSuggestion[] {
    return suggestions.filter((suggestion) => suggestion.confidence >= minConfidence);
  }

  /**
   * 对建议进行排序
   */
  sortSuggestions(suggestions: CompletionSuggestion[]): CompletionSuggestion[] {
    return [...suggestions].sort((a, b) => {
      // 主要按相关性分数排序
      if (b.relevanceScore !== a.relevanceScore) {
        return b.relevanceScore - a.relevanceScore;
      }
      // 次要按置信度排序
      return b.confidence - a.confidence;
    });
  }

  /**
   * 生成缓存键
   */
  private generateCacheKey(request: CompletionRequest): string {
    const keyData = {
      prefix: request.prefix,
      language: request.language,
      provider: request.provider,
      contextHash: this.hashString(request.context.join('\n')),
    };
    return btoa(JSON.stringify(keyData));
  }

  /**
   * 简单的字符串哈希函数
   */
  private hashString(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // 转换为32位整数
    }
    return hash.toString();
  }

  /**
   * 获取认证令牌
   */
  private getAuthToken(): string {
    return localStorage.getItem('access_token') ?? '';
  }

  // ========== DeepSeek 增强功能实现 ==========

  /**
   * 使用 DeepSeek 解释代码
   * 提供代码的详细解释、元素分析、复杂度评估
   */
  explainCodeWithDeepSeek(request: DeepSeekExplainRequest): Observable<DeepSeekExplainResponse> {
    return of(null).pipe(
      switchMap(async () => {
        try {
          const response = await unifiedHttpClient.post<DeepSeekExplainResponse>(
            `${this.AI_TUTOR_BASE_URL}/explain`,
            {
              ...request,
              provider: DEEPSEEK_PROVIDER,
              model: DEEPSEEK_MODEL,
            }
          );
          return response.data;
        } catch (error) {
          console.error('DeepSeek代码解释失败:', error);
          return this.getDefaultExplainResponse();
        }
      }),
      shareReplay(1)
    );
  }

  /**
   * 使用 DeepSeek 优化代码
   * 提供性能、可读性、安全性等方面的优化建议
   */
  optimizeCodeWithDeepSeek(request: DeepSeekOptimizeRequest): Observable<DeepSeekOptimizeResponse> {
    return of(null).pipe(
      switchMap(async () => {
        try {
          const response = await unifiedHttpClient.post<DeepSeekOptimizeResponse>(
            `${this.AI_TUTOR_BASE_URL}/optimize`,
            {
              ...request,
              provider: DEEPSEEK_PROVIDER,
              model: DEEPSEEK_MODEL,
            }
          );
          return response.data;
        } catch (error) {
          console.error('DeepSeek代码优化失败:', error);
          return this.getDefaultOptimizeResponse(request.code);
        }
      }),
      shareReplay(1)
    );
  }

  /**
   * 使用 DeepSeek 进行智能编程辅导
   * 回答编程问题，提供代码示例和解释
   */
  askDeepSeekTutor(request: DeepSeekTutorRequest): Observable<DeepSeekTutorResponse> {
    return of(null).pipe(
      switchMap(async () => {
        try {
          const response = await unifiedHttpClient.post<DeepSeekTutorResponse>(
            `${this.AI_TUTOR_BASE_URL}/tutor`,
            {
              ...request,
              provider: DEEPSEEK_PROVIDER,
              model: DEEPSEEK_MODEL,
            }
          );
          return response.data;
        } catch (error) {
          console.error('DeepSeek智能辅导失败:', error);
          return this.getDefaultTutorResponse(request.question);
        }
      }),
      shareReplay(1)
    );
  }

  /**
   * 使用 DeepSeek 进行实时代码补全（流式）
   * 支持流式输出，提供更快的反馈
   */
  streamCompletionWithDeepSeek(
    prefix: string,
    context: string[],
    language: string = 'python'
  ): Observable<string> {
    return new Observable((observer) => {
      const request: CompletionRequest = {
        prefix,
        context,
        language,
        provider: DEEPSEEK_PROVIDER,
        maxSuggestions: 3,
        temperature: this.DEEPSEEK_CONFIG.temperature,
      };

      this.getSuggestions(request).subscribe({
        next: (response) => {
          if (response.suggestions.length > 0) {
            observer.next(response.suggestions[0].text);
          }
          observer.complete();
        },
        error: (error) => observer.error(error),
      });
    });
  }

  /**
   * 设置 DeepSeek 为默认补全提供商
   */
  setDeepSeekAsDefaultProvider(): void {
    // 更新请求默认provider
    this.DEEPSEEK_CONFIG.provider = DEEPSEEK_PROVIDER;
  }

  /**
   * 获取 DeepSeek 配置信息
   */
  getDeepSeekConfig(): { provider: string; model: string } {
    return {
      provider: this.DEEPSEEK_CONFIG.provider,
      model: this.DEEPSEEK_CONFIG.model,
    };
  }

  // ========== 默认响应 ==========

  private getDefaultExplainResponse(): DeepSeekExplainResponse {
    return {
      explanation: '抱歉，无法获取代码解释。请确保后端服务正常运行。',
      codeElements: [],
      complexity: { score: 0, level: 'low', factors: [] },
      suggestions: [],
      relatedConcepts: [],
      modelUsed: 'error',
      processingTime: 0,
    };
  }

  private getDefaultOptimizeResponse(code: string): DeepSeekOptimizeResponse {
    return {
      originalCode: code,
      optimizedCode: code,
      improvements: [],
      explanation: '抱歉，无法获取代码优化建议。请确保后端服务正常运行。',
      warnings: [],
      modelUsed: 'error',
      processingTime: 0,
    };
  }

  private getDefaultTutorResponse(question: string): DeepSeekTutorResponse {
    return {
      answer: '抱歉，无法获取智能辅导。请确保后端服务正常运行。',
      codeExamples: [],
      relatedTopics: [],
      nextSteps: [],
      modelUsed: 'error',
      processingTime: 0,
    };
  }
}

// 缓存条目接口（已导出供其他模块使用）
export interface CacheEntry {
  response: CompletionResponse;
  timestamp: number;
}
