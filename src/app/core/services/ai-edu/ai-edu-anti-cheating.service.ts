/**
 * AI-Edu 闃蹭綔寮婃湇鍔? * 鎻愪緵澶氱闃蹭綔寮婂姛鑳斤細鍒囧睆妫€娴嬨€佹椂闂寸洃鎺с€侀殢鏈哄寲銆佸叏灞忓己鍒? *
 * 妗岄潰绔寮猴細
 * - Electron 绐楀彛澶辩劍妫€娴嬶紙main.js 鈫?IPC 鈫?preload.js锛? * - 鍏ㄥ睆妯″紡寮哄埗绛旈
 * - 鏈湴浜嬩欢鐩戝惉锛坴isibilitychange + blur/focus锛? */
import { isPlatformBrowser } from '@angular/common';
import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

export interface AntiCheatingConfig {
  enableScreenChangeDetection: boolean;
  enableTimeMonitoring: boolean;
  enableOptionRandomization: boolean;
  enableQuestionRandomization: boolean;
  maxScreenChanges: number;
  minTimePerQuestion: number;
  /** 妗岄潰绔細鏄惁鍚敤 Electron 绐楀彛澶辩劍妫€娴?*/
  enableElectronBlurDetection?: boolean;
  /** 鏄惁寮哄埗鍏ㄥ睆妯″紡 */
  forceFullscreen?: boolean;
}

export interface ScreenChangeEvent {
  timestamp: number;
  visible: boolean;
  count: number;
  /** 鏉ユ簮锛歜rowser | electron */
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
  /** 鍏ㄥ睆鐘舵€?*/
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
   * 鍒濆鍖栧 RuntimeException 鍙岄€氶亾锛?   */
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
   * Electron 经典剑舞妫€娴?   */
  private initElectronDetection(): void {
    if (!this.config.enableElectronBlurDetection) return;

    try {
      const electronAPI = (
        window as unknown as {
          electronAPI?: {
            on: (event: string, callback: (...args: unknown[]) => void) => void;
            removeAllListeners?: (event: string) => void;
          };
        }
      ).electronAPI;

      if (electronAPI?.on) {
        // 鐩戝惉 Electron 涓昏繘绋嬬殑绐楀彛澶辩劍浜嬩欢
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
   * 处理切换事件
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
        this.triggerWarning('切换次数过多，可能被警告');
      }
    }
  }

  /**
   * 寮哄埗鍏ㄥ睆妯″紡
   */
  requestFullscreen(): void {
    if (!this.config.forceFullscreen) return;

    try {
      const elem = document.documentElement;
      if (elem.requestFullscreen) {
        void elem.requestFullscreen();
      } else if (
        (elem as unknown as { webkitRequestFullscreen?: () => void }).webkitRequestFullscreen
      ) {
        void (
          elem as unknown as { webkitRequestFullscreen: () => Promise<void> }
        ).webkitRequestFullscreen();
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

  /** 閫€鍑哄叏灞?*/
  exitFullscreen(): void {
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      this.fullscreenSubject.next(false);
    }
  }

  /**
   * 寮€濮嬬洃鎺ф煇棰樼殑绛旈鏃堕棿
   */
  startMonitoringQuestion(questionId: number): void {
    if (!this.config.enableTimeMonitoring) {
      return;
    }

    this.questionStartTime.set(questionId, Date.now());
  }

  /**
   * 鍋滄鐩戞帶骞舵鏌ユ椂闂磋繚瑙?   */
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
   * 闅忔満鎵撲贡鏁扮粍锛團isher-Yates 绠楁硶锛?   */
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
   * 闅忔満鎵撲贡閫夋嫨棰橀€夐」
   */
  shuffleOptions(options: string[]): { shuffled: string[]; originalIndex: number[] } {
    if (!this.config.enableOptionRandomization) {
      return { shuffled: options, originalIndex: options.map((_, i) => i) };
    }

    const indexed = options.map((opt, index) => ({ opt, index }));

    // Fisher-Yates 娲楃墝
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
   * 鑾峰彇鍒囧睆浜嬩欢娴?   */
  getScreenChangeEvents(): Observable<ScreenChangeEvent> {
    return this.screenChangeEvents$.asObservable();
  }

  /**
   * 鑾峰彇鏃堕棿杩濊浜嬩欢娴?   */
  getTimeViolations(): Observable<TimeViolationEvent> {
    return this.timeViolationEvents$.asObservable();
  }

  /**
   * 鑾峰彇鍒囧睆璀﹀憡璁℃暟
   */
  getVisibilityWarnings(): Observable<number> {
    return this.visibilityWarnings$.asObservable();
  }

  /**
   * 鑾峰彇褰撳墠鍒囧睆娆℃暟
   */
  getScreenChangeCount(): number {
    return this.screenChangeCount;
  }

  /**
   * 閲嶇疆璁℃暟鍣?   */
  reset(): void {
    this.screenChangeCount = 0;
    this.suspiciousActivityCount = 0;
    this.questionStartTime.clear();
    this.visibilityWarnings$.next(0);
  }

  /**
   * 鑾峰彇鍙枒娲诲姩鎬绘暟
   */
  getSuspiciousActivityCount(): number {
    return this.suspiciousActivityCount;
  }

  /**
   * 鐢熸垚闃蹭綔寮婃姤鍛?   */
  generateReport(): {
    totalScreenChanges: number;
    suspiciousActivities: number;
    isSuspicious: boolean;
    details: string[];
  } {
    const details: string[] = [];

    if (this.screenChangeCount > 0) {
      details.push(`鍒囧睆娆℃暟锛?{this.screenChangeCount}`);
    }

    if (this.suspiciousActivityCount > 0) {
      details.push(`鍙枒娲诲姩锛?{this.suspiciousActivityCount}`);
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
   * 瑙﹀彂璀﹀憡
   */
  private triggerWarning(_message: string): void {
    // 鍙互閫氳繃 Toast 鎴栧叾浠栨柟寮忛€氱煡鐢ㄦ埛
  }

  /**
   * 鏇存柊閰嶇疆
   */
  updateConfig(config: Partial<AntiCheatingConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * 鑾峰彇褰撳墠閰嶇疆
   */
  getConfig(): AntiCheatingConfig {
    return { ...this.config };
  }
}
