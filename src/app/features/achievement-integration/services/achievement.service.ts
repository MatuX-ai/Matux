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
  AchievementProgress,
  AchievementReview,
  AchievementStats,
  AchievementUnlockEvent,
  ProgressMilestone,
} from '../models/achievement.model';

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
   */
  getAchievements(userId: number): Observable<AchievementBadge[]> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http
      .get<{ badges: AchievementBadge[] }>(`${this.apiUrl}/badges`, { params })
      .pipe(
        map((res) => res.badges),
        tap((badges) => {
          this.badgesSubject.next(badges);
          this.unlockedCountSubject.next(
            badges.filter((b) => b.unlocked).length
          );
        }),
        catchError(() => {
          // 失败时返回空列表
          return of([]);
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
      .pipe(
        catchError(() => {
          return of({
            totalBadges: 0,
            unlockedBadges: 0,
            overallProgress: 0,
            completionPercentage: 0,
            averageScore: 0,
            totalAchievements: 0,
            completedAchievements: 0,
            categoryProgress: {} as Record<string, number>,
            recentUnlocks: [],
            milestones: [],
          });
        })
      );
  }

  /**
   * 获取成就统计
   */
  getStats(userId: number): Observable<AchievementStats> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http
      .get<AchievementStats>(`${this.apiUrl}/stats`, { params })
      .pipe(
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
  getRecentUnlocks(
    userId: number,
    limit: number = 5
  ): Observable<AchievementUnlockEvent[]> {
    const params = new HttpParams()
      .set('userId', userId.toString())
      .set('limit', limit.toString());
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
  unlockAchievement(
    userId: number,
    badgeId: string
  ): Observable<AchievementUnlockEvent | null> {
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
      .pipe(
        catchError(() => {
          return of({
            totalBadges: 0,
            unlockedBadges: 0,
            overallProgress: 0,
            completionPercentage: 0,
            averageScore: 0,
            totalAchievements: 0,
            completedAchievements: 0,
            categoryProgress: {} as Record<string, number>,
            recentUnlocks: [],
            milestones: [],
          });
        })
      );
  }

  /**
   * 获取待审核的成就记录
   */
  getAchievementReviews(
    userId: number
  ): Observable<AchievementReview[]> {
    const params = new HttpParams().set('userId', userId.toString());
    return this.http
      .get<{ reviews: AchievementReview[] }>(
        `${this.apiUrl}/reviews`,
        { params }
      )
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
      .pipe(
        catchError(() => of(null))
      );
  }

  /**
   * 刷新本地缓存
   */
  refresh(userId: number): void {
    this.getAchievements(userId).subscribe();
  }
}
