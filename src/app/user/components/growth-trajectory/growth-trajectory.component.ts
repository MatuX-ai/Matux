/**
 * 成长轨迹页面（包装组件）
 *
 * PRD 6.6 关键页面线框 - "我的成长"
 * 使用共享组件 GrowthTrajectoryComponent 渲染内容
 */

import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { of, Subject, timeout } from 'rxjs';
import { catchError, map, take, takeUntil } from 'rxjs/operators';

import type { GrowthTrajectory } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { GrowthTrajectoryComponent } from '../../../shared/components/growth-trajectory/growth-trajectory.component';

/**
 * 【P1-3 修复】成长轨迹加载超时阈值
 * 当 authService.currentUser$ 未在合理时间内 emit 或 API 调用 hang 时，
 * 主动切到 error 状态，避免 stuck loading 8s+。
 */
const LOAD_TIMEOUT_MS = 6000;

/**
 * 【P2-R01 增强】后端探测超时阈值
 * 仅用于 backendAvailable 探测，不影响主要数据加载流程
 */
const BACKEND_PROBE_TIMEOUT_MS = 3500;

@Component({
  selector: 'app-growth-trajectory-page',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, GrowthTrajectoryComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="growth-page">
      <!-- 【P2-R01 修复】后端不可达时顶部提示,告知用户当前展示的是演示数据 -->
      <div *ngIf="!backendAvailable && trajectory" class="fallback-banner" role="status">
        <mat-icon>cloud_off</mat-icon>
        <span>当前后端不可达,以下展示为演示数据。真实数据将在后端恢复后自动同步。</span>
        <button mat-stroked-button color="primary" (click)="retryLoad()">
          <mat-icon>refresh</mat-icon>
          重试
        </button>
      </div>

      <div class="page-header">
        <h1 class="page-title">我的成长轨迹</h1>
        <span class="update-time" *ngIf="currentDate">{{ currentDate }}</span>
      </div>

      <app-growth-trajectory *ngIf="trajectory" [trajectory]="trajectory"></app-growth-trajectory>

      <div class="loading-state" *ngIf="!trajectory && !error">
        <mat-icon>hourglass_empty</mat-icon>
        <p>正在加载你的成长数据...</p>
      </div>

      <div class="error-state" *ngIf="error">
        <mat-icon>error_outline</mat-icon>
        <p>无法加载成长数据，请稍后重试</p>
        <button mat-stroked-button color="primary" (click)="retryLoad()" class="retry-btn">
          <mat-icon>refresh</mat-icon>
          重新加载
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      /* K12 STEM 探索绿主题 */
      :host {
        --stem-primary: #059669;
        --stem-primary-light: #10b981;
        --stem-text-primary: #1c1917;
        --stem-text-secondary: #57534e;
        --stem-bg-page: #fafaf9;
        --stem-radius-lg: 20px;
        --stem-shadow-sm: 0 1px 3px rgba(5, 150, 105, 0.08);
      }

      .growth-page {
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
        background: var(--stem-bg-page, #fafaf9);
        min-height: 100vh;
      }
      .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .page-title {
        font-size: 28px;
        font-weight: 700;
        // STEM 探索绿主题色
        color: var(--stem-primary, #059669);
        margin: 0;
      }
      .update-time {
        font-size: 13px;
        color: var(--stem-text-secondary, #57534e);
      }
      .loading-state,
      .error-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px;
        color: var(--stem-text-secondary, #57534e);
      }
      .loading-state mat-icon,
      .error-state mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 16px;
        color: var(--stem-primary, #059669);
      }
      .error-state {
        // 【对比度修复 #1】原 var(--stem-error, #ef4444) on $stem-bg-page 仅 3.60:1
        // 改用 var(--stem-error-dark, #dc2626) = 4.59:1 AA
        color: var(--stem-error-dark, #dc2626);
      }
      .error-state mat-icon {
        // 【对比度修复 #1】同步加深图标色，保持一致性
        color: var(--stem-error-dark, #dc2626);
      }
      .retry-btn {
        margin-top: 16px;
      }
      /* 【P2-R01 修复】兑底 banner 样式 */
      .fallback-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        margin-bottom: 16px;
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        font-size: 13px;
        color: #991b1b;
      }
      .fallback-banner mat-icon {
        color: #ef4444;
      }
      .fallback-banner span {
        flex: 1;
      }
    `,
  ],
})
export class GrowthTrajectoryPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  trajectory: GrowthTrajectory | null = null;
  error = false;
  currentDate = '';

  /** 【P2-R01 修复】后端是否可用,用于驱动兑底 banner 显示 */
  backendAvailable = true;

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const now = new Date();
    this.currentDate = `${now.getFullYear()}年${now.getMonth() + 1}月`;

    // 【P1-3 修复】独立安全兜底：直接走 localStorage，不再依赖 authService emit
    //   上一轮仍 stuck 13s+ 的根因是 currentUser$ 行为不确定（take(1) 阻塞、
    //   或者 user 同步快照为 null），而 rxjs timeout 仅在 source 订阅后生效。
    //   现在三路径并行：localStorage 优先 → authService 备选 → timeout 兜底
    const idFromStorage = this.readUserIdFromStorage();
    if (idFromStorage !== null) {
      // 最常见路径：测试 / 已登录用户 — 立即拉数据，不再等 authService
      this.loadGrowthTrajectory(idFromStorage);
    } else {
      // localStorage 都没有 — 退化到 authService（异步），并配置超时
      this.authService.currentUser$.pipe(take(1), timeout(LOAD_TIMEOUT_MS)).subscribe({
        next: (user: { id?: number | string } | null) => {
          if (user?.id !== undefined && user.id !== null) {
            this.loadGrowthTrajectory(Number(user.id));
            return;
          }
          this.error = true;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = true;
          this.cdr.markForCheck();
        },
      });
    }

    // 【P1-3 修复】兜底：N 秒后仍未拿到 trajectory → 切到 error,并提供手动重试
    setTimeout(() => {
      if (!this.trajectory && !this.error) {
        this.error = true;
        this.cdr.markForCheck();
      }
    }, LOAD_TIMEOUT_MS);

    // 【P2-R01 增强】直接在组件内探测 backend 状态(不依赖 ModuleStatusService)。
    //   - ai-teacher.service.getGrowthTrajectory 有 catchError 兑底返回 mock 数据,
    //     所以 trajectory 走通不能证明 backend 可用。
    //   - ModuleStatusService 的 healthy$ 可能因 health-detail 返回 status=healthy 但 modules=null
    //     而持续保持 true,不能反映真实业务可用性。
    //   - 因此直接探测 /api/v1/system/health-detail (或该后端任意可达端点) 来判断 backend。
    //   探测超时 3.5s,失败/超时一律视为不可达。
    this.http
      .get<{ status?: string }>('/api/v1/system/health-detail')
      .pipe(
        timeout(BACKEND_PROBE_TIMEOUT_MS),
        map((resp) => {
          const healthy = resp?.status === 'healthy';
          // 【P2-R01 增强】即使 status=healthy,业务可用性还需业务 API 走通才算 OK。
          //   后续若 trajectory 报错会再设为 false。
          this.backendAvailable = healthy;
          this.cdr.markForCheck();
          return healthy;
        }),
        catchError(() => {
          // 探测失败直接视为 backend 不可达
          this.backendAvailable = false;
          this.cdr.markForCheck();
          return of(false);
        }),
        takeUntil(this.destroy$)
      )
      .subscribe();
  }

  /**
   * 【P1-3 修复】手动重试入口 — 提供给 UI 按钮
   */
  retryLoad(): void {
    this.error = false;
    this.trajectory = null;
    this.cdr.markForCheck();
    const idFromStorage = this.readUserIdFromStorage();
    if (idFromStorage !== null) {
      this.loadGrowthTrajectory(idFromStorage);
    } else {
      this.authService.currentUser$.pipe(take(1), timeout(LOAD_TIMEOUT_MS)).subscribe({
        next: (user: { id?: number | string } | null) => {
          if (user?.id !== undefined && user.id !== null) {
            this.loadGrowthTrajectory(Number(user.id));
            return;
          }
          this.error = true;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = true;
          this.cdr.markForCheck();
        },
      });
    }
  }

  /**
   * 【P1-3 修复】从 localStorage.user_data 读取用户 ID（覆盖 AuthService 未初始化场景）
   */
  private readUserIdFromStorage(): number | null {
    try {
      const raw = localStorage.getItem('user_data');
      if (!raw) return null;
      const parsed = JSON.parse(raw) as { id?: number | string };
      const id = parsed?.id;
      if (typeof id === 'number') return Number.isFinite(id) ? id : null;
      if (typeof id === 'string' && id.trim() !== '') {
        const num = Number(id);
        return Number.isFinite(num) ? num : null;
      }
    } catch {
      /* 忽略解析错误 */
    }
    return null;
  }

  private loadGrowthTrajectory(userId: number): void {
    this.error = false;
    this.aiTeacherService
      .getGrowthTrajectory(String(userId))
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (trajectory) => {
          this.trajectory = trajectory;
          // 【P2-R01 增强】trajectory 走通不代表 backend 一定可用 —
          //   ai-teacher.service 的 getGrowthTrajectory 即使在错误时也会返回 mock 数据,
          //   所以 trajectory 有值不能证明 backend 可达。让 healthy$ 继续当单一来源。
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = true;
          // 【P2-R01 增强】catchError 触发说明 service 本身报错了,backend 不可达。
          // 即时设 backendAvailable = false,确保 banner 立刻显示。
          this.backendAvailable = false;
          this.cdr.markForCheck();
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
