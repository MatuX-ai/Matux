/**
 * Design Tokens - Shadows
 *
 * 阴影设计变量系统，定义不同层级的阴影效果
 * 用于营造界面层次感和深度效果
 */

/** 基础阴影 */
export const baseShadows = {
  /** 无阴影 */
  none: 'none',
  /** 极轻微投影 - 用于细微的悬浮效果 */
  xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  /** 小投影 - 用于基础卡片和组件 */
  sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  /** 中等投影 - 用于重要卡片和面板 */
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  /** 大投影 - 用于模态框和重要组件 */
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  /** 超大投影 - 用于突出显示的重要元素 */
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
} as const;

/** 组件特定阴影 */
export const componentShadows = {
  /** 按钮默认阴影 */
  button: baseShadows.sm,
  /** 按钮悬停阴影 */
  buttonHover: baseShadows.md,
  /** 卡片默认阴影 */
  card: baseShadows.sm,
  /** 卡片悬停阴影 */
  cardHover: baseShadows.md,
  /** 模态框阴影 */
  modal: baseShadows.xl,
  /** 下拉菜单阴影 */
  dropdown: baseShadows.lg,
  /** 提示框阴影 */
  tooltip: baseShadows.sm,
  /** 导航栏阴影 */
  navbar: baseShadows.sm,
} as const;

/** 状态阴影 */
export const stateShadows = {
  /** 焦点状态阴影 */
  focus: '0 0 0 3px rgba(33, 150, 243, 0.3)',
  /** 错误状态阴影 */
  error: '0 0 0 3px rgba(244, 67, 54, 0.3)',
  /** 成功状态阴影 */
  success: '0 0 0 3px rgba(76, 175, 80, 0.3)',
  /** 警告状态阴影 */
  warning: '0 0 0 3px rgba(255, 152, 0, 0.3)',
} as const;

/** 方向性阴影 */
export const directionalShadows = {
  /** 向下投影 */
  down: {
    sm: '0 2px 4px 0 rgba(0, 0, 0, 0.1)',
    md: '0 4px 8px 0 rgba(0, 0, 0, 0.12)',
    lg: '0 8px 16px 0 rgba(0, 0, 0, 0.16)',
  },
  /** 向上投影 */
  up: {
    sm: '0 -2px 4px 0 rgba(0, 0, 0, 0.1)',
    md: '0 -4px 8px 0 rgba(0, 0, 0, 0.12)',
    lg: '0 -8px 16px 0 rgba(0, 0, 0, 0.16)',
  },
  /** 内阴影 */
  inner: {
    sm: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    md: 'inset 0 4px 8px 0 rgba(0, 0, 0, 0.1)',
    lg: 'inset 0 8px 16px 0 rgba(0, 0, 0, 0.15)',
  },
} as const;

/** 响应式阴影 */
export const responsiveShadows = {
  /** 移动端阴影 - 更加明显以适应触摸交互 */
  mobile: {
    card: baseShadows.md,
    modal: baseShadows.xl,
    button: baseShadows.sm,
  },
  /** 桌面端阴影 - 相对微妙 */
  desktop: {
    card: baseShadows.sm,
    modal: baseShadows.lg,
    button: baseShadows.xs,
  },
} as const;

/** 阴影工具函数 */
export const shadowUtils = {
  /** 获取阴影值 */
  get: (size: keyof typeof baseShadows): string => baseShadows[size],

  /** 应用阴影到元素 */
  apply: (element: string, shadow: keyof typeof baseShadows): string =>
    `${element} { box-shadow: ${baseShadows[shadow]}; }`,

  /** 创建自定义阴影 */
  create: (
    offsetX: string,
    offsetY: string,
    blurRadius: string,
    spreadRadius: string,
    color: string
  ): string => `${offsetX} ${offsetY} ${blurRadius} ${spreadRadius} ${color}`,

  /** 多层阴影组合 */
  multiple: (...shadows: string[]): string => shadows.join(', '),
} as const;

/** 完整阴影系统 */
export const shadows = {
  ...baseShadows,
  component: componentShadows,
  state: stateShadows,
  directional: directionalShadows,
  responsive: responsiveShadows,
  utils: shadowUtils,
} as const;

/** 类型定义 */
export type BaseShadow = typeof baseShadows;
export type ComponentShadow = typeof componentShadows;
export type StateShadow = typeof stateShadows;
export type DirectionalShadow = typeof directionalShadows;
export type ResponsiveShadow = typeof responsiveShadows;
export type ShadowToken = typeof shadows;

export default shadows;
