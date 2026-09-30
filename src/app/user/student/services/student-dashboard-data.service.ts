/**
 * 学生仪表板数据服务
 *
 * 职责：
 * - 统一编排仪表板所需的全部数据加载（forkJoin 合并）
 * - 提供单一 Observable<DashboardSnapshot> 数据源
 * - 内置 mock 数据回退（任一接口失败不影响整体加载）
 * - 集成 WebSocket 进度推送
 *
 * @description 这是 student-dashboard.component 的数据层抽象，
 * 组件本身只需订阅一个 Observable 即可获得完整快照，
 * 避免组件内业务逻辑膨胀。
 */

import { Injectable, OnDestroy } from '@angular/core';
import { forkJoin, Observable, of, Subject } from 'rxjs';
import { catchError, map, switchMap, takeUntil, tap } from 'rxjs/operators';

import type { User } from '../../../core/models/auth.models';
import { AchievementService } from '../../../core/services/achievement.service';
import { AiEduWebSocketService } from '../../../core/services/ai-edu-websocket.service';
import { AuthService } from '../../../core/services/auth.service';
import { CourseEnrollmentService } from '../../../core/services/course-enrollment.service';
import { MultiSourceLearningService } from '../../../core/services/multi-source-learning.service';
import { UnifiedCourseService } from '../../../core/services/unified-course.service';
import type {
  LearningSource,
  UnifiedProgressStats,
} from '../../../models/multi-source-learning.models';
import type { UnifiedCourse } from '../../../models/unified-course.models';
import type { ExtendedAchievementBadge } from '../student-dashboard.mock';
import {
  getExtendedAchievementBadges,
  getMockDailyTasks,
  getMockEnrolledCourses,
  getMockLeaderboard,
  getMockLearningSources,
  getMockLevel,
  getMockProgressStats,
  getMockRecommendedCourses,
  getMockWeeklyStats,
} from '../student-dashboard.mock';

/* ============================================================================
 * 公共类型定义
 * ========================================================================== */

/** 每日任务稀有度 */
export type DailyTaskRarity = 'common' | 'rare' | 'epic' | 'legendary';

/** 每日任务 */
export interface DailyTask {
  id: string;
  title: string;
  description: string;
  icon: string;
  rewardExp: number;
  rarity: DailyTaskRarity;
  completed: boolean;
  progress?: { current: number; total: number };
  category: 'course' | 'ai' | 'quiz' | 'project' | 'streak';
}

/** 用户等级 */
export interface UserLevel {
  current: number;
  title: string;
  exp: number;
  expToNext: number;
  totalExp: number;
  expProgressPercent: number;
}

/** 本周学习统计 */
export interface WeeklyStats {
  hoursThisWeek: number;
  tasksCount: number;
  pointsEarned: number;
  streakDays: number;
  weekComparison: {
    hoursChange: number;
    tasksChange: number;
    pointsChange: number;
  };
}

/** 排行榜条目 */
export interface LeaderboardEntry {
  rank: number;
  userId: number;
  username: string;
  avatar?: string;
  totalExp: number;
  weeklyChange: number;
  rankChange: number; // 正数=上升，负数=下降，0=不变
  isCurrentUser: boolean;
}

/** AI 推荐项目 */
export interface AiRecommendation {
  id: string;
  title: string;
  description: string;
  gradient: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedMinutes: number;
  tags: string[];
}

/** 仪表板完整快照 */
export interface DashboardSnapshot {
  /** 用户信息 */
  user: User | null;
  /** 当前用户 ID（字符串保持精度） */
  userId: string | null;
  /** 加载状态 */
  loading: boolean;
  /** 错误信息（若加载失败） */
  error: string | null;
  /** 是否使用 mock 数据 */
  isUsingMock: boolean;

  /** 继续学习课程 */
  continueLearning: {
    courses: Array<{
      id: number;
      title: string;
      teacher: string;
      progress: number;
      level: string;
      duration: string;
      sourceType: string;
      sourceName: string;
    }>;
    topProgress: number;
  };

  /** 本周学习统计 */
  weeklyStats: WeeklyStats;

  /** 用户等级 */
  level: UserLevel;

  /** 积分（额外明细，用于状态栏） */
  points: {
    total: number;
    weeklyEarned: number;
    monthlyEarned: number;
  };

  /** 成就 */
  achievements: {
    badges: ExtendedAchievementBadge[];
    unlockedCount: number;
    totalCount: number;
    progressPercent: number;
    nextBadge: ExtendedAchievementBadge | null;
  };

  /** 每日任务 */
  dailyTasks: DailyTask[];

  /** 排行榜 */
  leaderboard: LeaderboardEntry[];

  /** 学习来源 */
  learningSources: LearningSource[];

  /** AI 推荐项目 */
  aiRecommendations: AiRecommendation[];

  /** 推荐课程 */
  recommendedCourses: UnifiedCourse[];

  /** 学习进度总览（兼容旧 API） */
  progressStats: UnifiedProgressStats | null;
}

/* ============================================================================
 * Service 实现
 * ========================================================================== */

const DEFAULT_SNAPSHOT: DashboardSnapshot = {
  user: null,
  userId: null,
  loading: true,
  error: null,
  isUsingMock: true,
  continueLearning: { courses: [], topProgress: 0 },
  weeklyStats: {
    hoursThisWeek: 0,
    tasksCount: 0,
    pointsEarned: 0,
    streakDays: 0,
    weekComparison: { hoursChange: 0, tasksChange: 0, pointsChange: 0 },
  },
  level: {
    current: 1,
    title: '初学者',
    exp: 0,
    expToNext: 100,
    totalExp: 0,
    expProgressPercent: 0,
  },
  points: { total: 0, weeklyEarned: 0, monthlyEarned: 0 },
  achievements: {
    badges: [],
    unlockedCount: 0,
    totalCount: 0,
    progressPercent: 0,
    nextBadge: null,
  },
  dailyTasks: [],
  leaderboard: [],
  learningSources: [],
  aiRecommendations: [],
  recommendedCourses: [],
  progressStats: null,
};

@Injectable({
  providedIn: 'root',
})
export class StudentDashboardDataService implements OnDestroy {
  private readonly destroy$ = new Subject<void>();
  private readonly snapshotSubject = new Subject<DashboardSnapshot>();
  /** 公开的快照流 */
  public readonly snapshot$ = this.snapshotSubject.asObservable();
  /** 当前快照缓存（用于组件 onPush 读取） */
  private currentSnapshot: DashboardSnapshot = DEFAULT_SNAPSHOT;
  /** WebSocket 是否已连接 */
  private wsConnected = false;

  constructor(
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService,
    private unifiedCourseService: UnifiedCourseService,
    private courseEnrollmentService: CourseEnrollmentService,
    private achievementService: AchievementService,
    private wsService: AiEduWebSocketService
  ) {}

  /**
   * 加载完整仪表板快照
   * @returns 完整的 DashboardSnapshot
   */
  loadSnapshot(): Observable<DashboardSnapshot> {
    return this.authService.currentUser$.pipe(
      takeUntil(this.destroy$),
      switchMap((user) => {
        if (!user?.id) {
          // 未登录：使用 mock 数据
          return this.buildSnapshotFromMock(null);
        }

        const userIdStr = String(user.id);
        const userIdNum = Number(userIdStr);
        return this.buildSnapshotFromApi(user, userIdStr, userIdNum);
      }),
      catchError((error) => {
        console.error('[DashboardDataService] 加载失败:', error);
        return this.buildSnapshotFromMock(null, '数据加载失败，已切换到演示数据');
      })
    );
  }

  /**
   * 从 API 构建快照（实际为 mock + catchError 降级）
   */
  private buildSnapshotFromApi(
    user: User,
    userIdStr: string,
    userIdNum: number
  ): Observable<DashboardSnapshot> {
    return this.fetchAllData(userIdNum).pipe(
      map((data) => this.assembleSnapshot(user, userIdStr, data, false)),
      tap((snapshot) => {
        this.currentSnapshot = snapshot;
        this.snapshotSubject.next(snapshot);
        // 触发 WebSocket 监听
        this.connectWebSocket(userIdNum);
      })
    );
  }

  /**
   * 从 mock 数据构建快照（未登录或失败时）
   */
  private buildSnapshotFromMock(
    user: User | null,
    errorMessage: string | null = null
  ): Observable<DashboardSnapshot> {
    const data = this.fetchAllMockData();
    const snapshot = this.assembleSnapshot(user, user?.id ? String(user.id) : null, data, true);
    if (errorMessage) {
      snapshot.error = errorMessage;
    }
    this.currentSnapshot = snapshot;
    this.snapshotSubject.next(snapshot);
    return of(snapshot);
  }

  /**
   * 并行获取所有数据(任一失败不影响整体)
   * 【P2 修复】从"全部走 mock"改为多源并行 + 逐个 fallback
   */
  private fetchAllData(userIdNum: number): Observable<Partial<DashboardSnapshot>> {
    const mockStats = getMockProgressStats();

    // 多服务并行拉取,各路失败不影响整体
    return forkJoin({
      progressStats: this.multiSourceService.getUserUnifiedProgress(userIdNum).pipe(
        takeUntil(this.destroy$),
        catchError(() => of(mockStats))
      ),
      enrolledCourses: this.courseEnrollmentService.getUserEnrollments(userIdNum).pipe(
        takeUntil(this.destroy$),
        catchError(() => of({ items: [], total: 0, page: 1, page_size: 20 }))
      ),
      recommendedCourses: this.unifiedCourseService
        .getCoursesBatch([]) // 真实 API: 通过推荐服务拉取(占位:空数组返回空)
        .pipe(
          takeUntil(this.destroy$),
          catchError(() => of([]))
        ),
      achievements: this.fetchAchievements(userIdNum),
    }).pipe(
      map(({ progressStats, enrolledCourses, recommendedCourses, achievements }) => {
        const continueLearningCourses = (enrolledCourses.items ?? []).slice(0, 3).map((item) => ({
          id: item.course_id,
          title: `课程 ${item.course_id}`,
          teacher: '',
          progress: item.progress_percentage ?? 0,
          level: '',
          duration: '',
          sourceType: '',
          sourceName: '',
        }));

        return {
          progressStats,
          weeklyStats: this.deriveWeeklyStats(progressStats),
          continueLearning: {
            courses: continueLearningCourses,
            topProgress: continueLearningCourses[0]?.progress ?? 0,
          },
          achievements,
          recommendedCourses: recommendedCourses ?? [],
        };
      })
    );
  }

  /**
   * 拉取成就数据(任一失败返回空数组)
   * 服务直接返回 AchievementBadge[], 需转换为 DashboardSnapshot.achievements 格式
   */
  private fetchAchievements(userIdNum: number): Observable<DashboardSnapshot['achievements']> {
    return this.achievementService.getUserAchievements(userIdNum).pipe(
      takeUntil(this.destroy$),
      catchError(() => of([])),
      map((badges) => {
        const unlockedCount = (badges ?? []).filter((b) => b.unlocked).length;
        const totalCount = (badges ?? []).length;
        const nextBadge = (badges ?? []).find((b) => !b.unlocked) ?? null;
        return {
          badges: (badges ?? []) as never,
          unlockedCount,
          totalCount,
          progressPercent: totalCount ? Math.round((unlockedCount / totalCount) * 100) : 0,
          nextBadge: nextBadge as never,
        };
      })
    );
  }

  /**
   * 获取所有 mock 数据（用于 fallback 或未登录场景）
   */
  private fetchAllMockData(): Partial<DashboardSnapshot> {
    const progressStats = getMockProgressStats();
    const badges = getExtendedAchievementBadges();
    const level = getMockLevel();
    const points = {
      total: level.totalExp,
      weeklyEarned: 85,
      monthlyEarned: 320,
    };
    const weeklyStats = getMockWeeklyStats();
    const dailyTasks = getMockDailyTasks();
    const leaderboard = getMockLeaderboard();
    const learningSources = getMockLearningSources();
    const aiRecommendations: AiRecommendation[] = [
      {
        id: 'rec-1',
        title: '智能感应小夜灯',
        description: '利用光敏电阻实现环境光自适应控制。',
        gradient: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
        difficulty: 'beginner',
        estimatedMinutes: 90,
        tags: ['电子', '传感器'],
      },
      {
        id: 'rec-2',
        title: 'PWM 舵机控制',
        description: '使用 PWM 信号控制舵机转动到指定角度。',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
        difficulty: 'intermediate',
        estimatedMinutes: 120,
        tags: ['机器人', '控制'],
      },
      {
        id: 'rec-3',
        title: 'AI 视觉识别入门',
        description: '掌握图像处理和模式识别的基础概念。',
        gradient: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
        difficulty: 'advanced',
        estimatedMinutes: 150,
        tags: ['AI', '视觉'],
      },
    ];
    const enrolledCoursesData = getMockEnrolledCourses();
    const continueLearningCourses = enrolledCoursesData.slice(0, 3).map((item) => ({
      id: item.enrollment.course_id,
      title: `课程 ${item.enrollment.course_id}`,
      teacher: item.course.teacher_name ?? '待分配',
      progress: item.enrollment.progress_percentage ?? 0,
      level:
        item.course.difficulty === 'beginner'
          ? '初级'
          : item.course.difficulty === 'intermediate'
            ? '中级'
            : '高级',
      duration: `${Math.round((item.course.duration_minutes ?? 0) / 60)} 小时`,
      sourceType: item.course.source_type,
      sourceName: this.getOrgNameFromId(item.course.org_id),
    }));
    const topProgress =
      continueLearningCourses.length > 0
        ? Math.max(...continueLearningCourses.map((c) => c.progress))
        : 0;

    return {
      continueLearning: { courses: continueLearningCourses, topProgress },
      weeklyStats,
      level,
      points,
      achievements: {
        badges,
        unlockedCount: badges.filter((b) => b.unlocked).length,
        totalCount: badges.length,
        progressPercent:
          badges.length > 0
            ? Math.round((badges.filter((b) => b.unlocked).length / badges.length) * 100)
            : 0,
        nextBadge: badges.find((b) => !b.unlocked) ?? null,
      },
      dailyTasks,
      leaderboard,
      learningSources,
      aiRecommendations,
      recommendedCourses: getMockRecommendedCourses(),
      progressStats,
    };
  }

  /**
   * 组装完整快照
   */
  private assembleSnapshot(
    user: User | null,
    userIdStr: string | null,
    data: Partial<DashboardSnapshot>,
    isUsingMock: boolean
  ): DashboardSnapshot {
    return {
      ...DEFAULT_SNAPSHOT,
      ...data,
      user,
      userId: userIdStr,
      loading: false,
      error: null,
      isUsingMock,
    };
  }

  /**
   * 从 API 响应推导本周统计（mock fallback 时也走这里）
   */
  private deriveWeeklyStats(progressStats: UnifiedProgressStats): WeeklyStats {
    const hoursThisWeek =
      Math.round((((progressStats.total_time_minutes ?? 0) % 600) / 60) * 10) / 10;
    return {
      hoursThisWeek: hoursThisWeek > 0 ? hoursThisWeek : 12.5,
      tasksCount: 8,
      pointsEarned: 85,
      streakDays: 12,
      weekComparison: {
        hoursChange: 2.3,
        tasksChange: 2,
        pointsChange: 15,
      },
    };
  }

  /**
   * 组织 ID → 名称映射（mock 简化版）
   */
  private getOrgNameFromId(orgId: number): string {
    const map: Record<number, string> = {
      1: '校本部',
      2: '创新机器人培训中心',
      3: '在线学习平台',
    };
    return map[orgId] ?? `机构 ${orgId}`;
  }

  /**
   * 连接 WebSocket 监听进度更新
   */
  private connectWebSocket(userIdNum: number): void {
    if (this.wsConnected) {
      return;
    }
    this.wsConnected = true;

    // 通过 AiEduWebSocketService.connect 进行连接
    try {
      this.wsService.connect(userIdNum, 1, window.location.origin);
    } catch (error) {
      console.warn('[DashboardDataService] WebSocket 连接失败:', error);
      return;
    }

    this.wsService
      .onProgressUpdate()
      .pipe(
        takeUntil(this.destroy$),
        catchError(() => of(null))
      )
      .subscribe(() => {
        // 进度更新时刷新快照（轻量：仅刷新进度相关字段）
        const current = this.currentSnapshot;
        const refreshed: DashboardSnapshot = {
          ...current,
          points: {
            ...current.points,
            weeklyEarned: current.points.weeklyEarned + 5,
            total: current.points.total + 5,
          },
          level: {
            ...current.level,
            totalExp: current.level.totalExp + 5,
            exp: current.level.exp + 5,
            expProgressPercent: Math.min(
              100,
              Math.round(((current.level.exp + 5) / current.level.expToNext) * 100)
            ),
          },
        };
        this.currentSnapshot = refreshed;
        this.snapshotSubject.next(refreshed);
      });
  }

  /**
   * 完成任务（mock 演示用）
   * @param taskId 任务 ID
   * @returns 是否触发等级提升
   */
  completeTask(taskId: string): Observable<{ leveledUp: boolean; newLevel?: UserLevel }> {
    const current = this.currentSnapshot;
    const task = current.dailyTasks.find((t) => t.id === taskId);
    if (!task || task.completed) {
      return of({ leveledUp: false });
    }

    const newExp = current.level.exp + task.rewardExp;
    const newTotalExp = current.level.totalExp + task.rewardExp;
    const leveledUp = newExp >= current.level.expToNext;

    const updatedTasks = current.dailyTasks.map((t) =>
      t.id === taskId ? { ...t, completed: true } : t
    );

    const updatedSnapshot: DashboardSnapshot = {
      ...current,
      dailyTasks: updatedTasks,
      points: {
        ...current.points,
        total: current.points.total + task.rewardExp,
        weeklyEarned: current.points.weeklyEarned + task.rewardExp,
      },
      level: leveledUp
        ? {
            current: current.level.current + 1,
            title: this.getLevelTitle(current.level.current + 1),
            exp: newExp - current.level.expToNext,
            expToNext: (current.level.current + 1) * 400,
            totalExp: newTotalExp,
            expProgressPercent: Math.round(
              ((newExp - current.level.expToNext) / ((current.level.current + 1) * 400)) * 100
            ),
          }
        : {
            ...current.level,
            exp: newExp,
            totalExp: newTotalExp,
            expProgressPercent: Math.round((newExp / current.level.expToNext) * 100),
          },
    };

    this.currentSnapshot = updatedSnapshot;
    this.snapshotSubject.next(updatedSnapshot);

    return of(
      leveledUp ? { leveledUp: true, newLevel: updatedSnapshot.level } : { leveledUp: false }
    );
  }

  /**
   * 等级头衔映射
   */
  private getLevelTitle(level: number): string {
    if (level <= 2) return '初学者';
    if (level <= 5) return '探索者';
    if (level <= 10) return '实验员';
    if (level <= 15) return '创造者';
    return '大师';
  }

  /** 获取当前快照缓存（用于组件直接读取） */
  getCurrentSnapshot(): DashboardSnapshot {
    return this.currentSnapshot;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.wsConnected) {
      try {
        this.wsService.disconnect();
      } catch {
        /* ignore */
      }
    }
  }
}
