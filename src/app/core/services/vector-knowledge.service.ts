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
    stage?: LearningStage
  ): Observable<{ results: KnowledgeSearchResult[]; total: number }> {
    return this.http
      .post<{
        results: KnowledgeSearchResult[];
        total: number;
      }>(`${this.API_BASE}/search`, {
        query,
        user_id: userId,
        top_k: topK,
        layer_filter: layerFilter,
        stage,
      })
      .pipe(
        catchError(() => {
          const results = this.createMockSearchResults(query, layerFilter, stage, topK);
          return of({ results, total: results.length });
        })
      );
  }

  /** RAG 检索增强（PRD F-08-AI.3 核心方法） */
  ragRetrieve(
    query: string,
    userId: string,
    profileSeed?: string,
    stage?: LearningStage,
    topK: number = 3
  ): Observable<RAGResult> {
    return this.http
      .post<RAGResult>(`${this.API_BASE}/rag`, {
        query,
        user_id: userId,
        profile_seed: profileSeed,
        stage,
        top_k: topK,
      })
      .pipe(
        tap((result) => this.lastRagResultSubject.next(result)),
        catchError(() => {
          const mockResult = this.createMockRAGResult(query, stage, topK);
          this.lastRagResultSubject.next(mockResult);
          return of(mockResult);
        })
      );
  }

  // ==================== 知识管理 ====================

  /** 添加个人知识 */
  addPersonalKnowledge(
    userId: string,
    content: string,
    tags: string[] = []
  ): Observable<{ success: boolean; item_id: string }> {
    return this.http
      .post<{
        success: boolean;
        item_id: string;
      }>(`${this.API_BASE}/knowledge/personal`, { user_id: userId, content, tags })
      .pipe(catchError(() => of({ success: false, item_id: '' })));
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
    return this.http
      .post<{ success: boolean; item_id: string }>(`${this.API_BASE}/knowledge`, item)
      .pipe(catchError(() => of({ success: false, item_id: '' })));
  }

  /** 获取知识库统计 */
  getStats(): Observable<KnowledgeBaseStats> {
    return this.http.get<KnowledgeBaseStats>(`${this.API_BASE}/stats`).pipe(
      tap((stats) => this.statsSubject.next(stats)),
      catchError(() => of(this.createMockStats()))
    );
  }

  /** 获取指定阶段的知识项 */
  getKnowledgeForStage(stage: LearningStage): Observable<KnowledgeSearchResult[]> {
    return this.http
      .get<KnowledgeSearchResult[]>(`${this.API_BASE}/stage/${stage}`)
      .pipe(catchError(() => of(this.getStageKnowledge(stage))));
  }

  // ==================== Mock 降级（三层知识库）====================

  /** 全局知识库（Layer 1：所有学生共享的通用编程/STEM概念） */
  private readonly GLOBAL_KNOWLEDGE: KnowledgeSearchResult[] = [
    {
      item_id: 'g_python_variables',
      content:
        '变量与数据类型：Python 中的 int、float、str、bool 四种基本类型，变量命名规则（字母/下划线开头，区分大小写）',
      category: 'programming',
      layer: 'global',
      difficulty: 'beginner',
      tags: ['python', '变量', '数据类型'],
      metadata: {},
      relevance_score: 0.95,
    },
    {
      item_id: 'g_python_conditions',
      content:
        '条件判断：if/elif/else 语法，比较运算符（==, !=, <, >, <=, >=），逻辑运算符（and, or, not）',
      category: 'programming',
      layer: 'global',
      difficulty: 'beginner',
      tags: ['python', '条件判断'],
      metadata: {},
      relevance_score: 0.92,
    },
    {
      item_id: 'g_python_loops',
      content:
        '循环结构：for 循环（for item in iterable）、while 循环、range() 函数、break/continue 控制流、循环嵌套',
      category: 'programming',
      layer: 'global',
      difficulty: 'intermediate',
      tags: ['python', '循环', 'for', 'while'],
      metadata: {},
      relevance_score: 0.88,
    },
    {
      item_id: 'g_python_functions',
      content:
        '函数定义与调用：def 关键字、参数（位置/默认/关键字/*args/**kwargs）、返回值、作用域规则（LEGB）',
      category: 'programming',
      layer: 'global',
      difficulty: 'intermediate',
      tags: ['python', '函数', '作用域'],
      metadata: {},
      relevance_score: 0.85,
    },
    {
      item_id: 'g_python_lists',
      content:
        '列表与元组：list 创建/索引/切片/方法（append, remove, sort）、tuple 不可变性、列表推导式',
      category: 'programming',
      layer: 'global',
      difficulty: 'beginner',
      tags: ['python', '列表', '元组', '数据结构'],
      metadata: {},
      relevance_score: 0.9,
    },
    {
      item_id: 'g_stem_circuit',
      content:
        '电路基础：电压(V)、电流(I)、电阻(R) 的欧姆定律 V=IR，串联/并联电路特点，LED、电阻、开关的基本用法',
      category: 'stem',
      layer: 'global',
      difficulty: 'beginner',
      tags: ['stem', '电路', '欧姆定律'],
      metadata: {},
      relevance_score: 0.82,
    },
    {
      item_id: 'g_stem_sensors',
      content:
        '传感器原理：光敏电阻、温度传感器(DHT11)、超声波测距(HC-SR04)、红外传感器的工作原理与Arduino接线方式',
      category: 'stem',
      layer: 'global',
      difficulty: 'intermediate',
      tags: ['stem', '传感器', 'Arduino'],
      metadata: {},
      relevance_score: 0.78,
    },
    {
      item_id: 'g_methodology_debug',
      content:
        '调试方法论：print 调试法、二分定位法、阅读错误栈（Traceback）、单元测试基础、代码审查',
      category: 'methodology',
      layer: 'global',
      difficulty: 'intermediate',
      tags: ['方法论', '调试', '错误处理'],
      metadata: {},
      relevance_score: 0.75,
    },
    {
      item_id: 'g_ai_ml_basics',
      content:
        'AI 基础知识：机器学习三要素（数据、模型、算法），监督学习/无监督学习/强化学习区分，训练/验证/测试流程',
      category: 'ai',
      layer: 'global',
      difficulty: 'advanced',
      tags: ['AI', '机器学习', '深度学习'],
      metadata: {},
      relevance_score: 0.7,
    },
  ];

  /** 阶段知识库（Layer 2：按年级/难度分层） */
  // eslint-disable-next-line max-lines-per-function
  private getStageKnowledge(stage?: LearningStage): KnowledgeSearchResult[] {
    const stageBase: KnowledgeSearchResult[] = [
      {
        item_id: 's_l1_blockly',
        content: 'L1 Blockly 编程入门：积木块拼接、顺序执行、循环积木、条件积木、事件驱动',
        category: 'programming',
        layer: 'stage',
        difficulty: 'beginner',
        tags: ['blockly', '编程入门', '可视化'],
        metadata: { stage: 'L1' },
        relevance_score: 0.9,
      },
      {
        item_id: 's_l2_python_transition',
        content:
          'L2 Blockly → Python 过渡：将积木逻辑翻译为 Python 代码，认识缩进、关键字、基础语法',
        category: 'programming',
        layer: 'stage',
        difficulty: 'beginner',
        tags: ['blockly', 'python', '过渡'],
        metadata: { stage: 'L2' },
        relevance_score: 0.88,
      },
      {
        item_id: 's_l3_python_advanced',
        content:
          'L3 Python 进阶：文件读写、异常处理、模块导入、函数式编程（map/filter/lambda）、面向对象入门',
        category: 'programming',
        layer: 'stage',
        difficulty: 'intermediate',
        tags: ['python', '进阶'],
        metadata: { stage: 'L3' },
        relevance_score: 0.85,
      },
      {
        item_id: 's_l3_data_structures',
        content:
          'L3 数据结构：栈(Stack)、队列(Queue)、链表(LinkedList) 的概念与 Python 实现，时间/空间复杂度入门',
        category: 'programming',
        layer: 'stage',
        difficulty: 'intermediate',
        tags: ['数据结构', '算法'],
        metadata: { stage: 'L3' },
        relevance_score: 0.82,
      },
      {
        item_id: 's_l4_algorithm',
        content:
          'L4 算法基础：排序（冒泡/快排/归并）、搜索（二分/DFS/BFS）、动态规划入门、贪心算法',
        category: 'programming',
        layer: 'stage',
        difficulty: 'advanced',
        tags: ['算法', '竞赛'],
        metadata: { stage: 'L4' },
        relevance_score: 0.8,
      },
      {
        item_id: 's_l4_ai_project',
        content: 'L4 AI 实战项目：使用 Python 实现简单的图像分类、文本情感分析、聊天机器人',
        category: 'ai',
        layer: 'stage',
        difficulty: 'advanced',
        tags: ['AI', '项目实战'],
        metadata: { stage: 'L4' },
        relevance_score: 0.78,
      },
    ];

    if (!stage) return stageBase;
    return stageBase.filter((item) => {
      const meta = item.metadata as Record<string, string>;
      const itemStage = meta['stage'];
      if (!itemStage) return false;
      const stageOrder: string[] = ['L1', 'L2', 'L3', 'L4'];
      const itemIdx = stageOrder.indexOf(itemStage);
      const stageIdx = stageOrder.indexOf(stage);
      // 返回对应阶段及以下（适合当前阶段的知识）
      return itemIdx <= stageIdx;
    });
  }

  /** 个人知识库（Layer 3：每个学生独有的个性化内容） */
  private getPersonalKnowledge(userId?: string): KnowledgeSearchResult[] {
    return [
      {
        item_id: `p_${userId}_range_explained`,
        content: `[个性化] 之前讲解过的 range() 形象比喻：range(5) 就像从第 0 个台阶走 5 步 → [0,1,2,3,4]；range(1,5) 从第 1 个台阶走到第 5 个 → [1,2,3,4]；range(1,5,2) 每步跨 2 个台阶 → [1,3]`,
        category: 'programming',
        layer: 'personal',
        difficulty: 'beginner',
        tags: ['range', '循环', '个性化'],
        metadata: { userId },
        relevance_score: 0.95,
      },
      {
        item_id: `p_${userId}_loop_mistake`,
        content: `[个性化] 该生循环常见错误：忘记缩进循环体、range() 参数顺序混淆、for/while 使用场景不分、循环变量未更新导致死循环`,
        category: 'programming',
        layer: 'personal',
        difficulty: 'intermediate',
        tags: ['循环', '常见错误', '个性化'],
        metadata: { userId },
        relevance_score: 0.92,
      },
      {
        item_id: `p_${userId}_blockly_transition`,
        content: `[个性化] 该生的 Blockly → Python 过渡记录：已完成 Blockly 循环关卡 80%，推荐的对照练习是"积木转代码"模式`,
        category: 'programming',
        layer: 'personal',
        difficulty: 'beginner',
        tags: ['blockly', '转换', '个性化'],
        metadata: { userId },
        relevance_score: 0.88,
      },
      {
        item_id: `p_${userId}_interest_hint`,
        content: `[个性化] 该生偏好视觉型学习 + 游戏开发兴趣，推荐使用 Minecraft 风格类比解释编程概念，多用动画/图表辅助理解`,
        category: 'methodology',
        layer: 'personal',
        difficulty: 'beginner',
        tags: ['学习风格', '兴趣', '个性化'],
        metadata: { userId },
        relevance_score: 0.85,
      },
    ];
  }

  /**
   * 获取完整的模拟知识库（三层结构）
   */
  private getAllMockKnowledge(userId?: string, stage?: LearningStage): KnowledgeSearchResult[] {
    return [
      ...this.GLOBAL_KNOWLEDGE,
      ...this.getStageKnowledge(stage),
      ...this.getPersonalKnowledge(userId),
    ];
  }

  /**
   * 根据关键词匹配度排序
   */
  private rankByRelevance(
    results: KnowledgeSearchResult[],
    query: string
  ): KnowledgeSearchResult[] {
    const keywords = query
      .toLowerCase()
      .split(/[\s,，。]+/)
      .filter(Boolean);
    if (keywords.length === 0) return results;

    return results
      .map((item) => {
        const content = (item.content + ' ' + item.tags.join(' ')).toLowerCase();
        const matchCount = keywords.filter((k) => content.includes(k)).length;
        const matchRatio = matchCount / keywords.length;
        // 三层加权：个人 > 阶段 > 全局
        const layerBonus = item.layer === 'personal' ? 0.15 : item.layer === 'stage' ? 0.08 : 0;
        return {
          ...item,
          relevance_score: Math.min(1, matchRatio + layerBonus + item.relevance_score * 0.3),
        };
      })
      .sort((a, b) => b.relevance_score - a.relevance_score);
  }

  private createMockSearchResults(
    query: string,
    layerFilter?: KnowledgeLayer,
    stage?: LearningStage,
    topK: number = 5
  ): KnowledgeSearchResult[] {
    let allKnowledge = this.getAllMockKnowledge('mock_user', stage);

    if (layerFilter) {
      allKnowledge = allKnowledge.filter((item) => item.layer === layerFilter);
    }

    const ranked = this.rankByRelevance(allKnowledge, query);
    return ranked.slice(0, topK);
  }

  private createMockRAGResult(query: string, stage?: LearningStage, topK: number = 3): RAGResult {
    // 按三层分别检索，各取 topK 条
    const globalResults = this.createMockSearchResults(query, 'global', stage, topK);
    const stageResults = this.createMockSearchResults(query, 'stage', stage, topK);
    const personalResults = this.createMockSearchResults(query, 'personal', stage, topK);

    const allItems = [...globalResults, ...stageResults, ...personalResults];
    const mergedContext = [
      `[全局知识库] ${globalResults.map((r) => r.content).join('；')}`,
      stageResults.length > 0
        ? `[${stage ?? 'L2'}阶段知识库] ${stageResults.map((r) => r.content).join('；')}`
        : '',
      personalResults.length > 0
        ? `[个人知识库] ${personalResults.map((r) => r.content).join('；')}`
        : '',
    ]
      .filter(Boolean)
      .join('\n');

    return {
      items: allItems,
      context: mergedContext ?? '[全局知识库] 暂无匹配结果',
      sources: allItems.map((r) => r.item_id),
      total_score:
        allItems.reduce((acc, r) => acc + r.relevance_score, 0) / Math.max(allItems.length, 1),
    };
  }

  private createMockStats(): KnowledgeBaseStats {
    const global = this.GLOBAL_KNOWLEDGE.length;
    const stage = this.getStageKnowledge().length;
    const personal = this.getPersonalKnowledge('mock').length;
    return {
      total_items: global + stage + personal,
      layer_counts: { global, stage, personal },
      category_counts: { programming: 10, stem: 2, methodology: 2, ai: 2 },
      index_size: global + stage + personal,
      embedding_dimension: 384,
      has_embedding_model: false,
    };
  }
}
