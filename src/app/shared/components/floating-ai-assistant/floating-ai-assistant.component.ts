/**
 * AI 老师浮动按钮组件 - FloatingAiAssistant（P0-5 状态化扩展）
 *
 * 4 态：
 *   - idle    绿点呼吸（默认）
 *   - message 蓝底徽章 +未读数
 *   - reward  金色星星粒子
 *   - stuck   橙色 ? 闪烁
 *
 * 通过 `AiAssistantToggleService` 与 `UserPageLayoutComponent` 中的
 * `.ai-panel` 通讯，避免点击 FAB 时跳转路由。
 *
 * @see 桌面端游戏化P0升级.md §2.5
 */

import { animate, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  OnDestroy,
  OnInit,
  Output,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AiAssistantToggleService } from '../../../core/services/ai-assistant-toggle.service';
import { AIFabStateService, FabState } from '../../../core/services/ai-fab-state.service';

@Component({
  selector: 'app-floating-ai-assistant',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  animations: [
    trigger('enterScale', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0)' }),
        animate(
          '600ms cubic-bezier(0.34, 1.56, 0.64, 1)',
          style({ opacity: 1, transform: 'scale(1)' })
        ),
      ]),
    ]),
  ],
  template: `
    <button
      class="floating-ai-btn"
      [class]="'state-' + state"
      type="button"
      [@enterScale]
      mat-fab
      color="primary"
      [matTooltip]="tooltip"
      [attr.aria-label]="ariaLabel"
      (click)="onClick()"
    >
      <mat-icon>smart_toy</mat-icon>

      <!-- 默认 idle 绿点 -->
      <span *ngIf="state === 'idle'" class="online-dot idle-dot"></span>

      <!-- message 蓝底徽章 -->
      <span *ngIf="state === 'message'" class="fab-badge message-badge" aria-hidden="true">
        {{ unreadCount }}
      </span>

      <!-- reward 金色徽章 + 粒子 -->
      <span *ngIf="state === 'reward'" class="fab-badge reward-badge" aria-hidden="true">
        <mat-icon class="badge-icon">auto_awesome</mat-icon>
      </span>

      <!-- stuck 橙底 ? -->
      <span *ngIf="state === 'stuck'" class="fab-badge stuck-badge" aria-hidden="true">?</span>
    </button>
  `,
  styles: [
    `
      :host {
        position: fixed;
        right: 32px;
        bottom: 24px;
        z-index: 100;
      }

      .floating-ai-btn {
        position: relative !important;
        width: var(--stem-floating-ai-size, 56px) !important;
        height: var(--stem-floating-ai-size, 56px) !important;
        background: var(
          --stem-gradient-ai,
          linear-gradient(135deg, #059669 0%, #0ea5e9 100%)
        ) !important;
        box-shadow: var(--stem-floating-ai-shadow, 0 8px 24px rgba(5, 150, 105, 0.4)) !important;
        color: white !important;
        transition:
          transform 200ms ease,
          box-shadow 200ms ease;
      }

      .floating-ai-btn:hover {
        transform: scale(1.1) translateY(-2px);
        box-shadow: var(
          --stem-floating-ai-shadow-hover,
          0 12px 32px rgba(5, 150, 105, 0.5)
        ) !important;
      }

      .floating-ai-btn:active {
        transform: scale(0.96);
      }

      .floating-ai-btn mat-icon {
        width: 28px;
        height: 28px;
        font-size: 28px;
      }

      /* ===== state: idle ===== */
      .online-dot {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 10px;
        height: 10px;
        border: 2px solid white;
        border-radius: 50%;
        background: var(--stem-success, #059669);
        box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
        animation: pulse-dot 2s ease-in-out infinite;
      }
      @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.15); }
      }

      /* ===== state: message ===== */
      .message-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        min-width: 20px;
        height: 20px;
        padding: 0 5px;
        border-radius: 10px;
        background: var(--stem-fab-message, #3b82f6);
        color: white;
        font-size: 11px;
        font-weight: 700;
        line-height: 20px;
        text-align: center;
        box-shadow: 0 0 0 2px white, 0 4px 8px rgba(59, 130, 246, 0.4);
        animation: badge-pop 200ms cubic-bezier(0.34, 1.56, 0.64, 1);
      }

      /* ===== state: reward ===== */
      .reward-badge {
        position: absolute;
        top: -6px;
        right: -6px;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: var(--stem-fab-reward, #f59e0b);
        color: white;
        box-shadow: 0 0 0 2px white, 0 4px 12px rgba(245, 158, 11, 0.5);
        animation: badge-pop 200ms cubic-bezier(0.34, 1.56, 0.64, 1),
          reward-orbit 3s ease-in-out infinite;
      }
      .badge-icon {
        font-size: 14px !important;
        width: 14px !important;
        height: 14px !important;
      }
      @keyframes reward-orbit {
        0%, 100% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(15deg) scale(1.08); }
      }

      /* ===== state: stuck ===== */
      .stuck-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: var(--stem-fab-stuck, #f97316);
        color: white;
        font-size: 14px;
        font-weight: 800;
        box-shadow: 0 0 0 2px white, 0 4px 8px rgba(249, 115, 22, 0.5);
        animation: stuck-blink 0.8s ease-in-out infinite;
      }
      @keyframes stuck-blink {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.12); }
      }

      @keyframes badge-pop {
        0% { transform: scale(0); }
        70% { transform: scale(1.2); }
        100% { transform: scale(1); }
      }

      @media (prefers-reduced-motion: reduce) {
        .online-dot, .reward-badge, .stuck-badge, .message-badge {
          animation: none !important;
        }
        .stuck-badge {
          outline: 2px solid var(--stem-fab-stuck, #f97316);
          outline-offset: 2px;
        }
      }

      @media (width <= 768px) {
        :host {
          right: 16px;
          bottom: 16px;
        }
        .floating-ai-btn {
          width: 48px !important;
          height: 48px !important;
        }
      }
    `,
  ],
})
export class FloatingAiAssistantComponent implements OnInit, OnDestroy {
  private readonly toggleService = inject(AiAssistantToggleService);
  private readonly fabState = inject(AIFabStateService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();

  @Output() clicked = new EventEmitter<void>();

  state: FabState = 'idle';
  unreadCount = 0;

  get tooltip(): string {
    switch (this.state) {
      case 'message':
        return `AI 老师 · 收到 ${this.unreadCount} 条新消息`;
      case 'reward':
        return 'AI 老师 · 有新奖励待领取';
      case 'stuck':
        return 'AI 老师 · 需要帮助吗？';
      default:
        return 'AI 老师在线 · 点击开始对话';
    }
  }

  get ariaLabel(): string {
    return this.tooltip;
  }

  ngOnInit(): void {
    this.fabState.state$.pipe(takeUntil(this.destroy$)).subscribe((s) => {
      this.state = s;
      this.cdr.markForCheck();
    });
    this.fabState.unreadCount$.pipe(takeUntil(this.destroy$)).subscribe((n) => {
      this.unreadCount = n;
      this.cdr.markForCheck();
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onClick(): void {
    this.clicked.emit();
    // 携带主动开场白（仅非 idle 状态）
    const opening = this.fabState.popOpeningMessage();
    if (opening && this.state !== 'idle') {
      this.toggleService.open({ contextMessage: opening });
    } else {
      this.toggleService.toggle();
    }
    // 打开后清空部分状态
    if (this.state === 'message') {
      this.fabState.clearUnread();
    } else if (this.state === 'reward') {
      this.fabState.setRewards(0);
    } else if (this.state === 'stuck') {
      this.fabState.clearStuck();
    }
  }
}
