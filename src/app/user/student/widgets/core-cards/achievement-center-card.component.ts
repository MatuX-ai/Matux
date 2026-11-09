/**
 * 成就中心卡 - 核心 dashboard 卡 #2（P0-3 改造 + P0-2 触发源）
 *
 * 内容：
 * - 等级徽章 + 段位色环
 * - 10 级叙事化称号（好奇宝宝 → 元宇宙创世者）
 * - 经验值进度条 + 下一称号预告
 * - 连续打卡天数（火焰图标）
 * - 徽章预览（解锁/未解锁状态，含稀有度）
 * - 跳转成就墙
 *
 * 视觉：琥珀渐变 + 段位色环
 *
 * 触发升级：ngOnChanges 监听 level.current 变化 → LevelEventService.emit
 *
 * @see 桌面端游戏化P0升级.md §2.2 / §2.3
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { I18nService } from '../../../../core/services/i18n.service';
import { LevelEventService } from '../../../../core/services/level-event.service';
import { LevelTitleService } from '../../../../core/services/level-title.service';
import type { DashboardSnapshot, UserLevel } from '../../services/student-dashboard-data.service';
import type { ExtendedAchievementBadge } from '../../student-dashboard.mock';

@Component({
  selector: 'app-achievement-center-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatCardModule, MatIconModule, MatProgressBarModule, MatTooltipModule],
  template: `
    <mat-card
      class="core-card core-card--achievement"
      [class.clickable]="true"
      tabindex="0"
      role="button"
      [attr.aria-label]="ariaLabel"
      (click)="onClick()"
      (keyup.enter)="onClick()"
    >
      <div class="card-icon-wrap" [style.background]="cardIconGradient">
        <mat-icon>emoji_events</mat-icon>
      </div>
      <div class="card-body">
        <div class="card-header">
          <span class="card-label">成就中心</span>
          <mat-icon class="card-arrow">arrow_forward</mat-icon>
        </div>

        <!-- 等级 + 段位色环 + 经验值进度条 -->
        <div class="level-row">
          <div
            class="level-badge"
            [style.background]="levelGradient"
            [style.box-shadow]="
              '0 0 0 3px ' + tierColor + ', 0 4px 12px ' + tierColor + '60'
            "
            [attr.aria-label]="'段位 ' + tierLabel"
            [matTooltip]="'段位：' + tierLabel"
          >
            <span class="level-number">Lv.{{ level.current }}</span>
          </div>
          <div class="level-info">
            <div class="level-title">
              <span class="title-text">{{ levelTitle }}</span>
              <span class="tier-dot" [style.background]="tierColor" [matTooltip]="tierLabel"></span>
            </div>
            <div class="exp-bar">
              <mat-progress-bar
                mode="determinate"
                [value]="level.expProgressPercent"
                color="accent"
              ></mat-progress-bar>
            </div>
            <div class="exp-text" *ngIf="!isMax">
              {{ level.exp }} / {{ level.expToNext }} EXP
            </div>
            <div class="exp-text max-text" *ngIf="isMax">
              <mat-icon class="crown-icon">workspace_premium</mat-icon>
              已达巅峰，解锁创世者之冠
            </div>
          </div>
        </div>

        <!-- 下一称号预告（非满级时） -->
        <div class="next-title-row" *ngIf="!isMax && nextTitle" [matTooltip]="'下一等级预告'">
          <span class="next-label">再 {{ expToNextCount }} EXP 解锁</span>
          <span class="next-title-text">「{{ nextTitleLabel }}」</span>
          <span class="next-badge-mini" *ngIf="nextTitle.nextBadgeIcon">
            {{ nextTitle.nextBadgeIcon }}
          </span>
        </div>

        <!-- 连续打卡 -->
        <div class="streak-row">
          <span class="streak-icon">🔥</span>
          <span class="streak-days">{{ streakDays }}</span>
          <span class="streak-label">连续打卡</span>
          <span class="streak-meta" *ngIf="nextMilestoneDays > 0">
            再 {{ nextMilestoneDays }} 天解锁新成就
          </span>
        </div>

        <!-- 徽章预览 -->
        <div class="badges-preview">
          <div
            *ngFor="let badge of previewBadges"
            class="badge-mini"
            [class.locked]="!badge.unlocked"
            [class]="'rarity-' + badge.rarity"
            [matTooltip]="badge.name + (badge.unlocked ? ' · 已解锁' : ' · 未解锁')"
          >
            <span class="badge-icon">{{ badge.icon }}</span>
          </div>
          <div class="badge-mini badge-more" *ngIf="totalCount > previewBadges.length">
            +{{ totalCount - previewBadges.length }}
          </div>
        </div>
        <div class="progress-summary">
          已解锁 {{ unlockedCount }} / {{ totalCount }} · 完成度 {{ progressPercent }}%
        </div>
      </div>
    </mat-card>
  `,
  styles: [
    `
      :host {
        display: block;
      }

      .core-card {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        min-height: 200px;
        padding: 20px;
        border: none !important;
        border-radius: var(--dash-card-radius, 20px);
        background: var(--stem-bg-surface, #ffffff);
        box-shadow: var(--stem-shadow-sm, 0 1px 3px rgba(5, 150, 105, 0.08));
        cursor: pointer;
        transition:
          transform 200ms ease,
          box-shadow 200ms ease;

        &:hover,
        &:focus-visible {
          outline: none;
          transform: translateY(-4px);
          box-shadow: var(--stem-shadow-card-hover, 0 14px 28px rgba(5, 150, 105, 0.12));
        }

        &:hover .card-arrow,
        &:focus-visible .card-arrow {
          transform: translateX(4px);
          color: var(--stem-warning, #f59e0b);
        }
      }

      .card-icon-wrap {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 56px;
        height: 56px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        color: white;
      }

      .card-icon-wrap mat-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
        color: #ffffff;
      }

      .card-body {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 8px;
        min-width: 0;
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .card-label {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }

      .card-arrow {
        flex-shrink: 0;
        width: 20px;
        height: 20px;
        color: var(--matux-color-text-disabled, #94a3b8);
        font-size: 20px;
        transition:
          transform 200ms ease,
          color 200ms ease;
      }

      .level-row {
        display: flex;
        gap: 10px;
        align-items: center;
        padding: 8px 10px;
        border-radius: 10px;
        background: var(--matux-color-background, #f1f5f9);
      }

      .level-badge {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        color: white;
        transition:
          box-shadow 800ms cubic-bezier(0.34, 1.56, 0.64, 1),
          background 600ms ease;
      }

      .level-number {
        font-size: 11px;
        font-weight: 700;
      }

      .level-info {
        display: flex;
        flex: 1;
        flex-direction: column;
        gap: 2px;
        min-width: 0;
      }

      .level-title {
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .title-text {
        color: var(--matux-color-text-primary, #1c1917);
        font-size: 13px;
        font-weight: 700;
      }

      .tier-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
      }

      .exp-bar {
        height: 6px;
      }

      .exp-text {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .max-text {
        display: flex;
        align-items: center;
        gap: 4px;
        color: var(--stem-tier-star, #ec4899);
        font-weight: 700;
      }

      .crown-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }

      .next-title-row {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 8px;
        background: rgba(245, 158, 11, 0.08);
        font-size: 11px;
        line-height: 1.4;
      }

      .next-label {
        color: var(--matux-color-text-secondary, #57534e);
      }

      .next-title-text {
        color: var(--stem-warning, #f59e0b);
        font-weight: 700;
      }

      .next-badge-mini {
        margin-left: auto;
        font-size: 16px;
      }

      .streak-row {
        display: flex;
        align-items: baseline;
        gap: 4px;
        margin-top: 2px;
      }

      .streak-icon {
        font-size: 20px;
      }

      .streak-days {
        color: var(--stem-rarity-legendary, #b45309);
        font-size: 22px;
        font-weight: 700;
      }

      .streak-label {
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 12px;
      }

      .streak-meta {
        margin-left: auto;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 10px;
      }

      .badges-preview {
        display: flex;
        gap: 6px;
        margin-top: 4px;
      }

      .badge-mini {
        display: flex;
        flex-shrink: 0;
        justify-content: center;
        align-items: center;
        width: 32px;
        height: 32px;
        border-radius: 8px;
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        font-size: 16px;
        transition: transform 200ms ease;
      }

      .badge-mini.rarity-rare {
        background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
      }
      .badge-mini.rarity-epic {
        background: linear-gradient(135deg, #ede9fe 0%, #c4b5fd 100%);
      }
      .badge-mini.rarity-legendary {
        background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%);
      }

      .badge-mini.badge-more {
        background: var(--matux-color-background, #f1f5f9);
        color: var(--matux-color-text-secondary, #57534e);
        font-weight: 700;
      }

      .badge-mini.locked {
        filter: grayscale(0.8);
        opacity: 0.6;
      }

      .progress-summary {
        margin-top: 2px;
        color: var(--matux-color-text-secondary, #57534e);
        font-size: 11px;
        text-align: center;
      }
    `,
  ],
})
export class AchievementCenterCardComponent implements OnInit, OnChanges {
  @Input() snapshot: DashboardSnapshot | null = null;
  @Output() navigate = new EventEmitter<string>();

  private readonly levelTitleService = inject(LevelTitleService);
  private readonly levelEventService = inject(LevelEventService);
  private readonly i18n = inject(I18nService);

  /** 上一次记录的等级 current（去重避免同 level 多次触发） */
  private lastLevelCurrent: number | null = null;

  // ===== 派生数据 =====

  get level(): UserLevel {
    return (
      this.snapshot?.level ?? {
        current: 1,
        title: '初学者',
        exp: 0,
        expToNext: 100,
        totalExp: 0,
        expProgressPercent: 0,
      }
    );
  }

  get currentEntry() {
    return this.levelTitleService.getTitleByLevel(this.level.current);
  }

  get nextTitle() {
    return this.levelTitleService.getNextTitle(this.level.current);
  }

  get isMax(): boolean {
    return this.levelTitleService.isMaxLevel(this.level.current);
  }

  get levelTitle(): string {
    // 优先用 i18n key（level.title.{n}），缺失时 fallback 到阶梯中的 tier 推导
    const key = `level.title.${this.currentEntry.level}`;
    const translated = this.i18n?.translate?.(key);
    if (translated && translated !== key) return translated;
    return this.fallbackTitle(this.currentEntry.level, this.currentEntry.tier);
  }

  get nextTitleLabel(): string {
    if (!this.nextTitle) return '';
    const key = `level.title.${this.nextTitle.level}`;
    const translated = this.i18n?.translate?.(key);
    if (translated && translated !== key) return translated;
    return this.fallbackTitle(this.nextTitle.level, this.nextTitle.tier);
  }

  get tierLabel(): string {
    const key = `level.tier.${this.currentEntry.tier}`;
    const translated = this.i18n?.translate?.(key);
    if (translated && translated !== key) return translated;
    return this.fallbackTier(this.currentEntry.tier);
  }

  get tierColor(): string {
    return this.levelTitleService.getTierColor(this.currentEntry.tier);
  }

  get levelGradient(): string {
    // 段位色渐变背景
    return `linear-gradient(135deg, ${this.tierColor} 0%, ${this.tierColor}cc 100%)`;
  }

  get cardIconGradient(): string {
    return 'var(--stem-gradient-warning, linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%))';
  }

  get expToNextCount(): number {
    return this.levelTitleService.expToNext(this.level.current, this.level.totalExp);
  }

  get streakDays(): number {
    return (this.snapshot as any)?.streakDays ?? 0;
  }

  get nextMilestoneDays(): number {
    const days = this.streakDays;
    const milestones = [7, 14, 30, 60, 100];
    const next = milestones.find((m) => m > days);
    return next ? next - days : 0;
  }

  get previewBadges(): ExtendedAchievementBadge[] {
    return (this.snapshot?.achievements?.badges ?? []).slice(0, 4);
  }

  get unlockedCount(): number {
    return this.snapshot?.achievements?.unlockedCount ?? 0;
  }

  get totalCount(): number {
    return this.snapshot?.achievements?.totalCount ?? 0;
  }

  get progressPercent(): number {
    return this.snapshot?.achievements?.progressPercent ?? 0;
  }

  get ariaLabel(): string {
    return `成就中心：连续打卡 ${this.streakDays} 天，${this.levelTitle} Lv.${this.level.current}，已解锁 ${this.unlockedCount}/${this.totalCount} 徽章`;
  }

  // ===== 生命周期 =====

  ngOnInit(): void {
    this.lastLevelCurrent = this.level.current;
  }

  ngOnChanges(changes: SimpleChanges): void {
    const lvlChange = changes['snapshot'];
    if (!lvlChange) return;
    const newLevel: UserLevel | undefined = lvlChange.currentValue?.level;
    if (!newLevel) return;

    if (this.lastLevelCurrent === null) {
      this.lastLevelCurrent = newLevel.current;
      return;
    }
    if (newLevel.current > this.lastLevelCurrent) {
      const old: UserLevel = {
        current: this.lastLevelCurrent,
        title: '',
        exp: 0,
        expToNext: 0,
        totalExp: 0,
        expProgressPercent: 0,
      };
      const userId = (this.snapshot as any)?.userId ?? null;
      this.levelEventService.emitLevelUp(userId, old, newLevel, newLevel.totalExp);
      this.lastLevelCurrent = newLevel.current;
    }
  }

  onClick(): void {
    this.navigate.emit('/achievements');
  }

  // ===== 文案降级（i18n 缺失时） =====

  private fallbackTitle(level: number, tier: string): string {
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

  private fallbackTier(tier: string): string {
    const FALLBACK: Record<string, string> = {
      bronze: '青铜',
      silver: '白银',
      gold: '黄金',
      diamond: '钻石',
      star: '星耀',
    };
    return FALLBACK[tier] ?? tier;
  }
}
