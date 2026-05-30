// Stylelint 配置文件
// 用于 SCSS/CSS 代码质量和一致性检查

module.exports = {
  // 扩展标准配置
  extends: [
    'stylelint-config-standard-scss',
    'stylelint-config-recommended'
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
    'property-no-unknown': true,
    
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
    
    // 禁止未知函数
    'function-no-unknown': [
      true,
      {
        ignoreFunctions: ['map-get', 'map-has-key', 'map-keys', 'map-values']
      }
    ],

    // ==========================================================================
    // 命名规范
    // ==========================================================================
    
    // 类名必须使用 kebab-case 或 BEM 命名法
    'selector-class-pattern': [
      '^[a-z]([a-z0-9-]+)?(__[a-z0-9]([a-z0-9-]+)?)?(--[a-z0-9]([a-z0-9-]+)?)?$',
      {
        message: 'Expected class selector to be kebab-case or BEM format (e.g., "component-name", "component__element", "component--modifier")'
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
          // 允许的百分比值
          '/^\\d+%$/',
          // 允许的计算值
          '/^calc\\(.+\\)$/'
        ],
        expandShorthand: true,
        severity: 'warning'
      }
    ],

    // ==========================================================================
    // SCSS 特定规则
    // ==========================================================================
    
    // 禁止嵌套深度超过 3 层
    'scss/max-nesting-depth': [
      3,
      {
        ignore: ['blockless-at-rules', 'pseudo-classes']
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

    // ==========================================================================
    // 性能和最佳实践
    // ==========================================================================
    
    // 禁止低效的选择器
    'selector-max-specificity': [
      '0,3,0',
      {
        ignoreSelectors: [':global', ':local', ':export'],
        severity: 'warning'
      }
    ],
    
    // 限制选择器数量
    'selector-max-compound-selectors': [
      3,
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
    
    // 禁止使用 !important（严重违规）
    'declaration-no-important': [
      true,
      {
        severity: 'error',
        message: '!important declarations should be avoided. Use specificity instead.'
      }
    ],
    
    // 禁止过多的空行
    'selector-max-empty-lines': [
      0,
      {
        severity: 'error'
      }
    ],
    
    // 限制每行最大长度
    'max-line-length': [
      120,
      {
        ignore: ['comments'],
        severity: 'warning'
      }
    ],
    
    // 禁止重复的选择器
    'no-duplicate-selectors': [
      true,
      {
        severity: 'error'
      }
    ],
    
    // 禁止未知的动画名称
    'keyframe-declaration-no-important': [
      true,
      {
        severity: 'error'
      }
    ],
    
    // 限制媒体查询嵌套深度
    'media-query-no-invalid': true,

    // ==========================================================================
    // 可访问性
    // ==========================================================================
    
    // 确保颜色对比度相关的属性正确使用
    'color-named': 'never',
    'color-hex-length': 'short',
    'color-hex-case': 'lower',
    
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
        'selector-max-specificity': '0,4,0',
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
        'selector-max-specificity': null
      }
    }
  ]
};