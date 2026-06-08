/**
 * 用户中心主组件（桌面端）
 *
 * 按照 PRD 第 6.5 节布局规范重构：
 * - 顶部导航栏
 * - 主内容区（单列布局，无侧边栏）
 * - 浮动 AI 助手按钮
 * - 底部状态栏
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router, RouterModule } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../core/models/auth.models';
import { AuthService } from '../core/services/auth.service';
import { ROUTES } from '../routes.const';

import { UserFooterComponent } from './components/user-footer/user-footer.component';
import { UserNavbarComponent } from './components/user-navbar/user-navbar.component';
import { UserCenterService } from './services/user-center.service';

@Component({
  selector: 'app-user-center',
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
  template: `
    <div class="user-center-container">
      <!-- 顶部导航栏 -->
      <app-user-navbar></app-user-navbar>

      <!-- 主内容区 -->
      <main class="main-content">
        <div class="content-wrapper">
          <router-outlet></router-outlet>
        </div>
        <app-user-footer></app-user-footer>
      </main>

      <!-- 浮动 AI 助手按钮 -->
      <button
        class="ai-assistant-fab"
        (click)="toggleAIAssistant()"
        matTooltip="AI 老师"
        [class.expanded]="showAIAssistant"
      >
        <mat-icon>{{ showAIAssistant ? 'close' : 'smart_toy' }}</mat-icon>
      </button>

      <!-- AI 对话面板 -->
      <div class="ai-panel" [class.show]="showAIAssistant">
        <div class="ai-panel-header">
          <div class="ai-panel-title">
            <mat-icon>smart_toy</mat-icon>
            <span>AI 老师</span>
          </div>
          <button mat-icon-button (click)="toggleAIAssistant()">
            <mat-icon>close</mat-icon>
          </button>
        </div>
        <div class="ai-panel-content">
          <div class="ai-message ai-message-welcome">
            <div class="ai-avatar">🤖</div>
            <div class="ai-bubble">
              你好！我是你的 AI 老师 👋<br><br>
              有什么我可以帮助你的吗？
            </div>
          </div>
        </div>
        <div class="ai-panel-input">
          <input
            type="text"
            placeholder="输入你的问题..."
            class="ai-input"
            [(ngModel)]="aiMessage"
            (keyup.enter)="sendAIMessage()"
          />
          <button mat-icon-button color="primary" (click)="sendAIMessage()">
            <mat-icon>send</mat-icon>
          </button>
        </div>
      </div>

      <!-- 底部状态栏 -->
      <footer class="status-bar">
        <div class="status-item">
          <span class="status-dot" [class.online]="deviceStatus === 'online'" [class.offline]="deviceStatus !== 'online'"></span>
          <span>{{ deviceStatus === 'online' ? '设备已连接' : '设备未连接' }}</span>
        </div>
        <div class="status-item" *ngIf="hardwareInfo">
          <mat-icon>memory</mat-icon>
          <span>{{ hardwareInfo }}</span>
        </div>
        <div class="status-item version">
          <span>v1.0.0</span>
        </div>
      </footer>
    </div>
  `,
  styles: [
    `
      .user-center-container {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        background-color: var(--color-background, #f8fafc);
      }

      /* 主内容区 */
      .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding-bottom: 28px; /* 为状态栏留空间 */
      }

      .content-wrapper {
        flex: 1;
        max-width: 1400px;
        width: 100%;
        margin: 0 auto;
        padding: 24px;
      }

      /* 浮动 AI 助手按钮 */
      .ai-assistant-fab {
        position: fixed;
        bottom: 48px; /* 在状态栏上方 */
        right: 24px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .ai-assistant-fab:hover {
        transform: scale(1.1);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.5);
      }

      .ai-assistant-fab.expanded {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      }

      .ai-assistant-fab mat-icon {
        font-size: 24px;
        width: 24px;
        height: 24px;
      }

      /* AI 对话面板 */
      .ai-panel {
        position: fixed;
        bottom: 120px;
        right: 24px;
        width: 380px;
        max-height: 500px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
        opacity: 0;
        visibility: hidden;
        transform: translateY(20px);
        transition: all 0.3s ease;
        z-index: 999;
        overflow: hidden;
      }

      .ai-panel.show {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
      }

      .ai-panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .ai-panel-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
      }

      .ai-panel-content {
        flex: 1;
        padding: 16px;
        overflow-y: auto;
        max-height: 300px;
      }

      .ai-message {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
      }

      .ai-message.user {
        flex-direction: row-reverse;
      }

      .ai-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #f1f5f9;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
      }

      .ai-bubble {
        background: #f1f5f9;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 14px;
        line-height: 1.5;
        max-width: 80%;
      }

      .ai-message.user .ai-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .ai-panel-input {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        border-top: 1px solid #e2e8f0;
      }

      .ai-input {
        flex: 1;
        padding: 10px 16px;
        border: 1px solid #e2e8f0;
        border-radius: 24px;
        font-size: 14px;
        outline: none;
        transition: border-color 0.2s;
      }

      .ai-input:focus {
        border-color: #667eea;
      }

      /* 底部状态栏 */
      .status-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 28px;
        background: #0f172a;
        color: #94a3b8;
        display: flex;
        align-items: center;
        padding: 0 16px;
        font-size: 12px;
        z-index: 998;
      }

      .status-item {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 0 12px;
        border-right: 1px solid #334155;
      }

      .status-item:first-child {
        padding-left: 0;
      }

      .status-item.version {
        margin-left: auto;
        border-right: none;
        border-left: 1px solid #334155;
      }

      .status-item mat-icon {
        font-size: 14px;
        width: 14px;
        height: 14px;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #ef4444;
      }

      .status-dot.online {
        background: #22c55e;
      }

      /* 响应式 */
      @media (max-width: 1024px) {
        .content-wrapper {
          padding: 16px;
        }

        .ai-panel {
          width: calc(100vw - 48px);
          right: 24px;
          left: 24px;
        }
      }

      @media (max-width: 768px) {
        .ai-panel {
          width: calc(100vw - 32px);
          right: 16px;
          left: 16px;
          bottom: 100px;
        }

        .ai-assistant-fab {
          bottom: 36px;
          right: 16px;
        }
      }
    `,
  ],
})
export class UserCenterComponent implements OnInit, OnDestroy {
  readonly ROUTES = ROUTES;

  isMobile = false;
  currentUser: User | null = null;
  userType: string | undefined;

  // AI 助手状态
  showAIAssistant = false;
  aiMessage = '';
  aiMessages: Array<{ role: 'user' | 'ai'; content: string }> = [];

  // 设备状态
  deviceStatus: 'online' | 'offline' = 'online';
  hardwareInfo = 'ESP32 已连接';

  private destroy$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private userCenterService: UserCenterService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // 检查屏幕宽度
    this.checkScreenWidth();
    window.addEventListener('resize', () => this.checkScreenWidth());

    // 订阅当前用户信息
    this.userCenterService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      this.userType = user?.userType;
    });

    // 如果没有用户信息，尝试获取
    if (!this.currentUser) {
      this.currentUser = this.userCenterService.getCurrentUser();
      this.userType = this.currentUser?.userType;
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    window.removeEventListener('resize', () => this.checkScreenWidth());
  }

  /**
   * 检查屏幕宽度，判断是否为移动端
   */
  checkScreenWidth(): void {
    this.isMobile = window.innerWidth <= 768;
  }

  /**
   * 切换 AI 助手面板
   */
  toggleAIAssistant(): void {
    this.showAIAssistant = !this.showAIAssistant;
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

  /**
   * 登出
   */
  logout(): void {
    this.userCenterService.logout();
  }
}
