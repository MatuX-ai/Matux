/**
 * 【P3-A-1】成就统计服务
 *
 * 负责从后端拉取真实的全球解锁率、累计解锁人数等数据，
 * 替换 P2 阶段的 simulateUnlockRate() mock 数据。
 *
 * 行为契约：
 * 1. 默认 BehaviorSubject 缓存（getStats 可同步访问）
 * 2. 拉取失败时降级：返回空 map + 上次缓存（前端继续显示旧数据）
 * 3. 60s 内重复调用直接走缓存（前端层）
 */

import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

/** 后端返回的单个成就统计 */
export interface AchievementBackendStats {
  id: number | string;
  name: string;
  rarity: string;
  total_unlocked: number;
  unlock_rate: number;
  global_unlock_rate: number;
  total_holders: number;
  stats_updated_at: string | null;
}

/** 前端消费的统计（key 为 string 类型） */
export interface AchievementStats {
  id: string;
  name: string;
  rarity: string;
  totalUnlocked: number;
  unlockRate: number;
  /** 0-1 */
  globalUnlockRate: number;
  totalHolders: number;
  statsUpdatedAt: string | null;
}

@Injectable({ providedIn: 'root' })
export class AchievementStatsService {
  private readonly http = inject(HttpClient);

  /** 内部缓存（id → stats） */
  private readonly cache$ = new BehaviorSubject<Map<string, AchievementStats>>(new Map());

  /** 加载状态 */
  private loadingPromise: Promise<Map<string, AchievementStats>> | null = null;

  /** 最后一次加载时间 */
  private lastLoadedAt = 0;
  private readonly CACHE_TTL_MS = 60_000; // 60s

  /**
   * 批量加载统计（带缓存）
   */
  loadStats(achievementIds?: string[]): Promise<Map<string, AchievementStats>> {
    // 命中缓存
    if (this.loadingPromise && Date.now() - this.lastLoadedAt < this.CACHE_TTL_MS) {
      return this.loadingPromise;
    }

    this.loadingPromise = this.fetchStats(achievementIds)
      .pipe(
        map((list) => this.normalize(list)),
        tap((map) => {
          this.cache$.next(map);
          this.lastLoadedAt = Date.now();
        }),
        catchError((err) => {
          console.warn('[AchievementStatsService] load failed:', err);
          return of(this.cache$.value); // 降级：返回旧缓存
        })
      )
      .toPromise()
      .then((m) => m ?? new Map());

    return this.loadingPromise;
  }

  /**
   * 同步获取已缓存的统计
   */
  getStats(id: string | number): AchievementStats | undefined {
    return this.cache$.value.get(String(id));
  }

  /**
   * 异步获取（先尝试缓存，再拉取）
   */
  getStats$(id: string | number): Observable<AchievementStats | undefined> {
    const cached = this.getStats(id);
    if (cached) return of(cached);
    return new Observable((observer) => {
      this.loadStats([String(id)]).then(() => {
        observer.next(this.getStats(id));
        observer.complete();
      });
    });
  }

  /**
   * 监听缓存更新
   */
  get cacheStream$(): Observable<Map<string, AchievementStats>> {
    return this.cache$.asObservable();
  }

  /**
   * 强制刷新（忽略 TTL）
   */
  async refresh(achievementIds?: string[]): Promise<Map<string, AchievementStats>> {
    this.lastLoadedAt = 0;
    return this.loadStats(achievementIds);
  }

  /**
   * 清空缓存
   */
  clear(): void {
    this.cache$.next(new Map());
    this.lastLoadedAt = 0;
    this.loadingPromise = null;
  }

  // ================ 私有方法 ================

  private fetchStats(achievementIds?: string[]): Observable<AchievementBackendStats[]> {
    let url = `${environment.apiUrl}/api/v1/org/1/achievements/stats/batch`;
    if (achievementIds && achievementIds.length > 0) {
      url += `?achievement_ids=${encodeURIComponent(achievementIds.join(','))}`;
    }
    return this.http.get<{ success: boolean; data: AchievementBackendStats[] }>(url).pipe(
      map((r) => r?.data ?? [])
    );
  }

  private normalize(list: AchievementBackendStats[]): Map<string, AchievementStats> {
    const map = new Map<string, AchievementStats>();
    for (const raw of list) {
      map.set(String(raw.id), {
        id: String(raw.id),
        name: raw.name,
        rarity: raw.rarity,
        totalUnlocked: raw.total_unlocked,
        unlockRate: raw.unlock_rate,
        globalUnlockRate: raw.global_unlock_rate,
        totalHolders: raw.total_holders,
        statsUpdatedAt: raw.stats_updated_at,
      });
    }
    return map;
  }
}
