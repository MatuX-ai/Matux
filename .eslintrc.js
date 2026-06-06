module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:prettier/recommended', // 集成 prettier，避免格式冲突
  ],
  plugins: [
    '@typescript-eslint',
    'simple-import-sort', // 自动导入排序
    'unused-imports' // 未使用导入检测
  ],
  rules: {
    // TypeScript 严格规则
    '@typescript-eslint/explicit-function-return-type': ['warn', {
      allowExpressions: true,
      allowTypedFunctionExpressions: true,
      allowHigherOrderFunctions: true,
    }],
    '@typescript-eslint/explicit-module-boundary-types': 'warn',
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_',
      caughtErrorsIgnorePattern: '^_',
    }],
    '@typescript-eslint/prefer-nullish-coalescing': 'warn',
    '@typescript-eslint/prefer-optional-chain': 'warn',
    '@typescript-eslint/no-non-null-assertion': 'warn',

    // 导入排序规则
    'simple-import-sort/imports': ['error', {
      groups: [
        // Side effect imports
        ['^\\u0000'],
        // Packages - `@angular/*` comes first
        ['^@angular/[^.]', '^@[^.]', '^[^.][^@]'],
        // Parent imports - `../`
        ['^\\.\\.(?!/?$)', '^\\.\\./?$'],
        // Sibling imports - `./`
        ['^\\./(?=.*/)(?!/?$)', '^\\.(?!/?$)', '^\\./?$'],
        // Style imports
        ['^.+\\.s?css$'],
      ],
    }],
    'simple-import-sort/exports': 'error',

    // 未使用导入检测
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': [
      'warn',
      {
        vars: 'all',
        varsIgnorePattern: '^_',
        args: 'after-used',
        argsIgnorePattern: '^_'
      }
    ],

    // 通用JavaScript规则
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'error',
    'prefer-arrow-callback': 'error',

    // 复杂度控制
    'complexity': ['warn', 10],
    'max-depth': ['warn', 4],
    'max-lines-per-function': ['warn', { max: 50, skipBlankLines: true, skipComments: true }],
  },
  env: {
    node: true,
    es6: true,
    browser: true,
  },
  ignorePatterns: [
    'dist',
    'build',
    'node_modules',
    '*.js',
    'coverage',
    '*.min.js',
    'vendor/',
    'scripts/', // 忽略脚本目录
    // 以下文件/目录被 tsconfig.app.json 排除，eslint 不应对其检查
    'src/ai-sdk/**/*',
    'src/shared/**/*',
    'src/design-tokens/**/*',
    'src/environments/environment.prod.ts',
    'src/assets/i18n/helpers.ts',
    'src/assets/i18n/index.ts',
    'src/assets/i18n/types.ts',
    'src/assets/icons/icon-index.ts',
    'src/assets/icons/icon.module.ts',
    'src/app/admin/dashboard/dashboard.module.ts',
    'src/app/ai-code-generator/**/*',
    'src/app/education/**/*',
    'src/app/features/**/*',
    'src/app/management/**/*',
    'src/app/models/**/*',
    'src/app/offline-mode/**/*',
    'src/app/services/**/*',
    'src/app/routes.const.ts',
  ],
  // 忽略特定包的安全警告（xlsx 0.20.3 已修复安全问题，但工具可能误报）
  overrides: [
    {
      files: ['**/node_modules/xlsx/**/*'],
      rules: {
        // 忽略 node_modules 中的 xlsx 包
        '@typescript-eslint/no-explicit-any': 'off',
        '@typescript-eslint/no-unsafe-assignment': 'off',
      }
    }
  ],
};
