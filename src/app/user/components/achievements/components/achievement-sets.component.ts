/**
 * 成就套装视图组件（P2-B）
 *
 * 每个套装一张卡片，含进度环、套装图标、完成奖励
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
import { MatTooltipModule } from '@angular/material/tooltip';

import { AchievementSetsService } from '../../../../core/services/achievement-sets.service';
import type { AchievementSet, AchievementSetProgress } from '../../../../features/achievement-integration/models/achievement.model';
import type { ExtendedAchievementBadge } from '../../../../features/achievement-integration/models/achievement.model';

@Component({
  selector: 'app-achievement-sets',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  template: `
    <div class="sets-wrapper">
      <div *ngFor="let progress of setProgress" class="set-card" [class.completed]="progress.isCompleted">
        <!-- 完成光效 -->
        <div *ngIf="progress.isCompleted" class="completion-glow"></div>

        <div class="set-icon" [style.background]="progress.set.gradient">
          <span class="set-emoji">{{ progress.set.emoji }}</span>
          <!-- 完成标记 -->
          <div *ngIf="progress.isCompleted" class="completed-badge">
            <mat-icon>verified</mat-icon>
          </div>
        </div>

        <div class="set-body">
          <div class="set-header">
            <h3 class="set-name">{{ progress.set.name }}</h3>
            <span class="set-count">{{ progress.unlockedCount }} / {{ progress.totalCount }}</span>
          </div>
          <p class="set-desc">{{ progress.set.description }}</p>

          <!-- 进度条 -->
          <div class="set-progress">
            <div class="progress-track">
              <div
                class="progress-fill"
                [style.background]="progress.set.gradient"
                [style.width.%]="progress.completionPercent * 100"
              ></div>
            </div>
            <span class="progress-percent">
              {{ (progress.completionPercent * 100) | number: '1.0-0' }}%
            </span>
          </div>

          <!-- Bonus 奖励 -->
          <div *ngIf="progress.set.bonusReward as reward" class="bonus-section">
            <div class="bonus-label">🎁 完成奖励</div>
            <div class="bonus-content">
              <span class="bonus-emoji">{{ reward.emoji }}</span>
              <span class="bonus-name">{{ reward.label }}</span>
            </div>
          </div>

          <!-- 剩余成就 -->
          <div *ngIf="!progress.isCompleted && progress.remaining.length > 0" class="remaining-section">
            <div class="remaining-label">剩余 {{ progress.remaining.length }} 项：</div>
            <div class="remaining-list">
              <span
                *ngFor="let b of progress.remaining.slice(0, 3)"
                class="remaining-chip"
              >
                {{ b.icon }} {{ b.name }}
              </span>
              <span *ngIf="progress.remaining.length > 3" class="remaining-more">
                +{{ progress.remaining.length - 3 }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空 -->
      <div *ngIf="setProgress.length === 0" class="empty-state">
        <mat-icon class="empty-icon">workspaces</mat-icon>
        <p>暂无套装数据</p>
      </div>
    </div>
  `,
  styleUrls: ['./achievement-sets.component.scss'],
})
export class AchievementSetsComponent implements OnChanges {
  @Input() badges: ExtendedAchievementBadge[] = [];
  @Output() setClick = new EventEmitter<AchievementSet>();

  setProgress: AchievementSetProgress[] = [];

  private readonly setsService = inject(AchievementSetsService);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['badges']) {
      this.setProgress = this.setsService.computeAllProgress(this.badges);
    }
  }
}