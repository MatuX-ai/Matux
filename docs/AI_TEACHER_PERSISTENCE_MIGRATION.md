# AI 教师持久化迁移指南（File → SQL）

> **状态**：P3-D-1 已完成 ✅
> **版本**：v1.0
> **更新日期**：2026-10-09

本文档说明如何将 AI 教师持久化从 JSON 文件（默认 P3-B 行为）切换到 SQLite + SQLAlchemy ORM（P3-D-1 新增），以及回退步骤。

---

## 1. 架构概览

### 1.1 双 backend 设计

```
                ┌──────────────────────┐
                │  AI 教师调用方代码   │
                │  (routes / services) │
                └──────────┬───────────┘
                           │
                ┌──────────▼───────────┐
                │   Repository[T]      │   ← 抽象接口
                │   cache/repository/  │
                │       base.py        │
                └──────────┬───────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
   ┌──────────▼──────────┐   ┌──────────▼──────────┐
   │  FileJsonRepository │   │ SqlAlchemyRepository │
   │  (P3-B 默认)        │   │ (P3-D-1 新增)        │
   │  cache/repository/   │   │ cache/repository/    │
   │    file_json.py     │   │    sql.py            │
   └──────────┬──────────┘   └──────────┬──────────┘
              │                         │
   ┌──────────▼──────────┐   ┌──────────▼──────────┐
   │  data/ai_teacher/   │   │  ai_service.db      │
   │  *.json             │   │  (7 张 ORM 表)       │
   └─────────────────────┘   └─────────────────────┘
```

### 1.2 关键文件

| 路径 | 角色 | 行为 |
|------|------|------|
| `cache/repository/base.py` | `Repository[T]` 抽象接口 | 12 个抽象方法 + 6 个 helper |
| `cache/repository/file_json.py` | FileJsonRepository 实现 | JSON 文件 + debounced flush + atomic writes |
| `cache/repository/sql.py` | SqlAlchemyRepository 实现 | 内存缓存 + ORM 写穿透 + 优雅降级 |
| `cache/repository/factory.py` | 工厂 + 全局单例 | 根据 backend 配置选择实现 |
| `cache/repository/__init__.py` | 模块导出 | 所有公开 API |
| `cache/ai_teacher_persistence.py` | 向后兼容 shim | 重新导出所有 API + AITeacherProfile dataclass |
| `models/ai_teacher_persistence.py` | 7 张 ORM 表 | `AiTeacherKVRow` 基类 + 7 个具体表 |
| `scripts/migrate_ai_teacher_to_sqlite.py` | 迁移工具 | JSON → SQLite 一次性迁移 |

---

## 2. 切换到 SQL backend

### 2.1 前置准备

1. **数据库表已创建**：启动 `main.py` 时会通过 `_do_startup()` 导入 `models.ai_teacher_persistence` 并由 `create_db_and_tables()` 自动建表。
2. **环境准备**：`DATABASE_URL` 环境变量已设置（默认 `sqlite+aiosqlite:///./ai_service.db`）。

### 2.2 切换步骤

#### 方法 A：环境变量（推荐）

```bash
# 临时切换（当前进程）
export AI_TEACHER_PERSISTENCE_BACKEND=sql

# 永久切换（写入 .env）
echo "AI_TEACHER_PERSISTENCE_BACKEND=sql" >> .env
```

#### 方法 B：Settings 配置

修改 `backend/config/settings.py`：

```python
class Settings(BaseSettings):
    # ...
    AI_TEACHER_PERSISTENCE_BACKEND: str = "sql"  # 默认从 file 改为 sql
```

### 2.3 数据迁移（可选）

如果你已经在 file 模式下积累了大量数据，先运行迁移工具：

```bash
# 默认：data/ → ai_service.db，自动备份
python -m scripts.migrate_ai_teacher_to_sqlite

# 自定义路径
python -m scripts.migrate_ai_teacher_to_sqlite \
    --source-dir data/ \
    --target-db /var/lib/imato/ai_teacher.db \
    --backup-dir /backup/ai_teacher_20261009/

# 演练模式（不写数据库）
python -m scripts.migrate_ai_teacher_to_sqlite --dry-run
```

迁移完成后，备份目录保留所有原始 JSON 文件，可用于回退。

### 2.4 验证

```bash
# 验证表已创建
sqlite3 ai_service.db ".tables" | grep ai_teacher
# 输出：ai_teacher_event_history  ai_teacher_live_settings  ai_teacher_memories  ai_teacher_personas  ai_teacher_profiles  ai_teacher_sessions  ai_teacher_user_history

# 验证数据已迁移
sqlite3 ai_service.db "SELECT COUNT(*) FROM ai_teacher_profiles"
# 输出：N（迁移前的画像数）
```

---

## 3. 切换回 File backend（回退）

如果 SQL 模式出现问题需要紧急回退：

### 3.1 修改配置

```bash
# 方法 1：环境变量
export AI_TEACHER_PERSISTENCE_BACKEND=file

# 方法 2：修改 settings.py
AI_TEACHER_PERSISTENCE_BACKEND: str = "file"
```

### 3.2 重启服务

```bash
# 重启 FastAPI 服务
uvicorn main:app --reload
```

### 3.3 验证回退

```bash
# 检查 data/ai_teacher/ 目录
ls -la data/ai_teacher/
# 应包含 7 个 JSON 文件（profiles, sessions, memories, personas, live_settings, event_history, user_history）

# 检查日志
grep "SqlAlchemyRepository" logs/ai_service.log
# 应为空（不应有 SQL 相关日志）
```

---

## 4. 性能对比

| 操作 | File 模式 | SQL 模式 | 差异 |
|------|----------|---------|------|
| 启动加载（100 条数据） | ~5ms | ~10ms（含 ORM 反序列化） | SQL 略慢 2x |
| 单次 set/get | <1ms（纯内存） | <1ms（纯内存 + DB 写） | 一致 |
| 1000 次并发写入 | ~50ms（含 debounced flush） | ~80ms（即时写 DB） | SQL 略慢 |
| 优雅降级 | 文件不可写时仅内存 | DB 不可用时仅内存 | 一致 |

**结论**：在单进程部署中，SQL 模式性能与 file 模式相当（差异在毫秒级）。

---

## 5. ORM 模型设计

### 5.1 7 张表一览

| 表名 | 主键类型 | 值类型 | 来源 |
|------|---------|--------|------|
| `ai_teacher_profiles` | `user_id` (str) | JSON value | 学习画像 |
| `ai_teacher_sessions` | `user_id` (str) | JSON value | 会话上下文 |
| `ai_teacher_memories` | `user_id` (str) | JSON value | 长期记忆 |
| `ai_teacher_personas` | `user_id` (str) | JSON value | AI 教师人格 |
| `ai_teacher_live_settings` | `user_id` (str) | JSON value | 实时推送设置 |
| `ai_teacher_event_history` | `user_id` (固定为 `"records"`) | JSON list | 全局事件历史 |
| `ai_teacher_user_history` | `user_id` (str) | JSON list | 用户事件历史 |

### 5.2 KV 模型设计说明

所有 7 张表都采用 KV 模型：
- **主键**：`user_id`（`String(64)`）
- **值**：`value`（`JSON` 类型）
- **元数据**：`created_at`, `updated_at`（`DateTime`）

为什么不用列表模型（id 主键 + 时间索引）？
- P3-B 的 `_event_history_repo.replace_all({"records": [...]})` 和 `_user_history_repo.set(str(user_id), [...])` 都是 KV 模式
- KV 模型让 SqlAlchemyRepository 与 FileJsonRepository 行为完全一致
- 调用方代码（routes / services）零修改

### 5.3 索引

```python
# PRIMARY KEY 自动索引
user_id  -- 所有 7 张表的主键

# 自动维护
updated_at  -- 所有 7 张表
created_at  -- 所有 7 张表
```

---

## 6. 测试

### 6.1 测试覆盖

| 测试文件 | 测试数 | 覆盖范围 |
|---------|-------|---------|
| `tests/test_ai_teacher_persistence.py` | 22 | FileJsonRepository 基础行为（file backend 专用） |
| `tests/test_ai_teacher_persistence_sql.py` | 25 | SqlAlchemyRepository 基础行为 + 7 张表端到端 |
| `tests/test_ai_teacher_persistence_factory.py` | 14 | factory 切换 + 环境变量 + 单例 |
| `tests/test_ai_teacher_persistence_migration.py` | 12 | 数据迁移工具 + dry-run + 备份 |
| `tests/test_ai_teacher_live_e2e.py` | 14 | live_bus + live_settings 集成（file 模式） |
| `tests/test_ai_teacher_recommender.py` | 13 | AI 教师推荐器 |
| `tests/test_ai_teacher_triggers.py` | 25 | AI 教师触发器 |

**总计**：125 个 AI 教师相关测试，**全部通过** ✅

### 6.2 运行测试

```bash
# 全部 AI 教师测试
cd backend
python -m pytest tests/test_ai_teacher_*.py -v

# 仅 SQL backend 测试
python -m pytest tests/test_ai_teacher_persistence_sql.py -v

# 强制 SQL backend（验证两种 backend）
AI_TEACHER_PERSISTENCE_BACKEND=sql python -m pytest tests/test_ai_teacher_*.py
```

---

## 7. 常见问题

### Q1: 切换到 SQL 模式后，原 JSON 文件还在吗？

**A**: 切换不影响原文件。SQL 模式直接从数据库读取。如果你用迁移工具，备份目录保留了原始 JSON。

### Q2: 数据迁移工具能多次运行吗？

**A**: 可以。已存在的记录会被跳过（不会覆盖），新数据会被写入。

### Q3: SQL 模式能多进程部署吗？

**A**: **不建议**。SQLite 在多进程并发写入时有锁竞争。生产环境推荐：
- 单进程部署（SQL 模式 OK）
- 多进程部署（请等待 P3-D-2：Redis 后端）

### Q4: 表创建失败怎么办？

**A**: 检查：
1. `DATABASE_URL` 是否正确指向可写目录
2. 用户是否有数据库文件写入权限
3. 是否磁盘空间不足

修复后重启服务，`create_db_and_tables()` 会自动重新建表。

### Q5: 性能突然下降？

**A**: 检查：
1. DB 文件是否在慢速磁盘（建议 SSD）
2. 是否有长事务（避免在 route handler 中持有 session）
3. 是否启用了 `pool_pre_ping`（utils/database.py 已启用）

---

## 8. 后续规划

- **P3-D-2**：实现 Redis Pub/Sub 跨进程方案（接 P3-A AchievementStatsCache 模式）
- **P3-D-3**：PostgreSQL 后端（接 Supabase）
- **P3-E**：默认 backend 从 file 切换到 sql（统一升级）

---

## 9. 相关文档

- [P3-D-1持久化升级计划](../reports/P3-D-1持久化升级计划_2026-10-09.md)
- [P3-D-1持久化升级验收报告_2026-10-09.md](../reports/P3-D-1持久化升级验收报告_2026-10-09.md)
- [P3-B技术债解决报告](../reports/P3-B技术债解决报告_2026-10-09.md)
- [utils/database.py](../../backend/utils/database.py) - 数据库连接配置

---

**文档版本**：v1.0
**最后更新**：2026-10-09
**维护**：AI 教师组