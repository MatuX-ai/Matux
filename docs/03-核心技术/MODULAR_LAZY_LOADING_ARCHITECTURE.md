# MatuX 桌面端模块化懒加载架构重设计需求文档

**文档编号**: MATU-ARCH-2026-001  
**版本**: v1.0  
**状态**: 需求评审  
**作者**: 系统架构组  
**日期**: 2026-06-06  

---

## 1. 背景与问题描述

### 1.1 当前架构问题

MatuX 桌面端（Electron + Angular + FastAPI）当前采用**单体全量启动**模式，存在以下核心问题：

| 问题 | 现象 | 影响 |
|------|------|------|
| **启动过慢** | 后端一次性加载 60+ 路由模块、48+ ORM 模型 | 用户需等待 30~60 秒才能使用 |
| **强依赖外部服务** | 强制要求 Redis、Neo4j、PostgreSQL 同时可用 | 任一服务不可用则整体崩溃 |
| **无模块容错** | 单个模块初始化失败导致整个后端无法启动 | 系统稳定性极差 |
| **状态栏误报** | 健康检查代理配置缺失，前端误判后端未启动 | 用户体验混乱 |
| **资源浪费** | 用户不使用的模块（如区块链、AR/VR）也全量加载 | 内存占用过大，启动资源浪费 |

### 1.2 当前模块清单（60+ 路由模块）

**当前全量加载的模块分类：**

```
┌─────────────────────────────────────────────────────────────────┐
│  核心模块（必须立即启动）                                        │
│  ├── auth_routes（认证登录）                                     │
│  ├── course_routes（课程管理）                                   │
│  ├── user_routes（用户信息）                                     │
│  └── health（健康检查）                                          │
├─────────────────────────────────────────────────────────────────┤
│  重要模块（应在 5 秒内可用）                                      │
│  ├── ai_routes / ai_recommend_routes（AI 服务）                  │
│  ├── payment_routes（支付系统）                                  │
│  ├── learning_behavior_routes（学习行为）                        │
│  ├── ai_teacher_routes（AI 个性化教师）                          │
│  └── exam_routes（防作弊测验）                                   │
├─────────────────────────────────────────────────────────────────┤
│  次要模块（用户使用时再加载）                                     │
│  ├── blockchain_gateway_routes（区块链）                         │
│  ├── ar_lab_routes / ar_vr_routes（AR/VR 实验室）               │
│  ├── creativity_routes（创意引擎）                               │
│  ├── digital_twin_routes（数字孪生）                             │
│  ├── openhydra_routes（AI 沙箱环境）                             │
│  ├── sponsorship_routes（企业赞助）                              │
│  ├── model_benchmark_routes（模型基准测试）                      │
│  └── collaborative_editor_routes（协作编辑）                    │
├─────────────────────────────────────────────────────────────────┤
│  边缘模块（极少使用，按需加载）                                   │
│  ├── federated_routes（联邦学习）                                │
│  ├── hardware_certification_routes（硬件认证）                   │
│  ├── vircadia_avatar_routes（虚拟化身）                          │
│  ├── vector_knowledge_routes（向量知识库）                       │
│  └── local_knowledge_graph_routes（知识图谱）                     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 当前启动时序（问题所在）

```
用户点击 App
    │
    ▼
Electron 主进程启动（~2s）
    │
    ▼
Python 环境检测（~3s）
    │
    ▼
Redis 检测/启动（~2s）         ← 失败则降级
Neo4j 检测（~2s）              ← 失败则降级
    │
    ▼
FastAPI 应用初始化
    ├── 导入 60+ 路由文件（~5s）      ← 串行 import，阻塞主线程
    ├── 加载 48+ ORM 模型（~3s）      ← 全部 model 必须同时导入
    ├── 建表操作 create_all（~2s）     ← 同步等待
    ├── 初始化测试数据（~5s，开发模式） ← 阻塞
    ├── 注册表初始化（~3s）            ← 阻塞
    └── APM 初始化（~1s）
    │
    ▼
Angular 前端启动（~80s）             ← 独立并行，不依赖后端
    │
    ▼
后端可用（总计约 30~60s 后端等待时间）
```

---

## 2. 目标架构设计

### 2.1 设计原则

1. **最小启动集原则**：只加载用户打开 App 必需的核心模块（< 5 秒）
2. **按需激活原则**：模块在首次被访问时自动激活（Lazy Activation）
3. **故障隔离原则**：单个模块失败不影响其他模块和整体系统
4. **优雅降级原则**：依赖服务不可用时，提供只读/本地/缓存模式
5. **状态透明原则**：前端实时感知各模块状态，提供清晰的用户提示

### 2.2 目标启动时序

```
用户点击 App
    │
    ▼ [0~2s]
Electron 主进程 + Splash 屏启动
    │
    ▼ [2~5s]
FastAPI 核心层启动（仅 auth + health + course）
    │ → 后端状态变为 "核心可用"
    │ → 前端状态栏显示 "核心服务运行中"
    ▼ [5~10s]
Angular 前端就绪，用户可登录、浏览课程列表
    │
    ▼ [用户操作触发]
AI 模块激活（用户进入 AI 功能页面时）
区块链模块激活（用户进入积分页面时）
AR/VR 模块激活（用户进入实验室时）
...
```

### 2.3 模块分级策略

#### Tier 0 - 核心层（启动即加载，目标 < 3s）

| 模块 | 路由 | 职责 | 失败影响 |
|------|------|------|---------|
| `core_auth` | `/api/v1/auth/*` | 登录/注册/Token | 无法使用 App |
| `core_health` | `/health`, `/api/v1/status` | 健康检查/模块状态 | 状态栏异常 |
| `core_course` | `/api/v1/courses/*` | 课程列表/详情 | 首页无法显示 |
| `core_user` | `/api/v1/user/*` | 用户信息/设置 | 个人中心不可用 |

#### Tier 1 - 高优先级（后台异步预加载，目标 < 10s）

| 模块 | 触发条件 | 依赖 |
|------|---------|------|
| `ai_service` | 后台预加载 | OpenAI API Key（可降级） |
| `learning_progress` | 后台预加载 | SQLite |
| `exam_system` | 后台预加载 | SQLite |
| `payment_service` | 后台预加载 | 支付网关（可降级） |

#### Tier 2 - 按需激活（首次请求时加载，延迟 < 2s）

| 模块 | 触发条件 | 依赖 | 降级方案 |
|------|---------|------|---------|
| `blockchain` | 访问积分/证书页 | Hyperledger | 显示缓存数据 |
| `ar_vr_lab` | 进入 AR/VR 实验 | Vircadia | 提示服务不可用 |
| `digital_twin` | 进入数字孪生 | Docker | 只读演示模式 |
| `creativity_engine` | 使用创意工具 | OpenAI | 本地模板模式 |
| `collaborative_editor` | 进入协作编辑 | WebSocket | 单人编辑模式 |

#### Tier 3 - 延迟激活（用户主动触发，允许较长加载）

| 模块 | 触发条件 | 说明 |
|------|---------|------|
| `openhydra` | 进入 AI 沙箱 | 需要 K8s 环境 |
| `hardware_cert` | 硬件认证操作 | 需要硬件设备 |
| `model_management` | AI 模型管理 | 需要 GPU 支持 |
| `federated_learning` | 联邦学习任务 | 多节点协作 |

---

## 3. 核心架构变更

### 3.1 后端：模块懒加载引擎（Module Lazy Loader）

#### 3.1.1 ModuleRegistry 设计

```python
# backend/core/module_registry.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)


class ModuleState(Enum):
    """模块生命周期状态"""
    UNLOADED = "unloaded"       # 未加载（仅注册）
    LOADING = "loading"         # 加载中
    ACTIVE = "active"           # 运行中
    DEGRADED = "degraded"       # 降级运行
    FAILED = "failed"           # 加载失败
    DISABLED = "disabled"       # 已禁用


class ModuleTier(Enum):
    """模块优先级层级"""
    TIER_0_CORE = 0    # 核心层：启动必须
    TIER_1_HIGH = 1    # 高优先级：后台预加载
    TIER_2_ON_DEMAND = 2  # 按需激活：首次请求时
    TIER_3_DELAYED = 3    # 延迟激活：用户主动触发


@dataclass
class ModuleSpec:
    """模块规格描述"""
    name: str
    tier: ModuleTier
    router_factory: Callable  # () -> APIRouter
    prefix: str = ""
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    required_services: list[str] = field(default_factory=list)
    state: ModuleState = ModuleState.UNLOADED
    error_message: Optional[str] = None
    load_time_ms: float = 0.0
    activation_count: int = 0


class ModuleLazyLoader:
    """
    模块懒加载引擎
    
    核心职责：
    1. 管理所有模块的注册与生命周期
    2. 提供模块激活/去激活接口
    3. 拦截未激活模块的路由请求并自动激活
    4. 实现模块级熔断与故障隔离
    """
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.modules: dict[str, ModuleSpec] = {}
        self._loading_lock = asyncio.Lock()
        self._activated_routers: set[str] = set()
    
    def register(self, spec: ModuleSpec):
        """注册模块（不立即加载）"""
        self.modules[spec.name] = spec
        logger.info(f"📦 模块已注册: {spec.name} (Tier {spec.tier.value})")
    
    async def activate(self, module_name: str) -> bool:
        """
        激活指定模块
        1. 检查依赖模块是否已激活
        2. 调用 router_factory 创建路由
        3. 注册到 FastAPI 应用
        4. 更新状态
        """
        ...
    
    async def activate_tier(self, tier: ModuleTier):
        """批量激活指定层级的所有模块"""
        ...
    
    async def get_module_status(self) -> dict:
        """获取所有模块当前状态"""
        ...
    
    def create_activation_middleware(self):
        """
        创建路由激活中间件
        拦截请求，判断目标路由所属模块是否已激活
        若未激活则先激活再处理请求
        """
        ...
```

#### 3.1.2 激活中间件（Activation Middleware）

```python
# backend/middleware/module_activation_middleware.py

class ModuleActivationMiddleware:
    """
    路由级懒加载激活中间件
    
    工作流程：
    1. 请求进入时，匹配 URL 前缀找到对应模块
    2. 若模块状态为 UNLOADED，触发异步激活
    3. 激活期间返回 503 + Retry-After 头
    4. 激活失败返回 503 + 模块错误信息
    5. 激活成功后请求正常处理
    """
    
    STATUS_RESPONSES = {
        "loading": {
            "status": "module_loading",
            "message": "功能模块正在启动，请稍候...",
            "retry_after": 3
        },
        "failed": {
            "status": "module_unavailable", 
            "message": "该功能模块暂时不可用",
            "fallback": "graceful_degradation"
        },
        "degraded": {
            "status": "module_degraded",
            "message": "该功能模块降级运行中"
        }
    }
```

#### 3.1.3 模块状态 API

```python
# backend/routes/module_status_routes.py

@router.get("/api/v1/system/modules")
async def list_modules():
    """
    返回所有模块状态，供前端状态栏和模块管理页使用
    响应格式:
    {
      "modules": [
        {
          "name": "ai_service",
          "state": "active",
          "tier": 1,
          "load_time_ms": 123.4,
          "dependencies": ["openai_api"],
          "error": null
        },
        {
          "name": "blockchain",
          "state": "unloaded",
          "tier": 2,
          "error": null
        }
      ],
      "summary": {
        "total": 25,
        "active": 8,
        "degraded": 1,
        "failed": 0,
        "unloaded": 16
      }
    }
    """

@router.post("/api/v1/system/modules/{name}/activate")
async def activate_module(name: str):
    """手动激活指定模块（管理员操作）"""

@router.post("/api/v1/system/modules/{name}/deactivate")
async def deactivate_module(name: str):
    """去激活指定模块，释放资源"""

@router.get("/api/v1/system/health")
async def system_health():
    """
    增强版健康检查，返回各模块状态摘要
    替代现有 /health 端点
    """
```

### 3.2 后端：服务依赖降级策略

#### 3.2.1 依赖服务分级

```python
# backend/core/service_dependencies.py

class ServiceDependency:
    """服务依赖管理器"""
    
    DEPENDENCY_MAP = {
        "redis": {
            "required_for": ["session", "cache", "celery"],
            "fallback": {
                "session": "memory_session",
                "cache": "no_cache",
                "celery": "sync_execution"
            }
        },
        "neo4j": {
            "required_for": ["knowledge_graph"],
            "fallback": {
                "knowledge_graph": "sql_graph_fallback"
            }
        },
        "openai_api": {
            "required_for": ["ai_code_gen", "ai_teacher", "creativity"],
            "fallback": {
                "ai_code_gen": "template_mode",
                "ai_teacher": "rule_based_tutor",
                "creativity": "local_templates"
            }
        },
        "vircadia": {
            "required_for": ["ar_vr_lab", "virtual_classroom"],
            "fallback": {
                "ar_vr_lab": "2d_simulation",
                "virtual_classroom": "video_mode"
            }
        },
        "docker": {
            "required_for": ["code_sandbox", "digital_twin"],
            "fallback": {
                "code_sandbox": "restricted_sandbox",
                "digital_twin": "read_only_demo"
            }
        }
    }
    
    async def check_and_fallback(self, service_name: str) -> str:
        """
        检查服务可用性，不可用时返回降级方案名称
        返回: "available" | "fallback:{mode}" | "unavailable"
        """
        ...
```

#### 3.2.2 数据库表延迟创建

```python
# backend/core/lazy_table_creation.py

class LazyTableManager:
    """
    数据库表延迟创建管理器
    
    替代当前 startup_event 中的一次性 create_all()
    
    行为：
    1. 启动时只创建 Tier 0 核心模块的表
    2. 模块激活时创建该模块所需的表
    3. 表已存在时跳过（幂等操作）
    """
    
    TIER_0_TABLES = [
        "users", "user_roles", "sessions",
        "courses", "course_lessons", "course_enrollments",
    ]
    
    async def create_tables_for_module(self, module_name: str):
        """为指定模块创建所需的数据库表"""
        ...
```

### 3.3 前端：模块状态感知与 UX 优化

#### 3.3.1 模块状态服务

```typescript
// src/app/core/services/module-status.service.ts

@Injectable()
export class ModuleStatusService {
  private moduleStates$ = new BehaviorSubject<ModuleStatusMap>({});
  
  /**
   * 轮询后端模块状态（每 30 秒）
   * 前端缓存模块状态，避免每次请求都检查
   */
  async refreshModuleStates(): Promise<ModuleStatusMap> { ... }
  
  /**
   * 检查指定模块是否可用
   * 若未加载，触发激活并等待
   */
  async ensureModuleActive(moduleName: string): Promise<ModuleState> { ... }
  
  /**
   * 模块激活时的 UX 反馈
   * 显示 "正在启动 XX 功能..." 的进度遮罩
   */
  showModuleLoading(moduleName: string): void { ... }
}
```

#### 3.3.2 模块加载状态 UI

```
┌─────────────────────────────────────────────────────────────┐
│  底部状态栏（StatusBar）                                      │
│  [在线 ✓] [核心服务 ✓] [AI模块 ⏳ 加载中] [区块链 ○ 未激活]   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  功能模块卡片（用户点击进入时）                                 │
│  ┌─────────────────────────────────┐                        │
│  │  🤖 AI 实验室                    │                        │
│  │  ⏳ 功能模块正在启动，预计 3 秒... │                        │
│  │  ████████░░░░ 75%                │                        │
│  └─────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  模块不可用时的优雅提示                                        │
│  ┌─────────────────────────────────┐                        │
│  │  ⚠️ 区块链服务暂时不可用          │                        │
│  │  原因：Hyperledger 网络未连接    │                        │
│  │  [查看缓存数据] [重试] [了解更多] │                        │
│  └─────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.3 Angular 路由守卫

```typescript
// src/app/core/guards/module-active.guard.ts

@Injectable()
export class ModuleActiveGuard implements CanActivate {
  constructor(private moduleStatus: ModuleStatusService) {}
  
  async canActivate(route: ActivatedRouteSnapshot): Promise<boolean> {
    const moduleName = route.data['requiredModule'];
    if (!moduleName) return true;
    
    const state = await this.moduleStatus.ensureModuleActive(moduleName);
    
    if (state === 'active') return true;
    if (state === 'loading') {
      // 显示加载遮罩，等待激活
      this.moduleStatus.showModuleLoading(moduleName);
      return this.waitForActivation(moduleName);
    }
    if (state === 'degraded') {
      // 显示降级提示，允许继续
      return this.showDegradedWarning(moduleName);
    }
    // failed / disabled
    this.showUnavailableDialog(moduleName);
    return false;
  }
}
```

### 3.4 Electron：智能后端启动策略

#### 3.4.1 分阶段启动

```javascript
// electron/main.js - 后端启动优化

const BACKEND_STARTUP_PHASES = {
  phase1_core: {
    timeout: 5000,
    description: '启动核心服务',
    healthEndpoint: '/health?tier=0',
    onSuccess: () => showMainWindow(),  // 核心就绪即显示主窗口
  },
  phase1_preload: {
    timeout: 15000,
    description: '预加载高优先级模块',
    healthEndpoint: '/api/v1/system/health',
    background: true,  // 不阻塞 UI
  },
};

async function startBackendPhased() {
  // Phase 1: 启动最小核心
  splashStatus('正在启动核心服务...');
  backendProcess = spawn(pythonPath, ['run.py', '--tier=0']);
  await waitForHealth('/health?tier=0', 5000);
  
  // 核心就绪 → 立即显示主窗口
  mainWindow.show();
  splashWindow.close();
  
  // Phase 2: 后台预加载（不阻塞用户操作）
  backgroundPreloadTier1();
}
```

---

## 4. 容错与降级机制

### 4.1 模块级熔断器

```python
# backend/core/module_circuit_breaker.py

class ModuleCircuitBreaker:
    """
    模块级熔断器
    
    状态机:
    CLOSED → (连续失败 N 次) → OPEN → (超时后) → HALF_OPEN → (成功) → CLOSED
                                                                    → (失败) → OPEN
    
    行为：
    - CLOSED: 正常处理请求
    - OPEN: 立即返回降级响应，不尝试执行
    - HALF_OPEN: 允许 1 个探测请求，成功则恢复
    """
    
    def __init__(self, module_name: str, failure_threshold=3, timeout=60):
        self.module_name = module_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"
        self.failure_count = 0
    
    async def execute(self, func, fallback=None):
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.timeout:
                self.state = "HALF_OPEN"
            else:
                return await fallback() if fallback else raise ModuleUnavailableError()
        
        try:
            result = await func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            return await fallback() if fallback else raise
```

### 4.2 依赖服务降级矩阵

| 依赖服务 | 不可用时的降级方案 | 用户感知 |
|---------|-----------------|---------|
| **Redis** | 改用内存缓存 + SQLite 会话 | 重启后需重新登录（提示） |
| **Neo4j** | 改用 SQL 关联查询 | 知识图谱功能简化 |
| **OpenAI API** | 本地模板 + 规则引擎 | AI 功能变为基础模式 |
| **Vircadia** | 2D 模拟 / 视频替代 | AR/VR 功能不可用 |
| **Docker** | 受限沙箱 / 只读模式 | 代码执行受限提示 |
| **PostgreSQL** | SQLite 本地存储 | 数据仅本地保存（提示） |
| **Hyperledger** | 本地积分缓存 | 积分操作待同步提示 |

### 4.3 模块故障恢复流程

```
模块请求失败
    │
    ├── 重试 1 次（立即）
    │     ├── 成功 → 正常响应
    │     └── 失败
    │           │
    │           ├── 重试 2 次（延迟 500ms）
    │           │     ├── 成功 → 正常响应
    │           │     └── 失败
    │           │           │
    │           │           ├── 检查依赖服务状态
    │           │           │     ├── 依赖不可用 → 切换降级模式
    │           │           │     └── 依赖正常 → 模块内部错误
    │           │           │           │
    │           │           │           ├── 熔断器打开（停止请求 60s）
    │           │           │           └── 返回降级响应给用户
    │           │           │
    │           │           └── 记录错误日志
    │           │
    │           └── 返回错误
    │
    └── 前端显示模块状态徽章（降级/不可用）
```

---

## 5. 实施方案

### 5.1 Phase 1：基础设施（2 周）

**目标**：实现模块注册表和懒加载引擎

- [ ] 创建 `backend/core/module_registry.py`（ModuleSpec / ModuleLazyLoader）
- [ ] 创建 `backend/core/module_activation_middleware.py`
- [ ] 重构 `main.py` 启动流程，仅注册 Tier 0 模块
- [ ] 实现 `ModuleStatusService`（前端）
- [ ] 实现 `/api/v1/system/modules` 状态 API
- [ ] 修复 `proxy.conf.json`（已完成 ✅）

**验收标准**：
- 后端冷启动时间 < 5 秒（仅核心模块）
- `/health` 端点在 3 秒内返回
- 前端状态栏正确显示后端状态

### 5.2 Phase 2：模块分级与迁移（3 周）

**目标**：将现有 60+ 路由模块按 Tier 分级

- [ ] Tier 0 模块迁移（auth/course/user/health）
- [ ] Tier 1 模块迁移（AI/payment/exam/learning）
- [ ] Tier 2 模块迁移（blockchain/AR/creativity/collab）
- [ ] Tier 3 模块迁移（openhydra/hardware/federated）
- [ ] 每个模块添加 `module_spec.py` 描述文件
- [ ] 数据库表按模块拆分创建

**验收标准**：
- 所有现有 API 接口功能不变
- 每个模块可独立激活/去激活
- 单个模块失败不影响其他模块

### 5.3 Phase 3：容错与降级（2 周）

**目标**：实现完整的故障隔离和降级机制

- [ ] 实现 `ModuleCircuitBreaker`
- [ ] 实现 `ServiceDependency` 降级管理器
- [ ] 为每个 Tier 2/3 模块实现降级方案
- [ ] 前端模块加载状态 UI
- [ ] Angular 路由守卫（ModuleActiveGuard）
- [ ] 模块故障通知机制

**验收标准**：
- Redis 不可用时系统仍可运行（内存降级）
- 外部 API 不可用时显示友好提示
- 模块崩溃后 60 秒内自动恢复尝试

### 5.4 Phase 4：Electron 集成优化（1 周）

**目标**：Electron 桌面端启动策略优化

- [ ] 修改 `electron/main.js` 分阶段启动后端
- [ ] 核心就绪即显示主窗口（不等待所有模块）
- [ ] Splash 屏显示模块加载进度
- [ ] 模块状态托盘图标

**验收标准**：
- 用户从点击 App 到可操作 < 10 秒
- Splash 屏显示真实的模块加载进度
- 后台预加载不卡顿主界面

---

## 6. 监控与可观测性

### 6.1 模块状态仪表盘

```
┌────────────────────────────────────────────────────┐
│  MatuX 系统健康仪表盘                                │
│  整体状态: ✅ 正常 (23/25 模块可用)                  │
├────────────────────────────────────────────────────┤
│  Tier 0 核心层      ████████████ 4/4 ✅             │
│  Tier 1 高优先级    ██████████░░ 5/5 ✅             │
│  Tier 2 按需激活    ██████░░░░░ 8/10 ⚠️             │
│  Tier 3 延迟激活    ░░░░░░░░░░░ 0/6 ○              │
├────────────────────────────────────────────────────┤
│  依赖服务:                                          │
│  Redis: ✅ 已连接    Neo4j: ⚠️ 降级模式             │
│  Docker: ❌ 不可用   OpenAI: ✅ 已连接              │
└────────────────────────────────────────────────────┘
```

### 6.2 日志规范

```
# 模块生命周期日志格式
[INFO]  [module:ai_service] 模块激活开始 (Tier 1)
[INFO]  [module:ai_service] 依赖检查: openai_api=available, redis=available
[INFO]  [module:ai_service] 数据库表创建: ai_requests (已存在，跳过)
[INFO]  [module:ai_service] 路由注册完成: /api/v1/ai/*
[INFO]  [module:ai_service] 模块激活完成 (耗时: 342ms)

# 模块故障日志
[WARN]  [module:blockchain] 依赖服务不可用: hyperledger_fabric
[WARN]  [module:blockchain] 切换至降级模式: cache_fallback
[INFO]  [module:blockchain] 模块降级运行 (功能受限)

# 熔断器日志
[ERROR] [breaker:ar_vr_lab] 连续失败 3 次，熔断器打开 (60s)
[INFO]  [breaker:ar_vr_lab] 熔断器半开，尝试探测请求
[INFO]  [breaker:ar_vr_lab] 探测成功，熔断器关闭
```

---

## 7. 配置规范

### 7.1 环境变量新增配置

```bash
# .env 新增配置项

# 模块懒加载配置
MODULE_LAZY_LOADING_ENABLED=true          # 是否启用懒加载（false=全量加载）
MODULE_TIER0_TIMEOUT=5000                 # Tier 0 启动超时（ms）
MODULE_TIER1_PRELOAD_DELAY=3000           # Tier 1 预加载延迟（ms）
MODULE_ACTIVATION_TIMEOUT=10000           # 单模块激活超时（ms）
MODULE_CIRCUIT_BREAKER_THRESHOLD=3        # 模块熔断失败阈值
MODULE_CIRCUIT_BREAKER_TIMEOUT=60         # 模块熔断超时（秒）

# 模块禁用配置（通过环境变量禁用特定模块）
DISABLE_MODULE_BLOCKCHAIN=false
DISABLE_MODULE_AR_VR=false
DISABLE_MODULE_DIGITAL_TWIN=false
DISABLE_MODULE_FEDERATED=false

# 降级模式配置
FALLBACK_REDIS=memory                     # Redis 降级: memory|none
FALLBACK_NEO4J=sql_graph                  # Neo4j 降级: sql_graph|none
FALLBACK_OPENAI=templates                 # OpenAI 降级: templates|none
FALLBACK_DOCKER=restricted                # Docker 降级: restricted|none
```

### 7.2 模块描述文件规范

每个路由模块目录下添加 `module_spec.py`：

```python
# backend/routes/module_specs/ai_service_spec.py

from core.module_registry import ModuleSpec, ModuleTier

AI_SERVICE_SPEC = ModuleSpec(
    name="ai_service",
    tier=ModuleTier.TIER_1_HIGH,
    router_factory=lambda: __import__('routes.ai_routes').ai_routes.router,
    prefix="/api/v1",
    tags=["AI服务"],
    dependencies=[],
    required_services=["openai_api"],  # 依赖 OpenAI
    # 降级配置
    fallback_services={"openai_api": "template_mode"},
)
```

---

## 8. 迁移兼容性

### 8.1 向后兼容保证

- 所有现有 API 路径不变
- 前端无需修改（除状态栏增强外）
- 通过 `MODULE_LAZY_LOADING_ENABLED=false` 可回退到全量加载模式
- 渐进式迁移，支持新旧模式并存

### 8.2 数据迁移

- 数据库 Schema 不变
- 无数据格式变更
- 表创建从一次性 `create_all()` 改为按模块分批创建（幂等操作）

---

## 9. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 懒加载引入首次请求延迟 | 高 | 中 | Tier 1 后台预加载，用户无感知 |
| 模块依赖关系复杂导致激活链过长 | 中 | 高 | 严格限制依赖深度，最多 2 级 |
| 降级模式功能缺失影响用户 | 中 | 中 | 明确提示用户，提供手动重试 |
| 熔断器误判导致模块长时间不可用 | 低 | 中 | 半开探测机制 + 管理员手动重置 |
| 迁移期间新旧模式冲突 | 中 | 高 | 环境变量控制，支持快速回退 |

---

## 10. 验收标准总览

| 指标 | 当前值 | 目标值 | 验收方法 |
|------|--------|--------|---------|
| 后端冷启动时间 | ~30s | < 5s | 计时 `/health` 首次可用 |
| 用户可操作等待时间 | ~90s | < 10s | Electron 启动到主窗口显示 |
| 单模块失败影响范围 | 整个系统崩溃 | 仅该模块不可用 | 故障注入测试 |
| Redis 不可用时系统可用性 | 0% | > 80% 功能可用 | 依赖断网测试 |
| 模块激活平均延迟 | N/A | < 2s | 模块首次请求响应时间 |
| 前端状态栏准确率 | 0%（当前 bug） | 100% | 人工验证 |

---

## 11. 附录：现有 Bug 修复记录

### 11.1 状态栏"后端未启动"误报 Bug

**问题根因**：`proxy.conf.json` 仅代理 `/api/*` 路径，`/health` 端点请求未到达后端

**修复方案**：
1. `proxy.conf.json` 添加 `/health`、`/metrics`、`/registry` 代理规则
2. `status-bar.component.ts` 改用相对路径 `/health` 代替绝对 URL

**涉及文件**：
- `g:\iMato\proxy.conf.json`
- `g:\iMato\src\app\shared\components\status-bar\status-bar.component.ts`
