/**
 * 头像裁剪对话框组件
 *
 * 提供图像上传、裁剪、旋转、缩放功能
 * 支持实时预览和裁剪结果输出
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSliderModule } from '@angular/material/slider';
import { ImageCroppedEvent, ImageCropperComponent, LoadedImage } from 'ngx-image-cropper';

export interface CropDialogData {
  imageFile: File;
  aspectRatio?: number;
  canvasRotation?: number;
  initialImage?: string;
}

export interface CropDialogResult {
  croppedImageBlob: Blob;
  croppedImageBase64: string;
  croppedImageFile?: File;
}

@Component({
  selector: 'app-avatar-crop-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatSliderModule,
    MatProgressSpinnerModule,
    ImageCropperComponent,
  ],
  template: `
    <div class="crop-dialog">
      <div mat-dialog-title>
        <h2>裁剪头像</h2>
        <button mat-icon-button (click)="onCancel()">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div mat-dialog-content>
        <!-- 裁剪区域 -->
        <div class="cropper-container">
          <image-cropper
            [imageChangedEvent]="imageChangedEvent"
            [maintainAspectRatio]="true"
            [aspectRatio]="aspectRatio"
            [resizeToWidth]="800"
            [resizeToHeight]="800"
            [format]="'png'"
            [roundCropper]="true"
            [canvasRotation]="canvasRotation"
            [initialStepSize]="3"
            (imageLoaded)="onImageLoaded($event)"
            (cropperReady)="onCropperReady()"
            (imageCropped)="onImageCropped($event)"
          >
          </image-cropper>
        </div>

        <!-- 控制按钮 -->
        <div class="controls">
          <div class="control-group">
            <label>缩放:</label>
            <mat-slider
              min="0.5"
              max="3"
              step="0.1"
              value="1"
              discrete
              (change)="onZoomChange($event)"
            >
              <input matSliderThumb />
            </mat-slider>
          </div>

          <div class="control-buttons">
            <button mat-button (click)="rotateLeft()">
              <mat-icon>rotate_left</mat-icon>
              左转
            </button>
            <button mat-button (click)="rotateRight()">
              <mat-icon>rotate_right</mat-icon>
              右转
            </button>
            <button mat-button (click)="flipHorizontal()">
              <mat-icon>flip</mat-icon>
              水平翻转
            </button>
            <button mat-button (click)="flipVertical()">
              <mat-icon>flip</mat-icon>
              垂直翻转
            </button>
          </div>
        </div>

        <!-- 预览区域 -->
        <div class="preview-section">
          <h3>预览</h3>
          <div class="preview-container">
            <div class="preview-item">
              <img [src]="croppedImageBase64" alt="裁剪预览" />
              <p>裁剪后</p>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div *ngIf="loading" class="loading-overlay">
          <mat-spinner diameter="40"></mat-spinner>
          <p>正在处理图片...</p>
        </div>
      </div>

      <div mat-dialog-actions align="end">
        <button mat-button (click)="onCancel()">取消</button>
        <button
          mat-raised-button
          color="primary"
          [disabled]="!croppedImageBase64 || loading"
          (click)="onConfirm()"
        >
          确认裁剪
        </button>
      </div>
    </div>
  `,
  styles: [
    `
      .crop-dialog {
        max-width: 900px;
        width: 90vw;
      }

      [mat-dialog-title] {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 0;
      }

      [mat-dialog-title] h2 {
        margin: 0;
        font-size: 1.5rem;
      }

      .cropper-container {
        max-height: 500px;
        overflow: hidden;
        margin: 20px 0;
        background: #f5f5f5;
        border-radius: 8px;
      }

      .controls {
        margin: 20px 0;
      }

      .control-group {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 16px;
      }

      .control-group label {
        min-width: 60px;
        font-weight: 500;
      }

      mat-slider {
        flex: 1;
      }

      .control-buttons {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      .preview-section {
        margin-top: 20px;
        text-align: center;
      }

      .preview-section h3 {
        margin-bottom: 16px;
      }

      .preview-container {
        display: flex;
        justify-content: center;
        gap: 20px;
      }

      .preview-item {
        text-align: center;
      }

      .preview-item img {
        max-width: 200px;
        max-height: 200px;
        border-radius: 50%;
        border: 2px solid #e0e0e0;
        margin-bottom: 8px;
      }

      .preview-item p {
        margin: 0;
        font-size: 0.875rem;
        color: #666;
      }

      .loading-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 16px;
        z-index: 100;
        border-radius: 8px;
      }

      [mat-dialog-actions] {
        padding-top: 20px;
        border-top: 1px solid #e0e0e0;
      }
    `,
  ],
})
export class AvatarCropDialogComponent implements OnInit {
  /** 图片改变事件 */
  imageChangedEvent: Event | null = null;

  /** 裁剪后的图片 Base64 */
  croppedImageBase64: string = '';

  /** 裁剪后的图片 Blob */
  croppedImageBlob: Blob | null = null;

  /** 画布旋转角度 */
  canvasRotation: number = 0;

  /** 宽高比 */
  aspectRatio: number = 1;

  /** 是否水平翻转 */
  flipH: boolean = false;

  /** 是否垂直翻转 */
  flipV: boolean = false;

  /** 加载状态 */
  loading: boolean = false;

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: CropDialogData,
    private dialogRef: MatDialogRef<AvatarCropDialogComponent>,
    private fb: FormBuilder
  ) {}

  ngOnInit(): void {
    // 初始化图片
    if (this.data.imageFile) {
      // 创建一个符合 Event 类型的对象
      this.imageChangedEvent = {
        target: {
          files: [this.data.imageFile],
        },
      } as unknown as Event;
    }

    // 设置宽高比
    if (this.data.aspectRatio) {
      this.aspectRatio = this.data.aspectRatio;
    }

    // 设置初始旋转角度
    if (this.data.canvasRotation) {
      this.canvasRotation = this.data.canvasRotation;
    }
  }

  /**
   * 图片加载完成
   */
  onImageLoaded(_loadedImage: LoadedImage): void {
    // 图片加载完成，可以在此进行后续处理
  }

  /**
   * 裁剪器准备就绪
   */
  onCropperReady(): void {
    // 裁剪器准备就绪
  }

  /**
   * 图片裁剪完成
   */
  onImageCropped(event: ImageCroppedEvent): void {
    this.croppedImageBase64 = event.base64 ?? '';
    this.croppedImageBlob = event.blob ?? null;
  }

  /**
   * 缩放变化
   */
  onZoomChange(_event: unknown): void {
    // ngx-image-cropper 会自动处理缩放
  }

  /**
   * 向左旋转
   */
  rotateLeft(): void {
    this.canvasRotation--;
  }

  /**
   * 向右旋转
   */
  rotateRight(): void {
    this.canvasRotation++;
  }

  /**
   * 水平翻转
   */
  flipHorizontal(): void {
    this.flipH = !this.flipH;
  }

  /**
   * 垂直翻转
   */
  flipVertical(): void {
    this.flipV = !this.flipV;
  }

  /**
   * 取消操作
   */
  onCancel(): void {
    this.dialogRef.close();
  }

  /**
   * 确认裁剪
   */
  onConfirm(): void {
    if (!this.croppedImageBlob) {
      return;
    }

    const result: CropDialogResult = {
      croppedImageBlob: this.croppedImageBlob,
      croppedImageBase64: this.croppedImageBase64,
      croppedImageFile: new File([this.croppedImageBlob], 'avatar.png', {
        type: 'image/png',
      }),
    };

    this.dialogRef.close(result);
  }
}
