/**
 * 等级升阶全屏仪式组件（P0-2）
 *
 * 由 StudentDashboard 挂载在 <app-level-up-modal> 监听 LevelEventService.levelUp$ 触发。
 * 入场序列（总 2400ms）：
 *   1. 0~400ms   mask opacity 0→0.85 + 旧徽章中心 scale 0.6→1.2→1
 *   2. 400~800ms 旧徽章粒子爆裂
 *   3. 800~1600ms 新徽章 3D 翻转（rotateY 180→0 + scale 0→1.1→1）
 *   4. 1200~2400ms 新称号 + countUp + 按钮渐入
 *
 * 出口：opacity 1→0 + scale 1→0.95，400ms
 *
 * a11y：focus trap / aria-live / body overflow 锁 / Esc 关闭
 *
 * @see 桌面端游戏化P0升级.md §2.2
 */

import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  HostListener,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { I18nService } from '../../../core/services/i18n.service';
import { LevelEventService, LevelUpPayload } from '../../../core/services/level-event.service';
import { LevelTitleService } from '../../../core/services/level-title.service';
import { SparkleBurstComponent } from '../sparkle-burst/sparkle-burst.component';

type Phase = 'idle' | 'enter' | 'old-burst' | 'new-reveal' | 'title' | 'exit';

@Component({
  selector: 'app-level-up-modal',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule, SparkleBurstComponent],
  template: `
    <ng-container *ngIf="visible">
      <div
        #mask
        class="level-up-mask"
        [class.is-entering]="phase === 'enter'"
        [class.is-exiting]="phase === 'exit'"
        [class.phase-old-burst]="phase === 'old-burst'"
        [class.phase-new-reveal]="phase === 'new-reveal'"
        [class.phase-title]="phase === 'title'"
        role="dialog"
        aria-modal="true"
        [attr.aria-labelledby]="titleId"
        (click)="onMaskClick($event)"
      >
        <div class="stage" (click)="$event.stopPropagation()">
          <!-- 旧徽章（仅阶段 1-2 显示） -->
          <div
            #oldBadge
            class="badge-old"
            *ngIf="phase === 'enter' || phase === 'old-burst'"
            [style.background]="oldGradient"
          >
            <span class="badge-text">Lv.{{ currentOldLevel }}</span>
          </div>

          <!-- 粒子爆裂（阶段 2） -->
          <app-sparkle-burst
            *ngIf="phase === 'old-burst'"
            [active]="true"
            [x]="centerX"
            [y]="centerY"
            [count]="30"
            [color]="oldTierColor"
            [durationMs]="400"
          ></app-sparkle-burst>

          <!-- 新徽章（阶段 3-4） -->
          <div
            #newBadge
            class="badge-new"
            *ngIf="phase === 'new-reveal' || phase === 'title'"
            [style.background]="newGradient"
            [style.box-shadow]="'0 0 40px ' + newTierColor + ', 0 0 0 4px ' + newTierColor + 'cc'"
          >
            <span class="badge-text">Lv.{{ currentNewLevel }}</span>
          </div>

          <!-- 阶段 4：标题 + 数字 + 按钮 -->
          <div
            #titleBlock
            class="title-block"
            *ngIf="phase === 'title'"
            [attr.id]="titleId"
            aria-live="assertive"
          >
            <div class="title-prefix">你已升级到</div>
            <div class="title-text" [style.color]="newTierColor">{{ newTitleLabel }}</div>
            <div class="total-exp">
              <span class="exp-num">{{ displayedExp }}</span>
              <span class="exp-unit">累计 EXP</span>
            </div>
            <button
              #closeBtn
              mat-flat-button
              class="continue-btn"
              [style.background]="newGradient"
              (click)="close()"
            >
              继续学习
              <mat-icon iconPositionEnd>arrow_forward</mat-icon>
            </button>
          </div>
        </div>
      </div>
    </ng-container>
  `,
  styles: [
    `
      :host {
        display: contents;
      }

      .level-up-mask {
        position: fixed;
        inset: 0;
        z-index: 1500;
        display: flex;
        justify-content: center;
        align-items: center;
        background: rgba(15, 23, 42, 0);
        opacity: 0;
        pointer-events: none;
        transition:
          background 400ms ease,
          opacity 400ms ease;
      }

      .level-up-mask.is-entering,
      .level-up-mask.phase-old-burst,
      .level-up-mask.phase-new-reveal,
      .level-up-mask.phase-title {
        background: rgba(15, 23, 42, 0.85);
        opacity: 1;
        pointer-events: auto;
      }

      .level-up-mask.is-exiting {
        background: rgba(15, 23, 42, 0);
        opacity: 0;
        pointer-events: auto;
        transform: scale(0.95);
      }

      .stage {
        position: relative;
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 32px;
      }

      .badge-old,
      .badge-new {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 140px;
        height: 140px;
        border-radius: 50%;
        color: white;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        position: relative;
        transition:
          transform 400ms cubic-bezier(0.34, 1.56, 0.64, 1),
          box-shadow 600ms ease;
      }

      .badge-old {
        transform: scale(0.6);
        opacity: 0;
      }

      .level-up-mask.is-entering .badge-old {
        animation: badge-old-enter 400ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
      }

      @keyframes badge-old-enter {
        0% {
          transform: scale(0.6);
          opacity: 0;
        }
        50% {
          transform: scale(1.2);
          opacity: 1;
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }

      .level-up-mask.phase-new-reveal .badge-new,
      .level-up-mask.phase-title .badge-new {
        animation: badge-new-reveal 800ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
      }

      @keyframes badge-new-reveal {
        0% {
          transform: perspective(800px) rotateY(180deg) scale(0);
          opacity: 0;
        }
        60% {
          transform: perspective(800px) rotateY(0) scale(1.15);
          opacity: 1;
        }
        100% {
          transform: perspective(800px) rotateY(0) scale(1);
          opacity: 1;
        }
      }

      .badge-text {
        font-size: 22px;
        font-weight: 700;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
      }

      .title-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
        opacity: 0;
        transform: translateY(40px);
        animation: title-enter 1000ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        animation-delay: 200ms;
      }

      @keyframes title-enter {
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .title-prefix {
        color: rgba(255, 255, 255, 0.85);
        font-size: 18px;
        font-weight: 600;
      }

      .title-text {
        font-size: 56px;
        font-weight: 800;
        line-height: 1.2;
        text-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
      }

      .total-exp {
        display: flex;
        align-items: baseline;
        gap: 8px;
        color: rgba(255, 255, 255, 0.9);
      }

      .exp-num {
        font-size: 36px;
        font-weight: 800;
        font-variant-numeric: tabular-nums;
      }

      .exp-unit {
        font-size: 14px;
        font-weight: 500;
      }

      .continue-btn {
        margin-top: 16px !important;
        padding: 0 32px !important;
        height: 48px !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border-radius: 24px !important;
        color: white !important;
      }

      @media (prefers-reduced-motion: reduce) {
        .level-up-mask,
        .level-up-mask.is-entering,
        .level-up-mask.is-exiting,
        .level-up-mask.phase-old-burst,
        .level-up-mask.phase-new-reveal,
        .level-up-mask.phase-title {
          transition: opacity 200ms ease;
        }
        .badge-old,
        .badge-new,
        .title-block {
          animation: none !important;
          opacity: 1 !important;
          transform: none !important;
        }
      }
    `,
  ],
})
export class LevelUpModalComponent implements OnChanges, AfterViewInit, OnDestroy {
  @ViewChild('closeBtn') closeBtnRef?: ElementRef<HTMLButtonElement>;

  /** 由父组件传入的服务 */
  private readonly levelEventService = inject(LevelEventService);
  private readonly levelTitleService = inject(LevelTitleService);
  private readonly i18n = inject(I18nService);
  private readonly cdr = inject(ChangeDetectorRef);

  // 内部状态
  visible = false;
  phase: Phase = 'idle';
  payload: LevelUpPayload | null = null;

  // 派生数据
  currentOldLevel = 1;
  currentNewLevel = 1;
  newTitleLabel = '';
  newTierColor = '#f59e0b';
  oldTierColor = '#94a3b8';
  newGradient = '';
  oldGradient = '';
  displayedExp = 0;

  // 粒子位置（屏幕中心）
  centerX = 0;
  centerY = 0;

  readonly titleId = 'level-up-modal-title';

  // 阶段定时器
  private phaseTimer: ReturnType<typeof setTimeout> | null = null;
  private countTimer: ReturnType<typeof setInterval> | null = null;
  private prevFocusEl: HTMLElement | null = null;

  ngAfterViewInit(): void {
    this.levelEventService.levelUp$.subscribe((payload) => {
      this.startSequence(payload);
    });
  }

  ngOnChanges(_: SimpleChanges): void {
    // no-op（事件驱动，不依赖 @Input）
  }

  ngOnDestroy(): void {
    this.clearTimers();
    this.unlockBodyScroll();
  }

  // ===== 阶段控制 =====

  private startSequence(payload: LevelUpPayload): void {
    if (this.visible) {
      // 已有展示中的 modal，新事件排队忽略（避免叠加）
      return;
    }
    this.clearTimers();
    this.payload = payload;
    this.currentOldLevel = payload.old.current;
    this.currentNewLevel = payload.next.current;
    this.newTitleLabel = this.resolveTitle(payload.next.current);
    const newEntry = this.levelTitleService.getTitleByLevel(payload.next.current);
    const oldEntry = this.levelTitleService.getTitleByLevel(payload.old.current || 1);
    this.newTierColor = this.levelTitleService.getTierColor(newEntry.tier);
    this.oldTierColor = this.levelTitleService.getTierColor(oldEntry.tier);
    this.newGradient = `linear-gradient(135deg, ${this.newTierColor} 0%, ${this.newTierColor}cc 100%)`;
    this.oldGradient = `linear-gradient(135deg, ${this.oldTierColor} 0%, ${this.oldTierColor}cc 100%)`;
    this.displayedExp = 0;

    // 屏幕中心
    if (typeof window !== 'undefined') {
      this.centerX = window.innerWidth / 2;
      this.centerY = window.innerHeight / 2;
    }

    this.lockBodyScroll();
    this.prevFocusEl = document.activeElement as HTMLElement | null;

    // 阶段 1: enter
    this.visible = true;
    this.phase = 'enter';
    this.cdr.markForCheck();

    // 阶段 2: old-burst
    this.phaseTimer = setTimeout(() => {
      this.phase = 'old-burst';
      this.cdr.markForCheck();
    }, 400);

    // 阶段 3: new-reveal
    this.phaseTimer = setTimeout(() => {
      this.phase = 'new-reveal';
      this.cdr.markForCheck();
    }, 800);

    // 阶段 4: title（含 countUp）
    this.phaseTimer = setTimeout(() => {
      this.phase = 'title';
      this.cdr.markForCheck();
      this.startCountUp(payload.totalExp, 1200);
      // 自动 focus 关闭按钮
      setTimeout(() => this.closeBtnRef?.nativeElement?.focus(), 250);
    }, 1600);
  }

  private startCountUp(target: number, duration: number): void {
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // ease-out
      const eased = 1 - Math.pow(1 - t, 3);
      this.displayedExp = Math.round(target * eased);
      this.cdr.markForCheck();
      if (t < 1) {
        this.countTimer = setTimeout(() => tick(performance.now()), 16) as unknown as ReturnType<
          typeof setInterval
        >;
      } else {
        this.displayedExp = target;
        this.cdr.markForCheck();
      }
    };
    tick(performance.now());
  }

  close(): void {
    if (this.phase === 'exit') return;
    this.phase = 'exit';
    this.cdr.markForCheck();
    this.phaseTimer = setTimeout(() => {
      this.visible = false;
      this.phase = 'idle';
      this.payload = null;
      this.unlockBodyScroll();
      this.prevFocusEl?.focus?.();
      this.cdr.markForCheck();
    }, 400);
  }

  onMaskClick(e: MouseEvent): void {
    // 点击背景关闭，点击内容不关闭（由内层 stopPropagation 处理）
    if (e.target === e.currentTarget) {
      this.close();
    }
  }

  @HostListener('document:keydown.escape')
  onEsc(): void {
    if (this.visible && this.phase !== 'exit') {
      this.close();
    }
  }

  // ===== helpers =====

  private clearTimers(): void {
    if (this.phaseTimer) {
      clearTimeout(this.phaseTimer);
      this.phaseTimer = null;
    }
    if (this.countTimer) {
      clearTimeout(this.countTimer);
      this.countTimer = null;
    }
  }

  private lockBodyScroll(): void {
    if (typeof document !== 'undefined') {
      document.body.style.overflow = 'hidden';
    }
  }

  private unlockBodyScroll(): void {
    if (typeof document !== 'undefined') {
      document.body.style.overflow = '';
    }
  }

  private resolveTitle(level: number): string {
    const key = `level.title.${level}`;
    const translated = this.i18n?.translate?.(key);
    if (translated && translated !== key) return translated;
    const FALLBACK: Record<number, string> = {
      1: '好奇宝宝',
      2: '编程新手',
      3: '代码学徒',
      4: '循环骑士',
      5: '函数巫师',
      6: '算法工匠',
      7: '数据炼金师',
      8: '架构大师',
      9: 'AI 协作者',
      10: '元宇宙创世者',
    };
    return FALLBACK[level] ?? `Lv.${level}`;
  }
}
