/**
 * 【P3-B】AI 教师实时推送设置面板
 *
 * 字段：
 * - 启用总开关
 * - 3 类分别开关（celebration / suggestion / nudge）
 * - 勿扰时段（双数字输入，0-23）
 * - 每小时上限（slider 1-10）
 * - 同一类型冷却（slider 60-1800s）
 */
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  Input,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSliderModule } from '@angular/material/slider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';

import {
  AiTeacherLiveSettings,
  DEFAULT_LIVE_SETTINGS,
} from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-ai-teacher-live-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatDividerModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSlideToggleModule,
    MatSliderModule,
    MatSnackBarModule,
    // 【P3-B】页面内"返回"链接
    RouterModule,
  ],
  templateUrl: './ai-teacher-live-settings.component.html',
  styleUrls: ['./ai-teacher-live-settings.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AiTeacherLiveSettingsComponent implements OnInit, OnDestroy {
  @Input() userId = '';

  private readonly aiTeacher = inject(AITeacherService);
  private readonly auth = inject(AuthService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly cdr = inject(ChangeDetectorRef);

  /** 当前设置（双向绑定） */
  settings: AiTeacherLiveSettings = {
    userId: '',
    updatedAt: new Date().toISOString(),
    ...DEFAULT_LIVE_SETTINGS,
  };

  loading = false;
  saving = false;

  private sub: Subscription | null = null;
  private authSub: Subscription | null = null;

  ngOnInit(): void {
    // 优先使用外部传入的 userId；未传则从 AuthService 推导
    if (this.userId) {
      this.load();
    } else {
      this.authSub = this.auth.currentUser$.subscribe((user) => {
        if (user) {
          this.userId = String(user.id);
          this.settings = { ...this.settings, userId: this.userId };
          this.load();
        }
      });
    }
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    this.authSub?.unsubscribe();
  }

  load(): void {
    if (!this.userId) {
      return;
    }
    this.loading = true;
    this.sub = this.aiTeacher
      .getLiveSettings(this.userId)
      .subscribe({
        next: (s) => {
          this.settings = s;
          this.loading = false;
          this.cdr.markForCheck();
        },
        error: () => {
          this.loading = false;
          this.cdr.markForCheck();
        },
      });
  }

  save(): void {
    if (!this.userId) {
      return;
    }
    this.saving = true;
    this.sub = this.aiTeacher
      .updateLiveSettings(this.userId, this.settings)
      .subscribe({
        next: (s) => {
          this.settings = s;
          this.saving = false;
          this.snackBar.open('设置已保存', '关闭', { duration: 2000 });
          this.cdr.markForCheck();
        },
        error: () => {
          this.saving = false;
          this.snackBar.open('保存失败，已使用本地缓存', '关闭', {
            duration: 3000,
          });
          this.cdr.markForCheck();
        },
      });
  }

  reset(): void {
    this.settings = {
      userId: this.userId,
      updatedAt: new Date().toISOString(),
      ...DEFAULT_LIVE_SETTINGS,
    };
    this.cdr.markForCheck();
  }
}