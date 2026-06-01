/**
 * 向量知识库检索服务 (RAG Pipeline)
 *
 * 基于PRD F-08-AI.3 个性化知识库设计，提供：
 * - 分层知识库检索（全局/阶段/个人）
 * - RAG 上下文注入
 * - 与 AITeacherService 集成
 *
 * 后端API: /api/v1/knowledge-base
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

/** 知识层级 */
export type KnowledgeLayer = 'global' | 'stage' | 'personal';

/** 学习阶段 */
export type LearningStage = 'L1' | 'L2' | 'L3' | 'L4';

/** 知识检索结果条目 */
export interface KnowledgeSearchResult {
  item_id: string;
  content: string;
  category: string;
  layer: KnowledgeLayer;
  difficulty: string;
  tags: string[];
  metadata: Record<string, unknown>;
  relevance_score: number;
}

/** RAG 检索结果 */
export interface RAGResult {
  items: KnowledgeSearchResult[];
  context: string;
  sources: string[];
  total_score: number;
}

/** 知识库统计 */
export interface KnowledgeBaseStats {
  total_items: number;
  layer_counts: Record<string, number>;
  category_counts: Record<string, number>;
  index_size: number;
  embedding_dimension: number;
  has_embedding_model: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class VectorKnowledgeService {
  private readonly API_BASE = '/api/v1/knowledge-base';

  /** 知识库统计 */
  private statsSubject = new BehaviorSubject<KnowledgeBaseStats | null>(null);
  public stats$ = this.statsSubject.asObservable();

  /** 最近检索结果缓存 */
  private lastRagResultSubject = new BehaviorSubject<RAGResult | null>(null);
  public lastRagResult$ = this.lastRagResultSubject.asObservable();

  constructor(private http: HttpClient) {}

  // ==================== 知识检索 ====================

  /** 搜索知识库 */
  search(
    query: string,
    userId?: string,
    topK: number = 5,
    layerFilter?: KnowledgeLayer,
    stage?: LearningStage,
  ): Observable<{ results: KnowledgeSearchResult[]; total: number }> {
    return this.http.post<{ results: KnowledgeSearchResult[]; total: number }>(
      `${this.API_BASE}/search`,
      { query, user_id: userId, top_k: topK, layer_filter: layerFilter, stage },
    ).pipe(
      catchError(() => of({ results: this.createMockSearchResults(query), total: 0 })),
    );
  }

  /** RAG 检索增强（PRD F-08-AI.3 核心方法） */
  ragRetrieve(
    query: string,
    userId: string,
    profileSeed?: string,
    stage?: LearningStage,
    topK: number = 3,
  ): Observable<RAGResult> {
    return this.http.post<RAGResult>(
      `${this.API_BASE}/rag`,
      { query, user_id: userId, profile_seed: profileSeed, stage, top_k: topK },
    ).pipe(
      tap((result) => this.lastRagResultSubject.next(result)),
      catchError(() => {
        const mockResult = this.createMockRAGResult(query);
        this.lastRagResultSubject.next(mockResult);
        return of(mockResult);
      }),
    );
  }

  // ==================== 知识管理 ====================

  /** 添加个人知识 */
  addPersonalKnowledge(
    userId: string,
    content: string,
    tags: string[] = [],
  ): Observable<{ success: boolean; item_id: string }> {
    return this.http.post<{ success: boolean; item_id: string }>(
      `${this.API_BASE}/knowledge/personal`,
      { user_id: userId, content, tags },
    ).pipe(
      catchError(() => of({ success: false, item_id: '' })),
    );
  }

  /** 添加知识 */
  addKnowledge(item: {
    item_id: string;
    content: string;
    category: string;
    layer: KnowledgeLayer;
    difficulty?: string;
    tags?: string[];
  }): Observable<{ success: boolean; item_id: string }> {
    return this.http.post<{ success: boolean; item_id: string }>(
      `${this.API_BASE}/knowledge`,
      item,
    ).pipe(
      catchError(() => of({ success: false, item_id: '' })),
    );
  }

  /** 获取知识库统计 */
  getStats(): Observable<KnowledgeBaseStats> {
    return this.http.get<KnowledgeBaseStats>(`${this.API_BASE}/stats`).pipe(
      tap((stats) => this.statsSubject.next(stats)),
      catchError(() => of(this.createMockStats())),
    );
  }

  // ==================== Mock 降级 ====================

  private createMockSearchResults(query: string): KnowledgeSearchResult[] {
    return [
      {
        item_id: 'g_python_loops',
        content: '循环结构：for 循环、while 循环、range() 函数、break/continue',
        category: 'programming',
        layer: 'global',
        difficulty: 'intermediate',
        tags: ['python', '循环'],
        metadata: {},
        relevance_score: 0.85,
      },
    ];
  }

  private createMockRAGResult(query: string): RAGResult {
    return {
      items: this.createMockSearchResults(query),
      context: '[全局知识库] 循环结构：for 循环、while 循环、range() 函数、break/continue',
      sources: ['g_python_loops'],
      total_score: 0.85,
    };
  }

  private createMockStats(): KnowledgeBaseStats {
    return {
      total_items: 16,
      layer_counts: { global: 9, stage: 5, personal: 2 },
      category_counts: { programming: 10, stem: 2, methodology: 1, ai: 1 },
      index_size: 16,
      embedding_dimension: 384,
      has_embedding_model: false,
    };
  }
}
