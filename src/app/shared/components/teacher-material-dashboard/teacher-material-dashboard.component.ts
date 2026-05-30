/**
 * 教师课件库仪表板组件
 */

import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-teacher-material-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="material-dashboard">
      <h3>课件库管理</h3>
      <p class="placeholder">课件库功能开发中...</p>
    </div>
  `,
  styles: [
    `
      .material-dashboard {
        padding: 16px;
        background: #f9f9f9;
        border-radius: 8px;
      }
      h3 {
        margin: 0 0 8px 0;
        color: #333;
      }
      .placeholder {
        color: #999;
        font-size: 14px;
      }
    `,
  ],
})
export class TeacherMaterialDashboardComponent {}
