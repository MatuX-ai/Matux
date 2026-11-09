/**
 * 成就解锁 Toast 组件（P2-B）
 *
 * 全屏动画：
 * - 中央成就图标 3D 翻转 + 缩放
 * - 周围金色光线放射
 * - 滑入式 Toast
 * - 自动 5s 消失
 *
 * 用法：
 * <app-achievement-unlock-toast
 *   [badge]="latestBadge"
 *   [visible]="showToast"
 *   (visibleChange)="onToastDismiss()"
 * ></app-achievement-unlock-toast>
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
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import type { ExtendedAchievementBadge } from '../../../../features/achievement-integration/models/achievement.model';

@Component({
  selector: 'app-achievement-unlock-toast',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, MatButtonModule, MatIconModule],
  template: `
    <div *ngIf="visible && badge" class="toast-overlay" (click)="dismiss()">
      <!-- 放射光线背景 -->
      <div class="rays-bg">
        <div class="ray" *ngFor="let r of rayAngles" [style.transform]="'rotate(' + r + 'deg)'"></div>
      </div>

      <!-- 中央徽章 -->
      <div class="badge-stage" [class.rarity-legendary]="badge.rarity === 'legendary'">
        <div class="stage-ring"></div>
        <div class="stage-ring stage-ring-2"></div>
        <div class="badge-flip">
          <span class="badge-emoji">{{ badge.icon }}</span>
        </div>
      </div>

      <!-- 文案 -->
      <div class="toast-text">
        <div class="toast-title">🎉 成就解锁！</div>
        <div class="toast-name">{{ badge.name }}</div>
        <div class="toast-desc" *ngIf="badge.storyLine">
          {{ badge.storyLine }}
        </div>
        <div class="toast-meta">
          <span class="rarity-tag" [class]="'rarity-' + (badge.rarity || 'common')">
            {{ rarityLabel(badge.rarity) }}
          </span>
          <span class="points-tag" *ngIf="badge.pointsValue">
            +{{ badge.pointsValue }} 积分
          </span>
        </div>
      </div>

      <!-- 关闭提示 -->
      <div class="dismiss-hint">点击任意处关闭</div>
    </div>
  `,
  styleUrls: ['./achievement-unlock-toast.component.scss'],
})
export class AchievementUnlockToastComponent implements OnChanges {
  @Input() badge: ExtendedAchievementBadge | null = null;
  @Input() visible = false;
  @Output() visibleChange = new EventEmitter<boolean>();

  /** 放射光线角度（8 条） */
  readonly rayAngles = [0, 45, 90, 135, 180, 225, 270, 315];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && this.visible) {
      this.startAutoDismiss();
    }
  }

  rarityLabel(rarity?: string): string {
    const map: Record<string, string> = {
      common: '普通',
      uncommon: '少见',
      rare: '稀有',
      epic: '史诗',
      legendary: '传说',
    };
    return map[rarity ?? 'common'] ?? '普通';
  }

  dismiss(): void {
    this.visible = false;
    this.visibleChange.emit(false);
  }

  private startAutoDismiss(): void {
    setTimeout(() => {
      if (this.visible) {
        this.dismiss();
      }
    }, 5000);
  }
}