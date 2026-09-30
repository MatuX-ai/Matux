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

import { I18nService } from '../../../core/services/i18n.service';
import { ROUTES } from '../../../routes.const';

@Component({
  selector: 'app-user-footer',
  standalone: true,
  imports: [CommonModule, RouterModule, MatToolbarModule, MatIconModule, MatButtonModule],
  template: `
    <footer class="user-footer">
      <div class="footer-content">
        <div class="footer-links">
          <a
            mat-button
            [routerLink]="ROUTES.USER.PROFILE"
            [attr.aria-label]="i18n.translate('userFooter.profile')"
          >
            <mat-icon>person</mat-icon>
            {{ i18n.translate('userFooter.profile') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.USER.TOKEN"
            [attr.aria-label]="i18n.translate('userFooter.token')"
          >
            <mat-icon>token</mat-icon>
            {{ i18n.translate('userFooter.token') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.USER.LEARNING_PROFILE"
            [attr.aria-label]="i18n.translate('userFooter.learningProfile')"
          >
            <mat-icon>insights</mat-icon>
            {{ i18n.translate('userFooter.learningProfile') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.USER.TEACHING_SUGGESTIONS"
            [attr.aria-label]="i18n.translate('userFooter.teachingSuggestions')"
          >
            <mat-icon>lightbulb</mat-icon>
            {{ i18n.translate('userFooter.teachingSuggestions') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.USER.EMOTIONAL_COMPANION"
            [attr.aria-label]="i18n.translate('userFooter.emotionalCompanion')"
          >
            <mat-icon>favorite</mat-icon>
            {{ i18n.translate('userFooter.emotionalCompanion') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.USER.REPORTS"
            [attr.aria-label]="i18n.translate('userFooter.reports')"
          >
            <mat-icon>assessment</mat-icon>
            {{ i18n.translate('userFooter.reports') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.USER.SETTINGS"
            [attr.aria-label]="i18n.translate('userFooter.settings')"
          >
            <mat-icon>settings</mat-icon>
            {{ i18n.translate('userFooter.settings') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.HELP"
            [attr.aria-label]="i18n.translate('userFooter.help')"
          >
            <mat-icon>help_outline</mat-icon>
            {{ i18n.translate('userFooter.help') }}
          </a>
          <a
            mat-button
            [routerLink]="ROUTES.ABOUT"
            [attr.aria-label]="i18n.translate('userFooter.about')"
          >
            <mat-icon>info</mat-icon>
            {{ i18n.translate('userFooter.about') }}
          </a>
        </div>
        <div class="footer-copyright">
          <span>&copy; {{ currentYear }} iMato. {{ i18n.translate('userFooter.copyright') }}.</span>
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
        // 【对比度修复 #7】原 color: var(--color-text-disabled) 即 #a8a29e on #fff
        // 对比度 2.52:1，12px 文本需要 WCAG AA 4.5:1，严重违规。
        // 改用 --color-text-secondary (#57534e) 后对比度 7.63:1，通过 AAA。
        color: var(--color-text-secondary, #57534e);
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .divider {
        // 【对比度修复 #23】原 color: var(--color-divider) 即 #e7e5e4 on #fff
        // 对比度 1.26:1，作为装饰性文字分隔符可接受，但为了语义一致性
        // 仍升级为中灰 #64748b (4.92:1)。
        color: var(--color-gray-500, #64748b);
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

  // 路由常量供模板使用
  readonly ROUTES = ROUTES;

  // 【P2】i18n 服务供模板调用
  constructor(public i18n: I18nService) {}
}
