/**
 * Mac 风格按钮组件
 * Apple-inspired button component for Angular marketing pages
 */
import { Component, HostBinding, Input } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-mac-button',
  template: `
    <button [class]="buttonClasses" [type]="type" [disabled]="disabled" (click)="onClick($event)">
      <ng-content></ng-content>
    </button>
  `,
  styles: [
    `
      .mac-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 10px 24px;
        font-size: 14px;
        font-weight: 500;
        line-height: 1;
        text-decoration: none;
        border-radius: 9999px;
        border: none;
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        white-space: nowrap;

        &:hover {
          transform: scale(1.02);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25); // Mac 渐变紫阴影
        }

        &:active {
          transform: scale(0.98);
        }

        &:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }
      }

      /* Primary variant - 星空蓝 (Starry Blue) */
      .mac-btn-primary {
        background: linear-gradient(
          135deg,
          var(--gradient-primary-start, #0b1426) 0%,
          var(--gradient-primary-end, #3b82f6) 100%
        );
        color: #ffffff;

        &:hover:not(:disabled) {
          background: linear-gradient(
            135deg,
            var(--gradient-primary-end, #3b82f6) 0%,
            var(--gradient-primary-start, #0b1426) 100%
          );
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }
      }

      /* Secondary variant */
      .mac-btn-secondary {
        background: #f5f5f7;
        color: #1d1d1f;

        &:hover:not(:disabled) {
          background: #e5e5ea;
        }
      }

      /* Outline variant - Mac 渐变紫边框 */
      .mac-btn-outline {
        background: transparent;
        color: var(--gradient-primary-start, #667eea);
        border: 2px solid var(--gradient-primary-start, #667eea);

        &:hover:not(:disabled) {
          background: rgba(102, 126, 234, 0.08);
        }
      }

      /* Ghost variant - Mac 渐变紫文字 */
      .mac-btn-ghost {
        background: transparent;
        color: var(--gradient-primary-start, #667eea);
        border: none;

        &:hover:not(:disabled) {
          background: rgba(102, 126, 234, 0.08);
        }
      }

      /* Sizes */
      .mac-btn-sm {
        padding: 6px 16px;
        font-size: 13px;
      }

      .mac-btn-md {
        padding: 10px 24px;
        font-size: 14px;
      }

      .mac-btn-lg {
        padding: 14px 32px;
        font-size: 16px;
      }

      /* Full width */
      .mac-btn-fullwidth {
        width: 100%;
        display: flex;
      }
    `,
  ],
})
export class MacButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() type: 'button' | 'submit' | 'reset' = 'button';
  @Input() disabled = false;
  @Input() fullWidth = false;

  @HostBinding('class') get buttonClasses(): string {
    const baseClasses = `mac-btn mac-btn-${this.variant} mac-btn-${this.size}`;
    return this.fullWidth ? `${baseClasses} mac-btn-fullwidth` : baseClasses;
  }

  onClick(event: MouseEvent): void {
    if (!this.disabled) {
      // Event emission logic can be added here
    }
  }
}
