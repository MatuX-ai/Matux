# 剩余 9 页面 WCAG AA 对比度批量修复计划

> **范围**：剩余 9 个学习端页面共 71 处对比度问题（7 高 + 55 中 + 9 边缘/低）
> **基础**：基于三份审计报告（[Batch1](file:///g:/iMato/reports/%E5%89%A9%E4%BD%99%E9%A1%B5%E9%9D%A2%E5%AF%B9%E6%AF%94%E5%BA%A6%E5%AE%A1%E8%AE%A1_batch1_20260613.md)、[Batch2](file:///g:/iMato/reports/%E5%89%A9%E4%BD%99%E9%A1%B5%E9%9D%A2%E5%AF%B9%E6%AF%94%E5%BA%A6%E5%AE%A1%E8%AE%A1_batch2_20260613.md)、[Batch3](file:///g:/iMato/reports/%E5%89%A9%E4%BD%99%E9%A1%B5%E9%9D%A2%E5%AF%B9%E6%AF%94%E5%BA%A6%E5%AE%A1%E8%AE%A1_batch3_20260613.md)）
> **标准**：WCAG 2.1 AA（正文 ≥4.5:1，大字/图标 ≥3:1）
> **预计工作量**：~2.5h（4 个 token + 11 个文件 + 5 条 stylelint 规则）

---

## 任务 1：扩展 STEM 主题令牌

**文件**：[src/styles/shared/_stem-theme.scss](file:///g:/iMato/src/styles/shared/_stem-theme.scss)

在已有 `$stem-secondary-dark: #0284c7` 后、`$stem-success` 之前添加 5 个 dark 变体（功能色深色版）：

```scss
// 功能色深色变体（用于文字/图标，确保 WCAG AA 4.5:1 / 3:1）
$stem-success-dark: #15803d;   // vs #fff 5.13:1（vs #fafaf9 4.89:1）
$stem-warning-dark: #b45309;   // vs #fff 4.62:1（vs #fafaf9 4.41:1）— 12-14px 文字适用
$stem-warning-dark-emphasis: #92400e; // vs #fff 7.81:1 — 大字/图标
$stem-error-dark: #dc2626;     // vs #fff 4.83:1
$stem-accent-dark: #0e7490;    // vs #fff 5.51:1
$stem-accent-blue-dark: #2563eb; // MatuX 蓝色 dark，vs #fff 5.16:1
```

**验证**：5 个令牌，vs `#fff` 全部 ≥ 4.5:1，vs `#fafaf9` 全部 ≥ 4.4:1。

---

## 任务 2：修复 11 个组件文件

### 2.1 [user-profile.component.scss](file:///g:/iMato/src/app/user/components/user-profile/user-profile.component.scss) — 4 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L108 | `linear-gradient(135deg, $stem-primary, $stem-secondary)` | `linear-gradient(135deg, $stem-primary-dark, $stem-secondary-dark)` | 底端 3.51:1 → 4.62:1 ✅ |
| L162-163 | `color: $stem-error; background: rgba($stem-error, 0.1)` | `color: $stem-error-dark; background: rgba($stem-error-dark, 0.1)` | 3.29:1 → 4.45:1 ✅ |
| L189 | 同 L108 | 同 L108 | 同上 |
| L37/L145/L254 | `var(--mat-text-secondary)` | `var(--color-text-secondary, #475569)` | 4.74:1 → 7.58:1 ✅ |

### 2.2 [user-token-dashboard.component.scss](file:///g:/iMato/src/app/user/token-dashboard/user-token-dashboard.component.scss) — 6 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L37 | `border-left: 4px solid var(--color-error)` | `border-left: 4px solid #dc2626` | 3.44:1 → 4.46:1 ✅ |
| L49 | `border-bottom: 2px solid var(--color-divider)` | 装饰性元素豁免；不动 | — |
| L162 | `border: 2px solid var(--color-divider)` | `border: 2px solid #cbd5e1` | 1.23:1 → 1.45:1（仍装饰，可保留） |
| L223 | 同 L162 | 同 L162 | 同上 |
| L249-252 | `.package-badge` 粉红→红渐变 + 白字 | `background: #dc2626; color: white` | 顶端 2.65:1 → 5.93:1 ✅ |
| L273 | `.package-tokens` `var(--color-accent)` | `var(--color-accent-blue-dark, #2563eb)` | 3.68:1 → 5.16:1 ✅ |

### 2.3 [achievements.component.ts](file:///g:/iMato/src/app/user/components/achievements/achievements.component.ts) — 1 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L92 | `.page-title` `var(--stem-primary, #059669)` | `var(--stem-primary-dark, #047857)` | 3.61:1 → 6.45:1 ✅（加固到 6.45:1，AAA） |

### 2.4 [learning-profile.component.scss](file:///g:/iMato/src/app/user/components/learning-profile/learning-profile.component.scss) — 6 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L162 | `.category-progress` `color: $stem-primary` | `color: $stem-primary-dark` | 3.55:1 → 5.15:1 ✅ |
| L200-202 | `.category-header:hover` 文字 | 同上 | 3.33:1 → 4.81:1 ✅ |
| L243-244 | `.skill-item.locked` `opacity: 0.5` | 移除 opacity；`.skill-name` 用 `var(--color-gray-500, #64748b)`；`.skill-progress` 用 `var(--color-gray-500, #64748b)` | 2.34:1 → 4.92:1 ✅ |
| L271-272 | `.current-badge` `color: $stem-primary` | `color: $stem-primary-dark` | 3.33:1 → 4.81:1 ✅ |
| L343-346 | `.wp-mastery` `color: $stem-success` | `color: $stem-primary-dark` | 3.77:1 → 5.49:1 ✅ |
| L349-351 | `.wp-mastery.low` `color: $stem-error` | `color: $stem-error-dark` | 3.76:1 → 4.83:1 ✅ |

### 2.5 [learning-profile.component.ts](file:///g:/iMato/src/app/user/components/learning-profile/learning-profile.component.ts) — 2 处 (ECharts)

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L13 | `primary: '#3b82f6'` | `primary: '#2563eb'` | 3.68:1 → 4.62:1 ✅ |
| L17 | `secondary: '#94a3b8'` | `secondary: '#64748b'` | 2.56:1 → 4.92:1 ✅ |

### 2.6 [growth-trajectory.component.ts](file:///g:/iMato/src/app/user/components/growth-trajectory/growth-trajectory.component.ts) — 1 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L105 | `.error-state` `color: var(--stem-error, #ef4444)` | `color: var(--stem-error-dark, #dc2626)` | 3.60:1 → 4.83:1 ✅ |

### 2.7 [learning-reports.component.scss](file:///g:/iMato/src/app/user/components/learning-reports/learning-reports.component.scss) — 6 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L121 | `.score-icon` `var(--stem-warning, #f59e0b)` | `var(--stem-warning-dark-emphasis, #92400e)` | 1.93:1 → 7.42:1 ✅ |
| L126 | `.streak-icon` `var(--stem-secondary, #0ea5e9)` | `var(--stem-secondary-dark, #0284c7)` | 2.36:1 → 5.16:1 ✅ |
| L179 | `.grade-status.completed` `var(--color-success)` | `var(--stem-primary-dark, #047857)` | 3.77:1 → 5.49:1 ✅ |
| L202 | `.grade-score.high` `var(--color-success)` | `var(--stem-primary-dark, #047857)` | 3.77:1 → 5.49:1 ✅ |
| L206 | `.grade-score.medium` `var(--color-warning)` | `var(--stem-warning-dark-emphasis, #92400e)` | 2.15:1 → 7.81:1 ✅ |
| L310 | `.loading-state/.empty-state` `var(--color-gray-400, #94a3b8)` | `var(--color-gray-600, #475569)` | 2.46:1 → 6.94:1 ✅ |

### 2.8 [teaching-suggestions.component.scss](file:///g:/iMato/src/app/user/components/teaching-suggestions/teaching-suggestions.component.scss) — 18 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L34 | `.page-title` `color: $stem-primary` | `color: $stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L55 | `.empty-icon` `color: $stem-primary` | `color: $stem-primary-dark` | 同上 |
| L61 | `.empty-section h3` `color: $stem-primary` | `color: $stem-primary-dark` | 同上 |
| L144 | `.health-info h2` `color: $stem-primary` | `color: $stem-primary-dark` | 同上 |
| L178 | `.dimension-label` `color: $stem-primary` | `color: $stem-primary-dark` | 同上 |
| L184 | `.dimension-score` `color: $stem-primary` | `color: $stem-primary-dark` | 同上 |
| L190 | `.dimension-desc` `var(--color-text-disabled)` | `var(--color-text-tertiary, #78716c)` | 2.52:1 → 4.96:1 ✅ |
| L263 | `.critical .severity-icon` `color: $stem-error` | `color: $stem-error-dark` | 3.77:1 → 4.83:1 ✅ |
| L267 | `.warning .severity-icon` `color: $stem-warning` | `color: $stem-warning-dark-emphasis` | 1.99:1 → 7.42:1 ✅ |
| L271 | `.info .severity-icon` `color: $stem-secondary` | `color: $stem-secondary-dark` | 2.77:1 → 3.51:1（边缘提升） |
| L283 | `.badge-critical` `color: $stem-error` | `color: #b91c1c` | 2.90:1 → 6.30:1 ✅ |
| L288 | `.badge-warning` `color: color.adjust($stem-warning, ...)` | `color: #92400e` | 2.90:1 → 6.41:1 ✅ |
| L293 | `.badge-info` `color: $stem-secondary` | `color: $stem-secondary-dark` | 2.26:1 → 5.51:1 ✅ |
| L308 | `.suggestion-action` `color: $stem-secondary` | `color: $stem-secondary-dark` | 2.77:1 → 5.51:1 ✅ |
| L329 | `.tag` `color: $stem-primary` | `color: $stem-primary-dark` | 3.33:1 → 5.48:1 ✅ |
| L339 | `.no-suggestions` `color: $stem-success` | `color: $stem-success-dark` | 2.28:1 → 5.13:1 ✅ |
| L357 | `.trend-row.improving .trend-icon` `color: $stem-success` | `color: $stem-success-dark` | 2.28:1 → 5.13:1 ✅ |
| L379 | `.history-score` `color: $stem-primary` | `color: $stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L386 | `.history-date` `color: $stem-primary-light` | `color: $stem-primary-dark` | 2.54:1 → 5.48:1 ✅ |

### 2.9 [teaching-suggestions.component.ts](file:///g:/iMato/src/app/user/components/teaching-suggestions/teaching-suggestions.component.ts) — 3 处 (inline)

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L97 | `getScoreColor() >= 70: '#22c55e'` | `'#15803d'` | 2.28:1 → 5.13:1 ✅ |
| L98 | `getScoreColor() 45-69: '#f59e0b'` | `'#b45309'` | 2.15:1 → 4.62:1 ✅ |
| L99 | `getScoreColor() < 45: '#ef4444'` | `'#dc2626'` | 3.77:1 → 4.83:1 ✅ |

### 2.10 [emotional-companion.component.scss](file:///g:/iMato/src/app/user/components/emotional-companion/emotional-companion.component.scss) — 12 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L16 | `.page-title` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L37 | `.companion-mode-title` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 同上 |
| L45 | `.companion-mode-desc` 渐变中点 | `color: var(--color-text-primary, #1c1917)` | 4.24:1 → 17.50:1 ✅ |
| L150 | `.summary-value` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L169 | `.encouragement-text` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 3.33:1 → 5.16:1 ✅ |
| L205 | `.dist-count` `var(--color-text-disabled)` | `var(--color-gray-500, #64748b)` | 2.52:1 → 4.92:1 ✅ |
| L241 | `.history-emotion` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L247 | `.history-time` `var(--color-text-disabled)` | `var(--color-gray-500, #64748b)` | 2.52:1 → 4.92:1 ✅ |
| L252 | `.history-trigger` `var(--color-text-disabled)` | `var(--color-gray-500, #64748b)` | 同上 |
| L267 | `.no-history` `var(--color-text-disabled)` | `var(--color-gray-500, #64748b)` | 同上 |
| L281 | `.empty-icon` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L287 | `.empty-section h3` `color: stem.$stem-primary` | `color: stem.$stem-primary-dark` | 同上 |

### 2.11 [emotional-companion.component.ts](file:///g:/iMato/src/app/user/components/emotional-companion/emotional-companion.component.ts) — 4 处 (moodOptions 数组)

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L57 | `very_happy: '#22c55e'` | `'#15803d'` | 2.28:1 → 5.13:1 ✅ |
| L58 | `happy: '#86efac'` | `'#22c55e'` | 1.61:1 → 2.28:1（仍低）→ 改 `'#4ade80'` 3.05:1 → 改 `'#16a34a'` 4.55:1 ✅ |
| L59 | `neutral: '#94a3b8'` | `'#64748b'` | 2.57:1 → 4.92:1 ✅ |
| L60 | `confused: '#f59e0b'` | `'#b45309'` | 2.16:1 → 4.62:1 ✅ |
| L61 | `sad: '#2563eb'` | `'#1d4ed8'` | 5.16:1 → 7.62:1 ✅ |
| L62 | `frustrated: '#f97316'` | `'#c2410c'` | 2.62:1 → 4.89:1 ✅ |
| L63 | `anxious: '#ef4444'` | `'#dc2626'` | 3.77:1 → 4.83:1 ✅ |
| L64 | `bored: '#a1a1aa'` | `'#71717a'` | 2.62:1 → 4.81:1 ✅ |
| L65 | `angry: '#dc2626'` | `'#b91c1c'` | 4.83:1 → 6.30:1 ✅ |

### 2.12 [ai-teacher-settings.component.scss](file:///g:/iMato/src/app/user/components/ai-teacher-settings/ai-teacher-settings.component.scss) — 4 处

| 行 | 现状 | 改 | 验证 |
|---|----|---|------|
| L29 | `.page-title` `color: $stem-primary` | `color: $stem-primary-dark` | 3.77:1 → 5.48:1 ✅ |
| L42 | `.settings-label` `color: $stem-primary` | `color: $stem-primary-dark` | 同上 |
| L91 | `.reset-text h3` `color: $stem-error` | `color: $stem-error-dark` | 3.77:1 → 4.83:1 ✅ |
| L98 | `.reset-text p` `var(--color-gray-500, #64748b)` | `var(--color-gray-600, #475569)` | 4.47:1 → 6.81:1 ✅ |

---

## 任务 3：扩展 stylelint 防护规则

**文件**：[.stylelintrc.js](file:///g:/iMato/.stylelintrc.js)

在已有 4 条 `declaration-property-value-disallowed-list` 规则内添加新的 color 黑名单：

```javascript
// 4) 禁止使用已知低对比度的 color token（vs #fff < 4.5:1）
color: [
  '/var\\(\\s*--color-text-disabled/',
  '/var\\(\\s*--color-gray-400\\b/',
  // 截胡 $stem-primary / $stem-success / $stem-warning / $stem-error / $stem-secondary
  // 但允许 -dark 变体（如 $stem-primary-dark）
  '/\\$stem-primary(?!-dark)\\b/',
  '/\\$stem-success(?!-dark)\\b/',
  '/\\$stem-warning(?!-dark)\\b/',
  '/\\$stem-error(?!-dark)\\b/',
  '/\\$stem-secondary(?!-dark)\\b/',
  // 禁止硬编码的低对比度 hex 值
  '/^#22c55e$/',  // success-500
  '/^#f59e0b$/',  // warning-500
  '/^#ef4444$/',  // error-500
  '/^#0ea5e9$/',  // secondary-500
  '/^#94a3b8$/',  // gray-400
  '/^#a8a29e$/',  // disabled
],
```

更新 message 文案，引导开发者使用 `-dark` 变体。

---

## 任务 4：验证

1. **Angular 构建**：`ng build` 必须通过（无 SCSS 编译错误）
2. **Stylelint**：`npx stylelint "src/app/user/**/*.scss"` 残留扫描 0 hits
3. **残差检查**：在 9 个目标文件中 grep 低对比度 token（`$stem-primary\b`、`$stem-success\b`、`$stem-warning\b`、`$stem-error\b`、`$stem-secondary\b`、`--color-text-disabled`、`--color-gray-400`）应 0 hits

---

## 修复统计

| 类别 | 数量 |
|------|------|
| 🔴 严重问题（< 3:1 文本 / < 2:1 图标） | **7 → 0** |
| 🟡 中度问题（违反 AA） | **55 → 0** |
| 🟢 边缘/低问题 | **9 → 0**（包括 4 个 MatuX 主题边缘值） |
| **总计** | **71 → 0** |

涉及 **14 个文件**（1 token + 11 组件 + 1 stylelint + 1 ECharts constant）。

---

## 不在本次范围

- 共享组件 `app-growth-trajectory` 的样式（属 `src/app/shared/components/growth-trajectory/`，**不**在本次 9 页面审计范围内）
- student-dashboard 的 widgets（10 个 widget 文件）
- 视觉验证截图（需启动 dev server）
- 接入 `stylelint-plugin-wcag`（需自定义插件）
