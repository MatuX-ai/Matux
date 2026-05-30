/**
 * Design Tokens - Colors
 *
 * 颜色设计变量系统，为整个项目提供一致的颜色规范
 * 所有颜色值均使用 HEX 格式，关键颜色提供深浅变体
 */

/** 主要品牌色 */
export const primaryColors = {
  /** 主品牌色，用于按钮、链接和重要操作 */
  primary: '#2196F3',
  /** 主色浅色变体，用于悬停状态 */
  primaryLight: '#64B5F6',
  /** 主色深色变体，用于激活状态 */
  primaryDark: '#1976D2',
} as const;

/** 辅助品牌色 */
export const secondaryColors = {
  /** 辅助品牌色，用于次要按钮和装饰元素 */
  secondary: '#9C27B0',
  /** 辅助色浅色变体 */
  secondaryLight: '#BA68C8',
  /** 辅助色深色变体 */
  secondaryDark: '#7B1FA2',
} as const;

/** 状态颜色 */
export const statusColors = {
  /** 成功状态色，用于成功提示和确认操作 */
  success: '#4CAF50',
  /** 警告状态色，用于警告提示 */
  warning: '#FF9800',
  /** 错误状态色，用于错误提示和危险操作 */
  error: '#F44336',
  /** 信息状态色，用于普通信息提示 */
  info: '#2196F3',
} as const;

/** 中性灰度色系 */
export const neutralColors = {
  /** 纯黑色 */
  black: '#000000',
  /** 纯白色 */
  white: '#FFFFFF',
  /** 灰色 50 - 最浅灰色 */
  gray50: '#FAFAFA',
  /** 灰色 100 */
  gray100: '#F5F5F5',
  /** 灰色 200 */
  gray200: '#EEEEEE',
  /** 灰色 300 */
  gray300: '#E0E0E0',
  /** 灰色 400 */
  gray400: '#BDBDBD',
  /** 灰色 500 */
  gray500: '#9E9E9E',
  /** 灰色 600 */
  gray600: '#757575',
  /** 灰色 700 */
  gray700: '#616161',
  /** 灰色 800 */
  gray800: '#424242',
  /** 灰色 900 - 最深灰色 */
  gray900: '#212121',
} as const;

/** 文本颜色 */
export const textColors = {
  /** 主要文本色，用于标题和重要内容 */
  textPrimary: '#212121',
  /** 次要文本色，用于普通正文 */
  textSecondary: '#757575',
  /** 禁用文本色，用于禁用状态 */
  textDisabled: '#9E9E9E',
  /** 白色文本，用于深色背景 */
  textWhite: '#FFFFFF',
} as const;

/** 背景颜色 */
export const backgroundColors = {
  /** 页面背景色 */
  background: '#FFFFFF',
  /** 组件表面色，用于卡片、对话框等 */
  surface: '#FFFFFF',
  /** 分割线颜色 */
  divider: '#E0E0E0',
  /** 悬停背景色 */
  hover: '#F5F5F5',
  /** 选中背景色 */
  selected: '#E3F2FD',
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
