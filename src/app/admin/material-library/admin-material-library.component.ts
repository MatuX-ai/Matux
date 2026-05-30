/**
 * @deprecated 素材管理已解耦到 OpenMTSciEd 项目。此组件仅保留用于向后兼容路由引用。
 * 请直接访问 OpenMTSciEd 项目进行素材管理。
 */

import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-admin-material-library',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule],
  template: `
    <div class="migration-notice">
      <mat-card>
        <mat-card-header>
          <mat-card-title>功能已迁移</mat-card-title>
          <mat-card-subtitle>素材库管理</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p>素材库管理功能已迁移到独立的 <strong>OpenMTSciEd</strong> 课件管理系统。</p>
          <p>请在 OpenMTSciEd 项目中进行素材的上传、分类和管理操作。</p>
          <div class="info-box">
            <strong>迁移说明：</strong>
            <ul>
              <li>素材上传与管理 → OpenMTSciEd 素材管理系统</li>
              <li>课件素材关联 → OpenMTSciEd 课件管理系统</li>
              <li>本路由保留仅用于向后兼容，未来版本将移除</li>
            </ul>
          </div>
        </mat-card-content>
        <mat-card-actions>
          <a mat-raised-button color="primary" href="/admin/courses" class="nav-link">
            前往课程库
          </a>
        </mat-card-actions>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .migration-notice {
        max-width: 600px;
        margin: 40px auto;
        padding: 0 20px;
      }
      .info-box {
        background: #f5f5f5;
        border-left: 4px solid #ff9800;
        padding: 12px 16px;
        margin: 16px 0;
        border-radius: 4px;
      }
      .info-box ul {
        margin: 8px 0 0;
        padding-left: 20px;
      }
      .info-box li {
        margin: 4px 0;
        font-size: 14px;
      }
      mat-card-actions {
        padding: 16px;
      }
      .nav-link {
        text-decoration: none;
      }
    `,
  ],
})
export class AdminMaterialLibraryComponent {}
