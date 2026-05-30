/**
 * Design Tokens Index
 *
 * Design Token 系统入口文件
 * 导出所有设计变量供项目使用
 */

export {
  default as borderRadii,
  borderRadius,
  componentBorderRadius,
  directionalBorderRadius,
  responsiveBorderRadius,
} from './border-radius';
export {
  backgroundColors,
  default as colors,
  neutralColors,
  primaryColors,
  secondaryColors,
  semanticColors,
  statusColors,
  textColors,
} from './colors';
export {
  fontFamilies,
  default as fonts,
  fontSizes,
  fontWeights,
  lineHeights,
  typography,
} from './fonts';
export {
  baseShadows,
  componentShadows,
  directionalShadows,
  responsiveShadows,
  default as shadows,
  stateShadows,
} from './shadows';
export {
  baseSpacing,
  directionalSpacing,
  extraLargeSpacing,
  largeSpacing,
  responsiveSpacing,
  default as spacing,
  tinySpacing,
} from './spacing';

// 重新导出所有类型
export type {
  BorderRadius,
  BorderRadiusToken,
  ComponentBorderRadius,
  DirectionalBorderRadius,
  ResponsiveBorderRadius,
} from './border-radius';
export type { ColorToken, NeutralColor, PrimaryColor, StatusColor } from './colors';
export type { FontFamily, FontSize, FontToken, FontWeight, LineHeight, Typography } from './fonts';
export type {
  BaseShadow,
  ComponentShadow,
  DirectionalShadow,
  ResponsiveShadow,
  ShadowToken,
  StateShadow,
} from './shadows';
export type {
  BaseSpacing,
  DirectionalSpacing,
  ExtraLargeSpacing,
  LargeSpacing,
  ResponsiveSpacing,
  SpacingToken,
  TinySpacing,
} from './spacing';

/**
 * 完整 Design Token 系统
 *
 * 包含所有设计变量的统一导出
 */
export const designTokens = {
  colors: () => import('./colors').then((m) => m.default),
  fonts: () => import('./fonts').then((m) => m.default),
  spacing: () => import('./spacing').then((m) => m.default),
  borderRadii: () => import('./border-radius').then((m) => m.default),
  shadows: () => import('./shadows').then((m) => m.default),
} as const;

export default designTokens;
