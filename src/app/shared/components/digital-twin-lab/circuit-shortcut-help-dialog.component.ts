/**
 * 电路实验快捷键帮助对话框
 *
 * PRD F-07 桌面端适配：显示所有分组快捷键的参考面板
 */

import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface ShortcutHelpGroup {
  group: string;
  items: { key: string; action: string; description: string }[];
}

@Component({
  selector: 'app-circuit-shortcut-help-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <div class="shortcut-help-overlay">
      <div class="shortcut-help-panel">
        <div class="panel-header">
          <h2><mat-icon>keyboard</mat-icon> 键盘快捷键参考</h2>
          <button mat-icon-button (click)="close()" aria-label="关闭">
            <mat-icon>close</mat-icon>
          </button>
        </div>
        <div class="panel-body">
          <div *ngFor="let group of data" class="shortcut-group">
            <h3>{{ group.group }}</h3>
            <div class="shortcut-items">
              <div *ngFor="let item of group.items" class="shortcut-item">
                <kbd>{{ item.key }}</kbd>
                <span class="shortcut-desc">{{ item.description }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="panel-footer">
          <button mat-stroked-button (click)="close()">关闭</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .shortcut-help-overlay {
      display: flex;
      justify-content: center;
      align-items: center;
      min-width: 420px;
      min-height: 300px;
    }
    .shortcut-help-panel {
      width: 100%;
      max-height: 80vh;
      overflow-y: auto;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      border-bottom: 1px solid rgba(0,0,0,0.12);
    }
    .panel-header h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .panel-body {
      padding: 16px 24px;
    }
    .shortcut-group {
      margin-bottom: 20px;
    }
    .shortcut-group h3 {
      margin: 0 0 8px;
      font-size: 14px;
      font-weight: 500;
      color: rgba(0,0,0,0.6);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .shortcut-items {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .shortcut-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 14px;
    }
    kbd {
      display: inline-block;
      padding: 3px 8px;
      font-size: 12px;
      font-family: 'SF Mono', 'Consolas', monospace;
      background: #f5f5f5;
      border: 1px solid #d0d0d0;
      border-radius: 4px;
      box-shadow: 0 1px 0 rgba(0,0,0,0.12);
      min-width: 60px;
      text-align: center;
      color: #333;
    }
    .shortcut-desc {
      color: rgba(0,0,0,0.87);
    }
    .panel-footer {
      padding: 12px 24px;
      border-top: 1px solid rgba(0,0,0,0.12);
      display: flex;
      justify-content: flex-end;
    }
  `],
})
export class CircuitShortcutHelpDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<CircuitShortcutHelpDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ShortcutHelpGroup[],
  ) {}

  close(): void {
    this.dialogRef.close();
  }
}
