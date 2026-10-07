/**
 * EXP 飞升动画组件 - ExpGainToast
 *
 * 显示 +EXP 反馈动画（金色数字从点击位置向上飘移）
 * 通常在完成任务/答对题目/解锁成就时触发
 *
 * @see Task 5.2 EXP 飞升动画
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { animate, style, transition, trigger } from '@angular/animations';

export interface ExpGainData {
  amount: number;
  reason?: string;
  startX?: number;
  startY?: number;
}

@Component({
  selector: 'app-exp-gain-toast',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatDialogModule],
  animations: [
    trigger('flyUp', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(0) scale(0.5)' }),
        animate(
          '300ms cubic-bezier(0.34, 1.56, 0.64, 1)',
          style({ opacity: 1, transform: 'translateY(-30px) scale(1.2)' })
        ),
        animate('900ms ease-out', style({ opacity: 0, transform: 'translateY(-100px) scale(1)' })),
      ]),
    ]),
  ],
  template: `
    <div class="exp-toast" [@flyUp]>
      <span class="exp-amount">+{{ data.amount }}</span>
      <span class="exp-unit">EXP</span>
      <span class="exp-reason" *ngIf="data.reason">{{ data.reason }}</span>
    </div>
  `,
  styles: [
    `
      :host {
        position: fixed;
        top: 50%;
        left: 50%;
        z-index: 2000;
        transform: translate(-50%, -50%);
        pointer-events: none;
      }

      .exp-toast {
        display: flex;
        flex-direction: column;
        gap: 4px;
        align-items: center;
        padding: 12px 24px;
        border-radius: 16px;
        background: var(--stem-gradient-points, linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%));
        box-shadow: 0 8px 24px rgba(245, 158, 11, 0.5);
        color: var(--matux-color-text-primary, #1c1917);
        font-weight: 700;
      }

      .exp-amount {
        font-size: 32px;
        line-height: 1;
        text-shadow: 0 1px 2px rgba(255, 255, 255, 0.3);
      }

      .exp-unit {
        font-size: 14px;
        letter-spacing: 1px;
        opacity: 0.9;
      }

      .exp-reason {
        margin-top: 4px;
        font-size: 12px;
        font-weight: 500;
        opacity: 0.85;
      }
    `,
  ],
})
export class ExpGainToastComponent {
  constructor(
    public dialogRef: MatDialogRef<ExpGainToastComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ExpGainData
  ) {
    // 1.2s 后自动关闭
    setTimeout(() => {
      this.dialogRef.close();
    }, 1300);
  }
}
