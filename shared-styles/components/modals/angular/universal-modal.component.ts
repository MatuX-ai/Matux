import { Component, Input, Output, EventEmitter, TemplateRef } from '@angular/core';

/**
 * 通用模态框组件 - Angular版本
 * 提供一致的对话框体验，支持自定义内容和操作按钮
 */
@Component({
  selector: 'universal-modal',
  template: `
    <!-- 模态框遮罩 -->
    <div 
      class="modal-overlay"
      [class.modal-overlay--open]="isOpen"
      [class.modal-overlay--fullscreen]="fullscreen"
      (click)="onBackdropClick()"
      *ngIf="isOpen">
      
      <!-- 模态框容器 -->
      <div 
        class="modal-container"
        [class.modal-container--fullscreen]="fullscreen"
        [ngStyle]="containerStyles"
        (click)="$event.stopPropagation()"
        role="dialog"
        aria-modal="true"
        [attr.aria-labelledby]="'modal-title-' + modalId"
        [attr.aria-describedby]="'modal-content-' + modalId">
        
        <!-- 标准模态框 -->
        <ng-container *ngIf="!fullscreen">
          <!-- 标题栏 -->
          <div class="modal-header" *ngIf="title || showCloseButton">
            <h2 
              class="modal-title" 
              [id]="'modal-title-' + modalId"
              *ngIf="title">
              {{ title }}
            </h2>
            <button 
              *ngIf="showCloseButton"
              class="modal-close-button"
              (click)="close()"
              [attr.aria-label]="'关闭 ' + (title || '对话框')">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          
          <!-- 内容区域 -->
          <div 
            class="modal-content" 
            [id]="'modal-content-' + modalId">
            <ng-container *ngIf="contentTemplate; else defaultContent">
              <ng-template [ngTemplateOutlet]="contentTemplate"></ng-template>
            </ng-container>
            <ng-template #defaultContent>
              <p>{{ content }}</p>
            </ng-template>
          </div>
          
          <!-- 操作按钮 -->
          <div class="modal-actions" *ngIf="hasActions">
            <button 
              *ngIf="cancelButtonText"
              class="modal-button modal-button--secondary"
              (click)="onCancel()"
              type="button">
              {{ cancelButtonText }}
            </button>
            <button 
              *ngIf="secondaryButtonText"
              class="modal-button modal-button--secondary"
              (click)="onSecondaryAction()"
              type="button">
              {{ secondaryButtonText }}
            </button>
            <button 
              *ngIf="primaryButtonText"
              class="modal-button modal-button--primary"
              (click)="onPrimaryAction()"
              type="button">
              {{ primaryButtonText }}
            </button>
          </div>
        </ng-container>
        
        <!-- 全屏模态框 -->
        <ng-container *ngIf="fullscreen">
          <!-- 顶部工具栏 -->
          <div class="modal-toolbar">
            <button 
              class="modal-back-button"
              (click)="close()"
              [attr.aria-label]="'返回'">
              <span aria-hidden="true">←</span>
            </button>
            <h2 
              class="modal-toolbar-title" 
              [id]="'modal-title-' + modalId"
              *ngIf="title">
              {{ title }}
            </h2>
            <button 
              *ngIf="showCloseButton"
              class="modal-close-button modal-close-button--toolbar"
              (click)="close()"
              [attr.aria-label]="'关闭 ' + (title || '对话框')">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          
          <!-- 内容区域 -->
          <div class="modal-fullscreen-content">
            <ng-container *ngIf="contentTemplate; else defaultContent">
              <ng-template [ngTemplateOutlet]="contentTemplate"></ng-template>
            </ng-container>
            <ng-template #defaultContent>
              <p>{{ content }}</p>
            </ng-template>
          </div>
          
          <!-- 底部操作按钮 -->
          <div class="modal-fullscreen-actions" *ngIf="hasActions">
            <button 
              *ngIf="cancelButtonText"
              class="modal-button modal-button--secondary modal-button--fullwidth"
              (click)="onCancel()"
              type="button">
              {{ cancelButtonText }}
            </button>
            <button 
              *ngIf="primaryButtonText"
              class="modal-button modal-button--primary modal-button--fullwidth"
              (click)="onPrimaryAction()"
              type="button">
              {{ primaryButtonText }}
            </button>
          </div>
        </ng-container>
      </div>
    </div>
  `,
  styleUrls: ['./universal-modal.component.scss']
})
export class UniversalModalComponent {
  /** 模态框唯一标识 */
  @Input() modalId: string = Math.random().toString(36).substr(2, 9);
  
  /** 是否打开模态框 */
  @Input() isOpen: boolean = false;
  
  /** 模态框标题 */
  @Input() title?: string;
  
  /** 模态框内容（字符串） */
  @Input() content?: string;
  
  /** 模态框内容模板 */
  @Input() contentTemplate?: TemplateRef<any>;
  
  /** 主要操作按钮文本 */
  @Input() primaryButtonText?: string;
  
  /** 次要操作按钮文本 */
  @Input() secondaryButtonText?: string;
  
  /** 取消按钮文本 */
  @Input() cancelButtonText: string = '取消';
  
  /** 是否显示关闭按钮 */
  @Input() showCloseButton: boolean = true;
  
  /** 是否允许点击外部关闭 */
  @Input() backdropClose: boolean = true;
  
  /** 模态框宽度 (像素或百分比) */
  @Input() width?: string;
  
  /** 是否为全屏模态框 */
  @Input() fullscreen: boolean = false;
  
  /** 主要操作事件 */
  @Output() primaryAction = new EventEmitter<void>();
  
  /** 次要操作事件 */
  @Output() secondaryAction = new EventEmitter<void>();
  
  /** 取消事件 */
  @Output() cancel = new EventEmitter<void>();
  
  /** 关闭事件 */
  @Output() closed = new EventEmitter<void>();

  /** 检查是否有操作按钮 */
  get hasActions(): boolean {
    return !!(
      this.primaryButtonText ||
      this.secondaryButtonText ||
      this.cancelButtonText
    );
  }

  /** 容器样式 */
  get containerStyles() {
    const styles: any = {};
    
    if (this.width && !this.fullscreen) {
      styles.maxWidth = this.width;
    }
    
    return styles;
  }

  /** 处理主要操作 */
  onPrimaryAction(): void {
    this.primaryAction.emit();
    this.close();
  }

  /** 处理次要操作 */
  onSecondaryAction(): void {
    this.secondaryAction.emit();
    this.close();
  }

  /** 处理取消操作 */
  onCancel(): void {
    this.cancel.emit();
    this.close();
  }

  /** 关闭模态框 */
  close(): void {
    this.isOpen = false;
    this.closed.emit();
  }

  /** 处理背景点击 */
  onBackdropClick(): void {
    if (this.backdropClose) {
      this.close();
    }
  }

  /** 确认对话框静态方法 */
  static confirm(config: {
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
  }): Promise<boolean> {
    // 这里应该通过服务注入来实现
    // 返回一个Promise供调用者处理
    return Promise.resolve(true);
  }

  /** 信息对话框静态方法 */
  static alert(config: {
    title: string;
    message: string;
    buttonText?: string;
  }): Promise<void> {
    return Promise.resolve();
  }
}