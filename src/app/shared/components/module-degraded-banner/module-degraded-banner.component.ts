/**
 * 模块降级横幅组件
 *
 * 显示在页面顶部的横幅,提示模块正在降级运行。
 * 用户可关闭横幅,但降级状态持续存在。
 *
 * 用法:
 * <app-module-degraded-banner
 *   moduleName="AI 服务"
 *   reason="OpenAI API 不可用"
 *   fallbackMode="本地模板模式"
 *   (dismissed)="onDismissed()">
 * </app-module-degraded-banner>
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-module-degraded-banner',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule],
  template: `
    <div class="degraded-banner" *ngIf="visible && !dismissed" @slideIn>
      <div class="banner-content">
        <mat-icon class="banner-icon">info</mat-icon>
        
        <div class="banner-text">
          <h4 class="banner-title">
            {{ moduleName }} 降级运行中
          </h4>
          <p class="banner-message">
            <span *ngIf="reason">{{ reason }}，</span>
            当前模式: <strong>{{ fallbackMode }}</strong>
            <span *ngIf="limitations">，{{ limitations }}</span>
          </p>
        </div>

        <div class="banner-actions">
          <button
            mat-button
            color="primary"
            class="btn-details"
            *ngIf="showDetails"
            (click)="showDetailsClicked.emit()"
          >
            查看详情
          </button>
          
          <button
            mat-icon-button
            class="btn-dismiss"
            (click)="dismiss()"
            aria-label="关闭提示"
          >
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .degraded-banner {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 1000;
      background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
      border-bottom: 2px solid #f39c12;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      animation: slideIn 0.3s ease-out;
    }

    .banner-content {
      display: flex;
      align-items: center;
      padding: 12px 24px;
      gap: 16px;
      max-width: 1400px;
      margin: 0 auto;
    }

    .banner-icon {
      font-size: 24px;
      width: 24px;
      height: 24px;
      color: #f39c12;
      flex-shrink: 0;
    }

    .banner-text {
      flex: 1;
      min-width: 0;
    }

    .banner-title {
      margin: 0 0 4px 0;
      font-size: 14px;
      font-weight: 600;
      color: #856404;
    }

    .banner-message {
      margin: 0;
      font-size: 13px;
      color: #856404;
      line-height: 1.4;
      
      strong {
        color: #664d03;
      }
    }

    .banner-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    .btn-details {
      font-size: 13px;
      padding: 4px 12px;
    }

    .btn-dismiss {
      width: 32px;
      height: 32px;
      line-height: 32px;
      
      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }
    }

    @keyframes slideIn {
      from {
        transform: translateY(-100%);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
      .banner-content {
        flex-wrap: wrap;
        padding: 10px 16px;
      }

      .banner-text {
        flex: 1 1 calc(100% - 60px);
      }

      .banner-actions {
        flex: 1 1 auto;
        justify-content: flex-end;
      }
    }
  `],
})
export class ModuleDegradedBannerComponent {
  /** 模块名称 */
  @Input() moduleName = '功能模块';

  /** 降级原因 */
  @Input() reason = '';

  /** 降级模式 */
  @Input() fallbackMode = '基础模式';

  /** 功能限制说明 */
  @Input() limitations = '';

  /** 是否可见 */
  @Input() visible = true;

  /** 是否显示详情按钮 */
  @Input() showDetails = false;

  /** 已关闭状态 */
  dismissed = false;

  /** 关闭事件 */
  @Output() dismissedChange = new EventEmitter<void>();

  /** 查看详情事件 */
  @Output() showDetailsClicked = new EventEmitter<void>();

  /** 关闭横幅 */
  dismiss(): void {
    this.dismissed = true;
    this.dismissedChange.emit();
  }
}
