# AI教学推荐系统

## 📋 系统概述

AI教学推荐系统是一个基于机器学习的个性化课程推荐引擎，结合协同过滤和内容推荐算法，为用户提供精准的学习内容推荐。

## 🏗️ 系统架构

### 核心组件

1. **推荐引擎 (RecommendationEngine)**
   - 协同过滤推荐算法
   - 基于内容的推荐算法
   - 混合推荐策略
   - 用户画像管理

2. **数据模型层**
   - 学习记录 (LearningRecord)
   - 用户学习画像 (UserLearningProfile)
   - 课程特征 (CourseFeature)
   - 推荐反馈 (RecommendationFeedback)

3. **API服务层**
   - 课程推荐接口
   - 学习记录接口
   - 用户画像管理
   - 推荐反馈收集

## 🔧 技术栈

### 后端
- **框架**: FastAPI (Python 3.11+)
- **机器学习**: scikit-learn, numpy, pandas
- **数据库**: SQLAlchemy (异步)
- **算法**: K近邻(NearestNeighbors), TF-IDF, 余弦相似度

### 前端
- **SDK**: TypeScript
- **HTTP客户端**: Axios风格封装
- **类型安全**: 完整的TypeScript类型定义

## 🚀 快速开始

### 1. 安装依赖

```bash
# 后端依赖
pip install -r backend/requirements.txt

# 前端依赖 (如果需要)
npm install
```

### 2. 数据库迁移

```bash
# 创建数据库表
cd backend
python -m utils.database create_tables
```

### 3. 启动服务

```bash
# 启动FastAPI服务
cd backend
uvicorn main:app --reload --port 8000
```

### 4. 前端集成

```typescript
import { AIServiceClient } from './ai-sdk';

const client = new AIServiceClient({
  baseUrl: 'http://localhost:8000',
  accessToken: 'your-access-token'
});

// 获取个性化推荐
const recommendations = await client.getCourseRecommendations(5);
console.log(recommendations);
```

## 📊 核心功能

### 1. 个性化课程推荐

```typescript
// 获取推荐课程
const recommendations = await client.getCourseRecommendations(5);

recommendations.recommendations.forEach(course => {
  console.log(`${course.title} - 推荐分数: ${course.recommendationScore}`);
});
```

### 2. 学习行为追踪

```typescript
// 记录学习进度
await client.recordLearningActivity(
  'course_id',
  'lesson_id',
  0.75,    // 75%进度
  45,      // 45分钟
  'completed',
  4,       // 难度评分
  5        // 兴趣评分
);
```

### 3. 推荐反馈收集

```typescript
// 提交推荐反馈
await client.submitRecommendationFeedback(
  'course_id',
  'like',  // like/dislike/click/skip
  { source: 'homepage' }
);
```

### 4. 用户画像管理

```typescript
// 获取用户学习画像
const profile = await client.getUserLearningProfile();
console.log('技能水平:', profile.skillLevels);
console.log('学习兴趣:', profile.interests);

// 更新学习偏好
await client.updateLearningPreferences({
  preferred_difficulty: 'intermediate',
  preferred_categories: ['programming', 'data_science']
});
```

## 🧠 推荐算法详解

### 协同过滤推荐
- 基于用户行为相似性
- 使用K近邻算法找相似用户
- 推荐相似用户喜欢的课程

### 内容推荐
- 基于课程特征和用户兴趣
- 使用TF-IDF向量化课程描述
- 计算余弦相似度匹配用户兴趣

### 混合策略
- 加权融合两种推荐结果
- 协同过滤权重: 0.6
- 内容推荐权重: 0.4
- 增加结果多样性

## 🛠️ API接口文档

### 推荐相关接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/recommendations/courses` | 获取课程推荐 |
| POST | `/api/v1/recommendations/feedback` | 提交推荐反馈 |
| POST | `/api/v1/recommendations/learning-record` | 记录学习活动 |
| GET | `/api/v1/recommendations/user-profile` | 获取用户画像 |
| PUT | `/api/v1/recommendations/user-profile/preferences` | 更新学习偏好 |
| GET | `/api/v1/recommendations/stats` | 获取推荐统计 |
| POST | `/api/v1/recommendations/refresh-model` | 刷新推荐模型 |

### 请求示例

```bash
# 获取推荐课程
curl -X GET "http://localhost:8000/api/v1/recommendations/courses?num_recommendations=5" \
  -H "Authorization: Bearer your-access-token"

# 记录学习活动
curl -X POST "http://localhost:8000/api/v1/recommendations/learning-record" \
  -H "Authorization: Bearer your-access-token" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "course_python_basics",
    "lesson_id": "variables_intro",
    "progress": 0.75,
    "time_spent": 45,
    "completion_status": "in_progress",
    "difficulty_rating": 4,
    "interest_rating": 5
  }'
```

## 🧪 测试

### 运行单元测试

```bash
cd backend
pytest tests/test_recommendation_service.py -v
```

### 测试覆盖率

```bash
pytest --cov=ai_service tests/test_recommendation_service.py
```

## 📈 性能优化

### 模型缓存
- 推荐模型定期持久化
- 支持快速加载已训练模型
- 增量更新用户画像

### 数据预处理
- 批量处理学习记录
- 异步数据库操作
- 向量化特征缓存

### 算法优化
- 稀疏矩阵优化
- 近似最近邻搜索
- 并行计算支持

## 🔒 安全考虑

### 认证授权
- JWT Token认证
- 用户数据隔离
- 权限分级控制

### 数据保护
- 敏感信息加密存储
- 访问日志记录
- 数据备份策略

## 📊 监控指标

### 推荐质量指标
- 点击率 (CTR)
- 转化率
- 用户满意度
- 推荐多样性

### 系统性能指标
- 响应时间
- 吞吐量
- 模型准确率
- 资源使用率

## 🚀 部署指南

### Docker部署

```dockerfile
# 构建镜像
docker build -t imato-recommendation .

# 运行容器
docker run -p 8000:8000 imato-recommendation
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendation-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recommendation
  template:
    metadata:
      labels:
        app: recommendation
    spec:
      containers:
      - name: recommendation
        image: imato-recommendation:latest
        ports:
        - containerPort: 8000
```

## 🤝 贡献指南

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-org/imato.git
cd imato

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd ../src/ai-sdk
npm install
```

### 代码规范

- Python: Black格式化, Flake8检查
- TypeScript: ESLint + Prettier
- 文档: 使用JSDoc/Google风格注释

## 📞 技术支持

如有问题，请联系：
- 📧 邮箱: support@imato.com
- 🐛 GitHub Issues: [项目Issues页面]
- 💬 技术交流群: [微信群/Slack频道]

---

*© 2024 iMato AI Service. 保留所有权利.*
