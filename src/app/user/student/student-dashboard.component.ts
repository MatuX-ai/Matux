/**
 * 学生用户中心 - 学习仪表板（重构版）
 *
 * 核心职责（重构后）：
 * - 订阅 StudentDashboardDataService 的单一数据流
 * - 编排 4 个核心 dashboard 卡 + 3 个次要 widget 的渲染
 * - 提供页面级交互（导航、自定义布局）
 *
 * 数据加载、WebSocket、Mock fallback 已下沉至 StudentDashboardDataService。
 *
 * @see student-dashboard-data.service.ts 数据服务
 * @see PRD 6.5 节 学生仪表板线框图
 */

import { animate, state, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { DashboardLayoutService } from '../../core/services/dashboard-layout.service';
import { ROUTES } from '../../routes.const';
import { DashboardLayoutDialogComponent } from '../../shared/components/dashboard-layout-dialog/dashboard-layout-dialog.component';
import { ExpGainToastComponent } from '../../shared/components/exp-gain-toast/exp-gain-toast.component';
import { FloatingAiAssistantComponent } from '../../shared/components/floating-ai-assistant/floating-ai-assistant.component';
import { LearningCalendarHeatmapComponent } from '../../shared/components/learning-calendar-heatmap/learning-calendar-heatmap.component';
import { LevelUpDialogComponent } from '../../shared/components/level-up-dialog/level-up-dialog.component';
import { MockModeBannerComponent } from '../../shared/components/mock-mode-banner/mock-mode-banner.component';
import { StudentMaterialDashboardComponent } from '../../shared/components/student-material-dashboard/student-material-dashboard.component';
import { StudentStatusBarComponent } from '../../shared/components/student-status-bar/student-status-bar.component';
import { UnifiedCourseCardComponent } from '../../shared/components/unified-course-card/unified-course-card.component';

import type { DailyTask, DashboardSnapshot } from './services/student-dashboard-data.service';
import { StudentDashboardDataService } from './services/student-dashboard-data.service';
import { AchievementCenterCardComponent } from './widgets/core-cards/achievement-center-card.component';
import { CreationCenterCardComponent } from './widgets/core-cards/creation-center-card.component';
import { LearningCenterCardComponent } from './widgets/core-cards/learning-center-card.component';
import { SocialCenterCardComponent } from './widgets/core-cards/social-center-card.component';
import { DailyTasksWidgetComponent } from './widgets/daily-tasks-widget.component';
import { WeeklyLeaderboardWidgetComponent } from './widgets/weekly-leaderboard-widget.component';

@Component({
  selector: 'app-student-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('fadeInUp', [
      state('void', style({ opacity: 0, transform: 'translateY(16px)' })),
      transition('void => *', animate('0.4s ease-out')),
    ]),
  ],
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatChipsModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatDialogModule,
    LearningCalendarHeatmapComponent,
    StudentMaterialDashboardComponent,
    UnifiedCourseCardComponent,
    StudentStatusBarComponent,
    FloatingAiAssistantComponent,
    LearningCenterCardComponent,
    AchievementCenterCardComponent,
    CreationCenterCardComponent,
    SocialCenterCardComponent,
    DailyTasksWidgetComponent,
    WeeklyLeaderboardWidgetComponent,
    MockModeBannerComponent,
  ],
  templateUrl: './student-dashboard.component.html',
  styleUrls: ['./student-dashboard.component.scss'],
})
export class StudentDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  /** 路由常量，供模板使用 */
  readonly ROUTES = ROUTES;

  /** 当前仪表板快照 */
  snapshot: DashboardSnapshot | null = null;
  /** 当前日期（中文格式） */
  currentDate: string = '';
  /** 未读通知数 */
  notificationCount = 0;

  constructor(
    private dataService: StudentDashboardDataService,
    private cdr: ChangeDetectorRef,
    private router: Router,
    public layout: DashboardLayoutService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.updateCurrentDate();
    // 主动触发加载（如果尚未加载）
    this.dataService.loadSnapshot().pipe(takeUntil(this.destroy$)).subscribe();
    this.dataService.snapshot$.pipe(takeUntil(this.destroy$)).subscribe((snapshot) => {
      this.snapshot = snapshot;
      this.notificationCount = this.computeNotificationCount(snapshot);
      this.cdr.markForCheck();
    });
  }

  /**
   * 根据快照计算通知数（解锁新成就/任务奖励/连续天数里程碑）
   */
  private computeNotificationCount(snapshot: DashboardSnapshot | null): number {
    if (!snapshot) return 0;
    let count = 0;
    const recentBadges = snapshot.achievements.badges.filter(
      (b) => b.unlocked && b.unlockedDate && this.isRecent(b.unlockedDate)
    );
    count += recentBadges.length;
    if (snapshot.weeklyStats.streakDays > 0 && snapshot.weeklyStats.streakDays % 7 === 0) {
      count += 1;
    }
    return count;
  }

  /**
   * 是否为最近 7 天内
   */
  private isRecent(dateStr: string): boolean {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    return diffMs >= 0 && diffMs <= 7 * 24 * 60 * 60 * 1000;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /** 打开仪表盘布局设置对话框 */
  openLayoutDialog(): void {
    this.dialog.open(DashboardLayoutDialogComponent, {
      width: '480px',
      maxWidth: '90vw',
    });
  }

  /** 导航到指定路由 */
  navigateTo(path: string): void {
    void this.router.navigate([path]);
  }

  /** 完成任务（委托 service，触发 EXP 飞升和升级 modal） */
  onTaskCompleted(task: DailyTask): void {
    const oldLevel = this.snapshot?.level;
    this.dataService.completeTask(task.id).subscribe((result) => {
      if (!result) return;
      // 显示 EXP 飞升动画
      this.dialog.open(ExpGainToastComponent, {
        data: { amount: task.rewardExp, reason: task.title },
        panelClass: 'exp-gain-dialog',
        hasBackdrop: false,
        autoFocus: false,
      });
      // 升级时弹出 modal
      if (result.leveledUp && result.newLevel && oldLevel) {
        setTimeout(() => {
          this.dialog.open(LevelUpDialogComponent, {
            data: { oldLevel, newLevel: result.newLevel },
            panelClass: 'level-up-dialog-panel',
            disableClose: false,
          });
        }, 500);
      }
    });
  }

  /** 跳转推荐课程 */
  onRecommendedCourseClick(course: { title: string; difficulty: string }): void {
    void this.router.navigate(['/user/courses'], {
      queryParams: {
        courseTitle: course.title,
        level: course.difficulty,
      },
    });
  }

  /** 更新当前日期 */
  private updateCurrentDate(): void {
    const now = new Date();
    const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    const date = now.getDate();
    const day = days[now.getDay()];
    this.currentDate = `${year}年${month}月${date}日${day}`;
  }
}
