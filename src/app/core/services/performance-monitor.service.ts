/**
 * 性能监控服务
 *
 * @description 监控 Core Web Vitals 和应用性能指标
 */

import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

// Core Web Vitals 指标
/**
 * Navigation Timing 类型
 */
interface NavigationTimingLike {
  loadEventEnd: number;
  navigationStart: number;
  responseStart: number;
  requestStart: number;
}

/**
 * LCP Entry 类型
 */
interface LargestContentfulPaintLike {
  renderTime: number;
  startTime: number;
}

/**
 * FID Entry 类型
 */
interface FirstInputLike {
  processingStart: number;
  startTime: number;
}

/**
 * CLS Entry 类型
 */
interface LayoutShiftLike {
  hadRecentInput: boolean;
  value: number;
}

// Core Web Vitals 指标
export interface CoreWebVitals {
  // FCP - First Contentful Paint (首次内容绘制)
  fcp?: number;

  // LCP - Largest Contentful Paint (最大内容绘制)
  lcp?: number;

  // FID - First Input Delay (首次输入延迟)
  fid?: number;

  // CLS - Cumulative Layout Shift (累积布局偏移)
  cls?: number;

  // TTFB - Time to First Byte (首字节时间)
  ttfb?: number;
}

// 自定义性能指标
export interface PerformanceMetrics {
  // 页面加载时间
  pageLoadTime?: number;

  // 路由切换时间
  routeChangeTime?: number;

  // 组件渲染时间
  componentRenderTime?: Record<string, number>;

  // API 响应时间
  apiResponseTime?: Record<string, number>;

  // 内存使用
  memoryUsage?: number;

  // 时间戳
  timestamp: number;
}

// 性能评分
export interface PerformanceScore {
  overall: number; // 总体评分 (0-100)
  loading: number; // 加载性能
  interactivity: number; // 交互性
  stability: number; // 稳定性
}

@Injectable({
  providedIn: 'root',
})
export class PerformanceMonitorService {
  private metrics: PerformanceMetrics[] = [];
  private webVitals: CoreWebVitals = {};
  private routeStartTime: number = 0;

  // 性能评分阈值
  private readonly thresholds = {
    fcp: { good: 1800, needsImprovement: 3000 },
    lcp: { good: 2500, needsImprovement: 4000 },
    fid: { good: 100, needsImprovement: 300 },
    cls: { good: 0.1, needsImprovement: 0.25 },
  };

  constructor(private router: Router) {
    this.init();
  }

  /**
   * 初始化性能监控
   */
  private init(): void {
    // 监听路由变化
    this.router.events.subscribe((event) => {
      if (event && event.constructor.name === 'NavigationStart') {
        this.routeStartTime = performance.now();
      }

      if (event && event.constructor.name === 'NavigationEnd') {
        this.recordRouteChangeTime();
      }
    });

    // 监听页面加载
    if ('PerformanceObserver' in window) {
      this.initPerformanceObserver();
    }

    // 监听 Core Web Vitals
    this.initWebVitals();

    console.warn('[PerformanceMonitorService] 已初始化');
  }

  /**
   * 初始化 PerformanceObserver
   */
  private initPerformanceObserver(): void {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        switch (entry.entryType) {
          case 'navigation': {
            const navEntry = entry as unknown as NavigationTimingLike;
            this.recordNavigationTiming(navEntry);
            break;
          }
          case 'paint': {
            const paintEntry = entry as PerformancePaintTiming;
            this.recordPaintTiming(paintEntry);
            break;
          }
          case 'largest-contentful-paint': {
            const lcpEntry = entry as unknown as LargestContentfulPaintLike;
            this.webVitals.lcp = lcpEntry.renderTime || lcpEntry.startTime;
            break;
          }
          case 'first-input': {
            const fidEntry = entry as unknown as FirstInputLike;
            this.webVitals.fid = fidEntry.processingStart - fidEntry.startTime;
            break;
          }
          case 'layout-shift': {
            const clsEntry = entry as unknown as LayoutShiftLike;
            if (!clsEntry.hadRecentInput) {
              this.webVitals.cls = (this.webVitals.cls ?? 0) + clsEntry.value;
            }
            break;
          }
        }
      }
    });

    observer.observe({
      entryTypes: [
        'navigation',
        'paint',
        'largest-contentful-paint',
        'first-input',
        'layout-shift',
      ],
    });
  }

  /**
   * 初始化 Core Web Vitals
   */
  private initWebVitals(): void {
    // 动态加载 web-vitals 库（如果可用）
    // 这里提供基本实现，实际项目中建议使用 web-vitals 库
    setTimeout(() => {
      this.calculatePerformanceScore();
    }, 2000);
  }

  /**
   * 记录导航时间
   */
  private recordNavigationTiming(timing: NavigationTimingLike): void {
    this.metrics.push({
      pageLoadTime: timing.loadEventEnd - timing.navigationStart,
      timestamp: Date.now(),
    });

    this.webVitals.ttfb = timing.responseStart - timing.requestStart;
  }

  /**
   * 记录绘制时间
   */
  private recordPaintTiming(timing: PerformancePaintTiming): void {
    if (timing.name === 'first-paint') {
      // FP (First Paint)
    } else if (timing.name === 'first-contentful-paint') {
      this.webVitals.fcp = timing.startTime;
    }
  }

  /**
   * 记录路由切换时间
   */
  private recordRouteChangeTime(): void {
    const routeChangeTime = performance.now() - this.routeStartTime;
    this.metrics.push({
      routeChangeTime,
      timestamp: Date.now(),
    });
  }

  /**
   * 记录组件渲染时间
   */
  recordComponentRender(componentName: string, renderTime: number): void {
    const lastMetric = this.metrics[this.metrics.length - 1];
    if (!lastMetric) {
      this.metrics.push({
        componentRenderTime: { [componentName]: renderTime },
        timestamp: Date.now(),
      });
    } else {
      lastMetric.componentRenderTime = {
        ...lastMetric.componentRenderTime,
        [componentName]: renderTime,
      };
    }
  }

  /**
   * 记录 API 响应时间
   */
  recordApiResponse(apiEndpoint: string, responseTime: number): void {
    const lastMetric = this.metrics[this.metrics.length - 1];
    if (!lastMetric) {
      this.metrics.push({
        apiResponseTime: { [apiEndpoint]: responseTime },
        timestamp: Date.now(),
      });
    } else {
      lastMetric.apiResponseTime = {
        ...lastMetric.apiResponseTime,
        [apiEndpoint]: responseTime,
      };
    }
  }

  /**
   * 计算性能评分
   */
  private calculatePerformanceScore(): void {
    const scores = this.calculateScores();
    console.warn('[PerformanceMonitorService] 性能评分:', scores);
  }

  /**
   * 计算各项得分
   */
  private calculateScores(): PerformanceScore {
    // 加载性能评分 (基于 FCP 和 LCP)
    const fcpScore = this.calculateMetricScore(
      this.webVitals.fcp ?? 0,
      this.thresholds.fcp.good,
      this.thresholds.fcp.needsImprovement
    );
    const lcpScore = this.calculateMetricScore(
      this.webVitals.lcp ?? 0,
      this.thresholds.lcp.good,
      this.thresholds.lcp.needsImprovement
    );
    const loading = (fcpScore + lcpScore) / 2;

    // 交互性评分 (基于 FID)
    const interactivity = this.calculateMetricScore(
      this.webVitals.fid ?? 0,
      this.thresholds.fid.good,
      this.thresholds.fid.needsImprovement,
      true // FID 越小越好
    );

    // 稳定性评分 (基于 CLS)
    const stability = this.calculateMetricScore(
      this.webVitals.cls ?? 0,
      this.thresholds.cls.good,
      this.thresholds.cls.needsImprovement,
      true // CLS 越小越好
    );

    // 总体评分
    const overall = loading * 0.4 + interactivity * 0.3 + stability * 0.3;

    return { overall, loading, interactivity, stability };
  }

  /**
   * 计算单个指标得分
   */
  private calculateMetricScore(
    value: number,
    good: number,
    needsImprovement: number,
    lowerIsBetter = false
  ): number {
    if (lowerIsBetter) {
      if (value <= good) return 100;
      if (value >= needsImprovement) return 50;
      return 100 - ((value - good) / (needsImprovement - good)) * 50;
    } else {
      if (value >= needsImprovement) return 50;
      if (value <= good) return 100;
      return 50 + ((value - good) / (needsImprovement - good)) * 50;
    }
  }

  /**
   * 获取当前 Web Vitals
   */
  getWebVitals(): CoreWebVitals {
    return { ...this.webVitals };
  }

  /**
   * 获取性能指标历史
   */
  getMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  /**
   * 清空指标
   */
  clearMetrics(): void {
    this.metrics = [];
    this.webVitals = {};
    console.warn('[PerformanceMonitorService] 已清空性能指标');
  }

  /**
   * 导出性能报告
   */
  exportReport(): {
    webVitals: CoreWebVitals;
    metrics: PerformanceMetrics[];
    scores: PerformanceScore;
  } {
    return {
      webVitals: this.webVitals,
      metrics: this.metrics,
      scores: this.calculateScores(),
    };
  }

  /**
   * 检查性能是否达标
   */
  isPerformanceGood(): boolean {
    const scores = this.calculateScores();
    return scores.overall >= 75; // 总体评分 >= 75 认为良好
  }
}
