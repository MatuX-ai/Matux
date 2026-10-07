/**
 * K12 STEM 主题服务
 * 管理主题切换，支持按学科/场景动态切换主题色
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type SubjectType = 'science' | 'technology' | 'engineering' | 'math' | 'arts';
export type ThemeMode = 'light' | 'dark' | 'auto';

export interface StemThemeConfig {
  primary: string;
  primaryLight: string;
  primaryDark: string;
  secondary: string;
  gradient: string;
}

// 学科主题配置
const SUBJECT_THEMES: Record<SubjectType, StemThemeConfig> = {
  science: {
    primary: '#059669', // 探索绿
    primaryLight: '#10b981',
    primaryDark: '#047857',
    secondary: '#0ea5e9',
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
  },
  technology: {
    primary: '#2563eb', // 科技蓝
    primaryLight: '#3b82f6',
    primaryDark: '#1d4ed8',
    secondary: '#0ea5e9',
    gradient: 'linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%)',
  },
  engineering: {
    primary: '#f59e0b', // 琥珀橙
    primaryLight: '#fbbf24',
    primaryDark: '#d97706',
    secondary: '#f97316',
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
  },
  math: {
    primary: '#8b5cf6', // 紫罗兰
    primaryLight: '#a78bfa',
    primaryDark: '#7c3aed',
    secondary: '#a855f7',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
  },
  arts: {
    primary: '#ec4899', // 粉红
    primaryLight: '#f472b6',
    primaryDark: '#db2777',
    secondary: '#f9a8d4',
    gradient: 'linear-gradient(135deg, #ec4899 0%, #f472b6 100%)',
  },
};

// 学习状态颜色
const LEARNING_STATE_COLORS = {
  inProgress: '#059669',
  completed: '#10b981',
  locked: '#94a3b8',
  mastered: '#f59e0b',
  challenge: '#ef4444',
};

@Injectable({
  providedIn: 'root',
})
export class StemThemeService {
  private currentSubject$ = new BehaviorSubject<SubjectType>('science');
  private currentMode$ = new BehaviorSubject<ThemeMode>('light');
  private isInitialized = false;

  // 获取当前主题配置
  getCurrentTheme(): StemThemeConfig {
    return SUBJECT_THEMES[this.currentSubject$.value];
  }

  // 获取当前学科
  getCurrentSubject(): SubjectType {
    return this.currentSubject$.value;
  }

  // 获取当前主题 Observable
  getSubject$(): Observable<SubjectType> {
    return this.currentSubject$.asObservable();
  }

  // 获取主题模式 Observable
  getMode$(): Observable<ThemeMode> {
    return this.currentMode$.asObservable();
  }

  // 切换学科主题
  setSubject(subject: SubjectType): void {
    this.currentSubject$.next(subject);
    this.applyThemeToDOM(subject);
  }

  // 切换主题模式 (light/dark/auto)
  setMode(mode: ThemeMode): void {
    this.currentMode$.next(mode);
    this.applyModeToDOM(mode);
  }

  // 根据学科获取主题配置
  getSubjectTheme(subject: SubjectType): StemThemeConfig {
    return SUBJECT_THEMES[subject] || SUBJECT_THEMES['science'];
  }

  // 获取学习状态颜色
  getLearningStateColor(state: keyof typeof LEARNING_STATE_COLORS): string {
    return LEARNING_STATE_COLORS[state];
  }

  // 初始化主题
  initialize(): void {
    if (this.isInitialized) return;
    this.isInitialized = true;

    // 应用初始主题
    this.applyThemeToDOM(this.currentSubject$.value);
    this.applyModeToDOM(this.currentMode$.value);
  }

  // 应用主题到 DOM
  private applyThemeToDOM(subject: SubjectType): void {
    const theme = SUBJECT_THEMES[subject];
    const root = document.documentElement;

    root.style.setProperty('--stem-active-primary', theme.primary);
    root.style.setProperty('--stem-active-primary-light', theme.primaryLight);
    root.style.setProperty('--stem-active-primary-dark', theme.primaryDark);
    root.style.setProperty('--stem-active-secondary', theme.secondary);
    root.style.setProperty('--stem-active-gradient', theme.gradient);
  }

  // 应用模式到 DOM
  private applyModeToDOM(mode: ThemeMode): void {
    const root = document.documentElement;

    if (mode === 'dark') {
      root.classList.add('stem-theme-dark');
      root.classList.remove('stem-theme-light');
    } else if (mode === 'light') {
      root.classList.remove('stem-theme-dark');
      root.classList.add('stem-theme-light');
    } else {
      // auto: 跟随系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('stem-theme-dark', prefersDark);
      root.classList.toggle('stem-theme-light', !prefersDark);
    }
  }

  // 获取 CSS 变量名称
  getCSSVarName(variable: string): string {
    return `var(--stem-${variable})`;
  }

  // 获取所有学科主题
  getAllSubjectThemes(): Record<SubjectType, StemThemeConfig> {
    return { ...SUBJECT_THEMES };
  }

  // 获取学科图标
  getSubjectIcon(subject: SubjectType): string {
    const icons: Record<SubjectType, string> = {
      science: '🔬',
      technology: '💻',
      engineering: '⚙️',
      math: '📐',
      arts: '🎨',
    };
    return icons[subject] || '📚';
  }

  // 获取学科名称
  getSubjectName(subject: SubjectType): string {
    const names: Record<SubjectType, string> = {
      science: '科学',
      technology: '技术',
      engineering: '工程',
      math: '数学',
      arts: '艺术',
    };
    return names[subject] || subject;
  }
}
