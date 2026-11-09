/**
 * 离线奖励 Banner 组件（P1-2）
 *
 * 仅在离线模式时显示：
 * - 顶部条幅，渐变橙色背景
 * - 提示「离线模式 · 经验值 x2 加成 · 已累计 +N EXP」
 * - 入场动画：translateY(-100%) → 0 + opacity
 *
 * @see 桌面端游戏化P1升级.md §2.2
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { Observable, combineLatest, map } from 'rxjs';

import { OfflineBonusService } from '../../../core/services/offline-bonus.service';

interface BannerVm {
  show: boolean;
  multiplier: number;
  pending: number;
}

@Component({
  selector: 'app-offline-bonus-banner',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule],
  template: `
    <ng-container *ngIf="vm$ | async as vm">
      <div
        *ngIf="vm.show"
        class="offline-banner show"
        role="status"
        aria-live="polite"
      >
        <span class="banner-icon">⚡</span>
        <span class="banner-text">
          离线模式 · 经验值 <strong>x{{ vm.multiplier }}</strong> 加成
        </span>
        <span *ngIf="vm.pending > 0" class="banner-pending">
          已累计 +{{ vm.pending }} EXP 待同步
        </span>
      </div>
    </ng-container>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      :host:not(:has(.offline-banner)) {
        display: none;
      }

      .offline-banner {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        height: 0;
        padding: 0 16px;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #ffffff;
        font-size: 13px;
        font-weight: 600;
        overflow: hidden;
        opacity: 0;
        transform: translateY(-100%);
        transition:
          height 320ms cubic-bezier(0.34, 1.56, 0.64, 1),
          padding 320ms cubic-bezier(0.34, 1.56, 0.64, 1),
          opacity 280ms ease,
          transform 320ms cubic-bezier(0.34, 1.56, 0.64, 1);
      }

      .offline-banner.show {
        height: 40px;
        padding: 8px 16px;
        opacity: 1;
        transform: translateY(0);
      }

      .banner-icon {
        font-size: 16px;
        filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.15));
      }

      .banner-text {
        font-weight: 600;
      }

      .banner-text strong {
        font-weight: 800;
        font-variant-numeric: tabular-nums;
      }

      .banner-pending {
        padding: 2px 8px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.22);
        color: #ffffff;
        font-size: 11px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
      }
    `,
  ],
})
export class OfflineBonusBannerComponent implements OnInit {
  private readonly offlineBonus = inject(OfflineBonusService);

  vm$!: Observable<BannerVm>;

  ngOnInit(): void {
    // 修复：使用 combineLatest 让 multiplier / pending 在 isOffline$ 不变时也能触发更新
    this.vm$ = combineLatest([
      this.offlineBonus.isOffline$,
      this.offlineBonus.bonusMultiplier$,
      this.offlineBonus.pendingOfflineExp$,
    ]).pipe(
      map(([offline, multiplier, pending]) => ({
        show: offline,
        multiplier,
        pending,
      }))
    );
  }
}
