# -*- coding: utf-8 -*-
"""
R-01 growth-trajectory 修复:
当 backend 不可达时,service 层 catchError 返回 mock 数据,组件正常渲染。
但用户感知不到当前是演示数据。修复: 在 page 组件顶部添加后端状态 banner。
"""
path = r'I:\iMato\src\app\user\components\growth-trajectory\growth-trajectory.component.ts'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加 ModuleStatusService import
old_imports = """import type { GrowthTrajectory } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { GrowthTrajectoryComponent } from '../../../shared/components/growth-trajectory/growth-trajectory.component';"""

new_imports = """import type { GrowthTrajectory } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { ModuleStatusService } from '../../../core/services/module-status.service';
import { GrowthTrajectoryComponent } from '../../../shared/components/growth-trajectory/growth-trajectory.component';"""

assert old_imports in content, "old_imports not found"
content = content.replace(old_imports, new_imports)

# 2. 修改 template: 在 page-header 之前添加 fallback banner
old_template = """  template: `
    <div class="growth-page">
      <div class="page-header">
        <h1 class="page-title">我的成长轨迹</h1>
        <span class="update-time" *ngIf="currentDate">{{ currentDate }}</span>
      </div>

      <app-growth-trajectory *ngIf="trajectory" [trajectory]="trajectory"></app-growth-trajectory>"""

new_template = """  template: `
    <div class="growth-page">
      <!-- 【P2-R01 修复】后端不可达时顶部提示,告知用户当前展示的是演示数据 -->
      <div *ngIf="!backendAvailable && trajectory" class="fallback-banner" role="status">
        <mat-icon>cloud_off</mat-icon>
        <span>当前后端不可达,以下展示为演示数据。真实数据将在后端恢复后自动同步。</span>
        <button mat-stroked-button color="primary" (click)="retryLoad()">
          <mat-icon>refresh</mat-icon>
          重试
        </button>
      </div>

      <div class="page-header">
        <h1 class="page-title">我的成长轨迹</h1>
        <span class="update-time" *ngIf="currentDate">{{ currentDate }}</span>
      </div>

      <app-growth-trajectory *ngIf="trajectory" [trajectory]="trajectory"></app-growth-trajectory>"""

assert old_template in content, "old_template not found"
content = content.replace(old_template, new_template)

# 3. 添加 banner 样式
old_styles_close = """      .retry-btn {
        margin-top: 16px;
      }
    `,
  ],
})"""

new_styles_close = """      .retry-btn {
        margin-top: 16px;
      }
      /* 【P2-R01 修复】兑底 banner 样式:明显但不影响主要布局 */
      .fallback-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        margin-bottom: 16px;
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        font-size: 13px;
        color: #991b1b;
      }
      .fallback-banner mat-icon {
        color: #ef4444;
      }
      .fallback-banner span {
        flex: 1;
      }
    `,
  ],
})"""

assert old_styles_close in content, "old_styles_close not found"
content = content.replace(old_styles_close, new_styles_close)

# 4. 修改 class: 添加 backendAvailable 属性 + 订阅 moduleStatus
old_class_start = """export class GrowthTrajectoryPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  trajectory: GrowthTrajectory | null = null;
  error = false;
  currentDate = '';

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}"""

new_class_start = """export class GrowthTrajectoryPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  trajectory: GrowthTrajectory | null = null;
  error = false;
  currentDate = '';

  /** 【P2-R01 修复】后端是否可用,用于驱动兑底 banner 显示 */
  backendAvailable = true;

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private moduleStatusService: ModuleStatusService,
    private cdr: ChangeDetectorRef
  ) {}"""

assert old_class_start in content, "old_class_start not found"
content = content.replace(old_class_start, new_class_start)

# 5. 在 ngOnInit 中订阅 healthy$, 在 ngOnDestroy 中清理
old_ngoninit_end = """    // 【P1-3 修复】兜底：N 秒后仍未拿到 trajectory → 切到 error,并提供手动重试
    setTimeout(() => {
      if (!this.trajectory && !this.error) {
        this.error = true;
        this.cdr.markForCheck();
      }
    }, LOAD_TIMEOUT_MS);
  }"""

new_ngoninit_end = """    // 【P1-3 修复】兜底：N 秒后仍未拿到 trajectory → 切到 error,并提供手动重试
    setTimeout(() => {
      if (!this.trajectory && !this.error) {
        this.error = true;
        this.cdr.markForCheck();
      }
    }, LOAD_TIMEOUT_MS);

    // 【P2-R01 修复】订阅后端健康状态,驱动兑底 banner 显示。
    // takeUntil(destroy$) 防止组件销毁后回调泄漏。
    this.moduleStatusService.healthy$
      .pipe(takeUntil(this.destroy$))
      .subscribe((healthy) => {
        this.backendAvailable = healthy;
        this.cdr.markForCheck();
      });
  }"""

assert old_ngoninit_end in content, "old_ngoninit_end not found"
content = content.replace(old_ngoninit_end, new_ngoninit_end)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: GrowthTrajectoryPageComponent R-01 修复完成,添加了后端状态 banner")
