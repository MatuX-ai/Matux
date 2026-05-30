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

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

import {
  AITeacherChatRequest,
  AITeacherChatResponse,
  AbilityTrendPoint,
  ChatMessage,
  DailyLearningSuggestion,
  GrowthTrajectory,
  KnowledgeStateItem,
  LearningProfileUpdateRequest,
  LearningStyle,
  LongTermMemory,
  SessionMemory,
  SkillTreeNode,
  StudentLearningProfile,
  TeachingSuggestion,
  TeacherPersona,
} from '../models/ai-teacher.models';

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

  constructor(private http: HttpClient) {}

  // ==================== 学习画像 ====================

  /** 获取学生学习画像 */
  getProfile(userId: string): Observable<StudentLearningProfile> {
    return this.http.get<StudentLearningProfile>(`${this.API_BASE}/profile/${userId}`).pipe(
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
  updateProfile(userId: string, update: LearningProfileUpdateRequest): Observable<StudentLearningProfile> {
    return this.http.patch<StudentLearningProfile>(`${this.API_BASE}/profile/${userId}`, update).pipe(
      tap((profile) => this.profileSubject.next(profile)),
      catchError(() => {
        // 本地更新
        const current = this.profileSubject.value;
        if (current) {
          const updated = { ...current, ...update, updatedAt: new Date().toISOString() };
          this.profileSubject.next(updated as StudentLearningProfile);
          return of(updated as StudentLearningProfile);
        }
        return of(current!);
      })
    );
  }

  /** 生成画像摘要（供AI教师prompt使用） */
  generatePersonaSeed(profile: StudentLearningProfile): string {
    const styleMap: Record<LearningStyle, string> = {
      visual: '视觉型',
      auditory: '听觉型',
      reading: '读写型',
      kinesthetic: '动觉型',
    };
    const weakPointsStr = profile.weakPoints
      .slice(0, 3)
      .map((w) => `${w.knowledgePoint}(${Math.round(w.mastery * 100)}%)`)
      .join('、');

    return [
      `${profile.displayName}，${profile.gradeLevel}，${styleMap[profile.learningStyle]}学习者`,
      `编程思维${profile.abilityDimensions.programmingThinking}/100，`,
      `独立完成率${profile.abilityDimensions.independentCompletion}%`,
      weakPointsStr ? `薄弱环节：${weakPointsStr}` : '',
      `连续学习${profile.currentStreakDays}天`,
    ].filter(Boolean).join('。');
  }

  // ==================== 上下文记忆 ====================

  /** 获取长期记忆 */
  getLongTermMemories(userId: string, query?: string): Observable<LongTermMemory[]> {
    const params: Record<string, string> = query ? { query } : {};
    return this.http.get<LongTermMemory[]>(`${this.API_BASE}/memory/${userId}/long-term`, { params }).pipe(
      catchError(() => of(this.createMockMemories()))
    );
  }

  /** 保存长期记忆 */
  saveLongTermMemory(userId: string, memory: Omit<LongTermMemory, 'id' | 'createdAt' | 'accessCount' | 'lastAccessedAt'>): Observable<LongTermMemory> {
    return this.http.post<LongTermMemory>(`${this.API_BASE}/memory/${userId}/long-term`, memory).pipe(
      catchError(() => of({ ...memory, id: `mem_${Date.now()}`, createdAt: new Date().toISOString(), accessCount: 0, lastAccessedAt: new Date().toISOString() } as LongTermMemory))
    );
  }

  /** 获取/创建会话记忆 */
  getOrCreateSession(userId: string): Observable<SessionMemory> {
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
  chat(request: AITeacherChatRequest): Observable<AITeacherChatResponse> {
    const profile = this.profileSubject.value;
    const persona = this.personaSubject.value;

    // 注入画像和人格到请求
    const enhancedRequest = {
      ...request,
      profileSeed: profile ? this.generatePersonaSeed(profile) : '',
      persona: {
        addressMode: persona.addressMode,
        languageStyle: persona.languageStyle,
        hintLevel: persona.hintLevel,
        encouragementFrequency: persona.encouragementFrequency,
        emojiUsage: persona.emojiUsage,
      },
    };

    return this.http.post<AITeacherChatResponse>(`${this.API_BASE}/chat`, enhancedRequest).pipe(
      tap((response) => {
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
              knowledgeUsed: response.knowledgeUsed,
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
      catchError(() => {
        // Mock响应降级
        const mockResponse: AITeacherChatResponse = {
          reply: this.generateMockReply(request.message, persona),
          sessionId: request.sessionId,
          emotionDetected: 'neutral',
          memoriesReferenced: [],
          knowledgeUsed: false,
          suggestions: [],
          model: 'mock',
          confidence: 0.7,
          inferenceTimeMs: 200,
        };
        return of(mockResponse);
      })
    );
  }

  // ==================== 成长轨迹 ====================

  /** 获取成长轨迹 */
  getGrowthTrajectory(userId: string, months: number = 6): Observable<GrowthTrajectory> {
    return this.http.get<GrowthTrajectory>(`${this.API_BASE}/growth/${userId}`, { params: { months } }).pipe(
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
    return this.http.get<TeachingSuggestion[]>(`${this.API_BASE}/suggestions/${userId}`).pipe(
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
    return this.http.get<DailyLearningSuggestion>(`${this.API_BASE}/daily-suggestion/${userId}`).pipe(
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
          current.map((s) => s.id === suggestionId ? { ...s, isRead: true } : s)
        );
      }),
      catchError(() => of(void 0))
    );
  }

  // ==================== 知识状态 ====================

  /** 获取知识状态 */
  getKnowledgeState(userId: string): Observable<KnowledgeStateItem[]> {
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
    return this.http.get<TeacherPersona>(`${this.API_BASE}/persona/${userId}`).pipe(
      tap((persona) => this.personaSubject.next(persona)),
      catchError(() => of(this.personaSubject.value))
    );
  }

  /** 更新人格配置 */
  updatePersona(userId: string, persona: Partial<TeacherPersona>): Observable<TeacherPersona> {
    const updated = { ...this.personaSubject.value, ...persona };
    this.personaSubject.next(updated);
    return this.http.patch<TeacherPersona>(`${this.API_BASE}/persona/${userId}`, persona).pipe(
      catchError(() => of(updated))
    );
  }

  /** 重置AI教师记忆 */
  resetMemory(userId: string): Observable<{ success: boolean }> {
    this.sessionSubject.next(null);
    return this.http.delete<{ success: boolean }>(`${this.API_BASE}/memory/${userId}`).pipe(
      catchError(() => of({ success: true }))
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
        'python_basics': 0.85,
        'conditions': 0.90,
        'loops': 0.45,
        'functions': 0.0,
        'led_control': 1.0,
        'sensors': 0.45,
      },
      totalStudyTimeMinutes: 11220,
      completedCoursesCount: 23,
      averageQuizScore: 72.5,
      currentStreakDays: 15,
      longestStreakDays: 30,
      weakPoints: [
        { knowledgePoint: 'range() 参数理解', mastery: 0.55, errorRate: 0.45, suggestion: 'Blockly 对照练习', lastDetected: new Date().toISOString() },
        { knowledgePoint: '缩进规范', mastery: 0.70, errorRate: 0.30, suggestion: '代码格式化插件', lastDetected: new Date().toISOString() },
        { knowledgePoint: '列表索引', mastery: 0.65, errorRate: 0.35, suggestion: '互动小测验', lastDetected: new Date().toISOString() },
      ],
      errorPatterns: { 'indentation_error': 12, 'range_parameter': 8, 'list_index': 6 },
      attentionProfile: {
        averageFocusDurationMinutes: 25,
        tabSwitchFrequency: 2.3,
        hesitationTimeMs: 4500,
        trend: 'stable',
      },
      emotionalStates: [
        { timestamp: new Date().toISOString(), emotion: 'excited', source: 'dialogue', confidence: 0.8 },
      ],
      learningMilestones: [
        { id: 'm1', type: 'first_blockly', title: '初入编程', description: '完成第一个 Blockly 关卡', achievedAt: '2026-01-15T10:00:00Z' },
        { id: 'm2', type: 'python_intro', title: 'Python 入门', description: '完成 Python 基础课程', achievedAt: '2026-02-20T14:00:00Z' },
        { id: 'm3', type: 'first_independent_project', title: '首个独立项目', description: '猜数字游戏', achievedAt: '2026-03-10T16:00:00Z' },
        { id: 'm4', type: 'first_debug', title: '独立 Debug 成功', description: '修复 3 个以上错误', achievedAt: '2026-04-05T11:00:00Z' },
        { id: 'm5', type: 'breakthrough', title: '突破瓶颈', description: '循环正确率从 40% → 75%', achievedAt: '2026-04-28T09:00:00Z' },
      ],
      skillTree: this.createMockSkillTree(),
      personaSeed: '',
      learningGoals: ['掌握 Python 函数', '完成机器人项目', '学习 AI 基础'],
      createdAt: '2026-01-10T08:00:00Z',
      updatedAt: new Date().toISOString(),
    };
  }

  private createMockSkillTree(): SkillTreeNode[] {
    return [
      {
        id: 'python_basics', name: 'Python 基础', category: 'python', progress: 0.6, status: 'learning',
        children: [
          { id: 'variables', name: '变量与数据类型', category: 'python', progress: 1.0, status: 'mastered', parent: 'python_basics' },
          { id: 'conditions', name: '条件判断', category: 'python', progress: 0.95, status: 'mastered', parent: 'python_basics' },
          { id: 'loops', name: '循环', category: 'python', progress: 0.6, status: 'learning', parent: 'python_basics' },
          { id: 'functions', name: '函数', category: 'python', progress: 0, status: 'not_started', parent: 'python_basics', unlockRequirement: 'loops' },
          { id: 'oop', name: '面向对象', category: 'python', progress: 0, status: 'not_started', parent: 'python_basics', unlockRequirement: 'functions' },
        ],
      },
      {
        id: 'stem_basics', name: 'STEM 实验', category: 'stem', progress: 0.5, status: 'learning',
        children: [
          { id: 'led_control', name: 'LED 控制', category: 'stem', progress: 1.0, status: 'mastered', parent: 'stem_basics' },
          { id: 'sensors', name: '传感器入门', category: 'stem', progress: 0.45, status: 'learning', parent: 'stem_basics' },
          { id: 'robotics', name: '机器人编程', category: 'stem', progress: 0, status: 'not_started', parent: 'stem_basics', unlockRequirement: 'sensors' },
        ],
      },
    ];
  }

  private createMockMemories(): LongTermMemory[] {
    return [
      {
        id: 'mem_1', userId: '', category: 'learning_summary',
        content: '学生完成循环入门测验，for/while 正确率 60%',
        tags: ['循环', '测验'], importance: 0.8,
        createdAt: new Date(Date.now() - 3 * 86400000).toISOString(),
        accessCount: 2, lastAccessedAt: new Date().toISOString(),
      },
      {
        id: 'mem_2', userId: '', category: 'key_dialogue',
        content: '学生提问 "为什么 for 和 while 有区别？"',
        tags: ['循环', '概念对比'], importance: 0.7,
        createdAt: new Date(Date.now() - 7 * 86400000).toISOString(),
        accessCount: 1, lastAccessedAt: new Date(Date.now() - 7 * 86400000).toISOString(),
      },
    ];
  }

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
      aiMonthlyMessage: '小明，这个月你进步非常大！从月初对循环一知半解，到现在已经能独立写出 for/while 两种循环了。特别让我惊喜的是，你在电路实验里独立完成了红绿灯项目。下个月我建议你重点攻克函数，加油！💪',
      statistics: {
        totalStudyHours: 187,
        completedCourses: 23,
        completedProjects: 8,
        totalQuestions: 156,
        questionQualityTrend: 'improving',
      },
      interestEvolution: [
        { period: '2026-01', interests: [{ name: '游戏开发', percentage: 60 }] },
        { period: '2026-03', interests: [{ name: '机器人', percentage: 30 }, { name: '游戏开发', percentage: 50 }] },
        { period: '2026-05', interests: [{ name: '机器人', percentage: 45 }, { name: '游戏开发', percentage: 35 }] },
      ],
    };
  }

  private createMockSuggestions(): TeachingSuggestion[] {
    return [
      {
        id: 'sug_1', diagnosisType: 'prerequisite_missing', severity: 'warning',
        title: '前置知识缺失', description: '你正在学函数，但变量作用域还没掌握',
        suggestedAction: '先回顾变量作用域的概念',
        relatedKnowledgePoints: ['变量作用域', '函数'],
        recommendedCourses: ['python_scope_basics'],
        createdAt: new Date().toISOString(), isRead: false,
      },
      {
        id: 'sug_2', diagnosisType: 'concept_confusion', severity: 'info',
        title: '概念混淆', description: '你好像把 list 和 tuple 搞混了',
        suggestedAction: '对比练习：创建 list 和 tuple，尝试修改元素',
        relatedKnowledgePoints: ['list', 'tuple'],
        recommendedCourses: ['python_data_structures'],
        createdAt: new Date().toISOString(), isRead: false,
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
        { knowledgePoint: 'range() 参数理解', mastery: 0.55, errorRate: 0.45, suggestion: 'Blockly 对照练习', lastDetected: new Date().toISOString() },
      ],
      suggestedCourses: [
        { courseId: 'python_loops_advanced', reason: '因为你刚学完循环基础，进阶课程是自然延伸' },
      ],
      aiMessage: '💡 今日建议：先用 Blockly 搭 3 个循环积木，再翻译成 Python，你会更清楚！',
    };
  }

  private createMockKnowledgeState(): KnowledgeStateItem[] {
    return [
      { knowledgePoint: 'python_basics', mastery: 0.85, status: 'mastered', prerequisites: [], nextTopics: ['conditions', 'loops'], lastPracticed: new Date().toISOString(), practiceCount: 45 },
      { knowledgePoint: 'conditions', mastery: 0.90, status: 'mastered', prerequisites: ['python_basics'], nextTopics: ['loops'], lastPracticed: new Date().toISOString(), practiceCount: 30 },
      { knowledgePoint: 'loops', mastery: 0.45, status: 'learning', prerequisites: ['conditions'], nextTopics: ['functions'], lastPracticed: new Date().toISOString(), practiceCount: 18 },
      { knowledgePoint: 'functions', mastery: 0.0, status: 'not_started', prerequisites: ['loops'], nextTopics: ['oop'], lastPracticed: null, practiceCount: 0 },
    ];
  }

  private generateMockReply(message: string, persona: TeacherPersona): string {
    const emoji = persona.emojiUsage === 'heavy' ? '🎉😊💡' : persona.emojiUsage === 'moderate' ? '💡' : '';
    const address = persona.addressMode === 'nickname' && persona.nickname
      ? persona.nickname
      : persona.addressMode === 'classmate' ? '同学' : '小明';

    if (message.includes('循环') || message.includes('loop')) {
      return `${address}，循环是一个很重要的概念！${emoji} 记得上次你用动画学懂了条件判断吗？循环其实很像条件判断的重复版。要不要先在 Blockly 里试试循环积木？`;
    }
    return `${address}，这是个好问题！${emoji} 让我帮你理清思路，你觉得可以从哪个角度来思考呢？`;
  }
}
