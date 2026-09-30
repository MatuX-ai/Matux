/**
 * Coming Soon 占位页
 *
 * 用于尚未实现的路由(/plugins/installed、/store/...、/subscription/plans/:id 等)
 * 统一提示用户功能即将上线，避免点击后跳到 404
 *
 * 用法: 路由配置指向此组件,通过 query 参数传入模块名
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ActivatedRoute, RouterModule } from '@angular/router';

import { ROUTES } from '../../../routes.const';

@Component({
  selector: 'app-coming-soon',
  standalone: true,
  imports: [CommonModule, RouterModule, MatButtonModule, MatIconModule],
  template: `
    <div class="coming-soon-container">
      <div class="coming-soon-card">
        <div class="icon-wrap">
          <mat-icon>construction</mat-icon>
        </div>
        <h1 class="title">{{ title }}</h1>
        <p class="subtitle" *ngIf="subtitle">{{ subtitle }}</p>
        <p class="description">{{ description }}</p>
        <div class="actions">
          <button mat-flat-button color="primary" [routerLink]="ROUTES.USER.DASHBOARD">
            <mat-icon>home</mat-icon>
            返回首页
          </button>
          <button mat-stroked-button [routerLink]="ROUTES.USER.COURSES">
            <mat-icon>school</mat-icon>
            浏览课程
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .coming-soon-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        padding: 24px;
      }

      .coming-soon-card {
        max-width: 480px;
        padding: 48px 32px;
        text-align: center;
        border-radius: 20px;
        background: var(--matux-color-surface, #ffffff);
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
      }

      .icon-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 80px;
        height: 80px;
        margin: 0 auto 24px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f59e0b, #ef4444);
        color: white;
        box-shadow: 0 8px 20px rgba(245, 158, 11, 0.25);
      }

      .icon-wrap mat-icon {
        font-size: 40px;
        width: 40px;
        height: 40px;
      }

      .title {
        margin: 0 0 12px;
        font-size: 22px;
        font-weight: 700;
        color: var(--matux-color-text-primary, #0f172a);
      }

      .subtitle {
        margin: 0 0 8px;
        font-size: 16px;
        font-weight: 600;
        color: var(--matux-color-warning-dark, #b45309);
      }

      .description {
        margin: 0 0 24px;
        font-size: 14px;
        line-height: 1.6;
        color: var(--matux-color-text-secondary, #475569);
      }

      .actions {
        display: flex;
        gap: 12px;
        justify-content: center;
        flex-wrap: wrap;
      }

      .actions button {
        border-radius: 12px;
        font-weight: 600;
      }
    `,
  ],
})
export class ComingSoonComponent implements OnInit {
  @Input() title = '功能即将上线';
  @Input() subtitle = '';
  @Input() description = '该模块正在开发中，敬请期待。我们会尽快完善此功能。';

  readonly ROUTES = ROUTES;

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    // 从路由 data 读取配置,优先于 @Input 默认值
    const data = this.route.snapshot.data as {
      title?: string;
      subtitle?: string;
      description?: string;
    };
    if (data.title) this.title = data.title;
    if (data.subtitle) this.subtitle = data.subtitle;
    if (data.description) this.description = data.description;
  }
}
