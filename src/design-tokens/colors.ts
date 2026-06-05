/**
 * Design Tokens - Colors
 *
 * 颜色设计变量系统，为整个项目提供一致的颜色规范
 * 所有颜色值均使用 HEX 格式，关键颜色提供深浅变体
 */

/** 主要品牌色 */
export const primaryColors = {
  /** 主品牌色，用于按钮、链接和重要操作 - MatuX 藏青色 */
  primary: '#0f172a',
  /** 主色浅色变体，用于悬停状态 */
  primaryLight: '#1e293b',
  /** 主色深色变体，用于激活状态 */
  primaryDark: '#020617',
} as const;

/** 辅助品牌色 - MatuX 科技蓝 */
export const secondaryColors = {
  /** 辅助品牌色，用于次要按钮和装饰元素 */
  secondary: '#3b82f6',
  /** 辅助色浅色变体 */
  secondaryLight: '#60a5fa',
  /** 辅助色深色变体 */
  secondaryDark: '#2563eb',
} as const;

/** 状态颜色 - MatuX 功能色 */
export const statusColors = {
  /** 成功状态色 */
  success: '#10b981',
  /** 警告状态色 */
  warning: '#f59e0b',
  /** 错误状态色 */
  error: '#ef4444',
  /** 信息状态色 */
  info: '#3b82f6',
} as const;

/** 中性灰度色系 - MatuX Slate 系 */
export const neutralColors = {
  black: '#000000',
  white: '#FFFFFF',
  gray50: '#f8fafc',
  gray100: '#f1f5f9',
  gray200: '#e2e8f0',
  gray300: '#cbd5e1',
  gray400: '#94a3b8',
  gray500: '#64748b',
  gray600: '#475569',
  gray700: '#334155',
  gray800: '#1e293b',
  gray900: '#0f172a',
} as const;

/** 文本颜色 */
export const textColors = {
  textPrimary: '#0f172a',
  textSecondary: '#475569',
  textDisabled: '#94a3b8',
  textWhite: '#FFFFFF',
} as const;

/** 背景颜色 */
export const backgroundColors = {
  background: '#FFFFFF',
  surface: '#FFFFFF',
  divider: '#e2e8f0',
  hover: '#f1f5f9',
  selected: '#eff6ff',
} as const;

/** 语义化颜色别名 */
export const semanticColors = {
  /** 品牌主色 */
  brand: primaryColors.primary,
  /** 链接色 */
  link: primaryColors.primary,
  /** 链接悬停色 */
  linkHover: primaryColors.primaryDark,
  /** 边框色 */
  border: neutralColors.gray300,
  /** 输入框焦点色 */
  focus: primaryColors.primary,
  /** 占位符文本色 */
  placeholder: neutralColors.gray500,
} as const;

/** 完整颜色系统 */
export const colors = {
  ...primaryColors,
  ...secondaryColors,
  ...statusColors,
  ...neutralColors,
  ...textColors,
  ...backgroundColors,
  ...semanticColors,
} as const;

/** 颜色类型定义 */
export type ColorToken = typeof colors;
export type PrimaryColor = typeof primaryColors;
export type StatusColor = typeof statusColors;
export type NeutralColor = typeof neutralColors;

export default colors;
