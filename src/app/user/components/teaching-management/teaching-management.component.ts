/**
 * 教学管理组件（教师）
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-teaching-management',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="teaching-container">
      <h2>教学管理</h2>
      <p>教学管理页面开发中...</p>
    </div>
  `,
  styles: [
    `
      .teaching-container {
        padding: 20px;
      }
    `,
  ],
})
export class TeachingManagementComponent implements OnInit {
  constructor() {}

  ngOnInit(): void {}
}
