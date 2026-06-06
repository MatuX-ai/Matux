# MatuX 模块化懒加载架构 — 开发计划

**关联需求文档**: [MODULAR_LAZY_LOADING_ARCHITECTURE.md](./MODULAR_LAZY_LOADING_ARCHITECTURE.md)  
**版本**: v1.0  
**计划周期**: 8 周（4 Phase）  
**日期**: 2026-06-06  

---

## 总览

```
Phase 1 ─── 基础设施层 (Week 1~2)    ← 模块注册表 + 懒加载引擎 + 状态 API
Phase 2 ─── 模块分级迁移 (Week 3~5)  ← 60+ 路由拆分为 4 层 Tier
Phase 3 ─── 容错与降级 (Week 6~7)    ← 熔断器 + 依赖降级 + 前端 UX
Phase 4 ─── Electron 集成 (Week 8)   ← 分阶段启动 + Splash 进度
```

**核心约束**：
- 全程向后兼容，`MODULE_LAZY_LOADING_ENABLED=false` 可回退
- 每个 Phase 交付可独立运行的版本
- 所有现有 API 路径不变

---

## Phase 1：基础设施层 (Week 1~2)

### 目标
搭建模块懒加载引擎，重构 `main.py` 启动流程，实现模块状态 API。

### 前置依赖
- 无外部依赖，仅涉及后端 Python 代码

---

### Task 1.1: 创建模块注册表核心数据结构

**新建文件**: `backend/core/__init__.py`, `backend/core/module_spec.py`

**工作内容**:
- 定义 `ModuleState` 枚举 (UNLOADED / LOADING / ACTIVE / DEGRADED / FAILED / DISABLED)
- 定义 `ModuleTier` 枚举 (TIER_0_CORE / TIER_1_HIGH / TIER_2_ON_DEMAND / TIER_3_DELAYED)
- 定义 `ModuleSpec` 数据类，包含 name / tier / router_factory / prefix / tags / dependencies / required_services / fallback_services / state / error_message / load_time_ms

**验收**:
- `ModuleSpec` 可序列化
- 枚举值与需求文档对齐

**预估**: 0.5 天

---

### Task 1.2: 实现模块懒加载引擎 (ModuleLazyLoader)

**新建文件**: `backend/core/lazy_loader.py`

**工作内容**:
- `ModuleLazyLoader` 类，持有 `FastAPI app` 引用和模块注册表 `dict[str, ModuleSpec]`
- `register(spec)` — 注册模块到注册表（不加载路由）
- `activate(module_name)` — 异步激活：
  1. 检查依赖模块是否已激活（递归，最多 2 级深度）
  2. 检查 `required_services` 可用性（调用 ServiceDependency）
  3. 调用 `router_factory()` 创建 `APIRouter`
  4. `app.include_router(router, prefix, tags)` 注册到 FastAPI
  5. 调用 `LazyTableManager.create_tables_for_module()` 创建该模块的表
  6. 更新 `ModuleSpec.state = ACTIVE`，记录 `load_time_ms`
- `deactivate(module_name)` — 去激活（标记 UNLOADED，路由仍注册但可通过中间件拦截）
- `activate_tier(tier)` — 批量激活指定层级
- `get_status()` — 返回所有模块状态摘要
- 使用 `asyncio.Lock` 防止并发激活同一模块

**关键设计**:
```python
class ModuleLazyLoader:
    def __init__(self, app: FastAPI):
        self.app = app
        self.modules: dict[str, ModuleSpec] = {}
        self._loading_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
```

**验收**:
- 单元测试：注册 → 激活 → 状态变更 → 路由可访问
- 并发激活同一模块不会重复加载

**预估**: 2 天

---

### Task 1.3: 实现路由激活中间件

**新建文件**: `backend/core/activation_middleware.py`

**工作内容**:
- `ModuleActivationMiddleware` — Starlette ASGI 中间件
- 请求进入时：
  1. 解析 URL path，匹配到对应模块的 prefix
  2. 若模块状态为 `UNLOADED`，触发 `lazy_loader.activate(module_name)`
  3. 激活期间返回 `503 Service Unavailable` + `Retry-After: 3` + JSON body `{"status": "module_loading", "message": "功能模块正在启动..."}`
  4. 激活失败返回 `503` + `{"status": "module_unavailable", "message": "..."}`
  5. 激活成功后放行请求
- Tier 0 模块跳过检查（始终 ACTIVE）
- 维护 URL prefix → module_name 的映射表

**验收**:
- 访问 Tier 2 模块 URL 时自动激活
- 激活中返回 503 + Retry-After
- 激活后请求正常处理

**预估**: 1.5 天

---

### Task 1.4: 实现数据库表延迟创建管理器

**新建文件**: `backend/core/lazy_tables.py`

**工作内容**:
- `LazyTableManager` 类
- 维护 `module_name → list[model_class]` 映射
- `register_models(module_name, model_classes)` — 注册模型（不创建表）
- `create_tables_for_module(module_name)` — 仅创建指定模块的表
- `create_tier0_tables()` — 启动时只创建核心表
- 使用 `async with engine.begin()` + `conn.run_sync(table.create, checkfirst=True)` 幂等创建
- 重构现有 `utils/database.py:create_db_and_tables()`:
  - 保留原有函数作为全量模式兼容
  - 新增 `create_tables_subset(model_classes)` 用于分批创建

**涉及文件**:
- `backend/core/lazy_tables.py` (新建)
- `backend/utils/database.py` (修改 — 添加 `create_tables_subset()`)

**验收**:
- 核心表（users/courses）可独立创建
- 非核心表创建失败不影响核心表

**预估**: 1 天

---

### Task 1.5: 实现模块状态 API

**新建文件**: `backend/routes/system_status_routes.py`

**工作内容**:
- `GET /api/v1/system/modules` — 返回所有模块状态列表
- `GET /api/v1/system/modules/{name}` — 返回单个模块详情
- `POST /api/v1/system/modules/{name}/activate` — 手动激活模块
- `POST /api/v1/system/modules/{name}/deactivate` — 手动去激活
- `GET /api/v1/system/health` — 增强版健康检查（替代 `/health`）
  - 返回 `{ status, modules: {active, degraded, failed, unloaded}, dependencies: {redis, neo4j, ...} }`
- `GET /api/v1/system/dependencies` — 返回依赖服务状态

**验收**:
- 前端状态栏可调用 `/api/v1/system/health` 获取后端状态
- 管理员可手动激活/去激活模块

**预估**: 1 天

---

### Task 1.6: 重构 main.py 启动流程

**修改文件**: `backend/main.py`

**工作内容**:
1. 添加 `MODULE_LAZY_LOADING_ENABLED` 环境变量到 `config/settings.py`
2. `main.py` 顶部只保留核心 import（FastAPI / CORS / Middleware / settings）
3. 移除所有 `from routes import ...` 的顶层 import（改为运行时通过 LazyLoader 注册）
4. `startup_event` 重构为：
   ```
   a. 创建数据库引擎（不变）
   b. 创建 Tier 0 核心表（users / courses / sessions）
   c. 初始化 LazyLoader，注册所有 ModuleSpec
   d. 激活 Tier 0 模块（auth / course / user / health）
   e. 注册 ActivationMiddleware
   f. 注册 SystemStatusRoutes
   g. 返回 "核心就绪"
   h. [后台任务] 预加载 Tier 1 模块
   ```
5. 保留 `MODULE_LAZY_LOADING_ENABLED=false` 回退到原有全量加载模式
6. 将原有 `startup_event` 中的模型导入移入 `lazy_tables.py`

**涉及文件**:
- `backend/main.py` (大幅重构)
- `backend/config/settings.py` (新增环境变量)

**验收**:
- `MODULE_LAZY_LOADING_ENABLED=true` 模式下：
  - 后端启动到 `/health` 可用 < 5 秒
  - 只有 Tier 0 路由可访问
- `MODULE_LAZY_LOADING_ENABLED=false` 模式下：
  - 行为与重构前完全一致

**预估**: 2 天（最复杂的 Task，需仔细处理 import 顺序）

---

### Task 1.7: 前端状态栏增强

**修改文件**: `src/app/shared/components/status-bar/status-bar.component.ts`

**工作内容**:
- `checkWebBackend()` 改用 `HttpClient.get('/api/v1/system/health')` (Angular 代理)
- 解析返回的 `modules.summary` 数据
- 状态栏显示增强：`[核心服务 ✓] [AI模块 ⏳] [区块链 ○]`
- 添加定时轮询（每 30 秒刷新一次模块状态）
- 添加 `isModuleAvailable(name)` 公共方法

**涉及文件**:
- `status-bar.component.ts` (修改)
- `status-bar.component.html` (修改 — 显示更多状态)
- `status-bar.component.scss` (修改 — 模块状态样式)

**验收**:
- 状态栏准确反映各模块状态
- 模块激活/去激活时状态栏实时更新

**预估**: 1 天

---

### Task 1.8: 单元测试 — Phase 1

**新建文件**: `backend/tests/test_lazy_loader.py`, `backend/tests/test_activation_middleware.py`, `backend/tests/test_lazy_tables.py`

**工作内容**:
- ModuleSpec 序列化/反序列化测试
- LazyLoader 注册 → 激活 → 状态变更测试
- 并发激活同一模块的幂等性测试
- ActivationMiddleware 的 503 响应测试
- LazyTableManager 分批创建表测试
- SystemStatus API 端点测试

**验收**: 覆盖率 > 80%

**预估**: 1 天

---

### Phase 1 交付物检查清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/core/__init__.py` | 新建 | 核心引擎包 |
| `backend/core/module_spec.py` | 新建 | ModuleState/ModuleTier/ModuleSpec |
| `backend/core/lazy_loader.py` | 新建 | ModuleLazyLoader 引擎 |
| `backend/core/activation_middleware.py` | 新建 | 路由激活中间件 |
| `backend/core/lazy_tables.py` | 新建 | LazyTableManager |
| `backend/routes/system_status_routes.py` | 新建 | 模块状态 API |
| `backend/main.py` | 重构 | 分阶段启动流程 |
| `backend/config/settings.py` | 修改 | 新增懒加载配置项 |
| `backend/utils/database.py` | 修改 | 添加 create_tables_subset |
| `status-bar.component.ts/html/scss` | 修改 | 前端状态增强 |
| `backend/tests/test_lazy_loader.py` | 新建 | 单元测试 |

**Phase 1 验收标准**:
- ✅ 后端冷启动 < 5 秒
- ✅ `/health` 3 秒内可用
- ✅ `MODULE_LAZY_LOADING_ENABLED=false` 可回退
- ✅ 前端状态栏准确显示

---

## Phase 2：模块分级迁移 (Week 3~5)

### 目标
将现有 60+ 路由模块按 Tier 分级，每个模块添加 `module_spec.py` 描述文件。

### 前置依赖
- Phase 1 全部完成

---

### Task 2.1: 定义模块分级映射表

**新建文件**: `backend/core/module_tiers.py`

**工作内容**: 为每个现有路由文件定义 `ModuleSpec`

```python
# Tier 0 — 核心模块 (4 个)
CORE_MODULES = [
    ModuleSpec(name="auth",         tier=TIER_0, router_factory=..., prefix="/api/v1/auth"),
    ModuleSpec(name="course",       tier=TIER_0, router_factory=..., prefix="/api/v1"),
    ModuleSpec(name="system_health",tier=TIER_0, router_factory=..., prefix="/"),
    ModuleSpec(name="unified_auth", tier=TIER_0, router_factory=..., prefix="/api/v1/auth"),
]

# Tier 1 — 高优先级 (8 个)
HIGH_PRIORITY_MODULES = [
    ModuleSpec(name="ai_service",     tier=TIER_1, required_services=["openai_api"]),
    ModuleSpec(name="ai_recommend",   tier=TIER_1, required_services=["openai_api"]),
    ModuleSpec(name="payment",        tier=TIER_1),
    ModuleSpec(name="exam",           tier=TIER_1),
    ModuleSpec(name="learning_behavior", tier=TIER_1),
    ModuleSpec(name="ai_teacher",     tier=TIER_1, required_services=["openai_api"]),
    ModuleSpec(name="ai_edu_progress",tier=TIER_1),
    ModuleSpec(name="achievement",    tier=TIER_1),
]

# Tier 2 — 按需激活 (18 个)
ON_DEMAND_MODULES = [
    ModuleSpec(name="blockchain",     tier=TIER_2, required_services=["hyperledger"]),
    ModuleSpec(name="ar_lab",         tier=TIER_2),
    ModuleSpec(name="ar_vr",          tier=TIER_2, required_services=["vircadia"]),
    ModuleSpec(name="creativity",     tier=TIER_2, required_services=["openai_api"]),
    ModuleSpec(name="digital_twin",   tier=TIER_2, required_services=["docker"]),
    ModuleSpec(name="openhydra",      tier=TIER_2, required_services=["openhydra"]),
    ModuleSpec(name="sponsorship",    tier=TIER_2),
    ModuleSpec(name="collaborative_editor", tier=TIER_2),
    ModuleSpec(name="multimedia",     tier=TIER_2),
    ModuleSpec(name="model_benchmark",tier=TIER_2),
    ModuleSpec(name="course_version", tier=TIER_2),
    ModuleSpec(name="subscription",   tier=TIER_2),
    ModuleSpec(name="finance",        tier=TIER_2),
    ModuleSpec(name="oauth",          tier=TIER_2),
    ModuleSpec(name="sensor_data",    tier=TIER_2),
    ModuleSpec(name="vector_knowledge", tier=TIER_2),
    ModuleSpec(name="local_knowledge_graph", tier=TIER_2),
    ModuleSpec(name="leaderboard",    tier=TIER_2),
]

# Tier 3 — 延迟激活 (6 个)
DELAYED_MODULES = [
    ModuleSpec(name="federated",          tier=TIER_3),
    ModuleSpec(name="hardware_cert",      tier=TIER_3),
    ModuleSpec(name="vircadia_avatar",    tier=TIER_3, required_services=["vircadia"]),
    ModuleSpec(name="model_update",       tier=TIER_3),
    ModuleSpec(name="ar_rewards",         tier=TIER_3),
    ModuleSpec(name="admin_settings",     tier=TIER_3),
]
```

**验收**: 所有 60+ 路由文件均有对应 ModuleSpec，无遗漏

**预估**: 1 天

---

### Task 2.2: 实现模块 model → table 映射

**新建文件**: `backend/core/model_module_map.py`

**工作内容**:
- 为每个模块定义它所需的 ORM model 列表
- 将 `utils/database.py:create_db_and_tables()` 中的 20+ 个 model import 拆分到各模块
- 确保 `create_tables_for_module(module_name)` 能正确找到对应的 model

**示例**:
```python
MODULE_MODELS = {
    "auth": ["models.user.User", "models.oauth_account.OAuthAccount"],
    "course": ["models.course.Course", "models.course.CourseLesson", "models.course.CourseAssignment"],
    "payment": ["models.payment.Payment"],
    "exam": ["models.exam.Exam", "models.exam.Question", "models.exam.ExamAttempt", "models.exam.CheatEvent"],
    ...
}
```

**验收**: 每个模块的表可独立创建，无交叉依赖遗漏

**预估**: 1.5 天

---

### Task 2.3: 迁移 Tier 0 模块

**工作内容**:
- 将 auth_routes / course_routes / unified_auth / system_health 的 import 从 main.py 顶部移除
- 改为通过 LazyLoader 在 startup_event 中立即激活
- 验证：仅 Tier 0 加载时，登录/课程列表/健康检查正常工作

**涉及文件**: `backend/main.py`

**验收**: `/api/v1/auth/login` + `/api/v1/courses` + `/health` 在 5 秒内可用

**预估**: 0.5 天

---

### Task 2.4: 迁移 Tier 1 模块

**工作内容**:
- AI 服务模块（ai_routes, ai_recommend_routes, ai_teacher_routes）
  - required_services: openai_api（可降级为 template_mode）
  - 模型: ai_request, recommendation
- 支付模块（payment_routes, subscription_routes）
  - required_services: 支付网关（可降级为 read_only）
  - 模型: payment, subscription, subscription_fsm
- 测验模块（exam_routes）
  - 模型: exam, exam_questions, exam_attempts, cheat_events
- 学习进度模块（ai_edu_progress_routes, learning_behavior_routes）
- 成就模块（achievement_routes）

**验证方法**: 启动后 Tier 1 模块在 10 秒内后台预加载完毕，用户访问时无延迟

**预估**: 2 天

---

### Task 2.5: 迁移 Tier 2 模块

**工作内容**:
- 区块链网关 — required_services: hyperledger → fallback: cache_mode
- AR/VR 实验室 — required_services: vircadia → fallback: 2d_simulation
- 创意引擎 — required_services: openai_api → fallback: local_templates
- 数字孪生 — required_services: docker → fallback: read_only
- 协作编辑 / 多媒体 / 课程版本 / 赞助 / 财务 等
- 每个模块添加 `required_services` 和 `fallback_services`

**验证方法**: 访问 `/api/v1/blockchain/*` 触发自动激活，首次请求延迟 < 2 秒

**预估**: 3 天（模块最多，需逐个验证）

---

### Task 2.6: 迁移 Tier 3 模块

**工作内容**:
- 联邦学习、硬件认证、虚拟化身、模型更新、AR奖励、管理设置
- 这些模块默认 DISABLED，需管理员手动激活或通过环境变量启用

**验证方法**: 默认不加载，POST `/api/v1/system/modules/federated/activate` 可手动激活

**预估**: 1 天

---

### Task 2.7: 已解耦模块存根清理

**工作内容**:
- 标记为已解耦的模块（tenant_config / educational_institution / permission / material）
- 保留路由存根但 tier = DISABLED，不消耗启动资源
- 添加说明注释指向 OpenMTSciEd / OpenMTEduInst

**预估**: 0.5 天

---

### Task 2.8: 集成测试 — Phase 2

**新建文件**: `backend/tests/test_module_tier_migration.py`

**工作内容**:
- 测试所有 API 端点在懒加载模式下仍正常响应
- 测试模块激活顺序正确（依赖先于被依赖）
- 测试全量模式 (`MODULE_LAZY_LOADING_ENABLED=false`) 行为不变
- 对比测试：全量模式 vs 懒加载模式的 API 响应一致性

**验收**: 所有现有 API 端点功能不变

**预估**: 2 天

---

### Phase 2 交付物检查清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/core/module_tiers.py` | 新建 | 4 层 Tier 映射表 |
| `backend/core/model_module_map.py` | 新建 | 模块→ORM模型映射 |
| `backend/main.py` | 修改 | 移除顶层 import，改为 LazyLoader |
| `backend/tests/test_module_tier_migration.py` | 新建 | 集成测试 |

**Phase 2 验收标准**:
- ✅ 所有 60+ API 端点功能不变
- ✅ 每个模块可独立激活/去激活
- ✅ 单个模块加载失败不影响其他模块
- ✅ 全量模式回退正常

---

## Phase 3：容错与降级 (Week 6~7)

### 目标
实现模块级熔断器、依赖服务降级、前端 UX 反馈。

### 前置依赖
- Phase 2 全部完成

---

### Task 3.1: 实现模块级熔断器

**新建文件**: `backend/core/module_circuit_breaker.py`

**工作内容**:
- `ModuleCircuitBreaker` 类
- 三态机: CLOSED → OPEN → HALF_OPEN → CLOSED
- 可配置: `failure_threshold` (默认 3), `timeout` (默认 60s)
- `execute(func, fallback)` — 包裹模块处理函数
- 与 `ActivationMiddleware` 集成：当模块熔断时自动调用降级方案
- Prometheus 指标: `module_circuit_breaker_state`, `module_circuit_breaker_failures`

**验收**:
- 连续失败 3 次 → 熔断器打开
- 60 秒后 → 半开状态探测
- 探测成功 → 关闭熔断器

**预估**: 1.5 天

---

### Task 3.2: 实现依赖服务降级管理器

**新建文件**: `backend/core/service_dependencies.py`

**工作内容**:
- `ServiceDependencyManager` 类
- `DEPENDENCY_MAP` — 定义每个外部服务的检测方法和降级方案
- `check_service(name)` — 检测服务可用性（Redis ping / Neo4j bolt / Docker info / OpenAI models）
- `get_fallback(name)` — 返回降级方案实例
- 降级方案实现：
  - Redis → `MemoryCacheBackend`（dict 缓存 + TTL）
  - Neo4j → SQL 关联查询替代
  - OpenAI → 本地模板响应器
  - Docker → 受限执行模式
  - Vircadia → 2D 模拟返回
- 启动时检测所有依赖，记录可用性状态
- 定期重检（每 30 秒）

**验收**:
- Redis 不可用 → 系统仍可运行（内存缓存）
- OpenAI 不可用 → AI 功能降级为基础模式
- 降级状态通过 `/api/v1/system/dependencies` 可查询

**预估**: 3 天

---

### Task 3.3: 为 Tier 2/3 模块实现降级方案

**工作内容**: 为每个按需模块编写 fallback handler

| 模块 | 降级方案 | 实现方式 |
|------|---------|---------|
| blockchain | 缓存模式 | 返回最近缓存的积分数据 + "数据待同步"标记 |
| ar_vr | 2D 模式 | 返回 2D 模拟数据 + "3D 模式不可用"提示 |
| creativity | 模板模式 | 返回预设模板列表，不支持 AI 生成 |
| digital_twin | 只读模式 | 返回预置场景数据，禁止交互操作 |
| openhydra | 禁用模式 | 返回 503 + "沙箱环境不可用" |
| hardware_cert | 禁用模式 | 返回 503 + "需要硬件设备" |

**验收**: 每个 Tier 2/3 模块在依赖不可用时都有明确的降级行为

**预估**: 2 天

---

### Task 3.4: 前端模块状态服务

**新建文件**: `src/app/core/services/module-status.service.ts`

**工作内容**:
- `ModuleStatusService` — 全局 Injectable
- `moduleStates$: BehaviorSubject<Record<string, ModuleState>>` — 响应式状态
- `refreshModuleStates()` — 调用 `/api/v1/system/modules` 刷新
- `ensureModuleActive(name)` — 检查并等待模块激活
- `onModuleStateChange(name, callback)` — 监听模块状态变化
- 定时轮询（30 秒间隔）+ WebSocket 推送（可选，Phase 4）
- 使用 `shareReplay(1)` 缓存最新状态

**预估**: 1 天

---

### Task 3.5: Angular 路由守卫 — ModuleActiveGuard

**新建文件**: `src/app/core/guards/module-active.guard.ts`

**工作内容**:
- `ModuleActiveGuard implements CanActivate`
- 读取路由 `data.requiredModule` 属性
- 调用 `ModuleStatusService.ensureModuleActive()`
- 模块加载中 → 显示全屏遮罩 "正在启动 XX 功能..."
- 模块降级 → 显示 Snackbar 提示 "XX 功能降级运行中"
- 模块不可用 → 显示 Dialog + 提供重试按钮
- 在 `app-routing.module.ts` 中为 Tier 2/3 路由添加 `canActivate` + `data`

**修改文件**: `src/app/app-routing.module.ts`

**示例路由配置**:
```typescript
{
  path: 'vircadia',
  loadChildren: () => import('./vircadia/vircadia.module').then(m => m.VircadiaModule),
  canActivate: [ModuleActiveGuard],
  data: { requiredModule: 'ar_vr' }
}
```

**预估**: 1.5 天

---

### Task 3.6: 模块加载状态 UI 组件

**新建文件**: `src/app/shared/components/module-loading-overlay/`

**工作内容**:
- `ModuleLoadingOverlayComponent` — 全屏半透明遮罩
  - 显示模块名称 + 加载动画 + 预计等待时间
  - 超时 10 秒后显示 "加载时间较长，是否重试？"
- `ModuleDegradedBannerComponent` — 顶部横幅
  - 显示 "XX 功能降级运行中，部分功能受限"
  - 关闭按钮
- `ModuleUnavailableDialogComponent` — 不可用对话框
  - 显示原因 + 依赖服务状态 + 重试按钮 + 关闭按钮

**预估**: 1.5 天

---

### Task 3.7: 测试 — Phase 3

**工作内容**:
- 熔断器状态机测试（模拟连续失败 → 恢复）
- 依赖降级测试（Redis 断网 → 内存缓存生效）
- 前端守卫测试（模块不可用时路由拦截）
- 端到端测试：关闭 Redis → 访问课程 → 正常 + 访问积分 → 降级提示

**预估**: 1 天

---

### Phase 3 交付物检查清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/core/module_circuit_breaker.py` | 新建 | 模块级熔断器 |
| `backend/core/service_dependencies.py` | 新建 | 依赖降级管理器 |
| `src/app/core/services/module-status.service.ts` | 新建 | 前端模块状态服务 |
| `src/app/core/guards/module-active.guard.ts` | 新建 | 路由守卫 |
| `src/app/shared/components/module-loading-overlay/` | 新建 | 加载遮罩组件 |
| `src/app/shared/components/module-degraded-banner/` | 新建 | 降级横幅组件 |
| `src/app/shared/components/module-unavailable-dialog/` | 新建 | 不可用对话框 |
| `src/app/app-routing.module.ts` | 修改 | 添加路由守卫 |

**Phase 3 验收标准**:
- ✅ Redis 不可用时 > 80% 功能可用
- ✅ 模块崩溃后 60 秒内自动恢复
- ✅ 前端显示清晰的模块状态反馈

---

## Phase 4：Electron 集成优化 (Week 8)

### 目标
Electron 桌面端分阶段启动，核心就绪即显示主窗口。

### 前置依赖
- Phase 1~3 全部完成

---

### Task 4.1: Electron 分阶段后端启动

**修改文件**: `electron/main.js`

**工作内容**:
- 重构 `startBackend()` 为 `startBackendPhased()`：
  - Phase 1: 启动 Python 后端 + 等待 `/api/v1/system/health?tier=0` 返回
  - Phase 1 超时: 5 秒
  - Phase 1 成功 → 立即显示主窗口，关闭 Splash
  - Phase 2: 后台调用 `POST /api/v1/system/tiers/1/preload` 预加载 Tier 1
  - Phase 2 超时: 15 秒（不阻塞 UI）
- 修改 `BACKEND_START_TIMEOUT` 从 45s → 5s（仅核心启动）
- 新增 `HEALTH_CHECK_TIER0_URL = '/api/v1/system/health?tier=0'`

**验收**:
- 用户从点击 App 到主窗口显示 < 10 秒
- Tier 1 模块在后台静默加载

**预估**: 1.5 天

---

### Task 4.2: Splash 屏模块进度显示

**修改文件**: `electron/splash.html`, `electron/preload-splash.js`

**工作内容**:
- Splash 屏添加模块加载进度条
- 后端启动后通过 IPC 发送模块状态更新：
  ```
  splash-status: { phase: 'modules', text: '正在加载 AI 服务...', progress: 40 }
  splash-status: { phase: 'modules', text: '正在加载课程系统...', progress: 60 }
  splash-status: { phase: 'ready', text: '准备就绪', progress: 100 }
  ```
- Electron 主进程轮询 `/api/v1/system/modules` 获取进度

**预估**: 1 天

---

### Task 4.3: 模块状态托盘图标

**修改文件**: `electron/main.js`

**工作内容**:
- 系统托盘图标颜色反映后端状态：
  - 绿色 = 所有核心模块正常
  - 黄色 = 有模块降级运行
  - 红色 = 核心模块不可用
- 托盘菜单显示模块状态摘要
- 托盘菜单添加 "重启后端" 选项

**预估**: 0.5 天

---

### Task 4.4: IPC 通信扩展

**修改文件**: `electron/main.js`, `electron/preload.js`

**工作内容**:
- 新增 IPC channel: `backend:module-status` — 推送模块状态到渲染进程
- 新增 IPC channel: `backend:activate-module` — 渲染进程请求激活模块
- 新增 IPC channel: `backend:restart` — 重启后端
- `preload.js` 暴露 `electronAPI.getModuleStatus()` / `electronAPI.activateModule(name)`

**预估**: 1 天

---

### Task 4.5: 端到端测试 — Phase 4

**工作内容**:
- Electron 冷启动计时测试
- Splash 进度条显示正确性
- 主窗口显示后 Tier 1 后台加载不卡顿
- 模块状态托盘图标正确反映状态
- 托盘 "重启后端" 功能正常

**预估**: 1 天

---

### Phase 4 交付物检查清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `electron/main.js` | 修改 | 分阶段启动 + 托盘图标 |
| `electron/splash.html` | 修改 | 模块进度条 |
| `electron/preload-splash.js` | 修改 | 进度 IPC |
| `electron/preload.js` | 修改 | 模块状态 IPC |

**Phase 4 验收标准**:
- ✅ 用户点击 App → 可操作 < 10 秒
- ✅ Splash 显示真实模块加载进度
- ✅ 后台预加载不卡顿主界面

---

## 里程碑与风险缓冲

```
Week 1 ──── Task 1.1~1.4 (核心引擎)
Week 2 ──── Task 1.5~1.8 (状态API + 重构 + 测试)
              ↓ Phase 1 交付
Week 3 ──── Task 2.1~2.3 (分级映射 + Tier 0 迁移)
Week 4 ──── Task 2.4~2.5 (Tier 1/2 迁移)
Week 5 ──── Task 2.6~2.8 (Tier 3 + 清理 + 测试)
              ↓ Phase 2 交付
Week 6 ──── Task 3.1~3.3 (熔断器 + 降级)
Week 7 ──── Task 3.4~3.7 (前端UX + 测试)
              ↓ Phase 3 交付
Week 8 ──── Task 4.1~4.5 (Electron + 测试)
              ↓ Phase 4 交付
Week 9 ──── 风险缓冲（1 周）
```

**关键风险点**:
1. **Phase 1 Task 1.6** (main.py 重构) — 最复杂，建议先创建 feature branch
2. **Phase 2 Task 2.5** (Tier 2 模块最多) — 可能超出预估，缓冲 1 天
3. **Phase 3 Task 3.2** (依赖降级实现) — Redis 内存缓存需保证数据一致性

**回滚策略**:
- 每个 Phase 独立可部署
- `MODULE_LAZY_LOADING_ENABLED=false` 一键回退到全量模式
- Git 分支策略: `feature/lazy-loading` → `develop` → `main`
