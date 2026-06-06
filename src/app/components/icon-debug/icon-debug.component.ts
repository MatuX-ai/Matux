import { Component } from '@angular/core';

import { MacIconComponent } from '../../shared/components/mac-icons/mac-icon.component';

@Component({
  selector: 'app-icon-debug',
  standalone: true,
  imports: [MacIconComponent],
  template: `
    <div class="icon-debug">
      <h2>图标调试信息</h2>

      <div class="test-section">
        <h3>1. 原始 img 标签测试</h3>
        <div class="icon-row">
          <span>相对路径:</span>
          <img src="assets/icons/rocket.svg" width="32" height="32" alt="rocket" />
        </div>
        <div class="icon-row">
          <span>绝对路径:</span>
          <img src="/assets/icons/rocket.svg" width="32" height="32" alt="rocket" />
        </div>
      </div>

      <div class="test-section">
        <h3>2. MacIcon 组件测试</h3>
        <div class="icon-row">
          <span>rocket (lg):</span>
          <mac-icon name="rocket" size="lg"></mac-icon>
        </div>
        <div class="icon-row">
          <span>gamepad (lg):</span>
          <mac-icon name="gamepad" size="lg"></mac-icon>
        </div>
        <div class="icon-row">
          <span>check_circle (sm):</span>
          <mac-icon name="check_circle" size="sm"></mac-icon>
        </div>
      </div>

      <div class="test-section">
        <h3>3. 所有测试图标</h3>
        @for (icon of testIcons; track icon) {
          <div class="icon-row">
            <span class="icon-name">{{ icon }}:</span>
            <mac-icon [name]="icon" size="md"></mac-icon>
            <img [src]="'assets/icons/' + icon + '.svg'" width="24" height="24" [alt]="icon" />
          </div>
        }
      </div>

      <div class="test-section">
        <h3>4. 控制台日志</h3>
        <p>打开浏览器开发者工具查看详细信息</p>
        <button (click)="logInfo()">打印调试信息</button>
      </div>
    </div>
  `,
  styles: [
    `
      .icon-debug {
        padding: 20px;
        max-width: 800px;
        margin: 0 auto;
        font-family: sans-serif;
      }
      .test-section {
        margin: 30px 0;
        padding: 20px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
      }
      .icon-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 10px 0;
        padding: 10px;
        background: #f5f5f7;
        border-radius: 4px;
      }
      .icon-name {
        font-weight: 600;
        min-width: 120px;
      }
      button {
        padding: 10px 20px;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      button:hover {
        background: #2563eb;
      }
    `,
  ],
})
export class IconDebugComponent {
  testIcons = [
    'rocket',
    'gamepad',
    'brain',
    'wifi',
    'robot',
    'lock_open',
    'star',
    'ar',
    'school',
    'award',
    'trending_up',
    'phone',
    'desktop',
    'gift',
    'link',
  ];

  logInfo(): void {
    /* eslint-disable no-console */
    console.log('=== 图标调试信息 ===');
    console.log('测试图标列表:', this.testIcons);
    console.log('当前URL:', window.location.href);
    console.log('Base HREF:', document.querySelector('base')?.getAttribute('href'));
    /* eslint-enable no-console */

    // 测试fetch
    this.testIcons.forEach((icon) => {
      const url = `assets/icons/${icon}.svg`;
      fetch(url)
        .then((response) => {
          /* eslint-disable-next-line no-console */
          console.log(`✓ ${icon}:`, response.ok ? '成功' : '失败', response.status);
        })
        .catch((error) => {
          console.error(`✗ ${icon}:`, error);
        });
    });
  }

  constructor() {
    /* eslint-disable-next-line no-console */
    console.log('IconDebugComponent 已加载');
    // 自动打印调试信息
    setTimeout(() => this.logInfo(), 1000);
  }
}
