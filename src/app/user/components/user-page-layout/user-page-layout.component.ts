/**
 * 用户中心页面布局组件（桌面端）
 *
 * 统一布局容器，按照 PRD 第 6.5 节规范：
 * - 顶部导航栏
 * - 主内容区（单列布局，无侧边栏）
 * - 浮动 AI 助手按钮
 * - 底部状态栏
 *
 * 所有子页面共享此布局
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AiAssistantToggleService } from '../../../core/services/ai-assistant-toggle.service';
import { AuthService } from '../../../core/services/auth.service';
import { ROUTES } from '../../../routes.const';
import { UserCenterService } from '../../services/user-center.service';
import { UserFooterComponent } from '../user-footer/user-footer.component';
import { UserNavbarComponent } from '../user-navbar/user-navbar.component';

@Component({
  selector: 'app-user-page-layout',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatTooltipModule,
    UserNavbarComponent,
    UserFooterComponent,
  ],
  templateUrl: './user-page-layout.component.html',
  styleUrls: ['./user-page-layout.component.scss'],
})
export class UserPageLayoutComponent implements OnInit, OnDestroy {
  readonly ROUTES = ROUTES;

  isMobile = false;
  currentUser: User | null = null;

  // AI 助手状态
  showAIAssistant = false;
  aiMessage = '';
  aiMessages: Array<{ role: 'user' | 'ai'; content: string }> = [];

  // 【P3 修复】设备状态已移至全局 <app-status-bar>，此处不再持有
  // 保留占位避免模板编译错误,实际 UI 由 AppComponent 提供

  private destroy$ = new Subject<void>();
  // 保存 resize handler 引用，用于正确移除监听器
  private boundCheckScreenWidth: () => void = () => {};

  constructor(
    private authService: AuthService,
    private userCenterService: UserCenterService,
    private aiToggle: AiAssistantToggleService
  ) {}

  ngOnInit(): void {
    // 保存 handler 引用，确保 add/remove 使用同一函数
    this.boundCheckScreenWidth = () => this.checkScreenWidth();

    // 检查屏幕宽度
    this.checkScreenWidth();
    window.addEventListener('resize', this.boundCheckScreenWidth);

    // 订阅当前用户信息
    this.userCenterService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
    });

    // 如果没有用户信息，尝试获取
    if (!this.currentUser) {
      this.currentUser = this.userCenterService.getCurrentUser();
    }

    // 【P1 修复】同步外部 AI 面板开关（如 FAB 点击）到本地状态
    this.aiToggle.panelOpen$.pipe(takeUntil(this.destroy$)).subscribe((open) => {
      this.showAIAssistant = open;
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    // 使用保存的引用正确移除监听器
    if (this.boundCheckScreenWidth) {
      window.removeEventListener('resize', this.boundCheckScreenWidth);
    }
  }

  /**
   * 检查屏幕宽度，判断是否为移动端
   */
  checkScreenWidth(): void {
    this.isMobile = window.innerWidth <= 768;
  }

  /**
   * 切换 AI 助手面板
   * 通过共享服务切换,保证 FAB 与本页内 FAB 双向联动
   */
  toggleAIAssistant(): void {
    this.aiToggle.toggle();
  }

  /**
   * 发送 AI 消息
   */
  sendAIMessage(): void {
    if (!this.aiMessage.trim()) return;

    // 添加用户消息
    this.aiMessages.push({
      role: 'user',
      content: this.aiMessage,
    });

    const userMessage = this.aiMessage;
    this.aiMessage = '';

    // 模拟 AI 响应
    setTimeout(() => {
      this.aiMessages.push({
        role: 'ai',
        content: `好的，你说的是："${userMessage}"\n\n让我帮你解答...`,
      });
    }, 1000);
  }
}
