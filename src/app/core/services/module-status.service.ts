/**
 * 模块状态服务
 *
 * 轮询后端 /api/v1/system/health-detail 获取模块加载状态，
 * 为状态栏和其他 UI 组件提供实时模块可用性信息。
 */

import { HttpClient } from '@angular/common/http';
import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, interval, Observable, Subject, of } from 'rxjs';
import { catchError, filter, map, switchMap, take, takeUntil, timeout } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

/** 模块摘要统计 */
export interface ModuleSummary {
  total: number;
  active: number;
  degraded: number;
  loading: number;
  failed: number;
  unloaded: number;
  disabled: number;
}

/** 模块状态条目 */
export interface ModuleStatusEntry {
  name: string;
  tier: number;
  tier_description: string;
  state: string;
  prefix: string;
  load_time_ms: number | null;
  error_message: string | null;
  dependencies: string[];
  required_services: string[];
  fallback_services: Record<string, string>;
}

/** 依赖服务状态 */
export interface DependencyStatus {
  name: string;
  available: boolean;
  fallback: string;
  last_check: number | null;
  check_count: number;
  failure_count: number;
  has_fallback: boolean;
}

/** 健康检查详情响应 */
export interface HealthDetailResponse {
  status: string;
  service: string;
  version: string;
  modules: {
    modules: ModuleStatusEntry[];
    summary: ModuleSummary;
  } | null;
  database_tables: Record<string, unknown>;
  circuit_breakers?: {
    total: number;
    modules: Record<string, unknown>;
  };
  dependencies?: Record<string, DependencyStatus>;
}

/** Tier 分组状态 */
export interface TierGroupStatus {
  tier: number;
  label: string;
  icon: string;
  cssClass: string;
  active: number;
  total: number;
}

/** 模块激活结果 */
export interface ModuleActivationResult {
  module: string;
  state: string;
  success: boolean;
  message: string;
}

const POLL_INTERVAL_MS = 30_000;
const ACTIVATION_TIMEOUT_MS = 15_000;

@Injectable({ providedIn: 'root' })
export class ModuleStatusService implements OnDestroy {
  private destroy$ = new Subject<void>();
  private baseUrl = `${environment.apiUrl}/api/v1/system`;

  /** 整体健康状态 */
  readonly healthy$ = new BehaviorSubject<boolean>(false);

  /** 模块摘要 */
  readonly summary$ = new BehaviorSubject<ModuleSummary | null>(null);

  /** Tier 分组状态 */
  readonly tierGroups$ = new BehaviorSubject<TierGroupStatus[]>([]);

  /** 所有模块列表 */
  readonly modules$ = new BehaviorSubject<ModuleStatusEntry[]>([]);

  /** 依赖服务状态 */
  readonly dependencies$ = new BehaviorSubject<Record<string, DependencyStatus>>({});

  constructor(private http: HttpClient) {
    this.startPolling();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /** 开始定时轮询 */
  private startPolling(): void {
    this.fetchHealth();
    interval(POLL_INTERVAL_MS)
      .pipe(
        takeUntil(this.destroy$),
        switchMap(() => this.fetchHealthInternal()),
      )
      .subscribe();
  }

  /** 手动触发一次健康检查 */
  fetchHealth(): void {
    this.fetchHealthInternal().subscribe();
  }

  private fetchHealthInternal(): Observable<HealthDetailResponse | null> {
    return this.http.get<HealthDetailResponse>(`${this.baseUrl}/health-detail`).pipe(
      catchError(() => {
        this.healthy$.next(false);
        this.summary$.next(null);
        this.tierGroups$.next([]);
        this.modules$.next([]);
        return of(null);
      }),
      map((data) => {
        if (!data) return null;

        this.healthy$.next(data.status === 'healthy');

        if (data.modules) {
          this.summary$.next(data.modules.summary);
          this.modules$.next(data.modules.modules);
          this.tierGroups$.next(this.buildTierGroups(data.modules.modules));
        }

        if (data.dependencies) {
          this.dependencies$.next(data.dependencies);
        }

        return data;
      })
    );
  }

  /** 判断指定模块是否可用 */
  isModuleAvailable(name: string): boolean {
    const mod = this.modules$.value.find((m) => m.name === name);
    return mod?.state === 'active' || mod?.state === 'degraded';
  }

  /** 获取模块状态条目 */
  getModule(name: string): ModuleStatusEntry | undefined {
    return this.modules$.value.find((m) => m.name === name);
  }

  /**
   * 确保模块已激活
   *
   * 如果模块已激活，立即返回 true。
   * 如果模块未加载，触发激活并等待结果。
   * 超时后返回 false。
   */
  ensureModuleActive(name: string): Observable<boolean> {
    // 已激活
    if (this.isModuleAvailable(name)) {
      return of(true);
    }

    // 触发激活
    return this.http.post<ModuleActivationResult>(
      `${this.baseUrl}/modules/${name}/activate`, {}
    ).pipe(
      timeout(ACTIVATION_TIMEOUT_MS),
      map((result) => {
        this.fetchHealth();  // 刷新状态
        return result.success;
      }),
      catchError(() => of(false)),
    );
  }

  /**
   * 监听模块状态变化
   *
   * 当指定模块的状态发生变化时触发回调。
   */
  onModuleStateChange(
    name: string,
    callback: (entry: ModuleStatusEntry | undefined) => void,
  ): void {
    let prevState: string | undefined;
    this.modules$
      .pipe(takeUntil(this.destroy$))
      .subscribe((modules) => {
        const mod = modules.find((m) => m.name === name);
        if (mod?.state !== prevState) {
          prevState = mod?.state;
          callback(mod);
        }
      });
  }

  /** 构建 Tier 分组 */
  private buildTierGroups(modules: ModuleStatusEntry[]): TierGroupStatus[] {
    const tierMap = new Map<number, { total: number; active: number }>();

    for (const m of modules) {
      if (!tierMap.has(m.tier)) {
        tierMap.set(m.tier, { total: 0, active: 0 });
      }
      const g = tierMap.get(m.tier)!;
      g.total++;
      if (m.state === 'active' || m.state === 'degraded') {
        g.active++;
      }
    }

    const labels: Record<number, { label: string; icon: string }> = {
      0: { label: '核心', icon: 'shield' },
      1: { label: 'AI', icon: 'psychology' },
      2: { label: '扩展', icon: 'extension' },
      3: { label: '实验', icon: 'science' },
    };

    const groups: TierGroupStatus[] = [];
    tierMap.forEach((val, tier) => {
      const info = labels[tier] || { label: `T${tier}`, icon: 'category' };
      const ratio = val.total > 0 ? val.active / val.total : 0;
      let cssClass = 'tier-full';
      if (ratio < 1 && ratio > 0) cssClass = 'tier-partial';
      else if (ratio === 0) cssClass = 'tier-off';

      groups.push({
        tier,
        label: info.label,
        icon: info.icon,
        cssClass,
        active: val.active,
        total: val.total,
      });
    });

    return groups.sort((a, b) => a.tier - b.tier);
  }
}
