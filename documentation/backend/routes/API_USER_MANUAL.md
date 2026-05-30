# 教育数据联邦学习API使用手册

## 版本信息
- **文档版本**: 1.0
- **API版本**: v1
- **更新日期**: 2026-02-28

## 目录
1. [概述](#概述)
2. [认证与授权](#认证与授权)
3. [核心API接口](#核心api接口)
4. [数据格式规范](#数据格式规范)
5. [错误处理](#错误处理)
6. [使用示例](#使用示例)
7. [最佳实践](#最佳实践)

## 概述

教育数据联邦学习API提供了一套完整的接口，用于：
- 教育数据的安全共享和处理
- 联邦学习模型的训练和管理
- STEM能力分析和报告生成
- 区域教育水平对比分析

### 基础URL
```
生产环境: https://api.imato.edu.cn/api/v1/edu-data
测试环境: https://test-api.imato.edu.cn/api/v1/edu-data
```

### 响应格式
所有API响应均采用JSON格式：
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2026-02-28T10:30:00Z"
}
```

## 认证与授权

### JWT Token认证
```bash
# 获取访问令牌
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

# 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 请求头设置
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json
```

### 权限要求
不同API接口需要不同的权限：
- `education_data`: 教育数据访问权限
- `ai`: AI模型训练权限
- `admin`: 管理员权限

## 核心API接口

### 1. 联邦学习训练管理

#### 启动训练
```http
POST /api/v1/edu-data/trainings/
Authorization: Bearer {token}
Content-Type: application/json

{
  "model_name": "stem_ability_analyzer",
  "rounds": 20,
  "participants": ["school_001", "school_002", "school_003"],
  "subjects": ["math", "science", "technology", "engineering"],
  "grade_levels": ["middle", "high"],
  "privacy_level": "high",
  "privacy_budget": 1.0,
  "learning_rate": 0.01,
  "batch_size": 64,
  "enable_trend_analysis": true,
  "enable_region_comparison": true
}
```

**响应示例**:
```json
{
  "training_id": "train_20260228_12345",
  "message": "教育数据联邦学习训练已启动",
  "model_name": "stem_ability_analyzer",
  "subjects": ["math", "science", "technology", "engineering"],
  "privacy_level": "high",
  "created_at": "2026-02-28T10:30:00Z"
}
```

#### 查询训练状态
```http
GET /api/v1/edu-data/trainings/{training_id}
Authorization: Bearer {token}
```

**响应示例**:
```json
{
  "training_id": "train_20260228_12345",
  "current_round": 5,
  "total_rounds": 20,
  "status": "training",
  "progress_percentage": 25.0,
  "metrics_history": [
    {
      "round": 1,
      "accuracy": 0.75,
      "loss": 0.85
    }
  ],
  "participants_status": {
    "school_001": "online",
    "school_002": "online",
    "school_003": "offline"
  },
  "estimated_completion_time": "2026-02-28T15:30:00Z"
}
```

### 2. 节点管理

#### 注册教育节点
```http
POST /api/v1/edu-data/nodes/register
Authorization: Bearer {token}
Content-Type: application/json

{
  "node_id": "school_001",
  "node_name": "北京市第一中学",
  "node_type": "school",
  "region_id": "beijing_001",
  "contact_info": {
    "email": "tech@school001.edu.cn",
    "phone": "010-12345678"
  },
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
  "capabilities": ["education_data", "secure_computation"]
}
```

### 3. 数据上传

#### 上传教育数据
```http
POST /api/v1/edu-data/data/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

Form Fields:
- file: (binary) 数据文件（CSV/Excel/JSON格式）
- metadata: (JSON) 文件元数据
```

**metadata示例**:
```json
{
  "source_id": "school_001",
  "data_type": "academic_performance",
  "academic_year": "2023-2024",
  "upload_time": "2026-02-28T10:00:00Z",
  "description": "高三期末考试成绩数据"
}
```

### 4. 报告生成

#### 生成STEM分析报告
```http
POST /api/v1/edu-data/reports/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "training_id": "train_20260228_12345",
  "report_type": "stem_analysis",
  "format": "pdf",
  "include_charts": true,
  "include_detailed_stats": true,
  "comparison_regions": ["beijing_001", "shanghai_001"],
  "grade_filter": ["middle", "high"]
}
```

**响应示例**:
```json
{
  "report_id": "report_20260228_67890",
  "training_id": "train_20260228_12345",
  "report_type": "stem_analysis",
  "format": "pdf",
  "file_path": "./reports/output/report_20260228_67890.pdf",
  "file_size": 2048000,
  "page_count": 25,
  "generated_at": "2026-02-28T11:00:00Z"
}
```

#### 下载报告
```http
GET /api/v1/edu-data/reports/{report_id}/download
Authorization: Bearer {token}
```

### 5. 系统监控

#### 获取系统健康状态
```http
GET /api/v1/edu-data/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "service": "Education Data Federated Learning",
  "timestamp": "2026-02-28T10:30:00Z",
  "details": {
    "coordinator": true,
    "privacy_engine": true,
    "data_services": true,
    "active_trainings": 3,
    "registered_nodes": 15,
    "online_nodes": 12
  }
}
```

#### 获取系统统计信息
```http
GET /api/v1/edu-data/statistics
Authorization: Bearer {token}
```

## 数据格式规范

### 学生学术表现数据格式
```csv
student_id,subject,score,date_taken,academic_year,percentile_rank
S001,math,85.5,2024-01-15,2023-2024,87.5
S002,science,92.0,2024-01-15,2023-2024,92.0
S003,technology,78.5,2024-01-15,2023-2024,72.3
```

### 学生人口统计数据格式
```json
[
  {
    "student_id": "S001",
    "age": 16,
    "gender": "male",
    "grade_level": "high",
    "school_id": "school_001",
    "region_id": "beijing_001"
  },
  {
    "student_id": "S002",
    "age": 15,
    "gender": "female",
    "grade_level": "middle",
    "school_id": "school_001",
    "region_id": "beijing_001"
  }
]
```

### 学校信息数据格式
```excel
school_id,school_name,school_type,district_id,region_id,enrollment,teachers_count
school_001,北京市第一中学,public,district_001,beijing_001,1200,85
school_002,上海市实验学校,public,district_002,shanghai_001,980,68
```

## 错误处理

### 标准错误响应格式
```json
{
  "code": 400,
  "message": "Bad Request",
  "error": "Invalid training configuration",
  "details": {
    "field": "participants",
    "reason": "at least 3 participants required"
  },
  "timestamp": "2026-02-28T10:30:00Z"
}
```

### 常见错误码
| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式和必填字段 |
| 401 | 未授权访问 | 检查认证令牌是否有效 |
| 403 | 权限不足 | 确认用户具有相应权限 |
| 404 | 资源不存在 | 检查资源ID是否正确 |
| 429 | 请求过于频繁 | 降低请求频率或申请更高限额 |
| 500 | 服务器内部错误 | 联系技术支持 |

### 重试策略
```python
import time
import requests

def api_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code in [429, 500, 502, 503, 504]:
                # 指数退避重试
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)
```

## 使用示例

### Python客户端示例
```python
import requests
import json
from datetime import datetime

class EduFedLearningClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def start_training(self, config):
        """启动联邦学习训练"""
        url = f"{self.base_url}/trainings/"
        response = requests.post(url, headers=self.headers, json=config)
        response.raise_for_status()
        return response.json()
    
    def upload_data(self, file_path, metadata):
        """上传教育数据"""
        url = f"{self.base_url}/data/upload"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'metadata': json.dumps(metadata)}
            response = requests.post(url, headers=self.headers, files=files, data=data)
        
        response.raise_for_status()
        return response.json()
    
    def generate_report(self, training_id, report_type='stem_analysis'):
        """生成分析报告"""
        url = f"{self.base_url}/reports/generate"
        payload = {
            'training_id': training_id,
            'report_type': report_type,
            'format': 'pdf',
            'include_charts': True
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

# 使用示例
client = EduFedLearningClient(
    'https://api.imato.edu.cn/api/v1/edu-data',
    'your_api_key_here'
)

# 启动训练
training_config = {
    'model_name': 'stem_analyzer',
    'rounds': 10,
    'participants': ['school_001', 'school_002', 'school_003'],
    'subjects': ['math', 'science'],
    'privacy_budget': 1.0
}

result = client.start_training(training_config)
print(f"训练ID: {result['training_id']}")

# 上传数据
metadata = {
    'source_id': 'school_001',
    'data_type': 'academic_performance',
    'academic_year': '2023-2024'
}

upload_result = client.upload_data('student_scores.csv', metadata)
print(f"数据批次ID: {upload_result['batch_id']}")
```

### JavaScript/Node.js示例
```javascript
const axios = require('axios');

class EduFedLearningClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async startTraining(config) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/trainings/`,
                config,
                { headers: this.headers }
            );
            return response.data;
        } catch (error) {
            throw new Error(`API Error: ${error.response?.data?.message || error.message}`);
        }
    }
    
    async getTrainingStatus(trainingId) {
        try {
            const response = await axios.get(
                `${this.baseUrl}/trainings/${trainingId}`,
                { headers: this.headers }
            );
            return response.data;
        } catch (error) {
            throw new Error(`API Error: ${error.response?.data?.message || error.message}`);
        }
    }
}

// 使用示例
async function main() {
    const client = new EduFedLearningClient(
        'https://api.imato.edu.cn/api/v1/edu-data',
        'your_api_key'
    );
    
    try {
        const config = {
            model_name: 'stem_analyzer',
            rounds: 15,
            participants: ['school_001', 'school_002'],
            subjects: ['math', 'science'],
            privacy_budget: 1.0
        };
        
        const result = await client.startTraining(config);
        console.log('训练已启动:', result.training_id);
        
        // 轮询训练状态
        const interval = setInterval(async () => {
            try {
                const status = await client.getTrainingStatus(result.training_id);
                console.log(`进度: ${status.progress_percentage}%`);
                
                if (status.status === 'completed') {
                    clearInterval(interval);
                    console.log('训练完成!');
                }
            } catch (error) {
                console.error('状态查询失败:', error.message);
            }
        }, 30000); // 每30秒查询一次
        
    } catch (error) {
        console.error('操作失败:', error.message);
    }
}

main();
```

## 最佳实践

### 1. 性能优化建议
- 批量上传数据而非逐条上传
- 合理设置训练轮数和批次大小
- 使用连接池减少HTTP连接开销
- 缓存频繁查询的结果

### 2. 安全最佳实践
- 定期轮换API密钥
- 使用HTTPS加密传输
- 验证所有输入数据
- 实施适当的访问控制

### 3. 错误处理建议
- 实现重试机制处理临时故障
- 记录详细的错误日志
- 优雅处理API限流
- 提供用户友好的错误信息

### 4. 监控和运维
- 监控API调用频率和响应时间
- 设置告警阈值
- 定期检查系统健康状态
- 维护API使用文档的及时更新

### 5. 数据质量管理
- 验证数据格式和完整性
- 处理缺失值和异常值
- 定期清理过期数据
- 建立数据质量评估机制

---

**技术支持联系方式**:
- 技术支持邮箱: tech-support@imato.edu.cn
- API文档更新: https://docs.imato.edu.cn/api
- 问题反馈: https://support.imato.edu.cn/tickets
