/**
 * 学习地图主组件（P2-A）
 *
 * 视图：
 * - 地图视图：SVG 节点 + 连线，节点按 tier 分层渲染
 * - 列表视图：扁平列表（兼容旧版技能树）
 *
 * 交互：
 * - Track 切换 Tabs
 * - 视图模式切换
 * - 节点点击 → 打开详情弹窗
 * - 顶部进度条 + 推荐下一步
 *
 * @see 桌面端游戏化P2升级.md §2.3
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import type { StudentLearningProfile } from '../../../core/models/ai-teacher.models';
import { LearningMapService } from '../../../core/services/learning-map.service';
import {
  LearningMapCategory,
  LearningMapConnection,
  LearningMapNode,
  LearningMapNodePosition,
  LearningMapRecommendation,
  LearningMapStatus,
  LearningMapSummary,
  LearningMapTrack,
  LearningMapViewMode,
  NODE_STATUS_CONFIG,
} from '../../../core/models/learning-map.model';
import { LearningMapNodeDetailComponent } from './learning-map-node-detail.component';
import {
  GamificationEventBusService,
} from '../../../core/services/gamification-event-bus.service';
import { LearningMapHighlightService } from '../../../core/services/learning-map-highlight.service';

@Component({
  selector: 'app-learning-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTabsModule,
    MatTooltipModule,
    MatDialogModule,
  ],
  template: `
    <div class="learning-map-container">
      <!-- 顶部 Hero 区 -->
      <div class="lm-hero">
        <div class="hero-text">
          <h2 class="hero-title">
            <span class="title-icon">🗺️</span>
            学习地图
          </h2>
          <p class="hero-subtitle">
            看见你的学习路径，{{ summary.masteredNodes }} / {{ summary.totalNodes }} 技能已掌握
          </p>
        </div>

        <!-- 推荐下一步 -->
        <div class="hero-recommendation" *ngIf="recommendation as rec">
          <div class="rec-label">📍 下一步推荐</div>
          <div class="rec-card">
            <span class="rec-icon">{{ rec.node.icon }}</span>
            <div class="rec-info">
              <div class="rec-name">{{ rec.node.name }}</div>
              <div class="rec-meta">
                {{ rec.reason }} · 预计 {{ rec.estimatedMinutes }} 分钟
              </div>
            </div>
            <button
              mat-flat-button
              color="primary"
              class="rec-btn"
              (click)="openNodeDetail(rec.node)"
            >
              <mat-icon>play_arrow</mat-icon>
              开始
            </button>
          </div>
        </div>

        <!-- 视图切换 -->
        <div class="view-mode-switch">
          <button
            mat-stroked-button
            [class.active]="viewMode === 'map'"
            (click)="setViewMode('map')"
            class="mode-btn"
            matTooltip="地图视图"
          >
            <mat-icon>map</mat-icon>
          </button>
          <button
            mat-stroked-button
            [class.active]="viewMode === 'list'"
            (click)="setViewMode('list')"
            class="mode-btn"
            matTooltip="列表视图"
          >
            <mat-icon>view_list</mat-icon>
          </button>
        </div>
      </div>

      <!-- 整体进度条 -->
      <div class="lm-overall-progress">
        <div class="progress-info">
          <span class="progress-label">整体进度</span>
          <span class="progress-value">{{ overallPercent }}%</span>
        </div>
        <mat-progress-bar
          mode="determinate"
          [value]="overallPercent"
          color="primary"
          class="progress-bar"
        ></mat-progress-bar>
        <div class="progress-stats">
          <span class="stat-item">
            <span class="stat-emoji">✅</span>
            {{ summary.masteredNodes }} 已掌握
          </span>
          <span class="stat-item">
            <span class="stat-emoji">🔄</span>
            {{ summary.inProgressNodes }} 学习中
          </span>
          <span class="stat-item">
            <span class="stat-emoji">⭕</span>
            {{ summary.availableNodes }} 可学
          </span>
          <span class="stat-item">
            <span class="stat-emoji">🔒</span>
            {{ summary.lockedNodes }} 未解锁
          </span>
          <span class="stat-item" *ngIf="summary.legendaryNodes > 0">
            <span class="stat-emoji">🏆</span>
            {{ summary.legendaryNodes }} 传说
          </span>
        </div>
      </div>

      <!-- Track Tabs -->
      <mat-tab-group
        *ngIf="tracks.length > 0"
        [(selectedIndex)]="selectedTabIndex"
        (selectedIndexChange)="onTabChange($event)"
        class="track-tabs"
        mat-stretch-tabs="false"
      >
        <mat-tab *ngFor="let track of tracks" [label]="getTabLabel(track)">
        </mat-tab>
      </mat-tab-group>

      <!-- 当前 Track 视图 -->
      <div class="track-viewport" *ngIf="currentTrack as track">
        <!-- Track header -->
        <div class="track-header">
          <div class="track-icon" [style.background]="track.gradient">
            <span class="track-emoji">{{ track.emoji }}</span>
          </div>
          <div class="track-info">
            <h3 class="track-name">{{ track.name }}</h3>
            <p class="track-desc">{{ track.description }}</p>
          </div>
          <div class="track-stats">
            <div class="track-stat-main">
              <span class="track-stat-percent">{{ trackCompletion(track) }}%</span>
              <span class="track-stat-label">完成度</span>
            </div>
            <div class="track-stat-detail">
              {{ track.masteredNodes }} / {{ track.totalNodes }} 节点
            </div>
          </div>
        </div>

        <!-- 地图视图 -->
        <div *ngIf="viewMode === 'map'" class="map-viewport">
          <div class="map-canvas-wrapper">
            <svg
              class="map-svg"
              [attr.viewBox]="'0 0 ' + mapWidth + ' ' + mapHeight"
              [attr.width]="mapWidth"
              [attr.height]="mapHeight"
              preserveAspectRatio="xMidYMid meet"
            >
              <!-- 渐变定义 -->
                <defs>
                  <linearGradient id="legendary-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#fbbf24" />
                    <stop offset="100%" stop-color="#f59e0b" />
                  </linearGradient>
                  <linearGradient id="mastered-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#34d399" />
                    <stop offset="100%" stop-color="#10b981" />
                  </linearGradient>
                  <linearGradient id="in-progress-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#60a5fa" />
                    <stop offset="100%" stop-color="#3b82f6" />
                  </linearGradient>
                  <radialGradient id="node-glow">
                    <stop offset="0%" stop-color="rgba(255,255,255,0.4)" />
                    <stop offset="100%" stop-color="rgba(255,255,255,0)" />
                  </radialGradient>
                </defs>

                <!-- 连线 -->
                <g class="connections-layer">
                  <path
                    *ngFor="let conn of connections"
                    class="connection"
                    [class.completed]="conn.isCompleted"
                    [class.active]="conn.isActivePath"
                    [class.focused]="isConnectionFocused(conn)"
                    [attr.d]="conn.path"
                    [attr.stroke]="conn.isActivePath ? '#3b82f6' : conn.isCompleted ? '#10b981' : '#cbd5e1'"
                    [attr.stroke-width]="conn.isActivePath ? 3 : 2"
                    [attr.stroke-dasharray]="conn.isActivePath ? '8 4' : 'none'"
                    fill="none"
                  ></path>
                </g>

                <!-- 节点 -->
                <g class="nodes-layer">
                  <g
                    *ngFor="let pos of nodePositions"
                    class="node-group"
                    [class]="'status-' + pos.node.status"
                    [class.highlighting]="pos.node.id === highlightedNodeId"
                    [attr.transform]="'translate(' + pos.x + ',' + pos.y + ')'"
                    (click)="openNodeDetail(pos.node)"
                    [matTooltip]="getNodeTooltip(pos.node)"
                  >
                    <!-- 脉冲光圈（in_progress） -->
                    <circle
                      *ngIf="pos.node.status === 'in_progress'"
                      class="node-pulse"
                      [attr.r]="nodeRadius + 8"
                      fill="none"
                      stroke="#3b82f6"
                      stroke-width="2"
                    ></circle>

                    <!-- 【P3-A-3】高亮光圈（WebSocket 触发） -->
                    <circle
                      *ngIf="pos.node.id === highlightedNodeId"
                      class="node-highlight-halo"
                      [attr.r]="nodeRadius + 12"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="3"
                    ></circle>

                    <!-- 主圆 -->
                    <circle
                      class="node-circle"
                      [attr.r]="nodeRadius"
                      [attr.fill]="getNodeFill(pos.node)"
                      [attr.stroke]="getNodeStroke(pos.node)"
                      [attr.stroke-width]="pos.node.status === 'mastered' || pos.node.status === 'legendary' ? 3 : 2"
                    />

                    <!-- 传说级额外旋转光环 -->
                    <circle
                      *ngIf="pos.node.status === 'legendary'"
                      class="legendary-ring"
                      [attr.r]="nodeRadius + 6"
                      fill="none"
                      stroke="url(#legendary-gradient)"
                      stroke-width="3"
                      stroke-dasharray="6 4"
                    ></circle>

                    <!-- 图标 emoji -->
                    <text
                      class="node-emoji"
                      text-anchor="middle"
                      dominant-baseline="central"
                      [attr.font-size]="nodeRadius"
                    >
                      {{ pos.node.icon }}
                    </text>

                    <!-- 状态标记（角标） -->
                    <g class="status-badge" [attr.transform]="'translate(' + (nodeRadius - 6) + ',' + (-nodeRadius + 6) + ')'">
                      <circle r="9" [attr.fill]="getStatusBadgeColor(pos.node.status)" stroke="white" stroke-width="1.5" />
                      <text
                        text-anchor="middle"
                        dominant-baseline="central"
                        font-size="11"
                        font-weight="bold"
                        fill="white"
                      >
                        {{ getStatusBadgeText(pos.node.status) }}
                      </text>
                    </g>

                    <!-- 节点名称（圆下方） -->
                    <text
                      class="node-name"
                      text-anchor="middle"
                      [attr.y]="nodeRadius + 18"
                      font-size="13"
                      font-weight="600"
                      fill="#1e293b"
                    >
                      {{ pos.node.name }}
                    </text>

                    <!-- 完成度文字（mastered/in_progress） -->
                    <text
                      *ngIf="pos.node.status === 'in_progress' || pos.node.status === 'mastered' || pos.node.status === 'legendary'"
                      class="node-progress-text"
                      text-anchor="middle"
                      [attr.y]="nodeRadius + 34"
                      font-size="11"
                      fill="#64748b"
                    >
                      {{ pos.node.progress | percent }}
                    </text>
                  </g>
                </g>
              </svg>
          </div>

          <!-- 地图图例 -->
          <div class="map-legend">
            <div class="legend-title">状态图例</div>
            <div class="legend-items">
              <div class="legend-item" *ngFor="let key of statusKeys">
                <span class="legend-swatch" [style.background]="statusConfig[key].color"></span>
                <span class="legend-text">{{ statusConfig[key].label }}</span>
                <span class="legend-emoji">{{ statusConfig[key].emoji }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 列表视图 -->
        <div *ngIf="viewMode === 'list'" class="list-viewport">
          <div
            *ngFor="let node of track.nodes"
            class="list-item"
            [class]="'status-' + node.status"
            [class.rarity-legendary]="node.rarity === 'legendary'"
            (click)="openNodeDetail(node)"
          >
            <div class="list-icon">
              <span class="list-icon-emoji">{{ node.icon }}</span>
              <span
                class="list-status-badge"
                [style.background]="statusConfig[node.status].color"
              >
                {{ statusConfig[node.status].emoji }}
              </span>
            </div>
            <div class="list-body">
              <div class="list-name">{{ node.name }}</div>
              <div class="list-desc">{{ node.description }}</div>
              <div class="list-prereq" *ngIf="node.prerequisites.length > 0">
                <mat-icon class="prereq-mat-icon">link</mat-icon>
                前置：
                <span
                  *ngFor="let pid of node.prerequisites; let last = last"
                  class="prereq-name"
                >
                  {{ getPrereqName(track, pid) }}{{ last ? '' : '、' }}
                </span>
              </div>
              <mat-progress-bar
                *ngIf="node.status === 'in_progress' || node.status === 'mastered' || node.status === 'legendary'"
                mode="determinate"
                [value]="node.progress * 100"
                class="list-progress"
                [color]="node.status === 'mastered' ? 'accent' : 'primary'"
              ></mat-progress-bar>
            </div>
            <mat-icon class="list-arrow">chevron_right</mat-icon>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div *ngIf="tracks.length === 0" class="empty-state">
        <mat-icon class="empty-icon">explore_off</mat-icon>
        <p>暂无学习地图数据</p>
      </div>
    </div>
  `,
  styleUrls: ['./learning-map.component.scss'],
})
export class LearningMapComponent implements OnInit, OnDestroy, OnChanges {
  @Input() profile: StudentLearningProfile | null = null;
  /**
   * 【P2-C】高亮指定技能节点（从成就详情跳转过来时使用）
   * - 自动切换到节点所在 track
   * - 自动打开节点详情弹窗
   */
  @Input() highlightSkillId: string | null = null;
  @Output() navigateToCourse = new EventEmitter<{ courseId: string; courseTitle: string }>();
  @Output() navigateToAchievement = new EventEmitter<string>();

  private destroy$ = new Subject<void>();

  // 数据
  tracks: LearningMapTrack[] = [];
  currentTrack: LearningMapTrack | null = null;
  summary: LearningMapSummary = {
    totalNodes: 0,
    masteredNodes: 0,
    inProgressNodes: 0,
    availableNodes: 0,
    lockedNodes: 0,
    legendaryNodes: 0,
    overallPercent: 0,
  };
  recommendation: LearningMapRecommendation | undefined;

  // 视图状态
  viewMode: LearningMapViewMode = 'map';
  selectedTabIndex = 0;
  mapWidth = 880;
  mapHeight = 520;
  nodeRadius = 32;

  // SVG 渲染数据
  nodePositions: LearningMapNodePosition[] = [];
  connections: LearningMapConnection[] = [];

  // 【P3-A-3】当前高亮的节点 ID（来自 highlight service）
  highlightedNodeId: string | null = null;

  // 模板辅助
  readonly statusConfig = NODE_STATUS_CONFIG;
  readonly statusKeys: LearningMapStatus[] = ['locked', 'available', 'in_progress', 'mastered', 'legendary'];
  readonly Math = Math;

  private readonly learningMapService = inject(LearningMapService);
  private readonly dialog = inject(MatDialog);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly highlightService = inject(LearningMapHighlightService);
  private readonly gamificationBus = inject(GamificationEventBusService);

  ngOnInit(): void {
    this.rebuild();
    // 【P3-A-3】订阅高亮状态流（用于模板 class 绑定）
    this.highlightService.highlightedNode$
      .pipe(takeUntil(this.destroy$))
      .subscribe((nodeId) => {
        this.highlightedNodeId = nodeId;
        this.cdr.markForCheck();
      });

    // 【P3-A-2】订阅节点状态更新事件 → 应用增量更新 + 高亮
    this.gamificationBus
      .onNodeStatusUpdated()
      .pipe(takeUntil(this.destroy$))
      .subscribe((event) => {
        this.applyNodeStatusUpdate(event);
      });

    // 【P3-A-2】订阅成就解锁事件 → 关联节点高亮
    this.gamificationBus
      .onAchievementUnlocked()
      .pipe(takeUntil(this.destroy$))
      .subscribe((event) => {
        const skillIds = event.related_skill_ids ?? [];
        if (skillIds.length > 0) {
          // 高亮第一个关联节点 5s
          this.highlightService.highlight(skillIds[0], 5000);
        }
      });
  }

  /**
   * 【P3-A-2】应用节点状态更新：增量更新 tracks + 触发高亮
   */
  private applyNodeStatusUpdate(event: {
    skill_id: string;
    old_status?: string;
    new_status: string;
    progress?: number;
  }): void {
    const result = this.learningMapService.applyEventUpdate(this.tracks, event);
    if (result.changed) {
      this.summary = this.learningMapService.summarize(this.tracks);
      this.recommendation = this.learningMapService.getNextRecommended(this.tracks);
      this.refreshCurrentTrack();
      this.highlightService.highlight(event.skill_id, 5000);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['profile']) {
      this.rebuild();
    }
    if (changes['highlightSkillId'] && this.highlightSkillId) {
      this.highlightNode(this.highlightSkillId);
    }
  }

  /**
   * 【P2-C】高亮指定节点：切换到对应 track 并打开详情弹窗
   */
  private highlightNode(skillId: string): void {
    // 等 tracks 构建完成
    setTimeout(() => {
      let foundNode: LearningMapNode | undefined;
      let foundTrackIndex = -1;

      for (let i = 0; i < this.tracks.length; i++) {
        const t = this.tracks[i];
        const n = t.nodes.find((nd) => nd.id === skillId);
        if (n) {
          foundNode = n;
          foundTrackIndex = i;
          break;
        }
      }

      if (!foundNode) {
        return;
      }

      if (foundTrackIndex >= 0 && foundTrackIndex !== this.selectedTabIndex) {
        this.selectedTabIndex = foundTrackIndex;
        this.refreshCurrentTrack();
        this.cdr.markForCheck();
      }

      // 自动打开节点详情
      setTimeout(() => {
        this.openNodeDetail(foundNode!);
      }, 200);
    }, 100);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ================ 公开方法 ================

  setViewMode(mode: LearningMapViewMode): void {
    this.viewMode = mode;
    this.cdr.markForCheck();
  }

  onTabChange(index: number): void {
    this.selectedTabIndex = index;
    this.refreshCurrentTrack();
  }

  openNodeDetail(node: LearningMapNode): void {
    const dialogRef = this.dialog.open(LearningMapNodeDetailComponent, {
      data: { node, track: this.currentTrack },
      maxWidth: '90vw',
      panelClass: 'learning-map-node-dialog',
    });

    dialogRef.afterClosed().pipe(takeUntil(this.destroy$)).subscribe((result) => {
      if (result?.action === 'learn' && result.courseId) {
        this.navigateToCourse.emit({
          courseId: result.courseId,
          courseTitle: result.courseTitle ?? '',
        });
      } else if (result?.action === 'achievement' && result.achievementId) {
        this.navigateToAchievement.emit(result.achievementId);
      }
    });
  }

  // ================ 模板辅助方法 ================

  getTabLabel(track: LearningMapTrack): string {
    return `${track.emoji} ${track.name}`;
  }

  get overallPercent(): number {
    return Math.round(this.summary.overallPercent * 100);
  }

  trackCompletion(track: LearningMapTrack): number {
    return Math.round(track.completionPercent * 100);
  }

  getNodeTooltip(node: LearningMapNode): string {
    return `${node.name}（${this.statusConfig[node.status].label}）\n${node.description}`;
  }

  getNodeFill(node: LearningMapNode): string {
    if (node.status === 'legendary') return 'url(#legendary-gradient)';
    if (node.status === 'mastered') return 'url(#mastered-gradient)';
    if (node.status === 'in_progress') return 'url(#in-progress-gradient)';
    if (node.status === 'locked') return '#f1f5f9';
    return '#ffffff';
  }

  getNodeStroke(node: LearningMapNode): string {
    return this.statusConfig[node.status].color;
  }

  getStatusBadgeColor(status: LearningMapStatus): string {
    return this.statusConfig[status].color;
  }

  getStatusBadgeText(status: LearningMapStatus): string {
    const map: Record<LearningMapStatus, string> = {
      locked: '🔒',
      available: '○',
      in_progress: '◐',
      mastered: '✓',
      legendary: '★',
    };
    return map[status];
  }

  getPrereqName(track: LearningMapTrack, id: string): string {
    return track.nodes.find((n) => n.id === id)?.name ?? id;
  }

  /**
   * 【P3-A-3】判断连线是否属于当前高亮节点的 incoming path
   */
  isConnectionFocused(conn: LearningMapConnection): boolean {
    return this.highlightedNodeId !== null && conn.to.node.id === this.highlightedNodeId;
  }

  // ================ 私有方法 ================

  private rebuild(): void {
    const dim = this.learningMapService.getMapDimensions();
    this.mapWidth = dim.width;
    this.mapHeight = dim.height;
    this.nodeRadius = this.learningMapService.getNodeRadius();

    this.tracks = this.learningMapService.buildTracksFromProfile(this.profile);
    this.summary = this.learningMapService.summarize(this.tracks);
    this.recommendation = this.learningMapService.getNextRecommended(this.tracks);

    // 选中第一个 main track 或第一个
    const mainTrack = this.tracks.find((t) => t.isMainTrack) ?? this.tracks[0];
    if (mainTrack) {
      this.selectedTabIndex = this.tracks.indexOf(mainTrack);
    }

    this.refreshCurrentTrack();
  }

  private refreshCurrentTrack(): void {
    this.currentTrack = this.tracks[this.selectedTabIndex] ?? null;
    if (this.currentTrack) {
      this.nodePositions = this.learningMapService.layoutNodes(this.currentTrack);
      this.connections = this.learningMapService.generateConnections(this.nodePositions);
    } else {
      this.nodePositions = [];
      this.connections = [];
    }
    this.cdr.markForCheck();
  }
}