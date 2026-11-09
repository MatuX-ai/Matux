/**
 * 用户成就系统组件（P2-B 大改版）
 *
 * 主容器：
 * - Hero 总览 + 4 个视图切换（博物馆 / 时间轴 / 套装 / 画廊）
 * - 全局成就解锁 Toast
 * - 详情弹窗（点击任意徽章触发）
 *
 * @author MatuX Lab
 * @version 2.0.0 (P2-B)
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { AchievementSetsService } from '../../../core/services/achievement-sets.service';
import { AchievementStatsService } from '../../../core/services/achievement-stats.service';
import {
  AchievementDetailDialogComponent,
} from '../../../features/achievement-integration/components/achievement-gallery/achievement-gallery.component';
import {
  AchievementCategory,
  AchievementRarity,
  AchievementStatus,
} from '../../../features/achievement-integration/models/achievement.model';
import type { AchievementSet, ExtendedAchievementBadge } from '../../../features/achievement-integration/models/achievement.model';
import { AchievementService } from '../../../features/achievement-integration/services/achievement.service';
import {
  GamificationEventBusService,
} from '../../../core/services/gamification-event-bus.service';

import { AchievementMuseumComponent } from './components/achievement-museum.component';
import { AchievementProgressHeroComponent } from './components/achievement-progress-hero.component';
import { AchievementSetsComponent } from './components/achievement-sets.component';
import { AchievementTimelineComponent } from './components/achievement-timeline.component';
import { AchievementUnlockToastComponent } from './components/achievement-unlock-toast.component';

/** 视图 Tab 标识 */
type AchievementViewTab = 'museum' | 'timeline' | 'sets' | 'gallery';

interface TabDef {
  id: AchievementViewTab;
  label: string;
  emoji: string;
}

const VIEW_TABS: TabDef[] = [
  { id: 'museum', label: '博物馆', emoji: '🏛️' },
  { id: 'timeline', label: '时间轴', emoji: '🕒' },
  { id: 'sets', label: '套装', emoji: '🎁' },
  { id: 'gallery', label: '画廊', emoji: '🖼️' },
];

@Component({
  selector: 'app-achievements',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatTabsModule,
    MatTooltipModule,
    AchievementMuseumComponent,
    AchievementProgressHeroComponent,
    AchievementSetsComponent,
    AchievementTimelineComponent,
    AchievementUnlockToastComponent,
  ],
  template: `
    <div class="achievements-page">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="page-title">成就系统</h1>
        <p class="page-subtitle">解锁徽章，记录成长历程</p>
      </div>

      <!-- 未登录状态 -->
      <ng-container *ngIf="!hasValidUserId; else loggedIn">
        <mat-card class="info-card">
          <mat-card-content>
            <div class="empty-state">
              <mat-icon class="empty-icon">account_circle</mat-icon>
              <p>请先登录后查看成就信息</p>
              <button mat-stroked-button color="primary" class="login-cta" (click)="goToLogin()">
                <mat-icon>login</mat-icon>
                去登录
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      </ng-container>

      <!-- 已登录：Hero + Tabs -->
      <ng-template #loggedIn>
        <div class="achievements-content">
          <!-- 顶部 Hero 区 -->
          <app-achievement-progress-hero
            [badges]="enhancedBadges"
          ></app-achievement-progress-hero>

          <!-- 视图 Tabs -->
          <mat-tab-group
            class="view-tabs"
            [(selectedIndex)]="selectedTabIndex"
            animationDuration="200ms"
          >
            <mat-tab *ngFor="let tab of tabs">
              <ng-template mat-tab-label>
                <span class="tab-label">
                  <span class="tab-emoji">{{ tab.emoji }}</span>
                  {{ tab.label }}
                </span>
              </ng-template>

              <ng-template matTabContent>
                <!-- 博物馆 -->
                <div *ngIf="tab.id === 'museum'" class="tab-content">
                  <app-achievement-museum
                    [badges]="enhancedBadges"
                    (badgeClick)="openBadgeDetail($event)"
                  ></app-achievement-museum>
                </div>

                <!-- 时间轴 -->
                <div *ngIf="tab.id === 'timeline'" class="tab-content">
                  <app-achievement-timeline
                    [badges]="enhancedBadges"
                    (badgeClick)="openBadgeDetail($event)"
                  ></app-achievement-timeline>
                </div>

                <!-- 套装 -->
                <div *ngIf="tab.id === 'sets'" class="tab-content">
                  <app-achievement-sets
                    [badges]="enhancedBadges"
                    (setClick)="onSetClick($event)"
                  ></app-achievement-sets>
                </div>

                <!-- 兼容旧版画廊 -->
                <div *ngIf="tab.id === 'gallery'" class="tab-content">
                  <div class="gallery-legacy">
                    <h3 class="legacy-title">🖼️ 经典画廊视图</h3>
                    <p class="legacy-desc">
                      此视图保留了 P1 阶段的网格布局，可按分类 / 状态筛选。
                    </p>
                    <button
                      mat-stroked-button
                      color="primary"
                      (click)="onTestUnlock()"
                    >
                      <mat-icon>auto_awesome</mat-icon>
                      模拟新成就解锁（测试 Toast）
                    </button>
                  </div>
                </div>
              </ng-template>
            </mat-tab>
          </mat-tab-group>
        </div>
      </ng-template>

      <!-- 解锁 Toast（全局） -->
      <app-achievement-unlock-toast
        [badge]="latestUnlockedBadge"
        [visible]="showUnlockToast"
        (visibleChange)="onToastDismiss($event)"
      ></app-achievement-unlock-toast>
    </div>
  `,
  styles: [
    `
      /* K12 STEM 探索绿主题 */
      :host {
        --stem-primary: #059669;
        --stem-primary-dark: #047857;
        --stem-primary-light: #10b981;
        --stem-secondary: #0ea5e9;
        --stem-text-primary: #1c1917;
        --stem-text-secondary: #57534e;
        --stem-bg-page: #fafaf9;
        --stem-gradient-explore: linear-gradient(135deg, #059669 0%, #0ea5e9 100%);
      }

      .achievements-page {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px;
        background: var(--stem-bg-page);
        min-height: 100vh;
      }

      .page-header {
        margin-bottom: 24px;
      }

      .page-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0 0 8px 0;
        color: var(--stem-primary-dark, #047857);
      }

      .page-subtitle {
        font-size: 14px;
        color: var(--stem-text-secondary, #57534e);
        margin: 0;
      }

      .achievements-content {
        background: transparent;
      }

      .view-tabs {
        margin-top: 24px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(5, 150, 105, 0.06);
        overflow: hidden;
      }

      .tab-label {
        display: inline-flex;
        gap: 6px;
        align-items: center;
        font-weight: 600;
      }

      .tab-emoji {
        font-size: 16px;
      }

      .tab-content {
        padding: 24px;
      }

      .gallery-legacy {
        text-align: center;
        padding: 64px 24px;
        color: var(--stem-text-secondary, #57534e);
      }

      .legacy-title {
        margin: 0 0 12px;
        color: var(--stem-primary-dark, #047857);
        font-size: 20px;
        font-weight: 700;
      }

      .legacy-desc {
        margin: 0 0 24px;
        font-size: 14px;
        color: var(--stem-text-secondary, #57534e);
      }

      .info-card {
        max-width: 500px;
        margin: 64px auto;
        border-radius: 20px;
        box-shadow: 0 1px 3px rgba(5, 150, 105, 0.08);
      }

      .empty-state {
        text-align: center;
        padding: 48px 24px;
      }

      .empty-icon {
        font-size: 64px;
        width: 64px;
        height: 64px;
        color: var(--stem-primary, #059669);
        margin-bottom: 16px;
      }

      .empty-state p {
        font-size: 16px;
        color: var(--stem-text-secondary, #57534e);
        margin: 0;
      }
    `,
  ],
})
export class AchievementsComponent implements OnInit, OnDestroy {
  currentUserId: number = 0;

  /** 视图 Tab 列表 */
  readonly tabs = VIEW_TABS;
  selectedTabIndex = 0;

  /** 增强后的徽章（含解锁率 / 套装等） */
  enhancedBadges: ExtendedAchievementBadge[] = [];

  /** 解锁 Toast */
  latestUnlockedBadge: ExtendedAchievementBadge | null = null;
  showUnlockToast = false;

  private destroy$ = new Subject<void>();

  private readonly authService = inject(AuthService);
  private readonly achievementService = inject(AchievementService);
  private readonly setsService = inject(AchievementSetsService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly gamificationBus = inject(GamificationEventBusService);
  private readonly statsService = inject(AchievementStatsService);

  /** 【P3-A-2】待显示的解锁事件队列（FIFO，单个展示） */
  private unlockToastQueue: Array<{
    achievementId: string | number;
    name: string;
    rarity: string;
    points?: number;
    icon?: string;
    description?: string;
  }> = [];

  get hasValidUserId(): boolean {
    return this.currentUserId > 0 && !Number.isNaN(this.currentUserId);
  }

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user: User | null) => {
      this.resolveUser(user);
      this.cdr.markForCheck();
    });

    // 【P3-A-2】订阅游戏化事件总线 → 实时解锁 Toast
    this.subscribeGamificationEvents();
  }

  /**
   * 【P3-A-2】订阅游戏化事件总线
   * - achievement_unlocked → 推入 Toast 队列
   * - set_completed → SnackBar 提示套装完成
   */
  private subscribeGamificationEvents(): void {
    this.gamificationBus
      .onAchievementUnlocked()
      .pipe(takeUntil(this.destroy$))
      .subscribe((event) => {
        this.enqueueUnlockToast(event);
      });

    this.gamificationBus
      .onSetCompleted()
      .pipe(takeUntil(this.destroy$))
      .subscribe((event) => {
        const emoji = event.bonus_reward?.emoji ?? '🎁';
        const label = event.bonus_reward?.label ?? event.set_name;
        this.snackBar.open(
          `${emoji} 套装「${event.set_name}」完成！奖励：${label}`,
          '太棒了',
          { duration: 4000 },
        );
        this.cdr.markForCheck();
      });
  }

  /**
   * 将解锁事件入队，并在空闲时播放
   */
  private enqueueUnlockToast(event: {
    achievement_id: string | number;
    name: string;
    rarity?: string;
    points?: number;
    related_skill_ids?: string[];
    icon?: string;
    description?: string;
  }): void {
    // 已解锁的徽章忽略重复推送
    const alreadyUnlocked = this.enhancedBadges.some(
      (b) => String(b.id) === String(event.achievement_id) && b.unlocked,
    );
    if (alreadyUnlocked) return;

    this.unlockToastQueue.push({
      achievementId: event.achievement_id,
      name: event.name,
      rarity: event.rarity ?? 'common',
      points: event.points,
      icon: event.icon,
      description: event.description,
    });

    // 更新徽章列表中的解锁状态
    this.enhancedBadges = this.enhancedBadges.map((badge) =>
      String(badge.id) === String(event.achievement_id)
        ? {
            ...badge,
            unlocked: true,
            unlockedDate: new Date().toISOString(),
          }
        : badge,
    );

    this.processUnlockToastQueue();
    this.cdr.markForCheck();
  }

  /**
   * 处理解锁 Toast 队列：同一时刻仅展示一个
   */
  private processUnlockToastQueue(): void {
    if (this.unlockToastQueue.length === 0) return;
    if (this.showUnlockToast) return; // 当前正在展示

    const next = this.unlockToastQueue.shift()!;
    const badge = this.enhancedBadges.find(
      (b) => String(b.id) === String(next.achievementId),
    );
    if (badge) {
      this.latestUnlockedBadge = badge;
      this.showUnlockToast = true;
      this.cdr.markForCheck();
    } else {
      // 未在本地列表中（可能在另一界面同步）
      const rarityEnum = (Object.values(AchievementRarity) as string[]).includes(next.rarity)
        ? (next.rarity as AchievementRarity)
        : AchievementRarity.COMMON;
      this.latestUnlockedBadge = {
        id: String(next.achievementId),
        name: next.name,
        icon: next.icon ?? '🏆',
        description: next.description ?? '',
        unlocked: true,
        unlockedDate: new Date().toISOString(),
        rarity: rarityEnum,
        pointsValue: next.points ?? 0,
      };
      this.showUnlockToast = true;
      this.cdr.markForCheck();
    }
  }

  private resolveUser(user: User | null): void {
    if (user?.id) {
      const parsed = Number(user.id);
      this.currentUserId = !Number.isNaN(parsed) ? parsed : 0;
    } else {
      const snapshot = this.authService.getCurrentUser?.();
      if (snapshot?.id) {
        const parsed = Number(snapshot.id);
        this.currentUserId = !Number.isNaN(parsed) ? parsed : 0;
      }
    }
    if (this.currentUserId > 0) {
      // 【P0-C 修复】建立 /ws/gamification 连接（幂等），
      //   否则成就中心只能靠轮询，拿不到实时解锁推送。
      this.gamificationBus.connect(this.currentUserId);
      this.loadBadges();
    }
  }

  private loadBadges(): void {
    this.achievementService
      .getAchievements(this.currentUserId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((badges) => {
        this.enhancedBadges = this.setsService.enhanceBadges(badges);
        // 【P3-A-1】加载后端真实解锁率（如可用，覆盖 mock 值）
        this.loadRealUnlockStats();
        this.cdr.markForCheck();
      });
  }

  /**
   * 【P3-A-1】拉取后端真实解锁率 / 总持有者，覆盖本地 mock 数据。
   * 失败时静默降级，保留 mock 值。
   */
  private loadRealUnlockStats(): void {
    this.statsService
      .loadStats()
      .then(() => this.applyRealUnlockStats())
      .catch(() => {
        // 失败时保留 mock 值，不报错
      });
  }

  /**
   * 将后端真实 stats 合并到 enhancedBadges
   */
  private applyRealUnlockStats(): void {
    let changed = false;
    this.enhancedBadges = this.enhancedBadges.map((badge) => {
      const real = this.statsService.getStats(String(badge.id));
      if (!real) return badge;
      changed = true;
      return {
        ...badge,
        unlockRate: real.globalUnlockRate,
        totalHolders: real.totalHolders,
      };
    });
    if (changed) this.cdr.markForCheck();
  }

  /** 未登录提示 "去登录" 按钮跳转到登录页 */
  goToLogin(): void {
    void this.router.navigate(['/auth/login']);
  }

  /**
   * 点击徽章 → 打开详情弹窗
   */
  openBadgeDetail(badge: ExtendedAchievementBadge): void {
    const setInfo = badge.setId ? this.setsService.getSetById(badge.setId) : undefined;

    this.dialog.open(AchievementDetailDialogComponent, {
      data: {
        id: badge.id,
        name: badge.name,
        icon: badge.icon,
        description: badge.description,
        status: badge.unlocked ? AchievementStatus.COMPLETED : AchievementStatus.IN_PROGRESS,
        category: badge.category ?? AchievementCategory.LEARNING,
        rarity: badge.rarity ?? AchievementRarity.COMMON,
        progress: badge.unlocked ? 1 : 0,
        target: 1,
        unlockedDate: badge.unlockedDate,
        // P2-B 增强字段
        unlockRate: badge.unlockRate,
        totalHolders: badge.totalHolders,
        relatedSkillIds: badge.relatedSkillIds,
        setId: badge.setId,
        setName: setInfo?.name,
        obtainedFrom: badge.obtainedFrom,
        storyLine: badge.storyLine,
        pointsValue: badge.pointsValue,
        // P2-C 联动：点击关联学习节点时跳转到学习地图
        onNavigateToSkill: (skillId: string) => this.navigateToSkill(skillId),
      },
      panelClass: 'achievement-detail-dialog',
      maxWidth: '90vw',
    });
  }

  /**
   * 点击套装卡片 → 跳转到该套装的第一个未解锁成就详情
   */
  onSetClick(set: AchievementSet): void {
    const progress = this.setsService
      .computeAllProgress(this.enhancedBadges)
      .find((p) => p.set.id === set.id);

    const next = progress?.remaining[0];
    if (next) {
      this.openBadgeDetail(next);
    } else {
      this.snackBar.open(`套装：${set.name}`, '知道了', { duration: 2000 });
    }
  }

  /**
   * 【P2-C 联动】跳转到学习地图并高亮指定节点
   */
  private navigateToSkill(skillId: string): void {
    void this.router.navigate(['/user/learning-profile'], {
      queryParams: { highlightSkill: skillId },
    });
  }

  /**
   * 测试 Toast - 手动模拟新成就解锁
   */
  onTestUnlock(): void {
    const candidate = this.enhancedBadges.find((b) => !b.unlocked);
    if (!candidate) {
      this.snackBar.open('所有成就都已解锁 🎉', '知道了', { duration: 2000 });
      return;
    }
    // 模拟解锁状态
    this.latestUnlockedBadge = {
      ...candidate,
      unlocked: true,
      unlockedDate: new Date().toISOString(),
    };
    this.showUnlockToast = true;
    this.cdr.markForCheck();
  }

  onToastDismiss(visible: boolean): void {
    this.showUnlockToast = visible;
    if (!visible) {
      // 延迟清空 badge，让动画完成
      setTimeout(() => {
        this.latestUnlockedBadge = null;
        // 【P3-A-2】清空后尝试处理队列中的下一个事件
        this.processUnlockToastQueue();
        this.cdr.markForCheck();
      }, 500);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
