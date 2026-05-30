/**
 * Design Tokens - Fonts
 *
 * 字体设计变量系统，定义项目中的字体族、字号、行高和字重规范
 */

/** 字体族 */
export const fontFamilies = {
  /** 默认无衬线字体 */
  sans: "'Helvetica Neue', Helvetica, Arial, sans-serif",
  /** 衬线字体 */
  serif: "Georgia, 'Times New Roman', Times, serif",
  /** 等宽字体 */
  mono: "'Courier New', Courier, monospace",
  /** 系统字体堆栈 */
  system:
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif",
} as const;

/** 字号层级 - 基于 16px 根字体大小 */
export const fontSizes = {
  /** 超大标题 */
  h1: '2.5rem', // 40px
  /** 大标题 */
  h2: '2rem', // 32px
  /** 中标题 */
  h3: '1.75rem', // 28px
  /** 小标题 */
  h4: '1.5rem', // 24px
  /** 副标题 */
  h5: '1.25rem', // 20px
  /** 最小标题 */
  h6: '1.125rem', // 18px
  /** 大正文字体 */
  bodyLarge: '1rem', // 16px
  /** 中等正文字体 */
  bodyMedium: '0.875rem', // 14px
  /** 小正文字体 */
  bodySmall: '0.75rem', // 12px
  /** 标注字体 */
  caption: '0.625rem', // 10px
} as const;

/** 行高比例 */
export const lineHeights = {
  /** 紧凑行高 */
  tight: 1.2,
  /** 稍紧行高 */
  snug: 1.375,
  /** 标准行高 */
  normal: 1.5,
  /** 宽松行高 */
  relaxed: 1.625,
  /** 超宽松行高 */
  loose: 2,
} as const;

/** 字重 */
export const fontWeights = {
  /** 细体 */
  thin: 100,
  /** 超细体 */
  extraLight: 200,
  /** 细体 */
  light: 300,
  /** 常规 */
  regular: 400,
  /** 中等 */
  medium: 500,
  /** 半粗体 */
  semiBold: 600,
  /** 粗体 */
  bold: 700,
  /** 超粗体 */
  extraBold: 800,
  /** 黑体 */
  black: 900,
} as const;

/** 字体组合样式 */
export const typography = {
  /** 页面标题 */
  pageTitle: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.h1,
    fontWeight: fontWeights.bold,
    lineHeight: lineHeights.tight,
  },
  /** 卡片标题 */
  cardTitle: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.h4,
    fontWeight: fontWeights.semiBold,
    lineHeight: lineHeights.snug,
  },
  /** 正文大号 */
  bodyLarge: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.bodyLarge,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.normal,
  },
  /** 正文中号 */
  bodyMedium: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.bodyMedium,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.normal,
  },
  /** 正文小号 */
  bodySmall: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.bodySmall,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.relaxed,
  },
  /** 按钮文本 */
  button: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.bodyMedium,
    fontWeight: fontWeights.medium,
    lineHeight: lineHeights.normal,
  },
  /** 输入框占位符 */
  inputPlaceholder: {
    fontFamily: fontFamilies.system,
    fontSize: fontSizes.bodyMedium,
    fontWeight: fontWeights.regular,
    lineHeight: lineHeights.normal,
  },
} as const;

/** 完整字体系统 */
export const fonts = {
  families: fontFamilies,
  sizes: fontSizes,
  heights: lineHeights,
  weights: fontWeights,
  typography,
} as const;

/** 类型定义 */
export type FontFamily = typeof fontFamilies;
export type FontSize = typeof fontSizes;
export type LineHeight = typeof lineHeights;
export type FontWeight = typeof fontWeights;
export type Typography = typeof typography;
export type FontToken = typeof fonts;

export default fonts;
