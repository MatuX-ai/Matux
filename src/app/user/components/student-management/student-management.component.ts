/**
 * 学生管理组件（教师）
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-student-management',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="student-container">
      <h2>学生管理</h2>
      <p>学生管理页面开发中...</p>
    </div>
  `,
  styles: [
    `
      .student-container {
        padding: 20px;
      }
    `,
  ],
})
export class StudentManagementComponent implements OnInit {
  constructor() {}

  ngOnInit(): void {}
}
