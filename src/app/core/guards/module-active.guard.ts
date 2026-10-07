/**
 * 模块激活路由守卫
 *
 * 在导航到需要特定后端模块的页面时，检查模块是否已激活。
 * 如果模块未激活，自动触发激活流程并显示加载提示。
 *
 * 路由配置示例：
 * {
 *   path: 'vircadia',
 *   canActivate: [ModuleActiveGuard],
 *   data: { requiredModule: 'ar_vr' },
 *   ...
 * }
 */

import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRouteSnapshot, CanActivate, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

import { ModuleStatusService } from '../services/module-status.service';

/** 模块友好名称映射 */
const MODULE_LABELS: Record<string, string> = {
  auth: '认证系统',
  course: '课程管理',
  ai_service: 'AI 服务',
  ai_recommend: 'AI 推荐',
  ai_capabilities: 'AI 能力',
  ai_teacher: 'AI 教师',
  ai_edu_progress: 'AI 学习进度',
  payment: '支付系统',
  exam: '在线考试',
  achievement: '成就系统',
  ar_vr: 'AR/VR 课程',
  ar_vr_mock: 'AR/VR 模拟',
  ar_lab: 'AR 实验室',
  blockchain_gateway: '区块链网关',
  digital_twin: '数字孪生',
  creativity: '创意引擎',
  openhydra: 'AI 实验室',
  hardware: '硬件认证',
  multimedia: '多媒体资源',
  collaborative_editor: '协作编辑',
  learning_behavior: '学习行为分析',
  finance: '财务管理',
  sponsorship: '企业赞助',
  vector_knowledge: '向量知识库',
  model_benchmark: '模型基准测试',
  model_update: '模型热更新',
  sensor_data: '传感器数据',
};

@Injectable({ providedIn: 'root' })
export class ModuleActiveGuard implements CanActivate {
  constructor(
    private moduleStatus: ModuleStatusService,
    private snackBar: MatSnackBar
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    _state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> {
    const moduleName = route.data['requiredModule'] as string | undefined;

    if (!moduleName) {
      // 未配置 requiredModule，直接放行
      return of(true);
    }

    // 修复：竞态条件处理
    // 当模块列表为空时，先触发健康检查然后等待结果
    const modules = this.moduleStatus.modules$.value;
    if (!modules || modules.length === 0) {
      // 模块状态未初始化，先获取状态
      this.moduleStatus.fetchHealth();
      // 返回 true 放行，让组件自己处理降级
      // 这样可以避免路由被阻止
      return of(true);
    }

    // 已激活
    if (this.moduleStatus.isModuleAvailable(moduleName)) {
      const entry = this.moduleStatus.getModule(moduleName);
      if (entry?.state === 'degraded') {
        this.showDegradedBanner(moduleName, entry.error_message);
      }
      return of(true);
    }

    // 检查模块状态
    const entry = this.moduleStatus.getModule(moduleName);
    if (entry?.state === 'disabled') {
      this.showDisabledMessage(moduleName);
      return of(false);
    }

    if (entry?.state === 'failed') {
      // 【P1-BUG03 修复】后端 health-detail 返回 'failed' 时不应拦截用户访问。
      // 改为记录提示信息并放行,让组件内部处理降级逻辑,避免整个路由不可达。
      this.showFailedMessage(moduleName, entry.error_message);
      return of(true);
    }

    // 触发激活
    const label = MODULE_LABELS[moduleName] || moduleName;
    this.showLoadingMessage(label);

    return this.moduleStatus.ensureModuleActive(moduleName).pipe(
      tap((success) => {
        this.snackBar.dismiss();
        if (success) {
          const updatedEntry = this.moduleStatus.getModule(moduleName);
          if (updatedEntry?.state === 'degraded') {
            this.showDegradedBanner(moduleName, updatedEntry.error_message);
          }
        }
      }),
      catchError(() => {
        this.snackBar.dismiss();
        // 【P1-BUG03 修复】激活失败时改为放行 + 提示降级运行,而不是返回 false
        // 拦截用户访问。后端不可达不应该完全阻塞路由。
        this.showFailedMessage(moduleName, '后端不可达，以降级模式访问');
        return of(true);
      })
    );
  }

  private showLoadingMessage(label: string): void {
    this.snackBar.open(`正在启动 ${label} 功能...`, '', {
      duration: 0,
      panelClass: ['module-loading-snackbar'],
      horizontalPosition: 'center',
      verticalPosition: 'top',
    });
  }

  private showDegradedBanner(moduleName: string, reason: string | null): void {
    const label = MODULE_LABELS[moduleName] || moduleName;
    const msg = reason ? `${label} 降级运行中: ${reason}` : `${label} 降级运行中，部分功能受限`;
    this.snackBar.open(msg, '关闭', {
      duration: 8000,
      panelClass: ['module-degraded-snackbar'],
      horizontalPosition: 'center',
      verticalPosition: 'top',
    });
  }

  private showDisabledMessage(moduleName: string): void {
    const label = MODULE_LABELS[moduleName] || moduleName;
    this.snackBar.open(`${label} 功能已被管理员禁用`, '关闭', {
      duration: 5000,
      panelClass: ['module-unavailable-snackbar'],
      horizontalPosition: 'center',
      verticalPosition: 'top',
    });
  }

  private showFailedMessage(moduleName: string, error: string | null): void {
    const label = MODULE_LABELS[moduleName] || moduleName;
    const detail = error ? `: ${error}` : '';
    this.snackBar
      .open(`${label} 功能暂时不可用${detail}`, '重试', {
        duration: 8000,
        panelClass: ['module-unavailable-snackbar'],
        horizontalPosition: 'center',
        verticalPosition: 'top',
      })
      .onAction()
      .subscribe(() => {
        // 重试
        this.moduleStatus.ensureModuleActive(moduleName).subscribe();
      });
  }
}
