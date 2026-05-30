# iMato 项目文档索引

**最后更新**: 2026-04-28  
**维护者**: iMato Team  
**版本**: v1.0

---

## 📚 文档分类导航

### 1. 项目概览与核心架构
- [README.md](../README.md) - 项目主文档，包含功能介绍、技术栈、快速开始
- [GLOBAL_TECHNICAL_ARCHITECTURE.md](../GLOBAL_TECHNICAL_ARCHITECTURE.md) - 全局技术架构设计
- [PROJECT_ROADMAP.md](../PROJECT_ROADMAP.md) - 项目发展路线图和里程碑
- [SECURITY.md](../SECURITY.md) - 安全政策和漏洞响应流程

### 2. OpenHydra + XEdu AI教育集成
**核心文档**:
- [集成方案总览](../OPENHYDRA_XEDU_INTEGRATION_PLAN.md) - 完整的OpenHydra+XEdu集成计划（1535行）

**实施报告**:
- [阶段一完成总结](./PHASE1_COMPLETION_SUMMARY_20260304.md) - O1.1-O1.3任务完成（提前21天）
- [微课程与AI助手](./O2_3_O2_4_TASK_COMPLETE_REPORT.md) - O2.3 & O2.4完成报告
- [SSO技术方案](./O1_3_SSO_TECHNICAL_DESIGN.md) - 单点登录详细设计（1098行）
- [部署报告 O1.1](./OPENHYDRA_DEPLOYMENT_REPORT_O1.1.md) - OpenHydra部署详情
- [功能测试 O1.2](./XEdu_FUNCTION_TEST_REPORT_O1.2_FULL.md) - XEdu工具链测试
- [实施进度 2026-03-04](./OPENHYDRA_XEDU_IMPLEMENTATION_STATUS_20260304.md) - 最新进度状态

**快速开始**:
- [快速体验指南](../../docs/OPENHYDRA_QUICKSTART.md) - 5分钟快速上手

### 3. 测试与回测报告
- [Vircadia P1 开发检查清单](./tests/vircadia-p1-dev-checklist.md)
- [Vircadia P1 设置总结](./tests/vircadia-p1-setup-summary.md)

### 4. 前端增强功能报告
- [P1+P2+P3完成总结](./P1_P2_P3_COMPLETE_SUMMARY_20260305.md) - 18个任务全部完成
- [管理仪表板增强](./ADMIN_DASHBOARD_ENHANCEMENT_REPORT.md)
- [多模态激励系统发布](./MULTIMODAL_INCENTIVE_SYSTEM_RELEASE_REPORT.md)

### 5. Vircadia元宇宙集成
- [Vircadia阶段一总结](./VIRCADIA_STAGE1_SUMMARY.md)
- [Avatar系统集成](./VIRCADIA_AVATAR_INTEGRATION.md)

### 6. 其他技术文档
详见 [documentation/README.md](../../documentation/README.md)

---

## 🔍 按角色查找文档

### 我是...

#### 👨‍💻 新开发者
→ 从 [README.md](../README.md) 开始  
→ 查看 [快速开始指南](../../docs/QUICK_START_GUIDE.md)  
→ 阅读 [开发环境配置](../../docs/LOCAL_DEPLOYMENT_GUIDE.md)

#### 🤖 AI/机器学习工程师
→ [OpenHydra集成方案](../OPENHYDRA_XEDU_INTEGRATION_PLAN.md)  
→ [XEdu工具链测试报告](./XEdu_FUNCTION_TEST_REPORT_O1.2_FULL.md)  
→ [微课程转化系统](./O2_3_O2_4_TASK_COMPLETE_REPORT.md)

#### 🎮 游戏化/激励系统开发者
→ [多模态激励系统](./MULTIMODAL_INCENTIVE_SYSTEM_RELEASE_REPORT.md)  
→ [成就系统设计](../../documentation/backend/services/achievement-service.md)  
→ [积分排行榜](../../documentation/backend/services/leaderboard-service.md)

#### 🌐 前端工程师
→ [P1+P2+P3完成总结](./P1_P2_P3_COMPLETE_SUMMARY_20260305.md)  
→ [Angular组件文档](../../documentation/frontend/components/)  
→ [Design System](../../documentation/frontend/design-system/)

#### 🔗 区块链开发者
→ [Fabric开发者文档](../../blockchain/FABRIC_DEVELOPER_DOCUMENTATION.md)  
→ [API参考手册](../../blockchain/API_REFERENCE_MANUAL.md)  
→ [技术架构图谱](../../blockchain/TECHNICAL_ARCHITECTURE_DIAGRAMS.md)

#### 🥽 VR/AR/元宇宙开发者
→ [Vircadia集成方案](../../documentation/shared/architecture/vircadia/integration-plan.md)  
→ [3D模型库开发指南](../../docs/3D_MODEL_LIBRARY_DEVELOPER_GUIDE.md)  
→ [AR虚拟实验室](../../docs/AR_LAB_DESIGN.md)

#### 🏗️ 架构师
→ [全局技术架构](../GLOBAL_TECHNICAL_ARCHITECTURE.md)  
→ [系统架构设计](../../documentation/shared/architecture/system-architecture.md)  
→ [项目路线图](../PROJECT_ROADMAP.md)

#### 🧪 测试工程师
→ [测试标准](../../tests/TEST_STANDARD.md)  
→ [测试维护策略](../../tests/TEST_MAINTENANCE_POLICY.md)  
→ [回测报告目录](../../backtest_reports/)

#### 📊 产品经理
→ [项目概览](../README.md)  
→ [网站地图](../../docs/SITE_MAP.md)  
→ [功能模块清单](../PROJECT_ROADMAP.md#功能模块)

#### 🔒 安全工程师
→ [安全政策](../SECURITY.md)  
→ [认证系统实现](../../documentation/frontend/components/auth/system-implementation-report.md)  
→ [权限控制](../../documentation/frontend/components/auth/system-documentation.md)

---

## 📁 文档目录结构

```
iMato/
├── README.md                              # 项目主文档
├── GLOBAL_TECHNICAL_ARCHITECTURE.md       # 全局架构
├── PROJECT_ROADMAP.md                     # 路线图
├── SECURITY.md                            # 安全政策
├── OPENHYDRA_XEDU_INTEGRATION_PLAN.md    # OpenHydra集成
│
├── docs/                                  # 对外文档中心
│   ├── INDEX.md                           # 文档导航入口
│   ├── QUICK_START_GUIDE.md               # 快速开始
│   ├── LOCAL_DEPLOYMENT_GUIDE.md          # 本地部署
│   └── ...                                # 其他用户文档
│
├── documentation/                         # 技术文档中心
│   ├── backend/                           # 后端技术文档
│   ├── frontend/                          # 前端技术文档
│   ├── shared/                            # 共享架构文档
│   ├── deployment/                        # 部署运维
│   └── tests/                             # 测试报告
│       ├── vircadia-p1-dev-checklist.md
│       └── vircadia-p1-setup-summary.md
│
├── reports/                               # 实施报告
│   ├── DOCUMENT_INDEX.md                  # 本文档
│   ├── PHASE1_COMPLETION_SUMMARY_*.md     # 阶段完成总结
│   ├── O2_3_O2_4_TASK_COMPLETE_REPORT.md  # 任务完成报告
│   └── P1_P2_P3_COMPLETE_SUMMARY_*.md     # 优先级任务总结
│
└── blockchain/                            # 区块链技术
    ├── FABRIC_DEVELOPER_DOCUMENTATION.md
    ├── API_REFERENCE_MANUAL.md
    └── TECHNICAL_ARCHITECTURE_DIAGRAMS.md
```

---

## 📊 文档统计

| 类别 | 数量 | 总行数（估算） | 说明 |
|------|------|--------------|------|
| 核心架构文档 | 4 | ~2,500 | README, 架构, 路线图, 安全 |
| OpenHydra/XEdu | 7 | ~5,000 | 集成方案、报告、设计 |
| 实施报告 | 10+ | ~8,000 | 各阶段完成总结 |
| 测试报告 | 2 | ~700 | Vircadia相关 |
| 区块链技术 | 3 | ~1,500 | Fabric文档 |
| 其他技术文档 | 50+ | ~25,000 | 详见documentation/ |
| **总计** | **76+** | **~42,700+** | - |

---

## 🔄 文档维护指南

### 添加新文档
1. 确定文档类型（架构/实施/测试/用户指南）
2. 放置在对应的目录下
3. 更新本索引文件
4. 在相关README中添加链接

### 删除过时文档
1. 确认文档已被替代或不再需要
2. 检查是否有其他文档引用它
3. 删除文件并更新索引
4. 在Git提交信息中说明原因

### 定期清理
建议每月运行一次文档清理：
```powershell
# 查找超过6个月未更新的MD文件
Get-ChildItem -Recurse -Filter "*.md" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddMonths(-6) }
```

---

## 💡 最佳实践

1. **文档与代码同步更新** - 每次功能变更时同步更新相关文档
2. **使用相对路径** - 便于文档移动和仓库克隆
3. **保持简洁明了** - 避免冗长，使用图表和示例
4. **定期审查** - 每季度审查文档准确性和完整性
5. **版本控制** - 重要文档标注版本号和更新日期

---

## 📞 联系方式

如有文档问题或建议：
- 📧 Email: docs@imato.edu
- 💬 GitHub Issues: https://github.com/imato/issues
- 🌐 文档中心: https://docs.imato.edu

---

*本文档由自动化脚本生成，最后更新于 2026-04-28*  
*下次审查日期: 2026-05-28*
