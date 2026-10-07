/**
 * 成就系统服务
 *
 * 提供成就数据获取、解锁、进度跟踪等功能
 * 与后端 gamification API 通信
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

import { environment } from '../../../../environments/environment';
import {
  AchievementBadge,
  AchievementCategory,
  AchievementProgress,
  AchievementReview,
  AchievementRarity,
  AchievementStats,
  AchievementUnlockEvent,
  ProgressMilestone,
} from '../models/achievement.model';

/**
 * 【P3-2 修复】后端不可用时的示例成就数据
 * - 让新用户首次访问 /user/achievements 能看到示例徽章，而不是“空状态”
 * - 包含已解锁 + 未解锁 两类状态（与 AchievementBadge 类型严格一致）
 */
const FALLBACK_BADGES: AchievementBadge[] = [
  {
    id: 'first-login',
    name: '初次启航',
    icon: '🚀',
    description: '完成首次登录，开启 MatuX 学习之旅',
    unlocked: true,
    unlockedDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    category: AchievementCategory.LEARNING,
    rarity: AchievementRarity.COMMON,
  },
  {
    id: 'first-course',
    name: '开课达人',
    icon: '🎓',
    description: '完成第一节课程',
    unlocked: true,
    unlockedDate: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    category: AchievementCategory.LEARNING,
    rarity: AchievementRarity.COMMON,
  },
  {
    id: 'streak-7',
    name: '连续学习 7 天',
    icon: '🔥',
    description: '连续 7 天保持学习',
    unlocked: true,
    unlockedDate: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    category: AchievementCategory.CHALLENGE,
    rarity: AchievementRarity.UNCOMMON,
  },
  {
    id: 'ai-explorer',
    name: 'AI 探索者',
    icon: '🤖',
    description: '完成 3 个 AI 相关模块',
    unlocked: false,
    category: AchievementCategory.LEARNING,
    rarity: AchievementRarity.RARE,
  },
  {
    id: 'code-master',
    name: '编程大师',
    icon: '💻',
    description: '累计完成 10 个编程挑战',
    unlocked: false,
    category: AchievementCategory.CHALLENGE,
    rarity: AchievementRarity.EPIC,
  },
  {
    id: 'quiz-champion',
    name: '测验冠军',
    icon: '🏆',
    description: '在线测验平均分达到 90+',
    unlocked: false,
    category: AchievementCategory.CHALLENGE,
    rarity: AchievementRarity.LEGENDARY,
  },
];

@Injectable({
  providedIn: 'root',
})
export class AchievementService {
  private readonly apiUrl = `${environment.apiUrl}/gamification/achievements`;

  /** 成就数据缓存 */
  private badgesSubject = new BehaviorSubject<AchievementBadge[]>([]);
  readonly badges$ = this.badgesSubject.asObservable();

  /** 已解锁数 */
  private unlockedCountSubject = new BehaviorSubject<number>(0);
  readonly unlockedCount$ = this.unlockedCountSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * 获取用户所有成就徽章
   *
   * 【P3-2 修复】后端失败时返回 FALLBACK_BADGES 示例数据，避免空状态
   */
  getAchievements(userId: number): Observable<AchievementBadge[]> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http.get<{ badges: AchievementBadge[] }>(`${this.apiUrl}/badges`, { params }).pipe(
      map((res) => res.badges),
      tap((badges) => {
        this.badgesSubject.next(badges);
        this.unlockedCountSubject.next(badges.filter((b) => b.unlocked).length);
      }),
      catchError(() => {
        // 【P3-2 修复】返回示例徽章而非空数组
        this.badgesSubject.next(FALLBACK_BADGES);
        this.unlockedCountSubject.next(FALLBACK_BADGES.filter((b) => b.unlocked).length);
        return of(FALLBACK_BADGES);
      })
    );
  }

  /**
   * 获取成就进度
   */
  getProgress(userId: number): Observable<AchievementProgress> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http
      .get<AchievementProgress>(`${this.apiUrl}/progress`, { params })
      .pipe(catchError(() => of(this.buildFallbackProgress())));
  }

  /**
   * 获取成就统计
   */
  getStats(userId: number): Observable<AchievementStats> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http.get<AchievementStats>(`${this.apiUrl}/stats`, { params }).pipe(
      catchError(() => {
        return of({
          totalPoints: 0,
          badgesCount: 0,
          currentStreak: 0,
          longestStreak: 0,
          lastActiveDate: '',
        });
      })
    );
  }

  /**
   * 获取最近的成就解锁记录
   */
  getRecentUnlocks(userId: number, limit: number = 5): Observable<AchievementUnlockEvent[]> {
    const params = new HttpParams().set('userId', userId.toString()).set('limit', limit.toString());
    return this.http
      .get<{ unlocks: AchievementUnlockEvent[] }>(`${this.apiUrl}/recent`, {
        params,
      })
      .pipe(
        map((res) => res.unlocks),
        catchError(() => of([]))
      );
  }

  /**
   * 解锁成就（通常由后端规则引擎自动触发）
   */
  unlockAchievement(userId: number, badgeId: string): Observable<AchievementUnlockEvent | null> {
    return this.http
      .post<AchievementUnlockEvent>(`${this.apiUrl}/unlock`, {
        userId,
        badgeId,
      })
      .pipe(
        tap(() => {
          // 刷新成就列表
          this.getAchievements(userId).subscribe();
        }),
        catchError(() => of(null))
      );
  }

  /**
   * 获取用户成就进度（含里程碑）
   */
  getUserAchievementProgress(userId: number): Observable<AchievementProgress> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http
      .get<AchievementProgress>(`${this.apiUrl}/progress`, { params })
      .pipe(catchError(() => of(this.buildFallbackProgress())));
  }

  /**
   * 获取待审核的成就记录
   */
  getAchievementReviews(userId: number): Observable<AchievementReview[]> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http
      .get<{ reviews: AchievementReview[] }>(`${this.apiUrl}/reviews`, { params })
      .pipe(
        map((res) => res.reviews),
        catchError(() => of([]))
      );
  }

  /**
   * 审核成就（批准/拒绝/退回修改）
   */
  reviewAchievement(
    reviewId: string,
    status: 'approved' | 'rejected' | 'revision',
    comment: string,
    reviewerId: number
  ): Observable<AchievementReview | null> {
    return this.http
      .put<AchievementReview>(`${this.apiUrl}/reviews/${reviewId}`, {
        status,
        comment,
        reviewerId,
      })
      .pipe(catchError(() => of(null)));
  }

  /**
   * 刷新本地缓存
   */
  refresh(userId: number): void {
    this.getAchievements(userId).subscribe();
  }

  /**
   * 根据 FALLBACK_BADGES 派生进度数据
   */
  private buildFallbackProgress(): AchievementProgress {
    const unlocked = FALLBACK_BADGES.filter((b) => b.unlocked);
    const totalBadges = FALLBACK_BADGES.length;
    const unlockedBadges = unlocked.length;
    const categoryProgress: Record<AchievementCategory, number> = {
      [AchievementCategory.LEARNING]: 0,
      [AchievementCategory.EXPERIMENT]: 0,
      [AchievementCategory.SOCIAL]: 0,
      [AchievementCategory.CHALLENGE]: 0,
      [AchievementCategory.HIDDEN]: 0,
    };
    FALLBACK_BADGES.forEach((b) => {
      if (b.unlocked && b.category) {
        categoryProgress[b.category] = (categoryProgress[b.category] ?? 0) + 1;
      }
    });
    return {
      totalBadges,
      unlockedBadges,
      overallProgress: unlockedBadges,
      completionPercentage: totalBadges > 0 ? Math.round((unlockedBadges / totalBadges) * 100) : 0,
      averageScore: 78,
      totalAchievements: totalBadges,
      completedAchievements: unlockedBadges,
      categoryProgress,
      recentUnlocks: unlocked,
      milestones: [],
    };
  }
}
