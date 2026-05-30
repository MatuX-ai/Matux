import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  inject,
  Input,
  Output,
  signal,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

import { UnifiedMaterial } from '../../../models/unified-material.models';

@Component({
  selector: 'app-arvr-preview',
  standalone: true,
  imports: [
    CommonModule,
    MatProgressBarModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="arvr-preview-container" [class.loading]="isLoading()">
      <!-- 加载状态 -->
      @if (isLoading()) {
        <div class="loading-overlay">
          <mat-spinner [diameter]="50"></mat-spinner>
          <p>加载AR/VR资源中...</p>
          <mat-progress-bar mode="indeterminate" class="loading-bar"></mat-progress-bar>
        </div>
      }

      <!-- 头部 -->
      <div class="preview-header">
        <h2>{{ material?.title }}</h2>
        <div class="header-actions">
          <button mat-icon-button (click)="toggleFullscreen()" matTooltip="全屏模式">
            <mat-icon>{{ isFullscreen() ? 'fullscreen_exit' : 'fullscreen' }}</mat-icon>
          </button>
          <button mat-icon-button (click)="onClose()" matTooltip="关闭预览">
            <mat-icon>close</mat-icon>
          </button>
        </div>
      </div>

      <!-- AR/VR内容区域 -->
      <div class="arvr-content" #contentContainer>
        <!-- AR模型 -->
        @if (material?.material_type === 'ar_model') {
          <div class="ar-model-view">
            <canvas #arCanvas class="ar-canvas"></canvas>
            <div class="ar-controls">
              <div class="control-group">
                <mat-icon>3d_rotation</mat-icon>
                <span>拖拽旋转</span>
              </div>
              <div class="control-group">
                <mat-icon>zoom_in</mat-icon>
                <span>滚轮缩放</span>
              </div>
              <div class="control-group">
                <mat-icon>open_with</mat-icon>
                <span>双指平移</span>
              </div>
            </div>
            <div class="ar-info">
              <mat-icon class="ar-badge">view_in_ar</mat-icon>
              <span>AR模型</span>
            </div>
          </div>
        }

        <!-- VR体验 -->
        @if (material?.material_type === 'vr_experience') {
          <div class="vr-experience-view">
            <canvas #vrCanvas class="vr-canvas"></canvas>
            <div class="vr-controls">
              <button mat-fab (click)="enterVRMode()" color="primary">
                <mat-icon>videogame_asset</mat-icon>
              </button>
              <span class="control-hint">进入VR模式</span>
            </div>
            <div class="vr-info">
              <mat-icon class="vr-badge">vignette</mat-icon>
              <span>VR体验</span>
            </div>
          </div>
        }

        <!-- AR/VR场景 -->
        @if (material?.material_type === 'arvr_scene') {
          <div class="arvr-scene-view">
            <canvas #sceneCanvas class="scene-canvas"></canvas>
            <div class="scene-controls">
              <button
                mat-mini-fab
                (click)="toggleARMode()"
                [color]="isARMode() ? 'accent' : 'primary'"
              >
                <mat-icon>view_in_ar</mat-icon>
              </button>
              <button
                mat-mini-fab
                (click)="toggleVRMode()"
                [color]="isVRMode() ? 'accent' : 'primary'"
              >
                <mat-icon>vignette</mat-icon>
              </button>
              <button mat-mini-fab (click)="resetCamera()">
                <mat-icon>camera_rear</mat-icon>
              </button>
            </div>
            <div class="scene-info">
              <mat-icon class="scene-badge">landscape</mat-icon>
              <span>AR/VR场景</span>
            </div>
          </div>
        }
      </div>

      <!-- 底部工具栏 -->
      <div class="preview-toolbar">
        <div class="toolbar-left">
          <button mat-button (click)="toggleGrid()">
            <mat-icon>grid_on</mat-icon>
            网格
          </button>
          <button mat-button (click)="toggleLighting()">
            <mat-icon>lightbulb</mat-icon>
            光照
          </button>
          <button mat-button (click)="toggleStats()">
            <mat-icon>analytics</mat-icon>
            统计
          </button>
        </div>
        <div class="toolbar-center">
          @if (showStats()) {
            <div class="stats-display">
              <span>FPS: {{ fps() }}</span>
              <span>顶点: {{ vertices() }}</span>
              <span>三角形: {{ triangles() }}</span>
            </div>
          }
        </div>
        <div class="toolbar-right">
          <button mat-button (click)="takeScreenshot()">
            <mat-icon>photo_camera</mat-icon>
            截图
          </button>
          <button mat-button color="accent" (click)="downloadModel()">
            <mat-icon>download</mat-icon>
            下载
          </button>
        </div>
      </div>
    </div>
  `,
  styles: `
    :host {
      display: block;
    }

    .arvr-preview-container {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      background: #0a0a0f;
      color: white;
      overflow: hidden;
    }

    .arvr-preview-container.loading {
      position: relative;
    }

    /* 加载覆盖层 */
    .loading-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 24px;
      background: rgba(10, 10, 15, 0.95);
      z-index: 100;
    }

    .loading-overlay p {
      font-size: 18px;
      font-weight: 500;
    }

    .loading-bar {
      width: 60%;
    }

    /* 头部 */
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      background: rgba(255, 255, 255, 0.05);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .preview-header h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }

    /* AR/VR内容区域 */
    .arvr-content {
      flex: 1;
      position: relative;
      overflow: hidden;
    }

    /* AR模型视图 */
    .ar-model-view,
    .vr-experience-view,
    .arvr-scene-view {
      width: 100%;
      height: 100%;
      position: relative;
    }

    .ar-canvas,
    .vr-canvas,
    .scene-canvas {
      width: 100%;
      height: 100%;
      display: block;
    }

    /* AR控件 */
    .ar-controls,
    .scene-controls {
      position: absolute;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      gap: 24px;
      padding: 16px 24px;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(10px);
      border-radius: 12px;
    }

    .control-group {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
    }

    .control-group mat-icon {
      font-size: 24px;
    }

    /* VR控件 */
    .vr-controls {
      position: absolute;
      bottom: 40px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
    }

    .control-hint {
      font-size: 14px;
      background: rgba(0, 0, 0, 0.7);
      padding: 4px 12px;
      border-radius: 4px;
    }

    /* 信息徽章 */
    .ar-info,
    .vr-info,
    .scene-info {
      position: absolute;
      top: 20px;
      right: 20px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(103, 58, 183, 0.8);
      backdrop-filter: blur(10px);
      border-radius: 8px;
      font-weight: 500;
    }

    .ar-badge,
    .vr-badge,
    .scene-badge {
      font-size: 20px;
    }

    /* 工具栏 */
    .preview-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 24px;
      background: rgba(255, 255, 255, 0.05);
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .toolbar-left,
    .toolbar-center,
    .toolbar-right {
      display: flex;
      gap: 8px;
    }

    .toolbar-center {
      flex: 1;
      justify-content: center;
    }

    .toolbar-right {
      margin-left: auto;
    }

    /* 统计显示 */
    .stats-display {
      display: flex;
      gap: 24px;
      padding: 8px 16px;
      background: rgba(0, 0, 0, 0.5);
      border-radius: 8px;
      font-family: 'Courier New', monospace;
      font-size: 14px;
    }

    /* 全屏模式 */
    .arvr-preview-container:global(.fullscreen) {
      position: fixed !important;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      z-index: 1000;
    }

    /* 响应式 */
    @media (max-width: 768px) {
      .preview-header h2 {
        font-size: 16px;
      }

      .ar-controls,
      .scene-controls {
        padding: 12px 16px;
        gap: 16px;
      }

      .stats-display {
        display: none;
      }

      .toolbar-left button span,
      .toolbar-right button span {
        display: none;
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArvrPreviewComponent {
  @Input() material: UnifiedMaterial | null = null;
  @Output() close = new EventEmitter<void>();

  isLoading = signal<boolean>(false);
  isFullscreen = signal<boolean>(false);
  isARMode = signal<boolean>(false);
  isVRMode = signal<boolean>(false);
  showGrid = signal<boolean>(false);
  showLighting = signal<boolean>(true);
  showStats = signal<boolean>(false);

  fps = signal<number>(60);
  vertices = signal<number>(0);
  triangles = signal<number>(0);

  private dialogRef = inject(MatDialogRef<ArvrPreviewComponent>);

  ngOnInit(): void {
    this.loadARVRContent();
  }

  loadARVRContent(): void {
    this.isLoading.set(true);
    // 模拟加载AR/VR内容
    setTimeout(() => {
      this.isLoading.set(false);
      this.vertices.set(12453);
      this.triangles.set(24906);
    }, 2000);
  }

  onClose(): void {
    this.dialogRef.close();
    this.close.emit();
  }

  toggleFullscreen(): void {
    const container = document.querySelector('.arvr-preview-container') as HTMLElement;
    if (!container) return;

    if (!document.fullscreenElement) {
      void container.requestFullscreen().then(() => {
        this.isFullscreen.set(true);
        // 锁屏方向为横屏（移动端AR/VR体验）
        if ((screen.orientation as unknown as { lock?: (o: string) => Promise<void> })?.lock) {
          void (screen.orientation as unknown as { lock: (o: string) => Promise<void> }).lock('landscape').catch(() => {});
        }
      }).catch((err) => {
        console.warn('[ARVR] 全屏请求失败:', err);
      });
    } else {
      void document.exitFullscreen().then(() => {
        this.isFullscreen.set(false);
        if ((screen.orientation as unknown as { unlock?: () => void })?.unlock) {
          (screen.orientation as unknown as { unlock: () => void }).unlock();
        }
      });
    }
  }

  enterVRMode(): void {
    // 强制全屏后进入VR模式
    this.toggleFullscreen();
    // 通知Unity/Three.js进入VR
    console.log('[ARVR] Entering VR immersive mode');
  }

  toggleARMode(): void {
    this.isARMode.update((v) => !v);
    if (this.isARMode()) this.isVRMode.set(false);
  }

  toggleVRMode(): void {
    this.isVRMode.update((v) => !v);
    if (this.isVRMode()) this.isARMode.set(false);
  }

  resetCamera(): void {
    // 重置相机位置
    console.log('Resetting camera');
  }

  toggleGrid(): void {
    this.showGrid.update((v) => !v);
  }

  toggleLighting(): void {
    this.showLighting.update((v) => !v);
  }

  toggleStats(): void {
    this.showStats.update((v) => !v);
  }

  takeScreenshot(): void {
    // 截图功能
    console.log('Taking screenshot');
  }

  downloadModel(): void {
    if (this.material?.id) {
      // 下载模型文件
      console.log('Downloading model:', this.material.id);
    }
  }
}
