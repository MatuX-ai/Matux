/**
 * AI 个性化教师服务
 *
 * 基于PRD F-08-AI设计，提供：
 * - 学生学习画像管理
 * - 上下文记忆（长期+会话）
 * - 个性化对话（注入画像+记忆）
 * - 成长轨迹追踪
 * - 智能教学建议
 * - AI教师人格配置
 *
 * 技术要点：
 * - 升级现有LLMAssistantService为AITeacherService
 * - 集成后端API进行数据持久化
 * - 当前使用Mock数据，后续替换为真实API
 */

import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of, throwError } from 'rxjs';
import { catchError, map, switchMap, tap, timeout } from 'rxjs/operators';

/**
 * 【P1 修复】统一业务 HTTP 超时兑底。避免后端代理 hang / CORS 预检超时 / 服务不可用
 *   时调用者一直 pending、UI spinner 永远不消失。所有公开方法使用同一兑底时间。
 */
const AI_TEACHER_HTTP_TIMEOUT_MS = 8_000;

import {
  AbilityDimensions,
  AbilityTrendPoint,
  AITeacherChatRequest,
  AITeacherChatResponse,
  AiTeacherLiveEvent,
  AiTeacherLiveSettings,
  AttentionProfile,
  ChatMessage,
  DailyLearningSuggestion,
  DEFAULT_LIVE_SETTINGS,
  EmotionLog,
  GrowthTrajectory,
  KnowledgeStateItem,
  LearningMilestone,
  LearningProfileUpdateRequest,
  LearningStyle,
  LongTermMemory,
  SessionMemory,
  SkillTreeNode,
  StudentLearningProfile,
  TeacherPersona,
  TeachingSuggestion,
  WeakPoint,
} from '../models/ai-teacher.models';

import { EmotionalCompanionService } from './emotional-companion.service';
import { AiTeacherLiveService } from './ai-teacher-live.service';
import { RAGResult, VectorKnowledgeService } from './vector-knowledge.service';

@Injectable({
  providedIn: 'root',
})
export class AITeacherService {
  private readonly API_BASE = '/api/v1/ai-teacher';

  // ==================== 状态流 ====================

  /** 学生学习画像 */
  private profileSubject = new BehaviorSubject<StudentLearningProfile | null>(null);
  public profile$ = this.profileSubject.asObservable();

  /** 当前会话记忆 */
  private sessionSubject = new BehaviorSubject<SessionMemory | null>(null);
  public session$ = this.sessionSubject.asObservable();
  /** 同步获取当前会话值（供模板/组件使用） */
  get currentSession(): SessionMemory | null {
    return this.sessionSubject.value;
  }

  /** AI教师人格配置 */
  private personaSubject = new BehaviorSubject<TeacherPersona>(this.getDefaultPersona());
  public persona$ = this.personaSubject.asObservable();

  /** 教学建议列表 */
  private suggestionsSubject = new BehaviorSubject<TeachingSuggestion[]>([]);
  public suggestions$ = this.suggestionsSubject.asObservable();

  /** 成长轨迹 */
  private growthSubject = new BehaviorSubject<GrowthTrajectory | null>(null);
  public growth$ = this.growthSubject.asObservable();

  /** 每日建议 */
  private dailySuggestionSubject = new BehaviorSubject<DailyLearningSuggestion | null>(null);
  public dailySuggestion$ = this.dailySuggestionSubject.asObservable();

  /** 知识状态 */
  private knowledgeStateSubject = new BehaviorSubject<KnowledgeStateItem[]>([]);
  public knowledgeState$ = this.knowledgeStateSubject.asObservable();

  constructor(
    private http: HttpClient,
    private vectorKnowledge: VectorKnowledgeService,
    private emotionCompanion: EmotionalCompanionService,
    // 【P3-B】可选注入：在某些调用上下文（如 main.ts 启动时）可能未提供
    private liveService?: AiTeacherLiveService
  ) {}

  // ==================== 【NaN 防御】工具方法 ====================

  /**
   * userId 合法性判定。
   *
   * userId 为 string 类型（可能是用户名，如 "test-user"），因此只拦截三类脏值：
   * 空值、Number(x) 为 NaN 的字面量（NaN / undefined / null），以及数值溢出为 Infinity 的数字字面量。
   */
  private isInvalidUserId(userId: string): boolean {
    const normalized = (userId ?? '').trim();
    if (!normalized || /^(nan|undefined|null)$/i.test(normalized)) {
      return true;
    }
    return (
      /^[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(normalized) &&
      !Number.isFinite(Number(normalized))
    );
  }

  /**
   * 非法 userId 的统一错误流：保持 Observable 契约，调用方的 catchError 仍可正常兑底。
   */
  private invalidUserId<T>(userId: string): Observable<T> {
    return throwError(() => new Error(`非法 userId: ${userId}`));
  }
  
  // ==================== 【P0-A 修复】后端字段归一化 ====================
  
  /** 把 unknown 安全窄化为可索引对象 */
  private static asRecord(value: unknown): Record<string, unknown> {
    return value !== null && typeof value === 'object' ? (value as Record<string, unknown>) : {};
  }
  
  /** 读取字段：优先 camelCase，其次 snake_case，最后默认值 */
  private static pick<T>(src: Record<string, unknown>, camel: string, snake: string, def: T): T {
    const value = src[camel] !== undefined && src[camel] !== null ? src[camel] : src[snake];
    return (value === undefined || value === null ? def : value) as T;
  }
  
  private static toNumber(value: unknown, def = 0): number {
    const n = Number(value);
    return Number.isFinite(n) ? n : def;
  }
  
  private static toText(value: unknown, def = ''): string {
    if (typeof value === 'string') return value;
    if (value === undefined || value === null) return def;
    return String(value);
  }
  
  private static toArray(value: unknown): unknown[] {
    return Array.isArray(value) ? value : [];
  }
  
  /**
   * 【P0-4 合规】离线（mock）模型名集合。
   *
   * 后端尚未接入真实 LLM 时，/chat 返回的 model 落在这一集合；
   * 未来接入真实 LLM 后模型名不会命中本集合，角标自动消失。
   * 口径与 tmp/1.0.2-roadmap.md 的 P0-4 判据保持一致。
   */
  private static readonly MOCK_MODEL_NAMES: ReadonlySet<string> = new Set([
    'mock',
    'mock-ai-teacher',
    'rule-based-fallback',
  ]);

  /**
   * 【P0-4 合规】判定一次回复是否为离线模式。
   *
   * 判定口径：
   * 1) 精确命中 MOCK_MODEL_NAMES 集合；
   * 2) 兼容前缀写法（mock-xxx / mock_xxx / rule-based-xxx），
   *    避免后端新增 mock 变体时前端漏判。
   *
   * 相比原先的 `model === 'mock'` 单值比较，本方法覆盖
   * mock-ai-teacher / rule-based-fallback 等实际返回的模型名。
   */
  static isMockModel(model: string | null | undefined): boolean {
    const normalized = (model ?? '').trim().toLowerCase();
    if (!normalized) {
      return false;
    }
    if (AITeacherService.MOCK_MODEL_NAMES.has(normalized)) {
      return true;
    }
    return normalized.startsWith('mock') || normalized.startsWith('rule-based');
  }

  /** 递归归一化技能树节点 */
  private normalizeSkillNode(raw: unknown): SkillTreeNode {
    const n = AITeacherService.asRecord(raw);
    const children = AITeacherService.toArray(n['children']);
    const parent = AITeacherService.toText(n['parent']);
    const unlock = AITeacherService.toText(n['unlockRequirement'] ?? n['unlock_requirement']);
    return {
      id: AITeacherService.toText(n['id']),
      name: AITeacherService.toText(n['name']),
      category: AITeacherService.toText(n['category'], 'python') as SkillTreeNode['category'],
      progress: AITeacherService.toNumber(n['progress']),
      status: AITeacherService.toText(n['status'], 'not_started') as SkillTreeNode['status'],
      ...(children.length > 0 ? { children: children.map((c) => this.normalizeSkillNode(c)) } : {}),
      ...(parent ? { parent } : {}),
      ...(unlock ? { unlockRequirement: unlock } : {}),
    };
  }
  
  /**
   * 【P0-A 修复】把后端 snake_case 画像归一化为前端 camelCase 契约。
   *
   * 后端 GET /api/v1/ai-teacher/profile/{user_id} 返回 pydantic snake_case
   * （weak_points / display_name / ability_dimensions ...），而
   * StudentLearningProfile 是 camelCase。此前没有归一化层，
   * generatePersonaSeed 里的 `profile.weakPoints.slice(...)` 直接抛
   * TypeError: Cannot read properties of undefined (reading 'slice')，
   * 画像页与学习地图同时卡在「正在生成」。
   *
   * 注意：knowledgeMastery / errorPatterns 的 key 是业务实体 id
   * （如 python_basics / indentation_error），必须原样保留，不能转成 camelCase。
   */
  private normalizeProfile(raw: unknown, fallbackUserId: string): StudentLearningProfile {
    const src = AITeacherService.asRecord(raw);
    const dims = AITeacherService.asRecord(
      src['abilityDimensions'] ?? src['ability_dimensions']
    );
    const abilityDimensions: AbilityDimensions = {
      programmingThinking: AITeacherService.toNumber(
        dims['programmingThinking'] ?? dims['programming_thinking']
      ),
      algorithmAbility: AITeacherService.toNumber(
        dims['algorithmAbility'] ?? dims['algorithm_ability']
      ),
      debuggingSkill: AITeacherService.toNumber(
        dims['debuggingSkill'] ?? dims['debugging_skill']
      ),
      projectPractice: AITeacherService.toNumber(
        dims['projectPractice'] ?? dims['project_practice']
      ),
      stemExperiment: AITeacherService.toNumber(
        dims['stemExperiment'] ?? dims['stem_experiment']
      ),
      codeQuality: AITeacherService.toNumber(dims['codeQuality'] ?? dims['code_quality']),
      independentCompletion: AITeacherService.toNumber(
        dims['independentCompletion'] ?? dims['independent_completion']
      ),
      questionQuality: AITeacherService.toNumber(
        dims['questionQuality'] ?? dims['question_quality']
      ),
    };
  
    const weakPoints: WeakPoint[] = AITeacherService.toArray(
      AITeacherService.pick<unknown[]>(src, 'weakPoints', 'weak_points', [])
    ).map((item) => {
      const w = AITeacherService.asRecord(item);
      return {
        knowledgePoint: AITeacherService.toText(w['knowledgePoint'] ?? w['knowledge_point']),
        mastery: AITeacherService.toNumber(w['mastery']),
        errorRate: AITeacherService.toNumber(w['errorRate'] ?? w['error_rate']),
        suggestion: AITeacherService.toText(w['suggestion']),
        lastDetected: AITeacherService.toText(w['lastDetected'] ?? w['last_detected']),
      };
    });
  
    const att = AITeacherService.asRecord(
      src['attentionProfile'] ?? src['attention_profile']
    );
    const attentionProfile: AttentionProfile = {
      averageFocusDurationMinutes: AITeacherService.toNumber(
        att['averageFocusDurationMinutes'] ?? att['average_focus_duration_minutes']
      ),
      tabSwitchFrequency: AITeacherService.toNumber(
        att['tabSwitchFrequency'] ?? att['tab_switch_frequency']
      ),
      hesitationTimeMs: AITeacherService.toNumber(
        att['hesitationTimeMs'] ?? att['hesitation_time_ms']
      ),
      trend: AITeacherService.toText(att['trend'], 'stable') as AttentionProfile['trend'],
    };
  
    const emotionalStates: EmotionLog[] = AITeacherService.toArray(
      AITeacherService.pick<unknown[]>(src, 'emotionalStates', 'emotional_states', [])
    ).map((item) => {
      const e = AITeacherService.asRecord(item);
      return {
        timestamp: AITeacherService.toText(e['timestamp']),
        emotion: AITeacherService.toText(e['emotion'], 'neutral') as EmotionLog['emotion'],
        source: AITeacherService.toText(e['source'], 'dialogue') as EmotionLog['source'],
        confidence: AITeacherService.toNumber(e['confidence']),
      };
    });
  
    const learningMilestones: LearningMilestone[] = AITeacherService.toArray(
      AITeacherService.pick<unknown[]>(src, 'learningMilestones', 'learning_milestones', [])
    ).map((item) => {
      const m = AITeacherService.asRecord(item);
      return {
        id: AITeacherService.toText(m['id']),
        type: AITeacherService.toText(m['type'], 'custom') as LearningMilestone['type'],
        title: AITeacherService.toText(m['title']),
        description: AITeacherService.toText(m['description']),
        achievedAt: AITeacherService.toText(m['achievedAt'] ?? m['achieved_at']),
      };
    });
  
    const skillTree: SkillTreeNode[] = AITeacherService.toArray(
      AITeacherService.pick<unknown[]>(src, 'skillTree', 'skill_tree', [])
    ).map((item) => this.normalizeSkillNode(item));
  
    return {
      userId: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'userId', 'user_id', fallbackUserId),
        fallbackUserId
      ),
      displayName: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'displayName', 'display_name', '同学')
      ),
      gradeLevel: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'gradeLevel', 'grade_level', '')
      ),
      ageGroup: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'ageGroup', 'age_group', '')
      ),
      learningStyle: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'learningStyle', 'learning_style', 'visual')
      ) as LearningStyle,
      preferredContentType: AITeacherService.toText(
        AITeacherService.pick<unknown>(
          src,
          'preferredContentType',
          'preferred_content_type',
          'interactive'
        )
      ) as StudentLearningProfile['preferredContentType'],
      abilityDimensions,
      interestPreferences: AITeacherService.toArray(
        AITeacherService.pick<unknown[]>(src, 'interestPreferences', 'interest_preferences', [])
      ).map((i) => AITeacherService.toText(i)),
      knowledgeMastery: AITeacherService.asRecord(
        AITeacherService.pick<unknown>(src, 'knowledgeMastery', 'knowledge_mastery', {})
      ) as Record<string, number>,
      totalStudyTimeMinutes: AITeacherService.toNumber(
        AITeacherService.pick<unknown>(src, 'totalStudyTimeMinutes', 'total_study_time_minutes', 0)
      ),
      completedCoursesCount: AITeacherService.toNumber(
        AITeacherService.pick<unknown>(src, 'completedCoursesCount', 'completed_courses_count', 0)
      ),
      averageQuizScore: AITeacherService.toNumber(
        AITeacherService.pick<unknown>(src, 'averageQuizScore', 'average_quiz_score', 0)
      ),
      currentStreakDays: AITeacherService.toNumber(
        AITeacherService.pick<unknown>(src, 'currentStreakDays', 'current_streak_days', 0)
      ),
      longestStreakDays: AITeacherService.toNumber(
        AITeacherService.pick<unknown>(src, 'longestStreakDays', 'longest_streak_days', 0)
      ),
      weakPoints,
      errorPatterns: AITeacherService.asRecord(
        AITeacherService.pick<unknown>(src, 'errorPatterns', 'error_patterns', {})
      ) as Record<string, number>,
      attentionProfile,
      emotionalStates,
      learningMilestones,
      skillTree,
      personaSeed: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'personaSeed', 'persona_seed', '')
      ),
      learningGoals: AITeacherService.toArray(
        AITeacherService.pick<unknown[]>(src, 'learningGoals', 'learning_goals', [])
      ).map((i) => AITeacherService.toText(i)),
      createdAt: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'createdAt', 'created_at', '')
      ),
      updatedAt: AITeacherService.toText(
        AITeacherService.pick<unknown>(src, 'updatedAt', 'updated_at', '')
      ),
    };
  }
  
  // ==================== 学习画像 ====================

  /** 获取学生学习画像 */
  getProfile(userId: string): Observable<StudentLearningProfile> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /profile/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http.get<unknown>(`${this.API_BASE}/profile/${userId}`).pipe(
      // 【P1 修复】统一 8s 超时兑底，跳进 catchError → mock。
      timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
      // 【P0-A 修复】后端返回 snake_case，先归一化为前端 camelCase 契约
      map((raw) => this.normalizeProfile(raw, userId)),
      tap((profile) => this.profileSubject.next(profile)),
      catchError(() => {
        // 降级为Mock数据
        const mockProfile = this.createMockProfile(userId);
        this.profileSubject.next(mockProfile);
        return of(mockProfile);
      })
    );
  }

  /** 更新学习画像 */
  updateProfile(
    userId: string,
    update: LearningProfileUpdateRequest
  ): Observable<StudentLearningProfile> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /profile/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http
      .patch<unknown>(`${this.API_BASE}/profile/${userId}`, update)
      .pipe(
        // 【P0-A 修复】PATCH 同样返回 snake_case，需归一化
        map((raw) => this.normalizeProfile(raw, userId)),
        tap((profile) => this.profileSubject.next(profile)),
        catchError(() => {
          // 本地更新
          const current = this.profileSubject.value;
          if (current) {
            const updated = { ...current, ...update, updatedAt: new Date().toISOString() };
            this.profileSubject.next(updated as StudentLearningProfile);
            return of(updated as StudentLearningProfile);
          }
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          return of(current!);
        })
      );
  }

  /**
   * 生成画像摘要（供AI教师prompt使用）
   *
   * 【P0-A 修复】旧实现无条件访问 profile.weakPoints.slice / abilityDimensions，
   * 一旦后端返回 snake_case（weak_points）或字段缺失，就会抛
   * "Cannot read properties of undefined (reading 'slice')"：
   * 异常在 subscribe 的 next 回调里抛出，会越过 catchError，
   * 直接导致画像页与学习地图永久卡在「正在生成」。
   * 现在：空画像返回默认 seed 并告警；数组/数值都做类型防御。
   */
  generatePersonaSeed(profile: StudentLearningProfile | null | undefined): string {
    if (!profile) {
      console.warn('[AITeacher] generatePersonaSeed: 画像为空，返回默认人格种子');
      return '暂无学习画像数据，请以通用方式引导学生';
    }

    const styleMap: Record<LearningStyle, string> = {
      visual: '视觉型',
      auditory: '听觉型',
      reading: '读写型',
      kinesthetic: '动觉型',
    };

    const safeNum = (value: unknown): number => {
      const n = Number(value);
      return Number.isFinite(n) ? n : 0;
    };

    // 防御：weakPoints 缺失/非数组时按空数组处理，不抛异常
    if (!Array.isArray(profile.weakPoints)) {
      console.warn('[AITeacher] generatePersonaSeed: weakPoints 缺失，已按空数组处理');
    }
    const weakPoints = Array.isArray(profile.weakPoints) ? profile.weakPoints : [];
    const weakPointsStr = weakPoints
      .filter((w) => !!w && !!w.knowledgePoint)
      .slice(0, 3)
      .map((w) => `${w.knowledgePoint}(${Math.round(safeNum(w.mastery) * 100)}%)`)
      .join('、');

    if (!profile.abilityDimensions) {
      console.warn('[AITeacher] generatePersonaSeed: abilityDimensions 缺失，已按 0 处理');
    }
    const dims = profile.abilityDimensions;
    const styleLabel = styleMap[profile.learningStyle] ?? '综合型';

    return [
      `${profile.displayName || '同学'}，${profile.gradeLevel || '未知年级'}，${styleLabel}学习者`,
      `编程思维${safeNum(dims?.programmingThinking)}/100`,
      `独立完成率${safeNum(dims?.independentCompletion)}%`,
      weakPointsStr ? `薄弱环节：${weakPointsStr}` : '',
      `连续学习${safeNum(profile.currentStreakDays)}天`,
    ]
      .filter(Boolean)
      .join('。');
  }

  /** 注入情绪上下文到画像摘要 */
  private injectEmotionContext(seed: string): string {
    if (!this.emotionCompanion.companionModeEnabled) return seed;
    const emotion = this.emotionCompanion.currentEmotion;
    if (!emotion || emotion === 'neutral') return seed;
    const emoji = this.emotionCompanion.getEmotionEmoji(emotion);
    const label = this.emotionCompanion.getEmotionLabel(emotion);
    return `${seed}。当前情绪状态：${emoji}${label}`;
  }

  // ==================== 上下文记忆 ====================

  /** 获取长期记忆 */
  getLongTermMemories(userId: string, query?: string): Observable<LongTermMemory[]> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /memory/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    const params: Record<string, string> = query ? { query } : {};
    return this.http
      .get<LongTermMemory[]>(`${this.API_BASE}/memory/${userId}/long-term`, { params })
      .pipe(catchError(() => of(this.createMockMemories())));
  }

  /** 保存长期记忆 */
  saveLongTermMemory(
    userId: string,
    memory: Omit<LongTermMemory, 'id' | 'createdAt' | 'accessCount' | 'lastAccessedAt'>
  ): Observable<LongTermMemory> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /memory/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http
      .post<LongTermMemory>(`${this.API_BASE}/memory/${userId}/long-term`, memory)
      .pipe(
        catchError(() =>
          of({
            ...memory,
            id: `mem_${Date.now()}`,
            createdAt: new Date().toISOString(),
            accessCount: 0,
            lastAccessedAt: new Date().toISOString(),
          } as LongTermMemory)
        )
      );
  }

  /** 获取/创建会话记忆 */
  getOrCreateSession(userId: string): Observable<SessionMemory> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /session/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    const existing = this.sessionSubject.value;
    if (existing && existing.userId === userId) {
      return of(existing);
    }

    return this.http.get<SessionMemory>(`${this.API_BASE}/session/${userId}`).pipe(
      tap((session) => this.sessionSubject.next(session)),
      catchError(() => {
        const session: SessionMemory = {
          sessionId: `session_${Date.now()}`,
          userId,
          recentMessages: [],
          currentTask: null,
          startedAt: new Date().toISOString(),
          lastActivityAt: new Date().toISOString(),
        };
        this.sessionSubject.next(session);
        return of(session);
      })
    );
  }

  // ==================== AI 教师对话 ====================

  /** 发送消息给AI教师 */
  // eslint-disable-next-line max-lines-per-function, max-depth
  chat(request: AITeacherChatRequest): Observable<AITeacherChatResponse> {
    const profile = this.profileSubject.value;
    const persona = this.personaSubject.value;

    // 注入画像和人格到请求
    const profileSeed = this.injectEmotionContext(profile ? this.generatePersonaSeed(profile) : '');

    // RAG 检索：先获取相关知识上下文，再发送对话请求
    const ragObservable: Observable<RAGResult | null> = request.userId
      ? this.vectorKnowledge.ragRetrieve(
          request.message,
          request.userId,
          profile ? this.injectEmotionContext(this.generatePersonaSeed(profile)) : '',
          this.inferStage(profile?.gradeLevel)
        )
      : of(null);

    return ragObservable.pipe(
      // eslint-disable-next-line max-lines-per-function
      switchMap((ragResult: RAGResult | null) => {
        // 【P0-B 修复】后端 ChatRequest 是 pydantic snake_case 契约。
        //   之前直接发 camelCase（userId/sessionId），user_id/session_id 缺失，
        //   FastAPI 直接 422，所有对话都静默落进下面的 catchError → mock 分支，
        //   因此看起来「能用」但从未真实对接。
        const requestWithContext = {
          user_id: request.userId,
          message: request.message,
          session_id: request.sessionId,
          profile_seed: profileSeed,
          persona: {
            address_mode: persona.addressMode,
            language_style: persona.languageStyle,
            hint_level: persona.hintLevel,
            encouragement_frequency: persona.encouragementFrequency,
            emoji_usage: persona.emojiUsage,
          },
          knowledge_context: ragResult?.context ?? '',
          knowledge_sources: ragResult?.sources ?? [],
        };

        return this.http
          .post<unknown>(`${this.API_BASE}/chat`, requestWithContext)
          .pipe(
            // 【P0-B 修复】后端 RAG 懒加载模型时会长时间挂起，必须设超时，
            //   否则界面 spinner 永不结束（catchError 也进不去）。
            timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
            // 【P0-B 修复】响应也是 snake_case，归一化后再交给 UI
            map((raw) => this.normalizeChatResponse(raw, request.sessionId)),
            tap((response) => {
              // 自动记录AI检测到的情绪到情感陪伴日志（跳过 neutral 避免淹没日志）
              if (response.emotionDetected && response.emotionDetected !== 'neutral') {
                // EmotionLog.emotion 与 EmotionState 有交集但不是同一类型
                const detected = response.emotionDetected;
                const validEmotions: readonly string[] = [
                  'frustrated',
                  'anxious',
                  'confused',
                  'bored',
                ];
                if (validEmotions.includes(detected)) {
                  this.emotionCompanion.logEmotion(
                    detected as 'frustrated' | 'anxious' | 'confused' | 'bored',
                    'AI对话检测',
                    3
                  );
                }
              }
              // 更新会话记忆
              const session = this.sessionSubject.value;
              if (session) {
                const userMsg: ChatMessage = {
                  role: 'user',
                  content: request.message,
                  timestamp: new Date().toISOString(),
                };
                const aiMsg: ChatMessage = {
                  role: 'assistant',
                  content: response.reply,
                  timestamp: new Date().toISOString(),
                  metadata: {
                    knowledgeUsed: response.knowledgeUsed || !!ragResult?.context,
                    confidence: response.confidence,
                    referencedMemories: response.memoriesReferenced,
                    emotionDetected: response.emotionDetected,
                  },
                };
                const updatedMessages = [...session.recentMessages, userMsg, aiMsg].slice(-20);
                this.sessionSubject.next({
                  ...session,
                  recentMessages: updatedMessages,
                  lastActivityAt: new Date().toISOString(),
                });
              }
            }),
            catchError((error: HttpErrorResponse) => {
              // 【P0-4 合规】鉴权失败（401/403）不是「离线模式」：
              // 降级成 mock 回复会把合规故障伪装成正常体验，必须原样抛给调用方。
              const errorStatus = Number(error?.status ?? 0);
              if (errorStatus === 401 || errorStatus === 403) {
                console.warn('[AITeacher] /chat 鉴权失败（%s），不做离线降级', errorStatus);
                return throwError(() => error);
              }
              // 降级兜底：后端不可用时仍能让对话继续，但要明确标记 isMock=true
              console.warn('[AITeacher] /chat 请求失败，已降级为本地 mock 回复:', error?.status ?? error);
              const mockResponse: AITeacherChatResponse = {
                reply: this.generateMockReply(request.message, persona),
                sessionId: request.sessionId,
                emotionDetected: 'neutral',
                memoriesReferenced: [],
                knowledgeUsed: !!ragResult?.context,
                suggestions: [],
                model: 'mock',
                confidence: 0.7,
                inferenceTimeMs: 200,
                isMock: true,
              };
              return of(mockResponse);
            })
          );
      })
    );
  }

  /**
   * 【P0-B 修复】把后端 ChatResponse 的 snake_case 归一化为前端 camelCase 契约。
   * 后端只用到 reply / session_id / emotion_detected / memories_referenced /
   * knowledge_used / inference_time_ms，其余字段缺失时给安全默认值。
   */
  private normalizeChatResponse(raw: unknown, fallbackSessionId: string): AITeacherChatResponse {
    const r = AITeacherService.asRecord(raw);
    const model = AITeacherService.toText(r['model'], 'unknown');
    // 【P0-4 合规】isMock 判定：后端显式标记优先，缺失时回退 model 集合判定。
    const rawIsMock = AITeacherService.pick<unknown>(r, 'isMock', 'is_mock', undefined);
    const degraded = Boolean(
      AITeacherService.pick<unknown>(r, 'isDegraded', 'is_degraded', false) ||
        AITeacherService.pick<unknown>(r, 'degraded', 'degraded_flag', false)
    );
    const isMock =
      degraded ||
      (typeof rawIsMock === 'boolean' ? rawIsMock : AITeacherService.isMockModel(model));
    return {
      reply: AITeacherService.toText(r['reply'] ?? r['message']),
      sessionId: AITeacherService.toText(
        AITeacherService.pick<unknown>(r, 'sessionId', 'session_id', fallbackSessionId),
        fallbackSessionId
      ),
      emotionDetected: AITeacherService.toText(
        AITeacherService.pick<unknown>(r, 'emotionDetected', 'emotion_detected', 'neutral'),
        'neutral'
      ) as AITeacherChatResponse['emotionDetected'],
      memoriesReferenced: AITeacherService.toArray(
        AITeacherService.pick<unknown[]>(r, 'memoriesReferenced', 'memories_referenced', [])
      ).map((item) => AITeacherService.toText(item)),
      knowledgeUsed: Boolean(
        AITeacherService.pick<unknown>(r, 'knowledgeUsed', 'knowledge_used', false)
      ),
      suggestions: AITeacherService.toArray(
        AITeacherService.pick<unknown[]>(r, 'suggestions', 'suggestions', [])
      ) as TeachingSuggestion[],
      model,
      confidence: AITeacherService.toNumber(r['confidence']),
      inferenceTimeMs: AITeacherService.toNumber(
        AITeacherService.pick<unknown>(r, 'inferenceTimeMs', 'inference_time_ms', 0)
      ),
      isMock,
    };
  }

  /** 根据年级推断学习阶段 */
  private inferStage(gradeLevel?: string): 'L1' | 'L2' | 'L3' | 'L4' | undefined {
    if (!gradeLevel) return undefined;
    const match = gradeLevel.match(/(\d+)/);
    if (!match) return undefined;
    const grade = parseInt(match[1], 10);
    if (grade <= 3) return 'L1';
    if (grade <= 6) return 'L2';
    if (grade <= 9) return 'L3';
    return 'L4';
  }

  // ==================== 成长轨迹 ====================

  /** 获取成长轨迹 */
  getGrowthTrajectory(userId: string, months: number = 6): Observable<GrowthTrajectory> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /growth/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http
      .get<GrowthTrajectory>(`${this.API_BASE}/growth/${userId}`, { params: { months } })
      .pipe(
        // 【P1 修复】统一超时兑底 → mock
        timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
        tap((growth) => this.growthSubject.next(growth)),
        catchError(() => {
          const mockGrowth = this.createMockGrowthTrajectory(months);
          this.growthSubject.next(mockGrowth);
          return of(mockGrowth);
        })
      );
  }

  // ==================== 智能教学建议 ====================

  /** 获取教学建议 */
  getTeachingSuggestions(userId: string): Observable<TeachingSuggestion[]> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /suggestions/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http.get<TeachingSuggestion[]>(`${this.API_BASE}/suggestions/${userId}`).pipe(
      // 【P1 修复】统一超时兑底 → mock
      timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
      tap((suggestions) => this.suggestionsSubject.next(suggestions)),
      catchError(() => {
        const mockSuggestions = this.createMockSuggestions();
        this.suggestionsSubject.next(mockSuggestions);
        return of(mockSuggestions);
      })
    );
  }

  /** 获取每日学习建议 */
  getDailySuggestion(userId: string): Observable<DailyLearningSuggestion> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /daily-suggestion/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http
      .get<DailyLearningSuggestion>(`${this.API_BASE}/daily-suggestion/${userId}`)
      .pipe(
        // 【P1 修复】统一超时兑底 → mock
        timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
        tap((suggestion) => this.dailySuggestionSubject.next(suggestion)),
        catchError(() => {
          const mock = this.createMockDailySuggestion();
          this.dailySuggestionSubject.next(mock);
          return of(mock);
        })
      );
  }

  /** 标记建议已读 */
  markSuggestionRead(suggestionId: string): Observable<void> {
    return this.http.patch<void>(`${this.API_BASE}/suggestions/${suggestionId}/read`, {}).pipe(
      tap(() => {
        const current = this.suggestionsSubject.value;
        this.suggestionsSubject.next(
          current.map((s) => (s.id === suggestionId ? { ...s, isRead: true } : s))
        );
      }),
      catchError(() => of(void 0))
    );
  }

  // ==================== 学习诊断引擎（本地分析）====================

  /**
   * 本地诊断学生学习问题（当API不可用时降级使用）
   * 分析画像和知识状态，生成教学建议
   */
  diagnoseLearningIssues(
    profile: StudentLearningProfile,
    knowledgeState: KnowledgeStateItem[]
  ): TeachingSuggestion[] {
    const suggestions: TeachingSuggestion[] = [];

    // 1. 前置知识缺失检测
    this.detectPrerequisiteGaps(knowledgeState).forEach((s) => suggestions.push(s));

    // 2. 概念混淆检测（根据错误模式）
    this.detectConceptConfusion(profile).forEach((s) => suggestions.push(s));

    // 3. 学习高原期检测
    this.detectLearningPlateau(profile).forEach((s) => suggestions.push(s));

    // 4. 能力不均衡检测
    this.detectSkillImbalance(profile).forEach((s) => suggestions.push(s));

    // 5. 注意力下降检测
    this.detectAttentionDecline(profile).forEach((s) => suggestions.push(s));

    // 6. AI过度依赖检测
    this.detectAIDependence(profile).forEach((s) => suggestions.push(s));

    return suggestions;
  }

  /** 检测前置知识缺失 */
  private detectPrerequisiteGaps(knowledgeState: KnowledgeStateItem[]): TeachingSuggestion[] {
    const results: TeachingSuggestion[] = [];
    for (const item of knowledgeState) {
      if (item.status === 'learning' && item.mastery < 0.5) {
        // 检查前置知识是否掌握
        const missingPrereqs = item.prerequisites.filter((prereqId) => {
          const prereq = knowledgeState.find((k) => k.knowledgePoint === prereqId);
          return prereq && prereq.mastery < 0.7;
        });
        if (missingPrereqs.length > 0) {
          results.push({
            id: `diag_prereq_${item.knowledgePoint}_${Date.now()}`,
            diagnosisType: 'prerequisite_missing',
            severity: 'warning',
            title: `前置知识缺失：${item.knowledgePoint}`,
            description: `你正在学 ${item.knowledgePoint}，但 ${missingPrereqs.join('、')} 还没完全掌握。`,
            suggestedAction: `先巩固 ${missingPrereqs.join('、')} 的基础知识，再继续学习 ${item.knowledgePoint}`,
            relatedKnowledgePoints: [...missingPrereqs, item.knowledgePoint],
            recommendedCourses: missingPrereqs.map((p) => `review_${p}`),
            createdAt: new Date().toISOString(),
            isRead: false,
          });
        }
      }
    }
    return results;
  }

  /** 检测概念混淆（根据高频错误模式） */
  private detectConceptConfusion(profile: StudentLearningProfile): TeachingSuggestion[] {
    const results: TeachingSuggestion[] = [];

    // 分析错误模式，找出高频错误类型
    const errorEntries = Object.entries(profile.errorPatterns || {});
    if (errorEntries.length === 0) return results;

    // 按错误次数排序，取前2个
    const topErrors = errorEntries.sort(([, a], [, b]) => b - a).slice(0, 2);

    const errorLabels: Record<string, string> = {
      indentation_error: '缩进错误',
      range_parameter: 'range() 参数混淆',
      list_index: '列表索引越界',
      type_error: '类型错误',
      syntax_error: '语法错误',
    };

    for (const [errorType, count] of topErrors) {
      if (count >= 3) {
        results.push({
          id: `diag_confusion_${errorType}_${Date.now()}`,
          diagnosisType: 'concept_confusion',
          severity: count >= 10 ? 'critical' : 'info',
          title: `概念混淆：${errorLabels[errorType] || errorType}`,
          description: `你最近出现了 ${count} 次 ${errorLabels[errorType] || errorType}，你可能对这个概念的理解还不够扎实。`,
          suggestedAction: `建议做 ${errorLabels[errorType] || errorType} 相关的专项练习`,
          relatedKnowledgePoints: [errorType],
          recommendedCourses: [`practice_${errorType}`],
          createdAt: new Date().toISOString(),
          isRead: false,
        });
      }
    }
    return results;
  }

  /** 检测学习高原期 */
  private detectLearningPlateau(profile: StudentLearningProfile): TeachingSuggestion[] {
    const results: TeachingSuggestion[] = [];

    // 检查是否有在学的知识点进度停滞（> 3天没有进步）
    const learningSkills = Object.entries(profile.knowledgeMastery || {})
      .filter(([, mastery]) => mastery > 0 && mastery < 1)
      .sort(([, a], [, b]) => a - b);

    if (learningSkills.length > 0) {
      const slowest = learningSkills[0];
      if (slowest[1] < 0.3) {
        results.push({
          id: `diag_plateau_${Date.now()}`,
          diagnosisType: 'learning_plateau',
          severity: 'warning',
          title: `学习高原期：${slowest[0]}`,
          description: `${slowest[0]} 的进度似乎有些停滞，掌握度 ${Math.round(slowest[1] * 100)}%`,
          suggestedAction: '换个方式试试！换个学习方式，或者休息一下再来挑战。',
          relatedKnowledgePoints: [slowest[0]],
          recommendedCourses: [`alt_${slowest[0]}`],
          createdAt: new Date().toISOString(),
          isRead: false,
        });
      }
    }
    return results;
  }

  /** 检测能力不均衡 */
  private detectSkillImbalance(profile: StudentLearningProfile): TeachingSuggestion[] {
    const results: TeachingSuggestion[] = [];
    const dims = profile.abilityDimensions;
    if (!dims) return results;

    const entries = Object.entries(dims) as Array<[string, number]>;
    const values = entries.map(([, v]) => v);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const threshold = 20;

    // 找出明显低于平均的维度
    const weakDims = entries.filter(([key, val]) => {
      if (key === 'independentCompletion' || key === 'questionQuality') return false;
      return val < avg - threshold;
    });

    const strongDims = entries.filter(([key, val]) => {
      if (key === 'independentCompletion' || key === 'questionQuality') return false;
      return val > avg + threshold;
    });

    if (weakDims.length > 0 && strongDims.length > 0) {
      const dimLabels: Record<string, string> = {
        programmingThinking: '编程思维',
        algorithmAbility: '算法能力',
        debuggingSkill: '调试能力',
        projectPractice: '项目实践',
        stemExperiment: 'STEM实验',
        codeQuality: '代码规范',
      };

      results.push({
        id: `diag_imbalance_${Date.now()}`,
        diagnosisType: 'skill_imbalance',
        severity: 'info',
        title: '能力发展不均衡',
        description: `你的 ${dimLabels[strongDims[0][0]] || strongDims[0][0]} 很强，但 ${dimLabels[weakDims[0][0]] || weakDims[0][0]} 相对较弱。`,
        suggestedAction: `可以多花点时间在 ${dimLabels[weakDims[0][0]] || weakDims[0][0]} 上的练习。`,
        relatedKnowledgePoints: weakDims.map(([k]) => k),
        recommendedCourses: [`enhance_${weakDims[0][0]}`],
        createdAt: new Date().toISOString(),
        isRead: false,
      });
    }
    return results;
  }

  /** 检测注意力下降 */
  private detectAttentionDecline(profile: StudentLearningProfile): TeachingSuggestion[] {
    const results: TeachingSuggestion[] = [];
    const attention = profile.attentionProfile;
    if (!attention) return results;

    if (attention.trend === 'declining') {
      results.push({
        id: `diag_attention_${Date.now()}`,
        diagnosisType: 'attention_decline',
        severity: 'warning',
        title: '注意力下降提醒',
        description: '最近你的注意力集中时间有所下降，切屏频率增加。',
        suggestedAction: '建议适当休息，或换一个更有趣的学习任务来重新激发兴趣。',
        relatedKnowledgePoints: [],
        recommendedCourses: ['fun_projects'],
        createdAt: new Date().toISOString(),
        isRead: false,
      });
    }
    return results;
  }

  /** 检测AI过度依赖 */
  private detectAIDependence(profile: StudentLearningProfile): TeachingSuggestion[] {
    const results: TeachingSuggestion[] = [];

    // 检查独立完成率
    const independence = profile.abilityDimensions?.independentCompletion;
    if (independence !== undefined && independence < 40) {
      results.push({
        id: `diag_dependence_${Date.now()}`,
        diagnosisType: 'ai_overdependence',
        severity: 'info',
        title: '尝试独立解决问题',
        description: `你的独立完成率为 ${independence}%，可以先自己思考 2 分钟。`,
        suggestedAction: '遇到问题先自己尝试解决，实在不行再问 AI 老师。',
        relatedKnowledgePoints: [],
        recommendedCourses: ['independent_practice'],
        createdAt: new Date().toISOString(),
        isRead: false,
      });
    }
    return results;
  }

  /**
   * 获取主动教学建议（结合API和本地诊断）
   */
  getActiveTeachingSuggestions(userId: string): Observable<TeachingSuggestion[]> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /active-suggestions/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    const profile = this.profileSubject.value;
    const knowledgeState = this.knowledgeStateSubject.value;

    // 尝试从API获取
    return this.http
      .get<TeachingSuggestion[]>(`${this.API_BASE}/active-suggestions/${userId}`)
      .pipe(
        tap((suggestions) => {
          const updated = [
            ...this.diagnoseLearningIssues(
              profile ?? this.createMockProfile(userId),
              knowledgeState.length > 0 ? knowledgeState : this.createMockKnowledgeState()
            ),
            ...suggestions,
          ];
          this.suggestionsSubject.next(updated);
        }),
        catchError(() => {
          // API 不可用，使用本地诊断
          const localSuggestions: TeachingSuggestion[] = this.diagnoseLearningIssues(
            profile ?? this.createMockProfile(userId),
            knowledgeState.length > 0 ? knowledgeState : this.createMockKnowledgeState()
          );
          this.suggestionsSubject.next(localSuggestions);
          return of(localSuggestions);
        })
      );
  }

  // ==================== 知识状态 ====================

  /** 获取知识状态 */
  getKnowledgeState(userId: string): Observable<KnowledgeStateItem[]> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /knowledge-state/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http.get<KnowledgeStateItem[]>(`${this.API_BASE}/knowledge-state/${userId}`).pipe(
      tap((state) => this.knowledgeStateSubject.next(state)),
      catchError(() => {
        const mockState = this.createMockKnowledgeState();
        this.knowledgeStateSubject.next(mockState);
        return of(mockState);
      })
    );
  }

  // ==================== AI 教师人格 ====================

  /** 获取人格配置 */
  getPersona(userId: string): Observable<TeacherPersona> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /persona/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http.get<TeacherPersona>(`${this.API_BASE}/persona/${userId}`).pipe(
      tap((persona) => this.personaSubject.next(persona)),
      catchError(() => of(this.personaSubject.value))
    );
  }

  /** 更新人格配置 */
  updatePersona(userId: string, persona: Partial<TeacherPersona>): Observable<TeacherPersona> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /persona/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    const updated = { ...this.personaSubject.value, ...persona };
    this.personaSubject.next(updated);
    return this.http
      .patch<TeacherPersona>(`${this.API_BASE}/persona/${userId}`, persona)
      .pipe(catchError(() => of(updated)));
  }

  /** 重置AI教师记忆 */
  resetMemory(userId: string): Observable<{ success: boolean }> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /memory/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    this.sessionSubject.next(null);
    return this.http
      .delete<{ success: boolean }>(`${this.API_BASE}/memory/${userId}`)
      .pipe(catchError(() => of({ success: true })));
  }

  // ==================== 【P3-B】实时推送设置 + 事件历史 ====================

  /** 获取 AI 教师实时推送设置 */
  getLiveSettings(userId: string): Observable<AiTeacherLiveSettings> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /live-settings/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    return this.http.get<AiTeacherLiveSettings>(
      `${this.API_BASE}/live-settings/${userId}`
    ).pipe(
      // 【P1 修复】统一超时兑底 → 本地默认设置
      timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
      tap((s) => {
        if (s) {
          this.liveService?.applySettings(s);
        }
      }),
      catchError(() => {
        const defaults: AiTeacherLiveSettings = {
          userId,
          updatedAt: new Date().toISOString(),
          ...DEFAULT_LIVE_SETTINGS,
        };
        this.liveService?.applySettings(defaults);
        return of(defaults);
      })
    );
  }

  /** 更新 AI 教师实时推送设置 */
  updateLiveSettings(
    userId: string,
    partial: Partial<AiTeacherLiveSettings>
  ): Observable<AiTeacherLiveSettings> {
    // 【NaN 防御】userId 非法时禁止拼接，避免请求打到 /live-settings/NaN 路径。
    if (this.isInvalidUserId(userId)) {
      return this.invalidUserId(userId);
    }
    // 后端使用 snake_case 字段名
    const payload = {
      enabled: partial.enabled,
      celebration_enabled: partial.celebrationEnabled,
      suggestion_enabled: partial.suggestionEnabled,
      nudge_enabled: partial.nudgeEnabled,
      dnd_start_hour: partial.dndStartHour,
      dnd_end_hour: partial.dndEndHour,
      max_per_hour: partial.maxPerHour,
      min_interval_seconds: partial.minIntervalSeconds,
    };
    return this.http.put<AiTeacherLiveSettings>(
      `${this.API_BASE}/live-settings/${userId}`,
      payload
    ).pipe(
      tap((s) => {
        if (s) {
          this.liveService?.applySettings(s);
        }
      }),
      catchError(() => {
        // 降级：本地保存
        const merged: AiTeacherLiveSettings = {
          userId,
          updatedAt: new Date().toISOString(),
          ...this.liveService?.getSettingsSnapshot(),
          ...partial,
        } as AiTeacherLiveSettings;
        this.liveService?.applySettings(merged);
        return of(merged);
      })
    );
  }

  /** 获取最近 AI 教师实时事件历史（断线后回放） */
  getLiveHistory(
    userId: string,
    limit: number = 20
  ): Observable<AiTeacherLiveEvent[]> {
    return this.http.get<{
      success: boolean;
      data: AiTeacherLiveEvent[];
      count: number;
    }>(`${this.API_BASE}/live-events/history/${userId}`, {
      params: { limit: String(limit) },
    }).pipe(
      timeout(AI_TEACHER_HTTP_TIMEOUT_MS),
      map((res) => res?.data || []),
      catchError(() => of([] as AiTeacherLiveEvent[]))
    );
  }

  // ==================== 私有辅助方法 ====================

  private getDefaultPersona(): TeacherPersona {
    return {
      userId: '',
      addressMode: 'name',
      nickname: '',
      languageStyle: 'lively',
      hintLevel: 'guided_thinking',
      encouragementFrequency: 'moderate',
      strictness: 'standard',
      emojiUsage: 'moderate',
    };
  }

  // eslint-disable-next-line max-lines-per-function
  private createMockProfile(userId: string): StudentLearningProfile {
    return {
      userId,
      displayName: '小明',
      gradeLevel: 'G7',
      ageGroup: '12-14',
      learningStyle: 'visual',
      preferredContentType: 'interactive',
      abilityDimensions: {
        programmingThinking: 68,
        algorithmAbility: 45,
        debuggingSkill: 52,
        projectPractice: 60,
        stemExperiment: 55,
        codeQuality: 40,
        independentCompletion: 65,
        questionQuality: 58,
      },
      interestPreferences: ['game_development', 'robotics', '3d_modeling'],
      knowledgeMastery: {
        python_basics: 0.85,
        conditions: 0.9,
        loops: 0.45,
        functions: 0.0,
        led_control: 1.0,
        sensors: 0.45,
      },
      totalStudyTimeMinutes: 11220,
      completedCoursesCount: 23,
      averageQuizScore: 72.5,
      currentStreakDays: 15,
      longestStreakDays: 30,
      weakPoints: [
        {
          knowledgePoint: 'range() 参数理解',
          mastery: 0.55,
          errorRate: 0.45,
          suggestion: 'Blockly 对照练习',
          lastDetected: new Date().toISOString(),
        },
        {
          knowledgePoint: '缩进规范',
          mastery: 0.7,
          errorRate: 0.3,
          suggestion: '代码格式化插件',
          lastDetected: new Date().toISOString(),
        },
        {
          knowledgePoint: '列表索引',
          mastery: 0.65,
          errorRate: 0.35,
          suggestion: '互动小测验',
          lastDetected: new Date().toISOString(),
        },
      ],
      errorPatterns: { indentation_error: 12, range_parameter: 8, list_index: 6 },
      attentionProfile: {
        averageFocusDurationMinutes: 25,
        tabSwitchFrequency: 2.3,
        hesitationTimeMs: 4500,
        trend: 'stable',
      },
      emotionalStates: [
        {
          timestamp: new Date().toISOString(),
          emotion: 'excited',
          source: 'dialogue',
          confidence: 0.8,
        },
      ],
      learningMilestones: [
        {
          id: 'm1',
          type: 'first_blockly',
          title: '初入编程',
          description: '完成第一个 Blockly 关卡',
          achievedAt: '2026-01-15T10:00:00Z',
        },
        {
          id: 'm2',
          type: 'python_intro',
          title: 'Python 入门',
          description: '完成 Python 基础课程',
          achievedAt: '2026-02-20T14:00:00Z',
        },
        {
          id: 'm3',
          type: 'first_independent_project',
          title: '首个独立项目',
          description: '猜数字游戏',
          achievedAt: '2026-03-10T16:00:00Z',
        },
        {
          id: 'm4',
          type: 'first_debug',
          title: '独立 Debug 成功',
          description: '修复 3 个以上错误',
          achievedAt: '2026-04-05T11:00:00Z',
        },
        {
          id: 'm5',
          type: 'breakthrough',
          title: '突破瓶颈',
          description: '循环正确率从 40% → 75%',
          achievedAt: '2026-04-28T09:00:00Z',
        },
      ],
      skillTree: this.createMockSkillTree(),
      personaSeed: '',
      learningGoals: ['掌握 Python 函数', '完成机器人项目', '学习 AI 基础'],
      createdAt: '2026-01-10T08:00:00Z',
      updatedAt: new Date().toISOString(),
    };
  }

  // eslint-disable-next-line max-lines-per-function
  private createMockSkillTree(): SkillTreeNode[] {
    return [
      {
        id: 'python_basics',
        name: 'Python 基础',
        category: 'python',
        progress: 0.6,
        status: 'learning',
        children: [
          {
            id: 'variables',
            name: '变量与数据类型',
            category: 'python',
            progress: 1.0,
            status: 'mastered',
            parent: 'python_basics',
          },
          {
            id: 'conditions',
            name: '条件判断',
            category: 'python',
            progress: 0.95,
            status: 'mastered',
            parent: 'python_basics',
          },
          {
            id: 'loops',
            name: '循环',
            category: 'python',
            progress: 0.6,
            status: 'learning',
            parent: 'python_basics',
          },
          {
            id: 'functions',
            name: '函数',
            category: 'python',
            progress: 0,
            status: 'not_started',
            parent: 'python_basics',
            unlockRequirement: 'loops',
          },
          {
            id: 'oop',
            name: '面向对象',
            category: 'python',
            progress: 0,
            status: 'not_started',
            parent: 'python_basics',
            unlockRequirement: 'functions',
          },
        ],
      },
      {
        id: 'stem_basics',
        name: 'STEM 实验',
        category: 'stem',
        progress: 0.5,
        status: 'learning',
        children: [
          {
            id: 'led_control',
            name: 'LED 控制',
            category: 'stem',
            progress: 1.0,
            status: 'mastered',
            parent: 'stem_basics',
          },
          {
            id: 'sensors',
            name: '传感器入门',
            category: 'stem',
            progress: 0.45,
            status: 'learning',
            parent: 'stem_basics',
          },
          {
            id: 'robotics',
            name: '机器人编程',
            category: 'stem',
            progress: 0,
            status: 'not_started',
            parent: 'stem_basics',
            unlockRequirement: 'sensors',
          },
        ],
      },
    ];
  }

  private createMockMemories(): LongTermMemory[] {
    return [
      {
        id: 'mem_1',
        userId: '',
        category: 'learning_summary',
        content: '学生完成循环入门测验，for/while 正确率 60%',
        tags: ['循环', '测验'],
        importance: 0.8,
        createdAt: new Date(Date.now() - 3 * 86400000).toISOString(),
        accessCount: 2,
        lastAccessedAt: new Date().toISOString(),
      },
      {
        id: 'mem_2',
        userId: '',
        category: 'key_dialogue',
        content: '学生提问 "为什么 for 和 while 有区别？"',
        tags: ['循环', '概念对比'],
        importance: 0.7,
        createdAt: new Date(Date.now() - 7 * 86400000).toISOString(),
        accessCount: 1,
        lastAccessedAt: new Date(Date.now() - 7 * 86400000).toISOString(),
      },
    ];
  }

  // eslint-disable-next-line max-lines-per-function
  private createMockGrowthTrajectory(months: number): GrowthTrajectory {
    const trend: AbilityTrendPoint[] = [];
    const now = new Date();
    for (let i = months - 1; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const factor = (months - i) / months;
      trend.push({
        date: date.toISOString().slice(0, 7),
        programmingThinking: Math.round(30 + factor * 40),
        algorithmAbility: Math.round(15 + factor * 30),
        debuggingSkill: Math.round(20 + factor * 35),
        projectPractice: Math.round(25 + factor * 35),
        stemExperiment: Math.round(20 + factor * 35),
        independentCompletion: Math.round(30 + factor * 35),
      });
    }

    return {
      userId: '',
      abilityTrend: trend,
      milestones: this.profileSubject.value?.learningMilestones ?? [],
      aiMonthlyMessage:
        '小明，这个月你进步非常大！从月初对循环一知半解，到现在已经能独立写出 for/while 两种循环了。特别让我惊喜的是，你在电路实验里独立完成了红绿灯项目。下个月我建议你重点攻克函数，加油！💪',
      statistics: {
        totalStudyHours: 187,
        completedCourses: 23,
        completedProjects: 8,
        totalQuestions: 156,
        questionQualityTrend: 'improving',
      },
      interestEvolution: [
        { period: '2026-01', interests: [{ name: '游戏开发', percentage: 60 }] },
        {
          period: '2026-03',
          interests: [
            { name: '机器人', percentage: 30 },
            { name: '游戏开发', percentage: 50 },
          ],
        },
        {
          period: '2026-05',
          interests: [
            { name: '机器人', percentage: 45 },
            { name: '游戏开发', percentage: 35 },
          ],
        },
      ],
      peerComparison: {
        peerAverages: {
          programmingThinking: 45,
          algorithmAbility: 28,
          debuggingSkill: 35,
          projectPractice: 38,
          stemExperiment: 32,
          independentCompletion: 40,
          totalStudyHours: 140,
          completedProjects: 5,
        },
        userAverages: {
          programmingThinking: 62,
          algorithmAbility: 35,
          debuggingSkill: 48,
          projectPractice: 50,
          stemExperiment: 45,
          independentCompletion: 55,
          totalStudyHours: 187,
          completedProjects: 8,
        },
        percentileRank: 72,
        beatRate: '超过 72% 的同龄学习者',
        dimensionLabels: {
          programmingThinking: '编程思维',
          algorithmAbility: '算法能力',
          debuggingSkill: '调试技能',
          projectPractice: '项目实践',
          stemExperiment: 'STEM实验',
          independentCompletion: '独立完成',
          totalStudyHours: '总学时',
          completedProjects: '完成项目',
        },
      },
    };
  }

  // eslint-disable-next-line max-lines-per-function
  private createMockSuggestions(): TeachingSuggestion[] {
    return [
      {
        id: 'sug_1',
        diagnosisType: 'prerequisite_missing',
        severity: 'warning',
        title: '前置知识缺失',
        description: '你正在学函数，但变量作用域还没完全掌握',
        suggestedAction: '先回顾变量作用域的概念，再继续学习函数',
        relatedKnowledgePoints: ['变量作用域', '函数'],
        recommendedCourses: ['python_scope_basics'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_2',
        diagnosisType: 'concept_confusion',
        severity: 'info',
        title: '概念混淆',
        description: '你最近出现了 range() 参数混淆的错误',
        suggestedAction: '对比练习：分别测试 range(5)、range(1,5)、range(1,5,2) 的输出',
        relatedKnowledgePoints: ['range()', 'for循环'],
        recommendedCourses: ['python_loops_fundamentals'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_3',
        diagnosisType: 'learning_plateau',
        severity: 'warning',
        title: '学习高原期',
        description: '循环的掌握度在 45% 停留了 3 天，没有明显进步',
        suggestedAction: '换个方式试试！先用 Blockly 搭 3 个循环积木，再翻译成 Python',
        relatedKnowledgePoints: ['循环', 'Blockly 转换'],
        recommendedCourses: ['blockly_to_python'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_4',
        diagnosisType: 'skill_imbalance',
        severity: 'info',
        title: '能力发展不均衡',
        description: '你的编程思维很强，但代码规范方面需要加强',
        suggestedAction: '建议安装代码格式化插件，并学习 Python PEP 8 规范',
        relatedKnowledgePoints: ['PEP 8', '代码规范'],
        recommendedCourses: ['python_code_style'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_5',
        diagnosisType: 'attention_decline',
        severity: 'warning',
        title: '注意力下降',
        description: '最近你的平均专注时长从 30 分钟降到了 20 分钟',
        suggestedAction: '建议适当休息，或尝试交互式更强的学习方式',
        relatedKnowledgePoints: [],
        recommendedCourses: ['fun_interactive_projects'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_6',
        diagnosisType: 'ai_overdependence',
        severity: 'info',
        title: '独立解题能力提醒',
        description: '最近你频繁向 AI 老师求助，独立完成率 40%',
        suggestedAction: '遇到问题先自己思考 2 分钟，借助提示尝试独立解决',
        relatedKnowledgePoints: ['问题拆解', '独立调试'],
        recommendedCourses: ['independent_debug_practice'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_7',
        diagnosisType: 'skill_imbalance',
        severity: 'critical',
        title: '编程能力严重失衡',
        description: '你的调试技能(25)远低于编程思维(75)，差距超过30分',
        suggestedAction: '建议暂停新知识学习，集中进行调试专项练习，完成「调试大师」挑战',
        relatedKnowledgePoints: ['断点调试', '错误追踪', '日志分析'],
        recommendedCourses: ['debugging_master', 'error_analysis_101'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
      {
        id: 'sug_8',
        diagnosisType: 'prerequisite_missing',
        severity: 'critical',
        title: '关键前置知识缺失',
        description: '函数章节前置知识(变量作用域)掌握率仅 15%，严重阻碍后续学习',
        suggestedAction: '立即暂停函数学习，退回至变量作用域章节完成所有练习并通过测试',
        relatedKnowledgePoints: ['变量作用域', '函数', '闭包'],
        recommendedCourses: ['python_scope_fundamentals', 'scope_quiz'],
        createdAt: new Date().toISOString(),
        isRead: false,
      },
    ];
  }

  private createMockDailySuggestion(): DailyLearningSuggestion {
    return {
      date: new Date().toISOString().slice(0, 10),
      greeting: '小明，下午好！☀️',
      yesterdayReview: '昨天你完成了 Python 循环练习，正确率 75%，比前天提升了 10%！',
      todayGoals: ['完成循环进阶练习', '尝试用 for 循环写一个小程序', '复习 range() 的三种用法'],
      weakPointReminder: [
        {
          knowledgePoint: 'range() 参数理解',
          mastery: 0.55,
          errorRate: 0.45,
          suggestion: 'Blockly 对照练习',
          lastDetected: new Date().toISOString(),
        },
      ],
      suggestedCourses: [
        { courseId: 'python_loops_advanced', reason: '因为你刚学完循环基础，进阶课程是自然延伸' },
      ],
      aiMessage: '💡 今日建议：先用 Blockly 搭 3 个循环积木，再翻译成 Python，你会更清楚！',
    };
  }

  private createMockKnowledgeState(): KnowledgeStateItem[] {
    return [
      {
        knowledgePoint: 'python_basics',
        mastery: 0.85,
        status: 'mastered',
        prerequisites: [],
        nextTopics: ['conditions', 'loops'],
        lastPracticed: new Date().toISOString(),
        practiceCount: 45,
      },
      {
        knowledgePoint: 'conditions',
        mastery: 0.9,
        status: 'mastered',
        prerequisites: ['python_basics'],
        nextTopics: ['loops'],
        lastPracticed: new Date().toISOString(),
        practiceCount: 30,
      },
      {
        knowledgePoint: 'loops',
        mastery: 0.45,
        status: 'learning',
        prerequisites: ['conditions'],
        nextTopics: ['functions'],
        lastPracticed: new Date().toISOString(),
        practiceCount: 18,
      },
      {
        knowledgePoint: 'functions',
        mastery: 0.0,
        status: 'not_started',
        prerequisites: ['loops'],
        nextTopics: ['oop'],
        lastPracticed: null,
        practiceCount: 0,
      },
    ];
  }

  private generateMockReply(message: string, persona: TeacherPersona): string {
    const emoji =
      persona.emojiUsage === 'heavy' ? '🎉😊💡' : persona.emojiUsage === 'moderate' ? '💡' : '';
    const address =
      persona.addressMode === 'nickname' && persona.nickname
        ? persona.nickname
        : persona.addressMode === 'classmate'
          ? '同学'
          : '小明';

    if (message.includes('循环') || message.includes('loop')) {
      return `${address}，循环是一个很重要的概念！${emoji} 记得上次你用动画学懂了条件判断吗？循环其实很像条件判断的重复版。要不要先在 Blockly 里试试循环积木？`;
    }
    return `${address}，这是个好问题！${emoji} 让我帮你理清思路，你觉得可以从哪个角度来思考呢？`;
  }
}
