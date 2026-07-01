/**
 * 系统设置页面组件
 *
 * 提供：通用设置（通知/深色模式/音效/省流量）、语言选择、缓存清除、退出登录确认
 * 带确认弹窗和 Toast 反馈
 */

import { animate, state, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

// ============ 确认弹窗组件 ============
@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatDialogModule],
  template: `
    <div class="confirm-dialog-wrapper">
      <h2 mat-dialog-title>{{ data.title }}</h2>
      <mat-dialog-content>{{ data.message }}</mat-dialog-content>
      <mat-dialog-actions align="end">
        <button mat-stroked-button mat-dialog-close>取消</button>
        <button mat-flat-button color="warn" [mat-dialog-close]="true">确认</button>
      </mat-dialog-actions>
    </div>
  `,
  styles: [`
    .confirm-dialog-wrapper { border-radius: 16px; overflow: hidden; }
    h2[mat-dialog-title] { font-size: 18px; font-weight: 700; }
    mat-dialog-content { font-size: 14px; color: #64748b; margin-bottom: 16px; }
    mat-dialog-actions { padding: 8px 0; }
    [mat-dialog-close] { border-radius: 12px; }
  `],
})
export class ConfirmDialogComponent {
  constructor(
    public data: { title: string; message: string },
  ) {}
}

// ============ 主设置组件 ============
@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatSlideToggleModule,
    MatFormFieldModule,
    MatSelectModule,
    MatDialogModule,
    MatSnackBarModule,
  ],
  animations: [
    trigger('slideToggle', [
      state('off', style({ transform: 'translateX(0)' })),
      state('on', style({ transform: 'translateX(20px)' })),
      transition('off <=> on', animate('200ms cubic-bezier(0.4, 0, 0.2, 1)')),
    ]),
    trigger('fadeIn', [
      state('void', style({ opacity: 0, transform: 'translateY(8px)' })),
      transition('void => *', animate('250ms ease-out')),
    ]),
  ],
  template: `
    <div class="settings-container">
      <div class="settings-header">
        <h1 class="page-title">
          <mat-icon>settings</mat-icon>
          系统设置
        </h1>
      </div>

      <!-- 账号卡片 -->
      <div class="account-card" [@fadeIn]>
        <div class="account-info">
          <div class="account-avatar">👤</div>
          <div class="account-details">
            <h3 class="account-name">小明同学</h3>
            <p class="account-grade">五年级 · 账号ID: STU-20240001</p>
            <p class="account-email">xiaoming@matux.edu</p>
          </div>
        </div>
      </div>

      <!-- 通用设置 -->
      <mat-card class="settings-section" [@fadeIn]>
        <mat-card-header>
          <mat-icon mat-card-avatar>notifications</mat-icon>
          <mat-card-title>通用</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">推送通知</span>
              <span class="setting-desc">接收课程提醒、成就通知等</span>
            </div>
            <mat-slide-toggle
              [checked]="settings.notifications"
              (change)="toggleSetting('notifications', $event.checked)"
            ></mat-slide-toggle>
          </div>

          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">音效</span>
              <span class="setting-desc">操作提示音和完成音效</span>
            </div>
            <mat-slide-toggle
              [checked]="settings.sound"
              (change)="toggleSetting('sound', $event.checked)"
            ></mat-slide-toggle>
          </div>

          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">省流量模式</span>
              <span class="setting-desc">减少图片加载，节省网络流量</span>
            </div>
            <mat-slide-toggle
              [checked]="settings.dataSaver"
              (change)="toggleSetting('dataSaver', $event.checked)"
            ></mat-slide-toggle>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 外观设置 -->
      <mat-card class="settings-section" [@fadeIn]>
        <mat-card-header>
          <mat-icon mat-card-avatar>palette</mat-icon>
          <mat-card-title>外观</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">深色模式</span>
              <span class="setting-desc">切换到深色主题保护眼睛</span>
            </div>
            <mat-slide-toggle
              [checked]="settings.darkMode"
              (change)="toggleSetting('darkMode', $event.checked)"
            ></mat-slide-toggle>
          </div>

          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">语言</span>
              <span class="setting-desc">界面显示语言</span>
            </div>
            <mat-form-field appearance="outline" class="language-select">
              <mat-select [value]="settings.language" (selectionChange)="onLanguageChange($event.value)">
                <mat-option value="zh-CN">🇨🇳 简体中文</mat-option>
                <mat-option value="en-US">🇺🇸 English</mat-option>
              </mat-select>
            </mat-form-field>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 学习同步 -->
      <mat-card class="settings-section" [@fadeIn]>
        <mat-card-header>
          <mat-icon mat-card-avatar>sync</mat-icon>
          <mat-card-title>学习同步</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">自动同步</span>
              <span class="setting-desc">自动同步学习进度到云端</span>
            </div>
            <mat-slide-toggle
              [checked]="settings.autoSync"
              (change)="toggleSetting('autoSync', $event.checked)"
            ></mat-slide-toggle>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 存储 -->
      <mat-card class="settings-section" [@fadeIn]>
        <mat-card-header>
          <mat-icon mat-card-avatar>storage</mat-icon>
          <mat-card-title>存储</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">缓存大小</span>
              <span class="setting-desc">当前缓存占用空间</span>
            </div>
            <span class="setting-value">{{ cacheSize }}</span>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">清除缓存</span>
              <span class="setting-desc">清除本地缓存数据</span>
            </div>
            <button mat-stroked-button color="warn" (click)="clearCache()" [disabled]="clearingCache">
              <mat-icon *ngIf="clearingCache">hourglass_empty</mat-icon>
              {{ clearingCache ? '清除中...' : '清除缓存' }}
            </button>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 关于 -->
      <mat-card class="settings-section" [@fadeIn]>
        <mat-card-header>
          <mat-icon mat-card-avatar>info</mat-icon>
          <mat-card-title>关于</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">版本</span>
            </div>
            <span class="setting-value">v2.1.0</span>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <span class="setting-label">退出登录</span>
              <span class="setting-desc">退出当前账号</span>
            </div>
            <button mat-stroked-button color="warn" (click)="confirmLogout()">
              <mat-icon>logout</mat-icon>
              退出登录
            </button>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .settings-container {
      max-width: 720px;
      margin: 0 auto;
      padding: 24px 16px;
    }

    .settings-header {
      margin-bottom: 24px;
    }
    .page-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 24px;
      font-weight: 700;
      color: var(--matux-color-text-primary, #0f172a);
      margin: 0;
    }
    .page-title mat-icon {
      color: var(--matux-color-primary, #3b82f6);
    }

    /* 账号卡片 */
    .account-card {
      background: linear-gradient(135deg, #3b82f6, #8b5cf6);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 16px;
      color: #fff;
    }
    .account-info {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .account-avatar {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
      border: 2px solid rgba(255,255,255,0.4);
    }
    .account-name {
      font-size: 18px;
      font-weight: 700;
      margin: 0 0 4px;
      color: #fff;
    }
    .account-grade {
      font-size: 13px;
      color: rgba(255,255,255,0.8);
      margin: 0 0 2px;
    }
    .account-email {
      font-size: 12px;
      color: rgba(255,255,255,0.6);
      margin: 0;
    }

    /* 设置分组 */
    .settings-section {
      margin-bottom: 16px;
      border-radius: 16px;
    }
    .settings-section mat-card-header {
      padding: 16px 16px 8px;
    }
    .settings-section mat-card-title {
      font-size: 16px;
      font-weight: 700;
    }
    .settings-section mat-card-content {
      padding: 0 16px 16px;
    }

    /* 设置项 */
    .setting-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid var(--matux-color-divider, #f1f5f9);
    }
    .setting-item:last-child {
      border-bottom: none;
    }
    .setting-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .setting-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--matux-color-text-primary, #0f172a);
    }
    .setting-desc {
      font-size: 12px;
      color: var(--matux-color-text-secondary, #64748b);
    }
    .setting-value {
      font-size: 13px;
      color: var(--matux-color-text-secondary, #64748b);
    }

    .language-select {
      width: 180px;
    }
    .language-select .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }

    /* 按钮样式 */
    .setting-item button {
      border-radius: 12px;
      font-weight: 600;
    }

    @media (max-width: 768px) {
      .settings-container {
        padding: 16px 8px;
      }
    }
  `],
})
export class SettingsComponent {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  settings: Record<string, any> = {
    notifications: true,
    sound: true,
    dataSaver: false,
    darkMode: false,
    language: 'zh-CN',
    autoSync: true,
  };

  cacheSize = '128 MB';
  clearingCache = false;

  constructor(
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
  ) {}

  toggleSetting(key: keyof typeof this.settings, value: boolean): void {
    this.settings[key] = value;
    const labels: Record<keyof typeof this.settings, string> = {
      notifications: '推送通知',
      sound: '音效',
      dataSaver: '省流量模式',
      darkMode: '深色模式',
      language: '语言',
      autoSync: '自动同步',
    };
    this.snackBar.open(`${labels[key]} 已${value ? '开启' : '关闭'}`, '知道了', {
      duration: 2000,
      panelClass: 'settings-toast',
    });
  }

  onLanguageChange(lang: string): void {
    this.settings['language'] = lang;
    const label = lang === 'zh-CN' ? '简体中文' : 'English';
    this.snackBar.open(`语言已切换为 ${label}`, '知道了', {
      duration: 2000,
      panelClass: 'settings-toast',
    });
  }

  clearCache(): void {
    this.clearingCache = true;
    // 模拟异步清除
    setTimeout(() => {
      this.cacheSize = '0 MB';
      this.clearingCache = false;
      this.snackBar.open('缓存已清除', '知道了', {
        duration: 2000,
        panelClass: 'settings-toast',
      });
    }, 1500);
  }

  confirmLogout(): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: '退出登录',
        message: '确定要退出当前账号吗？',
      },
      maxWidth: '90vw',
    });

    dialogRef.afterClosed().subscribe((confirmed) => {
      if (confirmed) {
        this.snackBar.open('已退出登录', '知道了', {
          duration: 2000,
          panelClass: 'settings-toast',
        });
        // TODO: 实际退出逻辑由路由守卫处理
      }
    });
  }
}
