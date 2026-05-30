/**
 * i18n辅助函数
 *
 * 提供通用的翻译辅助函数
 */

import { I18nTranslations } from '../../app/core/services/i18n.service';

/**
 * 安全获取嵌套对象的值
 */
export function getNestedValue(obj: any, keyPath: string): any {
  if (!obj) return undefined;

  const keys = keyPath.split('.');
  let current = obj;

  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return undefined;
    }
  }

  return current;
}

/**
 * 检查翻译键是否存在
 */
export function hasTranslation(translations: I18nTranslations, key: string): boolean {
  return getNestedValue(translations, key) !== undefined;
}

/**
 * 获取翻译占位符替换后的文本
 */
export function formatTranslation(
  translation: string,
  params: { [key: string]: string | number } = {}
): string {
  let result = translation;

  for (const [key, value] of Object.entries(params)) {
    const placeholder = `{{${key}}}`;
    result = result.replace(new RegExp(placeholder, 'g'), String(value));
  }

  return result;
}

/**
 * 创建翻译管道函数
 */
export function createTranslationPipeline(
  translations: I18nTranslations
): (key: string, params?: { [key: string]: string | number }) => string {
  return (key: string, params?: { [key: string]: string | number }): string => {
    const translation = getNestedValue(translations, key);

    if (typeof translation === 'string') {
      return formatTranslation(translation, params);
    }

    return key;
  };
}

/**
 * 复数化处理
 */
export function pluralize(
  count: number,
  forms: {
    zero?: string;
    one: string;
    few?: string;
    many?: string;
    other: string;
  },
  lang: string
): string {
  // 简化版本：支持中英文
  if (lang.startsWith('zh')) {
    // 中文：通常不使用复数形式
    if (count === 1) {
      return forms.one;
    }
    return forms.other;
  } else {
    // 英文
    if (count === 1) {
      return forms.one;
    }
    return forms.other;
  }
}

/**
 * 日期格式化辅助函数
 */
export function formatDateLocalized(
  date: Date,
  lang: string,
  options: Intl.DateTimeFormatOptions = {}
): string {
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  };

  return date.toLocaleDateString(lang, defaultOptions);
}

/**
 * 数字格式化辅助函数
 */
export function formatNumberLocalized(
  number: number,
  lang: string,
  options: Intl.NumberFormatOptions = {}
): string {
  return number.toLocaleString(lang, options);
}
