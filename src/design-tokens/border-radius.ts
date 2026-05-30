/**
 * Design Tokens - Border Radius
 *
 * 圆角设计变量系统，定义统一的组件圆角规范
 * 确保界面元素具有协调一致的圆角效果
 */

/** 圆角尺寸规范 */
export const borderRadius = {
  /** 无圆角 */
  none: '0px',
  /** 极小圆角 - 用于细微的圆角效果 */
  xs: '0.125rem', // 2px
  /** 小圆角 - 用于按钮、输入框等基础组件 */
  sm: '0.25rem', // 4px
  /** 中等圆角 - 用于卡片、面板等容器组件 */
  md: '0.5rem', // 8px
  /** 大圆角 - 用于特色卡片、模态框等 */
  lg: '0.75rem', // 12px
  /** 超大圆角 - 用于突出显示的组件 */
  xl: '1rem', // 16px
  /** 完全圆形 - 用于头像、徽章等圆形元素 */
  full: '9999px',
} as const;

/** 组件特定圆角 */
export const componentBorderRadius = {
  /** 按钮圆角 */
  button: borderRadius.sm,
  /** 输入框圆角 */
  input: borderRadius.sm,
  /** 卡片圆角 */
  card: borderRadius.md,
  /** 模态框圆角 */
  modal: borderRadius.lg,
  /** 徽章圆角 */
  badge: borderRadius.full,
  /** 头像圆角 */
  avatar: borderRadius.full,
  /** 下拉菜单圆角 */
  dropdown: borderRadius.md,
  /** 提示框圆角 */
  tooltip: borderRadius.sm,
} as const;

/** 方向性圆角 */
export const directionalBorderRadius = {
  /** 顶部圆角 */
  top: {
    left: borderRadius.md,
    right: borderRadius.md,
  },
  /** 底部圆角 */
  bottom: {
    left: borderRadius.md,
    right: borderRadius.md,
  },
  /** 左侧圆角 */
  left: {
    top: borderRadius.md,
    bottom: borderRadius.md,
  },
  /** 右侧圆角 */
  right: {
    top: borderRadius.md,
    bottom: borderRadius.md,
  },
} as const;

/** 响应式圆角 */
export const responsiveBorderRadius = {
  /** 移动端圆角 - 更加圆润 */
  mobile: {
    button: borderRadius.sm,
    card: borderRadius.md,
    modal: borderRadius.lg,
  },
  /** 桌面端圆角 - 相对方正 */
  desktop: {
    button: borderRadius.xs,
    card: borderRadius.sm,
    modal: borderRadius.md,
  },
} as const;

/** 圆角工具函数 */
export const borderRadiusUtils = {
  /** 获取圆角值 */
  get: (size: keyof typeof borderRadius): string => borderRadius[size],

  /** 应用圆角到元素 */
  apply: (element: string, radius: keyof typeof borderRadius): string =>
    `${element} { border-radius: ${borderRadius[radius]}; }`,

  /** 创建圆角组合 */
  combine: (
    topLeft: keyof typeof borderRadius = 'none',
    topRight: keyof typeof borderRadius = 'none',
    bottomRight: keyof typeof borderRadius = 'none',
    bottomLeft: keyof typeof borderRadius = 'none'
  ): string =>
    `${borderRadius[topLeft]} ${borderRadius[topRight]} ${borderRadius[bottomRight]} ${borderRadius[bottomLeft]}`,
} as const;

/** 完整圆角系统 */
export const borderRadii = {
  ...borderRadius,
  component: componentBorderRadius,
  directional: directionalBorderRadius,
  responsive: responsiveBorderRadius,
  utils: borderRadiusUtils,
} as const;

/** 类型定义 */
export type BorderRadius = typeof borderRadius;
export type ComponentBorderRadius = typeof componentBorderRadius;
export type DirectionalBorderRadius = typeof directionalBorderRadius;
export type ResponsiveBorderRadius = typeof responsiveBorderRadius;
export type BorderRadiusToken = typeof borderRadii;

export default borderRadii;
