import { Injectable, OnDestroy } from '@angular/core';

import { ExamService } from './exam.service';

/**
 * 前端防作弊服务
 *
 * 实现客户端防作弊检测：
 * - 屏幕/标签页切换检测
 * - 复制粘贴禁用
 * - 全屏模式检测
 * - 定时心跳上报
 */
@Injectable({
  providedIn: 'root',
})
export class AntiCheatService implements OnDestroy {
  private screenSwitchCount = 0;
  private attemptId: number | null = null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private fullscreenMode = false;
  private pasteBlocked = false;

  // 事件处理器引用（用于取消监听）
  private onVisibilityChange = (): void => this.handleVisibilityChange();
  private onBlur = (): void => this.handleBlur();
  private onFocus = (): void => this.handleFocus();
  private onPaste = (e: ClipboardEvent): void => this.handlePaste(e);
  private onCopy = (e: ClipboardEvent): void => this.handleCopy(e);
  private onBeforeUnload = (e: BeforeUnloadEvent): void => this.handleBeforeUnload(e);

  constructor(private examService: ExamService) {}

  /**
   * 开始防作弊监控
   */
  startMonitoring(
    attemptId: number,
    options?: {
      restrictPaste?: boolean;
      restrictCopy?: boolean;
      fullscreenRequired?: boolean;
    }
  ): void {
    this.attemptId = attemptId;
    this.screenSwitchCount = 0;

    // 注册事件监听
    document.addEventListener('visibilitychange', this.onVisibilityChange);

    if (options?.fullscreenRequired) {
      this.requestFullscreen();
    }

    if (options?.restrictPaste !== false) {
      document.addEventListener('paste', this.onPaste as EventListener, true);
      this.pasteBlocked = true;
    }

    if (options?.restrictCopy !== false) {
      document.addEventListener('copy', this.onCopy as EventListener, true);
    }

    // 窗口 blur/focus 检测（备用）
    window.addEventListener('blur', this.onBlur);
    window.addEventListener('focus', this.onFocus);

    // 页面关闭提醒
    window.addEventListener('beforeunload', this.onBeforeUnload);

    // 启动心跳（每 30 秒）
    this.heartbeatInterval = setInterval(() => this.sendHeartbeat(), 30000);
  }

  /**
   * 停止防作弊监控
   */
  stopMonitoring(): void {
    document.removeEventListener('visibilitychange', this.onVisibilityChange);
    document.removeEventListener('paste', this.onPaste as EventListener, true);
    document.removeEventListener('copy', this.onCopy as EventListener, true);
    window.removeEventListener('blur', this.onBlur);
    window.removeEventListener('focus', this.onFocus);
    window.removeEventListener('beforeunload', this.onBeforeUnload);

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    this.exitFullscreen();
    this.attemptId = null;
  }

  private handleVisibilityChange(): void {
    if (document.hidden) {
      this.screenSwitchCount++;
      // 上报标签页切换事件
      this.reportEvent('tab_switch', { switch_count: this.screenSwitchCount });
    }
  }

  private handleBlur(): void {
    this.screenSwitchCount++;
    this.reportEvent('screen_switch', { switch_count: this.screenSwitchCount });
  }

  private handleFocus(): void {
    // 焦点回来时检查全屏状态
    this.checkFullscreen();
  }

  private handlePaste(e: ClipboardEvent): void {
    e.preventDefault();
    const content = e.clipboardData?.getData('text') ?? '';
    this.reportEvent('copy_paste', { action: 'paste', content_length: content.length });
  }

  private handleCopy(e: ClipboardEvent): void {
    e.preventDefault();
  }

  private handleBeforeUnload(e: BeforeUnloadEvent): void {
    // 上报页面关闭
    this.reportEvent('screen_switch', { action: 'page_close' });
    e.preventDefault();
    e.returnValue = '';
  }

  private requestFullscreen(): void {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
      elem
        .requestFullscreen()
        .then(() => {
          this.fullscreenMode = true;
        })
        .catch(() => {
          this.reportEvent('screen_switch', { action: 'fullscreen_failed' });
        });
    }
  }

  private exitFullscreen(): void {
    if (document.fullscreenElement && document.exitFullscreen) {
      document.exitFullscreen().catch(() => {});
    }
  }

  private checkFullscreen(): void {
    if (this.fullscreenMode && !document.fullscreenElement) {
      this.reportEvent('screen_switch', { action: 'exited_fullscreen' });
      this.requestFullscreen();
    }
  }

  private sendHeartbeat(): void {
    if (this.attemptId) {
      this.examService
        .reportCheatEvent(this.attemptId, 'heartbeat', {
          screen_switches: this.screenSwitchCount,
          timestamp: Date.now(),
        })
        .subscribe({
          error: (err) => console.warn('[AntiCheat] Heartbeat failed:', err),
        });
    }
  }

  private reportEvent(cheatType: string, details: Record<string, unknown>): void {
    if (this.attemptId) {
      this.examService.reportCheatEvent(this.attemptId, cheatType, details).subscribe({
        error: (err) => console.warn('[AntiCheat] Report failed:', err),
      });
    }
  }

  ngOnDestroy(): void {
    this.stopMonitoring();
  }
}
