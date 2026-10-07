# RFC-2026-v2: MatuX v2.0 AI 协作学习平台蓝图

> **状态**: Draft
> **作者**: 架构师 + 产品负责人
> **创建**: 2026-10-08
> **目标评审**: 2026-11-08 前
> **关联**: [PROJECT_REQUIREMENTS.md §12](../PROJECT_REQUIREMENTS.md)
> **Supersedes**: 无（v6.0 的首个 RFC）

---

## 摘要（TL;DR）

v2.0 将 MatuX 从"AI 辅助编程教育工具"演进为"**AI 协作学习平台**"。核心是引入**三大支柱**：

1. **AI 协作编程工作台**（Cursor/Windsurf 模式，但面向学生）
2. **Prompt Engineering 课程体系**（L1→L2→L3）
3. **学习者 AI 副驾**（个性化路径 + 档案摘要）

不再追求"防作弊"等过时的 v5.0 概念。v2.0 GA 目标：2026-12-31。

---

## 1. 背景与动机

### 1.1 v5.0 的局限

2026-05 制定的 v5.0 需求中，多处概念已与 AI 时代脱节：

| v5.0 表述 | 现状（2026-10） |
|---|---|
| "防作弊测验" | Cursor / Windsurf 等 AI 协作工具普及，"禁止 AI" 已不现实 |
| "AI 辅助编程" | 业界已转向 "AI 协作编程"，AI 是 Pair 而非 Tool |
| "AI 个性化教师" | 学生已习惯直接与 ChatGPT 对话，期望更深度协作 |
| "边缘计算 + 区块链 + AR/VR" | 多技术堆叠但缺少核心叙事 |

### 1.2 竞品参照

| 竞品 | 定位 | 对 MatuX 的启示 |
|---|---|---|
| Cursor | 开发者 AI 协作 IDE | 工作台形态可借鉴，但面向学生需简化 |
| Windsurf | Cascade 多 Agent 协作 | 多 Agent 编排课程可直接借鉴 |
| Khan Academy | Khanmigo AI 导师 | 学习者副驾可参考 |
| Replit | 学习 + 部署一体化 | 部署能力 v2.0 不强求 |

### 1.3 MatuX 的差异化机会

- **国内 K12 STEM 场景**：Cursor / Khanmigo 均无中文 K12 适配
- **教师可控**：课堂场景需要教师视角的协作监控
- **学习档案沉淀**：v1 已有的学习档案系统是天然壁垒

---

## 2. v2.0 三大支柱（详细设计）

### 支柱 A · AI 协作编程工作台

#### 用户故事

> 作为一名高一学生，我希望在受控环境下与 AI 共同完成 Python 编程作业，AI 不是直接给我答案，而是分步协作：先让我尝试，再让我评估 AI 的方案，最后让我修改。

#### 功能需求

| ID | 功能 | 优先级 |
|---|---|---|
| COLLAB-A1 | Monaco Editor + AI Chat 侧栏 | Must |
| COLLAB-A2 | AI 行为显式化（每个 AI 回复可看到 prompt） | Must |
| COLLAB-A3 | 多 Agent 切换（架构师 / 测试员 / 评审员） | Should |
| COLLAB-A4 | 版本回放（按步重放 AI 推理） | Should |
| COLLAB-A5 | 代码 diff 可视化（学习者修改 vs AI 修改） | Could |
| COLLAB-A6 | 教师视角协作监控（仅看，不操作） | Could |

#### 数据模型

```python
class CollabSession(Base):
    id: UUID
    user_id: UUID
    assignment_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    steps: JSON  # [{actor: 'human'|'ai', prompt: str, response: str, diff: str}]
    final_code: Text
    evaluation: JSON  # AI 自评 + 教师评分
```

#### API 设计（草案）

```
POST /api/v2/ai-collab/sessions          # 创建协作会话
GET  /api/v2/ai-collab/sessions/{id}     # 获取会话详情（含 steps）
POST /api/v2/ai-collab/sessions/{id}/step # 推进一步（人输入或 AI 响应）
POST /api/v2/ai-collab/sessions/{id}/evaluate # 触发 AI 评估
GET  /api/v2/ai-collab/sessions/{id}/replay # 版本回放
```

### 支柱 B · Prompt Engineering 课程体系

#### 课程结构

| 级别 | 名称 | 课时 | 评估方式 |
|---|---|---|---|
| L1 | 基础提示词 | 8 | 50 题提示词编写 + AI 评分 |
| L2 | 多轮对话与上下文 | 16 | 3 个项目（每项目 4 轮对话） |
| L3 | 多 Agent 编排 | 24 | 设计 3-Agent 协作方案并跑通 |

#### 课程内容托管

复用 `edu-proto/` Next.js 原型框架，迁移到生产环境的 `edu-platform/`。

#### 关键技术点

- **Prompt 模板库**：开源 + 教师贡献
- **AI 评分校准**：用 Claude 评分，再用 DeepSeek 复评，最终教师抽检
- **学习路径**：基于学习档案的下一课程推荐

### 支柱 C · 学习者 AI 副驾

#### 核心能力

| ID | 能力 | 实现基础 |
|---|---|---|
| COPILOT-C1 | 7 天学习档案 AI 摘要 | 扩展 `ai-teacher.service.ts` |
| COPILOT-C2 | 错题归因（基于提交历史） | 新增 `error-attribution` 服务 |
| COPILOT-C3 | 学习路径推荐 | 接入课程地图 |
| COPILOT-C4 | 多模态（截图 + 代码 + 文本） | 接入视觉模型（GPT-4V 等） |

#### 隐私边界

- 学生数据**不外发**：本地 CodeLlama 优先
- 摘要文本**可外发**：脱敏后发送给云端
- 教师视角**仅看聚合**：不暴露个人聊天记录

---

## 3. 技术选型草案

### 3.1 后端

| 组件 | 选型 | 理由 |
|---|---|---|
| Web 框架 | FastAPI（沿用） | 已成熟 |
| AI 编排 | LangChain + LangGraph | 多 Agent 编排需求匹配 |
| WebSocket | FastAPI 内置 | AI 流式输出必需 |
| 任务队列 | Celery（沿用） | 已稳定 |
| 缓存 | Redis（沿用） | 已部署 |

**模块新增**：

- `backend/services/ai_collab_service/` — AI 协作会话管理
- `backend/routes/ai_collab_routes.py` — FastAPI 路由
- `backend/routes/prompt_eng_routes.py` — 课程相关
- `backend/services/error_attribution.py` — 错题归因

### 3.2 前端（Angular）

| 组件 | 路径 |
|---|---|
| ai-collab-workspace | `src/app/shared/components/ai-collab-workspace/` |
| prompt-lab | `src/app/shared/components/prompt-lab/` |
| ai-pair-panel | `src/app/user/components/ai-pair-panel/` |
| collab-replay | `src/app/shared/components/collab-replay/` |

**复用**：

- `ngx-monaco-editor-v2`（已存在）
- 现有状态管理（NgRx 或服务）
- 现有路由懒加载机制

### 3.3 模型层

| 模型 | 用途 | 备注 |
|---|---|---|
| DeepSeek-Coder | 主力代码生成 | 见 [DeepSeek模型名称配置](../../../) |
| Claude-3.5-Sonnet | 评审 / 评分 | 主力评审 |
| 本地 CodeLlama-13B | 离线 / 隐私 | 部署在桌面端或边缘 |

**路由策略**：

```
任务路由:
  代码生成 → DeepSeek-Coder
  评审 / 评分 → Claude
  隐私任务 / 离线 → 本地 CodeLlama
```

### 3.4 数据存储

- 协作会话 steps（JSON）→ PostgreSQL JSON 字段
- 课程进度 → 现有 `learning_progress` 表扩展
- 摘要缓存 → Redis（TTL 24h）

---

## 4. 里程碑与工期

| 阶段 | 工期 | 输出物 |
|---|---|---|
| 原型验证 | 2026-11 下旬 (2 周) | 3 个 demo 各 1 个端到端流程 |
| AI 协作后端 | 2026-12 上旬 (3 周) | FastAPI + WebSocket + 5 API |
| Angular 前端 | 2026-12 上中旬 (3 周) | 共享组件 + 路由 + 状态管理 |
| 课程内容 | 2026-12 中旬 (2 周) | L1 + L2 课程包 + 评估题库 |
| 学习者副驾 | 2026-12 下旬 (2 周) | ai-teacher 扩展 |
| 集成测试 + UX | 2026-12 下旬 (1 周) | 5 个关键流程 E2E |
| **v2.0 GA** | **2026-12-31** | 三端（至少两端）打通 |

---

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| DeepSeek / Claude API 限流 | 后端服务不稳定 | 本地 CodeLlama fallback 优先 |
| 学习者过度依赖 AI | 教学目标违背 | L1 课程明确"先思考再用 AI"；评分看过程 |
| 教师抵触"AI 协作" | 推广失败 | v2.0 GA 不强制，先 1 个班级试用 |
| WebSocket 长连接稳定性 | 协作中断 | 自动重连 + 步骤本地缓存 |
| 三端打通成本 | 时间超期 | 允许"两端打通"降级 |

---

## 6. 替代方案与拒绝理由

### 方案 B：保持 v5.0 "AI 辅助编程" 表述，仅做小修小补

**拒绝理由**：竞品 Cursor/Windsurf 已确立 "AI 协作编程" 范式；继续 v5.0 表述将让 MatuX 在 12 个月内彻底边缘化。

### 方案 C：完全重构（抛弃桌面端优先策略）

**拒绝理由**：桌面端已发布 1.0.3，82% 完成度是核心资产；推翻重来不现实。

### 方案 D：仅做 Prompt Engineering 课程，不做工作台

**拒绝理由**：仅有课程无工具，学习者无法在 MatuX 内完成完整 AI 协作体验。

---

## 7. 开放讨论

需在 11-01 工作坊确定：

1. 三大支柱的优先级排序（A 先还是 B 先）
2. L3 课程的"多 Agent 编排"是否 v2.0 必须
3. 教师视角协作监控是否 v2.0 必须（COPILOT-C4）
4. 三端打通是否必须（v2.0 GA 验收）
5. 旧 v1 用户数据迁移策略

---

## 8. 决策日志

| 日期 | 决策 | 理由 |
|---|---|---|
| 2026-10-08 | RFC 创建 | v5.0 路线图与 AI 时代脱节 |
| 待 2026-11-01 | 工作坊结论采纳 | 待 §7 5 项决议 |
| 待 2026-11-08 | RFC 评审通过 | 进入实施 |

---

## 附录 A · 参考资料

- Cursor 官方文档：<https://cursor.com/docs>
- Windsurf Cascade：<https://codeium.com/windsurf>
- Khan Academy Khanmigo：<https://www.khanacademy.org/khan-labs>
- Anthropic Prompt Engineering 指南
- LangGraph 多 Agent 文档

## 附录 B · 相关文档

- [PROJECT_REQUIREMENTS.md §12](../PROJECT_REQUIREMENTS.md) — v6.0 需求草案
- [PROJECT_REQUIREMENTS.md §13](../PROJECT_REQUIREMENTS.md) — v2.0 路线图
- [electron-builder 输出路径配置](../../../electron-builder 输出路径配置.md)（如有）
- [iMato Python 检测与 NSIS 桥接方案](../../../iMato Python 检测与 NSIS 桥接方案.md)（如有）