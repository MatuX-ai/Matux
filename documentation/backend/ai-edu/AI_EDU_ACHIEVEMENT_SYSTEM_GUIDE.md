# AI-Edu 成就系统使用指南

**版本**: v1.0.0  
**更新日期**: 2026-03-03  
**状态**: ✅ 已完成

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [API 端点详解](#api 端点详解)
- [使用示例](#使用示例)
- [成就类型说明](#成就类型说明)
- [最佳实践](#最佳实践)

---

## 概述

### 核心功能

✅ **成就定义与管理**
- 支持多种成就类型（累计型、单次型、序列型、隐藏型）
- 灵活的解锁条件配置（JSON 格式）
- 徽章系统与稀有度分级

✅ **用户成就追踪**
- 实时进度更新与自动解锁判定
- 多维度统计信息
- 成就奖励领取

✅ **通知推送**
- WebSocket 实时通知（可选）
- 成就解锁即时提醒

### 技术特性

- **数据库**: SQLAlchemy ORM
- **API 规范**: RESTful + FastAPI
- **数据模型**: 3 个核心表（Achievement, UserAchievement, AchievementProgress）
- **权限控制**: 管理员 vs 普通用户分离

---

## 快速开始

### 1. 启动服务

```bash
cd backend
python main_ai_edu.py
```

### 2. 初始化成就系统

```bash
# 使用 curl 测试
curl -X POST http://localhost:8000/api/v1/org/1/achievements/admin/initialize \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**:
```json
{
  "success": true,
  "initialized_count": 6,
  "message": "成功初始化 6 个成就"
}
```

### 3. 运行自动化测试

```bash
cd scripts
python test_achievement_api.py
```

---

## API 端点详解

### 管理员接口

#### 1. 创建成就
```http
POST /api/v1/org/{org_id}/achievements/admin/create
Content-Type: application/json
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "name": "代码大师",
  "description": "累计执行 1000 次代码",
  "category": "coding",
  "achievement_type": "cumulative",
  "badge_icon": "/badges/code_master.png",
  "badge_color": "#FFD700",
  "badge_rarity": "legendary",
  "unlock_condition": {
    "type": "cumulative",
    "metric": "code_executions",
    "threshold": 1000,
    "operator": ">="
  },
  "points_reward": 1000,
  "is_hidden": false
}
```

#### 2. 更新成就
```http
PUT /api/v1/org/{org_id}/achievements/admin/{achievement_id}
Content-Type: application/json
Authorization: Bearer {token}
```

#### 3. 停用成就
```http
DELETE /api/v1/org/{org_id}/achievements/admin/{achievement_id}
Authorization: Bearer {token}
```

#### 4. 获取所有成就列表
```http
GET /api/v1/org/{org_id}/achievements/admin/list
  ?category=learning
  &achievement_type=cumulative
  &limit=50
  &offset=0
Authorization: Bearer {token}
```

#### 5. 初始化预定义成就
```http
POST /api/v1/org/{org_id}/achievements/admin/initialize
Authorization: Bearer {token}
```

---

### 用户接口

#### 1. 获取我的成就列表
```http
GET /api/v1/org/{org_id}/achievements/my/list
  ?include_locked=false
  &include_hidden=false
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": 1,
      "user_id": 123,
      "achievement_id": 1,
      "progress": 100.0,
      "is_unlocked": true,
      "unlocked_at": "2026-03-03T10:30:00Z",
      "achievement": {
        "id": 1,
        "name": "勤奋学习者",
        "description": "累计学习时长达到 10 小时",
        "badge_icon": "/badges/diligent_learner.png",
        "badge_color": "#FFD700",
        "points_reward": 100
      }
    }
  ]
}
```

#### 2. 获取我的成就统计
```http
GET /api/v1/org/{org_id}/achievements/my/statistics
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_achievements": 20,
    "unlocked_count": 5,
    "claimed_count": 3,
    "completion_rate": 25.0,
    "category_breakdown": {
      "learning": {
        "total": 8,
        "unlocked": 3,
        "rate": 37.5
      },
      "coding": {
        "total": 6,
        "unlocked": 2,
        "rate": 33.3
      }
    }
  }
}
```

#### 3. 领取成就奖励
```http
POST /api/v1/org/{org_id}/achievements/my/{achievement_id}/claim
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "points": 100,
    "badge": "/badges/diligent_learner.png",
    "message": "恭喜获得成就：勤奋学习者"
  }
}
```

---

### 进度追踪接口

#### 1. 更新成就进度
```http
POST /api/v1/org/{org_id}/achievements/progress/update
Content-Type: application/json
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "metric_name": "study_time_minutes",
  "metric_value": 600,
  "period_type": "all_time"
}
```

**响应示例**:
```json
{
  "success": true,
  "updated_metric": {
    "name": "study_time_minutes",
    "value": 600,
    "period": "all_time"
  },
  "newly_unlocked": [
    {
      "achievement_id": 1,
      "achievement_name": "勤奋学习者",
      "badge_icon": "/badges/diligent_learner.png",
      "points_reward": 100
    }
  ]
}
```

#### 2. 获取当前进度
```http
GET /api/v1/org/{org_id}/achievements/progress/current
  ?metric_name=study_time_minutes
Authorization: Bearer {token}
```

---

## 使用示例

### 场景 1: 学生学习解锁成就

```python
import requests

# 1. 登录获取 token
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'username': 'student1', 'password': 'password123'}
)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 2. 完成课程学习后，更新学习时长
requests.post(
    'http://localhost:8000/api/v1/org/1/achievements/progress/update',
    headers=headers,
    json={
        'metric_name': 'study_time_minutes',
        'metric_value': 600,  # 10 小时
        'period_type': 'all_time'
    }
)

# 3. 查看是否解锁了新成就
response = requests.get(
    'http://localhost:8000/api/v1/org/1/achievements/my/list',
    headers=headers
)
achievements = response.json()['data']

# 4. 领取奖励
for ach in achievements:
    if not ach['is_claimed']:
        requests.post(
            f"http://localhost:8000/api/v1/org/1/achievements/my/{ach['achievement_id']}/claim",
            headers=headers
        )
```

### 场景 2: 教师查看班级成就统计

```python
# 获取班级学生的成就统计
response = requests.get(
    'http://localhost:8000/api/v1/org/1/achievements/admin/list',
    headers={'Authorization': f'Bearer {admin_token}'}
)

all_achievements = response.json()['data']
print(f"总成就数：{len(all_achievements)}")
```

---

## 成就类型说明

### 1. 累计型 (Cumulative)
累计达到某个阈值

```json
{
  "type": "cumulative",
  "metric": "study_time_minutes",
  "threshold": 600,
  "operator": ">="
}
```

**示例**:
- 累计学习 10 小时
- 执行 100 次代码
- 完成 50 道测验

### 2. 单次型 (Single)
单次行为达成条件

```json
{
  "type": "single",
  "event": "quiz_perfect_score",
  "condition": {"score": 100}
}
```

**示例**:
- 单次测验满分
- 第一次成功执行代码
- 一次性通过所有测试

### 3. 序列型 (Sequence)
连续完成某个序列

```json
{
  "type": "sequence",
  "metric": "consecutive_days",
  "threshold": 7
}
```

**示例**:
- 连续学习 7 天
- 连续 5 次测验 90 分以上
- 连续打卡 30 天

### 4. 隐藏型 (Hidden)
达成条件前不显示详情

```json
{
  "is_hidden": true,
  "name": "???",
  "description": "???"
}
```

**示例**:
- 深夜程序员（凌晨写代码 10 次）
- 完美主义者（所有课程满分）

---

## 最佳实践

### 1. 成就设计原则

✅ **难度梯度**
- 设置不同稀有度（common, rare, epic, legendary）
- 从易到难，循序渐进

✅ **多样性**
- 覆盖不同维度（学习、编程、社交、特殊）
- 兼顾不同类型的学生

✅ **及时反馈**
- 实时更新进度
- 解锁时立即推送通知

✅ **奖励机制**
- 积分奖励与成就难度匹配
- 可考虑额外奖励（徽章展示、特殊权限等）

### 2. 性能优化

```python
# 批量更新进度（避免频繁数据库操作）
def batch_update_progress(user_id, metrics_list):
    for metric in metrics_list:
        service.update_progress(user_id, metric['name'], metric['value'])
```

### 3. 安全注意事项

⚠️ **防止刷成就**
- 添加频率限制
- 验证数据来源真实性
- 记录详细日志

⚠️ **数据一致性**
- 使用事务处理
- 定期校验统计数据

---

## 预定义成就清单

系统默认提供以下 6 个成就：

| 名称 | 分类 | 类型 | 难度 | 奖励 |
|-----|------|------|------|------|
| 勤奋学习者 | learning | cumulative | common | 100 |
| 持之以恒 | learning | sequence | rare | 200 |
| 代码新手 | coding | single | common | 50 |
| 调试大师 | coding | cumulative | epic | 500 |
| 学霸附体 | quiz | single | rare | 150 |
| 深夜程序员 | special | cumulative | legendary | 300 |

---

## 故障排查

### 常见问题

**Q1: 成就没有自动解锁？**
- 检查 `unlock_condition` 配置是否正确
- 确认 metric_name 与条件中的名称一致
- 查看 operator 运算符（>=, >, ==, <=, <）

**Q2: 如何添加自定义成就？**
- 使用管理员接口创建
- 或直接修改 `DEFAULT_ACHIEVEMENTS` 常量

**Q3: 成就重复解锁？**
- 检查数据库唯一索引（user_id, achievement_id）
- 确认 `is_unlocked` 状态判断逻辑

---

## 下一步计划

- [ ] WebSocket 实时通知推送
- [ ] 成就分享功能（社交媒体）
- [ ] 成就排行榜
- [ ] 更多预定义成就模板
- [ ] 成就成就链（前置条件）

---

## 参考资源

- [API 文档](http://localhost:8000/docs#/成就系统)
- [测试脚本](../scripts/test_achievement_api.py)
- [数据模型](../backend/models/achievement.py)
- [服务层](../backend/services/achievement_service.py)

---

**文档版本**: v1.0.0  
**维护团队**: AI-Edu Development Team  
**最后更新**: 2026-03-03
