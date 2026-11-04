/**
 * 启动模式服务（启动优化 P3）
 *
 * 提供"学习优先模式"状态查询能力，让前端组件能：
 * - 区分"主动跳过启动"与"用户主动启用学习优先模式"
 * - 在 fast mode 下显示"功能加载中"横幅，监听后端就绪后自动消失
 * - 在登录页、ARVR 课程、学生仪表盘等模块适配 fast mode 体验
 *
 * 设计原则：
 * 1. 单一数据源：仅通过 Electron IPC 询问主进程，避免与后端模块状态混用
 * 2. BehaviorSubject：保证新订阅者能立即拿到当前模式
 * 3. 幂等 refresh()：多次调用安全，结果会被 BehaviorSubject 去重
 */

import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { map } from 'rxjs/operators';

/** 启动模式 */
export interface StartupMode {
  /** 用户启用"学习优先模式"（主窗口立即显示，后端在后台启动） */
  fastMode: boolean;
  /** 后端启动失败 / 用户主动跳过 / 端口被占用等降级场景 */
  degraded: boolean;
}

/** 默认启动模式（非 Electron 环境下使用） */
const DEFAULT_MODE: StartupMode = {
  fastMode: false,
  degraded: false,
};

@Injectable({ providedIn: 'root' })
export class StartupModeService implements OnDestroy {
  private destroy$ = new Subject<void>();

  /** 当前启动模式（默认非 fast / 非 degraded） */
  private readonly modeSubject = new BehaviorSubject<StartupMode>(DEFAULT_MODE);

  /** 当前启动模式 Observable（推荐订阅此流） */
  readonly mode$: Observable<StartupMode> = this.modeSubject.asObservable();

  /** 仅 fast mode 状态 Observable（兼容老调用方） */
  readonly isFastMode$: Observable<boolean> = this.modeSubject.pipe(map((m) => m.fastMode));

  constructor() {
    // 构造时立即询问一次主进程（同步 fire-and-forget）
    void this.refresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 重新查询主进程当前启动模式
   * 安全可重入，结果与当前值相同时不触发订阅者（BehaviorSubject 内部去重）
   */
  async refresh(): Promise<StartupMode> {
    if (typeof window === 'undefined' || !window.electronAPI?.getStartupMode) {
      // 非 Electron 环境：保持默认值
      return DEFAULT_MODE;
    }
    try {
      const mode = await window.electronAPI.getStartupMode();
      const next: StartupMode = {
        fastMode: mode?.fastMode === true,
        degraded: mode?.degraded === true,
      };
      const prev = this.modeSubject.value;
      if (prev.fastMode !== next.fastMode || prev.degraded !== next.degraded) {
        this.modeSubject.next(next);
        console.log('[StartupMode] 启动模式更新:', next);
      }
      return next;
    } catch (err) {
      console.warn('[StartupMode] getStartupMode 失败，保持当前值:', err);
      return this.modeSubject.value;
    }
  }

  /**
   * 获取当前模式快照（同步）
   */
  snapshot(): StartupMode {
    return this.modeSubject.value;
  }

  /**
   * 是否处于学习优先模式
   */
  isFastMode(): boolean {
    return this.modeSubject.value.fastMode;
  }

  /**
   * 是否处于降级模式
   */
  isDegraded(): boolean {
    return this.modeSubject.value.degraded;
  }
}
