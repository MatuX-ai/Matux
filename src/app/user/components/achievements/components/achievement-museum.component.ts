/**
 * 成就博物馆组件（P2-B）
 *
 * 主视图：按稀有度分组的展柜（传说 → 史诗 → 稀有 → 少见 → 普通）
 * 每组卡片横向排列，含全球解锁率 + 稀有度光效
 *
 * 点击卡片调用 badgeClick EventEmitter
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AchievementRarity } from '../../../../features/achievement-integration/models/achievement.model';
import type { ExtendedAchievementBadge } from '../../../../features/achievement-integration/models/achievement.model';

interface RarityGroup {
  rarity: AchievementRarity;
  label: string;
  emoji: string;
  color: string;
  gradient: string;
  badgeCount: number;
  unlockedCount: number;
  badges: ExtendedAchievementBadge[];
}

const RARITY_CONFIG: Record<
  AchievementRarity,
  { label: string; emoji: string; color: string; gradient: string }
> = {
  common: {
    label: '普通',
    emoji: '⚪',
    color: '#64748b',
    gradient: 'linear-gradient(135deg, #94a3b8 0%, #475569 100%)',
  },
  uncommon: {
    label: '少见',
    emoji: '🟢',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #34d399 0%, #047857 100%)',
  },
  rare: {
    label: '稀有',
    emoji: '🔵',
    color: '#3b82f6',
    gradient: 'linear-gradient(135deg, #60a5fa 0%, #1d4ed8 100%)',
  },
  epic: {
    label: '史诗',
    emoji: '🟣',
    color: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #a78bfa 0%, #5b21b6 100%)',
  },
  legendary: {
    label: '传说',
    emoji: '🟡',
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, #fbbf24 0%, #b45309 100%)',
  },
};

const RARITY_ORDER: AchievementRarity[] = [
  AchievementRarity.LEGENDARY,
  AchievementRarity.EPIC,
  AchievementRarity.RARE,
  AchievementRarity.UNCOMMON,
  AchievementRarity.COMMON,
];

@Component({
  selector: 'app-achievement-museum',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatProgressBarModule, MatTooltipModule],
  template: `
    <div class="museum-wrapper">
      <div *ngFor="let group of groups" class="rarity-section">
        <!-- 稀有度 header -->
        <div class="rarity-header" [style.background]="group.gradient">
          <div class="header-left">
            <span class="rarity-emoji">{{ group.emoji }}</span>
            <div>
              <h3 class="rarity-label">{{ group.label }}</h3>
              <p class="rarity-sub">
                {{ group.unlockedCount }} / {{ group.badgeCount }} 已解锁
              </p>
            </div>
          </div>
          <div class="header-progress">
            <div class="progress-text">
              {{ unlockedPercent(group) | number: '1.0-0' }}%
            </div>
            <mat-progress-bar
              mode="determinate"
              [value]="unlockedPercent(group)"
              class="rarity-progress"
            ></mat-progress-bar>
          </div>
        </div>

        <!-- 卡片网格 -->
        <div class="badge-grid">
          <div
            *ngFor="let badge of group.badges"
            class="badge-card"
            [class.unlocked]="badge.unlocked"
            [class.locked]="!badge.unlocked"
            [class.rarity-legendary]="badge.rarity === 'legendary' && badge.unlocked"
            [class.rarity-epic]="badge.rarity === 'epic' && badge.unlocked"
            [class.rarity-rare]="badge.rarity === 'rare' && badge.unlocked"
            (click)="badgeClick.emit(badge)"
            [matTooltip]="badge.unlocked ? badge.description : (badge.storyLine || badge.description)"
          >
            <!-- 传说级旋转光环 -->
            <div
              *ngIf="badge.unlocked && badge.rarity === 'legendary'"
              class="legendary-ring"
            ></div>

            <!-- 史诗级脉冲 -->
            <div
              *ngIf="badge.unlocked && badge.rarity === 'epic'"
              class="epic-pulse"
            ></div>

            <!-- 稀有级静态光 -->
            <div
              *ngIf="badge.unlocked && badge.rarity === 'rare'"
              class="rare-glow"
            ></div>

            <!-- 徽章圆 -->
            <div class="badge-circle" [class.locked]="!badge.unlocked">
              <span class="badge-emoji">
                {{ badge.unlocked ? badge.icon : '🔒' }}
              </span>
            </div>

            <!-- 信息 -->
            <div class="badge-info">
              <h4 class="badge-name">{{ badge.name }}</h4>
              <div class="badge-meta">
                <span class="meta-item" *ngIf="badge.unlockedDate">
                  <mat-icon class="meta-icon">calendar_today</mat-icon>
                  {{ badge.unlockedDate | date: 'yyyy-MM-dd' }}
                </span>
                <span class="meta-item" *ngIf="badge.unlockRate !== undefined">
                  <mat-icon class="meta-icon">public</mat-icon>
                  {{ (badge.unlockRate * 100) | number: '1.0-0' }}% 已解锁
                </span>
              </div>
            </div>

            <!-- 未解锁遮罩 -->
            <div *ngIf="!badge.unlocked" class="locked-overlay">
              <mat-icon class="lock-icon">lock</mat-icon>
            </div>
          </div>

          <!-- 空状态 -->
          <div *ngIf="group.badges.length === 0" class="empty-state">
            <span class="empty-emoji">🪨</span>
            <p>暂无{{ group.label }}徽章</p>
          </div>
        </div>
      </div>

      <!-- 总空状态 -->
      <div *ngIf="groups.length === 0" class="global-empty">
        <mat-icon class="empty-icon">museum</mat-icon>
        <p>暂无成就可展示</p>
      </div>
    </div>
  `,
  styleUrls: ['./achievement-museum.component.scss'],
})
export class AchievementMuseumComponent implements OnChanges {
  @Input() badges: ExtendedAchievementBadge[] = [];
  @Output() badgeClick = new EventEmitter<ExtendedAchievementBadge>();

  groups: RarityGroup[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['badges']) {
      this.rebuild();
    }
  }

  unlockedPercent(group: RarityGroup): number {
    if (group.badgeCount === 0) return 0;
    return (group.unlockedCount / group.badgeCount) * 100;
  }

  private rebuild(): void {
    const grouped = new Map<AchievementRarity, ExtendedAchievementBadge[]>();

    for (const rarity of Object.values(AchievementRarity)) {
      grouped.set(rarity, []);
    }

    for (const badge of this.badges) {
      const rarity = badge.rarity ?? AchievementRarity.COMMON;
      const list = grouped.get(rarity) ?? [];
      list.push(badge);
      grouped.set(rarity, list);
    }

    this.groups = RARITY_ORDER.filter((r) => grouped.get(r)!.length > 0).map((rarity) => {
      const badges = grouped.get(rarity)!;
      const cfg = RARITY_CONFIG[rarity];
      return {
        rarity,
        label: cfg.label,
        emoji: cfg.emoji,
        color: cfg.color,
        gradient: cfg.gradient,
        badgeCount: badges.length,
        unlockedCount: badges.filter((b) => b.unlocked).length,
        badges,
      };
    });
  }
}