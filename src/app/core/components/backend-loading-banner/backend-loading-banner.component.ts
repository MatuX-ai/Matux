/**
 * 后端加载中横幅（启动优化 P3）
 *
 * 启动优化 P3：学习优先模式 (fast mode) 下，主窗口已显示但 Python 后端仍在后台启动。
 * 此横幅在主窗口顶部显示，提示用户：
 *   - AI / 考试 / 支付 等依赖后端的功能暂不可用
 *   - 本地缓存的视频与课程立即可用
 *   - 后端就绪后自动消失
 *
 * 显示条件：
 *   fastMode && !backendReady
 *
 * 用法：
 *   <app-backend-loading-banner></app-backend-loading-banner>
 *   （建议挂在 app.component 模板顶部，自动按启动模式显示/隐藏）
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { combineLatest, Subject } from 'rxjs';
import { distinctUntilChanged, map, takeUntil } from 'rxjs/operators';

import { ModuleStatusService } from '../../services/module-status.service';
import { StartupModeService } from '../../services/startup-mode.service';

@Component({
  selector: 'app-backend-loading-banner',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div
      *ngIf="visible"
      class="backend-loading-banner"
      role="status"
      aria-live="polite"
      [matTooltip]="'本地内容（已下载视频、课程）立即可用；AI / 考试 / 支付 等后端功能将在 10~30s 内自动解锁'"
    >
      <div class="banner-icon-wrap">
        <mat-icon class="banner-icon">bolt</mat-icon>
        <span class="banner-pulse" aria-hidden="true"></span>
      </div>
      <div class="banner-content">
        <span class="banner-title">⚡ 学习优先模式 · 后端后台启动中</span>
        <span class="banner-detail">
          本地课程立即可用；AI / 考试 / 支付功能将在 {{ etaSeconds }}s 内自动解锁
        </span>
      </div>
      <div class="banner-progress" aria-hidden="true">
        <div class="banner-progress-fill"></div>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        position: sticky;
        top: 0;
        z-index: 999;
      }

      .backend-loading-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 16px;
        background: linear-gradient(
          90deg,
          rgba(59, 130, 246, 0.18) 0%,
          rgba(59, 130, 246, 0.1) 100%
        );
        border-bottom: 1px solid rgba(59, 130, 246, 0.4);
        color: #dbeafe;
        font-size: 13px;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 12px rgba(59, 130, 246, 0.15);
        animation: banner-slide-in 0.4s ease-out;
      }

      @keyframes banner-slide-in {
        from {
          opacity: 0;
          transform: translateY(-100%);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .banner-icon-wrap {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        flex-shrink: 0;
      }

      .banner-icon {
        position: relative;
        z-index: 1;
        color: #fde047;
        font-size: 20px;
        width: 20px;
        height: 20px;
        filter: drop-shadow(0 0 4px rgba(253, 224, 71, 0.6));
      }

      .banner-pulse {
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: rgba(253, 224, 71, 0.4);
        animation: banner-pulse 1.6s ease-in-out infinite;
      }

      @keyframes banner-pulse {
        0%,
        100% {
          transform: scale(0.6);
          opacity: 0.7;
        }
        50% {
          transform: scale(1.4);
          opacity: 0;
        }
      }

      .banner-content {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .banner-title {
        font-weight: 700;
        color: #ffffff;
        font-size: 13px;
        letter-spacing: 0.3px;
      }

      .banner-detail {
        color: #bfdbfe;
        font-size: 11px;
        line-height: 1.4;
      }

      .banner-progress {
        position: relative;
        width: 80px;
        height: 4px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 2px;
        overflow: hidden;
        flex-shrink: 0;
      }

      .banner-progress-fill {
        position: absolute;
        inset: 0;
        background: linear-gradient(90deg, transparent, #3b82f6, #fde047, transparent);
        animation: banner-progress-flow 1.8s linear infinite;
      }

      @keyframes banner-progress-flow {
        from {
          transform: translateX(-100%);
        }
        to {
          transform: translateX(100%);
        }
      }

      @media (max-width: 640px) {
        .backend-loading-banner {
          padding: 6px 12px;
          font-size: 12px;
        }
        .banner-title {
          font-size: 12px;
        }
        .banner-detail {
          font-size: 10px;
        }
        .banner-progress {
          width: 48px;
        }
      }
    `,
  ],
})
export class BackendLoadingBannerComponent implements OnInit, OnDestroy {
  /** 横幅可见性：fast mode + 后端未就绪时为 true */
  visible = false;

  /**
   * 预估剩余秒数（粗略 30s 倒计时）
   * 后端启动经验值 10~30s，超过 60s 仍未就绪时不再倒计时
   */
  etaSeconds = 30;

  private destroy$ = new Subject<void>();
  private startTime = 0;
  private etaTimer: ReturnType<typeof setInterval> | null = null;

  constructor(
    private startupMode: StartupModeService,
    private moduleStatus: ModuleStatusService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    // 显示条件：fast mode && !backendReady
    combineLatest([
      this.startupMode.mode$.pipe(
        map((m) => m.fastMode),
        distinctUntilChanged()
      ),
      this.moduleStatus.healthy$.pipe(distinctUntilChanged()),
    ])
      .pipe(takeUntil(this.destroy$))
      .subscribe(([fastMode, healthy]) => {
        const shouldShow = fastMode && !healthy;
        if (shouldShow && !this.visible) {
          this.startEtaCountdown();
        } else if (!shouldShow && this.visible) {
          this.stopEtaCountdown();
        }
        this.visible = shouldShow;
        this.cdr.markForCheck();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.stopEtaCountdown();
  }

  private startEtaCountdown(): void {
    this.startTime = Date.now();
    this.etaSeconds = 30;
    if (this.etaTimer) clearInterval(this.etaTimer);
    this.etaTimer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const remaining = Math.max(0, 30 - elapsed);
      // 60s 之后停止倒计时（避免给用户"卡死"错觉）
      this.etaSeconds = elapsed > 60 ? 0 : remaining;
      this.cdr.markForCheck();
    }, 1000);
  }

  private stopEtaCountdown(): void {
    if (this.etaTimer) {
      clearInterval(this.etaTimer);
      this.etaTimer = null;
    }
  }
}
