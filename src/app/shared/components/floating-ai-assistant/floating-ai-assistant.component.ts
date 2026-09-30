/**
 * AI 老师浮动按钮组件 - FloatingAiAssistant
 *
 * 位于 dashboard 右下角的固定位置浮动按钮
 * 点击展开 AI 老师对话面板（PRD 6.5 节强制要求）
 *
 * 通过 `AiAssistantToggleService` 与 `UserPageLayoutComponent` 中的
 * `.ai-panel` 通讯，避免点击 FAB 时跳转路由。
 *
 * @see Task 4.5 AI 老师浮动按钮
 */

import { animate, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, inject, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AiAssistantToggleService } from '../../../core/services/ai-assistant-toggle.service';

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
      type="button"
      [@enterScale]
      mat-fab
      color="primary"
      matTooltip="AI 老师在线 · 点击开始对话"
      aria-label="打开 AI 老师助手"
      (click)="onClick()"
    >
      <mat-icon>smart_toy</mat-icon>
      <span class="online-dot"></span>
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
        0%,
        100% {
          opacity: 1;
          transform: scale(1);
        }
        50% {
          opacity: 0.7;
          transform: scale(1.15);
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
export class FloatingAiAssistantComponent {
  private toggleService = inject(AiAssistantToggleService);

  @Output() clicked = new EventEmitter<void>();

  onClick(): void {
    this.clicked.emit();
    // 【P1 修复】改为切换 AI 对话面板,不再跳转路由（PRD 6.5 要求）
    this.toggleService.toggle();
  }
}
