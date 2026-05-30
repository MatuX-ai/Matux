import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';

/**
 * AI-Edu 加载动画组件
 * 提供多种加载效果：旋转器、骨架屏、脉冲等
 */
@Component({
  selector: 'app-ai-edu-loading',
  templateUrl: './ai-edu-loading.component.html',
  styleUrls: ['./ai-edu-loading.component.scss'],
  imports: [CommonModule],
})
export class AIEduLoadingComponent {
  /**
   * 加载类型
   * spinner: 旋转器 (默认)
   * pulse: 脉冲
   * skeleton: 骨架屏
   * progress: 进度条
   */
  @Input() type: 'spinner' | 'pulse' | 'skeleton' | 'progress' = 'spinner';

  /**
   * 是否为全屏遮罩模式
   */
  @Input() overlay: boolean = true;

  /**
   * 遮罩是否透明 (白色背景)
   */
  @Input() transparent: boolean = false;

  /**
   * 加载消息
   */
  @Input() message: string = '加载中...';

  /**
   * 加载子消息
   */
  @Input() subMessage?: string;

  /**
   * 进度值 (仅 progress 类型使用)
   */
  @Input() progress: number | null = null;

  /**
   * 骨架屏行数 (仅 skeleton 类型使用)
   */
  @Input() skeletonLines: number[] = [1, 2, 3, 4];

  /**
   * TrackBy 函数优化 ngFor 性能
   */
  trackByIndex(index: number): number {
    return index;
  }
}
