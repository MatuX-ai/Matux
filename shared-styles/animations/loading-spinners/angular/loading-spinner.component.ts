import { Component, Input, HostBinding } from '@angular/core';

/**
 * 通用加载动画组件 - Angular版本
 * 提供一致的加载指示器，支持主题适配和自定义配置
 */
@Component({
  selector: 'universal-loading-spinner',
  template: `
    <div 
      class="loading-spinner" 
      [ngStyle]="spinnerStyles"
      [attr.aria-label]="ariaLabel"
      role="progressbar"
      aria-valuemin="0"
      [attr.aria-valuemax]="value !== undefined ? 100 : undefined"
      [attr.aria-valuenow]="value !== undefined ? (value * 100) : undefined">
      
      <!-- 背景圆环 -->
      <div 
        class="spinner-background" 
        *ngIf="showBackground"
        [ngStyle]="backgroundStyles">
      </div>
      
      <!-- 主要加载轨道 -->
      <div 
        class="spinner-track" 
        [ngStyle]="trackStyles">
      </div>
      
      <!-- 旋转指示器 -->
      <div 
        class="spinner-indicator"
        [ngClass]="{'spinner-indicator--animated': value === undefined}"
        [ngStyle]="indicatorStyles">
      </div>
      
      <!-- 确定性进度指示器 -->
      <div 
        class="spinner-progress"
        *ngIf="value !== undefined"
        [ngStyle]="progressStyles">
      </div>
    </div>
  `,
  styleUrls: ['./loading-spinner.component.scss']
})
export class UniversalLoadingSpinnerComponent {
  /** 组件大小 (像素) */
  @Input() size: number = 40;
  
  /** 主色调，支持CSS颜色值或CSS变量 */
  @Input() color?: string;
  
  /** 边框宽度 (像素) */
  @Input() strokeWidth: number = 3;
  
  /** 动画持续时间 (毫秒) */
  @Input() duration: number = 1500;
  
  /** 背景颜色 */
  @Input() backgroundColor?: string;
  
  /** 是否显示背景圆环 */
  @Input() showBackground: boolean = false;
  
  /** 确定性进度值 (0-1之间)，undefined时显示无限旋转 */
  @Input() value?: number;
  
  /** ARIA标签 */
  @Input() ariaLabel: string = '正在加载';
  
  /** 主机元素CSS类绑定 */
  @HostBinding('class.universal-loading-spinner') 
  readonly hostClass = true;

  /** 主要旋转动画 */
  @HostBinding('style.--spinner-animation-duration') 
  get animationDuration(): string {
    return `${this.duration}ms`;
  }

  /** Spinner容器样式 */
  get spinnerStyles() {
    return {
      width: `${this.size}px`,
      height: `${this.size}px`,
    };
  }

  /** 背景圆环样式 */
  get backgroundStyles() {
    return {
      width: `${this.size}px`,
      height: `${this.size}px`,
      'border-radius': '50%',
      'background-color': this.backgroundColor || 'var(--surface-color, #ffffff)',
    };
  }

  /** 轨道样式 */
  get trackStyles() {
    return {
      width: `${this.size}px`,
      height: `${this.size}px`,
      'border-radius': '50%',
      'border': `${this.strokeWidth}px solid`,
      'border-color': this.showBackground 
        ? (this.backgroundColor || 'var(--surface-color, #ffffff)')
        : 'transparent',
    };
  }

  /** 指示器样式 */
  get indicatorStyles() {
    const primaryColor = this.color || 'var(--primary-color, #2196f3)';
    return {
      width: `${this.size}px`,
      height: `${this.size}px`,
      'border-radius': '50%',
      'border': `${this.strokeWidth}px solid ${primaryColor}`,
      'border-top-color': 'transparent',
    };
  }

  /** 进度指示器样式 */
  get progressStyles() {
    if (this.value === undefined) return {};
    
    const primaryColor = this.color || 'var(--primary-color, #2196f3)';
    const rotation = this.value * 360;
    
    return {
      width: `${this.size}px`,
      height: `${this.size}px`,
      'border-radius': '50%',
      'border': `${this.strokeWidth}px solid transparent`,
      'border-top-color': primaryColor,
      'transform': `rotate(${rotation}deg)`,
      'transition': 'transform 0.3s ease',
    };
  }
}