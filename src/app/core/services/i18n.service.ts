import { HttpClient } from '@angular/common/http';
import { ApplicationRef, Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, distinctUntilChanged, map } from 'rxjs/operators';

export interface I18nTranslations {
  [key: string]: unknown;
}

/**
 * 当前语言与该语言下的翻译包合并的快照，组件可以订阅它们实现自动变更检测。
 */
export interface I18nSnapshot {
  lang: 'zh-CN' | 'en-US';
  translations: I18nTranslations;
}

@Injectable({
  providedIn: 'root',
})
export class I18nService {
  private currentLang = new BehaviorSubject<'zh-CN' | 'en-US'>('zh-CN');
  // 【P1 修复 #13】原版使用普通对象 + HTTP subscribe 静默赋值，导致首次访问页面时
  //   translations 仍为空 → i18n.translate() 返回原始 key 字符串 → Angular 未收到变更
  //   检测 → 翻译永远不生效（需手动刷新页面才被错误地修复）。
  //   修复：将 translations 包装为 BehaviorSubject，HTTP 加载完成后 emit。
  //   translate() 保持同步 API（取值来自 snapshot），同时提供 translationsReady$ observable
  //   让组件可以用 async pipe 或 markForCheck() 实现自动刷新。
  private translations = new BehaviorSubject<I18nTranslations>({});

  currentLang$ = this.currentLang.asObservable();
  /** 当前语言 + 翻译包快照， HTTP 加载完成后会 emit。 */
  readonly snapshots$: Observable<I18nSnapshot> = this.translations.pipe(
    map((t) => ({ lang: this.currentLang.value, translations: t })),
    distinctUntilChanged((a, b) => a.lang === b.lang && a.translations === b.translations)
  );
  supportedLangs = ['zh-CN', 'en-US'];

  constructor(
    private http: HttpClient,
    private appRef: ApplicationRef
  ) {
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
      .subscribe((loaded) => {
        // 【P1 修复 #13】通过 BehaviorSubject emit，触发快照订阅链更新。
        //   同时调一次 ApplicationRef.tick()，让所有组件（包括未订阅 snapshots$
        //   的组件，例如 UserNav、UserFooter、LoginComponent）重新走变更检测，
        //   重新调用 i18n.translate() 取到新翻译。
        if (this.translations.value !== loaded) {
          this.translations.next(loaded);
          // 使用 setTimeout 推迟到下一个宏任务，避免在 HTTP subscribe 回调中
          // 触发额外的变更检测与正在运行的检测冲突。
          setTimeout(() => {
            try {
              this.appRef.tick();
            } catch {
              // 静默处理：tick 在初始化阶段可能被调度器放弃。
            }
          }, 0);
        }
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
    const translations = this.translations.value as Record<string, unknown>;

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
        // 【P1 修复 #13】首次渲染时 translations 仍为空，避免堆版出现多个重复 warn。
        if (translations && Object.keys(translations).length > 0) {
          console.warn(`Translation key not found: ${key}`);
        }
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
    return this.translations.value as I18nTranslations;
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
