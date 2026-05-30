# 动态课程生成API文档

## 概述

动态课程生成API基于GPT-3.5 Turbo模型，为不同年级和学习背景的学生生成个性化的课程设计方案。该服务能够根据学生的具体情况（年级、学习风格、兴趣爱好等）以及教学需求，自动生成符合教育目标的课程内容。

## 基础信息

- **API版本**: v1
- **基础URL**: `/api/v1/ai/dynamic-course`
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON
- **默认模型**: GPT-3.5 Turbo
- **语言支持**: 中文(zh-CN)

## 权限要求

使用此API需要以下权限：
- `ai.use` - 使用AI服务的基本权限
- `ai.manage` - 管理权限（用于回测等高级功能）

## API端点

### 1. 生成动态课程

#### POST `/api/v1/ai/dynamic-course`

基于学生档案和学习需求生成个性化课程。

**请求参数:**

```json
{
  "student_profile": {
    "grade": 8,
    "age": 14,
    "learning_style": "动手型",
    "prior_knowledge": ["基础电路知识", "简单编程"],
    "interests": ["机器人", "电子制作"],
    "learning_goals": ["理解传感器原理", "掌握基本编程"]
  },
  "subject_area": "信息技术",
  "learning_objectives": ["掌握Arduino编程", "理解传感器应用"],
  "difficulty_level": "中级",
  "project_type": "实践项目",
  "time_constraint": 10,
  "language": "zh-CN"
}
```

**字段说明:**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| student_profile.grade | integer | 是 | 年级 (1-12) |
| student_profile.age | integer | 是 | 年龄 (6-18) |
| student_profile.learning_style | string | 是 | 学习风格 (视觉型/听觉型/动手型/综合型/阅读写作型) |
| student_profile.prior_knowledge | array | 否 | 已有知识背景 |
| student_profile.interests | array | 否 | 兴趣爱好 |
| student_profile.learning_goals | array | 否 | 学习目标 |
| subject_area | string | 是 | 学科领域 (物理/化学/生物/信息技术/数学/工程/科学/技术) |
| learning_objectives | array | 是 | 学习目标列表 |
| difficulty_level | string | 是 | 难度等级 (初级/中级/高级/专家级) |
| project_type | string | 是 | 项目类型 |
| time_constraint | integer | 是 | 时间约束(小时) (1-100) |
| language | string | 否 | 语言，默认为zh-CN |

**成功响应 (200):**

```json
{
  "course_id": 123,
  "course_title": "光敏传感器智能浇水系统",
  "course_description": "这是一个为初中生设计的基于光敏传感器的自动浇水项目...",
  "learning_outcomes": [
    "理解光敏传感器的工作原理",
    "掌握Arduino基础编程",
    "学会设计简单的自动控制系统"
  ],
  "project_components": [
    {
      "title": "项目介绍与准备",
      "description": "了解项目背景、准备硬件设备、安装开发环境",
      "duration": 30,
      "materials": ["电脑", "Arduino开发板", "光敏传感器模块"],
      "steps": ["了解项目背景", "准备硬件设备", "安装开发环境"]
    }
  ],
  "required_materials": [
    "Arduino Uno开发板 x1",
    "光敏传感器模块 x1",
    "面包板 x1",
    "杜邦线若干"
  ],
  "estimated_duration": 135,
  "difficulty_assessment": "适中",
  "prerequisites": ["基础电路连接知识", "简单的C语言编程概念"],
  "assessment_methods": ["项目功能演示", "代码质量检查", "学习过程记录"],
  "generated_at": "2026-02-28T10:30:00",
  "tokens_used": 847,
  "generation_time": 2345
}
```

**错误响应:**

```json
{
  "detail": "请求参数无效"
}
```

**可能的HTTP状态码:**
- 200: 成功生成课程
- 400: 请求参数无效
- 401: 未认证
- 403: 权限不足
- 422: 参数验证失败
- 500: 服务器内部错误

### 2. 获取课程生成历史

#### GET `/api/v1/ai/dynamic-course/history`

获取当前用户的课程生成历史记录。

**查询参数:**

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| limit | integer | 20 | 返回记录数限制 (1-100) |
| offset | integer | 0 | 偏移量 |
| subject_area | string | null | 学科领域筛选 |
| difficulty_level | string | null | 难度等级筛选 |

**成功响应 (200):**

```json
[
  {
    "course_id": 123,
    "course_title": "光敏传感器智能浇水系统",
    "course_description": "这是一个为初中生设计的...",
    "learning_outcomes": ["理解光敏传感器的工作原理", "..."],
    "project_components": [...],
    "required_materials": ["Arduino Uno开发板 x1", "..."],
    "estimated_duration": 135,
    "difficulty_assessment": "适中",
    "prerequisites": ["基础电路连接知识"],
    "assessment_methods": ["项目功能演示"],
    "generated_at": "2026-02-28T10:30:00",
    "tokens_used": 847,
    "generation_time": 2345
  }
]
```

### 3. 获取课程生成统计

#### GET `/api/v1/ai/dynamic-course/stats`

获取当前用户的课程生成统计信息。

**成功响应 (200):**

```json
{
  "total_generations": 45,
  "successful_generations": 38,
  "average_response_time": 2456.7,
  "average_tokens_used": 789.3,
  "completion_rate": 84.4,
  "popular_subjects": [
    {"subject": "信息技术", "count": 23},
    {"subject": "物理", "count": 15}
  ],
  "average_duration": 142
}
```

### 4. 获取模板评估信息

#### GET `/api/v1/ai/dynamic-course/templates`

获取各课程模板的使用评估信息。

**成功响应 (200):**

```json
[
  {
    "template_id": "light_sensor_project",
    "template_name": "光敏传感器自动浇水系统",
    "usage_count": 45,
    "average_rating": 4.2,
    "success_rate": 88.5,
    "average_completion_rate": 92.3,
    "last_used": "2026-02-28T09:15:00"
  }
]
```

### 5. 运行A/B测试回测

#### POST `/api/v1/ai/dynamic-course/backtest`

运行A/B测试回测，比较生成课程与手工课程的效果。（需要管理权限）

**查询参数:**

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| test_period | string | "7d" | 测试周期 (如: 7d, 30d) |

**成功响应 (200):**

```json
{
  "test_name": "动态课程生成效果测试_7d",
  "generated_courses_count": 150,
  "manual_courses_count": 120,
  "generated_completion_rate": 87.5,
  "manual_completion_rate": 72.3,
  "improvement_percentage": 21.0,
  "statistical_significance": true,
  "test_period": "7d",
  "created_at": "2026-02-28T10:30:00"
}
```

## 课程模板

系统预定义了以下课程模板：

### 1. 光敏传感器自动浇水系统
- **适用年级**: 6-9年级
- **学科领域**: 物理、信息技术、生物
- **难度等级**: 初级、中级
- **特点**: 结合传感器技术和植物养护的实践项目

### 2. Arduino基础电子项目
- **适用年级**: 7-10年级
- **学科领域**: 信息技术、物理、工程
- **难度等级**: 初级
- **特点**: Arduino平台入门级电子制作

### 3. Python趣味编程项目
- **适用年级**: 6-10年级
- **学科领域**: 信息技术、数学
- **难度等级**: 初级、中级
- **特点**: 面向青少年的Python编程入门

### 4. STEM创新实践项目
- **适用年级**: 8-12年级
- **学科领域**: 科学、技术、工程、数学
- **难度等级**: 中级、高级
- **特点**: 跨学科STEM综合实践

## 性能指标

### 目标指标
- **生成时间**: < 5秒
- **完成率**: ≥ 85%
- **系统稳定性**: 99.9%

### 监控指标
- 平均响应时间
- 令牌使用效率
- 用户满意度
- 课程完成率追踪

## 错误处理

### 常见错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数无效 | 检查必填字段和参数范围 |
| 401 | 未认证 | 提供有效的JWT令牌 |
| 403 | 权限不足 | 确认用户具有相应权限 |
| 422 | 参数验证失败 | 检查参数格式和有效性 |
| 500 | 服务器内部错误 | 联系技术支持 |

### 错误响应格式

```json
{
  "detail": "具体的错误信息"
}
```

## 最佳实践

### 1. 参数优化建议
- 提供详细的学

生背景信息以获得更好的个性化效果
- 合理设置时间约束，建议10-20小时的项目
- 明确具体的学习目标而非宽泛的描述

### 2. 使用场景
- 个性化作业布置
- 课外兴趣小组活动设计
- STEM课程补充材料生成
- 项目式学习内容定制

### 3. 质量保证
- 系统会自动验证生成内容的安全性和适宜性
- 建议教师审阅后使用生成的课程内容
- 可通过历史记录追踪生成效果

## 配置说明

### 环境变量配置

```bash
# OpenAI API密钥（必需）
OPENAI_API_KEY=your-openai-api-key

# 动态课程生成配置
DYNAMIC_COURSE_MODEL=gpt-3.5-turbo
DYNAMIC_COURSE_TEMPERATURE=0.7
DYNAMIC_COURSE_MAX_TOKENS=1500
DYNAMIC_COURSE_CACHE_TTL=3600
DYNAMIC_COURSE_RATE_LIMIT=10
```

### 模型参数说明
- **temperature**: 0.7 (控制创造性，0-1之间)
- **max_tokens**: 1500 (最大输出长度)
- **cache_ttl**: 3600秒 (缓存有效期)

## 版本历史

### v1.0.0 (2026-02-28)
- 初始版本发布
- 支持4种预定义课程模板
- 实现基础的课程生成功能
- 添加历史记录和统计功能

## 技术支持

如有问题，请联系技术支持团队或查看相关文档。

---
*文档版本: 1.0.0*
*最后更新: 2026-02-28*