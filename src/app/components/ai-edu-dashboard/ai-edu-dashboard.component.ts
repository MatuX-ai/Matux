/**
 * AI 教育仪表板组件
 *
 * 【P2-2 修复】扩展为完整的仪表板：
 * - 展示后端 /api/v1/org/{org_id}/ai-edu/modules 返回的模块列表
 * - 显示学习进度（statistics）
 * - 快捷入口：编程课、测验
 * - 加载失败时降级显示静态示例
 */
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  NgZone,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { Subject, catchError, of, timeout } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface AIEduModule {
  id: number;
  module_code: string;
  name: string;
  description: string;
  category: string;
  expected_lessons: number;
  expected_duration_minutes: number;
}

interface AIEduStatistics {
  total_courses: number;
  completed_courses: number;
  in_progress_courses: number;
  not_started_courses: number;
  total_time_hours: number;
  average_quiz_score: number;
  average_code_score: number;
  total_points: number;
  completion_rate: number;
}

/**
 * 【P2-2 修复】后端不可用时的静态示例（浏览器/无后端场景）
 */
const FALLBACK_MODULES: AIEduModule[] = [
  {
    id: 1,
    module_code: 'basic_concepts_01',
    name: 'AI 基本概念入门',
    description: '人工智能基础概念介绍，适合小学 1-6 年级学生',
    category: 'basic_concepts',
    expected_lessons: 3,
    expected_duration_minutes: 60,
  },
  {
    id: 2,
    module_code: 'ml_intro_02',
    name: '机器学习导论',
    description: '理解机器学习的基本流程：数据、特征、模型、评估',
    category: 'machine_learning',
    expected_lessons: 4,
    expected_duration_minutes: 90,
  },
  {
    id: 3,
    module_code: 'python_for_ai_03',
    name: 'AI 编程实践（Python）',
    description: '用 Python 编写第一个 AI 程序：图像分类、文本预测',
    category: 'programming',
    expected_lessons: 5,
    expected_duration_minutes: 120,
  },
];

@Component({
  selector: 'app-ai-edu-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatButtonModule, HttpClientModule],
  changeDetection: ChangeDetectionStrategy.Default,
  template: `
    <div class="ai-edu-dashboard">
      <header class="dashboard-header">
        <h2>
          <mat-icon>school</mat-icon>
          AI 教育学习中心
        </h2>
        <p class="subtitle">从这里开启你的人工智能学习之旅</p>
      </header>

      <!-- 进度卡片 -->
      <section class="progress-card" *ngIf="statistics">
        <h3>我的学习进度</h3>
        <div class="progress-grid">
          <div class="progress-item">
            <span class="value">{{ statistics.completed_courses }}</span>
            <span class="label">已完成课程</span>
          </div>
          <div class="progress-item">
            <span class="value">{{ statistics.in_progress_courses }}</span>
            <span class="label">进行中</span>
          </div>
          <div class="progress-item">
            <span class="value">{{ statistics.total_time_hours }}h</span>
            <span class="label">累计学习时长</span>
          </div>
          <div class="progress-item">
            <span class="value">{{ statistics.average_quiz_score }}</span>
            <span class="label">平均测验分</span>
          </div>
        </div>
        <div class="completion-bar">
          <div class="bar-fill" [style.width.%]="statistics.completion_rate"></div>
        </div>
        <p class="completion-text">
          完成率 {{ statistics.completion_rate }}%
        </p>
      </section>

      <!-- 模块列表 -->
      <section class="modules-section">
        <div class="section-header">
          <h3>推荐学习模块</h3>
          <span *ngIf="loading" class="loading-badge">加载中…</span>
        </div>

        <div *ngIf="loading && modules.length === 0" class="module-skeleton">
          <div class="skeleton-card" *ngFor="let i of [1,2,3]"></div>
        </div>

        <!-- 【P2-2 修复】模块卡列表 + 重试按钮（限时兑底，6s 后不依赖后端也能继续使用） -->
        <div *ngIf="error && modules.length === 0" class="fallback-banner">
          <mat-icon>info</mat-icon>
          <span>{{ error }}</span>
          <button mat-stroked-button (click)="loadModules()">重新加载</button>
        </div>

        <!-- 【P2-2 BUG02 修复】顶部 fallback 提示: 后端不可达时优先显示,
             即使 modules 已有兜底数据也提示用户当前为离线模式 -->
        <div *ngIf="error && modules.length > 0" class="fallback-banner fallback-banner-top">
          <mat-icon>cloud_off</mat-icon>
          <span>{{ error }}</span>
          <button mat-stroked-button color="warn" (click)="loadModules()">
            <mat-icon>refresh</mat-icon>
            重新加载
          </button>
        </div>

        <div class="modules-grid" *ngIf="!loading || modules.length > 0">
          <div
            class="module-card"
            *ngFor="let module of modules"
            (click)="enterModule(module)"
            (keyup.enter)="enterModule(module)"
            tabindex="0"
            role="button"
          >
            <div class="module-icon">
              <mat-icon>{{ iconForCategory(module.category) }}</mat-icon>
            </div>
            <h4 class="module-name">{{ module.name }}</h4>
            <p class="module-desc">{{ module.description }}</p>
            <div class="module-meta">
              <span><mat-icon>menu_book</mat-icon> {{ module.expected_lessons }} 节</span>
              <span><mat-icon>schedule</mat-icon> {{ module.expected_duration_minutes }} 分钟</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 快捷入口 -->
      <section class="quick-links">
        <h3>快捷入口</h3>
        <div class="links-grid">
          <a class="quick-link" routerLink="/ai-edu/coding">
            <mat-icon>code</mat-icon>
            <span>编程实战</span>
          </a>
          <a class="quick-link" routerLink="/exam">
            <mat-icon>quiz</mat-icon>
            <span>在线测验</span>
          </a>
          <a class="quick-link" routerLink="/user/reports">
            <mat-icon>insights</mat-icon>
            <span>学习报告</span>
          </a>
        </div>
      </section>
    </div>
  `,
  styles: [
    `
      .ai-edu-dashboard {
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
        color: var(--matux-color-text-primary, #1c1917);
      }
      .dashboard-header {
        margin-bottom: 24px;
      }
      .dashboard-header h2 {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .subtitle {
        color: var(--matux-color-text-secondary, #57534e);
        margin: 0;
      }
      .progress-card,
      .modules-section,
      .quick-links {
        background: white;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
      }
      .progress-card h3,
      .modules-section h3,
      .quick-links h3 {
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 16px;
      }
      .progress-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
      }
      .progress-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
      }
      .progress-item .value {
        font-size: 24px;
        font-weight: 700;
        color: var(--matux-color-primary, #059669);
      }
      .progress-item .label {
        font-size: 13px;
        color: var(--matux-color-text-secondary, #57534e);
        margin-top: 4px;
      }
      .completion-bar {
        background: rgba(0, 0, 0, 0.06);
        border-radius: 999px;
        height: 8px;
        overflow: hidden;
      }
      .bar-fill {
        background: var(--matux-color-primary, #059669);
        height: 100%;
        transition: width 0.4s ease;
      }
      .completion-text {
        text-align: right;
        font-size: 12px;
        color: var(--matux-color-text-secondary, #57534e);
        margin: 8px 0 0;
      }
      .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
      }
      .section-header h3 {
        margin: 0;
      }
      .loading-badge {
        font-size: 12px;
        color: var(--matux-color-text-secondary, #57534e);
      }
      .modules-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
      }
      .module-card {
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 12px;
        padding: 20px;
        cursor: pointer;
        transition:
          transform 0.2s ease,
          box-shadow 0.2s ease,
          border-color 0.2s ease;
        background: #fafaf9;
      }
      .module-card:hover,
      .module-card:focus {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(5, 150, 105, 0.15);
        border-color: var(--matux-color-primary, #059669);
        outline: none;
      }
      .module-icon mat-icon {
        font-size: 32px;
        height: 32px;
        width: 32px;
        color: var(--matux-color-primary, #059669);
      }
      .module-name {
        font-size: 16px;
        font-weight: 600;
        margin: 8px 0;
      }
      .module-desc {
        font-size: 13px;
        color: var(--matux-color-text-secondary, #57534e);
        margin: 0 0 12px;
        line-height: 1.5;
      }
      .module-meta {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: var(--matux-color-text-secondary, #57534e);
      }
      .module-meta mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
        vertical-align: middle;
        margin-right: 4px;
      }
      .module-skeleton {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
      }
      .skeleton-card {
        height: 180px;
        border-radius: 12px;
        background: linear-gradient(
          90deg,
          rgba(0, 0, 0, 0.05) 25%,
          rgba(0, 0, 0, 0.1) 50%,
          rgba(0, 0, 0, 0.05) 75%
        );
        background-size: 200% 100%;
        animation: skeleton-shimmer 1.2s infinite;
      }
      @keyframes skeleton-shimmer {
        to {
          background-position: -200% 0;
        }
      }
      .fallback-banner {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: rgba(245, 158, 11, 0.1);
        border-radius: 8px;
        font-size: 13px;
        color: #92400e;
        margin-top: 12px;
      }
      /* 【P2-2 BUG02 修复】顶部兑底 banner 更显眼,与 grid 分离 */
      .fallback-banner-top {
        margin-top: 0;
        margin-bottom: 16px;
        background: rgba(239, 68, 68, 0.1);
        color: #991b1b;
        border-left: 4px solid #ef4444;
        font-weight: 500;
      }
      .links-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 12px;
      }
      .quick-link {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        border-radius: 12px;
        background: #fafaf9;
        text-decoration: none;
        color: var(--matux-color-text-primary, #1c1917);
        font-weight: 500;
        border: 1px solid transparent;
        transition: all 0.2s ease;
      }
      .quick-link:hover {
        background: var(--matux-color-primary, #059669);
        color: white;
        border-color: var(--matux-color-primary, #059669);
      }
      .quick-link mat-icon {
        font-size: 24px;
        height: 24px;
        width: 24px;
      }
    `,
  ],
})
export class AIEduDashboardComponent implements OnInit, OnDestroy {
  modules: AIEduModule[] = [];
  statistics: AIEduStatistics | null = null;
  loading = true;
  error: string | null = null;

  /**
   * 【P2-2 修复】默认从 localStorage 或注入的用户信息推断 orgId，
   * 缺少时退回 1 以匹配后端临时测试路由。
   */
  private readonly orgId = this.resolveOrgId();

  /** 【P2-2 BUG02 修复】内部销毁信号,避免 setTimeout 兑底回调对已销毁组件调用 */
  private destroy$ = new Subject<void>();

  /** 【P2-2 BUG02 修复】兑底定时器句柄,用于 ngOnDestroy 时清理 */
  private fallbackTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.loadModules();
    this.loadStatistics();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.fallbackTimer !== null) {
      clearTimeout(this.fallbackTimer);
      this.fallbackTimer = null;
    }
  }

  /**
   * 【P2-2 BUG02 修复】加载后端模块列表,失败时降级到静态示例。
   * 三层防护：
   * 1) RxJS timeout({ each: 6000 }) — pipe 级超时
   * 2) HttpTimeoutInterceptor (5s) — 全局超时(可能在 pipe 之前触发)
   * 3) setTimeout(6000) runOutsideAngular — 兑底,确保任何边界条件下 6s 后
   *    一定切换到 fallback,避免 stuck loading
   */
  loadModules(): void {
    this.loading = true;
    if (this.fallbackTimer !== null) {
      clearTimeout(this.fallbackTimer);
      this.fallbackTimer = null;
    }
    this.http
      .get<{ success: boolean; data: AIEduModule[] }>(
        `/api/v1/org/${this.orgId}/ai-edu/modules`
      )
      .pipe(
        timeout({ each: 6000 }),
        catchError(() => {
          this.applyModulesFallback('后端不可达，已切换到本地推荐目录');
          return of({ success: true, data: FALLBACK_MODULES });
        })
      )
      .pipe(takeUntil(this.destroy$))
      .subscribe((resp) => {
        if (resp?.data) {
          this.modules = resp.data;
        } else if (this.modules.length === 0) {
          this.modules = FALLBACK_MODULES;
        }
        this.loading = false;
        if (this.fallbackTimer !== null) {
          clearTimeout(this.fallbackTimer);
          this.fallbackTimer = null;
        }
        this.cdr.markForCheck();
      });

    // 兑底定时器：6s 后若仍在 loading,强制切到 fallback。
    this.zone.runOutsideAngular(() => {
      this.fallbackTimer = setTimeout(() => {
        if (!this.loading) return;
        this.zone.run(() => {
          this.applyModulesFallback('后端响应超时，已切换到本地推荐目录');
        });
      }, 6000);
    });
  }

  /**
   * 【P2-2 BUG02 修复】统一的 modules fallback 应用入口。
   * setTimeout 兑底和 catchError 走同一逻辑,避免状态不一致。
   */
  private applyModulesFallback(reason: string): void {
    if (this.modules.length === 0) {
      this.modules = FALLBACK_MODULES;
    }
    this.error = reason;
    this.loading = false;
    if (this.fallbackTimer !== null) {
      clearTimeout(this.fallbackTimer);
      this.fallbackTimer = null;
    }
    this.cdr.markForCheck();
  }
  
  /**
   * 【P2-2 修复】加载学习进度统计；失败时使用零值兑底
   * 同样增加 6s 限时
   */
  loadStatistics(): void {
    const fallback: { success: boolean; data: AIEduStatistics } = {
      success: true,
      data: {
        total_courses: 3,
        completed_courses: 0,
        in_progress_courses: 0,
        not_started_courses: 3,
        total_time_hours: 0,
        average_quiz_score: 0,
        average_code_score: 0,
        total_points: 0,
        completion_rate: 0,
      },
    };
    this.http
      .get<{ success: boolean; data: AIEduStatistics }>(
        `/api/v1/org/${this.orgId}/ai-edu/progress/statistics`
      )
      .pipe(
        // 【P2-2 修复】6s 超时兑底
        timeout({ each: 6000 }),
        catchError(() => of(fallback))
      )
      .pipe(takeUntil(this.destroy$))
      .subscribe((resp) => {
        this.statistics = resp?.data ?? null;
        this.cdr.markForCheck();
      });
  }

  /**
   * 【P2-2 修复】从 user_data 解析 orgId，缺省回退到 1
   */
  private resolveOrgId(): number {
    try {
      const raw = localStorage.getItem('user_data');
      if (raw) {
        const parsed = JSON.parse(raw) as { orgId?: number; org_id?: number };
        const id = parsed?.orgId ?? parsed?.org_id;
        if (typeof id === 'number' && Number.isFinite(id)) return id;
      }
    } catch {
      /* 忽略 */
    }
    return 1;
  }

  iconForCategory(category: string): string {
    const map: Record<string, string> = {
      basic_concepts: 'psychology',
      machine_learning: 'model_training',
      programming: 'code',
      ai_capabilities: 'auto_awesome',
    };
    return map[category] ?? 'school';
  }

  enterModule(module: AIEduModule): void {
    // 简化处理：跳转到 AI 编程课，后续可改为 module 详情页
    console.info('[AIEduDashboard] enterModule:', module.module_code);
  }
}
