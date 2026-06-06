/**
 * 用户中心底部导航组件
 *
 * 显示版权信息和辅助链接
 */

import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-user-footer',
  standalone: true,
  imports: [CommonModule, RouterModule, MatToolbarModule, MatIconModule, MatButtonModule],
  template: `
    <footer class="user-footer">
      <div class="footer-content">
        <div class="footer-links">
          <a mat-button routerLink="/user/profile">
            <mat-icon>person</mat-icon>
            个人资料
          </a>
          <a mat-button routerLink="/user/token">
            <mat-icon>token</mat-icon>
            Token管理
          </a>
          <a mat-button href="javascript:void(0)" (click)="openHelp()">
            <mat-icon>help_outline</mat-icon>
            帮助中心
          </a>
          <a mat-button href="javascript:void(0)" (click)="openAbout()">
            <mat-icon>info</mat-icon>
            关于我们
          </a>
        </div>
        <div class="footer-copyright">
          <span>&copy; {{ currentYear }} iMato. All rights reserved.</span>
          <span class="divider">|</span>
          <span>Powered by iMato Platform</span>
        </div>
      </div>
    </footer>
  `,
  styles: [
    `
      .user-footer {
        background: var(--color-surface);
        border-top: 1px solid var(--color-divider);
        padding: 16px 24px;
        margin-top: auto;
      }

      .footer-content {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
      }

      .footer-links {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 8px;
      }

      .footer-links a {
        font-size: 13px;
        color: var(--color-text-secondary);
      }

      .footer-links mat-icon {
        font-size: 16px;
        width: 16px;
        height: 16px;
        margin-right: 4px;
      }

      .footer-copyright {
        font-size: 12px;
        color: var(--color-text-disabled);
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .divider {
        color: var(--color-divider);
      }

      @media (max-width: 768px) {
        .footer-links {
          flex-direction: column;
          align-items: center;
        }
      }
    `,
  ],
})
export class UserFooterComponent {
  currentYear = new Date().getFullYear();

  openHelp(): void {
    console.warn('打开帮助中心');
  }

  openAbout(): void {
    console.warn('打开关于我们');
  }
}
