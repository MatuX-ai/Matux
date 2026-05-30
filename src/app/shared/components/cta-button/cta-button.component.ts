/**
 * 公共CTA按钮组件 - 可复用的行动召唤按钮
 * 统一按钮样式和行为，支持多种变体
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { RouterModule } from '@angular/router';

import { MacButtonComponent } from '../mac/mac-button.component';

export type CtaVariant = 'primary' | 'secondary' | 'outline' | 'ghost';
export type CtaSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-cta-button',
  standalone: true,
  imports: [CommonModule, RouterModule, MacButtonComponent],
  template: `
    <a
      *ngIf="routerLink; else buttonTemplate"
      [routerLink]="routerLink"
      [queryParams]="queryParams"
      [fragment]="fragment"
      class="cta-link"
    >
      <ng-container *ngTemplateOutlet="buttonContent"></ng-container>
    </a>

    <ng-template #buttonTemplate>
      <app-mac-button
        [variant]="variant"
        [size]="size"
        [disabled]="disabled"
        [fullWidth]="fullWidth"
        (onClick)="handleClick()"
      >
        <ng-container *ngTemplateOutlet="buttonContent"></ng-container>
      </app-mac-button>
    </ng-template>

    <ng-template #buttonContent>
      <span class="cta-icon" *ngIf="icon">{{ icon }}</span>
      <span class="cta-text">{{ label }}</span>
    </ng-template>
  `,
  styles: [
    `
      .cta-link {
        text-decoration: none;
        display: inline-block;
      }

      .cta-icon {
        margin-right: 8px;
      }

      .cta-text {
        font-weight: 500;
      }

      /* 全宽样式 */
      :host(.full-width) {
        display: block;
        width: 100%;
      }

      :host(.full-width) .cta-link {
        width: 100%;
      }
    `,
  ],
})
export class CtaButtonComponent {
  @Input() label: string = '';
  @Input() icon?: string;
  @Input() variant: CtaVariant = 'primary';
  @Input() size: CtaSize = 'md';
  @Input() disabled: boolean = false;
  @Input() fullWidth: boolean = false;

  // Router link inputs
  @Input() routerLink?: string | any[];
  @Input() queryParams?: { [k: string]: any };
  @Input() fragment?: string;

  // Click output for non-router actions
  @Output() clicked = new EventEmitter<void>();

  handleClick(): void {
    if (!this.routerLink) {
      this.clicked.emit();
    }
  }
}
