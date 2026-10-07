# MatuX 桌面端缺口功能迭代开发计划

> **编制日期**：2026-06-09  
> **基于**：代码审计结果 + MatuX_桌面端缺口功能开发计划  
> **审计角色**：项目经理 + Senior Engineer 审计视角

---

## 一、审计结论摘要

| Phase | 功能 | 计划状态 | 审计完成度 | 阻塞级缺陷 | 判定 |
|-------|------|----------|-----------|-----------|------|
| Phase 1 | OpenSciEDU 公共课程 (F-18) | P0 | **65%** | 1 | 需补全 |
| Phase 2 | Blockly 可视化编程 (F-05) | P0 | **20%** | 4 | 需重做 |
| Phase 3 | electron-updater 自动更新 (F-16) | P2 | **55%** | 2 | 需修复+补全 |
| Phase 4 | .imato 文件关联 (F-17) | P2 | **80%** | 1 | 接近完成 |

---

## 二、迭代排期

| 迭代 | 周期 | 目标 | 核心交付 |
|------|------|------|----------|
| **Sprint 0** | 1 天 | 全 Phase P0 级 BUG 修复 | 消除 7 个阻塞级缺陷 |
| **Sprint 1** | 1 周 | Blockly 真实集成 | blockly npm 安装 + 真实工作区 |
| **Sprint 2** | 1 周 | OpenSciEDU 离线缓存 + 自动更新补全 | 验收标准达标 |
| **Sprint 3** | 0.5 周 | 文件关联收尾 + 集成测试 | 全 Phase 验收通过 |

---

## 三、Sprint 0：P0 级 BUG 修复（1 天）

### Task 0.1：修复 OpenSciEDU Mock 服务竞态条件

**文件**：`src/app/core/services/opensciedu.service.ts`

**问题**：`getMockService()` 使用异步 `import().then()` 赋值模块级变量（L200），但 `createMockServiceInstance()` 同步读取（L241）。首次调用时 Promise 未 resolve，返回 null，导致 API 不可用时**所有 mock 降级全部静默失败**。

**修复方案**：
```
// 改为静态导入或同步 require
import { OpenSciEDUMockService as MockSvc } from './opensciedu-mock.service';
```
删除 `getMockService()` 方法，`createMockServiceInstance()` 直接 `new MockSvc()`。

**验收**：断网状态下，调用 `getPublicCourses()` 能返回模拟课程数据。

---

### Task 0.2：安装 blockly npm 依赖

**文件**：`package.json`

**问题**：`blockly` 包未出现在 `dependencies` 中。所有 Blockly 相关代码均为空壳。

**修复方案**：
```
npm install blockly@^11.0.0 --save
```

**验收**：`node_modules/blockly` 存在，`import * as Blockly from 'blockly'` 可编译通过。

---

### Task 0.3：修复 BlocklyService 绕过 DI 问题

**文件**：`src/app/shared/components/blockly-workspace/blockly-workspace.component.ts`

**问题**：L99-100 `this.blocklyService = new BlocklyService()` 手动实例化，绕过 Angular DI。无法被测试 mock，无法注入其他依赖。

**修复方案**：
```typescript
constructor(private blocklyService: BlocklyService) {}
```

**验收**：组件通过构造函数注入获取服务实例。

---

### Task 0.4：解决 inline template 与外部 HTML 冲突

**文件**：`src/app/shared/components/blockly-workspace/blockly-workspace.component.ts`

**问题**：L43-84 的 inline `template` + `styles` 与同目录的 `.html` + `.scss` 文件并存。Angular 优先使用 inline，外部完整 UI 文件（工具栏、主题切换、代码预览面板）全部为死代码。

**修复方案**：
- 删除 inline `template` 和 `styles` 属性
- 添加 `templateUrl: './blockly-workspace.component.html'`
- 添加 `styleUrls: ['./blockly-workspace.component.scss']`

**验收**：组件渲染使用外部 HTML 模板，工具栏可见。

---

### Task 0.5：修复 auto-updater.js electron-log 缺失依赖

**文件**：`electron/services/auto-updater.js` + `electron/package.json`

**问题**：L11 `require('electron-log')` 但 `electron/package.json` 中 `electron-log` 不是依赖。如果此文件被加载将直接崩溃。

**修复方案**（二选一）：
- **方案 A（推荐）**：在 `electron/package.json` 添加 `electron-log` 依赖并安装
- **方案 B**：将 `auto-updater.js` 中的日志改为 `console.log/warn/error`，去除 electron-log 依赖

**验收**：`require('electron-log')` 不报错（方案 A），或文件中无 electron-log 引用（方案 B）。

---

### Task 0.6：修复 .imato 文件打开数据结构不匹配

**文件**：`src/app/core/services/imato-file.service.ts` + `electron/main.js`

**问题**：
- 主进程 `main.js` L496-501 发送 `{ type: 'open-file', filePath, content: <已解析JSON对象>, fileType }`
- 渲染端 `imato-file.service.ts` L91 对 `data.content` 执行 `JSON.parse()`
- 已解析的对象传入 `JSON.parse()` 会抛 `SyntaxError`，文件打开功能完全失效

**修复方案**：
- 渲染端 `handleOpenFile` 判断 `content` 类型：若已是对象则直接使用，不再 `JSON.parse`
- 或者主进程发送 `raw` 字段（原始字符串）而非 `content`（已解析对象）

**验收**：双击 .imato 文件，`ImatoFileService.currentPackage$` 能正确发出解析后的课程包数据。

---

### Task 0.7：修复 auto-updater.js disableVersion 方法

**文件**：`electron/services/auto-updater.js`

**问题**：L160-161 `autoUpdater.autoUpdater.disable()` — 双重属性访问，`autoUpdater.autoUpdater` 为 `undefined`，调用 `.disable()` 必抛 `TypeError`。

**修复方案**：
```javascript
disableVersion() {
  autoUpdater.autoDownload = false;
  // 或标记一个内部 flag 跳过更新
}
```

**验收**：调用 `disableVersion()` 不抛异常。

---

## 四、Sprint 1：Blockly 真实集成（1 周）

### Task 1.1：Blockly 工作区真实初始化

**文件**：`src/app/core/services/blockly.service.ts`

**当前状态**：`initWorkspace` 返回 `Promise.resolve(null)`，`generateCode` 返回硬编码注释。

**实现内容**：
1. 导入 Blockly：`import * as Blockly from 'blockly'`
2. `initWorkspace` 中调用 `Blockly.inject(container, options)` 创建真实工作区
3. 配置工具箱（Toolbox）：逻辑块、循环块、数学块、文本块、列表块、变量块
4. `generateCode` 使用 `Blockly.Python` 或 `Blockly.JavaScript` 生成器
5. 监听 `workspace.addChangeListener` 触发代码生成事件

**验收**：
- [ ] 工作区渲染可见积木块工具箱
- [ ] 可拖拽积木块到工作区
- [ ] 拖拽后代码预览区显示生成的 Python/JS 代码

---

### Task 1.2：Blockly 组件集成真实工作区

**文件**：`src/app/shared/components/blockly-workspace/blockly-workspace.component.ts` + `.html`

**实现内容**：
1. `ngAfterViewInit` 中调用 `blocklyService.initWorkspace(container.nativeElement, options)`
2. 绑定工具栏按钮（撤销/重做/清空）到 Blockly API：`workspace.undo()`, `workspace.redo()`, `workspace.clear()`
3. 主题切换调用 `Blockly.Theme` API
4. `blockCount` 绑定 `workspace.getAllBlocks(false).length`
5. 代码预览区实时显示 `blocklyService.generateCode()` 输出

**验收**：
- [ ] 撤销/重做按钮功能正常
- [ ] 主题切换生效（深色/浅色）
- [ ] 积木块计数器准确

---

### Task 1.3：Blockly 项目保存/加载

**文件**：`src/app/core/services/blockly.service.ts`

**实现内容**：
1. `saveProject(name)`: `Blockly.Xml.workspaceToDom(workspace)` → 序列化 → `localStorage.setItem()`
2. `loadProject(name)`: `localStorage.getItem()` → `Blockly.Xml.domToWorkspace()`
3. `listProjects()`: 枚举 localStorage 中的 `blockly_*` key
4. `deleteProject(name)`: 移除 localStorage 条目

**验收**：
- [ ] 保存后刷新页面，可加载恢复之前的工作区状态
- [ ] 项目列表正确显示已保存项目

---

### Task 1.4：Blockly 与编程课页面集成

**文件**：`src/app/components/ai-edu-dashboard/ai-coding-course.component.ts`

**实现内容**：
1. 确保 `ai-coding-course` 正确嵌入 `app-blockly-workspace`
2. `onCodeChanged` 事件处理：显示生成代码
3. 课程选择后加载对应 Blockly 模板

**验收**：
- [ ] 从 AI 编程课 Tab 可正常使用 Blockly 工作区
- [ ] 选择课程后工作区加载对应积木块模板

---

## 五、Sprint 2：OpenSciEDU 离线缓存 + 自动更新补全（1 周）

### Task 2.1：OpenSciEDU 前端离线缓存

**文件**：`src/app/core/services/opensciedu.service.ts`

**验收标准要求**："离线时能缓存最近访问的课程"

**实现内容**：
1. 添加 IndexedDB 缓存层（复用 `offline-storage.service.ts` 的 IndexedDB 基础设施）
2. 课程列表 API 成功响应后写入 IndexedDB（key: `opensciedu_courses_{params_hash}`）
3. HTTP 请求失败时优先从 IndexedDB 读取，而非直接降级到 mock
4. 课程详情同步缓存
5. 缓存 TTL：24 小时，提供 `clearLocalCache()` 方法

**验收**：
- [ ] 在线访问课程列表后，断开网络，刷新页面仍能看到上次加载的课程
- [ ] 缓存数据不超过 24 小时

---

### Task 2.2：OpenSciEDU getCourseDetail mock 降级一致性

**文件**：`src/app/core/services/opensciedu.service.ts`

**当前状态**：`getCourseDetail()` (L337-341) 断网返回 `null`，`getPublicCourses` 有 mock 降级。

**修复方案**：
- 与 `getPublicCourses` 保持一致的降级策略：API 失败 → IndexedDB 缓存 → Mock 数据
- `searchCourses` 和 `getCategories` 同理

**验收**：断网状态下，`getCourseDetail` 返回模拟课程详情而非 `null`。

---

### Task 2.3：自动更新 IPC 处理器

**文件**：新建 `electron/src/core/ipc/handlers/updater-handlers.js`

**当前状态**：渲染进程无法主动触发下载/安装更新。

**实现内容**：
```javascript
// 注册以下 IPC handlers:
ipcMain.handle('updater:check', ...)       // 检查更新
ipcMain.handle('updater:download', ...)    // 下载更新
ipcMain.handle('updater:install', ...)     // 安装并重启
ipcMain.handle('updater:get-status', ...)  // 获取当前状态
```

**渲染端**：在 `preload.js` 暴露对应 API，Angular 创建 `updater.service.ts` 封装调用。

**验收**：
- [ ] 前端设置页可手动点击「检查更新」
- [ ] 发现更新后可触发下载
- [ ] 下载完成后可触发安装重启

---

### Task 2.4：清理 auto-updater.js 死代码

**文件**：`electron/services/auto-updater.js`

**当前状态**：`AutoUpdaterService` 类全局零引用，与 `src/core/updates.js` 功能重叠。

**方案**（二选一）：
- **方案 A（推荐）**：删除 `auto-updater.js`，将 `updates.js` 重构为使用 `AutoUpdaterService` 的模式
- **方案 B**：在 `app-initializer.js` 中实例化 `AutoUpdaterService`，替代 `updates.js` 的动态 require

**验收**：自动更新只有单一实现路径，无重复代码。

---

## 六、Sprint 3：文件关联收尾 + 集成测试（0.5 周）

### Task 3.1：Windows second-instance 文件关联处理

**文件**：`electron/main.js`

**当前状态**：仅处理首次启动的 `process.argv`。应用已运行时双击 .imato 文件，Windows 尝试启动新实例但无 `second-instance` 事件处理。

**实现内容**：
```javascript
app.on('second-instance', (event, commandLine) => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
    // 从 commandLine 提取文件路径
    const filePath = commandLine.find(arg => {
      const name = path.basename(arg);
      return isValidFileName(name);
    });
    if (filePath) {
      const result = safeReadFile(filePath);
      sendFileEvent(filePath, result);
    }
  }
});
```

同时需确认 `app.requestSingleInstanceLock()` 已调用（否则 second-instance 不触发）。

**验收**：应用运行中双击 .imato 文件，文件内容正确加载。

---

### Task 3.2：file-parser.js .imato 类型验证修复

**文件**：`electron/services/file-parser.js`

**问题**：`validateFileContent` 中 `course` 类型的 typeMap 值为 `'blockly-project|python-project|circuit-project'`，但测试文件使用 `type: 'course'`，导致所有 .imato 课程包验证失败。

**修复方案**：
```javascript
const typeMap = {
  course: 'course|blockly-project|python-project|circuit-project',
  blockly: 'blockly-project',
  circuit: 'circuit-project',
};
```

**验收**：`type: 'course'` 的 .imato 文件通过验证。

---

### Task 3.3：OpenSciEDU dead code 清理

**文件**：`src/app/core/services/opensciedu.service.ts`

**清理内容**：
- 删除未使用的 `checkApiAvailability()` 方法（L210-235）
- 删除未使用的 `healthCheckInProgress` 状态变量
- 删除未使用的 `forkJoin` 和 `finalize` 导入（L20-21）

**验收**：TypeScript 编译无 unused import 警告。

---

### Task 3.4：全 Phase 集成测试

**运行已有测试文件**：
- `tests/electron/test-blockly.spec.js` — Blockly E2E
- `tests/electron/test-auto-updater.spec.js` — 自动更新 E2E
- `tests/electron/test-file-association.spec.js` — 文件关联 E2E

**补充测试**：
- OpenSciEDU 离线缓存测试（断网 → 刷新 → 验证数据仍在）
- 文件关联端到端测试（创建 .imato 文件 → 双击打开 → 验证页面显示）

---

## 七、风险登记

| 风险 | 影响 | 概率 | 缓解 |
|------|------|------|------|
| blockly v11 API 变更 | Task 1.1-1.2 返工 | 低 | 锁定版本 `blockly@11.1.1`，参考官方 migration guide |
| IndexedDB 缓存与现有 `offline-storage.service.ts` 冲突 | Task 2.1 延期 | 中 | 使用独立 DB name `OpenSciEDUCache` |
| OpenSciEDU 远程 API 长期不可用（Neo4j DNS 问题） | Phase 1 降级为永久 mock | 高 | Mock 数据需覆盖所有 API 端点，确保用户体验完整 |
| electron-builder publish 需要 GitHub repo 实际存在 | Task 2.3 无法端到端验证 | 中 | 使用本地 file:// provider 做开发阶段验证 |

---

## 八、里程碑验收标准

| 里程碑 | 日期目标 | 验收条件 |
|--------|---------|----------|
| **Sprint 0 完成** | Day 1 | 7 个 P0 BUG 全部修复，TypeScript/JS 编译通过 |
| **Sprint 1 完成** | Day 8 | Blockly 工作区可拖拽积木块、生成代码、保存加载 |
| **Sprint 2 完成** | Day 15 | OpenSciEDU 离线缓存工作、自动更新 IPC 联通 |
| **Sprint 3 完成** | Day 18 | 全部 E2E 测试通过，四个 Phase 验收标准全部达标 |

---

## 九、资源估算（修正后）

| 角色 | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | 总计 |
|------|----------|----------|----------|----------|------|
| 前端开发 | 0.5 人天 | 4 人天 | 2 人天 | 0.5 人天 | **7 人天** |
| Electron 开发 | 0.5 人天 | 0 | 2 人天 | 1 人天 | **3.5 人天** |
| 测试 | 0 | 1 人天 | 1 人天 | 1 人天 | **3 人天** |
| **总计** | **1 人天** | **5 人天** | **5 人天** | **2.5 人天** | **13.5 人天** |

> 约 **2.7 人周** — 相比原计划 24.5 人天，审计后实际剩余工作量约 13.5 人天（因部分代码已实现）。
