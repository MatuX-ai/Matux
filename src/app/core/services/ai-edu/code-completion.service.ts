import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { shareReplay, switchMap } from 'rxjs/operators';

import { environment } from '../../../../environments/environment';
import { unifiedHttpClient } from '../unified-http-client';

// 数据模型接口
export interface CompletionSuggestion {
  text: string;
  confidence: number;
  relevanceScore: number;
  languageFeatures: string[];
  metadata: any;
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
  private cache = new Map<string, CachedResponse>();
  private cacheTimeout = 300000; // 5分钟缓存

  // WebSocket连接相关
  private websocket: WebSocket | null = null;
  private websocketSubject = new BehaviorSubject<any>(null);
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor() {}

  /**
   * 获取代码补全建议
   */
  getSuggestions(request: CompletionRequest): Observable<CompletionResponse> {
    const cacheKey = this.generateCacheKey(request);

    // 检查缓存
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return of(cached.response);
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
  connectWebSocket(): Observable<any> {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      return this.websocketSubject.asObservable();
    }

    const wsUrl = `${environment.wsUrl}/api/v1/completion/ws`;
    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = (event) => {
      this.reconnectAttempts = 0;
      this.websocketSubject.next({ type: 'connected', event });
    };

    this.websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.websocketSubject.next(message);
      } catch (error) {}
    };

    this.websocket.onclose = (event) => {
      this.websocketSubject.next({ type: 'disconnected', event });

      // 自动重连
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;

          this.connectWebSocket();
        }, 3000);
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
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
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
  async getHealthStatus(): Promise<any> {
    try {
      const response = await unifiedHttpClient.get(`${this.API_BASE_URL}/health`);
      return response.data;
    } catch (error: any) {
      return { status: 'unhealthy', error: error.message };
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
    return localStorage.getItem('access_token') || '';
  }
}

// 缓存条目接口
interface CacheEntry {
  response: CompletionResponse;
  timestamp: number;
}
