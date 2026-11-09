/**
 * 粒子爆裂组件（P0-1 / P0-2 / P0-4 共享）
 *
 * 用法：
 * <app-sparkle-burst
 *   [active]="burstActive"
 *   [x]="x" [y]="y"
 *   [count]="12"
 *   [color]="'#fbbf24'"
 *   [durationMs]="600"
 * />
 *
 * 触发后会在 (x, y) 处喷出 count 颗粒子，每颗向随机方向飞出 60~100px。
 * 动画结束自动重置 active，供下次触发。
 *
 * a11y：尊重 prefers-reduced-motion，直接重置不播动画。
 *
 * @see 桌面端游戏化P0升级.md §2.1
 */

import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  ViewChild,
  inject,
  NgZone,
} from '@angular/core';

@Component({
  selector: 'app-sparkle-burst',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule],
  template: `
    <div
      #host
      class="sparkle-burst"
      [class.is-active]="active"
      [attr.aria-hidden]="true"
    ></div>
  `,
  styles: [
    `
      :host {
        position: fixed;
        inset: 0;
        z-index: 2000;
        pointer-events: none;
      }
      .sparkle-burst {
        position: absolute;
        inset: 0;
        pointer-events: none;
      }
      /* ::ng-deep 穿透视图封装，让动态创建的 .particle 节点也能命中样式 */
      :host ::ng-deep .particle {
        position: absolute;
        display: block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        will-change: transform, opacity;
        box-shadow: 0 0 8px currentColor;
      }
    `,
  ],
})
export class SparkleBurstComponent implements OnChanges, AfterViewInit {
  @Input() active = false;
  @Input() x = 0;
  @Input() y = 0;
  @Input() count = 12;
  @Input() color = '#fbbf24';
  @Input() durationMs = 800;

  @ViewChild('host', { static: true }) hostRef!: ElementRef<HTMLDivElement>;

  private readonly zone = inject(NgZone);

  ngAfterViewInit(): void {
    // 初始即激活时自动触发
    if (this.active) {
      this.burst();
    }
  }

  ngOnChanges(): void {
    if (this.active) {
      // 等待 DOM 渲染
      queueMicrotask(() => this.burst());
    }
  }

  private burst(): void {
    if (typeof window === 'undefined') return;
    const prefersReducedMotion = window.matchMedia?.(
      '(prefers-reduced-motion: reduce)'
    ).matches;
    if (prefersReducedMotion) return;

    const host = this.hostRef?.nativeElement;
    if (!host) return;

    // 清理旧粒子
    host.querySelectorAll('.particle').forEach((n) => n.remove());

    const particles: HTMLElement[] = [];
    for (let i = 0; i < this.count; i++) {
      const p = document.createElement('span');
      p.className = 'particle';
      const size = 6 + Math.random() * 4;
      p.style.width = `${size}px`;
      p.style.height = `${size}px`;
      p.style.left = `${this.x}px`;
      p.style.top = `${this.y}px`;
      p.style.background = this.color;
      p.style.color = this.color;
      host.appendChild(p);
      particles.push(p);
    }

    this.zone.runOutsideAngular(() => {
      const anims: Animation[] = [];
      particles.forEach((p) => {
        const angle = Math.random() * Math.PI * 2;
        const dist = 60 + Math.random() * 40;
        const dx = Math.cos(angle) * dist;
        const dy = Math.sin(angle) * dist;
        const a = p.animate(
          [
            { transform: 'translate(-50%, -50%) scale(0.4)', opacity: 1 },
            {
              transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(1.4)`,
              opacity: 0.9,
              offset: 0.4,
            },
            {
              transform: `translate(calc(-50% + ${dx * 1.2}px), calc(-50% + ${dy * 1.2 + 20}px)) scale(0)`,
              opacity: 0,
            },
          ],
          {
            duration: this.durationMs,
            easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
            fill: 'forwards',
          }
        );
        anims.push(a);
      });

      Promise.all(anims.map((a) => a.finished.catch(() => undefined))).then(() => {
        particles.forEach((p) => p.remove());
      });
    });
  }
}
