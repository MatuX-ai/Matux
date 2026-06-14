// Stylelint 配置文件
// 用于 SCSS/CSS 代码质量和一致性检查

module.exports = {
  // 扩展标准配置（注意：stylelint-config-standard-scss 已包含 recommended-scss，无需再扩展 CSS 版本）
  extends: [
    'stylelint-config-standard-scss'
  ],

  // 自定义插件
  plugins: [
    'stylelint-scss',
    'stylelint-order',
    'stylelint-declaration-strict-value'
  ],

  // 自定义规则
  rules: {
    // ==========================================================================
    // 基础规则
    // ==========================================================================

    // 禁止未知属性
    'property-no-unknown': [
      true,
      {
        ignoreProperties: [
          '^--',
          'stemPrimary',
          'stemPrimaryDark',
          'stemPrimaryLight',
          'stemSecondary',
          'stemAccent',
          'stemBackground',
          'stemSurface',
          'stemError',
          'stemWarning',
          'stemSuccess',
          'stemInfo',
          'stemShadow',
          'stemShadowCard',
          'stemShadowHover',
          'stemBorderRadius',
          'stemBorderRadiusFull',
          'stemBorderRadiusLg',
          'stemBorderRadiusMd',
          'stemBorderWidth',
          'stemTransition',
          'stemFontFamily',
          'stemFontSize',
          'stemZIndex',
          'stemRadiusFull',
          'stemRadiusLg',
          'stemRadiusMd'
        ]
      }
    ],

    // 禁止未知伪类选择器
    'selector-pseudo-class-no-unknown': [
      true,
      {
        ignorePseudoClasses: ['global', 'local', 'export']
      }
    ],

    // 禁止未知伪元素选择器
    'selector-pseudo-element-no-unknown': [
      true,
      {
        ignorePseudoElements: ['ng-deep']
      }
    ],

    'function-no-unknown': [
      true,
      {
        ignoreFunctions: ['map-get', 'map-has-key', 'map-keys', 'map-values', 'lighten', 'darken', 'percentage', 'define-palette', 'typography-level', 'define-light-theme', 'define-dark-theme']
      }
    ],

    // 使用标准 SCSS 配置的默认处理，允许 SCSS 变量在属性值中使用
    'declaration-property-value-no-unknown': null,

    // ==========================================================================
    // 命名规范
    // ==========================================================================

    // 类名必须使用 kebab-case 或 BEM 命名法
    'selector-class-pattern': [
      '^[a-z]([a-z0-9]+)?(__[a-z0-9]([a-z0-9]+)?)?(--[a-z0-9]([a-z0-9]+)?)?$',
      {
        message: 'Expected class selector to be kebab-case or BEM format (e.g., "component-name", "component__element", "component--modifier")',
        severity: 'warning'
      }
    ],

    // ID 选择器命名规范
    'selector-id-pattern': [
      '^[a-z][a-zA-Z0-9]*$',
      {
        message: 'Expected id selector to be camelCase'
      }
    ],

    // SCSS 变量命名规范
    'scss/dollar-variable-pattern': [
      '^[_]?[a-z][a-zA-Z0-9]*([-][a-z0-9]+)*$',
      {
        message: 'Expected SCSS variable to be kebab-case with optional leading underscore'
      }
    ],

    // 自定义属性命名规范
    'custom-property-pattern': [
      '^[a-z][a-zA-Z0-9]*([-][a-z0-9]+)*$',
      {
        message: 'Expected custom property to be kebab-case'
      }
    ],

    // ==========================================================================
    // 代码组织和结构
    // ==========================================================================

    // 属性声明顺序 - 增强版
    'order/properties-order': [
      [
        // CSS Custom Properties (CSS变量)
        {
          properties: ['--*'],
          order: 'flexible'
        },

        // Positioning
        'position',
        'inset',
        'top',
        'right',
        'bottom',
        'left',
        'z-index',

        // Display & Box Model
        'display',
        'visibility',
        'float',
        'clear',
        'overflow',
        'overflow-x',
        'overflow-y',
        '-ms-overflow-x',
        '-ms-overflow-y',
        '-webkit-overflow-scrolling',
        'clip',
        'clip-path',
        'zoom',

        // Flexbox
        'flex',
        'flex-grow',
        'flex-shrink',
        'flex-basis',
        'flex-direction',
        'flex-wrap',
        'flex-flow',
        'order',
        'justify-content',
        'align-items',
        'align-content',
        'align-self',

        // Grid
        'grid',
        'grid-area',
        'grid-template',
        'grid-template-columns',
        'grid-template-rows',
        'grid-template-areas',
        'grid-auto-columns',
        'grid-auto-rows',
        'grid-auto-flow',
        'grid-column',
        'grid-column-start',
        'grid-column-end',
        'grid-row',
        'grid-row-start',
        'grid-row-end',
        'gap',
        'grid-gap',
        'grid-column-gap',
        'grid-row-gap',

        // Table Layout
        'table-layout',
        'empty-cells',
        'caption-side',
        'border-spacing',
        'border-collapse',
        'list-style',
        'list-style-position',
        'list-style-type',
        'list-style-image',

        // Box Model
        'box-sizing',
        'width',
        'min-width',
        'max-width',
        'height',
        'min-height',
        'max-height',
        'margin',
        'margin-top',
        'margin-right',
        'margin-bottom',
        'margin-left',
        'padding',
        'padding-top',
        'padding-right',
        'padding-bottom',
        'padding-left',

        // Border
        'border',
        'border-width',
        'border-style',
        'border-color',
        'border-top',
        'border-top-width',
        'border-top-style',
        'border-top-color',
        'border-right',
        'border-right-width',
        'border-right-style',
        'border-right-color',
        'border-bottom',
        'border-bottom-width',
        'border-bottom-style',
        'border-bottom-color',
        'border-left',
        'border-left-width',
        'border-left-style',
        'border-left-color',
        'border-radius',
        'border-top-left-radius',
        'border-top-right-radius',
        'border-bottom-right-radius',
        'border-bottom-left-radius',
        'border-image',
        'border-image-source',
        'border-image-slice',
        'border-image-width',
        'border-image-outset',
        'border-image-repeat',

        // Outline
        'outline',
        'outline-width',
        'outline-style',
        'outline-color',
        'outline-offset',

        // Background
        'background',
        'background-color',
        'background-image',
        'background-repeat',
        'background-attachment',
        'background-position',
        'background-position-x',
        'background-position-y',
        'background-clip',
        'background-origin',
        'background-size',
        'box-decoration-break',
        'box-shadow',

        // Color & Opacity
        'color',
        'opacity',
        'filter',
        'backdrop-filter',

        // Typography
        'font',
        'font-family',
        'font-size',
        'font-weight',
        'font-style',
        'font-variant',
        'font-size-adjust',
        'font-stretch',
        'font-effect',
        'font-emphasize',
        'font-emphasize-position',
        'font-emphasize-style',
        'font-smooth',
        'line-height',

        // Text
        'text-align',
        'text-align-last',
        'vertical-align',
        'white-space',
        'text-decoration',
        'text-emphasis',
        'text-emphasis-color',
        'text-emphasis-style',
        'text-emphasis-position',
        'text-indent',
        'text-justify',
        'letter-spacing',
        'word-spacing',
        'text-outline',
        'text-transform',
        'text-wrap',
        'text-overflow',
        'text-overflow-ellipsis',
        'text-overflow-mode',
        'word-wrap',
        'word-break',
        'tab-size',
        'hyphens',
        'unicode-bidi',
        'direction',

        // Content
        'content',
        'quotes',
        'counter-reset',
        'counter-increment',

        // Interaction
        'resize',
        'cursor',
        'pointer-events',
        'user-select',
        'touch-action',

        // Navigation
        'nav-index',
        'nav-up',
        'nav-right',
        'nav-down',
        'nav-left',

        // Transitions & Animations
        'transition',
        'transition-delay',
        'transition-timing-function',
        'transition-duration',
        'transition-property',
        'transform',
        'transform-origin',
        'transform-style',
        'perspective',
        'perspective-origin',
        'backface-visibility',

        // Animations
        'animation',
        'animation-name',
        'animation-duration',
        'animation-play-state',
        'animation-timing-function',
        'animation-delay',
        'animation-iteration-count',
        'animation-direction',
        'animation-fill-mode',

        // Performance
        'will-change',
        'contain',

        // Print
        'page-break-before',
        'page-break-after',
        'page-break-inside',
        'orphans',
        'widows',

        // Columns
        'columns',
        'column-span',
        'column-width',
        'column-count',
        'column-fill',
        'column-gap',
        'column-rule',
        'column-rule-width',
        'column-rule-style',
        'column-rule-color'
      ],
      {
        unspecified: 'bottomAlphabetical',
        severity: 'error',
        message: 'CSS properties must follow the established order: CSS variables first, then positioning, display, flexbox/grid, box model, border, background, typography, interactions, and animations last'
      }
    ],

    // 声明块内属性按字母顺序排列（可选）
    'order/order': [
      [
        'custom-properties',
        'dollar-variables',
        {
          type: 'at-rule',
          name: 'include',
          hasBlock: false
        },
        'declarations',
        {
          type: 'at-rule',
          name: 'include',
          hasBlock: true
        },
        'rules'
      ]
    ],

    // 强制属性按字母顺序（仅用于特定场景）
    'order/properties-alphabetical-order': null,

    // 禁止重复属性
    'declaration-block-no-duplicate-properties': [
      true,
      {
        ignore: ['consecutive-duplicates-with-different-values']
      }
    ],

    // 禁止空规则
    'block-no-empty': true,

    // ==========================================================================
    // 严格值检查
    // ==========================================================================

    // 强制使用 Design Tokens 变量而非硬编码值
    'scale-unlimited/declaration-strict-value': [
      [
        '/color/',
        'font-family',
        'font-size',
        'font-weight',
        'line-height',
        'z-index',
        'border-radius',
        'box-shadow',
        'transition',
        'animation'
      ],
      {
        ignoreValues: [
          'inherit',
          'initial',
          'unset',
          'currentColor',
          'transparent',
          'none',
          '0',
          '1',
          'auto',
          'normal',
          'bold',
          'italic',
          'center',
          'left',
          'right',
          'white',
          'black',
          '#fff',
          '#000',
          // 允许的百分比值
          '/^\\d+%$/',
          // 允许的 px/rem/em 值
          '/^\\d+px$/',
          '/^\\d+\\.\\d+px$/',
          '/^\\d+rem$/',
          '/^\\d+\\.\\d+rem$/',
          // 允许的 rgb/rgba/hsl/hsla 颜色值
          '/^rgba?\(.+\)$/',
          '/^hsla?\(.+\)$/',
          '/^#[0-9a-fA-F]{3}$/',
          '/^#[0-9a-fA-F]{6}$/',
          '/^#[0-9a-fA-F]{8}$/',
          // 允许的计算值
          '/^calc\\(.+\\)$/',
          // 允许的负 px 值（如 -1px）
          '/^-?\\d+px$/',
          '/^-?\\d+\\.\\d+px$/',
          // 允许的 em 值
          '/^\\d+\\.\\d+em$/',
          '/^\\d+em$/',
          // 允许的纯数字（如 font-weight: 500, z-index: 10, line-height: 1.5）
          '/^\\d+$/',
          '/^\\d+\\.\\d+$/',
          // 允许的动画名称
          'spin',
          'fadeInUp',
          'pulse-dot',
          'infinite',
          // 允许的 CSS 属性名作为 transition 值
          'opacity',
          'background',
          'background-color',
          'width',
          'box-shadow',
          'transform',
          'color',
          // 允许常见的字体系列名
          '/^[\'\"][a-zA-Z\s-]+[\'\"]$/',
          // 允许 'Courier New', 等带逗号字体名
          '/^[\'\"][a-zA-Z\s-]+[\'\"],$/',
          // 允许 'Courier New', monospace 等组合字体
          '/^[\'\"][a-zA-Z\s-]+[\'\"],\\s*[a-zA-Z-]+$/',
          // 允许的时间值（如 transition: 0.3s）
          '/^-?\\d+(\\.\\d+)?s,?$/',
          '/^-?\\d+(\\.\\d+)?ms$/',
          // 允许 transition: all
          'all',
          // 允许的过渡时间函数
          'ease',
          'ease,',
          'ease-in',
          'ease-out',
          'ease-in-out',
          'linear',
          'step-start',
          'step-end',
          // 允许的过渡时长
          // 已由上方时间值规则覆盖，移除重复
          // 允许 cubic-bezier 时间函数
          '/^cubic-bezier\\(.+\\)$/',
          // 允许 Material Design 标准 cubic-bezier
          'cubic-bezier(0.4, 0, 0.2, 1)',
          'cubic-bezier(0.4, 0, 0.2, 1),',
          'border-color',
        ],
        expandShorthand: true,
        severity: 'warning'
      }
    ],

    // ==========================================================================
    // SCSS 特定规则
    // ==========================================================================

    // 禁止嵌套深度超过 3 层
    'max-nesting-depth': [
      10,
      {
        ignore: ['blockless-at-rules', 'pseudo-classes'],
        severity: 'warning'
      }
    ],

    // 禁止重复的 mixin
    'scss/at-mixin-pattern': [
      '^[a-z][a-zA-Z0-9]*([-][a-z0-9]+)*$',
      {
        message: 'Expected @mixin name to be kebab-case'
      }
    ],

    // 禁止重复的 function
    'scss/at-function-pattern': [
      '^[a-z][a-zA-Z0-9]*([-][a-z0-9]+)*$',
      {
        message: 'Expected @function name to be kebab-case'
      }
    ],

    // 禁止重复的 placeholder
    'scss/percent-placeholder-pattern': [
      '^[a-z][a-zA-Z0-9]*([-][a-z0-9]+)*$',
      {
        message: 'Expected %placeholder name to be kebab-case'
      }
    ],

    // 禁止使用全局变量（除了 Design Tokens）
    'scss/no-global-function-names': [
      true,
      {
        severity: 'warning'
      }
    ],

    // 允许 mixin 中的控制流嵌套（@if/@else 等）
    'nesting-selector-no-missing-scoping-root': [
      true,
      {
        severity: 'warning'
      }
    ],

    // ==========================================================================
    // 性能和最佳实践
    // ==========================================================================

    // 禁止低效的选择器
    'selector-max-specificity': [
      '2,8,0',
      {
        ignoreSelectors: [':global', ':local', ':export', ':host', ':host-context', ':is'],
        severity: 'warning'
      }
    ],

    // 限制选择器数量
    'selector-max-compound-selectors': [
      5,
      {
        severity: 'warning'
      }
    ],

    // 限制 ID 选择器使用
    'selector-max-id': [
      0,
      {
        severity: 'warning',
        message: 'Avoid using ID selectors for better reusability'
      }
    ],

    // 禁止使用 !important（降级为 null，避免过度警告）
    'declaration-no-important': null,





    // 禁止重复的选择器（SCSS 嵌套可能导致误报，降为 warning）
    'no-duplicate-selectors': [
      true,
      {
        severity: 'warning'
      }
    ],

    // 禁止未知的动画名称
    'keyframe-declaration-no-important': [
      true,
      {
        severity: 'error'
      }
    ],

    // keyframe 命名规范（降为 warning）
    'keyframes-name-pattern': [
      '^[a-z][a-z0-9-_]*$',
      {
        severity: 'warning'
      }
    ],

    // 无参数 mixin 调用允许带括号
    'scss/at-mixin-argumentless-call-parentheses': null,

    // @extend 建议使用占位符，但降为 warning
    'scss/at-extend-no-missing-placeholder': [
      true,
      {
        severity: 'warning'
      }
    ],

    // 允许 SCSS 导入在任意位置（@use/@forward 位置规则在 SCSS 中可能误报）
    'no-invalid-position-at-import-rule': null,
    'no-invalid-position-declaration': null,

    // 允许 SCSS 变量在媒体查询中使用
    'media-query-no-invalid': null,

    // ==========================================================================
    // 可访问性
    // ==========================================================================

    // 颜色命名检查 - 取消（已由 declaration-strict-value 覆盖颜色检查）
    'color-named': null,
    'color-hex-length': 'short',


    // 禁止无效的颜色值
    'color-no-invalid-hex': [
      true,
      {
        severity: 'error'
      }
    ],

    // 确保单位使用正确
    'unit-no-unknown': [
      true,
      {
        ignoreUnits: ['x'],
        severity: 'error'
      }
    ],

    // ==========================================================================
    // WCAG 对比度防护规则（2026-06-13 新增，基于 my-courses 页面审计）
    // 背景：原项目扫描仅用 regex 查找弱化白，未考虑：
    //   1) 渐变底端低对比度（如 $stem-primary-light 终点 2.54:1）
    //   2) 文字对比度系统性遗漏（--color-text-disabled, --color-gray-400 等 token）
    //   3) opacity 会同时降低文字对比度
    //   4) 错误红色 #ef4444 与白色文字仅 3.77:1，违反 AA
    // 以下规则拦截常见违规模式，均为 warning 不阻塞提交。
    // ==========================================================================
    'declaration-property-value-disallowed-list': [
      {
        // 1) 禁止使用已知的低对比度文字 token（vs 背景白色 2.52:1-2.57:1）
        // 2) 禁止使用 $stem-primary / $stem-success / $stem-warning / $stem-error / $stem-secondary
        //    作为 color（vs #fff < 4.5:1，应改用 -dark 变体）
        //    3) 禁止硬编码低对比度 hex 值
        color: [
          '/var\\(\\s*--color-text-disabled/',
          '/var\\(\\s*--color-gray-400\\b/',
          // SCSS 变量（使用 negative lookahead 排除 -dark 变体）
          '/\\$stem-primary(?!-dark)\\b/',
          '/\\$stem-success(?!-dark)\\b/',
          '/\\$stem-warning(?!-dark)\\b/',
          '/\\$stem-error(?!-dark)\\b/',
          '/\\$stem-secondary(?!-dark)\\b/',
          // 硬编码 hex 值（vs #fff < 4.5:1）
          '/^#22c55e$/',  // success-500 (2.28:1)
          '/^#f59e0b$/',  // warning-500 (2.15:1)
          '/^#ef4444$/',  // error-500 (3.77:1)
          '/^#0ea5e9$/',  // secondary-500 (2.77:1)
          '/^#94a3b8$/',  // gray-400 (2.57:1)
          '/^#a8a29e$/',  // disabled (2.52:1)
          '/^#86efac$/',  // success-300 (1.61:1)
          '/^#a1a1aa$/',  // gray-400 alt (2.62:1)
          '/^#f97316$/',  // orange-500 (2.62:1)
          '/^#3b82f6$/',  // blue-500 (3.68:1, 需 4.5:1 正文)
        ],
        // 4) 禁止错误红 #ef4444 作为 background（vs 白色 3.77:1，不达 AA 4.5:1）
        background: [
          '/var\\(\\s*--color-error\\s*,\\s*#ef4444\\s*\\)/'
        ],
        // 5) 禁止 opacity 0.5-0.89（同时降低文字对比度）
        opacity: [
          '/^0\\.[5-8]\\d*$|^0\\.5$|^0\\.6$|^0\\.7$|^0\\.8$|^0\\.9$/'
        ]
      },
      {
        message: 'WCAG 对比度违规：禁止使用已知的低对比度 color/background/opacity 值。请改用 token 设计系统中提供的深色变体（如 $stem-primary-dark 代替 $stem-primary）。',
        severity: 'warning'
      }
    ],

    // 4) 禁止 $stem-primary-light 作为 linear-gradient 终点
    // 原问题：linear-gradient(135deg, $stem-primary 0%, $stem-primary-light 100%)
    // 渐变底端 #10b981 与白色文字仅 2.54:1，违反 AA。
    // 应改用 $stem-primary-dark 保持对比度。
    // 注：拦截 linear-gradient 中的 $stem-primary-light 需要自定义 stylelint 插件
    // （因为渐变是组合值，declaration-property-value-disallowed-list 不支持）。
    // 现阶段为不阻塞构建，验证留给 PR 评审。后续可接入 stylelint-plugin-wcag。

    // ==========================================================================
    // 兼容性
    // ==========================================================================

    // 禁止使用过时的属性
    'property-no-vendor-prefix': [
      true,
      {
        ignoreProperties: ['appearance', 'user-select', 'tap-highlight-color']
      }
    ],

    // 禁止使用过时的值
    'value-no-vendor-prefix': [
      true,
      {
        ignoreValues: ['box', 'inline-box', 'flex', 'grid']
      }
    ],

    // 禁止无效的媒体查询
    'media-feature-name-no-unknown': [
      true,
      {
        ignoreMediaFeatureNames: ['prefers-reduced-motion'],
        severity: 'error'
      }
    ],

    // 确保字体系列使用引号
    'font-family-name-quotes': [
      'always-where-recommended',
      {
        severity: 'warning'
      }
    ],

    // 禁止无效的函数
    'function-calc-no-unspaced-operator': [
      true,
      {
        severity: 'error'
      }
    ],
  },

  // 忽略文件
  ignoreFiles: [
    '**/node_modules/**',
    '**/dist/**',
    '**/build/**',
    '**/*.min.css',
    '**/*.bundle.css',
    'coverage/**',
    '.git/**'
  ],

  // 配置覆盖
  overrides: [
    // 针对 Angular 组件样式文件的特殊规则
    {
      files: ['**/*.component.scss'],
      rules: {
        // Angular 组件允许更高的选择器特异性
        'selector-max-specificity': [
          '0,8,0',
          {
            ignoreSelectors: [':global', ':local', ':export', ':host', ':host-context', ':is'],
            severity: 'warning'
          }
        ],
        // 允许使用 ::ng-deep
        'selector-pseudo-element-no-unknown': [
          true,
          {
            ignorePseudoElements: ['ng-deep']
          }
        ]
      }
    },

    // 针对主题文件的特殊规则
    {
      files: ['**/themes/**/*.scss', '**/_custom-theme.scss'],
      rules: {
        // 主题文件可能需要更多的灵活性
        'declaration-no-important': null,
        'selector-max-specificity': null,
        'no-duplicate-selectors': null
      }
    },

    // 针对协同编辑器组件的特殊规则
    {
      files: ['**/collaborative-editor/**'],
      rules: {
        // 协同编辑器组件使用 Material CDK 类名，不符合标准 BEM 格式
        'selector-class-pattern': null
      }
    }
  ]
};
