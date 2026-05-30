# AI-Edu 智能推荐系统使用指南

**版本**: v1.0.0  
**更新日期**: 2026-03-03  
**状态**: ✅ 已完成

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [API 端点详解](#api 端点详解)
- [使用示例](#使用示例)
- [推荐算法说明](#推荐算法说明)

---

## 概述

### 核心功能

✅ **个性化课程推荐**
- 基于用户画像的智能推荐
- 多维度匹配（难度、兴趣、技能提升）
- 推荐理由解释

✅ **学习路径规划**
- 根据目标技能生成学习序列
- 考虑时间约束
- 循序渐进的难度安排

✅ **用户画像建模**
- 学习风格分析
- 兴趣偏好追踪
- 知识掌握程度评估

### 技术特性

- **混合推荐算法**: 难度匹配 + 兴趣匹配 + 技能提升
- **实时推荐**: < 200ms响应时间
- **可解释性**: 每个推荐都附带理由
- **反馈循环**: 持续优化推荐质量

---

## 快速开始

### 1. 启动服务

```bash
cd backend
python main_ai_edu.py
```

### 2. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

找到"AI 智能推荐"部分

### 3. 测试推荐功能

```bash
# 获取个性化课程推荐
curl -X GET "http://localhost:8000/api/v1/org/1/recommendations/courses?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## API 端点详解

### 1. 获取课程推荐

```http
GET /api/v1/org/{org_id}/recommendations/courses
```

**查询参数**:
- `limit` (可选): 推荐数量，默认 10，最大 50
- `difficulty_min` (可选): 最低难度等级（1-5）
- `difficulty_max` (可选): 最高难度等级（1-5）
- `skill_category` (可选): 技能分类过滤

**响应示例**:
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "course": {
        "course_id": 123,
        "difficulty_level": 2,
        "knowledge_points": ["variables", "functions"],
        "skill_categories": ["programming", "logic"]
      },
      "score": 0.92,
      "reasons": [
        {
          "type": "difficulty_perfect",
          "description": "难度非常适合你当前的水平",
          "confidence": 0.95
        },
        {
          "type": "interest_match",
          "description": "这门课程符合你的兴趣：programming",
          "matched_features": ["programming"],
          "confidence": 0.88
        }
      ],
      "algorithm": "hybrid"
    }
  ]
}
```

---

### 2. 生成学习路径

```http
POST /api/v1/org/{org_id}/recommendations/learning-path
Content-Type: application/json
```

**请求体**:
```json
{
  "target_skills": ["python_basics", "functions"],
  "time_commitment_minutes": 60
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "target_skills": ["python_basics", "functions"],
    "time_commitment": 60,
    "recommended_sequence": [
      {
        "course_id": 1,
        "estimated_duration": 30,
        "difficulty": 1,
        "skills_covered": ["python_basics", "variables"]
      },
      {
        "course_id": 2,
        "estimated_duration": 25,
        "difficulty": 2,
        "skills_covered": ["functions", "parameters"]
      }
    ],
    "total_estimated_time": 55,
    "difficulty_progression": "循序渐进"
  }
}
```

---

### 3. 获取用户画像

```http
GET /api/v1/org/{org_id}/recommendations/user-profile
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 123,
    "learning_style": "visual",
    "preferred_content_type": "video",
    "ability_dimensions": {
      "logical_reasoning": {"score": 75, "level": "intermediate"},
      "math_foundation": {"score": 80, "level": "advanced"}
    },
    "interest_preferences": [
      {"category": "game_development", "interest_score": 90},
      {"category": "robotics", "interest_score": 85}
    ],
    "knowledge_mastery": {
      "python_basics": 0.8,
      "loops": 0.9,
      "functions": 0.6
    },
    "total_study_time_minutes": 600,
    "completed_courses_count": 5,
    "average_quiz_score": 85.5
  }
}
```

---

### 4. 更新学习偏好

```http
PUT /api/v1/org/{org_id}/recommendations/user-profile/preferences
Content-Type: application/json
```

**请求体**:
```json
{
  "learning_style": "kinesthetic",
  "preferred_content_type": "interactive",
  "interest_preferences": [
    {"category": "ai_ml", "interest_score": 95}
  ],
  "recommendation_weights": {
    "difficulty_match": 0.3,
    "interest_match": 0.3,
    "skill_improvement": 0.2,
    "popularity": 0.1,
    "diversity": 0.1
  }
}
```

---

### 5. 提交推荐反馈

```http
POST /api/v1/org/{org_id}/recommendations/feedback/{recommendation_id}
Content-Type: application/json
```

**请求体**:
```json
{
  "clicked": true,
  "completed": false,
  "rating": 4,
  "feedback_text": "课程内容很好，但难度稍高"
}
```

---

## 使用示例

### 场景 1: 学生获取个性化推荐

```python
import requests

# 1. 登录
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'username': 'student1', 'password': 'password123'}
)
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 2. 获取推荐课程
response = requests.get(
    'http://localhost:8000/api/v1/org/1/recommendations/courses',
    headers=headers,
    params={'limit': 10, 'difficulty_max': 3}
)

recommendations = response.json()['data']
for rec in recommendations[:5]:
    print(f"推荐课程 ID: {rec['course']['course_id']}")
    print(f"推荐分数：{rec['score']:.2f}")
    print("推荐理由:")
    for reason in rec['reasons']:
        print(f"  - {reason['description']}")
    print()
```

### 场景 2: 规划学习路径

```python
# 为想学习 Python 基础的学生规划 1 小时学习路径
response = requests.post(
    'http://localhost:8000/api/v1/org/1/recommendations/learning-path',
    headers=headers,
    json={
        'target_skills': ['python_basics'],
        'time_commitment_minutes': 60
    }
)

path = response.json()['data']
print(f"学习目标：{path['target_skills']}")
print(f"预计总时长：{path['total_estimated_time']}分钟")
print("\n推荐学习顺序:")
for i, course in enumerate(path['recommended_sequence'], 1):
    print(f"{i}. 课程{course['course_id']} - "
          f"难度{course['difficulty']} - "
          f"{course['estimated_duration']}分钟")
```

### 场景 3: 查看和优化用户画像

```python
# 获取当前画像
response = requests.get(
    'http://localhost:8000/api/v1/org/1/recommendations/user-profile',
    headers=headers
)

profile = response.json()['data']
print(f"学习风格：{profile['learning_style']}")
print(f"平均成绩：{profile['average_quiz_score']}")
print(f"已完成课程：{profile['completed_courses_count']}门")

# 更新偏好
requests.put(
    'http://localhost:8000/api/v1/org/1/recommendations/user-profile/preferences',
    headers=headers,
    json={
        'learning_style': 'kinesthetic',
        'preferred_content_type': 'interactive'
    }
)
```

---

## 推荐算法说明

### 混合推荐策略

推荐分数由以下 5 个维度加权计算：

#### 1. 难度匹配（权重 30%）

基于**i+1 理论**（最近发展区）：
- 分析用户历史成绩
- 推荐难度略高于当前水平的课程
- 确保成功率在 70-80%

```python
# 难度匹配逻辑
if avg_score >= 90: ideal_difficulty = 4  # 学霸→高难度
elif avg_score >= 70: ideal_difficulty = 3  # 中等→中上难度
elif avg_score >= 50: ideal_difficulty = 2  # 一般→中等难度
else: ideal_difficulty = 1  # 薄弱→基础难度
```

#### 2. 兴趣匹配（权重 30%）

- 提取用户的兴趣类别
- 匹配课程的技能分类和标签
- 优先推荐感兴趣领域的课程

```python
# 兴趣匹配
user_interests = {'game_development', 'robotics'}
course_tags = {'programming', 'game_development'}
match_score = len(intersection) / len(user_interests)
```

#### 3. 技能提升（权重 20%）

- 分析用户的知识掌握程度
- 识别薄弱环节（掌握度 < 70%）
- 推荐能帮助提升弱项的课程

```python
# 找出薄弱知识点
weak_points = [kp for kp in course_knowledge 
               if knowledge_mastery[kp] < 0.7]
```

#### 4. 热门程度（权重 10%）

综合考虑：
- 学习人数
- 平均评分
- 完成率

#### 5. 多样性（权重 10%）

- 避免推荐过于单一
- 鼓励探索不同领域
- 拓宽知识面

### 推荐流程

```
1. 获取用户画像
   ↓
2. 分析学习行为数据
   ↓
3. 筛选候选课程（应用过滤条件）
   ↓
4. 为每个课程计算 5 个维度分数
   ↓
5. 加权求和得到总分
   ↓
6. 按总分排序返回 Top N
   ↓
7. 记录推荐结果（用于优化）
```

---

## 最佳实践

### 1. 冷启动问题

对于新用户（无历史数据）：
- 使用默认权重配置
- 推荐热门入门课程
- 通过初始测验了解水平

### 2. 推荐调优

根据反馈数据调整权重：
```python
# 如果点击率低，提高兴趣匹配权重
weights['interest_match'] += 0.1
weights['difficulty_match'] -= 0.1
```

### 3. A/B 测试

对比不同算法效果：
- 组 A: 使用当前混合算法
- 组 B: 调整权重配置
- 比较点击率、完成率指标

---

## 性能指标

| 指标 | 目标值 | 实际值 |
|-----|-------|--------|
| 推荐响应时间 | < 200ms | ~100ms |
| 推荐点击率 | > 30% | 待统计 |
| 课程完成率 | > 50% | 待统计 |
| 用户满意度 | > 4.0 | 待统计 |

---

## 下一步计划

- [ ] 协同过滤算法（基于用户相似度）
- [ ] 深度学习模型（NeuralCF）
- [ ] 知识图谱推理
- [ ] 强化学习优化长期收益
- [ ] 多模态特征融合

---

## 故障排查

### Q1: 推荐结果不准确？

**可能原因**:
- 用户画像数据不足
- 课程特征标注不完整
- 权重配置不合理

**解决方案**:
- 完善用户兴趣偏好
- 补充课程元数据
- 调整推荐权重

### Q2: 推荐响应慢？

**优化方法**:
- 添加数据库索引
- 缓存用户画像
- 预计算推荐结果

---

**文档版本**: v1.0.0  
**维护团队**: AI-Edu Development Team  
**最后更新**: 2026-03-03
