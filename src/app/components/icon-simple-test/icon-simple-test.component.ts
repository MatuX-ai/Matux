import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { MacIconComponent } from '../../shared/components/mac-icons/mac-icon.component';

@Component({
  selector: 'app-icon-simple-test',
  standalone: true,
  imports: [MacIconComponent, CommonModule],
  template: `
    <div style="padding: 20px; font-family: sans-serif;">
      <h1>简单图标测试</h1>

      <section style="margin: 20px 0; padding: 20px; background: #f5f5f7; border-radius: 8px;">
        <h2>测试 1: 原始 img 标签</h2>
        <div style="margin: 10px;">
          <strong>相对路径 (assets/icons/rocket.svg):</strong><br />
          <img
            src="assets/icons/rocket.svg"
            width="48"
            height="48"
            alt="rocket"
            style="border: 2px solid #3B82F6;"
          />
        </div>
        <div style="margin: 10px;">
          <strong>绝对路径 (/assets/icons/rocket.svg):</strong><br />
          <img
            src="/assets/icons/rocket.svg"
            width="48"
            height="48"
            alt="rocket"
            style="border: 2px solid #3B82F6;"
          />
        </div>
      </section>

      <section style="margin: 20px 0; padding: 20px; background: #f5f5f7; border-radius: 8px;">
        <h2>测试 2: MacIcon 组件</h2>
        <p>如果看不到图标,说明组件有问题</p>
        <div style="margin: 10px; display: flex; align-items: center; gap: 10px;">
          <strong>rocket (lg):</strong>
          <div style="border: 2px solid #3B82F6; padding: 10px;">
            <mac-icon name="rocket" size="lg"></mac-icon>
          </div>
        </div>
      </section>

      <section style="margin: 20px 0; padding: 20px; background: #f5f5f7; border-radius: 8px;">
        <h2>测试 3: 动态绑定</h2>
        <div style="margin: 10px;">
          <strong>动态路径:</strong><br />
          <img
            [src]="rocketPath"
            width="48"
            height="48"
            alt="rocket"
            style="border: 2px solid #3B82F6;"
          />
        </div>
        <p>当前路径: {{ rocketPath }}</p>
      </section>

      <section style="margin: 20px 0; padding: 20px; background: #e0f2fe; border-radius: 8px;">
        <h2>调试信息</h2>
        <ul>
          <li>当前页面URL: {{ currentUrl }}</li>
          <li>Base HREF: {{ baseHref }}</li>
          <li>浏览器环境: {{ userAgent }}</li>
        </ul>
        <button
          (click)="testFetch()"
          style="padding: 10px 20px; background: #3B82F6; color: white; border: none; border-radius: 4px; cursor: pointer;"
        >
          测试 Fetch API
        </button>
        <div
          *ngIf="fetchResult"
          style="margin-top: 10px; padding: 10px; background: white; border-radius: 4px;"
        >
          <pre>{{ fetchResult }}</pre>
        </div>
      </section>
    </div>
  `,
  styles: [''],
})
export class IconSimpleTestComponent {
  rocketPath = 'assets/icons/rocket.svg';
  currentUrl = window.location.href;
  baseHref = document.querySelector('base')?.getAttribute('href') ?? '';
  userAgent = navigator.userAgent;
  fetchResult = '';

  constructor() {
    // Component initialized
  }

  testFetch(): void {
    const results: string[] = [];
    const paths = [
      'assets/icons/rocket.svg',
      '/assets/icons/rocket.svg',
      './assets/icons/rocket.svg',
    ];

    paths.forEach((path) => {
      fetch(path)
        .then((response) => {
          const result = `✓ ${path}: ${response.status} ${response.statusText}`;
          results.push(result);
        })
        .catch((error: unknown) => {
          const result = `✗ ${path}: ${(error as Error).message}`;
          results.push(result);
        });
    });

    this.fetchResult = results.join('\n');
  }
}
