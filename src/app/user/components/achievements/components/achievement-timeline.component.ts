/**
 * 成就时间轴组件（P2-B）
 *
 * 按解锁日期分组（按月聚合），垂直时间轴展示
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
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import type { ExtendedAchievementBadge } from '../../../../features/achievement-integration/models/achievement.model';

interface MonthGroup {
  monthKey: string;
  monthLabel: string;
  badges: ExtendedAchievementBadge[];
}

@Component({
  selector: 'app-achievement-timeline',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="timeline-wrapper">
      <div *ngFor="let group of monthGroups" class="month-group">
        <!-- 月份分隔 -->
        <div class="month-divider">
          <span class="month-label">{{ group.monthLabel }}</span>
          <span class="month-count">{{ group.badges.length }} 项</span>
          <span class="month-line"></span>
        </div>

        <!-- 时间轴条目 -->
        <div class="timeline-track">
          <div
            *ngFor="let badge of group.badges"
            class="timeline-item"
            [class]="'rarity-' + (badge.rarity || 'common')"
            (click)="badgeClick.emit(badge)"
            [matTooltip]="badge.storyLine || badge.description"
          >
            <div class="timeline-dot"></div>
            <div class="timeline-card">
              <span class="card-emoji">{{ badge.icon }}</span>
              <div class="card-body">
                <div class="card-name">{{ badge.name }}</div>
                <div class="card-meta">
                  <span class="meta-date" *ngIf="badge.unlockedDate">
                    {{ badge.unlockedDate | date: 'MM-dd' }}
                  </span>
                  <span class="meta-rarity" *ngIf="badge.rarity">
                    {{ rarityLabel(badge.rarity) }}
                  </span>
                </div>
              </div>
              <mat-icon class="card-arrow">chevron_right</mat-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div *ngIf="monthGroups.length === 0" class="empty-state">
        <mat-icon class="empty-icon">history_toggle_off</mat-icon>
        <p>解锁第一个徽章，开启你的时间轴</p>
      </div>
    </div>
  `,
  styleUrls: ['./achievement-timeline.component.scss'],
})
export class AchievementTimelineComponent implements OnChanges {
  @Input() badges: ExtendedAchievementBadge[] = [];
  @Output() badgeClick = new EventEmitter<ExtendedAchievementBadge>();

  monthGroups: MonthGroup[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['badges']) {
      this.rebuild();
    }
  }

  rarityLabel(rarity: string): string {
    const map: Record<string, string> = {
      common: '普通',
      uncommon: '少见',
      rare: '稀有',
      epic: '史诗',
      legendary: '传说',
    };
    return map[rarity] ?? rarity;
  }

  private rebuild(): void {
    const unlocked = this.badges
      .filter((b) => b.unlocked && b.unlockedDate)
      .sort((a, b) => (b.unlockedDate ?? '').localeCompare(a.unlockedDate ?? ''));

    const groups = new Map<string, ExtendedAchievementBadge[]>();
    for (const badge of unlocked) {
      const date = new Date(badge.unlockedDate!);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const list = groups.get(monthKey) ?? [];
      list.push(badge);
      groups.set(monthKey, list);
    }

    this.monthGroups = Array.from(groups.entries())
      .sort(([a], [b]) => b.localeCompare(a))
      .map(([monthKey, badges]) => ({
        monthKey,
        monthLabel: this.formatMonthLabel(monthKey),
        badges,
      }));
  }

  private formatMonthLabel(monthKey: string): string {
    const [year, month] = monthKey.split('-');
    return `${year} 年 ${parseInt(month, 10)} 月`;
  }
}