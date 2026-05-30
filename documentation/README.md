# iMatu 技术文档中心

本文档库包含 iMatu 项目的完整技术文档，按照代码模块结构组织，便于开发者快速查找和维护。

## 📁 文档组织结构

```
documentation/
├── backend/                      # 后端技术文档（与 backend/目录对齐）
│   ├── routes/                   # API 路由文档
│   ├── services/                 # 业务服务文档
│   ├── models/                   # 数据模型文档
│   ├── utils/                    # 工具函数文档
│   ├── ai-edu/                   # AI-Edu 教育平台文档
│   ├── blockchain/               # 区块链集成文档
│   └── hardware/                 # 硬件通信文档
│
├── frontend/                     # 前端技术文档（与 src/app/目录对齐）
│   ├── components/               # 组件文档
│   ├── services/                 # 服务文档
│   ├── modules/                  # 模块文档
│   └── design-system/            # Design System 文档
│
├── shared/                       # 公共技术文档
│   ├── architecture/             # 架构设计文档
│   ├── api-specs/                # API 规范文档
│   └── guides/                   # 开发指南
│
├── deployment/                   # 部署运维文档
├── tests/                        # 测试报告文档
└── resources/                    # 资源附件
```

## 🎯 设计原则

### 1. 与代码结构对齐
文档目录与代码目录严格对应，例如：
- `backend/services/recommendation_service.py` → `documentation/backend/services/recommendation-service.md`
- `src/app/components/ai-study-assistant/` → `documentation/frontend/components/ai-study-assistant.md`

### 2. 职责分离
- **对外文档** (`docs/`)：面向用户、管理者、新手，提供概览和快速入门
- **技术文档** (`documentation/`)：面向开发者、维护者，提供详细实现细节

### 3. 易于维护
- 每个模块的文档放在对应目录下
- 文档命名与代码文件名保持一致（使用连字符格式）
- 每个目录可包含 README.md 说明该模块的整体设计

## 📚 文档分类

### Backend 文档
包含所有后端相关的技术文档：
- API 路由设计和实现
- 业务服务逻辑说明
- 数据模型设计文档
- 工具函数使用指南
- 专项功能模块（AI-Edu、区块链、硬件等）

### Frontend 文档
包含所有前端相关的技术文档：
- 组件设计和使用说明
- 服务层实现细节
- 模块架构文档
- Design System 规范

### Shared 文档
跨模块的公共技术文档：
- 系统架构设计
- API 规范标准
- 开发指南和最佳实践

### Deployment 文档
部署和运维相关文档：
- 部署指南
- 配置说明
- 运维手册

### Tests 文档
测试和质量相关文档：
- 测试报告
- 回测结果
- 质量指标

### Resources 资源
辅助资源和附件：
- 演示文件
- 模板文件
- 参考资料

## 🔗 与对外文档的关系

```
项目根目录/
├── README.md                          # 项目总览（对外）
├── docs/                              # 对外文档中心
│   └── INDEX.md                       # 文档导航入口
└── documentation/                     # 技术文档中心（对内）
    ├── backend/
    ├── frontend/
    └── shared/
```

**访问路径**：
- 新用户、产品经理、管理者 → 从 `README.md` 进入，查看 `docs/INDEX.md`
- 开发者、维护者 → 直接访问 `documentation/` 查找对应模块文档

## 📝 文档编写规范

### 命名规范
- 使用小写字母和连字符：`my-document.md`
- 与对应的代码文件名保持一致
- 避免使用空格和下划线

### 模板结构
每个技术文档应包含：
```markdown
# 模块名称

## 概述
简要说明模块的功能和用途

## 架构设计
- 模块在系统中的位置
- 与其他模块的关系
- 核心类/函数说明

## API 接口
- 端点列表
- 请求/响应格式
- 使用示例

## 实现细节
- 关键算法说明
- 数据结构设计
- 性能优化点

## 测试验证
- 测试用例
- 验证方法
- 已知限制

## 参考资料
- 相关文档链接
- 外部资源
```

## 🚀 快速开始

### 查找文档
1. 确定你要找的模块属于前端还是后端
2. 在对应目录下找到子目录（components/services/routes 等）
3. 按文件名查找对应文档

### 添加新文档
1. 确定文档类型（backend/frontend/shared）
2. 选择正确的子目录
3. 使用规范的命名创建 `.md` 文件
4. 在文档顶部添加所属分类标签

## 📊 文档迁移状态

本文档库正在从旧的 `docs/` 目录迁移过来，迁移进度：

- [x] 目录结构创建
- [ ] 后端文档迁移
- [ ] 前端文档迁移
- [ ] 公共文档迁移
- [ ] 链接更新
- [ ] 清理旧文档

详细迁移指南请参考：`MIGRATION_GUIDE.md`

---

**最后更新**: 2026-03-04  
**维护团队**: iMatu Development Team
