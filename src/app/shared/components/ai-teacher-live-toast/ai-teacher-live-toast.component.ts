/**
 * 【P3-B】AI 教师实时事件 Toast 组件
 *
 * 展示模式：
 * - celebration（🎉/金色）：12s 自动消失
 * - suggestion（💡/蓝色）：8s 自动消失
 * - nudge（👋/灰色）：6s 自动消失
 *
 * 布局：右下角堆叠，最多 3 条
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
import { Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Subscription } from 'rxjs';

import {
  AiTeacherCelebrationPayload,
  AiTeacherLiveEvent,
  AiTeacherNudgePayload,
  AiTeacherSuggestionPayload,
} from '../../../core/models/ai-teacher.models';
import { AiTeacherLiveService } from '../../../core/services/ai-teacher-live.service';
import { GamificationEventType } from '../../../core/services/gamification-event-bus.service';

interface DisplayEvent extends AiTeacherLiveEvent {
  _variant: 'celebration' | 'suggestion' | 'nudge';
  _icon: string;
  _accentColor: string;
  _autoDismissMs: number;
}

@Component({
  selector: 'app-ai-teacher-live-toast',
  standalone: true,
  imports: [CommonModule, RouterModule, MatButtonModule, MatIconModule],
  templateUrl: './ai-teacher-live-toast.component.html',
  styleUrls: ['./ai-teacher-live-toast.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AiTeacherLiveToastComponent implements OnInit, OnDestroy {
  @Input() position: 'bottom-right' | 'bottom-left' | 'top-right' = 'bottom-right';

  private readonly liveService = inject(AiTeacherLiveService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  /** 当前展示的事件（最多 3 条） */
  toasts: DisplayEvent[] = [];
  private sub: Subscription | null = null;
  /** 每个 toast 的 timer handle */
  private timers = new Map<string, ReturnType<typeof setTimeout>>();

  ngOnInit(): void {
    this.sub = this.liveService.pending$.subscribe((events) => {
      this.toasts = events.map((e) => this.toDisplayEvent(e));
      // 清理已有 timer
      this.timers.forEach((handle, id) => {
        if (!this.toasts.find((t) => t.id === id)) {
          clearTimeout(handle);
          this.timers.delete(id);
        }
      });
      // 给新加入的 toast 设置 timer
      this.toasts.forEach((t) => {
        if (!this.timers.has(t.id)) {
          this.scheduleAutoDismiss(t);
        }
      });
      this.cdr.markForCheck();
    });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
    this.timers.forEach((h) => clearTimeout(h));
    this.timers.clear();
  }

  /** 点击 CTA */
  onCtaClick(toast: DisplayEvent): void {
    const payload = toast.payload as
      | AiTeacherCelebrationPayload
      | AiTeacherSuggestionPayload
      | AiTeacherNudgePayload;
    if (payload?.ctaRoute) {
      this.router.navigateByUrl(payload.ctaRoute);
    }
    this.liveService.click(toast, 'cta');
    this.removeToast(toast.id);
  }

  /** 关闭按钮 */
  onDismiss(toast: DisplayEvent): void {
    this.liveService.dismiss(toast.id);
    this.removeToast(toast.id);
  }

  /** 自动消失 */
  private scheduleAutoDismiss(toast: DisplayEvent): void {
    const handle = setTimeout(() => {
      this.liveService.click(toast, 'auto_expire');
      this.removeToast(toast.id);
    }, toast._autoDismissMs);
    this.timers.set(toast.id, handle);
  }

  private removeToast(id: string): void {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    const handle = this.timers.get(id);
    if (handle) {
      clearTimeout(handle);
      this.timers.delete(id);
    }
    this.cdr.markForCheck();
  }

  /** 转换为展示模型 */
  private toDisplayEvent(e: AiTeacherLiveEvent): DisplayEvent {
    if (e.type === GamificationEventType.AI_TEACHER_CELEBRATION) {
      const p = e.payload as AiTeacherCelebrationPayload;
      return {
        ...e,
        _variant: 'celebration',
        _icon: p?.emoji || '🎉',
        _accentColor: '#ffb300',
        _autoDismissMs: 12_000,
      };
    }
    if (e.type === GamificationEventType.AI_TEACHER_SUGGESTION) {
      const p = e.payload as AiTeacherSuggestionPayload;
      return {
        ...e,
        _variant: 'suggestion',
        _icon: '💡',
        _accentColor: '#1976d2',
        _autoDismissMs: 8_000,
      };
    }
    // nudge
    const p = e.payload as AiTeacherNudgePayload;
    return {
      ...e,
      _variant: 'nudge',
      _icon: '👋',
      _accentColor: '#607d8b',
      _autoDismissMs: 6_000,
    };
  }

  trackById(_idx: number, toast: DisplayEvent): string {
    return toast.id;
  }
}