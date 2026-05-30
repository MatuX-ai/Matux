# iMato 三种收费模式 - 项目目录结构规划

**创建时间**: 2026-03-14  
**目的**: 清晰分离开源版、Windows 本地版、云托管版的代码和资源

---

## 📁 推荐的目录结构

### **方案一：按版本类型分组（推荐）**

```
g:\iMato\
├── pricing_modes/                    # 【新建】三种收费模式专用目录
│   ├── README.md                     # 本模块说明文档
│   │
│   ├── open_source/                  # 开源社区版
│   │   ├── docker/                   # Docker 部署配置
│   │   ├── docs/                     # 部署文档
│   │   └── scripts/                  # 部署脚本
│   │
│   ├── windows_local/                # Windows 本地版
│   │   ├── electron/                 # Electron 主应用
│   │   │   ├── main.js              # 主进程
│   │   │   ├── preload.js           # 预加载脚本
│   │   │   ├── package.json         # Electron 配置
│   │   │   └── assets/              # 图标和启动画面
│   │   ├── electron-builder.yml      # 打包配置
│   │   ├── installer/               # NSIS 安装脚本
│   │   └── docs/                    # 安装和使用文档
│   │
│   ├── cloud_hosted/                # 云托管版
│   │   ├── docker/                  # Docker 配置
│   │   │   ├── Dockerfile.cloud    # 生产镜像
│   │   │   └── docker-compose.cloud.yml
│   │   ├── k8s/                     # Kubernetes 配置
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── secret.yaml
│   │   ├── monitoring/              # 监控配置
│   │   │   ├── prometheus/
│   │   │   └── grafana/
│   │   └── docs/                    # 运维文档
│   │
│   └── shared/                      # 共享资源
│       ├── token-billing/          # Token 计费系统（共用）
│       │   ├── backend/
│       │   └── frontend/
│       ├── license-permission/     # 许可证权限控制
│       └── payment-integration/    # 支付集成
│
└── ... (现有项目文件保持不变)
```

---

### **方案二：按技术栈分组（备选）**

```
g:\iMato\
├── pricing_modes/
│   ├── backend/                    # 后端相关
│   │   ├── models/                # 数据模型（已完成）
│   │   ├── services/              # 业务逻辑
│   │   ├── routes/                # API路由
│   │   └── migrations/            # 数据库迁移
│   │
│   ├── frontend/                   # 前端相关
│   │   ├── components/            # UI 组件
│   │   ├── services/              # Angular 服务
│   │   ├── models/                # TypeScript 类型
│   │   └── pages/                 # 页面（定价页等）
│   │
│   ├── electron/                   # Windows 安装包
│   │   └── ...
│   │
│   └── deploy/                     # 部署配置
│       ├── docker/
│       ├── k8s/
│       └── scripts/
```

---

## ✅ 推荐方案一的理由

### **优点**：
1. ✅ **清晰的版本隔离**：每个版本独立目录，互不干扰
2. ✅ **易于理解**：开发者一看就知道某个版本的代码在哪
3. ✅ **独立发布**：可以单独打包某个版本
4. ✅ **文档集中**：每个版本的文档就在对应目录下
5. ✅ **扩展性好**：未来增加第 4 种版本很容易

### **适合场景**：
- ✅ 三种版本有显著不同的代码和配置
- ✅ 需要独立部署和发布
- ✅ 团队分工明确（不同人负责不同版本）

---

## 🎯 具体实施步骤

### **Step 1: 创建基础目录结构**
```bash
# PowerShell 命令
cd G:\iMato
mkdir pricing_modes
mkdir pricing_modes\open_source
mkdir pricing_modes\windows_local
mkdir pricing_modes\cloud_hosted
mkdir pricing_modes\shared
```

### **Step 2: 移动已有文件**
将已创建的文档移动到对应目录：
- `TODO_PRICING_MODES_TASKS.md` → `pricing_modes\README.md`
- `PRICING_MODES_PROGRESS_REPORT.md` → `pricing_modes\shared\docs\`

### **Step 3: 创建新的开发文件**
按照目录结构逐步创建：
- Week 1: 主要在 `backend/models/` 和 `backend/services/` （已在根目录完成）
- Week 2: 在 `pricing_modes\shared\` 和前端目录
- Week 3: 在 `pricing_modes\windows_local\electron\`
- Week 4: 在 `pricing_modes\cloud_hosted\docker\` 和 `k8s\`

---

## 💡 建议

### **立即执行**：
1. ✅ 创建 `pricing_modes/` 目录结构
2. ✅ 创建 `.gitignore` 规则
3. ✅ 创建 `README.md` 说明文档

### **暂不移动**：
- ❌ 已完成的 `backend/models/user_license.py` 和 `backend/models/license.py`
  - 原因：这些是核心模型，应该保持在原位置
  - 其他模块通过 import 引用即可

### **后续新增**：
- ✅ 所有与三种收费模式相关的新代码都放在 `pricing_modes/` 下
- ✅ 保持现有项目结构不受影响

---

## 🔗 与现有项目的关系

```
现有项目根目录
├── backend/models/          # 核心数据模型（包含 Token 计费）
├── backend/services/        # 核心业务逻辑
├── src/app/                 # 前端应用
│   ├── marketing/          # 营销页面（包含定价页）
│   └── components/         # 通用组件
│
└── pricing_modes/          # 【新建】三种收费模式专用
    ├── open_source/        # 开源版特定代码
    ├── windows_local/      # Windows 版特定代码
    ├── cloud_hosted/       # 云托管版特定代码
    └── shared/             # 共享模块（可复用代码）
```

---

## ⚠️ 注意事项

1. **不要破坏现有结构**：现有代码继续工作，新增功能在 `pricing_modes/`
2. **避免重复代码**：共用的服务（如 TokenService）仍在 `backend/services/`
3. **Git 管理**：确保 `.gitignore` 包含必要的忽略规则
4. **文档同步**：在 `pricing_modes/README.md` 中记录所有变更

---

**决策**: 采用**方案一**（按版本类型分组）  
**下一步**: 创建目录结构和基础文档
