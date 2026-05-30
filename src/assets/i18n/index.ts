/**
 * i18n翻译文件索引
 *
 * 此文件定义了所有可用的翻译语言和它们的元数据
 */

export interface LanguageMetadata {
  code: string;
  name: string;
  nativeName: string;
  direction: 'ltr' | 'rtl';
  flag: string;
  locale: string;
}

export const SUPPORTED_LANGUAGES: LanguageMetadata[] = [
  {
    code: 'zh-CN',
    name: 'Chinese',
    nativeName: '简体中文',
    direction: 'ltr',
    flag: '🇨🇳',
    locale: 'zh-CN',
  },
  {
    code: 'en-US',
    name: 'English',
    nativeName: 'English',
    direction: 'ltr',
    flag: '🇺🇸',
    locale: 'en-US',
  },
];

export const DEFAULT_LANGUAGE = 'zh-CN';

/**
 * 获取语言元数据
 */
export function getLanguageMetadata(langCode: string): LanguageMetadata | undefined {
  return SUPPORTED_LANGUAGES.find((lang) => lang.code === langCode);
}

/**
 * 检测浏览器首选语言
 */
export function detectBrowserLanguage(): string {
  const browserLang = navigator.language;
  const supportedCodes = SUPPORTED_LANGUAGES.map((lang) => lang.code);

  // 检查完整语言代码
  if (supportedCodes.includes(browserLang)) {
    return browserLang;
  }

  // 检查语言前缀
  const langPrefix = browserLang.split('-')[0];
  const matchingLang = SUPPORTED_LANGUAGES.find((lang) => lang.code.startsWith(langPrefix));

  return matchingLang ? matchingLang.code : DEFAULT_LANGUAGE;
}
