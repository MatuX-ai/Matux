# -*- coding: utf-8 -*-
"""R-01 growth-trajectory 修复 steps 1-4 (第5步已通过 SearchReplace 完成)"""
path = r'I:\iMato\src\app\user\components\growth-trajectory\growth-trajectory.component.ts'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加 ModuleStatusService import + MatButtonModule (button 元素需要)
old_imports = """import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { Subject, timeout } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';

import type { GrowthTrajectory } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { GrowthTrajectoryComponent } from '../../../shared/components/growth-trajectory/growth-trajectory.component';"""

new_imports = """import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Subject, timeout } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';

import type { GrowthTrajectory } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { ModuleStatusService } from '../../../core/services/module-status.service';
import { GrowthTrajectoryComponent } from '../../../shared/components/growth-trajectory/growth-trajectory.component';"""

assert old_imports in content, "old_imports not found"
content = content.replace(old_imports, new_imports)

# 2. 添加 MatButtonModule 到 imports 数组
old_imports_arr = """  imports: [CommonModule, MatIconModule, GrowthTrajectoryComponent],"""
new_imports_arr = """  imports: [CommonModule, MatButtonModule, MatIconModule, GrowthTrajectoryComponent],"""

assert old_imports_arr in content, "old_imports_arr not found"
content = content.replace(old_imports_arr, new_imports_arr)

# 3. 修改 template: 在 page-header 之前添加 fallback banner
old_template = """  template: `
    <div class="growth-page">
      <div class="page-header">
        <h1 class="page-title">我的成长轨迹</h1>
        <span class="update-time" *ngIf="currentDate">{{ currentDate }}</span>
      </div>

      <app-growth-trajectory *ngIf="trajectory" [trajectory]="trajectory"></app-growth-trajectory>"""

new_template = """  template: `
    <div class="growth-page">
      <!-- 【P2-R01 修复】后端不可达时顶部提示,告知用户当前展示的是演示数据 -->
      <div *ngIf="!backendAvailable && trajectory" class="fallback-banner" role="status">
        <mat-icon>cloud_off</mat-icon>
        <span>当前后端不可达,以下展示为演示数据。真实数据将在后端恢复后自动同步。</span>
        <button mat-stroked-button color="primary" (click)="retryLoad()">
          <mat-icon>refresh</mat-icon>
          重试
        </button>
      </div>

      <div class="page-header">
        <h1 class="page-title">我的成长轨迹</h1>
        <span class="update-time" *ngIf="currentDate">{{ currentDate }}</span>
      </div>

      <app-growth-trajectory *ngIf="trajectory" [trajectory]="trajectory"></app-growth-trajectory>"""

assert old_template in content, "old_template not found"
content = content.replace(old_template, new_template)

# 4. 添加 banner 样式
old_styles_close = """      .retry-btn {
        margin-top: 16px;
      }
    `,
  ],
})"""

new_styles_close = """      .retry-btn {
        margin-top: 16px;
      }
      /* 【P2-R01 修复】兑底 banner 样式 */
      .fallback-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        margin-bottom: 16px;
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        font-size: 13px;
        color: #991b1b;
      }
      .fallback-banner mat-icon {
        color: #ef4444;
      }
      .fallback-banner span {
        flex: 1;
      }
    `,
  ],
})"""

assert old_styles_close in content, "old_styles_close not found"
content = content.replace(old_styles_close, new_styles_close)

# 5. 修改 class: 添加 backendAvailable 属性 + 注入 ModuleStatusService
old_class_start = """export class GrowthTrajectoryPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  trajectory: GrowthTrajectory | null = null;
  error = false;
  currentDate = '';

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}"""

new_class_start = """export class GrowthTrajectoryPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  trajectory: GrowthTrajectory | null = null;
  error = false;
  currentDate = '';

  /** 【P2-R01 修复】后端是否可用,用于驱动兑底 banner 显示 */
  backendAvailable = true;

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private moduleStatusService: ModuleStatusService,
    private cdr: ChangeDetectorRef
  ) {}"""

assert old_class_start in content, "old_class_start not found"
content = content.replace(old_class_start, new_class_start)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: GrowthTrajectoryPageComponent R-01 修复完成 (steps 1-5)")
