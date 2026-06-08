/**
 * 学生用户中心 - 学习仪表板
 *
 * 展示学生的学习进度、课程、成绩等信息
 * 集成多来源学习系统，显示跨机构/兴趣班的学习进度
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
import { forkJoin, Observable, of, Subject } from 'rxjs';
import { catchError, map, switchMap, takeUntil, tap } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import type { User } from '../../core/models/auth.models';
import {
  AiEduWebSocketService,
  type ProgressUpdateData,
} from '../../core/services/ai-edu-websocket.service';
import { AuthService } from '../../core/services/auth.service';
import { CourseEnrollmentService } from '../../core/services/course-enrollment.service';
import { DashboardLayoutService } from '../../core/services/dashboard-layout.service';
import { MultiSourceLearningService } from '../../core/services/multi-source-learning.service';
import { UnifiedCourseService } from '../../core/services/unified-course.service';
import type {
  LearningSource,
  LearningSourceType,
  UnifiedProgressStats,
} from '../../models/multi-source-learning.models';
import { LearningSourceTypeLabels } from '../../models/multi-source-learning.models';
import type { CourseEnrollment, UnifiedCourse } from '../../models/unified-course.models';
import { DashboardLayoutDialogComponent } from '../../shared/components/dashboard-layout-dialog/dashboard-layout-dialog.component';

import { ROUTES } from '../../routes.const';

// Mock 数据（从独立模块导入）
import {
  getMockProgressStats,
  getMockLearningSources,
  getMockAchievementBadges,
  type MockAchievementBadge,
} from './student-dashboard.mock';

/**
 * 用户扩展属性接口（后端可能返回的非标准字段）
 */
interface UserExtendedFields {
  org_id?: number;
  grade?: string;
  [key: string]: unknown;
}

/**
 * 统一获取用户的 org_id，确保类型安全
 */
function getUserOrgId(user: User | null): number {
  if (!user) return 1; // 默认值

  // 尝试从扩展字段获取 org_id
  const extended = user as unknown as UserExtendedFields;
  if (typeof extended.org_id === 'number' && extended.org_id > 0) {
    return extended.org_id;
  }

  // 尝试从 id 推导（如果有的话）
  return 1; // 默认值
}

interface QuickTool {
  icon: string;
  label: string;
  color: string;
  bgClass: string;
}

interface RecentCourse {
  title: string;
  teacher: string;
  progress: number;
  duration: string;
  level: string;
  sourceType?: string;
  sourceName?: string;
}

interface RecommendedCourse {
  title: string;
  teacher: string;
  description: string;
  duration: string;
  level: string;
}

// 【注意】AchievementBadge 接口已迁移到 student-dashboard.mock.ts，使用 MockAchievementBadge

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
  ],
  templateUrl: './student-dashboard.component.html',
  styleUrls: ['./student-dashboard.component.scss'],
})
export class StudentDashboardComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private wsConnected = false;  // 【修复】防止重复连接

  // 路由常量，供模板使用
  readonly ROUTES = ROUTES;

  currentUser: User | null = null;
  currentDate: string = '';
  progressStats: UnifiedProgressStats | null = null;
  learningSources: LearningSource[] = [];
  loadingProgress = false;
  loadingSources = false;

  recentCourses: RecentCourse[] = [
    {
      title: '机器人基础入门',
      teacher: '小M老师',
      progress: 75,
      duration: '20小时',
      level: '初级',
      sourceType: 'school_curriculum',
      sourceName: '校本部',
    },
    {
      title: 'AI 编程与机器学习',
      teacher: '阿博特老师',
      progress: 45,
      duration: '30 小时',
      level: '中级',
      sourceType: 'institution',
      sourceName: '创新机器人培训中心',
    },
    {
      title: 'Python 机器人控制',
      teacher: '小 X 老师',
      progress: 90,
      duration: '15 小时',
      level: '初级',
      sourceType: 'school_interest',
      sourceName: '校内兴趣班',
    },
  ];

  // 常用工具列表
  quickTools: QuickTool[] = [
    { icon: 'code', label: '代码', color: '#3b82f6', bgClass: 'bg-blue' },
    { icon: 'view_in_ar', label: '3D模型', color: '#f97316', bgClass: 'bg-orange' },
    { icon: 'camera_alt', label: 'AR扫描', color: '#22c55e', bgClass: 'bg-green' },
    { icon: 'smart_toy', label: 'AI助手', color: '#3b82f6', bgClass: 'bg-blue' },
  ];

  // AI 推荐项目
  aiRecommendations = [
    {
      title: '智能感应小夜灯',
      description: '利用光敏电阻实现环境光自适应控制。',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    },
    {
      title: 'PWM 舵机控制',
      description: '使用 PWM 信号控制舵机转动到指定角度。',
      gradient: 'linear-gradient(135deg, #f97316 0%, #ef4444 100%)',
    },
    {
      title: 'AI 视觉识别入门',
      description: '掌握图像处理和模式识别的基础概念。',
      gradient: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
    },
  ];

  // 硬件设备信息
  hardwareInfo = {
    name: 'ESP32 开发板',
    status: '在线',
    battery: 85,
    wifi: '-42dBm',
  };

  recommendedCourses: RecommendedCourse[] = [
    {
      title: 'ROS机器人操作系统',
      teacher: '博士坦老师',
      description: '学习 ROS 机器人操作系统的核心概念，包括节点通信、导航 SLAM、机械臂控制等。',
      duration: '40 小时',
      level: '高级',
    },
    {
      title: '深度学习与计算机视觉',
      teacher: '小 M 老师',
      description: '掌握深度学习算法在计算机视觉中的应用，实现目标检测、人脸识别等 AI 功能。',
      duration: '35 小时',
      level: '中级',
    },
  ];

  // 添加缺失的属性
  enrolledCourses$: Observable<
    Array<{ course: UnifiedCourse; progress: number; enrollment: CourseEnrollment }>
  > = of([]);  // 【修复】初始化为空数组，避免undefined
  recommendedCourses$!: Observable<UnifiedCourse[]>;
  orgNameMap: Map<number, string> = new Map();
  loadingEnrolledCourses = false;

  /** 成就徽章列表 */
  achievementBadges: MockAchievementBadge[] = getMockAchievementBadges();

  get unlockedAchievementsCount(): number {
    return this.achievementBadges.filter((b) => b.unlocked).length;
  }

  get achievementProgress(): number {
    return this.achievementBadges.length > 0
      ? Math.round((this.unlockedAchievementsCount / this.achievementBadges.length) * 100)
      : 0;
  }

  constructor(
    private authService: AuthService,
    private multiSourceService: MultiSourceLearningService,
    private unifiedCourseService: UnifiedCourseService,
    private courseEnrollmentService: CourseEnrollmentService,
    private wsService: AiEduWebSocketService,
    private cdr: ChangeDetectorRef,
    private router: Router,
    public layout: DashboardLayoutService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.loadCurrentUser();
    this.updateCurrentDate();
  }

  /** 打开仪表盘布局设置对话框 */
  openLayoutDialog(): void {
    this.dialog.open(DashboardLayoutDialogComponent, {
      width: '480px',
      maxWidth: '90vw',
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

  /** 导航到指定路由 */
  navigateTo(path: string): void {
    void this.router.navigate([path]);
  }

  /**
   * 安全获取用户ID（处理大数字精度问题）
   * @returns 用户ID或null
   */
  private getUserId(): string | null {
    if (!this.currentUser?.id) {
      console.warn('[Dashboard] 无效的用户ID: 未定义');
      return null;
    }

    // 保持原始字符串格式，避免数字精度丢失
    const userId = String(this.currentUser.id);

    // 验证是否为有效的非空字符串
    if (!userId || userId.trim() === '') {
      console.warn('[Dashboard] 无效的用户ID: 空字符串');
      return null;
    }

    // 验证是否为数字格式
    if (!/^\d+$/.test(userId)) {
      console.warn('[Dashboard] 无效的用户ID: 非数字格式', userId);
      return null;
    }

    return userId;
  }

  /**
   * 获取用户ID的数字形式（仅在需要计算时使用）
   * 注意：可能损失精度，仅用于非关键计算
   */
  private getUserIdAsNumber(): number | null {
    const userIdStr = this.getUserId();
    if (!userIdStr) return null;

    const userIdNum = Number(userIdStr);
    if (isNaN(userIdNum) || userIdNum <= 0) {
      return null;
    }
    return userIdNum;
  }

  private loadCurrentUser(): void {
    // 【优化】检查是否已有用户数据，避免重复请求
    const cachedUser = this.authService.getCurrentUser();
    const userIdStr = this.getUserId();

    if (cachedUser?.id && userIdStr !== null) {
      console.log('📦 使用缓存的用户数据:', cachedUser.username);
      this.currentUser = cachedUser;
      // 使用数字形式进行API调用（可能损失精度但不关键）
      const userIdNum = this.getUserIdAsNumber();
      if (userIdNum !== null) {
        this.triggerDataLoad(userIdNum);
      } else {
        console.warn('[Dashboard] 无法获取有效用户ID');
        this.loadMockData();
      }
      return;
    }

    // 没有缓存，订阅用户数据流
    this.authService.currentUser$.pipe(
      takeUntil(this.destroy$),
      catchError((error) => {
        console.error('[Dashboard] 获取用户信息失败:', error);
        this.handleLoadError('用户信息加载失败');
        return of(null);
      })
    ).subscribe((user) => {
      if (!user) {
        console.warn('[Dashboard] 用户数据为空');
        this.loadMockData();
        return;
      }

      this.currentUser = user;
      const uidStr = this.getUserId();
      const uidNum = this.getUserIdAsNumber();
      if (user?.id && uidStr !== null && uidNum !== null) {
        console.log('📥 获取到用户数据:', user.username, 'ID:', uidStr);
        this.triggerDataLoad(uidNum);
      } else {
        console.warn('[Dashboard] 无效用户数据，加载Mock数据');
        this.loadMockData();
      }
    });
  }

  /**
   * 处理数据加载失败
   * @param message 错误消息
   */
  private handleLoadError(message: string): void {
    this.loadingProgress = false;
    this.loadingSources = false;
    // 可选：显示全局错误通知
    console.error('[Dashboard]', message);
  }

  /** 触发数据加载（统一入口） */
  private triggerDataLoad(userId: number): void {
    // 标记所有加载状态
    this.loadingProgress = true;
    this.loadingSources = true;
    this.loadingEnrolledCourses = true;

    // 并行加载数据，每个方法独立处理错误
    forkJoin({
      progress: this.loadProgressStats(userId).pipe(catchError(err => {
        console.error('[Dashboard] 学习进度加载失败:', err);
        return of(getMockProgressStats());
      })),
      sources: this.loadLearningSources(userId).pipe(catchError(err => {
        console.error('[Dashboard] 学习来源加载失败:', err);
        return of({ total: 0, items: [] });
      })),
      courses: this.loadUnifiedCourses(userId).pipe(catchError(err => {
        console.error('[Dashboard] 统一课程加载失败:', err);
        return of([]);
      }))
    }).pipe(
      takeUntil(this.destroy$),
      catchError((err) => {
        console.error('[Dashboard] 并行加载失败:', err);
        this.handleLoadError('部分数据加载失败，请刷新重试');
        return of(null);
      })
    ).subscribe((result) => {
      if (!result) {
        // 加载失败，显示错误状态
        return;
      }

      // 更新进度统计
      if (result.progress) {
        this.progressStats = result.progress;
      }
      this.loadingProgress = false;

      // 更新学习来源
      if (result.sources?.items) {
        this.learningSources = result.sources.items;
      }
      this.loadingSources = false;

      console.log('✅ Dashboard 数据加载完成');
      // WebSocket 连接单独处理
      this.connectWebSocket(userId);
    });
  }

  /**
   * 建立 WebSocket 连接，实现数据自动刷新
   */
  private connectWebSocket(userId: number): void {
    // 【修复】防止重复连接
    if (this.wsConnected) {
      console.warn('[Dashboard] WebSocket 已连接，跳过重复连接');
      return;
    }
    this.wsConnected = true;
    
    // 使用 environment 配置 WebSocket URL
    const baseUrl = (environment as { wsUrl?: string }).wsUrl || window.location.origin;

    // 使用类型安全的 org_id 获取函数
    const orgId = getUserOrgId(this.currentUser);

    this.wsService.connect(userId, orgId, baseUrl);

    // 监听进度更新，自动刷新仪表板数据
    this.wsService
      .onProgressUpdate()
      .pipe(
        takeUntil(this.destroy$),
        catchError((error) => {
          console.error('[Dashboard] WebSocket 进度更新错误:', error);
          return of(null);
        })
      )
      .subscribe((update: ProgressUpdateData | null) => {
        if (!update) return;
        console.warn('[Dashboard] 收到进度更新:', update);
        // 【修复】订阅Observable以确保请求发出，添加takeUntil防止内存泄漏
        this.loadProgressStats(userId).pipe(
          takeUntil(this.destroy$)
        ).subscribe({
          next: (stats) => {
            this.progressStats = stats;
            this.cdr.markForCheck();
          },
          error: (err) => console.error('[Dashboard] 刷新进度失败:', err)
        });
      });

    // 监听连接状态
    this.wsService.connectionStatus$.pipe(
      takeUntil(this.destroy$),
      catchError((error) => {
        console.error('[Dashboard] WebSocket 连接状态错误:', error);
        return of('error');
      })
    ).subscribe((status) => {
      if (status === 'connected') {
        console.warn('[Dashboard] WebSocket 已连接，实时数据已启用');
      } else if (status === 'error' || status === 'disconnected') {
        console.warn('[Dashboard] WebSocket 连接异常，状态:', status);
      }
    });
  }

  /**
   * 加载统一课程数据
   * @param userId 用户ID（接受字符串保持精度，API需要时转换为number）
   * @returns Observable<Array<{ course: UnifiedCourse; progress: number; enrollment: CourseEnrollment }>>
   */
  private loadUnifiedCourses(
    userId: string | number
  ): Observable<Array<{ course: UnifiedCourse; progress: number; enrollment: CourseEnrollment }>> {
    // 转换为数字用于API调用（可能损失精度但不关键）
    const userIdNum = typeof userId === 'string' ? Number(userId) : userId;
    
    // 加载已报名课程
    const enrolled$ = this.courseEnrollmentService
      .getUserEnrollments(userIdNum, {
        page: 1,
        page_size: 10,
      })
      .pipe(
        takeUntil(this.destroy$),
        switchMap((enrollments) => {
          const courseIds = enrollments.items.map((e) => e.course_id);
          if (courseIds.length === 0) {
            return of([]);
          }

          // 获取课程详情
          return forkJoin(
            courseIds.map((courseId) =>
              this.unifiedCourseService.getCourse(courseId).pipe(
                catchError((err) => {
                  console.warn('[Dashboard] 获取课程详情失败:', courseId, err);
                  return of(null);  // 返回null表示获取失败
                })
              )
            )
          ).pipe(
            map((courses) =>
              enrollments.items.map((enrollment, index) => ({
                course: courses[index],
                progress: enrollment.progress_percentage || 0,
                enrollment,
              })).filter(item => item.course !== null) as Array<{ course: UnifiedCourse; progress: number; enrollment: CourseEnrollment }>
            )
          );
        }),
        catchError((error) => {
          console.error('[Dashboard] 获取已报名课程失败:', error);
          return of([]);
        }),
        tap((items: Array<{ course: UnifiedCourse; progress: number; enrollment: CourseEnrollment }>) => {
          this.enrolledCourses$ = of(items);
          this.loadingEnrolledCourses = false;
        })
      );

    // 加载推荐课程
    this.recommendedCourses$ = this.unifiedCourseService.getRecommendedCourses(userIdNum, 8).pipe(
      takeUntil(this.destroy$),
      catchError((error) => {
        console.error('[Dashboard] 获取推荐课程失败:', error);
        return this.unifiedCourseService.getNewestCourses(8);
      })
    );

    // 加载组织名称映射
    this.loadOrgNames();

    return enrolled$;
  }

  /**
   * 加载组织名称映射
   */
  private loadOrgNames(): void {
    // 简化实现：实际应从组织服务获取
    this.orgNameMap.set(1, '校本部');
    this.orgNameMap.set(2, '创新机器人培训中心');
    this.orgNameMap.set(3, '在线学习平台');
  }

  /**
   * 获取组织名称
   */
  getOrgName(orgId: number): string {
    return this.orgNameMap.get(orgId) ?? `机构 ${orgId}`;
  }

  /**
   * 继续学习
   */
  onContinueLearning(courseId: number): void {
    void this.router.navigate(['/student/course', courseId, 'learn']);
  }

  /**
   * 报名课程
   */
  onEnrollCourse(courseId: number): void {
    if (!this.currentUser?.id) {
      console.warn('[Dashboard] 报名失败：用户未登录');
      return;
    }

    // 使用字符串形式保持精度，仅在API需要时转换为number
    const userIdStr = String(this.currentUser.id);
    const userIdNum = Number(userIdStr);
    if (isNaN(userIdNum) || userIdNum <= 0) {
      console.warn('[Dashboard] 报名失败：无效的用户ID');
      return;
    }

    // 使用类型安全的 org_id 获取函数
    const orgId = getUserOrgId(this.currentUser);

    this.courseEnrollmentService
      .enrollInCourse(courseId, userIdNum, orgId)
      .pipe(
        takeUntil(this.destroy$),
        catchError((error) => {
          console.error('[Dashboard] 报名失败:', error);
          // 返回 null 以便订阅者处理
          return of(null);
        })
      )
      .subscribe((result) => {
        if (!result) {
          // 报名失败
          console.warn('[Dashboard] 报名服务返回失败');
          return;
        }
        // 报名成功，刷新已报名课程列表
        console.log('[Dashboard] 报名成功:', result);
        // 使用字符串形式的userId
        this.loadUnifiedCourses(userIdStr);
      });
  }

  /**
   * 查看课程详情
   */
  onViewCourseDetail(courseId: number): void {
    void this.router.navigate(['/student/course', courseId]);
  }

  /**
   * 导航到课程库
   */
  navigateToCourseLibrary(): void {
    void this.router.navigate(['/student/courses']);
  }

  ngOnDestroy(): void {
    // 1. 先停止接受新的数据
    this.destroy$.next();
    this.destroy$.complete();

    // 2. 等待所有异步操作完成后再断开 WebSocket
    // 使用 setTimeout 确保所有订阅都有机会处理最后的取消信号
    // 【修复】增加延迟时间到500ms，确保网络请求有足够时间完成
    setTimeout(() => {
      try {
        this.wsService.disconnect();
      } catch (error) {
        console.warn('[Dashboard] WebSocket 断开连接时出错:', error);
      }
    }, 500);
  }

  /**
   * 加载学习进度统计
   * @returns Observable<UnifiedProgressStats>
   */
  private loadProgressStats(userId: number): Observable<UnifiedProgressStats> {
    return this.multiSourceService
      .getUserUnifiedProgress(userId)
      .pipe(
        takeUntil(this.destroy$),
        catchError((err) => {
          console.error('[Dashboard] 加载学习进度失败:', err);
          // API失败时使用mock数据
          return of(getMockProgressStats());
        })
      );
  }

  /**
   * 加载学习来源
   * @returns Observable<{ total: number; items: LearningSource[] }>
   */
  private loadLearningSources(userId: number): Observable<{ total: number; items: LearningSource[] }> {
    return this.multiSourceService
      .getUserLearningSources(userId, { includeInactive: true })
      .pipe(
        takeUntil(this.destroy$),
        catchError((err) => {
          console.error('[Dashboard] 加载学习来源失败:', err);
          // API失败时使用mock数据
          return of({ total: 0, items: getMockLearningSources() });
        })
      );
  }

  /**
   * 加载Mock数据（用于模拟账号）
   */
  private loadMockData(): void {
    this.progressStats = getMockProgressStats();
    this.learningSources = getMockLearningSources();
    this.loadingProgress = false;
    this.loadingSources = false;
  }

  getSourceTypeLabel(type: string): string {
    return LearningSourceTypeLabels[type] || type;
  }

  getSourceIcon(type: string): string {
    const icons: Record<string, string> = {
      school_curriculum: 'school',
      school_interest: 'palette',
      institution: 'business',
      self_study: 'self_improvement',
      online_platform: 'computer',
      competition: 'emoji_events',
    };
    return icons[type] || 'source';
  }

  getSourceIconByName(type: string): string {
    return this.getSourceIcon(type);
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: '学习中',
      inactive: '未激活',
      completed: '已完成',
      suspended: '已暂停',
    };
    return labels[status] || status;
  }
}
