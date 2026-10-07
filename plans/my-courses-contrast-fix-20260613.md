# iMato "我的课程"页面对比度全面修复实施计划

## Context

用户要求使用与第一个页面（学生仪表板）相同的检查方法，对第二个页面（我的课程 `/courses`）进行全面的对比度检查。

**已完成的全量审计**（详见 [我的课程页面对比度审计报告_20260613.md](file:///g:/iMato/reports/我的课程页面对比度审计报告_20260613.md)）发现：

- **23 处对比度问题**：8 高优先级 + 11 中优先级 + 4 低优先级
- **第一个报告的 4 大系统盲区**：渐变背景未审计、文字对比度未审计、hover/active 状态引入回归、辅助组件未审计

**修复目标**：
1. 修复全部 23 处问题
2. 添加 stylelint 防护规则，避免同类问题重复出现

---

## 待修复问题清单（按优先级）

### 🔴 高优先级（8 处）— 必修
| # | 位置 | 元素 | 当前对比度 | 失败标准 |
|---|------|------|-----------|----------|
| 1 | [my-courses.scss:91-107](file:///g:/iMato/src/app/user/components/my-courses/my-courses.component.scss#L91-L107) | `.course-icon` mat-icon | 渐变底端 2.54:1 | WCAG 1.4.11 |
| 2 | [my-courses.scss:201-210](file:///g:/iMato/src/app/user/components/my-courses/my-courses.component.scss#L201-L210) | `.continue-btn` 文字 | 渐变底端 2.54:1 | WCAG AA 4.5:1 |
| 3 | [my-courses.scss:337-344](file:///g:/iMato/src/app/user/components/my-courses/my-courses.component.scss#L337-L344) | `.primary-badge` 文字 | 渐变底端 2.54:1 | WCAG AA 4.5:1 |
| 4 | [my-courses.scss:454-462](file:///g:/iMato/src/app/user/components/my-courses/my-courses.component.scss#L454-L462) | `.enroll-btn` 文字 | 渐变底端 2.54:1 | WCAG AA 4.5:1 |
| 5 | [user-navbar.scss:92-95](file:///g:/iMato/src/app/user/components/user-navbar/user-navbar.component.scss#L92-L95) | `.nav-link.active` | 3.13:1 | WCAG AA 4.5:1 |
| 6 | [user-navbar.scss:155-169](file:///g:/iMato/src/app/user/components/user-navbar/user-navbar.component.scss#L155-L169) | `.user-avatar-small` mat-icon | 2.87:1 | WCAG 1.4.11 |
| 7 | [user-footer.ts:86-92](file:///g:/iMato/src/app/user/components/user-footer/user-footer.component.ts#L86-L92) | `.footer-copyright` | 2.52:1 | WCAG AA 4.5:1 |
| 8 | [user-navbar.scss:62-77](file:///g:/iMato/src/app/user/components/user-navbar/user-navbar.component.scss#L62-L77) | `.nav-link` 文字 | 3.43-4.97 | WCAG AA 4.5:1 |

### 🟡 中优先级（11 处）— 应修
| # | 位置 | 元素 | 当前对比度 | 修复策略 |
|---|------|------|-----------|----------|
| 9 | my-courses.scss:81-83 | `.course-card.completed` opacity 0.85 | 多色降低 | 改用 `background` 表示完成态 |
| 10 | my-courses.scss:152-162 | `.progress-value` | 3.79:1 | 改用 `$stem-primary-dark` |
| 11 | my-courses.scss:164-166 | `.progress-value.complete` | 3.79:1 | 同上 |
| 12 | my-courses.scss:186-189 | `.source-tag` | 3.35:1 | 改用 `$stem-primary-dark` |
| 13 | my-courses.scss:440-446 | `.tag-recommend` | 3.35:1 | 同上 |
| 14 | user-page-layout.scss:144-147 | `.ai-message.user .ai-bubble` | 渐变底端 3.79:1 | 已用深绿渐变，检查 |
| 15 | user-page-layout.scss:171-188 | `.status-bar` 文字 | 3.43:1 | 背景改 `$stem-primary-dark` |
| 16 | user-navbar.scss:87-90 | `.nav-link:hover` | 3.31:1 | 移除白叠加，改用阴影/边框 |
| 17 | user-navbar.scss:121-135 | `.notification-badge` | 3.77:1 | 改用 `#dc2626` (4.83:1) |
| 18 | user-navbar.scss:274-276 | `.search-input::placeholder` | 2.57:1 | 改用 `--color-gray-500` |
| 19 | user-navbar.scss:278-284 | `.search-hint` | 2.35:1 | 改用 `--color-gray-600` |

### 🟢 低优先级（4 处）— 建议
| # | 位置 | 元素 | 当前对比度 | 备注 |
|---|------|------|-----------|------|
| 20 | my-courses.scss:34-41 | `.page-title` | 3.67:1 | 28px 700 大文本通过 AAA 边缘 |
| 21 | user-navbar.scss:221-226 | `.mobile-menu-header` | 4.55:1 | 勉强 AA |
| 22 | user-navbar.scss:205-213 | `.user-type-badge` | 4.39:1 | 接近 AA |
| 23 | user-footer.ts:94-96 | `.divider` | 1.26:1 | 装饰性 |

---

## 实施步骤

### 任务 1：扩展 Design Tokens

**修改文件**：[_stem-theme.scss](file:///g:/iMato/src/styles/shared/_stem-theme.scss)

在 STEM 渐变系统区域新增：
```scss
// 安全渐变（深色方向，保证白字对比度 ≥ 3.79:1）
$stem-gradient-primary-safe: linear-gradient(135deg, $stem-primary 0%, $stem-primary-dark 100%);
$stem-gradient-nature-safe: linear-gradient(135deg, $stem-primary 0%, $stem-primary-dark 100%);
```

### 任务 2：修复 my-courses 主页面（修复 #1-4, #9-13, #20）

**修改文件**：[my-courses.component.scss](file:///g:/iMato/src/app/user/components/my-courses/my-courses.component.scss)

1. **`.course-icon`** (line 91-107)：渐变改用 `$stem-primary → $stem-primary-dark`（白色 icon 3.79-5.49:1）
2. **`.continue-btn`** (line 201-210)：渐变改用 `$stem-primary → $stem-primary-dark`
3. **`.primary-badge`** (line 337-344)：渐变改用 `$stem-primary → $stem-primary-dark`
4. **`.enroll-btn`** (line 454-462)：渐变改用 `$stem-primary → $stem-primary-dark`
5. **`.course-card.completed`** (line 81-83)：移除 `opacity: 0.85`，改用 `background: #f5f5f4` + `border-left: 3px solid $stem-success`
6. **`.progress-value`** (line 152-162)：`color: $stem-primary-dark`
7. **`.progress-value.complete`** (line 164-166)：`color: $stem-success` → `$stem-primary-dark`（同色加深）
8. **`.source-tag`** (line 186-189)：`color: $stem-primary-dark`
9. **`.tag-recommend`** (line 440-446)：`color: $stem-primary-dark`
10. **`.page-title`** (line 34-41)：`color: $stem-primary-dark`

### 任务 3：修复 user-navbar（修复 #5, #6, #8, #16-19, #21, #22）

**修改文件**：[user-navbar.component.scss](file:///g:/iMato/src/app/user/components/user-navbar/user-navbar.component.scss)

1. **`.nav-link`** (line 62-77)：`color: rgb(255 255 255 / 100%)`（100% 纯白）
2. **`.nav-link:hover`** (line 87-90)：移除 `background: rgb(255 255 255 / 10%)`，改用 `box-shadow: inset 0 0 0 1px rgb(255 255 255 / 30%)`
3. **`.nav-link.active`** (line 92-95)：`background: $stem-primary-dark`（白色文字 5.49:1）
4. **`.user-avatar-small`** (line 155-169)：`background: $stem-primary-dark`，加 `border: 2px solid white`
5. **`.notification-badge`** (line 121-135)：`background: #dc2626` (4.83:1)
6. **`.search-input::placeholder`** (line 274-276)：`color: var(--color-gray-500, #64748b)` (4.92:1)
7. **`.search-hint`** (line 278-284)：`color: var(--color-gray-600, #475569)` (5.74:1)
8. **`.mobile-menu-header`** (line 221-226)：`color: var(--color-text-secondary, #57534e)` (7.63:1)
9. **`.user-type-badge`** (line 205-213)：`color: var(--color-text-secondary, #57534e)`

### 任务 4：修复 user-page-layout（修复 #14, #15）

**修改文件**：[user-page-layout.component.scss](file:///g:/iMato/src/app/user/components/user-page-layout/user-page-layout.component.scss)

1. **`.status-bar`** (line 171-188)：`background: $stem-primary-dark` + `color: white` (5.49:1)
2. **`.ai-message.user .ai-bubble`** (line 144-147)：渐变已用深色方向，确认无问题

### 任务 5：修复 user-footer（修复 #7, #23）

**修改文件**：[user-footer.component.ts](file:///g:/iMato/src/app/user/components/user-footer/user-footer.component.ts)

1. **`.footer-copyright`** (line 86-92)：`color: var(--color-text-secondary, #57534e)` (7.63:1)
2. **`.divider`** (line 94-96)：`color: var(--color-gray-500, #64748b)` (4.92:1)

### 任务 6：添加 stylelint 防护规则

**修改文件**：[.stylelintrc.js](file:///g:/iMato/.stylelintrc.js)

新增以下规则到 `rules` 对象：

```js
// 1. 禁止低对比度的弱化白（仅在 hover/disabled 状态允许）
'color-no-low-contrast': true, // 需安装 stylelint-plugin-wcag

// 2. 禁止 opacity: 0.[5-8] 形式（影响文字对比度）
// 需用 declaration-property-value-allowed-list 或自定义规则

// 3. 禁止 $stem-primary-light 作为 linear-gradient 终点
// （渐变底端对比度仅 2.54:1）
// 需用自定义 stylelint 插件或 regex pattern
```

实际可立即添加的规则（不需要新插件）：
- 在 `scale-unlimited/declaration-strict-value` 的 `ignoreValues` 中移除 `white` / `#fff`，强制使用 token
- 添加 `declaration-property-value-disallowed-list` 禁止特定 pattern

### 任务 7：验证

1. **构建验证**：
   ```powershell
   cd g:\iMato
   npx ng build --configuration development --source-map=false
   ```
   预期：构建成功，无新增 SCSS/TypeScript 错误

2. **Stylelint 验证**：
   ```powershell
   cd g:\iMato
   npx stylelint "src/**/*.scss"
   ```
   预期：无新增高优先级警告

3. **残留低对比度扫描**：
   ```powershell
   # 搜索 rgb(255 255 255 / [5-8]\d%) 弱化白
   Get-ChildItem -Path "src" -Recurse -Include "*.scss" | Select-String -Pattern "rgb\(255 255 255 / (5|6|7|8)\d%\)"
   ```
   预期：仅剩允许的 hover/disabled/装饰性用途

4. **视觉验证**（手动 dev 环境）：
   - 启动后端 + 前端
   - 登录 test_student
   - 访问 `/courses`
   - 截图核对 navbar、status-bar、course card、source card、recommendation card、footer

---

## 关键文件清单

| 类别 | 文件路径 | 修改类型 |
|------|---------|---------|
| Token | [src/styles/shared/_stem-theme.scss](file:///g:/iMato/src/styles/shared/_stem-theme.scss) | 新增 1-2 个 SCSS 变量 |
| 主页面 | [src/app/user/components/my-courses/my-courses.component.scss](file:///g:/iMato/src/app/user/components/my-courses/my-courses.component.scss) | 修改 10 处 |
| 顶部导航 | [src/app/user/components/user-navbar/user-navbar.component.scss](file:///g:/iMato/src/app/user/components/user-navbar/user-navbar.component.scss) | 修改 9 处 |
| 页面布局 | [src/app/user/components/user-page-layout/user-page-layout.component.scss](file:///g:/iMato/src/app/user/components/user-page-layout/user-page-layout.component.scss) | 修改 1-2 处 |
| 底部导航 | [src/app/user/components/user-footer/user-footer.component.ts](file:///g:/iMato/src/app/user/components/user-footer/user-footer.component.ts) | 修改 2 处（内嵌 CSS） |
| 防护规则 | [.stylelintrc.js](file:///g:/iMato/.stylelintrc.js) | 新增规则 |

**总计**：0 个新建，6 个修改，预计净增约 30-50 行（多数为注释 + 颜色值替换）

---

## 范围外（不在本次实施）

- ❌ 不重新审计第一个页面（学生仪表板）
- ❌ 不修改其他共享页面（learning-profile、achievements 等）
- ❌ 不调整暗色模式
- ❌ 不补充修复第一个报告的盲区（user-avatar-small、notification-badge、search-placeholder 等虽然发现了，但属于 #5, #6, #17, #18, #19，本计划已包含）

---

## 验收清单

- [ ] 23 处问题全部修复
- [ ] Angular 构建通过
- [ ] stylelint 防护规则添加
- [ ] 残留低对比度扫描通过
- [ ] 视觉验证（dev 环境手动）

---

**计划创建时间**：2026-06-13
**实施预计时间**：30-60 分钟
**依赖**：参考报告 `g:\iMato\reports\我的课程页面对比度审计报告_20260613.md`
