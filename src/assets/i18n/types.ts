/**
 * i18n类型定义
 *
 * 为翻译文件提供TypeScript类型支持
 */

export interface CommonTranslations {
  loading: string;
  error: string;
  success: string;
  cancel: string;
  confirm: string;
  save: string;
  delete: string;
  edit: string;
  search: string;
  filter: string;
  refresh: string;
}

export interface NavigationTranslations {
  home: string;
  features: string;
  pricing: string;
  about: string;
  contact: string;
  admin: string;
  dashboard: string;
  aiEdu: string;
  arLab: string;
}

export interface PricingPlanTranslations {
  name: string;
  price: string;
  features: string[];
}

export interface PricingTranslations {
  title: string;
  subtitle: string;
  free: PricingPlanTranslations;
  pro: PricingPlanTranslations;
  enterprise: PricingPlanTranslations;
}

export interface ContactTranslations {
  title: string;
  subtitle: string;
  name: string;
  email: string;
  message: string;
  send: string;
}

export interface AboutTranslations {
  title: string;
  subtitle: string;
  mission: string;
  vision: string;
}

export interface PWATranslations {
  installPrompt: string;
  notNow: string;
  installing: string;
  installed: string;
  offline: string;
  reconnected: string;
  updateAvailable: string;
  update: string;
}

export interface HomeTranslations {
  title: string;
  subtitle: string;
  heroTitle: string;
  heroSubtitle: string;
  getStarted: string;
  learnMore: string;
}

/**
 * 完整的翻译接口定义
 */
export interface TranslationFile {
  common: CommonTranslations;
  nav: NavigationTranslations;
  home: HomeTranslations;
  pricing: PricingTranslations;
  contact: ContactTranslations;
  about: AboutTranslations;
  pwa: PWATranslations;
}

/**
 * 翻译键类型，用于类型安全的翻译访问
 */
export type TranslationKeys =
  | 'common.loading'
  | 'common.error'
  | 'common.success'
  | 'common.cancel'
  | 'common.confirm'
  | 'common.save'
  | 'common.delete'
  | 'common.edit'
  | 'common.search'
  | 'common.filter'
  | 'common.refresh'
  | 'nav.home'
  | 'nav.features'
  | 'nav.pricing'
  | 'nav.about'
  | 'nav.contact'
  | 'nav.admin'
  | 'nav.dashboard'
  | 'nav.aiEdu'
  | 'nav.arLab'
  | 'home.title'
  | 'home.subtitle'
  | 'home.heroTitle'
  | 'home.heroSubtitle'
  | 'home.getStarted'
  | 'home.learnMore'
  | 'pricing.title'
  | 'pricing.subtitle'
  | 'pricing.free.name'
  | 'pricing.free.price'
  | 'pricing.free.features'
  | 'pricing.pro.name'
  | 'pricing.pro.price'
  | 'pricing.pro.features'
  | 'pricing.enterprise.name'
  | 'pricing.enterprise.price'
  | 'pricing.enterprise.features'
  | 'contact.title'
  | 'contact.subtitle'
  | 'contact.name'
  | 'contact.email'
  | 'contact.message'
  | 'contact.send'
  | 'about.title'
  | 'about.subtitle'
  | 'about.mission'
  | 'about.vision'
  | 'pwa.installPrompt'
  | 'pwa.notNow'
  | 'pwa.installing'
  | 'pwa.installed'
  | 'pwa.offline'
  | 'pwa.reconnected'
  | 'pwa.updateAvailable'
  | 'pwa.update';

/**
 * 语言代码类型
 */
export type LanguageCode = 'zh-CN' | 'en-US';

/**
 * 翻译加载器接口
 */
export interface TranslationLoader {
  load(lang: LanguageCode): Promise<TranslationFile>;
}

/**
 * 翻译上下文接口
 */
export interface TranslationContext {
  [key: string]: string | number;
}

/**
 * 翻译选项接口
 */
export interface TranslationOptions {
  defaultValue?: string;
  context?: TranslationContext;
}
