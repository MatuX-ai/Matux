import { Component } from '@angular/core';

@Component({
  selector: 'app-license-list',
  template: `
    <div class="license-list">
      <h1>许可证管理</h1>
      <p>许可证列表和管理功能</p>
      <div class="placeholder-content">
        <p>这里将显示许可证列表、批量操作、续费、吊销等功能</p>
      </div>
    </div>
  `,
  styles: [
    `
      .license-list {
        padding: 20px;
      }

      .placeholder-content {
        margin-top: 20px;
        padding: 20px;
        background: #f5f5f5;
        border-radius: 8px;
        text-align: center;
      }
    `,
  ],
})
export class LicenseListComponent {}
