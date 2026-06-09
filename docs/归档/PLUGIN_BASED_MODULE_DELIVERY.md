# MatuX 学习端设备评估与插件化模块交付需求文档

**文档编号**: MATU-ARCH-2026-002  
**版本**: v1.0  
**状态**: 需求评审  
**作者**: 系统架构组  
**日期**: 2026-06-06  
**依赖文档**: MODULAR_LAZY_LOADING_ARCHITECTURE.md (MATU-ARCH-2026-001)  

---

## 1. 背景与动机

### 1.1 与懒加载架构的关系

MATU-ARCH-2026-001 解决了模块"启动时加载"的性能问题，将 60+ 路由模块按 Tier 分级，实现了按需激活。但该方案仍假设**所有模块代码已存在于本地**，只是延迟了加载时机。

本文档在此基础上进一步解决：

| 问题 | 懒加载架构（已解决） | 插件化交付（本文档） |
|------|---------------------|---------------------|
| 模块启动慢 | ✅ 延迟激活 | ✅ 延迟激活 |
| 安装包体积过大 | ❌ 全量打包 | ✅ 按需下载 |
| 设备不兼容模块报错 | ❌ 加载后才发现 | ✅ 预评估+提示 |
| 用户不需要某些功能 | ❌ 无法卸载 | ✅ 按需安装/卸载 |
| 模块独立更新 | ❌ 需要全量更新 | ✅ 插件独立更新 |
| 低配设备运行困难 | ❌ 无差异化 | ✅ 智能推荐适配方案 |

### 1.2 当前安装包问题分析

MatuX 桌面端（Electron）当前安装包包含所有功能模块：

```
当前安装包构成（估算）：
├── Electron 运行时           ~120 MB
├── Angular 前端 bundle       ~15 MB（全量编译）
├── Python 后端代码           ~8 MB（60+ 路由 + 75 服务）
├── Python 依赖 (venv)        ~800 MB（含 PyTorch/MediaPipe/TF 等）
├── 3D/AR/VR 资源             ~200 MB
├── AI 模型文件               ~500 MB（本地推理模型）
├── 离线课件缓存              ~100 MB
└── 总计                      ~1.7 GB
```

**问题**：大部分用户实际只使用 30% 的功能（课程学习、AI 辅助、考试），却需要下载完整的 1.7 GB 包。

### 1.3 目标用户设备画像

| 设备类型 | 典型配置 | 适用模块 | 占比估算 |
|---------|---------|---------|---------|
| **低配 PC** | i3/4GB/无GPU/50GB HDD | 核心课程、文本AI、考试 | ~25% |
| **中配 PC** | i5/8GB/集成显卡/256GB SSD | + 代码沙箱、基础AI、协作 | ~45% |
| **高配 PC** | i7/16GB/GTX1650+/512GB SSD | + AR/VR、数字孪生、创意引擎 | ~20% |
| **专业工作站** | i9/32GB/RTX3060+/1TB NVMe | + 联邦学习、模型训练、硬件仿真 | ~10% |

---

## 2. 设备能力评估框架

### 2.1 评估维度

Electron 主进程在首次启动和设置变更时，自动执行设备能力评估：

#### 2.1.1 硬件能力检测

```typescript
// electron/device-profiler.ts

interface HardwareProfile {
  cpu: {
    arch: string;           // x64, arm64
    cores: number;          // 物理核心数
    model: string;          // CPU 型号
    benchmarkScore: number; // 内部基准分 (0~1000)
  };
  memory: {
    totalMB: number;        // 总内存
    availableMB: number;    // 可用内存
    speedMHz: number;       // 内存频率（可选）
  };
  gpu: {
    hasDedicatedGPU: boolean;     // 是否有独立显卡
    gpuName: string;              // 显卡名称
    vramMB: number;               // 显存大小
    supportsWebGL2: boolean;      // WebGL 2.0 支持
    supportsWebGPU: boolean;      // WebGPU 支持
    supportsCUDA: boolean;        // CUDA 支持（NVIDIA）
    supportsOpenCL: boolean;      // OpenCL 支持
  };
  storage: {
    totalGB: number;        // 磁盘总量
    freeGB: number;         // 磁盘剩余
    type: 'hdd' | 'ssd';   // 磁盘类型（通过读写速度推断）
  };
  peripherals: {
    hasCamera: boolean;           // 摄像头
    hasMicrophone: boolean;       // 麦克风
    hasUSBDevices: boolean;       // USB 设备连接
    hasGamepad: boolean;          // 手柄/控制器
  };
  network: {
    type: 'ethernet' | 'wifi' | 'cellular';
    bandwidthMbps: number;        // 估算带宽
    isMetered: boolean;           // 是否计量网络
  };
  display: {
    resolution: { width: number; height: number };
    pixelRatio: number;
    refreshRateHz: number;
  };
}
```

#### 2.1.2 软件环境检测

```typescript
interface SoftwareProfile {
  os: {
    platform: 'win32' | 'darwin' | 'linux';
    version: string;
    arch: 'x64' | 'arm64';
  };
  runtime: {
    pythonVersion: string;         // Python 版本
    pythonPath: string;            // Python 路径
    nodeVersion: string;           // Node.js 版本
  };
  containers: {
    dockerInstalled: boolean;
    dockerRunning: boolean;
    dockerVersion: string;
    kubectlInstalled: boolean;     // K8s CLI
  };
  hardware_tools: {
    arduinoCliInstalled: boolean;  // Arduino CLI
    platformioInstalled: boolean;  // PlatformIO
    edgeImpulseCli: boolean;       // Edge Impulse CLI
  };
  connectivity: {
    redisAvailable: boolean;       // 本地/远程 Redis
    neo4jAvailable: boolean;       // Neo4j
    hyperledgerAvailable: boolean; // Hyperledger Fabric
    vircadiaAvailable: boolean;    // Vircadia Server
  };
}
```

### 2.2 设备评级算法

```typescript
// electron/device-profiler.ts

enum DeviceClass {
  BASIC = 'basic',         // 基础级：核心学习功能
  STANDARD = 'standard',   // 标准级：+ AI辅助 + 代码沙箱
  ADVANCED = 'advanced',   // 进阶级：+ AR/VR + 创意引擎
  PROFESSIONAL = 'professional', // 专业级：+ 联邦学习 + 模型训练
}

interface DeviceAssessment {
  deviceClass: DeviceClass;
  score: number;                    // 综合得分 0~100
  scores: {
    cpuScore: number;
    memoryScore: number;
    gpuScore: number;
    storageScore: number;
    networkScore: number;
    peripheralScore: number;
  };
  compatiblePluginTiers: string[];  // 可安装的插件层级
  recommendedPlugins: string[];     // 推荐安装的插件
  incompatiblePlugins: string[];    // 不兼容的插件
  warnings: string[];               // 警告信息
}

/**
 * 设备评级阈值
 */
const DEVICE_THRESHOLDS = {
  [DeviceClass.BASIC]: {
    minMemory: 4096,          // 4GB
    minCores: 2,
    minStorage: 10,           // 10GB 可用
    minBandwidth: 1,          // 1 Mbps
    requireGPU: false,
  },
  [DeviceClass.STANDARD]: {
    minMemory: 8192,          // 8GB
    minCores: 4,
    minStorage: 20,           // 20GB 可用
    minBandwidth: 5,          // 5 Mbps
    requireGPU: false,        // 集成显卡可
  },
  [DeviceClass.ADVANCED]: {
    minMemory: 16384,         // 16GB
    minCores: 6,
    minStorage: 50,           // 50GB 可用
    minBandwidth: 10,         // 10 Mbps
    requireGPU: true,         // 需要独立显卡
    minVRAM: 2048,            // 2GB 显存
  },
  [DeviceClass.PROFESSIONAL]: {
    minMemory: 32768,         // 32GB
    minCores: 8,
    minStorage: 100,          // 100GB 可用
    minBandwidth: 50,         // 50 Mbps
    requireGPU: true,
    minVRAM: 6144,            // 6GB 显存
    requireCUDA: true,        // 需要 CUDA
  },
};
```

### 2.3 评估时机

| 时机 | 评估范围 | 触发方式 |
|------|---------|---------|
| **首次启动** | 全量评估 | Electron 主进程自动执行 |
| **系统设置变更** | 硬件变更检测 | 定时检查（每周） |
| **用户手动触发** | 全量评估 | 设置页"重新检测设备"按钮 |
| **插件安装前** | 针对性检查 | 插件安装流程触发 |
| **后端服务变更** | 软件环境检查 | 后端启动后自动检测 |

### 2.4 评估结果存储

```typescript
// 存储在 Electron userData 目录
// {userData}/device-profile.json

{
  "version": "1.0",
  "assessedAt": "2026-06-06T10:00:00Z",
  "hardware": { /* HardwareProfile */ },
  "software": { /* SoftwareProfile */ },
  "assessment": { /* DeviceAssessment */ },
  "installedPlugins": ["ar-vr-lab", "creativity-engine"],
  "pluginHistory": [
    { "plugin": "digital-twin", "action": "rejected", "reason": "insufficient_memory", "at": "..." }
  ]
}
```

---

## 3. 插件化模块定义

### 3.1 插件包格式

每个可插件化的模块打包为独立的 MatuX Plugin Package（.mxp 格式）：

```
ar-vr-lab.mxp (ZIP 格式)
├── manifest.json          # 插件清单
├── backend/
│   ├── routes/            # 后端路由文件
│   ├── services/          # 后端服务文件
│   ├── models/            # ORM 模型文件
│   └── migrations/        # 数据库迁移脚本
├── frontend/
│   ├── bundle.js          # 编译后的 Angular 模块
│   ├── styles.css         # 模块样式
│   └── assets/            # 图片、3D 模型等资源
├── python-deps/
│   └── requirements.txt   # 额外 Python 依赖
├── node-deps/
│   └── package.json       # 额外 Node.js 依赖
└── resources/
    ├── 3d-models/         # 3D 模型文件
    ├── textures/          # 贴图文件
    └── ml-models/         # ML 模型文件
```

### 3.2 插件清单规范（manifest.json）

```json
{
  "id": "ar-vr-lab",
  "name": "AR/VR 实验室",
  "nameEn": "AR/VR Lab",
  "version": "2.1.0",
  "description": "增强现实与虚拟现实实验环境，支持手势识别、3D 建模和虚拟课堂",
  "author": "MatuX Team",
  "category": "immersive-tech",
  "size": {
    "download": "85MB",
    "installed": "220MB"
  },
  "requirements": {
    "deviceClass": "advanced",
    "minMemory": 16384,
    "minVRAM": 2048,
    "requireGPU": true,
    "requireCamera": true,
    "requireWebGL2": true,
    "minStorage": 500,
    "pythonPackages": ["mediapipe>=0.10", "opencv-python>=4.8"],
    "systemPackages": [],
    "externalServices": ["vircadia"],
    "optionalServices": ["redis"]
  },
  "dependencies": {
    "required": ["core"],
    "optional": ["ai-service", "collaborative-editor"]
  },
  "provides": {
    "routes": ["/api/v1/ar-vr/*", "/api/v1/ar-lab/*", "/api/v1/ar-rewards/*"],
    "frontendModules": ["ArLabModule", "VircadiaModule"],
    "capabilities": ["gesture-recognition", "3d-viewer", "vr-classroom"]
  },
  "degradation": {
    "noCamera": "手势识别不可用，可使用鼠标替代操作",
    "noGPU": "3D 渲染降级为 2D 模拟视图",
    "noVircadia": "虚拟课堂不可用，AR 实验仍可离线使用"
  },
  "permissions": [
    "camera",
    "microphone",
    "gpu-compute",
    "local-network"
  ],
  "changelog": "修复手势识别延迟问题，新增 VR 白板协作功能",
  "icon": "icon.png",
  "screenshots": ["screenshot1.png", "screenshot2.png"]
}
```

### 3.3 插件分级体系

基于设备需求和功能复杂度，将插件分为 4 个层级：

#### Plugin Tier A — 通用增强型（所有设备可安装）

| 插件 ID | 名称 | 大小 | 核心依赖 | 说明 |
|---------|------|------|---------|------|
| `ai-tutor` | AI 个性化教师 | ~15 MB | OpenAI API（可降级） | 个性化学习路径、智能答疑 |
| `exam-pro` | 考试增强包 | ~8 MB | 无 | 防作弊检测、智能出题 |
| `achievement-plus` | 成就系统增强 | ~5 MB | 无 | 徽章系统、排行榜增强 |
| `offline-kit` | 离线学习工具包 | ~12 MB | 无 | 离线课件缓存、进度同步 |
| `collab-editor` | 协作编辑器 | ~10 MB | WebSocket | 实时协作编程、文档编辑 |
| `knowledge-graph` | 知识图谱可视化 | ~8 MB | 无（Neo4j 可选） | 知识点关联图谱 |
| `multimedia-plus` | 多媒体资源增强 | ~20 MB | 无 | 视频播放器、3D 预览器 |

#### Plugin Tier B — 标准扩展型（Standard+ 设备）

| 插件 ID | 名称 | 大小 | 核心依赖 | 说明 |
|---------|------|------|---------|------|
| `code-sandbox` | 代码沙箱环境 | ~50 MB | Docker（可降级） | 安全代码执行环境 |
| `blockchain-cert` | 区块链证书 | ~30 MB | Hyperledger（可降级） | 学习成果区块链存证 |
| `learning-analytics` | 学习行为分析 | ~15 MB | 无 | 学习路径分析、行为特征 |
| `content-store` | 内容商店 | ~10 MB | 无 | 课件/资源市场 |
| `dynamic-course` | 动态课程生成 | ~25 MB | OpenAI API | AI 自动生成课程 |
| `finance-module` | 财务管理 | ~8 MB | 无 | 学习积分、交易管理 |

#### Plugin Tier C — 高级功能型（Advanced+ 设备）

| 插件 ID | 名称 | 大小 | 核心依赖 | 说明 |
|---------|------|------|---------|------|
| `ar-vr-lab` | AR/VR 实验室 | ~220 MB | GPU + Camera + WebGL2 | 手势识别、虚拟课堂、AR 实验 |
| `creativity-engine` | 创意引擎 | ~80 MB | GPU + OpenAI API | AI 创意生成、艺术创作 |
| `digital-twin` | 数字孪生实验室 | ~150 MB | Docker + GPU | 电路仿真、物理模拟 |
| `vr-3d-editor` | VR 3D 编辑器 | ~180 MB | GPU + WebGL2 | VR 环境中的 3D 建模 |
| `gesture-recognition` | 手势识别系统 | ~120 MB | Camera + GPU + MediaPipe | 实时手势追踪与识别 |
| `voice-lab` | 语音实验室 | ~60 MB | Microphone + GPU | 语音识别、发音纠正 |

#### Plugin Tier D — 专业级（Professional 设备）

| 插件 ID | 名称 | 大小 | 核心依赖 | 说明 |
|---------|------|------|---------|------|
| `ai-sandbox` | AI 沙箱环境 | ~300 MB | K8s + Docker + GPU | OpenHydra 云端 AI 实验 |
| `federated-learning` | 联邦学习 | ~200 MB | GPU + CUDA + 多节点 | 分布式模型训练 |
| `model-bench` | 模型基准测试 | ~150 MB | GPU + CUDA | AI 模型性能评测 |
| `hardware-cert` | 硬件认证 | ~80 MB | USB + ESP32/FPGA | 硬件实验与认证 |
| `sensor-lab` | 传感器实验室 | ~40 MB | USB + MQTT | 物理传感器数据采集 |
| `tinyml-studio` | TinyML 工作室 | ~100 MB | USB + PlatformIO | 边缘设备 ML 部署 |

---

## 4. 插件生命周期管理

### 4.1 完整生命周期

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  评估    │──→│  推荐    │──→│  下载    │──→│  安装    │──→│  激活    │
│ Assess   │   │ Recommend│   │ Download │   │ Install  │   │ Activate │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                              │
     ┌──────────┐   ┌──────────┐   ┌──────────┐              │
     │  卸载    │←──│  更新    │←──│  运行    │←─────────────┘
     │Uninstall │   │  Update  │   │  Running │
     └──────────┘   └──────────┘   └──────────┘
```

### 4.2 插件评估流程（Assess）

```typescript
// electron/plugin-assessor.ts

class PluginAssessor {
  /**
   * 评估插件与当前设备的兼容性
   */
  async assessPlugin(
    pluginManifest: PluginManifest,
    deviceProfile: DeviceAssessment
  ): Promise<PluginCompatibility> {
    const checks: CompatibilityCheck[] = [];

    // 1. 设备等级检查
    checks.push(this.checkDeviceClass(pluginManifest, deviceProfile));

    // 2. 内存检查
    checks.push(this.checkMemory(pluginManifest, deviceProfile));

    // 3. GPU 检查
    checks.push(this.checkGPU(pluginManifest, deviceProfile));

    // 4. 存储空间检查
    checks.push(this.checkStorage(pluginManifest, deviceProfile));

    // 5. 外设检查（摄像头、麦克风等）
    checks.push(this.checkPeripherals(pluginManifest, deviceProfile));

    // 6. 软件依赖检查
    checks.push(this.checkSoftwareDeps(pluginManifest, deviceProfile));

    // 7. 外部服务检查
    checks.push(this.checkExternalServices(pluginManifest, deviceProfile));

    // 8. 磁盘类型对性能的影响
    checks.push(this.checkStoragePerformance(pluginManifest, deviceProfile));

    return {
      compatible: checks.every(c => c.passed || c.optional),
      score: this.calculateScore(checks),
      checks,
      recommendation: this.generateRecommendation(checks),
    };
  }
}

interface CompatibilityCheck {
  name: string;
  passed: boolean;
  optional: boolean;       // 是否可选（不通过也可降级使用）
  severity: 'block' | 'warn' | 'info';
  message: string;
  degradation?: string;    // 降级方案描述
}
```

### 4.3 插件推荐引擎

```typescript
// electron/plugin-recommender.ts

class PluginRecommender {
  /**
   * 基于设备评估结果，生成个性化的插件推荐列表
   */
  async generateRecommendations(
    deviceProfile: DeviceAssessment,
    userPreferences: UserPreferences,
    installedPlugins: string[]
  ): Promise<PluginRecommendation[]> {

    // 1. 过滤设备不兼容的插件
    const compatible = allPlugins.filter(p =>
      this.isCompatible(p, deviceProfile)
    );

    // 2. 排除已安装的插件
    const uninstalled = compatible.filter(p =>
      !installedPlugins.includes(p.id)
    );

    // 3. 按用户偏好排序
    const ranked = this.rankByPreference(uninstalled, userPreferences);

    // 4. 按依赖关系排序（被依赖的排在前面）
    const ordered = this.topologicalSort(ranked);

    // 5. 生成推荐包（Bundle）
    return this.createBundles(ordered, deviceProfile);
  }

  /**
   * 推荐套餐示例
   */
  RECOMMENDED_BUNDLES = {
    "stem-starter": {
      name: "STEM 入门套件",
      description: "适合基础学习，包含核心 AI 辅助和离线工具",
      plugins: ["ai-tutor", "offline-kit", "exam-pro"],
      totalSize: "35MB",
      minDeviceClass: "basic",
    },
    "developer-pack": {
      name: "开发者套件",
      description: "编程学习全套，含代码沙箱和协作编辑",
      plugins: ["ai-tutor", "code-sandbox", "collab-editor", "dynamic-course"],
      totalSize: "100MB",
      minDeviceClass: "standard",
    },
    "immersive-lab": {
      name: "沉浸式实验室",
      description: "AR/VR 全套体验，需高端设备",
      plugins: ["ar-vr-lab", "vr-3d-editor", "gesture-recognition", "voice-lab"],
      totalSize: "580MB",
      minDeviceClass: "advanced",
    },
    "ai-researcher": {
      name: "AI 研究员套件",
      description: "联邦学习、模型训练与评测",
      plugins: ["federated-learning", "model-bench", "ai-sandbox"],
      totalSize: "650MB",
      minDeviceClass: "professional",
    },
  };
}
```

### 4.4 插件下载流程

```typescript
// electron/plugin-downloader.ts

class PluginDownloader {
  private PLUGIN_REGISTRY_URL = 'https://plugins.matu.app/registry/v1';
  private CDN_BASE_URL = 'https://cdn.matu.app/plugins';

  /**
   * 下载插件包
   * 支持断点续传、增量更新、带宽适配
   */
  async downloadPlugin(
    pluginId: string,
    version: string,
    options: DownloadOptions = {}
  ): Promise<DownloadResult> {
    // 1. 从注册表获取下载清单
    const manifest = await this.fetchManifest(pluginId, version);

    // 2. 检查磁盘空间
    const hasSpace = await this.checkDiskSpace(manifest.size.installed);
    if (!hasSpace) throw new InsufficientStorageError();

    // 3. 生成下载计划（大文件分片）
    const plan = this.createDownloadPlan(manifest, options);

    // 4. 执行下载（支持断点续传）
    const result = await this.executeDownload(plan, {
      onProgress: (progress) => this.notifyProgress(pluginId, progress),
      onFileComplete: (file) => this.verifyChecksum(file),
    });

    // 5. 校验完整性
    await this.verifyPackageIntegrity(result.localPath, manifest.checksums);

    return result;
  }

  /**
   * 增量更新：只下载变更的文件
   */
  async downloadIncremental(
    pluginId: string,
    fromVersion: string,
    toVersion: string
  ): Promise<DownloadResult> {
    const diff = await this.fetchVersionDiff(pluginId, fromVersion, toVersion);
    // 只下载 changed / added 的文件
    // 删除 removed 的文件
    return this.executeDownload(diff.plan);
  }
}
```

### 4.5 插件安装流程

```typescript
// electron/plugin-installer.ts

class PluginInstaller {
  /**
   * 安装插件到本地
   * 
   * 步骤：
   * 1. 解压 .mxp 包到插件目录
   * 2. 安装额外 Python 依赖（pip install）
   * 3. 注册后端路由到 LazyLoader
   * 4. 加载前端模块到 Angular
   * 5. 创建数据库表（迁移脚本）
   * 6. 更新插件注册表
   */
  async install(packagePath: string): Promise<InstallResult> {
    // 1. 解压到 {userData}/plugins/{pluginId}/
    const installDir = await this.extractPackage(packagePath);

    // 2. 读取 manifest.json
    const manifest = await this.readManifest(installDir);

    // 3. 安装 Python 依赖
    if (manifest.requirements?.pythonPackages) {
      await this.installPythonDeps(installDir, manifest.requirements.pythonPackages);
    }

    // 4. 注册后端路由
    await this.registerBackendRoutes(installDir, manifest);

    // 5. 加载前端模块
    await this.loadFrontendModule(installDir, manifest);

    // 6. 执行数据库迁移
    if (manifest.provides?.migrations) {
      await this.runMigrations(installDir, manifest.provides.migrations);
    }

    // 7. 更新本地插件注册表
    await this.updateRegistry(manifest);

    return { success: true, pluginId: manifest.id, version: manifest.version };
  }

  /**
   * 卸载插件
   * 反向执行安装步骤，保留用户数据（可选）
   */
  async uninstall(pluginId: string, keepData = false): Promise<void> {
    await this.deactivateRoutes(pluginId);
    await this.unloadFrontendModule(pluginId);
    if (!keepData) await this.dropTables(pluginId);
    await this.removeFiles(pluginId);
    await this.removeFromRegistry(pluginId);
  }
}
```

### 4.6 插件激活与热加载

插件安装完成后，接入 MATU-ARCH-2026-001 的懒加载引擎：

```python
# backend/core/plugin_loader.py

class PluginLoader:
    """
    插件加载器 — 桥接插件系统与懒加载引擎
    
    将已安装的插件自动注册为 ModuleSpec，
    由 ModuleLazyLoader 统一管理激活/去激活。
    """
    
    PLUGIN_DIR = os.path.join(get_user_data_dir(), "plugins")
    
    def discover_installed_plugins(self) -> list[PluginInfo]:
        """扫描插件目录，发现所有已安装插件"""
        ...
    
    def plugin_to_module_spec(self, plugin: PluginInfo) -> ModuleSpec:
        """将插件清单转换为 ModuleSpec，注入懒加载引擎"""
        ...
    
    async def hot_load_plugin(self, plugin_id: str):
        """
        热加载插件（不重启后端）
        1. 动态 import 路由模块
        2. 注册到 FastAPI app
        3. 创建所需数据库表
        """
        ...
    
    async def hot_unload_plugin(self, plugin_id: str):
        """
        热卸载插件（不重启后端）
        1. 从 FastAPI app 移除路由
        2. 清理模块缓存
        3. 更新模块状态
        """
        ...
```

---

## 5. 前端 UI 设计

### 5.1 插件商店页面

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MatuX 功能中心                                          [搜索插件...]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📊 设备评估报告                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  设备等级: ⭐⭐⭐ 进阶 (Advanced)                                │  │
│  │  CPU: i7-12700H (8核)  |  内存: 16GB  |  GPU: RTX 3060 (6GB)    │  │
│  │  存储: 256GB 可用 (SSD)  |  摄像头: ✅  |  网络: 100Mbps        │  │
│  │                                                                   │  │
│  │  兼容插件: Tier A ✅ | Tier B ✅ | Tier C ✅ | Tier D ⚠️ 部分   │  │
│  │  [重新检测]  [查看详情]                                           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  🎯 推荐套餐                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ STEM 入门   │  │ 开发者套件  │  │ 沉浸式实验  │  │ AI 研究员   │  │
│  │ 35MB · 3插件│  │ 100MB · 4个 │  │ 580MB · 4个 │  │ 650MB · 3个 │  │
│  │ ✅ 兼容     │  │ ✅ 兼容     │  │ ✅ 兼容     │  │ ⚠️ 需专业级 │  │
│  │ [一键安装]  │  │ [一键安装]  │  │ [一键安装]  │  │ [查看详情]  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                         │
│  📦 全部插件 (按分类)                                                   │
│  [全部] [AI 智能] [沉浸式] [开发工具] [区块链] [硬件] [分析]           │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🤖 AI 个性化教师      v2.1.0  15MB   ✅ 已安装                   │  │
│  │    个性化学习路径、智能答疑、自适应推荐                             │  │
│  │    依赖: OpenAI API (可降级)  [管理] [更新]                       │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ 🔬 AR/VR 实验室       v1.8.0  220MB  ⬇️ 可安装                   │  │
│  │    手势识别、虚拟课堂、AR 实验                                     │  │
│  │    需要: GPU ✅ | Camera ✅ | WebGL2 ✅   [安装] [详情]           │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ 🔗 区块链证书          v1.2.0  30MB   ⚠️ 降级可用                 │  │
│  │    学习成果链上存证                                                │  │
│  │    需要: Hyperledger ❌ (缓存模式可用)  [安装] [详情]             │  │
│  ├───────────────────────────────────────────────────────────────────┤  │
│  │ 🏗️ 数字孪生实验室     v1.5.0  150MB  ⬇️ 可安装                   │  │
│  │    电路仿真、物理模拟                                              │  │
│  │    需要: Docker ✅ | GPU ✅   [安装] [详情]                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 插件安装确认弹窗

```
┌───────────────────────────────────────────────────┐
│  安装 AR/VR 实验室 v1.8.0                         │
├───────────────────────────────────────────────────┤
│                                                   │
│  📦 包大小: 220MB (安装后约 580MB)                │
│  ⏱️ 预计下载: 约 2 分钟 (当前网络 100Mbps)        │
│                                                   │
│  ✅ 兼容性检查全部通过:                           │
│  ├── ✅ GPU: RTX 3060 (满足 WebGL2 + CUDA)        │
│  ├── ✅ 摄像头: 已检测到 USB 摄像头               │
│  ├── ✅ 内存: 16GB (需要 16GB)                    │
│  ├── ✅ 存储: 256GB 可用 (需要 580MB)             │
│  ├── ⚠️ Vircadia 服务: 未连接 (降级为 2D 模拟)    │
│  └── ✅ Python 依赖: mediapipe, opencv (自动安装) │
│                                                   │
│  📋 将安装以下组件:                               │
│  ├── AR/VR 实验室核心                             │
│  ├── 手势识别引擎 (MediaPipe)                     │
│  ├── 3D 场景渲染器 (Three.js)                     │
│  └── 虚拟课堂客户端                               │
│                                                   │
│  🔒 权限请求:                                     │
│  ├── 📷 摄像头 (手势识别)                         │
│  ├── 🎤 麦克风 (语音控制)                         │
│  └── 🌐 本地网络 (设备发现)                       │
│                                                   │
│  [取消]                         [确认安装]         │
└───────────────────────────────────────────────────┘
```

### 5.3 安装进度界面

```
┌───────────────────────────────────────────────────┐
│  正在安装 AR/VR 实验室                            │
├───────────────────────────────────────────────────┤
│                                                   │
│  ████████████████████░░░░░░░░░░  65%              │
│                                                   │
│  当前步骤: 安装 Python 依赖 (mediapipe...)        │
│                                                   │
│  ✅ 下载插件包 (220MB)           完成              │
│  ✅ 校验文件完整性               完成              │
│  ✅ 解压文件                     完成              │
│  ⏳ 安装 Python 依赖             进行中...         │
│  ○  注册后端路由                 等待中            │
│  ○  加载前端模块                 等待中            │
│  ○  创建数据库表                 等待中            │
│                                                   │
│  预计剩余时间: 约 45 秒                            │
│                                                   │
│  [后台安装]                                       │
└───────────────────────────────────────────────────┘
```

### 5.4 已安装插件管理页

```
┌─────────────────────────────────────────────────────────────────────────┐
│  已安装插件                                          总计: 8 个 · 680MB │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ 运行中 (5)                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🤖 AI 个性化教师   v2.1.0  15MB   [设置] [日志] [卸载]          │  │
│  │ 📝 考试增强包      v1.3.0   8MB   [设置] [日志] [卸载]          │  │
│  │ 📴 离线学习工具    v1.1.0  12MB   [设置] [日志] [卸载]          │  │
│  │ 🏆 成就系统增强    v2.0.0   5MB   [设置] [日志] [卸载]          │  │
│  │ 📊 知识图谱        v1.0.0   8MB   [设置] [日志] [卸载]          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ⚠️ 降级运行 (2)                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🔗 区块链证书      v1.2.0  30MB   降级: Hyperledger 未连接       │  │
│  │    当前模式: 本地缓存  [重试连接] [设置] [卸载]                   │  │
│  │ 🔬 AR/VR 实验室    v1.8.0  220MB  降级: Vircadia 未连接          │  │
│  │    当前模式: 2D 模拟  [重试连接] [设置] [卸载]                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ❌ 已停止 (1)                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🏗️ 数字孪生实验室  v1.5.0  150MB  状态: 已停止                   │  │
│  │    原因: Docker 服务未启动  [启动] [设置] [卸载]                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  📥 可用更新 (2)                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🤖 AI 个性化教师   v2.1.0 → v2.2.0  12MB 增量更新  [更新]       │  │
│  │ 🔬 AR/VR 实验室    v1.8.0 → v1.9.0  45MB 增量更新  [更新]       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Electron 集成设计

### 6.1 新增 IPC 通道

```typescript
// electron/preload.js — 新增插件管理 API

contextBridge.exposeInMainWorld('pluginAPI', {
  // ==================== 设备评估 ====================
  
  /** 获取设备评估报告 */
  getDeviceProfile: () => ipcRenderer.invoke('plugin:device-profile'),
  
  /** 重新评估设备 */
  reassessDevice: () => ipcRenderer.invoke('plugin:reassess-device'),
  
  /** 评估指定插件兼容性 */
  assessPlugin: (pluginId) => ipcRenderer.invoke('plugin:assess', pluginId),
  
  // ==================== 插件商店 ====================
  
  /** 获取可用插件列表 */
  getPluginCatalog: () => ipcRenderer.invoke('plugin:catalog'),
  
  /** 获取推荐套餐 */
  getRecommendedBundles: () => ipcRenderer.invoke('plugin:recommended-bundles'),
  
  /** 搜索插件 */
  searchPlugins: (query) => ipcRenderer.invoke('plugin:search', query),
  
  // ==================== 插件管理 ====================
  
  /** 安装插件 */
  installPlugin: (pluginId, version) => 
    ipcRenderer.invoke('plugin:install', pluginId, version),
  
  /** 卸载插件 */
  uninstallPlugin: (pluginId, keepData) => 
    ipcRenderer.invoke('plugin:uninstall', pluginId, keepData),
  
  /** 更新插件 */
  updatePlugin: (pluginId) => ipcRenderer.invoke('plugin:update', pluginId),
  
  /** 获取已安装插件列表 */
  getInstalledPlugins: () => ipcRenderer.invoke('plugin:installed'),
  
  /** 启用/禁用插件 */
  togglePlugin: (pluginId, enabled) => 
    ipcRenderer.invoke('plugin:toggle', pluginId, enabled),
  
  // ==================== 事件监听 ====================
  
  /** 监听安装进度 */
  onInstallProgress: (callback) => 
    ipcRenderer.on('plugin:install-progress', (_, data) => callback(data)),
  
  /** 监听插件状态变化 */
  onPluginStatusChange: (callback) => 
    ipcRenderer.on('plugin:status-change', (_, data) => callback(data)),
  
  /** 监听可用更新 */
  onUpdatesAvailable: (callback) => 
    ipcRenderer.on('plugin:updates-available', (_, data) => callback(data)),
});
```

### 6.2 插件目录结构

```
{userData}/                         # Electron 用户数据目录
├── device-profile.json             # 设备评估报告
├── plugins/                        # 已安装插件目录
│   ├── registry.json               # 插件注册表（本地索引）
│   ├── downloads/                  # 下载缓存目录
│   │   └── ar-vr-lab-1.8.0.mxp   # 未安装的下载包
│   ├── ar-vr-lab/                  # 插件安装目录
│   │   ├── manifest.json
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── data/                   # 插件运行时数据
│   ├── ai-tutor/
│   │   ├── manifest.json
│   │   └── ...
│   └── ...
└── plugin-cache/                   # 插件缓存（可清理）
    ├── manifests/                  # 远程插件清单缓存
    └── icons/                      # 图标缓存
```

### 6.3 启动流程集成

```javascript
// electron/main.js — 启动流程增加插件扫描

async function startWithPlugins() {
  // 1. 设备评估（首次启动时）
  if (!fs.existsSync(DEVICE_PROFILE_PATH)) {
    sendSplashStatus('info', '正在评估设备性能...', 10);
    const profile = await assessDevice();
    saveDeviceProfile(profile);
  }
  
  // 2. 扫描已安装插件
  sendSplashStatus('info', '扫描已安装插件...', 20);
  const plugins = await scanInstalledPlugins();
  
  // 3. 启动核心后端
  sendSplashStatus('info', '启动核心服务...', 30);
  await startBackendCore();
  
  // 4. 注册插件路由到后端
  sendSplashStatus('info', `加载 ${plugins.length} 个插件...`, 50);
  for (const plugin of plugins.filter(p => p.enabled)) {
    await registerPluginRoutes(plugin);
  }
  
  // 5. 显示主窗口
  showMainWindow();
  
  // 6. 后台检查更新
  checkPluginUpdates();
}
```

---

## 7. 后端集成设计

### 7.1 插件路由注册

```python
# backend/core/plugin_manager.py

class PluginManager:
    """
    插件管理器 — 管理插件的安装、加载、路由注册
    
    与 ModuleLazyLoader 协作：
    - 已安装插件自动注册为 ModuleSpec
    - 通过 LazyLoader 引擎管理激活/去激活
    - 支持热加载/热卸载（不重启服务）
    """
    
    def __init__(self, lazy_loader: ModuleLazyLoader):
        self.lazy_loader = lazy_loader
        self.plugin_dir = self._get_plugin_dir()
        self.installed: dict[str, PluginInfo] = {}
    
    def scan_plugins(self) -> list[PluginInfo]:
        """扫描插件目录，发现所有已安装插件"""
        ...
    
    def load_plugin(self, plugin_id: str) -> bool:
        """
        加载插件到懒加载引擎
        1. 读取 manifest.json
        2. 转换为 ModuleSpec
        3. 注册到 LazyLoader
        """
        ...
    
    def load_all_plugins(self):
        """加载所有已安装且启用的插件"""
        for plugin_id, info in self.installed.items():
            if info.enabled:
                self.load_plugin(plugin_id)
    
    async def install_plugin(self, package_path: str) -> PluginInfo:
        """安装新插件"""
        ...
    
    async def uninstall_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        ...
    
    async def update_plugin(self, plugin_id: str, package_path: str) -> PluginInfo:
        """更新插件（保留用户数据）"""
        ...
```

### 7.2 插件状态 API

```python
# backend/routes/plugin_routes.py

@router.get("/api/v1/plugins")
async def list_plugins():
    """
    获取所有可用和已安装插件
    响应:
    {
      "installed": [
        {
          "id": "ai-tutor",
          "name": "AI 个性化教师",
          "version": "2.1.0",
          "state": "active",
          "size": "15MB",
          "deviceCompatible": true,
          "degradations": []
        }
      ],
      "available": [
        {
          "id": "ar-vr-lab",
          "name": "AR/VR 实验室",
          "version": "1.8.0",
          "size": "220MB",
          "deviceCompatible": true,
          "compatibilityScore": 95
        }
      ],
      "deviceProfile": {
        "deviceClass": "advanced",
        "score": 82
      }
    }
    """

@router.post("/api/v1/plugins/{plugin_id}/install")
async def install_plugin(plugin_id: str, version: str = "latest"):
    """触发插件安装"""

@router.post("/api/v1/plugins/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str, keep_data: bool = False):
    """卸载插件"""

@router.post("/api/v1/plugins/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, enabled: bool):
    """启用/禁用插件"""

@router.get("/api/v1/plugins/{plugin_id}/compatibility")
async def check_compatibility(plugin_id: str):
    """检查插件与当前设备的兼容性"""

@router.get("/api/v1/device/profile")
async def get_device_profile():
    """获取设备评估报告"""

@router.post("/api/v1/device/reassess")
async def reassess_device():
    """重新评估设备"""

@router.get("/api/v1/plugins/recommended")
async def get_recommendations():
    """获取个性化插件推荐"""

@router.get("/api/v1/plugins/bundles")
async def get_bundles():
    """获取推荐套餐列表"""
```

### 7.3 与懒加载引擎集成

```python
# backend/core/__init__.py — 扩展初始化

def init_with_plugins(app: FastAPI):
    """
    初始化懒加载引擎 + 插件管理器
    
    启动流程：
    1. 创建 LazyLoader 引擎
    2. 注册内置模块（Tier 0~3）
    3. 创建 PluginManager
    4. 扫描已安装插件
    5. 将插件注册为额外 ModuleSpec
    6. 激活 Tier 0 + 已安装插件中的 Tier A
    """
    loader = init_lazy_loader(app)
    plugin_manager = PluginManager(loader)
    plugin_manager.scan_plugins()
    plugin_manager.load_all_plugins()
    return loader, plugin_manager
```

---

## 8. 安全模型

### 8.1 插件签名验证

```
插件发布流程：
开发者 → 构建 .mxp → MatuX 签名服务器 → 签名后的 .mxp → CDN

安装验证：
1. 校验签名（Ed25519 公钥验证）
2. 校验文件完整性（SHA-256 校验和）
3. 校验版本号（防回退攻击）
4. 校验来源（仅信任 MatuX 官方 + 认证开发者）
```

### 8.2 插件权限控制

| 权限 | 说明 | 需要用户确认 |
|------|------|-------------|
| `camera` | 访问摄像头 | ✅ 是 |
| `microphone` | 访问麦克风 | ✅ 是 |
| `gpu-compute` | 使用 GPU 计算资源 | ❌ 否 |
| `local-network` | 访问本地网络 | ✅ 是 |
| `usb-devices` | 访问 USB 设备 | ✅ 是 |
| `file-system` | 读写用户文件 | ✅ 是 |
| `internet` | 访问互联网 | ❌ 否 |
| `docker` | 使用 Docker 容器 | ✅ 是 |
| `background` | 后台持续运行 | ❌ 否 |

### 8.3 插件沙箱隔离

```python
# 后端插件隔离策略
class PluginSandbox:
    """
    插件运行时隔离
    - 限制文件系统访问范围
    - 限制网络请求目标
    - 限制 CPU/内存使用
    - 数据库操作限定在插件专属表
    """
    ...
```

---

## 9. 增量更新与版本管理

### 9.1 版本策略

```
插件版本号: MAJOR.MINOR.PATCH (语义化版本)
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的 Bug 修复

后端兼容性: 插件声明兼容的后端版本范围
  "backendCompatibility": ">=2.0.0 <3.0.0"

前端兼容性: 插件声明兼容的前端版本范围
  "frontendCompatibility": ">=2.1.0"
```

### 9.2 更新机制

```
┌─────────────────────────────────────────────────┐
│  插件更新流程                                    │
│                                                  │
│  1. 后台检查更新 (每天 1 次 / 用户手动)         │
│  2. 下载更新清单 (diff manifest)                 │
│  3. 计算增量文件大小                             │
│  4. 提示用户 (非强制)                            │
│  5. 用户确认 → 下载增量包                        │
│  6. 校验 → 备份旧版本 → 应用增量                │
│  7. 验证 → 成功则清理备份 / 失败则回滚          │
└─────────────────────────────────────────────────┘
```

### 9.3 回滚机制

- 每次更新前自动备份当前版本
- 更新失败自动回滚到上一个稳定版本
- 用户可手动回退到指定版本
- 回滚保留用户数据

---

## 10. 网络适配策略

### 10.1 带宽自适应

| 网络类型 | 下载策略 | 说明 |
|---------|---------|------|
| 以太网 (>50Mbps) | 全速下载 | 完整包下载 |
| WiFi (5~50Mbps) | 限速下载 | 后台下载，不影响使用 |
| 计量网络 | 暂停自动下载 | 仅提示用户，手动触发 |
| 离线 | 离线安装 | 支持从 USB/局域网拷贝 .mxp 包 |

### 10.2 离线安装支持

```
离线安装流程：
1. 用户从其他渠道获取 .mxp 文件（U盘、局域网共享）
2. 拖拽 .mxp 文件到 MatuX 窗口
3. 本地校验 → 兼容性检查 → 安装
4. 无需联网即可完成安装
```

---

## 11. 实施方案

### 11.1 Phase 1：设备评估框架（2 周）

**目标**：实现设备能力检测和评级

- [ ] 创建 `electron/device-profiler.ts`（硬件/软件检测）
- [ ] 实现设备评级算法（Basic/Standard/Advanced/Professional）
- [ ] 新增 IPC 通道（`plugin:device-profile`, `plugin:reassess-device`）
- [ ] 前端设备评估报告组件
- [ ] 后端 `/api/v1/device/profile` API

**验收标准**：
- 设备检测耗时 < 5 秒
- 评级结果准确（与实际设备能力匹配）
- 检测结果持久化存储

### 11.2 Phase 2：插件包格式与管理器（3 周）

**目标**：实现插件打包、安装、卸载

- [ ] 定义 `.mxp` 插件包格式规范
- [ ] 创建插件打包工具（CLI）
- [ ] 实现 `electron/plugin-installer.ts`
- [ ] 实现 `backend/core/plugin_manager.py`
- [ ] 与 `ModuleLazyLoader` 集成
- [ ] 插件注册表（本地 + 远程）

**验收标准**：
- 可打包任意 Tier 2/3 模块为 .mxp
- 安装后插件可正常使用
- 卸载后无残留
- 不重启即可热加载/热卸载

### 11.3 Phase 3：插件商店 UI（2 周）

**目标**：实现插件浏览、搜索、安装的前端界面

- [ ] 插件商店页面（浏览、分类、搜索）
- [ ] 兼容性检查与展示
- [ ] 安装进度界面
- [ ] 已安装插件管理页
- [ ] 推荐套餐展示

**验收标准**：
- 用户可浏览并安装插件
- 不兼容的插件有明确提示
- 安装过程有清晰进度反馈

### 11.4 Phase 4：模块迁移与首批插件（3 周）

**目标**：将 5 个高价值模块打包为首批插件

- [ ] `ar-vr-lab` 插件打包（含 MediaPipe/Three.js）
- [ ] `digital-twin` 插件打包（含 Docker 依赖）
- [ ] `creativity-engine` 插件打包
- [ ] `blockchain-cert` 插件打包
- [ ] `hardware-cert` 插件打包
- [ ] 为每个模块编写 manifest.json
- [ ] 增量更新机制实现

**验收标准**：
- 首批 5 个插件可正常安装/使用/卸载
- 增量更新功能正常
- 安装后功能与内置版本一致

### 11.5 Phase 5：推荐引擎与智能适配（1 周）

**目标**：基于设备评估的个性化推荐

- [ ] 实现 `PluginRecommender` 推荐引擎
- [ ] 设备-插件兼容性自动匹配
- [ ] 低配设备自动推荐轻量替代方案
- [ ] 套餐推荐（Starter/Developer/Immersive/Researcher）

**验收标准**：
- 推荐列表与设备能力匹配
- 低配设备不会推荐高级插件
- 推荐套餐可一键安装

---

## 12. 验收标准总览

| 指标 | 目标值 | 验收方法 |
|------|--------|---------|
| 基础安装包体积 | < 300MB（从 1.7GB 减少 82%） | 打包后测量 |
| 设备评估耗时 | < 5 秒 | 计时测试 |
| 插件安装平均耗时 | < 30 秒/100MB | 计时测试 |
| 插件热加载耗时 | < 3 秒 | 计时测试 |
| 插件卸载无残留 | 100% 清理 | 文件系统检查 |
| 增量更新节省流量 | > 70% (vs 全量下载) | 流量统计 |
| 设备评级准确率 | > 95% | 多设备测试验证 |
| 插件兼容性检查覆盖率 | 100%（所有插件均有检查） | 代码审查 |
| 离线安装成功率 | 100% | 离线环境测试 |

---

## 13. 与现有架构的集成点

| 现有组件 | 集成方式 | 变更范围 |
|---------|---------|---------|
| `ModuleLazyLoader` | 插件自动注册为 ModuleSpec | 新增 `plugin_loader.py` |
| `ModuleRegistry` | 已安装插件追加到模块列表 | `module_registry.py` 扩展 |
| `ServiceDependencies` | 插件依赖复用降级策略 | 无变更 |
| `CircuitBreaker` | 插件级熔断 | 扩展熔断器粒度 |
| `phased-startup.js` | 启动时扫描插件 | 扩展启动流程 |
| `preload.js` | 新增 `pluginAPI` 通道 | 扩展 IPC |
| `status-bar.component.ts` | 显示已安装插件状态 | UI 扩展 |
| Angular Router | 插件路由动态注册 | 新增 `plugin-router.service.ts` |

---

## 14. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 插件依赖冲突 | 中 | 高 | 依赖版本锁定 + 安装前预检 |
| Python 依赖安装失败 | 高 | 中 | 预编译 wheel 包 + 离线安装 |
| 设备评估不准确 | 中 | 中 | 多轮校准 + 用户反馈修正 |
| 插件更新导致不兼容 | 中 | 高 | 灰度发布 + 自动回滚 |
| 插件安全风险 | 低 | 高 | 代码签名 + 权限沙箱 |
| 用户磁盘空间不足 | 高 | 中 | 安装前检查 + 定期清理建议 |
| 网络中断导致安装不完整 | 高 | 中 | 断点续传 + 离线安装支持 |
| 插件间资源竞争 (GPU) | 中 | 中 | 资源配额管理 + 优先级调度 |
