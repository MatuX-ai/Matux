/**
 * 飞升反馈服务（P0-1 + P0-4 共享基建）
 *
 * 职责：
 * - 数字飞升：把 +EXP 数字从源元素位置抛物线飞到目标元素位置
 * - 卡牌飞入：从源元素位置飞出后，由调用方决定目标
 * - 命中事件：飞升到达目标时 emit hit$，接收方（状态栏）订阅触发脉冲
 *
 * 实现：Web Animations API + 抛物线（quadratic bezier 采样 24 帧）。
 * a11y：自动尊重 prefers-reduced-motion，禁用动效时直接切换最终态。
 *
 * @see 桌面端游戏化P0升级.md §2.1 P0-1 / §2.4 P0-4
 */

import { Injectable, NgZone } from '@angular/core';
import { Observable, Subject } from 'rxjs';

export interface FlyHitEvent {
  target: HTMLElement;
  text: string;
}

export interface FlyCardOptions<T = unknown> {
  data?: T;
  durationMs?: number;
}

@Injectable({
  providedIn: 'root',
})
export class FeedbackFlyService {
  /** 飞升到达目标事件（供状态栏订阅触发脉冲） */
  private readonly hitSubject = new Subject<FlyHitEvent>();
  readonly hit$: Observable<FlyHitEvent> = this.hitSubject.asObservable();

  constructor(private readonly zone: NgZone) {}

  /**
   * 数字飞升
   * @param sourceEl 源元素（任务 checkbox / 任务卡）
   * @param targetEl 目标元素（状态栏 EXP 锚点）
   * @param text 显示文字（例: '+30'）
   * @param color hex 颜色（默认金色）
   */
  flyNumber(
    sourceEl: HTMLElement,
    targetEl: HTMLElement,
    text: string,
    color = '#fbbf24'
  ): Observable<void> {
    return new Observable<void>((subscriber) => {
      const prefersReducedMotion =
        typeof window !== 'undefined' &&
        window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (prefersReducedMotion || !sourceEl || !targetEl) {
        // 降级：直接命中，跳过动画
        this.hitSubject.next({ target: targetEl, text });
        subscriber.next();
        subscriber.complete();
        return;
      }

      const ghost = this.createGhostNumber(text, color);
      const sourceRect = sourceEl.getBoundingClientRect();
      const targetRect = targetEl.getBoundingClientRect();

      // 起点：源元素中心
      const startX = sourceRect.left + sourceRect.width / 2;
      const startY = sourceRect.top + sourceRect.height / 2;
      // 终点：目标元素中心
      const endX = targetRect.left + targetRect.width / 2;
      const endY = targetRect.top + targetRect.height / 2;
      // 控制点：抛物线顶点（水平中点偏上 80px）
      const midX = (startX + endX) / 2;
      const midY = Math.min(startY, endY) - 80;

      this.positionFixed(ghost, startX, startY);
      document.body.appendChild(ghost);

      const duration = 600;
      // 抛物线采样 24 帧
      const frames = this.sampleQuadraticBezier({ startX, startY, midX, midY, endX, endY }, 24);

      // 启动在 zone 外（避免频繁触发 CD），完成后回到 zone 内
      this.zone.runOutsideAngular(() => {
        const animations: Animation[] = [];
        const animX = ghost.animate(
          frames.map((p) => ({ transform: `translate(${p.x - startX}px, 0)` })),
          { duration, easing: 'cubic-bezier(0.4, 0, 0.2, 1)', fill: 'forwards' }
        );
        const animY = ghost.animate(
          frames.map((p) => ({ transform: `translate(0, ${p.y - startY}px)` })),
          { duration, easing: 'cubic-bezier(0.4, 0, 0.2, 1)', fill: 'forwards' }
        );
        const animOpacity = ghost.animate(
          [
            { opacity: 1, offset: 0 },
            { opacity: 1, offset: 0.7 },
            { opacity: 0, offset: 1 },
          ],
          { duration, fill: 'forwards' }
        );
        const animScale = ghost.animate(
          [
            { transform: 'scale(0.6)' },
            { transform: 'scale(1.15)', offset: 0.3 },
            { transform: 'scale(0.7)', offset: 0.85 },
            { transform: 'scale(0)' },
          ],
          { duration, fill: 'forwards' }
        );
        animations.push(animX, animY, animOpacity, animScale);

        const allDone = Promise.all(animations.map((a) => a.finished.catch(() => undefined)));
        allDone.then(() => {
          this.zone.run(() => {
            ghost.remove();
            this.hitSubject.next({ target: targetEl, text });
            subscriber.next();
            subscriber.complete();
          });
        });
      });
    });
  }

  /**
   * 卡牌飞入（简版）：从源元素放大缩小后由调用方 append 到目标容器
   * 不做抛物线（因为 target 容器是列表头部，不便精准定位单个卡）。
   * 返回一个 Observable，调用方 subscribe 后再执行 prepend。
   */
  flyCard(sourceEl: HTMLElement, options?: FlyCardOptions): Observable<void> {
    return new Observable<void>((subscriber) => {
      if (!sourceEl) {
        subscriber.next();
        subscriber.complete();
        return;
      }
      const prefersReducedMotion =
        typeof window !== 'undefined' &&
        window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReducedMotion) {
        subscriber.next();
        subscriber.complete();
        return;
      }
      const rect = sourceEl.getBoundingClientRect();
      const ghost = sourceEl.cloneNode(true) as HTMLElement;
      ghost.style.position = 'fixed';
      ghost.style.left = `${rect.left}px`;
      ghost.style.top = `${rect.top}px`;
      ghost.style.width = `${rect.width}px`;
      ghost.style.height = `${rect.height}px`;
      ghost.style.zIndex = '2000';
      ghost.style.pointerEvents = 'none';
      ghost.style.transformOrigin = 'center center';
      document.body.appendChild(ghost);

      this.zone.runOutsideAngular(() => {
        const duration = options?.durationMs ?? 500;
        const a = ghost.animate(
          [
            { transform: 'scale(1) rotate(0deg)', opacity: 1 },
            { transform: 'scale(1.1) rotate(4deg)', opacity: 1, offset: 0.3 },
            { transform: 'scale(0.6) rotate(-4deg)', opacity: 0 },
          ],
          { duration, easing: 'cubic-bezier(0.4, 0, 0.2, 1)', fill: 'forwards' }
        );
        a.finished
          .catch(() => undefined)
          .then(() => {
            this.zone.run(() => {
              ghost.remove();
              subscriber.next();
              subscriber.complete();
            });
          });
      });
    });
  }

  // ---- private helpers ----

  private createGhostNumber(text: string, color: string): HTMLElement {
    const ghost = document.createElement('span');
    ghost.textContent = text;
    ghost.style.cssText = `
      position: fixed;
      z-index: 2000;
      font-size: 20px;
      font-weight: 700;
      color: ${color};
      text-shadow: 0 2px 8px rgba(0,0,0,0.35), 0 0 12px ${color}80;
      pointer-events: none;
      user-select: none;
      transform: translate(-50%, -50%);
      will-change: transform, opacity;
      font-family: inherit;
    `;
    return ghost;
  }

  private positionFixed(el: HTMLElement, x: number, y: number): void {
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
  }

  private sampleQuadraticBezier(
    p: { startX: number; startY: number; midX: number; midY: number; endX: number; endY: number },
    frames: number
  ): Array<{ x: number; y: number }> {
    const result: Array<{ x: number; y: number }> = [];
    for (let i = 0; i < frames; i++) {
      const t = i / (frames - 1);
      // Quadratic Bezier: B(t) = (1-t)²P0 + 2(1-t)t P1 + t²P2
      const mt = 1 - t;
      const x = mt * mt * p.startX + 2 * mt * t * p.midX + t * t * p.endX;
      const y = mt * mt * p.startY + 2 * mt * t * p.midY + t * t * p.endY;
      result.push({ x, y });
    }
    return result;
  }
}
