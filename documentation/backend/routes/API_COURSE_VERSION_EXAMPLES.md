# 课程版本控制API使用示例

## 快速开始

以下是一些常见的API使用场景和示例代码。

## 1. 版本管理示例

### 提交新版本

```bash
# 提交课程的第一个版本
curl -X POST "http://localhost:8000/api/v1/org/1/courses/1/versions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "commit_message": "Initial commit: 创建基础课程结构",
    "branch_name": "main",
    "course_data": {
      "title": "Python编程入门",
      "description": "面向初学者的Python编程课程",
      "chapters": [
        {
          "id": 1,
          "title": "Python基础语法",
          "lessons": [
            {"id": 1, "title": "变量和数据类型"},
            {"id": 2, "title": "运算符和表达式"}
          ]
        }
      ],
      "metadata": {
        "created_by": "teacher@example.com",
        "created_at": "2024-01-15T10:00:00",
        "last_modified": "2024-01-15T10:00:00"
      }
    }
  }'
```

### 获取版本历史

```bash
# 获取指定课程的所有版本
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/versions?limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取指定分支的版本历史
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/versions?branch=main&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 查看特定版本内容

```bash
# 获取特定版本的完整课程内容
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/versions/a1b2c3d4e5f6/content" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 2. 分支管理示例

### 创建新分支

```bash
# 基于main分支创建功能分支
curl -X POST "http://localhost:8000/api/v1/org/1/courses/1/branches" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "feature/advanced-topics",
    "description": "开发高级Python主题内容"
  }'
```

### 列出所有分支

```bash
# 查看课程的所有分支
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/branches" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 在分支上提交更改

```bash
# 切换到功能分支并提交新内容
curl -X POST "http://localhost:8000/api/v1/org/1/courses/1/versions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": 1,
    "commit_message": "Add OOP chapter",
    "branch_name": "feature/advanced-topics",
    "course_data": {
      "title": "Python编程入门",
      "chapters": [
        {
          "id": 1,
          "title": "Python基础语法"
        },
        {
          "id": 2,
          "title": "面向对象编程",
          "lessons": [
            {"id": 3, "title": "类和对象"},
            {"id": 4, "title": "继承和多态"}
          ]
        }
      ]
    }
  }'
```

## 3. 合并管理示例

### 创建合并请求

```bash
# 从功能分支向主分支创建合并请求
curl -X POST "http://localhost:8000/api/v1/org/1/courses/1/merge-requests" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_branch": "feature/advanced-topics",
    "target_branch": "main",
    "title": "合并高级主题内容到主分支",
    "description": "添加了面向对象编程和异常处理两个重要章节"
  }'
```

### 检查合并冲突

```bash
# 检查合并请求是否存在冲突
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/merge-requests/1/conflicts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 执行合并

```bash
# 执行合并操作
curl -X POST "http://localhost:8000/api/v1/org/1/courses/1/merge-requests/1/merge" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 查看合并请求列表

```bash
# 查看所有合并请求
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/merge-requests" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查看开放的合并请求
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/merge-requests?status=open" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. 版本对比示例

### 比较两个版本的差异

```bash
# 比较版本之间的变化
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/compare/a1b2c3d4...e5f6g7h8" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
```json
{
  "from_version": 2,
  "to_version": 3,
  "from_commit": "a1b2c3d4e5f6",
  "to_commit": "e5f6g7h8i9j0",
  "changes": {
    "type": "update",
    "added": ["chapters.2"],
    "modified": ["description"],
    "deleted": ["chapters.0.lessons.2"]
  },
  "author": "张老师",
  "timestamp": "2024-01-15T15:30:00"
}
```

## 5. 版本回滚示例

### 回滚到指定版本

```bash
# 回滚到历史版本
curl -X POST "http://localhost:8000/api/v1/org/1/courses/1/versions/a1b2c3d4/revert" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "commit_message": "回滚到稳定版本v2"
  }'
```

## 6. 系统信息查询

### 获取版本统计信息

```bash
# 查看课程版本控制统计
curl -X GET "http://localhost:8000/api/v1/org/1/courses/1/versions/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例:**
```json
{
  "total_versions": 15,
  "total_branches": 3,
  "total_merge_requests": 8,
  "open_merge_requests": 2,
  "merged_merge_requests": 6,
  "latest_version": {
    "version_number": 15,
    "commit_hash": "a1b2c3d4",
    "timestamp": "2024-01-15T16:45:00",
    "author": "李老师"
  }
}
```

## JavaScript/前端使用示例

```javascript
class CourseVersionClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async commitVersion(courseId, orgId, versionData) {
    const response = await fetch(`${this.baseUrl}/api/v1/org/${orgId}/courses/${courseId}/versions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(versionData)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  }

  async getVersions(courseId, orgId, params = {}) {
    const queryParams = new URLSearchParams(params);
    const response = await fetch(`${this.baseUrl}/api/v1/org/${orgId}/courses/${courseId}/versions?${queryParams}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    });
    
    return await response.json();
  }

  async createBranch(courseId, orgId, branchData) {
    const response = await fetch(`${this.baseUrl}/api/v1/org/${orgId}/courses/${courseId}/branches`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(branchData)
    });
    
    return await response.json();
  }

  async createMergeRequest(courseId, orgId, mrData) {
    const response = await fetch(`${this.baseUrl}/api/v1/org/${orgId}/courses/${courseId}/merge-requests`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(mrData)
    });
    
    return await response.json();
  }
}

// 使用示例
const client = new CourseVersionClient('http://localhost:8000', 'YOUR_JWT_TOKEN');

// 提交新版本
try {
  const version = await client.commitVersion(1, 1, {
    course_id: 1,
    commit_message: "Update lesson content",
    branch_name: "main",
    course_data: {
      title: "Updated Course Title",
      lessons: [...]
    }
  });
  console.log('Version committed:', version);
} catch (error) {
  console.error('Commit failed:', error);
}
```

## Python客户端示例

```python
import requests
from typing import Dict, Any

class CourseVersionClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def commit_version(self, org_id: int, course_id: int, version_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/org/{org_id}/courses/{course_id}/versions"
        response = requests.post(url, json=version_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_versions(self, org_id: int, course_id: int, **params) -> list:
        url = f"{self.base_url}/api/v1/org/{org_id}/courses/{course_id}/versions"
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_branch(self, org_id: int, course_id: int, branch_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/org/{org_id}/courses/{course_id}/branches"
        response = requests.post(url, json=branch_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_merge_request(self, org_id: int, course_id: int, mr_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/org/{org_id}/courses/{course_id}/merge-requests"
        response = requests.post(url, json=mr_data, headers=self.headers)
        response.raise_for_status()
        return response.json()

# 使用示例
client = CourseVersionClient('http://localhost:8000', 'YOUR_JWT_TOKEN')

# 提交新版本
version_data = {
    'course_id': 1,
    'commit_message': 'Add new chapter',
    'branch_name': 'main',
    'course_data': {
        'title': 'Python Programming',
        'chapters': [{'id': 1, 'title': 'Introduction'}]
    }
}

try:
    result = client.commit_version(1, 1, version_data)
    print(f"Version committed: {result['commit_hash']}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
```

## 错误处理

### 常见错误码

- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未授权访问
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突（如分支已存在）
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式

```json
{
  "detail": "具体的错误信息"
}
```

## 最佳实践

1. **提交信息规范**: 编写清晰、有意义的提交消息
2. **分支命名**: 使用有意义的分支名称（如feature/、hotfix/、release/）
3. **及时合并**: 功能开发完成后及时创建合并请求
4. **冲突解决**: 发现冲突时及时沟通解决
5. **版本回滚**: 谨慎使用回滚功能，确保了解影响范围

---

*更多详细信息请参考 [课程版本控制系统技术文档](COURSE_VERSION_CONTROL_SYSTEM.md)*