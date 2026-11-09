# P3-C 社交化分享使用指南

> **版本**：v1.0
> **创建日期**：2026-10-09
> **承接文档**：[P3-D-2 Redis 跨进程方案](AI_TEACHER_PERSISTENCE_REDIS.md)

## 概述

P3-C 阶段为 iMato 学习平台引入了**完整的社交化分享能力**。用户可以一键分享学习成果（成就解锁、课程完成）、通过邀请码体系实现病毒式传播。所有分享均通过**短链 + 二维码 + HTML 落地页**实现多平台适配（微信 / 微博 / X / 复制链接）。

## 1. 功能总览

| 功能 | 说明 | 入口 |
|------|------|------|
| 分享卡片 | 解锁成就 / 完成课程时自动生成 | 成就解锁、课程完成 |
| 短链落地页 | 8 字符 base62 短链，永久可用 | `/share/{short_code}` |
| 二维码 | 自动生成 PNG 缓存到 `/static/qrcodes/` | `/api/v1/share/cards/{id}/qr` |
| Open Graph | 微信 / 微博 / X 平台预览 | `<meta property="og:*">` |
| 邀请码 | 每个用户可生成多个邀请码 | `/invite/{code}` |
| 奖励机制 | 使用邀请码注册自动奖励（mock） | `invite_records.rewarded_at` |
| 多渠道追踪 | wechat / weibo / x / link / copy | `share_count` + 分享历史 |

## 2. 数据模型

### 2.1 share_cards（分享卡片）

每张卡片 = 一个对象的分享元数据 + 短链 + 二维码：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | 主键 |
| `card_type` | String(50) | `achievement` / `course` / `user_profile` / `learning_record` |
| `target_id` | Integer | 目标对象 ID（成就/课程/用户/学习记录） |
| `creator_id` | Integer FK | 创建者 user_id |
| `title` | String(200) | 卡片标题（"我解锁了 [成就名]！"） |
| `subtitle` | String(500) | 副标题 |
| `cover_image` | String(500) | 封面图 URL |
| `description` | Text | 描述文案 |
| `metadata` | JSON | 扩展元数据（成就 badge、课程封面等） |
| `short_code` | String(16) UNIQUE | 短链代码（8 字符 base62） |
| `qr_code_path` | String(500) | 二维码图片路径 |
| `view_count` | Integer | 浏览次数 |
| `share_count` | Integer | 分享次数 |
| `status` | String(20) | `active` / `expired` / `disabled` |
| `expires_at` | DateTime | 过期时间（None 永不过期） |
| `created_at` / `updated_at` | DateTime | 时间戳 |

### 2.2 invite_codes（邀请码）

每个用户可生成多个邀请码，追踪推广效果：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | 主键 |
| `code` | String(16) UNIQUE | 邀请码（8 字符 base62） |
| `creator_id` | Integer FK | 生成者 user_id |
| `usage_limit` | Integer | 使用次数上限（NULL 无限） |
| `used_count` | Integer | 已使用次数 |
| `reward_type` | String(20) | `points` / `discount` / `gift` |
| `reward_value` | Integer | 奖励值（积分/折扣/礼品） |
| `channel` | String(50) | 推广渠道（wechat / weibo / x / link） |
| `status` | String(20) | `active` / `exhausted` / `expired` / `disabled` |
| `expires_at` | DateTime | 过期时间 |
| `created_at` | DateTime | 创建时间 |

### 2.3 invite_records（邀请记录）

每次邀请使用留痕，便于奖励发放与防刷：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | 主键 |
| `code_id` | Integer FK | 邀请码 ID |
| `inviter_id` | Integer FK | 邀请人 user_id |
| `invitee_id` | Integer FK | 被邀请人 user_id（NULL 直到注册） |
| `status` | String(20) | `pending` / `registered` / `rewarded` |
| `registered_at` | DateTime | 注册时间 |
| `rewarded_at` | DateTime | 奖励发放时间 |
| `metadata` | JSON | 扩展元数据（IP、设备等） |
| `created_at` | DateTime | 创建时间 |

## 3. API 文档

### 3.1 分享卡片 API

#### POST /api/v1/share/cards（需登录）

创建分享卡片（生成短链 + QR）。

**请求体**：
```json
{
  "card_type": "achievement",
  "target_id": 42,
  "title": "自定义标题（可选）",
  "subtitle": "自定义副标题（可选）",
  "description": "自定义描述（可选）",
  "expires_at": "2026-12-31T23:59:59Z（可选）"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "card_type": "achievement",
    "target_id": 42,
    "creator_id": 1,
    "title": "🎉 testuser 解锁了成就：勤奋学习者！",
    "subtitle": "连续学习 7 天",
    "cover_image": "/static/badges/diligent.png",
    "description": "我在 iMato 解锁了【勤奋学习者】，获得 100 积分！",
    "short_code": "skB0NM7V",
    "short_url": "http://localhost:8000/share/skB0NM7V",
    "qr_code_url": "http://localhost:8000/api/v1/share/cards/1/qr",
    "view_count": 0,
    "share_count": 0,
    "status": "active",
    "is_active": true,
    "created_at": "2026-10-09T12:00:00"
  }
}
```

**错误**：
- `400` - 目标对象不存在
- `422` - 请求字段缺失或类型错误

**Curl 示例**：
```bash
curl -X POST http://localhost:8000/api/v1/share/cards \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"card_type": "achievement", "target_id": 42}'
```

#### GET /api/v1/share/cards/{short_code}（公开）

查询卡片详情（统计、metadata）。

**响应**：同上 `data` 字段。

#### POST /api/v1/share/cards/{short_code}/track-view（公开）

追踪浏览行为（+1 view_count）。

**响应**：
```json
{"success": true}
```

#### POST /api/v1/share/cards/{short_code}/track-share?channel=wechat（公开）

追踪分享行为（+1 share_count）。

**Query 参数**：
- `channel`: `wechat` / `weibo` / `x` / `link` / `copy`（默认 `link`）

**响应**：
```json
{"success": true}
```

#### GET /api/v1/share/cards/{card_id}/qr（公开）

返回 QR 二维码图片（PNG）。

**响应**：`image/png` 文件流。

### 3.2 邀请码 API

#### POST /api/v1/invite/codes（需登录）

生成邀请码。

**请求体**：
```json
{
  "usage_limit": 10,
  "reward_type": "points",
  "reward_value": 200,
  "channel": "wechat",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "code": "abC12XyZ",
    "creator_id": 1,
    "usage_limit": 10,
    "used_count": 0,
    "remaining": 10,
    "reward_type": "points",
    "reward_value": 200,
    "channel": "wechat",
    "status": "active",
    "is_available": true,
    "created_at": "2026-10-09T12:00:00"
  }
}
```

#### GET /api/v1/invite/codes/me?limit=50&offset=0（需登录）

我创建的邀请码列表。

#### GET /api/v1/invite/codes/{code}（公开）

查询邀请码信息。

#### POST /api/v1/invite/codes/{code}/use（需登录）

使用邀请码（被邀请人注册后调用）。

**请求体**：
```json
{
  "invitee_id": 99,
  "metadata": {
    "ip": "127.0.0.1",
    "device": "iOS",
    "ua": "Mozilla/5.0..."
  }
}
```

**错误**：
- `404` - 邀请码不存在或已禁用
- `400` - 已达使用上限 / 已过期

#### GET /api/v1/invite/records/me?limit=50&offset=0（需登录）

我的邀请记录列表。

### 3.3 落地页（HTML 模板）

| 路径 | 说明 |
|------|------|
| `GET /share/{short_code}` | 分享落地页（公开访问） |
| `GET /invite/{code}` | 邀请注册落地页（公开访问） |

## 4. 落地页嵌入指南

### 4.1 Open Graph 标签

落地页自动嵌入 Open Graph 标签，微信/微博/X 平台可直接抓取预览：

```html
<meta property="og:title" content="🎉 testuser 解锁了成就：勤奋学习者！">
<meta property="og:description" content="我在 iMato 解锁了【勤奋学习者】，获得 100 积分！">
<meta property="og:image" content="/static/badges/diligent.png">
<meta property="og:url" content="http://localhost:8000/share/skB0NM7V">
<meta property="og:type" content="website">
```

### 4.2 多平台分享按钮

落地页内置 4 个分享按钮：

```html
<button onclick="shareToWechat()">微信（扫码）</button>
<button onclick="shareToWeibo()">微博</button>
<button onclick="shareToX()">X / Twitter</button>
<button onclick="copyLink()">复制链接</button>
```

按钮点击后会：
1. 触发 `track-share` API 记录渠道
2. 弹出对应平台的分享对话框（或复制到剪贴板）

### 4.3 移动优先设计

落地页采用响应式 CSS：

- 默认移动端布局（375px 宽）
- 平板自适应（>= 768px）
- 桌面端居中显示（max-width: 600px）

### 4.4 iOS 深度链接

落地页底部"打开 App"按钮调用 iMato scheme：

```html
<a href="imato://share/{short_code}">打开 iMato App</a>
```

## 5. 邀请码体系

### 5.1 使用流程

```
邀请人生成邀请码  →  分享链接 / QR  →  被邀请人点击  →  注册时调用 /use  →  自动奖励
   (creator_id)        (短链)          (落地页)        (invitee_id)         (rewarded)
```

### 5.2 奖励类型

| 类型 | 说明 | 字段 |
|------|------|------|
| `points` | 积分奖励 | `reward_value` = 积分数量 |
| `discount` | 折扣券 | `reward_value` = 折扣百分比 |
| `gift` | 实物礼品 | `reward_value` = 礼品 ID |

**当前实现**：仅记录 `rewarded_at` 时间戳，**未实际发放奖励**。未来接积分系统时实现。

### 5.3 推广渠道追踪

`channel` 字段记录推广渠道：

| 值 | 平台 |
|------|------|
| `wechat` | 微信 |
| `weibo` | 微博 |
| `x` | X / Twitter |
| `link` | 直接复制链接 |

用于分析不同渠道的转化率。

## 6. 数据迁移指南

### 6.1 创建迁移

```bash
cd backend
alembic upgrade head
```

会执行 `20261009_p3c_share.py`，创建 3 张表：

- `share_cards`（含 4 个索引：card_type、target_id、short_code、status）
- `invite_codes`（含 2 个索引：code、status）
- `invite_records`（含 2 个索引：code_id、inviter_id）

### 6.2 回滚

```bash
alembic downgrade -1
```

### 6.3 验证表结构

```sql
sqlite3 backend.db ".schema share_cards"
```

## 7. 成就自动分享机制

### 7.1 触发逻辑

在 `AchievementService.unlock_achievement` 方法中，自动创建分享卡：

```python
# backend/services/achievement_service.py
def unlock_achievement(self, user_id, achievement_id):
    # ... 原有解锁逻辑
    
    # 【P3-C】自动生成分享卡
    try:
        self._auto_create_share_card(user_id, achievement_id)
    except Exception as e:
        logger.warning(f"自动生成分享卡失败: {e}")
```

### 7.2 去重逻辑

同一用户同一成就**只创建一次**分享卡（避免重复刷分享链接）：

```python
existing = db.query(ShareCard).filter(
    ShareCard.card_type == ShareCardType.ACHIEVEMENT,
    ShareCard.target_id == achievement_id,
    ShareCard.creator_id == user_id,
).first()
if existing:
    return  # 已存在，跳过
```

## 8. 安全注意事项

### 8.1 防刷机制

| 风险 | 缓解措施 |
|------|----------|
| 短链碰撞 | `secrets.choice` 密码学强度 + 5 次重试 + 数据库唯一约束 |
| QR 生成性能 | 异步生成 + 文件缓存（不阻塞主流程） |
| 邀请刷量 | `usage_limit` 限制 + 后续接 IP 限流 + captcha |
| 公开页面爬虫 | 落地页只展示公开信息（不暴露用户隐私） |
| 二维码占用 | 设定 30 天过期清理任务（监控告警） |

### 8.2 数据访问控制

| API | 鉴权 |
|-----|------|
| `POST /api/v1/share/cards` | 需登录（JWT） |
| `GET /api/v1/share/cards/{code}` | 公开 |
| `POST /track-view`、`POST /track-share` | 公开（但建议接 IP 限流） |
| `GET /share/{code}` | 公开 |
| `POST /api/v1/invite/codes` | 需登录 |
| `POST /api/v1/invite/codes/{code}/use` | 需登录（被邀请人） |
| `GET /api/v1/invite/codes/me` | 需登录 |
| `GET /api/v1/invite/records/me` | 需登录 |

### 8.3 公开页面内容控制

`render_landing_data` 故意只返回 `creator.id`、`creator.username`、`creator.role` 三个字段，**不返回邮箱、手机号等隐私信息**。

## 9. 性能与监控

### 9.1 性能指标

| 操作 | 延迟 | 备注 |
|------|------|------|
| 创建分享卡 | < 50ms | 含短链生成 + QR 编码 |
| 短链跳转 | < 10ms | 仅 DB 查询 + view_count +1 |
| 邀请码生成 | < 20ms | 含短链唯一性检查 |
| 邀请码使用 | < 30ms | 含使用次数 + 记录创建 |

### 9.2 监控建议

未来应监控：

- `share_cards.created_at` 每日新增量（DAU 分享率）
- `share_cards.view_count` 分布（爆款内容识别）
- `invite_codes.used_count / usage_limit`（推广效果）
- `/static/qrcodes/` 目录大小（清理任务）

## 10. 测试

P3-C 共 **83 个测试**全部通过：

```bash
cd backend
python -m pytest tests/test_share_service.py \
                 tests/test_invite_service.py \
                 tests/test_share_routes.py -v
```

| 测试文件 | 测试数 | 覆盖 |
|----------|--------|------|
| `test_share_service.py` | 29 | 短链工具、QR 工具、创建/查询/追踪、状态判断 |
| `test_invite_service.py` | 30 | 生成/使用/限制/过期/记录/奖励 |
| `test_share_routes.py` | 24 | API 路由、HTML 落地页 |

## 11. 常见问题

### Q1: QR 二维码生成失败怎么办？

A: `create_card` 已使用 try-except 捕获 QR 生成错误，**不会阻塞主流程**。卡片仍可正常创建，只是 `qr_code_path` 为空。可后续异步重试。

### Q2: 短链冲突了怎么办？

A: 短链生成使用 8 字符 base62（62^8 ≈ 218 万亿），理论碰撞概率极低。即使碰撞，`generate_unique_short_code` 也会自动重试 5 次。极端情况会抛 `RuntimeError`。

### Q3: 邀请码奖励如何对接实际积分系统？

A: 当前 `InviteService._schedule_reward` 仅记录 `rewarded_at` 时间戳。接积分系统时，在该方法内调用积分服务：

```python
def _schedule_reward(self, record, invite):
    points_service.add_points(record.inviter_id, invite.reward_value)
    record.rewarded_at = datetime.now(timezone.utc)
    record.status = InviteRecordStatus.REWARDED
```

### Q4: 落地页模板可以自定义吗？

A: 可以。修改 `backend/templates/share/landing.html` 和 `invite.html` 即可。模板变量详见 `render_landing_data` 方法。

## 12. 未来演进

| 阶段 | 功能 |
|------|------|
| **P3-C-2** | 学习群组对比（同一班级/好友对比学习进度） |
| **P3-C-3** | 分享回流分析（用户从哪个平台 / 哪个用户进来） |
| **P3-D-3** | PostgreSQL 后端 + 短链查询索引优化 |
| **P3-E** | 风控系统：IP 限流 + captcha + 异常行为检测 |

## 13. 变更日志

### v1.0（2026-10-09）

- ✨ 新增 `share_cards` / `invite_codes` / `invite_records` 三张表
- ✨ 新增 `ShareService` + `InviteService` 服务层
- ✨ 新增短链生成 + 二维码生成工具
- ✨ 新增分享 / 邀请码 API 路由（10 个端点）
- ✨ 新增 3 个 HTML 落地页模板
- ✨ 集成成就解锁自动分享钩子
- ✅ 83 个测试全部通过
- 📝 完成本文档

---

**维护人**：iMato 后端团队
**反馈渠道**：Slack #p3-c-sharing
