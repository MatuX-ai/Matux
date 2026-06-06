import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface I18nTranslations {
  [key: string]: unknown;
}

@Injectable({
  providedIn: 'root',
})
export class I18nService {
  private currentLang = new BehaviorSubject<'zh-CN' | 'en-US'>('zh-CN');
  private translations: I18nTranslations = {};

  currentLang$ = this.currentLang.asObservable();
  supportedLangs = ['zh-CN', 'en-US'];

  constructor(private http: HttpClient) {
    this.loadSavedLanguage();
  }

  /**
   * 加载保存的语言设置
   */
  private loadSavedLanguage(): void {
    const savedLang = localStorage.getItem('app-language');
    if (savedLang && this.supportedLangs.includes(savedLang)) {
      this.currentLang.next(savedLang as 'zh-CN' | 'en-US');
      this.loadTranslations(savedLang as 'zh-CN' | 'en-US');
    } else {
      // 检测浏览器语言
      const browserLang = navigator.language;
      const lang = browserLang.startsWith('zh') ? 'zh-CN' : 'en-US';
      this.currentLang.next(lang);
      this.loadTranslations(lang);
    }
  }

  /**
   * 从JSON文件加载翻译
   */
  private loadTranslations(lang: 'zh-CN' | 'en-US'): void {
    const filePath = `/assets/i18n/${lang}.json`;
    this.http
      .get<I18nTranslations>(filePath)
      .pipe(
        catchError((error) => {
          console.error(`Failed to load translations for ${lang}:`, error);
          return of({} as I18nTranslations);
        })
      )
      .subscribe((translations) => {
        this.translations[lang] = translations;
      });
  }

  /**
   * 获取当前语言
   */
  getCurrentLang(): 'zh-CN' | 'en-US' {
    return this.currentLang.value;
  }

  /**
   * 切换语言
   */
  setLanguage(lang: 'zh-CN' | 'en-US'): void {
    if (this.supportedLangs.includes(lang)) {
      this.currentLang.next(lang);
      localStorage.setItem('app-language', lang);

      // 更新页面语言属性
      document.documentElement.lang = lang;

      // 重新加载页面以应用新语言
      setTimeout(() => {
        window.location.reload();
      }, 100);
    }
  }

  /**
   * 切换到另一种语言
   */
  toggleLanguage(): void {
    const currentLang = this.getCurrentLang();
    const newLang = currentLang === 'zh-CN' ? 'en-US' : 'zh-CN';
    this.setLanguage(newLang);
  }

  /**
   * 获取翻译文本
   */
  translate(key: string): string {
    const lang = this.currentLang.value;
    const translations = this.translations[lang] as Record<string, unknown> | undefined;

    const keys = key.split('.');
    let value: unknown = translations;

    for (const k of keys) {
      if (
        value &&
        typeof value === 'object' &&
        (value as Record<string, unknown>)[k] !== undefined
      ) {
        value = (value as Record<string, unknown>)[k];
      } else {
        console.warn(`Translation key not found: ${key}`);
        return key;
      }
    }

    if (typeof value === 'string') {
      return value;
    }

    return key;
  }

  /**
   * 获取所有翻译
   */
  getTranslations(): I18nTranslations {
    return this.translations[this.currentLang.value] as I18nTranslations;
  }

  /**
   * 格式化数字
   */
  formatNumber(num: number): string {
    const lang = this.currentLang.value;
    return num.toLocaleString(lang);
  }

  /**
   * 格式化日期
   */
  formatDate(date: Date): string {
    const lang = this.currentLang.value;
    return date.toLocaleDateString(lang);
  }

  /**
   * 格式化货币
   */
  formatCurrency(amount: number, currency: string = 'CNY'): string {
    const lang = this.currentLang.value;
    return new Intl.NumberFormat(lang, {
      style: 'currency',
      currency,
    }).format(amount);
  }
}
