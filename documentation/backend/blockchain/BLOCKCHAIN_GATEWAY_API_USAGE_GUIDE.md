# 区块链网关API使用指南

## 快速开始

### 1. 环境准备

确保已安装必要的依赖：
```bash
pip install fastapi uvicorn pydantic python-jose[cryptography] pytest
```

### 2. 服务启动

```bash
cd backend
python main.py
# 或
uvicorn main:app --reload
```

服务启动后，API文档可在以下地址访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API调用示例

### Python客户端示例

```python
import requests
import json
from datetime import datetime

class BlockchainGatewayClient:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def set_token(self, token):
        """设置认证令牌"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
    
    def health_check(self):
        """健康检查"""
        response = requests.get(f"{self.base_url}/api/v1/blockchain/health")
        return response.json()
    
    def issue_integral(self, student_id, amount, description=None):
        """发行积分"""
        data = {
            "student_id": student_id,
            "amount": amount
        }
        if description:
            data["description"] = description
            
        response = requests.post(
            f"{self.base_url}/api/v1/blockchain/issue-integral",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_student_balance(self, student_id):
        """查询学生余额"""
        response = requests.get(
            f"{self.base_url}/api/v1/blockchain/students/{student_id}/balance",
            headers=self.headers
        )
        return response.json()
    
    def get_transaction_history(self, student_id=None, limit=50, offset=0):
        """查询交易历史"""
        params = {"limit": limit, "offset": offset}
        if student_id:
            params["student_id"] = student_id
            
        response = requests.get(
            f"{self.base_url}/api/v1/blockchain/transactions/history",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def oauth_token_exchange(self, client_id, client_secret, scope="read"):
        """OAuth2令牌交换"""
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/blockchain/oauth/token",
            json=data
        )
        return response.json()

# 使用示例
if __name__ == "__main__":
    # 初始化客户端
    client = BlockchainGatewayClient()
    
    # 1. 健康检查
    health = client.health_check()
    print("健康检查:", health)
    
    # 2. 获取OAuth2令牌
    token_response = client.oauth_token_exchange(
        client_id="education_portal",
        client_secret="edu_portal_secret",
        scope="blockchain:read blockchain:write"
    )
    
    if "access_token" in token_response:
        client.set_token(token_response["access_token"])
        print("认证成功")
    
    # 3. 发行积分
    issue_result = client.issue_integral(
        student_id="student_001",
        amount=100,
        description="学习奖励积分"
    )
    print("积分发行结果:", issue_result)
    
    # 4. 查询余额
    balance = client.get_student_balance("student_001")
    print("学生余额:", balance)
    
    # 5. 查询交易历史
    history = client.get_transaction_history(limit=10)
    print("交易历史:", history)
```

### JavaScript/TypeScript客户端示例

```typescript
class BlockchainGatewayClient {
    private baseUrl: string;
    private token: string | null;

    constructor(baseUrl: string = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
    }

    setToken(token: string): void {
        this.token = token;
    }

    private async request(endpoint: string, options: RequestInit = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    async healthCheck() {
        return await this.request('/api/v1/blockchain/health');
    }

    async issueIntegral(studentId: string, amount: number, description?: string) {
        return await this.request('/api/v1/blockchain/issue-integral', {
            method: 'POST',
            body: JSON.stringify({ student_id: studentId, amount, description })
        });
    }

    async getStudentBalance(studentId: string) {
        return await this.request(`/api/v1/blockchain/students/${studentId}/balance`);
    }

    async getTransactionHistory(studentId?: string, limit: number = 50, offset: number = 0) {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString()
        });
        
        if (studentId) {
            params.append('student_id', studentId);
        }

        return await this.request(`/api/v1/blockchain/transactions/history?${params}`);
    }

    async oauthTokenExchange(clientId: string, clientSecret: string, scope: string = 'read') {
        return await this.request('/api/v1/blockchain/oauth/token', {
            method: 'POST',
            body: JSON.stringify({
                grant_type: 'client_credentials',
                client_id: clientId,
                client_secret: clientSecret,
                scope
            })
        });
    }
}

// 使用示例
async function main() {
    const client = new BlockchainGatewayClient();
    
    try {
        // 健康检查
        const health = await client.healthCheck();
        console.log('健康检查:', health);
        
        // 获取令牌
        const tokenResponse = await client.oauthTokenExchange(
            'education_portal',
            'edu_portal_secret',
            'blockchain:read blockchain:write'
        );
        
        client.setToken(tokenResponse.access_token);
        console.log('认证成功');
        
        // 发行积分
        const issueResult = await client.issueIntegral(
            'student_001',
            100,
            '学习奖励积分'
        );
        console.log('积分发行结果:', issueResult);
        
        // 查询余额
        const balance = await client.getStudentBalance('student_001');
        console.log('学生余额:', balance);
        
    } catch (error) {
        console.error('API调用失败:', error);
    }
}

main();
```

### cURL命令示例

```bash
# 健康检查
curl -X GET "http://localhost:8000/api/v1/blockchain/health"

# OAuth2令牌交换
curl -X POST "http://localhost:8000/api/v1/blockchain/oauth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "education_portal",
    "client_secret": "edu_portal_secret",
    "scope": "blockchain:read blockchain:write"
  }'

# 设置令牌变量
export TOKEN="your_access_token_here"

# 发行积分
curl -X POST "http://localhost:8000/api/v1/blockchain/issue-integral" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_001",
    "amount": 100,
    "description": "学习奖励积分"
  }'

# 查询学生余额
curl -X GET "http://localhost:8000/api/v1/blockchain/students/student_001/balance" \
  -H "Authorization: Bearer $TOKEN"

# 查询交易历史
curl -X GET "http://localhost:8000/api/v1/blockchain/transactions/history?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```

## 错误处理

### 常见HTTP状态码

| 状态码 | 含义 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求参数错误 | 检查请求参数格式 |
| 401 | 未认证 | 提供有效的JWT令牌 |
| 403 | 权限不足 | 检查用户角色和权限 |
| 422 | 参数验证失败 | 检查必填字段和数据格式 |
| 429 | 请求过于频繁 | 降低请求频率 |
| 500 | 服务器内部错误 | 查看服务日志 |
| 503 | 服务不可用 | 等待服务恢复或检查熔断器状态 |

### 错误响应格式

```json
{
  "detail": "具体的错误信息"
}
```

### 客户端错误处理示例

```python
import requests
from requests.exceptions import RequestException

def safe_api_call(func):
    """API调用装饰器，处理常见错误"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print("网络连接错误，请检查服务是否运行")
        except requests.exceptions.Timeout:
            print("请求超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
        except Exception as e:
            print(f"未知错误: {e}")
        return None
    return wrapper

class SafeBlockchainClient(BlockchainGatewayClient):
    @safe_api_call
    def issue_integral(self, student_id, amount, description=None):
        return super().issue_integral(student_id, amount, description)
    
    @safe_api_call
    def get_student_balance(self, student_id):
        return super().get_student_balance(student_id)

# 使用安全客户端
safe_client = SafeBlockchainClient()
result = safe_client.issue_integral("student_001", 100)
if result is None:
    print("API调用失败，使用降级逻辑")
```

## 性能优化建议

### 1. 连接复用

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OptimizedBlockchainClient(BlockchainGatewayClient):
    def __init__(self, base_url="http://localhost:8000", token=None):
        super().__init__(base_url, token)
        
        # 配置连接池
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()
```

### 2. 批量操作

```python
def batch_issue_integrals(self, student_amounts, description=None):
    """批量发行积分"""
    results = []
    for student_id, amount in student_amounts:
        try:
            result = self.issue_integral(student_id, amount, description)
            results.append({"student_id": student_id, "success": True, "result": result})
        except Exception as e:
            results.append({"student_id": student_id, "success": False, "error": str(e)})
    return results
```

### 3. 异步调用

```python
import asyncio
import aiohttp

class AsyncBlockchainClient:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    async def issue_integral_async(self, student_id, amount, description=None):
        data = {"student_id": student_id, "amount": amount}
        if description:
            data["description"] = description
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/blockchain/issue-integral",
                headers=self.headers,
                json=data
            ) as response:
                return await response.json()
    
    async def batch_issue_async(self, student_amounts):
        """异步批量发行"""
        tasks = [
            self.issue_integral_async(sid, amount) 
            for sid, amount in student_amounts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

## 监控与调试

### 1. 请求日志

```python
import logging
import time

class LoggingBlockchainClient(BlockchainGatewayClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    def issue_integral(self, student_id, amount, description=None):
        start_time = time.time()
        self.logger.info(f"开始发行积分 - 学生: {student_id}, 数量: {amount}")
        
        try:
            result = super().issue_integral(student_id, amount, description)
            duration = time.time() - start_time
            self.logger.info(f"积分发行成功 - 耗时: {duration:.2f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"积分发行失败 - 耗时: {duration:.2f}秒, 错误: {e}")
            raise
```

### 2. 性能监控

```python
from collections import defaultdict
import statistics

class MonitoringBlockchainClient(BlockchainGatewayClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = defaultdict(list)
    
    def issue_integral(self, student_id, amount, description=None):
        start_time = time.time()
        
        result = super().issue_integral(student_id, amount, description)
        
        duration = time.time() - start_time
        self.metrics['issue_integral'].append(duration)
        
        return result
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        stats = {}
        for operation, durations in self.metrics.items():
            if durations:
                stats[operation] = {
                    'count': len(durations),
                    'avg_time': statistics.mean(durations),
                    'min_time': min(durations),
                    'max_time': max(durations),
                    'p95_time': sorted(durations)[int(len(durations) * 0.95)]
                }
        return stats
```

这个API使用指南提供了完整的客户端实现示例，包括Python、JavaScript/TypeScript和cURL命令，涵盖了认证、错误处理、性能优化等各个方面。