import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/**
 * 主题管理服务
 * 负责处理主题切换、持久化和CSS变量更新
 */
@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  // 当前主题状态
  private currentThemeSubject = new BehaviorSubject<'light' | 'dark'>('light');

  // 可观察的主题变化
  public currentTheme$ = this.currentThemeSubject.asObservable();

  // 主题存储键名
  private readonly THEME_STORAGE_KEY = 'imatuproject-theme-preference';

  // CSS变量映射表
  private readonly themeVariables = {
    light: {
      '--background-color': '#ffffff',
      '--surface-color': '#ffffff',
      '--text-primary-color': '#212121',
      '--text-secondary-color': '#757575',
      '--text-disabled-color': '#9e9e9e',
      '--border-color': '#e0e0e0',
      '--primary-color': '#2196f3',
      '--primary-color-light': '#64b5f6',
      '--primary-color-dark': '#1976d2',
      '--secondary-color': '#9c27b0',
      '--success-color': '#4caf50',
      '--warning-color': '#ff9800',
      '--error-color': '#f44336',
      // 扩展的亮色主题变量
      '--surface-color-hover': '#f5f5f5',
      '--hover-color': 'rgba(0, 0, 0, 0.04)',
      '--focus-color': 'rgba(33, 150, 243, 0.2)',
      '--active-color': 'rgba(0, 0, 0, 0.08)',
      '--selected-color': 'rgba(33, 150, 243, 0.12)',
      '--divider-color': 'rgba(0, 0, 0, 0.12)',
      '--backdrop-color': 'rgba(0, 0, 0, 0.5)',
      '--scrim-color': 'rgba(0, 0, 0, 0.6)',
      '--input-background': '#ffffff',
      '--input-border': '#e0e0e0',
      '--input-placeholder': '#9e9e9e',
      '--input-focus-border': '#2196f3',
    },
    dark: {
      '--background-color': '#121212',
      '--surface-color': '#1e1e1e',
      '--text-primary-color': '#ffffff',
      '--text-secondary-color': '#b3b3b3',
      '--text-disabled-color': '#6f6f6f',
      '--border-color': '#333333',
      '--primary-color': '#BB86FC',
      '--primary-color-light': '#D0BCFF',
      '--primary-color-dark': '#9A67EA',
      '--secondary-color': '#03DAC6',
      '--success-color': '#4CAF50',
      '--warning-color': '#FF9800',
      '--error-color': '#CF6679',
      // 完整的暗色主题变量 (匹配新创建的SCSS文件)
      '--surface-color-hover': '#2d2d2d',
      '--hover-color': 'rgba(255, 255, 255, 0.08)',
      '--focus-color': 'rgba(187, 134, 252, 0.2)',
      '--active-color': 'rgba(255, 255, 255, 0.12)',
      '--selected-color': 'rgba(187, 134, 252, 0.16)',
      '--divider-color': 'rgba(255, 255, 255, 0.12)',
      '--backdrop-color': 'rgba(0, 0, 0, 0.5)',
      '--scrim-color': 'rgba(0, 0, 0, 0.6)',
      '--input-background': '#2d2d2d',
      '--input-border': '#444444',
      '--input-placeholder': '#757575',
      '--input-focus-border': '#BB86FC',
      '--on-primary-color': '#000000',
      '--on-secondary-color': '#000000',
      '--on-success-color': '#ffffff',
      '--on-warning-color': '#000000',
      '--on-error-color': '#ffffff',
      '--on-info-color': '#ffffff',
      '--border-color-light': '#2d2d2d',
      '--border-color-strong': '#444444',
      '--gray-50': '#2d2d2d',
      '--gray-100': '#333333',
      '--gray-200': '#444444',
      '--gray-300': '#555555',
      '--gray-400': '#666666',
      '--gray-500': '#777777',
      '--gray-600': '#888888',
      '--gray-700': '#999999',
      '--gray-800': '#aaaaaa',
      '--gray-900': '#bbbbbb',
      '--shadow-sm': '0 1px 2px rgba(0, 0, 0, 0.3)',
      '--shadow-md': '0 4px 6px rgba(0, 0, 0, 0.3)',
      '--shadow-lg': '0 10px 15px rgba(0, 0, 0, 0.3)',
      '--shadow-xl': '0 20px 25px rgba(0, 0, 0, 0.3)',
      '--shadow-inner': 'inset 0 2px 4px rgba(0, 0, 0, 0.3)',
      '--scrollbar-thumb': '#424242',
      '--scrollbar-track': '#1e1e1e',
      '--scrollbar-thumb-hover': '#616161',
      '--code-background': '#2d2d2d',
      '--code-text': '#f8f8f2',
      '--icon-color': '#e0e0e0',
      '--icon-color-disabled': '#6f6f6f',
      '--icon-color-primary': '#BB86FC',
      '--icon-color-success': '#4CAF50',
      '--icon-color-warning': '#FF9800',
      '--icon-color-error': '#CF6679',
      '--skeleton-base': '#2d2d2d',
      '--skeleton-highlight': '#3d3d3d',
      '--loading-spinner': '#BB86FC',
      '--card-background': '#1e1e1e',
      '--card-border': '#333333',
      '--dialog-background': '#2d2d2d',
      '--tooltip-background': '#424242',
      '--tooltip-text': '#ffffff',
      '--table-header': '#2d2d2d',
      '--table-row-even': '#1e1e1e',
      '--table-row-odd': '#252525',
      '--table-border': '#333333',
      '--navbar-background': '#1e1e1e',
      '--sidebar-background': '#121212',
      '--menu-item-hover': 'rgba(255, 255, 255, 0.08)',
      '--menu-item-active': 'rgba(187, 134, 252, 0.16)',
      '--toast-background': '#2d2d2d',
      '--alert-background': '#3d3d3d',
      '--badge-background': '#424242',
      '--progress-track': '#333333',
      '--progress-fill': '#BB86FC',
      '--slider-track': '#333333',
      '--slider-thumb': '#BB86FC',
      '--timeline-node': '#424242',
      '--timeline-line': '#333333',
      '--step-incomplete': '#424242',
      '--step-complete': '#4CAF50',
      '--step-active': '#BB86FC',
    },
  };

  constructor() {
    this.initializeTheme();
  }

  /**
   * 初始化主题
   * 从localStorage加载保存的主题或使用系统偏好
   */
  private initializeTheme(): void {
    const savedTheme = this.getStoredTheme();
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    let initialTheme: 'light' | 'dark' = 'light';

    if (savedTheme) {
      initialTheme = savedTheme;
    } else if (systemPrefersDark) {
      initialTheme = 'dark';
    }

    this.setTheme(initialTheme, false); // 不触发存储，因为这是初始化
  }

  /**
   * 切换主题
   */
  toggleTheme(): void {
    const currentTheme = this.currentThemeSubject.value;
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  /**
   * 设置特定主题
   * @param theme 主题名称 ('light' | 'dark')
   * @param save 是否保存到localStorage (默认true)
   */
  setTheme(theme: 'light' | 'dark', save: boolean = true): void {
    // 更新CSS类
    this.updateBodyClass(theme);

    // 更新CSS变量
    this.updateCSSVariables(theme);

    // 更新主题状态
    this.currentThemeSubject.next(theme);

    // 保存偏好设置
    if (save) {
      this.storeTheme(theme);
    }
  }

  /**
   * 获取当前主题
   */
  getCurrentTheme(): 'light' | 'dark' {
    return this.currentThemeSubject.value;
  }

  /**
   * 获取当前主题的可观察对象
   */
  getCurrentThemeObservable(): Observable<'light' | 'dark'> {
    return this.currentTheme$;
  }

  /**
   * 检查是否为暗色主题
   */
  isDarkTheme(): boolean {
    return this.currentThemeSubject.value === 'dark';
  }

  /**
   * 更新body元素的CSS类
   */
  private updateBodyClass(theme: 'light' | 'dark'): void {
    const body = document.body;
    body.classList.remove('theme-light', 'theme-dark');
    body.classList.add(`theme-${theme}`);

    // 同时更新data-theme属性用于Material主题
    body.setAttribute('data-theme', theme);
  }

  /**
   * 更新CSS自定义属性
   */
  private updateCSSVariables(theme: 'light' | 'dark'): void {
    const root = document.documentElement;
    const variables = this.themeVariables[theme];

    Object.entries(variables).forEach(([property, value]) => {
      root.style.setProperty(property, value);
    });
  }

  /**
   * 从localStorage获取保存的主题
   */
  private getStoredTheme(): 'light' | 'dark' | null {
    try {
      const stored = localStorage.getItem(this.THEME_STORAGE_KEY);
      if (stored === 'light' || stored === 'dark') {
        return stored;
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  /**
   * 将主题保存到localStorage
   */
  private storeTheme(theme: 'light' | 'dark'): void {
    try {
      localStorage.setItem(this.THEME_STORAGE_KEY, theme);
    } catch (error) {}
  }

  /**
   * 清除保存的主题设置
   */
  clearStoredTheme(): void {
    try {
      localStorage.removeItem(this.THEME_STORAGE_KEY);
    } catch (error) {}
  }

  /**
   * 监听系统主题偏好变化
   * @returns 清理函数
   */
  listenToSystemPreference(): () => void {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      const systemTheme: 'light' | 'dark' = e.matches ? 'dark' : 'light';
      const savedTheme = this.getStoredTheme();

      // 只有在用户没有明确设置主题时才跟随系统偏好
      if (!savedTheme) {
        this.setTheme(systemTheme, false);
      }
    };

    // 添加事件监听器
    mediaQuery.addEventListener('change', handleChange);

    // 返回清理函数
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }

  /**
   * 获取主题相关的工具方法
   */
  getThemeUtils() {
    return {
      // 获取对比色
      getContrastColor: (backgroundColor: string): 'light' | 'dark' => {
        // 简单的亮度计算
        const hex = backgroundColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        return brightness > 128 ? 'dark' : 'light';
      },

      // 混合颜色
      mixColors: (color1: string, color2: string, ratio: number): string => {
        const hex1 = color1.replace('#', '');
        const hex2 = color2.replace('#', '');

        const r1 = parseInt(hex1.substr(0, 2), 16);
        const g1 = parseInt(hex1.substr(2, 2), 16);
        const b1 = parseInt(hex1.substr(4, 2), 16);

        const r2 = parseInt(hex2.substr(0, 2), 16);
        const g2 = parseInt(hex2.substr(2, 2), 16);
        const b2 = parseInt(hex2.substr(4, 2), 16);

        const r = Math.round(r1 * (1 - ratio) + r2 * ratio);
        const g = Math.round(g1 * (1 - ratio) + g2 * ratio);
        const b = Math.round(b1 * (1 - ratio) + b2 * ratio);

        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
      },
    };
  }
}
