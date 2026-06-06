/**
 * 仪表盘布局设置对话框
 *
 * 允许用户勾选/取消仪表盘各区块的可见性并调整顺序
 */
import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatTooltipModule } from '@angular/material/tooltip';

import {
  DashboardLayoutService,
  DashboardWidget,
} from '../../../core/services/dashboard-layout.service';

@Component({
  selector: 'app-dashboard-layout-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatCheckboxModule,
    MatIconModule,
    MatListModule,
    MatTooltipModule,
  ],
  template: `
    <h2 mat-dialog-title>
      <mat-icon>dashboard_customize</mat-icon>
      自定义布局
    </h2>

    <mat-dialog-content>
      <p class="dialog-hint">勾选要在仪表盘上显示的区块，取消勾选则隐藏</p>

      <mat-list>
        <mat-list-item *ngFor="let widget of widgets; let last = last">
          <div class="widget-row">
            <button
              mat-icon-button
              (click)="moveUp(widget)"
              [disabled]="widget.order === 0"
              matTooltip="上移"
            >
              <mat-icon>keyboard_arrow_up</mat-icon>
            </button>
            <button mat-icon-button (click)="moveDown(widget)" [disabled]="last" matTooltip="下移">
              <mat-icon>keyboard_arrow_down</mat-icon>
            </button>
            <mat-checkbox [checked]="widget.visible" (change)="toggle(widget)">
              <mat-icon class="widget-icon">{{ widget.icon }}</mat-icon>
              {{ widget.label }}
            </mat-checkbox>
          </div>
        </mat-list-item>
      </mat-list>
    </mat-dialog-content>

    <mat-dialog-actions align="end">
      <button mat-button (click)="reset()">恢复默认</button>
      <button mat-raised-button color="primary" (click)="save()">保存</button>
    </mat-dialog-actions>
  `,
  styles: [
    `
      .dialog-hint {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 16px;
      }
      .widget-row {
        display: flex;
        align-items: center;
        gap: 4px;
        width: 100%;
      }
      .widget-icon {
        vertical-align: middle;
        margin-right: 4px;
        font-size: 20px;
      }
      mat-list-item {
        border-bottom: 1px solid #f1f5f9;
      }
      button[mat-icon-button] {
        --mat-icon-button-touch-target: 32px;
        width: 32px;
        height: 32px;
        line-height: 32px;
      }
      button[mat-icon-button] mat-icon {
        font-size: 18px;
      }
    `,
  ],
})
export class DashboardLayoutDialogComponent {
  widgets: DashboardWidget[];

  constructor(
    private dialogRef: MatDialogRef<DashboardLayoutDialogComponent>,
    private layoutService: DashboardLayoutService,
    @Inject(MAT_DIALOG_DATA) public data: unknown
  ) {
    this.widgets = this.layoutService.getWidgets().map((w) => ({ ...w }));
  }

  toggle(widget: DashboardWidget): void {
    widget.visible = !widget.visible;
  }

  moveUp(widget: DashboardWidget): void {
    const idx = this.widgets.indexOf(widget);
    if (idx <= 0) return;
    const prev = this.widgets[idx - 1];
    [prev.order, widget.order] = [widget.order, prev.order];
    this.widgets.sort((a, b) => a.order - b.order);
  }

  moveDown(widget: DashboardWidget): void {
    const idx = this.widgets.indexOf(widget);
    if (idx < 0 || idx >= this.widgets.length - 1) return;
    const next = this.widgets[idx + 1];
    [next.order, widget.order] = [widget.order, next.order];
    this.widgets.sort((a, b) => a.order - b.order);
  }

  reset(): void {
    this.layoutService.resetToDefault();
    this.widgets = this.layoutService.getWidgets().map((w) => ({ ...w }));
  }

  save(): void {
    this.layoutService.updateWidgets(this.widgets);
    this.dialogRef.close(true);
  }
}
