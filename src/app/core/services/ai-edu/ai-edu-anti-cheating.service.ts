/**
 * AI-Edu 防作弊服务
 * 提供多种防作弊功能：切屏检测、时间监控、随机化、全屏强制
 * 
 * 桌面端增强：
 * - Electron 窗口失焦检测（main.js → IPC → preload.js）
 * - 全屏模式强制答题
 * - 本地事件监听（visibilitychange + blur/focus）
 */
import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

export interface AntiCheatingConfig {
  enableScreenChangeDetection: boolean;
  enableTimeMonitoring: boolean;
  enableOptionRandomization: boolean;
  enableQuestionRandomization: boolean;
  maxScreenChanges: number;
  minTimePerQuestion: number;
  /** 桌面端：是否启用 Electron 窗口失焦检测 */
  enableElectronBlurDetection?: boolean;
  /** 是否强制全屏模式 */
  forceFullscreen?: boolean;
}

export interface ScreenChangeEvent {
  timestamp: number;
  visible: boolean;
  count: number;
  /** 来源：browser | electron */
  source?: 'browser' | 'electron';
}

export interface TimeViolationEvent {
  questionId: number;
  timeSpent: number;
  minRequired: number;
  violation: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class AIEduAntiCheatingService {
  private config: AntiCheatingConfig = {
    enableScreenChangeDetection: true,
    enableTimeMonitoring: true,
    enableOptionRandomization: true,
    enableQuestionRandomization: true,
    maxScreenChanges: 5,
    minTimePerQuestion: 3,
    enableElectronBlurDetection: true,
    forceFullscreen: false,
  };

  private screenChangeCount = 0;
  private screenChangeEvents$ = new Subject<ScreenChangeEvent>();
  private timeViolationEvents$ = new Subject<TimeViolationEvent>();
  private visibilityWarnings$ = new BehaviorSubject<number>(0);
  /** 全屏状态 */
  private fullscreenSubject = new BehaviorSubject<boolean>(false);
  public fullscreen$ = this.fullscreenSubject.asObservable();

  private questionStartTime: Map<number, number> = new Map();
  private suspiciousActivityCount = 0;
  private isBrowser: boolean;

  constructor(@Inject(PLATFORM_ID) private platformId: object) {
    this.isBrowser = isPlatformBrowser(platformId);
    if (this.isBrowser) {
      this.initScreenDetection();
    }
  }

  /**
   * 初始化切屏检测（Web + Electron 双通道）
   */
  private initScreenDetection(): void {
    if (!this.config.enableScreenChangeDetection) return;

    // Web 端：页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.handleScreenChange(false, 'browser');
      } else {
        this.handleScreenChange(true, 'browser');
      }
    });

    // Web 端：窗口失焦/聚焦
    window.addEventListener('blur', () => {
      this.handleScreenChange(false, 'browser');
    });

    window.addEventListener('focus', () => {
      this.handleScreenChange(true, 'browser');
    });

    // Electron 端：通过 window.electronAPI 监听 IPC 事件
    this.initElectronDetection();
  }

  /**
   * Electron 窗口失焦检测
   */
  private initElectronDetection(): void {
    if (!this.config.enableElectronBlurDetection) return;

    try {
      const electronAPI = (window as unknown as { electronAPI?: {
        on: (event: string, callback: (...args: unknown[]) => void) => void;
        removeAllListeners?: (event: string) => void;
      } }).electronAPI;

      if (electronAPI?.on) {
        // 监听 Electron 主进程的窗口失焦事件
        electronAPI.on('window-blur', () => {
          this.handleScreenChange(false, 'electron');
        });

        electronAPI.on('window-focus', () => {
          this.handleScreenChange(true, 'electron');
        });
      }
    } catch {
      // Electron API 不可用，仅使用 Web 检测
    }
  }

  /**
   * 处理切屏事件
   */
  private handleScreenChange(visible: boolean, source: 'browser' | 'electron' = 'browser'): void {
    if (!visible) {
      this.screenChangeCount++;
      this.suspiciousActivityCount++;

      const event: ScreenChangeEvent = {
        timestamp: Date.now(),
        visible: false,
        count: this.screenChangeCount,
        source,
      };

      this.screenChangeEvents$.next(event);
      this.visibilityWarnings$.next(this.screenChangeCount);

      if (this.screenChangeCount >= this.config.maxScreenChanges) {
        this.triggerWarning('切屏次数过多，可能被警告！');
      }
    }
  }

  /**
   * 强制全屏模式
   */
  requestFullscreen(): void {
    if (!this.config.forceFullscreen) return;

    try {
      const elem = document.documentElement;
      if (elem.requestFullscreen) {
        void elem.requestFullscreen();
      } else if ((elem as unknown as { webkitRequestFullscreen?: () => void }).webkitRequestFullscreen) {
        void (elem as unknown as { webkitRequestFullscreen: () => Promise<void> }).webkitRequestFullscreen();
      }

      this.fullscreenSubject.next(true);

      // 监听全屏退出
      const exitHandler = (): void => {
        if (!document.fullscreenElement) {
          this.fullscreenSubject.next(false);
          document.removeEventListener('fullscreenchange', exitHandler);
        }
      };
      document.addEventListener('fullscreenchange', exitHandler);
    } catch {
      console.warn('[AntiCheat] 无法进入全屏模式');
    }
  }

  /** 退出全屏 */
  exitFullscreen(): void {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      this.fullscreenSubject.next(false);
    }
  }

  /**
   * 开始监控某题的答题时间
   */
  startMonitoringQuestion(questionId: number): void {
    if (!this.config.enableTimeMonitoring) {
      return;
    }

    this.questionStartTime.set(questionId, Date.now());
  }

  /**
   * 停止监控并检查时间违规
   */
  stopMonitoringQuestion(questionId: number): TimeViolationEvent | null {
    if (!this.config.enableTimeMonitoring) {
      return null;
    }

    const startTime = this.questionStartTime.get(questionId);
    if (!startTime) {
      return null;
    }

    const timeSpent = Date.now() - startTime;
    const minRequired = this.config.minTimePerQuestion * 1000;
    const violation = timeSpent < minRequired;

    const event: TimeViolationEvent = {
      questionId,
      timeSpent: Math.floor(timeSpent / 1000),
      minRequired: this.config.minTimePerQuestion,
      violation,
    };

    if (violation) {
      this.suspiciousActivityCount++;
      this.timeViolationEvents$.next(event);
    }

    this.questionStartTime.delete(questionId);
    return event;
  }

  /**
   * 随机打乱数组（Fisher-Yates 算法）
   */
  shuffleArray<T>(array: T[]): T[] {
    if (!this.config.enableOptionRandomization && !this.config.enableQuestionRandomization) {
      return array;
    }

    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  }

  /**
   * 随机打乱选择题选项
   */
  shuffleOptions(options: string[]): { shuffled: string[]; originalIndex: number[] } {
    if (!this.config.enableOptionRandomization) {
      return { shuffled: options, originalIndex: options.map((_, i) => i) };
    }

    const indexed = options.map((opt, index) => ({ opt, index }));

    // Fisher-Yates 洗牌
    for (let i = indexed.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indexed[i], indexed[j]] = [indexed[j], indexed[i]];
    }

    return {
      shuffled: indexed.map((item) => item.opt),
      originalIndex: indexed.map((item) => item.index),
    };
  }

  /**
   * 获取切屏事件流
   */
  getScreenChangeEvents(): Observable<ScreenChangeEvent> {
    return this.screenChangeEvents$.asObservable();
  }

  /**
   * 获取时间违规事件流
   */
  getTimeViolations(): Observable<TimeViolationEvent> {
    return this.timeViolationEvents$.asObservable();
  }

  /**
   * 获取切屏警告计数
   */
  getVisibilityWarnings(): Observable<number> {
    return this.visibilityWarnings$.asObservable();
  }

  /**
   * 获取当前切屏次数
   */
  getScreenChangeCount(): number {
    return this.screenChangeCount;
  }

  /**
   * 重置计数器
   */
  reset(): void {
    this.screenChangeCount = 0;
    this.suspiciousActivityCount = 0;
    this.questionStartTime.clear();
    this.visibilityWarnings$.next(0);
  }

  /**
   * 获取可疑活动总数
   */
  getSuspiciousActivityCount(): number {
    return this.suspiciousActivityCount;
  }

  /**
   * 生成防作弊报告
   */
  generateReport(): {
    totalScreenChanges: number;
    suspiciousActivities: number;
    isSuspicious: boolean;
    details: string[];
  } {
    const details: string[] = [];

    if (this.screenChangeCount > 0) {
      details.push(`切屏次数：${this.screenChangeCount}`);
    }

    if (this.suspiciousActivityCount > 0) {
      details.push(`可疑活动：${this.suspiciousActivityCount}`);
    }

    const isSuspicious =
      this.screenChangeCount >= this.config.maxScreenChanges || this.suspiciousActivityCount >= 10;

    return {
      totalScreenChanges: this.screenChangeCount,
      suspiciousActivities: this.suspiciousActivityCount,
      isSuspicious,
      details,
    };
  }

  /**
   * 触发警告
   */
  private triggerWarning(message: string): void {
    // 可以通过 Toast 或其他方式通知用户
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<AntiCheatingConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * 获取当前配置
   */
  getConfig(): AntiCheatingConfig {
    return { ...this.config };
  }
}
