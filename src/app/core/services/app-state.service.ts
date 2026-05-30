/**
 * 全局状态管理服务
 *
 * @description 使用 Angular Signals 统一管理应用状态
 */

import { Injectable } from '@angular/core';
import { computed, signal } from '@angular/core';

// 用户订阅状态
export interface UserSubscription {
  id: string;
  planId: string;
  status: 'active' | 'pending' | 'cancelled' | 'expired';
  startDate: string;
  endDate?: string;
  autoRenew: boolean;
}

// 主题状态
export type ThemeMode = 'light' | 'dark' | 'auto';

// 加载状态
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

/**
 * 全局应用状态
 */
class AppState {
  // 用户订阅状态
  subscriptions = signal<UserSubscription[]>([]);
  activeSubscriptions = computed(() =>
    this.subscriptions().filter((sub) => sub.status === 'active')
  );

  // 主题状态
  themeMode = signal<ThemeMode>('auto');
  isDarkMode = computed(() => {
    const mode = this.themeMode();
    if (mode === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return mode === 'dark';
  });

  // 加载状态
  loadingState = signal<LoadingState>({ isLoading: false });

  // 用户信息（可扩展）
  isLoggedIn = signal(false);
  userId = signal<string | null>(null);

  // UI 状态
  sidebarOpen = signal(false);
  notificationsOpen = signal(false);

  // PWA 状态
  isOffline = signal(false);
  pwaInstallState = signal<'installed' | 'installable' | 'not-supported'>('not-supported');
  pwaUpdateStrategy = signal<'immediate' | 'manual' | 'background'>('manual');
  pwaAvailableUpdate = signal<boolean>(false);
}

@Injectable({
  providedIn: 'root',
})
export class AppStateService {
  private readonly state = new AppState();

  // ========== 订阅状态管理 ==========

  readonly subscriptions = this.state.subscriptions;
  readonly activeSubscriptions = this.state.activeSubscriptions;

  updateSubscriptions(subs: UserSubscription[]): void {
    this.state.subscriptions.set(subs);
  }

  addSubscription(sub: UserSubscription): void {
    this.state.subscriptions.update((subs) => [...subs, sub]);
  }

  updateSubscription(id: string, updates: Partial<UserSubscription>): void {
    this.state.subscriptions.update((subs) =>
      subs.map((sub) => (sub.id === id ? { ...sub, ...updates } : sub))
    );
  }

  removeSubscription(id: string): void {
    this.state.subscriptions.update((subs) => subs.filter((sub) => sub.id !== id));
  }

  hasActiveSubscription(): boolean {
    return this.state.activeSubscriptions().length > 0;
  }

  // ========== 主题状态管理 ==========

  readonly themeMode = this.state.themeMode;
  readonly isDarkMode = this.state.isDarkMode;

  setThemeMode(mode: ThemeMode): void {
    this.state.themeMode.set(mode);
    this.applyTheme(mode);
  }

  toggleTheme(): void {
    const currentMode = this.state.themeMode();
    const newMode: ThemeMode = currentMode === 'light' ? 'dark' : 'light';
    this.setThemeMode(newMode);
  }

  private applyTheme(mode: ThemeMode): void {
    const isDark =
      mode === 'auto' ? window.matchMedia('(prefers-color-scheme: dark)').matches : mode === 'dark';

    if (isDark) {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    }

    // 存储到 localStorage
    localStorage.setItem('theme-mode', mode);
  }

  initTheme(): void {
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode;
    if (savedMode) {
      this.setThemeMode(savedMode);
    } else {
      this.setThemeMode('auto');
    }
  }

  // ========== 加载状态管理 ==========

  readonly loadingState = this.state.loadingState;

  showLoading(message?: string): void {
    this.state.loadingState.set({ isLoading: true, message });
  }

  hideLoading(): void {
    this.state.loadingState.set({ isLoading: false });
  }

  // ========== 用户状态管理 ==========

  readonly isLoggedIn = this.state.isLoggedIn;
  readonly userId = this.state.userId;

  setUserLoggedIn(userId: string): void {
    this.state.isLoggedIn.set(true);
    this.state.userId.set(userId);
    localStorage.setItem('user-id', userId);
  }

  setUserLoggedOut(): void {
    this.state.isLoggedIn.set(false);
    this.state.userId.set(null);
    localStorage.removeItem('user-id');
    // 清空订阅状态
    this.updateSubscriptions([]);
  }

  initUserState(): void {
    const savedUserId = localStorage.getItem('user-id');
    if (savedUserId) {
      this.state.userId.set(savedUserId);
      this.state.isLoggedIn.set(true);
    }
  }

  // ========== UI 状态管理 ==========

  readonly sidebarOpen = this.state.sidebarOpen;
  readonly notificationsOpen = this.state.notificationsOpen;

  // ========== PWA 状态管理 ==========

  readonly isOffline = this.state.isOffline;
  readonly pwaInstallState = this.state.pwaInstallState;
  readonly pwaUpdateStrategy = this.state.pwaUpdateStrategy;
  readonly pwaAvailableUpdate = this.state.pwaAvailableUpdate;

  setOfflineStatus(offline: boolean): void {
    this.state.isOffline.set(offline);
  }

  setPwaInstallState(state: 'installed' | 'installable' | 'not-supported'): void {
    this.state.pwaInstallState.set(state);
  }

  setPwaUpdateStrategy(strategy: 'immediate' | 'manual' | 'background'): void {
    this.state.pwaUpdateStrategy.set(strategy);
  }

  setPwaAvailableUpdate(hasUpdate: boolean): void {
    this.state.pwaAvailableUpdate.set(hasUpdate);
  }

  toggleSidebar(): void {
    this.state.sidebarOpen.update((open) => !open);
  }

  closeSidebar(): void {
    this.state.sidebarOpen.set(false);
  }

  toggleNotifications(): void {
    this.state.notificationsOpen.update((open) => !open);
  }

  // ========== 重置状态 ==========

  resetAll(): void {
    this.updateSubscriptions([]);
    this.setThemeMode('auto');
    this.hideLoading();
    this.state.isLoggedIn.set(false);
    this.state.userId.set(null);
    this.state.sidebarOpen.set(false);
    this.state.notificationsOpen.set(false);
    this.state.isOffline.set(false);
    this.state.pwaInstallState.set('not-supported');
    this.state.pwaUpdateStrategy.set('manual');
    this.state.pwaAvailableUpdate.set(false);

    // 清除 localStorage（可选）
    // localStorage.clear();
  }

  // ========== 辅助方法 ==========

  // 导出当前状态快照（用于调试）
  exportState(): Record<string, unknown> {
    return {
      subscriptions: this.state.subscriptions(),
      activeSubscriptionsCount: this.state.activeSubscriptions().length,
      themeMode: this.state.themeMode(),
      isDarkMode: this.state.isDarkMode(),
      loadingState: this.state.loadingState(),
      isLoggedIn: this.state.isLoggedIn(),
      userId: this.state.userId(),
      sidebarOpen: this.state.sidebarOpen(),
      notificationsOpen: this.state.notificationsOpen(),
    };
  }
}
