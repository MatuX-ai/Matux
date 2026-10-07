/**
 * 升级庆祝弹窗 - LevelUpDialog
 *
 * 当用户 EXP 累积到下一级阈值时弹出
 * 显示 Lv 徽章放大+旋转、金光扫过、新等级称号
 *
 * @see Task 5.3 等级提升动画
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  Inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { animate, style, transition, trigger } from '@angular/animations';

import type { UserLevel } from '../../../user/student/services/student-dashboard-data.service';

export interface LevelUpData {
  oldLevel: UserLevel;
  newLevel: UserLevel;
}

@Component({
  selector: 'app-level-up-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule],
  animations: [
    trigger('badgeZoom', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0) rotate(0deg)' }),
        animate(
          '400ms cubic-bezier(0.34, 1.56, 0.64, 1)',
          style({ opacity: 1, transform: 'scale(1.3) rotate(180deg)' })
        ),
        animate(
          '300ms ease-out',
          style({ opacity: 1, transform: 'scale(1) rotate(360deg)' })
        ),
      ]),
    ]),
    trigger('textReveal', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate(
          '500ms 300ms ease-out',
          style({ opacity: 1, transform: 'translateY(0)' })
        ),
      ]),
    ]),
    trigger('sweep', [
      transition(':enter', [
        style({ transform: 'translateX(-100%)' }),
        animate(
          '1200ms 200ms ease-out',
          style({ transform: 'translateX(100%)' })
        ),
      ]),
    ]),
  ],
  template: `
    <div class="level-up-dialog">
      <!-- 金光扫过背景 -->
      <div class="light-sweep" [@sweep]></div>

      <div class="content">
        <div class="celebrate-emoji">🎉</div>

        <div class="badge-wrap" [@badgeZoom]>
          <div class="level-badge-big">
            <span class="lv-text">Lv.{{ data.newLevel.current }}</span>
          </div>
        </div>

        <h2 class="title" [@textReveal]>升级啦！</h2>
        <p class="subtitle" [@textReveal]>
          恭喜成为 <strong>{{ data.newLevel.title }}</strong>
        </p>

        <div class="transition-row" [@textReveal]>
          <span class="old-level">Lv.{{ data.oldLevel.current }} {{ data.oldLevel.title }}</span>
          <mat-icon class="arrow">arrow_forward</mat-icon>
          <span class="new-level">Lv.{{ data.newLevel.current }} {{ data.newLevel.title }}</span>
        </div>

        <button
          mat-flat-button
          color="primary"
          class="confirm-btn"
          (click)="onClose()"
          [@textReveal]
        >
          继续学习
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .level-up-dialog {
        position: relative;
        overflow: hidden;
        width: 400px;
        max-width: 90vw;
        padding: 32px 24px;
        border-radius: 24px;
        background: linear-gradient(135deg, #fef3c7 0%, #ffffff 50%, #ecfdf5 100%);
        text-align: center;
      }

      .light-sweep {
        position: absolute;
        top: 0;
        left: 0;
        width: 30%;
        height: 100%;
        background: linear-gradient(
          90deg,
          transparent 0%,
          rgba(255, 255, 255, 0.6) 50%,
          transparent 100%
        );
        pointer-events: none;
      }

      .content {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
      }

      .celebrate-emoji {
        font-size: 48px;
        line-height: 1;
      }

      .badge-wrap {
        position: relative;
        margin: 8px 0;
      }

      .level-badge-big {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        width: 96px;
        height: 96px;
        border-radius: 50%;
        background: var(--stem-gradient-explore, linear-gradient(135deg, #059669 0%, #10b981 100%));
        box-shadow:
          0 0 0 6px white,
          0 0 0 8px var(--stem-warning, #f59e0b),
          0 8px 24px rgba(5, 150, 105, 0.5);
        color: white;
      }

      .level-badge-big::before {
        content: '';
        position: absolute;
        inset: -16px;
        border-radius: 50%;
        background: conic-gradient(
          from 0deg,
          transparent 0%,
          rgba(245, 158, 11, 0.6) 25%,
          transparent 50%,
          rgba(245, 158, 11, 0.6) 75%,
          transparent 100%
        );
        animation: rotate-glow 2s linear infinite;
        z-index: -1;
      }

      @keyframes rotate-glow {
        to {
          transform: rotate(360deg);
        }
      }

      .lv-text {
        font-size: 28px;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }

      .title {
        margin: 0;
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 28px;
        font-weight: 700;
      }

      .subtitle {
        margin: 0;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 16px;
      }

      .subtitle strong {
        background: var(--stem-gradient-points, linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%));
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        font-weight: 700;
      }

      .transition-row {
        display: flex;
        gap: 8px;
        align-items: center;
        justify-content: center;
        margin-top: 8px;
        padding: 12px 16px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.7);
      }

      .old-level {
        color: var(--matux-color-text-disabled, #94a3b8);
        font-size: 14px;
        text-decoration: line-through;
      }

      .arrow {
        color: var(--stem-primary, #059669);
        font-size: 18px;
      }

      .new-level {
        color: var(--stem-primary, #059669);
        font-size: 14px;
        font-weight: 700;
      }

      .confirm-btn {
        margin-top: 12px;
        min-width: 160px;
      }
    `,
  ],
})
export class LevelUpDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<LevelUpDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: LevelUpData
  ) {}

  onClose(): void {
    this.dialogRef.close();
  }
}