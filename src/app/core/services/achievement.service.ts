/**
 * 成就服务
 * 管理用户的成就徽章、等级、积分、排行榜相关操作
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, delay, map } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

/** 成就徽章接口 */
export interface AchievementBadge {
  id: string;
  name: string;
  description: string;
  icon: string;
  icon_url?: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  point_value: number;
  unlocked: boolean;
  unlocked_at: string | null;
  streak_days?: number;
}

/** 用户成就响应 */
interface UserAchievementsResponse {
  success: boolean;
  data: {
    achievements: AchievementBadge[];
    statistics: {
      total_achievements: number;
      rarity_distribution: Record<string, number>;
      total_points: number;
    };
  };
}

/** 用户等级响应 */
export interface UserLevelResponse {
  current: number;
  title: string;
  exp: number;
  exp_to_next: number;
  total_exp: number;
}

/** 用户积分响应 */
export interface UserPointsResponse {
  total: number;
  weekly_earned: number;
  monthly_earned: number;
}

/** 排行榜条目 */
export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  avatar?: string;
  total_exp: number;
  weekly_change: number;
  rank_change: number;
  is_current_user: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class AchievementService {
  private readonly API_BASE = environment.apiUrl;

  constructor(private http: HttpClient) {}

  /**
   * 获取用户已解锁的成就徽章
   * @param _userId 用户ID
   * @returns Observable<AchievementBadge[]>
   */
  getUserAchievements(_userId: number): Observable<AchievementBadge[]> {
    const url = `${this.API_BASE}/ar-rewards/achievements/unlocked`;
    return this.http.get<UserAchievementsResponse>(url).pipe(
      map((response) => {
        if (response.success && response.data) {
          return response.data.achievements.map((badge) => ({
            ...badge,
            // 转换后端数据格式为前端格式
            icon: badge.icon_url ?? '🏆',
            unlocked: true, // 已解锁的成就
          }));
        }
        return [];
      }),
      catchError((error) => {
        console.error('[AchievementService] 获取成就失败:', error);
        return of([]);
      })
    );
  }

  /**
   * 获取所有可用的成就徽章（包括未解锁的）
   * @returns Observable<AchievementBadge[]>
   */
  getAllAchievements(): Observable<AchievementBadge[]> {
    // 如果后端支持获取全部成就，调用对应接口
    // 目前返回已解锁的成就
    return this.getUserAchievements(0);
  }

  /**
   * 获取用户等级信息
   * @param _userId 用户ID
   * @returns Observable<UserLevelResponse> - 包含当前等级、头衔、经验值
   */
  getUserLevel(_userId: number): Observable<UserLevelResponse> {
    const url = `${this.API_BASE}/ar-rewards/users/${_userId}/level`;
    return this.http.get<{ success: boolean; data: UserLevelResponse }>(url).pipe(
      map((response) => response.data),
      catchError((error) => {
        console.warn('[AchievementService] 获取用户等级失败，使用 mock:', error);
        // Mock 演示数据
        return of<UserLevelResponse>({
          current: 5,
          title: '探索者',
          exp: 1200,
          exp_to_next: 2000,
          total_exp: 6200,
        }).pipe(delay(200));
      })
    );
  }

  /**
   * 获取用户积分信息
   * @param _userId 用户ID
   * @returns Observable<UserPointsResponse> - 总积分、周变化、月变化
   */
  getUserPoints(_userId: number): Observable<UserPointsResponse> {
    const url = `${this.API_BASE}/ar-rewards/users/${_userId}/points`;
    return this.http.get<{ success: boolean; data: UserPointsResponse }>(url).pipe(
      map((response) => response.data),
      catchError((error) => {
        console.warn('[AchievementService] 获取用户积分失败，使用 mock:', error);
        // Mock 演示数据
        return of<UserPointsResponse>({
          total: 1250,
          weekly_earned: 85,
          monthly_earned: 320,
        }).pipe(delay(200));
      })
    );
  }

  /**
   * 获取同班同学排行榜
   * @param classId 班级 ID（可选，不传则查询用户默认班级）
   * @returns Observable<LeaderboardEntry[]> - top 50
   */
  getLeaderboard(classId?: number): Observable<LeaderboardEntry[]> {
    const params = classId ? `?class_id=${classId}` : '';
    const url = `${this.API_BASE}/ar-rewards/leaderboard${params}`;
    return this.http.get<{ success: boolean; data: LeaderboardEntry[] }>(url).pipe(
      map((response) => response.data),
      catchError((error) => {
        console.warn('[AchievementService] 获取排行榜失败，使用 mock:', error);
        // Mock 演示数据（top 5）
        return of<LeaderboardEntry[]>([
          {
            rank: 1,
            user_id: 1,
            username: '小明（我）',
            total_exp: 1250,
            weekly_change: 85,
            rank_change: 1,
            is_current_user: true,
          },
          {
            rank: 2,
            user_id: 2,
            username: '小红',
            total_exp: 1180,
            weekly_change: 60,
            rank_change: 0,
            is_current_user: false,
          },
          {
            rank: 3,
            user_id: 3,
            username: '小华',
            total_exp: 1050,
            weekly_change: 45,
            rank_change: 2,
            is_current_user: false,
          },
          {
            rank: 4,
            user_id: 4,
            username: '小丽',
            total_exp: 980,
            weekly_change: 30,
            rank_change: -1,
            is_current_user: false,
          },
          {
            rank: 5,
            user_id: 5,
            username: '小龙',
            total_exp: 920,
            weekly_change: 25,
            rank_change: 0,
            is_current_user: false,
          },
        ]).pipe(delay(200));
      })
    );
  }

  /**
   * 标记成就徽章为已读（前端本地状态）
   * @param _badgeId 徽章ID
   * @returns Observable<boolean>
   */
  markBadgeSeen(_badgeId: string): Observable<boolean> {
    // 实际对接：POST /ar-rewards/achievements/{id}/seen
    return of(true).pipe(delay(150));
  }
}
