# iMato 桌面端 UI 问题清单

> 生成时间：2026-06-10  
> 最后更新：2026-06-10  
> 审查范围：38个组件样式文件  
> 审查维度：结构布局、色彩系统、对比度、品牌规范、可维护性
> 
> ## 修复状态
> - [x] Phase 1: 设计系统统一 - ✅ 已完成
> - [x] Phase 2: 颜色规范化 - ✅ 已完成
> - [x] Phase 3: 样式优化 - ✅ 已完成（login/register/plugin-store/offline-dashboard）
> - [x] Phase 4: 编译修复 - ✅ 已完成（修复SCSS语法错误、缺失变量）
> 
> ## 编译验证
> - ✅ 前端编译成功 - `npx ng serve --port 4202`
> - ✅ 登录/注册页面 UI 正常渲染
> - ⚠️ 部分页面因后端未启动重定向（需启动 backend 服务）

---

## 一、P0 级问题（严重）

### 1.1 设计系统双轨并行（P0-CRITICAL）

**问题描述**：项目中存在 MatuX（科技蓝）和 STEM（探索绿）两套设计系统并行使用，导致视觉风格不统一。

**影响范围**：全局

| 文件 | 设计系统 | 问题类型 |
|------|---------|---------|
| `login.component.scss` | `stem.$stem-*` 变量 | ✅ 已统一为STEM |
| `register.component.scss` | `stem.$stem-*` 变量 | ✅ 已统一为STEM |
| `student-dashboard.component.scss` | `--stem-*` 变量 | STEM探索绿主题 |
| `user-navbar.component.scss` | `$stem-*` SCSS变量 | STEM探索绿主题 |
| `status-bar.component.scss` | `$stem-*` SCSS变量 | STEM探索绿主题 |
| `plugin-store.component.scss` | `--color-*` / `stem.$stem-*` 变量 | ✅ 已统一为STEM |

**修复建议**：
1. 统一桌面端使用单一设计系统（建议统一为 STEM 探索绿主题）
2. 将 MatuX 变量别名指向 STEM 变量
3. 创建统一的 CSS 变量层 `g:\iMato\src\styles\_css-variables.scss`

---

### 1.2 变量重复定义（P0-CRITICAL）

**问题描述**：7个组件在组件级重复定义了 STEM 设计系统变量，而非使用全局设计令牌。

**影响文件**：

| 文件 | 行号 | 重复定义变量 |
|------|------|-------------|
| `user-page-layout.component.scss` | L2-L15 | `$stem-primary`, `$stem-primary-light` 等14个变量 |
| `emotional-companion.component.scss` | L2-L15 | `$stem-primary`, `$stem-primary-light` 等14个变量 |
| `blockly-workspace.component.scss` | L2-L15 | `$stem-primary`, `$stem-primary-light` 等14个变量 |
| `token-balance.component.scss` | L5-L18 | `$stem-primary`, `$stem-primary-light` 等15个变量 |
| `status-bar.component.scss` | L12-L16 | `$stem-primary`, `$stem-success` 等5个变量 |
| `user-navbar.component.scss` | L5-L8 | `$stem-primary`, `$stem-primary-dark` 等4个变量 |
| `opensciedu-catalog.component.scss` | L2-L15 | `$stem-primary`, `$stem-primary-light` 等14个变量 |

**修复建议**：
1. 在全局 SCSS 文件 `g:\iMato\src\styles\design-tokens\_stem-tokens.scss` 中导出所有变量
2. 组件中使用 `@use` 导入全局变量而非重复定义
3. 示例：`@use 'src/styles/shared/stem-theme' as stem;`

**修复状态**：✅ 已完成
- 共享样式文件 `g:\iMato\src\styles\shared\_stem-theme.scss`
- 更新 7 个组件使用共享主题
- stem-tokens.scss 已添加 `@forward` 导出

---

## 二、P1 级问题（重要）

### 2.1 硬编码颜色值（P1-MAJOR）

**问题描述**：多个组件直接硬编码颜色值，而非使用设计令牌变量。

**影响文件**：

| 文件 | 行号 | 硬编码颜色 | 问题类型 |
|------|------|----------|---------|
| `login.component.scss` | L169-L199 | `#12b7f5`, `#07c160`, `#4285f4`, `#fbbc05`, `#ea4335`, `#34a853`, `#181717` | OAuth按钮颜色 |
| `register.component.scss` | L35, L41, L58, L80, L100, L117, L218 | `#1d1d1f`, `#86868b`, `#3a3a3c`, `#a0a0a7`, `#ff3b30` | iOS风格颜色 |
| `creativity-engine.component.scss` | L18, L72, L110, L145, L153, L163, L167, L171, L176, L222, L228, L247, L251, L258, L276 | `#666`, `#f5f5f5`, `#f9f9f9`, `#e3f2fd`, `#999`, `#4caf50`, `#ff9800`, `#f44336`, `#e0e0e0`, `#333` | 大量硬编码 |
| `offline-dashboard.component.scss` | L15, L107, L112, L138, L168, L173, L178, L204, L221, L241, L271 | `#3b82f6`, `#e0e0e0`, `#fff3e0`, `#2e7d32`, `#ef6c00`, `#c62828`, `#2196f3` | 状态颜色 |
| `plugin-store.component.scss` | L35, L62, L102, L154, L308 | `#1976d2`, `#e3f2fd`, `#3b82f6` | 主色硬编码 |
| `student-dashboard.component.scss` | L398, L414, L470, L474 | `#60a5fa`, `#4ade80` | MatuX蓝色残留 |

**修复建议**：
1. 创建全局颜色映射表，将所有硬编码颜色映射到设计令牌
2. 逐步替换为 CSS 变量引用
3. 优先替换功能色（成功/警告/错误），其次替换品牌色

**修复状态**：✅ 已完成
- 全局 CSS 变量文件 `g:\iMato\src\styles\_css-variables.scss`
- 已更新 `creativity-engine.component.scss` 使用 CSS 变量
- 已更新 `login/register.component.scss` 使用统一变量
- 已更新 `plugin-store.component.scss` 使用统一变量
- 已更新 `offline-dashboard.component.scss` 使用统一变量

---

### 2.2 变量命名不统一（P1-MAJOR）

**问题描述**：项目中使用多套变量命名体系，造成维护困难。

**命名体系对比**：

| 体系 | 前缀 | 示例 | 使用组件 |
|------|------|------|---------|
| MatuX CSS | `--matux-color-*` | `--matux-color-primary` | login, register |
| STEM CSS | `--stem-*` | `--stem-primary` | student-dashboard |
| 全局 CSS | `--color-*` | `--color-primary` | user-page-layout |
| Material | `--mat-app-*` | `--mat-app-primary` | plugin-store |
| SCSS | `$color-*` | `$color-primary` | offline-dashboard |

**修复建议**：
1. 统一为 `--stem-*` 命名体系（STEM为K12学习端主设计系统）
2. 创建兼容性别名：`--matux-*` → `--stem-*`
3. 更新所有组件引用统一前缀

---

### 2.3 对比度不足（P1-MAJOR）

**问题描述**：多个位置的文字/图标与背景对比度不足，影响可读性。

**具体问题**：

| 文件 | 行号 | 问题描述 | 当前值 | WCAG要求 |
|------|------|---------|--------|---------|
| `register.component.scss` | L80 | 输入框placeholder | `#a0a0a7` | ≥4.5:1 |
| `login.component.scss` | L110 | footer文字 | `#64748b` | ≥4.5:1 |
| `creativity-engine.component.scss` | L276 | 空状态文字 | `#999` | ≥4.5:1 |
| `offline-dashboard.component.scss` | L271 | 提示列表文字 | `#555` | ≥4.5:1 |

**修复建议**：
1. 使用 `student-dashboard.component.scss` L8-21 的变量定义方法
2. placeholder颜色使用 `$stem-gray-400` (#a8a29e) 或更深的颜色
3. 建议placeholder颜色：`#78716c` 或 `#57534e`

---

### 2.4 颜色语义冲突（P1-MAJOR）

**问题描述**：同一语义使用不同颜色，造成认知混乱。

**具体问题**：

| 语义 | 文件 | 颜色 | 问题 |
|------|------|------|------|
| 成功状态 | `register.component.scss` L168 | `#2e7d32` | Material绿色 |
| 成功状态 | `offline-dashboard.component.scss` L168 | `#2e7d32` | Material绿色 |
| 成功状态 | `_colors.scss` | `#10b981` | Emerald绿色 |
| 成功状态 | `_stem-tokens.scss` | `#059669` | Emerald绿色 |
| 主品牌色 | `login.component.scss` | `#3b82f6` | Blue-500 |
| 主品牌色 | `student-dashboard.component.scss` | `#059669` | Emerald-600 |

**修复建议**：
1. 统一状态色语义（成功=绿，警告=黄，错误=红）
2. 建议使用 STEM 设计系统状态色：
   - 成功：`$stem-success: #059669`
   - 警告：`$stem-warning: #f59e0b`
   - 错误：`$stem-error: #ef4444`

---

## 三、P2 级问题（优化）

### 3.1 样式重复代码（P2-OPTIMIZE）

**问题描述**：多个组件包含高度相似的样式代码，可抽取为共享样式。

**重复模式**：

```scss
// 以下代码在7个组件中重复出现
$stem-primary: #059669;
$stem-primary-light: #10b981;
$stem-primary-dark: #047857;
$stem-secondary: #0ea5e9;
$stem-accent: #06b6d4;
$stem-success: #22c55e;
$stem-warning: #f59e0b;
$stem-error: #ef4444;
$stem-radius-sm: 12px;
$stem-radius-md: 20px;
$stem-radius-lg: 9999px;
$stem-shadow: 0 4px 20px rgb(5 150 105 / 15%);
$stem-shadow-hover: 0 8px 30px rgb(5 150 105 / 20%);
$stem-transition: 250ms cubic-bezier(0.4, 0, 0.2, 1);
```

**受影响组件**：
- `user-page-layout.component.scss`
- `emotional-companion.component.scss`
- `blockly-workspace.component.scss`
- `token-balance.component.scss`
- `opensciedu-catalog.component.scss`

**修复建议**：
1. 创建共享 SCSS 文件 `g:\iMato\src\styles\shared\_stem-theme.scss`
2. 组件中通过 `@use` 导入：`@use '../../styles/shared/stem-theme';`
3. 使用 `forward` 导出所有变量

---

### 3.2 圆角系统不一致（P2-OPTIMIZE）

**问题描述**：不同组件使用的圆角值不统一。

**圆角值对比**：

| 组件 | 卡片圆角 | 按钮圆角 | 输入框圆角 |
|------|---------|---------|-----------|
| `student-dashboard.component.scss` | 20px | 12px | - |
| `login.component.scss` | 16px | 9999px | 12px |
| `register.component.scss` | - | 8px | 8px |
| `creativity-engine.component.scss` | 4px | - | - |
| `_matux-tokens.scss` | 16px (1rem) | 9999px | 12px (0.75rem) |
| `_stem-tokens.scss` | 20px (1.25rem) | 9999px | 16px |

**修复建议**：
1. 统一使用 `_stem-tokens.scss` 定义的系统圆角值
2. 组件中引用变量而非硬编码：`border-radius: $stem-radius-md;`

---

### 3.3 阴影层级不规范（P2-OPTIMIZE）

**问题描述**：部分组件使用了未在设计系统中定义的阴影值。

**问题位置**：

| 文件 | 行号 | 当前阴影 | 建议阴影 |
|------|------|---------|---------|
| `login.component.scss` | L46 | `0 8px 24px rgb(59 130 246 / 30%)` | `$stem-shadow` |
| `student-dashboard.component.scss` | L49 | `var(--stem-shadow-sm, ...)` | `$stem-shadow-sm` |
| `creativity-engine.component.scss` | 多个位置 | `0 4px 12px rgb(0 0 0 / 15%)` | `$stem-shadow-sm` |

**修复建议**：
1. 使用 `_stem-tokens.scss` 中定义的阴影变量
2. 禁止在组件中硬编码阴影值

---

## 四、问题统计汇总

### 4.1 按优先级统计

| 优先级 | 问题数量 | 描述 |
|--------|---------|------|
| P0 | 2 | 设计系统双轨、变量重复定义 |
| P1 | 4 | 硬编码颜色、命名不统一、对比度不足、语义冲突 |
| P2 | 3 | 样式重复、圆角不一致、阴影不规范 |

### 4.2 按文件统计

| 文件 | 问题数 | 优先级 |
|------|--------|--------|
| `login.component.scss` | 3 | P0, P1 |
| `register.component.scss` | 3 | P0, P1 |
| `creativity-engine.component.scss` | 3 | P1 |
| `offline-dashboard.component.scss` | 3 | P1 |
| `plugin-store.component.scss` | 2 | P0, P1 |
| `student-dashboard.component.scss` | 2 | P0, P1 |
| `user-page-layout.component.scss` | 2 | P0 |
| `emotional-companion.component.scss` | 1 | P0 |
| `blockly-workspace.component.scss` | 1 | P0 |
| `token-balance.component.scss` | 1 | P0 |
| `status-bar.component.scss` | 1 | P0 |
| `user-navbar.component.scss` | 1 | P0 |
| `opensciedu-catalog.component.scss` | 1 | P0 |

---

## 五、修复执行计划

### Phase 1: 设计系统统一（P0）
1. 创建统一 CSS 变量文件 `g:\iMato\src\styles\_css-variables.scss`
2. 创建共享 STEM SCSS 文件 `g:\iMato\src\styles\shared\_stem-theme.scss`
3. 更新所有组件导入共享文件

### Phase 2: 颜色规范化（P1）
1. 替换所有硬编码颜色为 CSS 变量
2. 统一状态色语义
3. 修复对比度问题

### Phase 3: 样式优化（P2）
1. 清理重复样式代码
2. 统一圆角系统
3. 规范化阴影使用

---

**审查结论**：当前桌面端存在严重的设计系统混乱问题，需要系统性重构以实现视觉统一。建议优先处理P0级问题，再逐步优化P1/P2级问题。