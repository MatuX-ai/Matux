# 自适应学习路径引擎技术文档

## 📋 系统概述

自适应学习路径引擎是一个智能教育推荐系统，能够根据用户的学习行为、技能水平和兴趣偏好，动态调整学习路径和内容推荐。

## 🏗️ 系统架构

### 核心组件

1. **推荐引擎 (RecommendationEngine)**
   - 协同过滤推荐算法
   - 基于内容的推荐算法
   - 混合推荐策略
   - 用户画像管理
   - **自适应学习路径推荐**

2. **智能分析组件**
   - **Markov Chain行为分析器** - 分析用户学习行为模式
   - **知识图谱管理器** - 基于Neo4j的路径规划
   - **动态难度计算器** - 实时难度系数调整

3. **数据模型层**
   - 学习记录 (LearningRecord)
   - 用户学习画像 (UserLearningProfile)
   - 课程特征 (CourseFeature)
   - 推荐反馈 (RecommendationFeedback)
   - 行为事件 (BehaviorEvent)
   - 知识节点 (KnowledgeNode)

4. **API服务层**
   - 课程推荐接口
   - 学习记录接口
   - 用户画像管理
   - 推荐反馈收集
   - **自适应推荐接口**
   - **难度分析接口**
   - **学习路径规划接口**
   - **行为事件记录接口**

## 🔧 技术实现

### 新增智能功能实现

#### 1. Markov Chain用户行为分析
```python
# 核心实现
class MarkovChainAnalyzer:
    def analyze_user_behavior(self, user_id: str) -> BehaviorAnalysis:
        # 分析用户操作日志中的失败次数、跳过节点等行为模式
        # 构建用户行为状态转移矩阵
        # 识别学习行为异常和偏好模式
        pass
    
    def add_behavior_event(self, event: BehaviorEvent):
        # 记录用户行为事件用于后续分析
        pass
```

#### 2. 知识图谱路径推荐
```python
# 基于Neo4j的知识图谱实现
class KnowledgeGraphManager:
    def recommend_path(self, user_profile: UserProfile, 
                      graph) -> List[str]:
        # 实现: graph.shortest_path(current_node, 'expert')
        # 构建知识点关联关系
        # 规划最优学习路径
        pass
```

#### 3. 动态难度系数计算
```python
# 核心难度公式实现
class DifficultyCalculator:
    @staticmethod
    def calculate_dynamic_difficulty(success_rate: float) -> float:
        """
        动态难度系数公式: difficulty = 1/(success_rate)^2
        """
        if success_rate <= 0:
            return float('inf')
        return 1 / (success_rate ** 2)
```

#### 4. 自适应推荐融合
```python
# 智能推荐融合算法
async def get_adaptive_recommendations(self, user_id: str, db: AsyncSession, 
                                     num_recommendations: int = 5) -> List[Dict[str, Any]]:
    # 1. 分析用户行为模式
    behavior_analysis = self.markov_analyzer.analyze_user_behavior(user_id)
    
    # 2. 基于知识图谱的路径推荐
    learning_path = self.knowledge_graph.recommend_learning_path(user_profile, target_expertise)
    
    # 3. 应用难度调整
    adjusted_recommendations = await self._apply_difficulty_adjustment(user_id, recommendations, db)
    
    return adjusted_recommendations
```

#### 1. 用户画像管理
```python
class UserLearningProfile(Base):
    """用户学习画像模型"""
    __tablename__ = "user_learning_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    learning_preferences = Column(JSON)  # 学习偏好设置
    skill_levels = Column(JSON)  # 技能水平字典 {skill: level}
    interests = Column(JSON)  # 兴趣标签列表
    learning_history_vector = Column(JSON)  # 学习历史向量表示
```

#### 2. 协同过滤推荐
```python
async def _collaborative_filtering_recommendations(self, user_id: str, num_candidates: int) -> List[Dict[str, Any]]:
    """协同过滤推荐"""
    if user_id not in self.user_index_map:
        return []
    
    user_idx = self.user_index_map[user_id]
    user_vector = self.interaction_matrix[user_idx].reshape(1, -1)
    
    # 找到相似用户
    distances, indices = self.model.kneighbors(user_vector, n_neighbors=min(10, len(self.interaction_matrix)))
    
    # 收集候选课程
    candidate_scores = {}
    for idx in indices[0]:
        if idx != user_idx:  # 排除自己
            similarity = 1 / (1 + distances[0][np.where(indices[0] == idx)[0][0]])
            neighbor_interactions = self.interaction_matrix[idx]
            
            for course_idx, score in enumerate(neighbor_interactions):
                if score > 0 and self.interaction_matrix[user_idx][course_idx] == 0:
                    course_id = list(self.course_index_map.keys())[course_idx]
                    if course_id not in candidate_scores:
                        candidate_scores[course_id] = 0
                    candidate_scores[course_id] += score * similarity
    
    return sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:num_candidates]
```

#### 3. 内容推荐
```python
async def _content_based_recommendations(self, user_id: str, num_candidates: int) -> List[Dict[str, Any]]:
    """基于内容的推荐"""
    if user_id not in self.user_profiles:
        return []
    
    user_profile = self.user_profiles[user_id]
    user_interests = ' '.join(user_profile.get('interests', []))
    
    if not user_interests or self.content_features is None:
        return []
    
    # 计算用户兴趣与课程的相似度
    user_vector = self.tfidf_vectorizer.transform([user_interests])
    similarities = cosine_similarity(user_vector, self.content_features).flatten()
    
    # 获取推荐课程
    candidate_scores = []
    for idx, similarity in enumerate(similarities):
        if similarity > 0:
            course_id = self.course_ids_for_content[idx]
            if course_id in self.course_features:
                base_score = similarity * self.course_features[course_id]['popularity_score']
                candidate_scores.append({
                    'course_id': course_id,
                    'score': base_score,
                    'type': 'content'
                })
    
    return sorted(candidate_scores, key=lambda x: x['score'], reverse=True)[:num_candidates]
```

#### 4. 混合推荐策略
```python
def _hybrid_recommendations(self, cf_recs: List[Dict], content_recs: List[Dict], num_final: int) -> List[Dict[str, Any]]:
    """混合推荐结果"""
    # 合并两种推荐结果
    all_recs = {}
    
    # 处理协同过滤推荐 (权重0.6)
    for rec in cf_recs:
        course_id = rec['course_id']
        if course_id not in all_recs:
            all_recs[course_id] = {'score': 0, 'types': []}
        all_recs[course_id]['score'] += rec['score'] * 0.6
        all_recs[course_id]['types'].append('collaborative')
    
    # 处理内容推荐 (权重0.4)
    for rec in content_recs:
        course_id = rec['course_id']
        if course_id not in all_recs:
            all_recs[course_id] = {'score': 0, 'types': []}
        all_recs[course_id]['score'] += rec['score'] * 0.4
        all_recs[course_id]['types'].append('content')
    
    # 转换为列表并排序
    final_recs = [
        {
            'course_id': course_id,
            'score': data['score'],
            'recommendation_types': data['types']
        }
        for course_id, data in all_recs.items()
    ]
    
    return sorted(final_recs, key=lambda x: x['score'], reverse=True)[:num_final]
```

## 🎯 待实现功能

### 1. Markov Chain用户行为分析
```python
# TODO: 实现Markov Chain分析用户操作日志
class MarkovChainAnalyzer:
    """Markov链用户行为分析器"""
    
    def __init__(self):
        self.transition_matrix = {}
        self.state_mapping = {}
        
    def analyze_user_logs(self, user_logs: List[Dict]) -> Dict:
        """分析用户操作日志，识别行为模式"""
        # 实现失败次数、跳过节点等行为分析
        pass
        
    def build_transition_matrix(self, sequences: List[List[str]]) -> np.ndarray:
        """构建状态转移矩阵"""
        # 实现马尔可夫链转移概率计算
        pass
```

### 2. 知识图谱集成 (Neo4j)
```python
# TODO: 实现知识图谱关联知识点和项目
class KnowledgeGraphManager:
    """知识图谱管理器"""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        
    def create_knowledge_nodes(self, concepts: List[Dict]):
        """创建知识点节点"""
        pass
        
    def create_relationships(self, relationships: List[Dict]):
        """创建知识点间的关系"""
        pass
        
    def find_shortest_path(self, start_node: str, end_node: str) -> List[str]:
        """查找最短学习路径"""
        # 实现: graph.shortest_path(current_node, 'expert')
        pass
```

### 3. 动态难度系数计算
```python
# TODO: 实现动态难度系数公式: difficulty = 1/(success_rate)^2
class DifficultyCalculator:
    """动态难度计算器"""
    
    @staticmethod
    def calculate_dynamic_difficulty(success_rate: float) -> float:
        """
        计算动态难度系数
        公式: difficulty = 1/(success_rate)^2
        """
        if success_rate <= 0:
            return float('inf')  # 无限难度
        return 1 / (success_rate ** 2)
        
    def adjust_course_difficulty(self, course_id: str, user_performance: Dict) -> float:
        """根据用户表现调整课程难度"""
        # 基于用户成功率动态调整难度
        pass
```

## 📊 验收标准

### 1. 推荐路径完成率
- **目标**: ≥70%
- **测量方法**: 跟踪用户按照推荐路径完成课程的比例
- **当前状态**: ⚠️ 需要实现路径跟踪和完成率统计

### 2. 学习时长优化
- **目标**: 用户平均学习时长减少30%
- **测量方法**: 对比推荐前后用户的平均学习时长
- **当前状态**: ⚠️ 需要实现学习时长统计和对比分析

## 🛠️ API接口

### 推荐相关接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/recommendations/courses` | 获取课程推荐 |
| POST | `/api/v1/recommendations/learning-record` | 记录学习活动 |
| GET | `/api/v1/recommendations/user-profile` | 获取用户画像 |
| PUT | `/api/v1/recommendations/user-profile/preferences` | 更新学习偏好 |

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

## 🧪 测试验证

### 单元测试
```bash
cd backend
python -m pytest tests/test_recommendation_service.py -v
```

### 回测验证
```bash
python scripts/completion_backtest.py
```

## 🚀 部署配置

### 环境变量
```bash
# 推荐系统配置
RECOMMENDATION_MODEL_PATH=./models/recommendation_model.pkl
TRAINING_DATA_REFRESH_INTERVAL=24  # 小时
MIN_TRAINING_SAMPLES=100
```

### 性能优化
- 模型缓存和定期训练
- 异步数据库操作
- 向量化特征预计算
- 结果多样性保证

## 📈 监控指标

### 推荐质量指标
- 点击率 (CTR)
- 转化率
- 用户满意度评分
- 推荐多样性指数

### 系统性能指标
- 响应时间 < 200ms
- 模型准确率 > 80%
- 并发处理能力
- 资源使用率

## 🔒 安全考虑

### 数据保护
- 用户学习数据加密存储
- 个人画像匿名化处理
- 访问权限控制
- 审计日志记录

### 隐私合规
- GDPR合规性
- 用户数据最小化原则
- 数据删除机制
- 第三方数据共享限制

## 🤝 开发规范

### 代码规范
- Python: Black格式化, Flake8检查
- 类型提示: 完整的类型注解
- 文档: Google风格注释
- 测试: 80%以上覆盖率

### 模块设计
- 高内聚低耦合
- 单一职责原则
- 接口抽象化
- 错误处理完善

---

*© 2024 iMato AI Service. 保留所有权利.*