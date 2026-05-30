/**
 * AI 教育仪表板组件
 */

import { Component } from '@angular/core';

@Component({
  selector: 'app-ai-edu-dashboard',
  standalone: true,
  template: `
    <div class="ai-edu-dashboard">
      <h2>AI 教育学习中心</h2>
      <p>AI 辅助学习功能开发中...</p>
    </div>
  `,
  styles: [
    `
      .ai-edu-dashboard {
        padding: 24px;
      }
      h2 {
        color: #333;
        margin-bottom: 16px;
      }
    `,
  ],
})
export class AIEduDashboardComponent {}
