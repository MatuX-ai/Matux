/**
 * 模块不可用对话框组件
 *
 * 当模块完全不可用时显示的对话框,提供原因说明和操作选项。
 *
 * 用法:
 * <app-module-unavailable-dialog
 *   moduleName="AR 实验室"
 *   reason="Vircadia 服务器未启动"
 *   [dependencyStatus]="dependencyStatus"
 *   (retry)="onRetry()"
 *   (close)="onClose()">
 * </app-module-unavailable-dialog>
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';

/** 依赖服务状态 */
interface DependencyStatus {
  name: string;
  available: boolean;
  fallback: string;
}

@Component({
  selector: 'app-module-unavailable-dialog',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatButtonModule, MatCardModule],
  template: `
    <div class="dialog-backdrop" *ngIf="visible" @fadeIn (click)="onBackdropClick($event)">
      <div class="dialog-container" (click)="$event.stopPropagation()">
        <!-- 头部 -->
        <div class="dialog-header">
          <mat-icon class="header-icon">error_outline</mat-icon>
          <h2 class="dialog-title">功能模块不可用</h2>
          <button mat-icon-button class="btn-close" (click)="close.emit()" aria-label="关闭">
            <mat-icon>close</mat-icon>
          </button>
        </div>

        <!-- 内容区 -->
        <div class="dialog-content">
          <!-- 模块信息 -->
          <div class="module-info">
            <h3 class="module-name">{{ moduleName }}</h3>
            <p class="module-reason" *ngIf="reason">{{ reason }}</p>
          </div>

          <!-- 依赖服务状态 -->
          <mat-card class="dependency-card" *ngIf="dependencyStatus && dependencyStatus.length > 0">
            <mat-card-header>
              <mat-card-title>依赖服务状态</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="dependency-list">
                <div
                  class="dependency-item"
                  *ngFor="let dep of dependencyStatus"
                >
                  <mat-icon
                    class="status-icon"
                    [class.available]="dep.available"
                    [class.unavailable]="!dep.available"
                  >
                    {{ dep.available ? 'check_circle' : 'cancel' }}
                  </mat-icon>
                  
                  <div class="dependency-info">
                    <span class="dependency-name">{{ dep.name }}</span>
                    <span class="dependency-status" [class]="dep.available ? 'status-available' : 'status-unavailable'">
                      {{ dep.available ? '可用' : '不可用' }}
                    </span>
                    <span class="dependency-fallback" *ngIf="!dep.available && dep.fallback">
                      降级方案: {{ dep.fallback }}
                    </span>
                  </div>
                </div>
              </div>
            </mat-card-content>
          </mat-card>

          <!-- 建议操作 -->
          <div class="suggestions">
            <h4>建议操作</h4>
            <ul>
              <li>检查网络连接是否正常</li>
              <li *ngIf="hasUnavailableDependencies">检查依赖服务是否已启动</li>
              <li>稍后重试或联系管理员</li>
            </ul>
          </div>
        </div>

        <!-- 底部操作区 -->
        <div class="dialog-actions">
          <button
            mat-button
            class="btn-secondary"
            (click)="close.emit()"
          >
            关闭
          </button>
          <button
            mat-flat-button
            color="primary"
            class="btn-primary"
            (click)="retry.emit()"
          >
            <mat-icon>refresh</mat-icon>
            重试
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dialog-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2000;
      animation: fadeIn 0.2s ease-out;
    }

    .dialog-container {
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      max-width: 560px;
      width: 90%;
      max-height: 80vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      animation: slideUp 0.3s ease-out;
    }

    .dialog-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 20px 24px;
      background: linear-gradient(135deg, #fee 0%, #fdd 100%);
      border-bottom: 1px solid #eee;
      position: relative;
    }

    .header-icon {
      font-size: 28px;
      width: 28px;
      height: 28px;
      color: #e74c3c;
    }

    .dialog-title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #c0392b;
      flex: 1;
    }

    .btn-close {
      width: 32px;
      height: 32px;
      line-height: 32px;
      
      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
      }
    }

    .dialog-content {
      padding: 24px;
      overflow-y: auto;
      flex: 1;
    }

    .module-info {
      margin-bottom: 20px;
    }

    .module-name {
      margin: 0 0 8px 0;
      font-size: 16px;
      font-weight: 600;
      color: #2c3e50;
    }

    .module-reason {
      margin: 0;
      font-size: 14px;
      color: #7f8c8d;
      line-height: 1.5;
    }

    .dependency-card {
      margin-bottom: 20px;
      background: #f8f9fa;
      
      mat-card-header {
        margin-bottom: 12px;
      }

      mat-card-title {
        font-size: 14px;
        font-weight: 600;
        color: #34495e;
      }
    }

    .dependency-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .dependency-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px;
      background: white;
      border-radius: 8px;
      border: 1px solid #e0e0e0;
    }

    .status-icon {
      font-size: 20px;
      width: 20px;
      height: 20px;
      flex-shrink: 0;
      margin-top: 2px;
      
      &.available {
        color: #27ae60;
      }
      
      &.unavailable {
        color: #e74c3c;
      }
    }

    .dependency-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .dependency-name {
      font-size: 14px;
      font-weight: 500;
      color: #2c3e50;
    }

    .dependency-status {
      font-size: 12px;
      
      &.status-available {
        color: #27ae60;
      }
      
      &.status-unavailable {
        color: #e74c3c;
      }
    }

    .dependency-fallback {
      font-size: 12px;
      color: #7f8c8d;
    }

    .suggestions {
      h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        font-weight: 600;
        color: #34495e;
      }

      ul {
        margin: 0;
        padding-left: 20px;
        
        li {
          font-size: 13px;
          color: #7f8c8d;
          line-height: 1.8;
        }
      }
    }

    .dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      padding: 16px 24px;
      background: #f8f9fa;
      border-top: 1px solid #e0e0e0;
    }

    .btn-secondary {
      font-size: 14px;
    }

    .btn-primary {
      font-size: 14px;
      
      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
        margin-right: 4px;
      }
    }

    @keyframes fadeIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes slideUp {
      from {
        transform: translateY(20px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }

    /* 响应式设计 */
    @media (max-width: 768px) {
      .dialog-container {
        width: 95%;
        max-height: 90vh;
      }

      .dialog-header {
        padding: 16px 20px;
      }

      .dialog-content {
        padding: 20px;
      }

      .dialog-actions {
        padding: 12px 20px;
        flex-direction: column-reverse;
        
        button {
          width: 100%;
        }
      }
    }
  `],
})
export class ModuleUnavailableDialogComponent {
  /** 模块名称 */
  @Input() moduleName = '功能模块';

  /** 不可用原因 */
  @Input() reason = '';

  /** 依赖服务状态列表 */
  @Input() dependencyStatus: DependencyStatus[] = [];

  /** 是否可见 */
  @Input() visible = true;

  /** 重试事件 */
  @Output() retry = new EventEmitter<void>();

  /** 关闭事件 */
  @Output() close = new EventEmitter<void>();

  /** 是否有不可用的依赖 */
  get hasUnavailableDependencies(): boolean {
    return this.dependencyStatus.some(dep => !dep.available);
  }

  /** 点击背景关闭 */
  onBackdropClick(event: MouseEvent): void {
    this.close.emit();
  }
}
