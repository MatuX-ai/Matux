/**
 * 自定义路由预加载策略
 *
 * @description 智能预加载策略，根据路由优先级和用户行为预加载模块
 */

import { Injectable } from '@angular/core';
import { PreloadingStrategy, Route } from '@angular/router';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

/** Navigator Network Information API */
interface NetworkConnection {
  effectiveType: string;
  type: string;
  downlink: number;
  rtt: number;
  downlinkMax: number;
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void;
}

export interface PreloadConfig {
  path: string;
  priority: number; // 优先级，数字越大优先级越高
  preloadWhen: 'always' | 'hover' | 'network-idle';
}

@Injectable({
  providedIn: 'root',
})
export class CustomPreloadingStrategy implements PreloadingStrategy {
  // 预加载配置
  private preloadConfigs: PreloadConfig[] = [
    { path: 'marketing', priority: 10, preloadWhen: 'always' }, // 营销页最高优先级
    { path: 'pricing', priority: 8, preloadWhen: 'always' },
    { path: 'features', priority: 8, preloadWhen: 'always' },
    { path: 'about', priority: 6, preloadWhen: 'always' },
    { path: 'contact', priority: 6, preloadWhen: 'always' },
    { path: 'dashboard', priority: 5, preloadWhen: 'hover' },
    { path: 'ai-edu', priority: 4, preloadWhen: 'network-idle' },
    { path: 'ar-lab', priority: 3, preloadWhen: 'network-idle' },
    { path: 'admin', priority: 2, preloadWhen: 'hover' }, // 管理后台仅hover时预加载
  ];

  // 已预加载的路由
  private preloadedRoutes = new Set<string>();

  // 当前网络状态
  private isNetworkIdle = false;

  constructor() {
    // 监听网络状态
    this.initNetworkIdleDetector();
  }

  /**
   * PreloadingStrategy 实现
   */
  preload(route: Route, load: () => Observable<unknown>): Observable<unknown> {
    const routePath = this.getRoutePath(route);

    // 检查是否应该预加载
    if (this.shouldPreload(routePath)) {
      this.preloadedRoutes.add(routePath);

      // 根据预加载时机返回
      return this.getPreloadObservable(routePath, load);
    }

    // 不预加载
    return of(null);
  }

  /**
   * 获取路由路径
   */
  private getRoutePath(route: Route): string {
    const path = route.path ?? '';
    return path.replace(/^\/+|\/+$/g, '');
  }

  /**
   * 检查是否应该预加载
   */
  private shouldPreload(routePath: string): boolean {
    const config = this.preloadConfigs.find((c) => routePath.includes(c.path));

    if (!config) {
      return false; // 没有配置，不预加载
    }

    // 已经预加载过
    if (this.preloadedRoutes.has(routePath)) {
      return false;
    }

    // 根据预加载时机判断
    switch (config.preloadWhen) {
      case 'always':
        return true; // 总是预加载
      case 'hover':
        return false; // 需要用户交互，这里返回false，实际在hover时触发
      case 'network-idle':
        return this.isNetworkIdle; // 网络空闲时预加载
      default:
        return false;
    }
  }

  /**
   * 获取预加载Observable
   */
  private getPreloadObservable(
    routePath: string,
    load: () => Observable<unknown>
  ): Observable<unknown> {
    const config = this.preloadConfigs.find((c) => routePath.includes(c.path));

    switch (config?.preloadWhen) {
      case 'always':
        return load();
      case 'network-idle':
        // 延迟100ms预加载，避免阻塞
        return load().pipe(delay(100));
      default:
        return of(null);
    }
  }

  /**
   * 手动触发路由预加载（用于hover等交互）
   */
  preloadRoute(routePath: string): void {
    if (this.preloadedRoutes.has(routePath)) {
      return; // 已经预加载过
    }

    const config = this.preloadConfigs.find((c) => routePath.includes(c.path));
    if (config?.preloadWhen === 'hover') {
      this.preloadedRoutes.add(routePath);
      console.warn(`[CustomPreloadingStrategy] 预加载路由: ${routePath}`);
      // 这里需要触发路由加载，实际实现中可以使用Router的loadChildren
    }
  }

  /**
   * 初始化网络空闲检测器
   */
  private initNetworkIdleDetector(): void {
    // 监听网络连接类型变化
    if ('connection' in navigator) {
      const connection = (navigator as unknown as { connection?: NetworkConnection }).connection;
      connection?.addEventListener('change', () => {
        this.checkNetworkIdle();
      });
    }

    // 定期检查网络空闲状态
    setInterval(() => {
      this.checkNetworkIdle();
    }, 5000);
  }

  /**
   * 检查网络是否空闲
   */
  private checkNetworkIdle(): void {
    // 这里可以实现更复杂的网络空闲检测逻辑
    // 简化版：假设网络总是空闲
    this.isNetworkIdle = true;
  }

  /**
   * 获取预加载状态（用于调试）
   */
  getPreloadedRoutes(): string[] {
    return Array.from(this.preloadedRoutes);
  }

  /**
   * 清除预加载缓存
   */
  clearPreloadedCache(): void {
    this.preloadedRoutes.clear();
    console.warn('[CustomPreloadingStrategy] 清除预加载缓存');
  }

  /**
   * 根据设备类型调整预加载策略
   */
  adjustStrategyForDevice(): void {
    const isMobile = window.innerWidth < 768;
    const isSlowConnection = this.isSlowConnection();

    // 移动端或慢速网络时，减少预加载
    if (isMobile || isSlowConnection) {
      this.preloadConfigs = this.preloadConfigs.filter(
        (config) => config.priority >= 5 // 只预加载高优先级路由
      );
      console.warn('[CustomPreloadingStrategy] 移动端模式：减少预加载');
    }
  }

  /**
   * 检测是否为慢速网络
   */
  private isSlowConnection(): boolean {
    if ('connection' in navigator) {
      const connection = (navigator as unknown as { connection?: NetworkConnection }).connection;
      const effectiveType = connection?.effectiveType ?? '';
      // slow-2g, 2g, 3g 被认为是慢速网络
      return ['slow-2g', '2g', '3g'].includes(effectiveType);
    }
    return false;
  }
}
