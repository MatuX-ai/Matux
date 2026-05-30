/**
 * Design Tokens 使用示例
 *
 * 展示如何在项目中使用 Design Token 系统
 */

import {
  baseShadows,
  baseSpacing,
  borderRadii,
  borderRadius,
  colors,
  fonts,
  fontSizes,
  primaryColors,
  shadows,
  spacing,
} from './index';

// 示例 1: 基础颜色使用
const buttonStyles = {
  backgroundColor: primaryColors.primary, // '#2196F3'
  color: colors.textWhite,
  borderColor: colors.border,
  hoverBackgroundColor: primaryColors.primaryDark, // '#1976D2'
};

// 示例 2: 字体系统使用
const typographyStyles = {
  heading: {
    fontFamily: fonts.families.system,
    fontSize: fontSizes.h2,
    fontWeight: fonts.weights.bold,
    lineHeight: fonts.heights.tight,
  },
  body: {
    fontFamily: fonts.families.system,
    fontSize: fontSizes.bodyMedium,
    fontWeight: fonts.weights.regular,
    lineHeight: fonts.heights.normal,
  },
};

// 示例 3: 间距系统使用
const layoutStyles = {
  container: {
    padding: spacing.lg, // '1rem' (16px)
    margin: spacing.xl, // '1.5rem' (24px)
    gap: spacing.md, // '0.75rem' (12px)
  },
  card: {
    padding: `${spacing.md} ${spacing.lg}`, // '0.75rem 1rem'
  },
};

// 示例 4: 圆角系统使用
const shapeStyles = {
  button: {
    borderRadius: borderRadius.sm, // '0.25rem' (4px)
  },
  card: {
    borderRadius: borderRadius.md, // '0.5rem' (8px)
  },
  avatar: {
    borderRadius: borderRadius.full, // '9999px'
  },
};

// 示例 5: 阴影系统使用
const effectStyles = {
  card: {
    boxShadow: baseShadows.sm, // '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
  },
  modal: {
    boxShadow: baseShadows.xl, // '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
  },
};

// 示例 6: 响应式设计
const responsiveStyles = {
  mobile: {
    padding: spacing.responsive.mobile.md,
    fontSize: fontSizes.bodyMedium,
  },
  desktop: {
    padding: spacing.responsive.desktop.lg,
    fontSize: fontSizes.bodyLarge,
  },
};

// 示例 7: 工具函数使用
const utilsExample = {
  // 创建自定义阴影
  customShadow: shadows.utils.create('0px', '4px', '8px', '0px', 'rgba(0, 0, 0, 0.1)'),

  // 组合多个阴影
  multipleShadows: shadows.utils.multiple(baseShadows.sm, '0 0 0 2px rgba(33, 150, 243, 0.2)'),

  // 应用圆角组合
  asymmetricBorderRadius: borderRadii.utils.combine('sm', 'md', 'lg', 'xl'),
};

// 示例 8: 组件样式定义
const componentTokens = {
  primaryButton: {
    backgroundColor: colors.primary,
    color: colors.textWhite,
    padding: `${spacing.sm} ${spacing.lg}`,
    borderRadius: borderRadii.component.button,
    boxShadow: shadows.component.button,
    fontFamily: fonts.typography.button.fontFamily,
    fontSize: fonts.typography.button.fontSize,
    fontWeight: fonts.typography.button.fontWeight,

    '&:hover': {
      backgroundColor: colors.primaryDark,
      boxShadow: shadows.component.buttonHover,
    },

    '&:focus': {
      boxShadow: shadows.state.focus,
    },

    '&:disabled': {
      backgroundColor: colors.gray300,
      color: colors.textDisabled,
      boxShadow: shadows.none,
    },
  },

  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadii.component.card,
    boxShadow: shadows.component.card,
    padding: spacing.lg,
    border: `1px solid ${colors.divider}`,

    '&:hover': {
      boxShadow: shadows.component.cardHover,
    },
  },
};

console.log('Design Tokens 系统加载完成！');
console.log('可用的颜色:', Object.keys(colors));
console.log('可用的字体大小:', Object.keys(fontSizes));
console.log('可用的间距:', Object.keys(baseSpacing));

export {
  buttonStyles,
  componentTokens,
  effectStyles,
  layoutStyles,
  responsiveStyles,
  shapeStyles,
  typographyStyles,
  utilsExample,
};
