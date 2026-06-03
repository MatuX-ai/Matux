import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatDividerModule } from '@angular/material/divider';

import { VircadiaSceneViewerComponent } from '../../../components/vircadia-scene-viewer/vircadia-scene-viewer.component';

interface AvatarOption {
  id: string;
  name: string;
  preview: string;
  category: 'body' | 'outfit' | 'accessory';
}

@Component({
  selector: 'app-avatar-customization',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatGridListModule,
    MatDividerModule,
    VircadiaSceneViewerComponent,
  ],
  template: `
    <div class="avatar-customization">
      <div class="scene-panel">
        <app-vircadia-scene-viewer
          serverUrl="http://localhost:9000"
          [autoConnect]="true"
          [debugMode]="false"
        ></app-vircadia-scene-viewer>
      </div>

      <div class="customization-panel">
        <h3><mat-icon>face</mat-icon> 自定义 Avatar</h3>

        <mat-divider></mat-divider>

        <div class="category-section">
          <h4>👤 体型</h4>
          <div class="option-grid">
            <div *ngFor="let opt of bodyOptions" class="option-card" [class.selected]="selectedBody === opt.id"
              (click)="selectBody(opt)">
              <div class="option-preview">{{ opt.preview }}</div>
              <span>{{ opt.name }}</span>
            </div>
          </div>
        </div>

        <mat-divider></mat-divider>

        <div class="category-section">
          <h4>👕 服装</h4>
          <div class="option-grid">
            <div *ngFor="let opt of outfitOptions" class="option-card" [class.selected]="selectedOutfit === opt.id"
              (click)="selectOutfit(opt)">
              <div class="option-preview">{{ opt.preview }}</div>
              <span>{{ opt.name }}</span>
            </div>
          </div>
        </div>

        <mat-divider></mat-divider>

        <div class="category-section">
          <h4>🎒 配饰</h4>
          <div class="option-grid">
            <div *ngFor="let opt of accessoryOptions" class="option-card" [class.selected]="selectedAccessory === opt.id"
              (click)="selectAccessory(opt)">
              <div class="option-preview">{{ opt.preview }}</div>
              <span>{{ opt.name }}</span>
            </div>
          </div>
        </div>

        <mat-divider></mat-divider>

        <div class="action-row">
          <button mat-raised-button color="primary" (click)="applyAvatar()">
            <mat-icon>check</mat-icon> 应用
          </button>
          <button mat-raised-button (click)="resetAvatar()">
            <mat-icon>undo</mat-icon> 重置
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .avatar-customization { height: 100%; display: flex; }
      .scene-panel { flex: 1; position: relative; }
      .customization-panel { width: 320px; padding: 16px; overflow-y: auto; background: rgba(255,255,255,0.05); color: white; }
      .customization-panel h3 { display: flex; align-items: center; gap: 8px; margin: 0 0 16px; font-size: 18px; }
      .customization-panel h4 { margin: 12px 0; font-size: 14px; color: rgba(255,255,255,0.7); }
      .option-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }
      .option-card { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 8px; border: 2px solid rgba(255,255,255,0.1); border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 12px; color: rgba(255,255,255,0.7); }
      .option-card:hover { border-color: rgba(102,126,234,0.5); background: rgba(102,126,234,0.1); }
      .option-card.selected { border-color: #667eea; background: rgba(102,126,234,0.2); color: white; }
      .option-preview { font-size: 32px; line-height: 1; }
      .action-row { display: flex; gap: 12px; margin-top: 16px; }
      .action-row button { flex: 1; }
    `,
  ],
})
export class AvatarCustomizationComponent {
  selectedBody = 'default';
  selectedOutfit = 'casual';
  selectedAccessory = 'none';

  bodyOptions: AvatarOption[] = [
    { id: 'default', name: '标准', preview: '🧑', category: 'body' },
    { id: 'slim', name: '苗条', preview: '👤', category: 'body' },
    { id: 'athletic', name: '运动', preview: '💪', category: 'body' },
    { id: 'petite', name: '小巧', preview: '🧒', category: 'body' },
  ];

  outfitOptions: AvatarOption[] = [
    { id: 'casual', name: '休闲', preview: '👕', category: 'outfit' },
    { id: 'formal', name: '正式', preview: '👔', category: 'outfit' },
    { id: 'sport', name: '运动', preview: '🎽', category: 'outfit' },
    { id: 'labcoat', name: '实验服', preview: '🥼', category: 'outfit' },
  ];

  accessoryOptions: AvatarOption[] = [
    { id: 'none', name: '无', preview: '➖', category: 'accessory' },
    { id: 'glasses', name: '眼镜', preview: '👓', category: 'accessory' },
    { id: 'hat', name: '帽子', preview: '🧢', category: 'accessory' },
    { id: 'headset', name: '耳机', preview: '🎧', category: 'accessory' },
  ];

  selectBody(opt: AvatarOption): void {
    this.selectedBody = opt.id;
  }

  selectOutfit(opt: AvatarOption): void {
    this.selectedOutfit = opt.id;
  }

  selectAccessory(opt: AvatarOption): void {
    this.selectedAccessory = opt.id;
  }

  applyAvatar(): void {
    console.log('[AvatarCustomization] Apply:', {
      body: this.selectedBody,
      outfit: this.selectedOutfit,
      accessory: this.selectedAccessory,
    });
  }

  resetAvatar(): void {
    this.selectedBody = 'default';
    this.selectedOutfit = 'casual';
    this.selectedAccessory = 'none';
  }
}
