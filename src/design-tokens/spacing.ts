/**
 * Design Tokens - Spacing
 *
 * 间距设计变量系统，基于 8px 网格系统的间距规范
 * 确保界面元素间保持一致的空间关系
 */

/** 微小间距 - 用于精细调整 */
export const tinySpacing = {
  /** 2px 间距 */
  xxs: '0.125rem', // 2px
  /** 4px 间距 */
  xs: '0.25rem', // 4px
} as const;

/** 基础间距 - 基于 8px 网格 */
export const baseSpacing = {
  /** 8px 基础单位 */
  sm: '0.5rem', // 8px
  /** 12px */
  md: '0.75rem', // 12px
  /** 16px */
  lg: '1rem', // 16px
  /** 24px */
  xl: '1.5rem', // 24px
  /** 32px */
  xxl: '2rem', // 32px
} as const;

/** 大间距 - 用于组件间距离 */
export const largeSpacing = {
  /** 40px */
  xxxl: '2.5rem', // 40px
  /** 48px */
  xxxxl: '3rem', // 48px
  /** 56px */
  xxxxxl: '3.5rem', // 56px
  /** 64px */
  xxxxxxl: '4rem', // 64px
} as const;

/** 特大间距 - 用于页面布局 */
export const extraLargeSpacing = {
  /** 80px */
  huge: '5rem', // 80px
  /** 96px */
  giant: '6rem', // 96px
  /** 128px */
  massive: '8rem', // 128px
} as const;

/** 方向性间距 */
export const directionalSpacing = {
  /** 内边距 */
  padding: baseSpacing,
  /** 外边距 */
  margin: baseSpacing,
  /** 间隔 */
  gap: baseSpacing,
} as const;

/** 响应式间距 */
export const responsiveSpacing = {
  /** 移动端紧凑间距 */
  mobile: {
    sm: '0.25rem', // 4px
    md: '0.5rem', // 8px
    lg: '0.75rem', // 12px
    xl: '1rem', // 16px
  },
  /** 平板端适中间距 */
  tablet: {
    sm: '0.5rem', // 8px
    md: '0.75rem', // 12px
    lg: '1rem', // 16px
    xl: '1.5rem', // 24px
  },
  /** 桌面端宽松间距 */
  desktop: {
    sm: '0.75rem', // 12px
    md: '1rem', // 16px
    lg: '1.5rem', // 24px
    xl: '2rem', // 32px
  },
} as const;

/** 完整间距系统 */
export const spacing = {
  ...tinySpacing,
  ...baseSpacing,
  ...largeSpacing,
  ...extraLargeSpacing,
  directional: directionalSpacing,
  responsive: responsiveSpacing,
} as const;

/** 间距工具函数 */
export const spacingUtils = {
  /** 将倍数转换为 rem 单位 */
  scale: (multiplier: number): string => `${multiplier * 0.5}rem`,

  /** 获取水平间距 */
  horizontal: (size: keyof typeof baseSpacing): string => baseSpacing[size],

  /** 获取垂直间距 */
  vertical: (size: keyof typeof baseSpacing): string => baseSpacing[size],

  /** 获取对称间距 */
  symmetric: (
    horizontal: keyof typeof baseSpacing,
    vertical: keyof typeof baseSpacing
  ): {
    paddingHorizontal: string;
    paddingVertical: string;
  } => ({
    paddingHorizontal: baseSpacing[horizontal],
    paddingVertical: baseSpacing[vertical],
  }),
} as const;

/** 类型定义 */
export type TinySpacing = typeof tinySpacing;
export type BaseSpacing = typeof baseSpacing;
export type LargeSpacing = typeof largeSpacing;
export type ExtraLargeSpacing = typeof extraLargeSpacing;
export type DirectionalSpacing = typeof directionalSpacing;
export type ResponsiveSpacing = typeof responsiveSpacing;
export type SpacingToken = typeof spacing;

export default spacing;
