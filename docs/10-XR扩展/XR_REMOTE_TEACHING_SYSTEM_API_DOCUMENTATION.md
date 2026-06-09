# XR远程教学系统API文档

## 概述

本文档详细描述了XR远程教学系统的RESTful API接口，包括AR手势识别、VR代码编辑器和白板协作三大核心模块的接口规范。

## 基础信息

- **API版本**: v1
- **基础URL**: `/api/v1/xr`
- **认证方式**: JWT Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

所有API请求都需要在HTTP头部包含有效的JWT Token:

```
Authorization: Bearer <your-jwt-token>
```

## 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

HTTP状态码:
- 200: 成功
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## 1. AR手势识别API

### 1.1 启动手势识别会话

```
POST /api/v1/xr/gesture/sessions/start
```

**请求体:**
```json
{
  "user_id": 123,
  "device_id": "ar_glasses_001",
  "config": {
    "min_detection_confidence": 0.7,
    "gesture_timeout": 2.0,
    "continuous_gesture_threshold": 3
  }
}
```

**响应:**
```json
{
  "session_id": "uuid-string",
  "message": "手势识别会话已启动",
  "status": "running"
}
```

### 1.2 停止手势识别会话

```
POST /api/v1/xr/gesture/sessions/{session_id}/stop
```

**响应:**
```json
{
  "session_id": "uuid-string",
  "message": "手势识别会话已停止",
  "status": "stopped"
}
```

### 1.3 获取会话信息

```
GET /api/v1/xr/gesture/sessions/{session_id}/info
```

**响应:**
```json
{
  "session_id": "uuid-string",
  "user_id": 123,
  "device_id": "ar_glasses_001",
  "start_time": "2026-02-27T10:30:00Z",
  "is_active": true,
  "statistics": {
    "total_gestures": 45,
    "gesture_counts": {
      "circle": 12,
      "swipe_right": 8,
      "fist": 15
    },
    "average_confidence": 0.85
  }
}
```

### 1.4 获取可用命令列表

```
GET /api/v1/xr/gesture/commands
```

**响应:**
```json
[
  {
    "gesture_type": "circle",
    "command": "save_project",
    "description": "保存当前项目",
    "priority": 10
  },
  {
    "gesture_type": "swipe_right",
    "command": "next_step",
    "description": "进入下一步",
    "priority": 8
  }
]
```

### 1.5 更新手势命令映射

```
PUT /api/v1/xr/gesture/commands/{gesture_type}
```

**请求体:**
```json
{
  "command": "new_save_command",
  "description": "新的保存命令",
  "enabled": true,
  "priority": 9
}
```

**响应:**
```json
{
  "gesture_type": "circle",
  "updated_sessions": ["session1", "session2"],
  "message": "手势命令映射已更新，影响 2 个会话"
}
```

### 1.6 WebSocket实时连接

```
WebSocket /api/v1/xr/gesture/ws/{session_id}
```

**客户端发送:**
```json
{
  "type": "get_state",
  "timestamp": "2026-02-27T10:30:00Z"
}
```

**服务器推送:**
```json
{
  "type": "gesture_event",
  "event": {
    "event_id": "event_uuid",
    "gesture_result": {
      "gesture_type": "circle",
      "confidence": 0.92,
      "hand_side": "right"
    },
    "mapped_command": "save_project"
  },
  "timestamp": "2026-02-27T10:30:01Z"
}
```

## 2. VR代码编辑器API

### 2.1 启动编辑器会话

```
POST /api/v1/xr/vr-editor/sessions/start
```

**请求体:**
```json
{
  "user_id": 123,
  "device_id": "vr_headset_001",
  "config": {
    "theme": "dark",
    "language": "python",
    "font_size": 16,
    "interaction_mode": "hand_tracking"
  }
}
```

**响应:**
```json
{
  "session_id": "editor-session-uuid",
  "message": "VR代码编辑器会话已启动",
  "supported_languages": ["python", "javascript", "java", "cpp"]
}
```

### 2.2 打开文件

```
POST /api/v1/xr/vr-editor/sessions/{session_id}/files/open
```

**请求体:**
```json
{
  "file_path": "/projects/hello.py",
  "content": "print('Hello XR World!')",
  "language": "python"
}
```

**响应:**
```json
{
  "file_id": "file-uuid",
  "message": "文件已打开: /projects/hello.py"
}
```

### 2.3 更新文件内容

```
POST /api/v1/xr/vr-editor/sessions/{session_id}/files/update
```

**请求体:**
```json
{
  "file_id": "file-uuid",
  "content": "def main():\n    print('Updated content')",
  "cursor_line": 2,
  "cursor_column": 10
}
```

**响应:**
```json
{
  "message": "文件内容已更新"
}
```

### 2.4 获取已打开文件列表

```
GET /api/v1/xr/vr-editor/sessions/{session_id}/files
```

**响应:**
```json
[
  {
    "id": "file-uuid",
    "name": "hello.py",
    "path": "/projects/hello.py",
    "language": "python",
    "size": 1024,
    "modified_at": "2026-02-27T10:30:00Z",
    "is_active": true
  }
]
```

### 2.5 移动光标

```
POST /api/v1/xr/vr-editor/sessions/{session_id}/cursor/move
```

**请求体:**
```json
{
  "line": 5,
  "column": 12
}
```

**响应:**
```json
{
  "message": "光标位置已更新"
}
```

### 2.6 更新VR状态

```
POST /api/v1/xr/vr-editor/sessions/{session_id}/vr-state/update
```

**请求体:**
```json
{
  "head_position": {"x": 0.5, "y": 1.6, "z": -2.0},
  "head_rotation": {"x": 0, "y": 45, "z": 0},
  "left_controller": {
    "position": {"x": -0.3, "y": 1.2, "z": -1.5},
    "buttons": {"trigger": true}
  }
}
```

**响应:**
```json
{
  "message": "VR状态已更新"
}
```

### 2.7 WebSocket连接

```
WebSocket /api/v1/xr/vr-editor/ws/{session_id}
```

**服务器推送事件:**
```json
{
  "type": "state_update",
  "state": {
    "cursor_position": {"line": 3, "column": 15},
    "zoom_level": 1.2
  },
  "timestamp": "2026-02-27T10:30:00Z"
}
```

## 3. 白板协作API

### 3.1 创建白板会话

```
POST /api/v1/xr/whiteboard/create
```

**请求体:**
```json
{
  "owner_id": 123,
  "board_name": "数学教学白板",
  "config": {
    "canvas_width": 1920,
    "canvas_height": 1080,
    "real_time_sync": true
  }
}
```

**响应:**
```json
{
  "session_id": "whiteboard-session-uuid",
  "message": "白板会话创建成功",
  "board_name": "数学教学白板",
  "owner_id": 123
}
```

### 3.2 加入白板会话

```
POST /api/v1/xr/whiteboard/{session_id}/join
```

**请求体:**
```json
{
  "user_id": 456
}
```

**响应:**
```json
{
  "session_id": "whiteboard-session-uuid",
  "user_id": 456,
  "message": "成功加入白板会话"
}
```

### 3.3 开始绘制笔画

```
POST /api/v1/xr/whiteboard/{session_id}/strokes/start
```

**请求体:**
```json
{
  "x": 100.5,
  "y": 200.3,
  "pressure": 0.8,
  "stroke_type": "pen",
  "color": "#FF0000",
  "width": 3.0,
  "user_id": 123
}
```

**响应:**
```json
{
  "stroke_id": "stroke-uuid",
  "message": "笔画开始绘制"
}
```

### 3.4 添加笔画点

```
POST /api/v1/xr/whiteboard/{session_id}/strokes/add-point
```

**请求体:**
```json
{
  "x": 150.2,
  "y": 220.1,
  "pressure": 0.7
}
```

**响应:**
```json
{
  "message": "笔画点已添加"
}
```

### 3.5 结束绘制笔画

```
POST /api/v1/xr/whiteboard/{session_id}/strokes/end
```

**响应:**
```json
{
  "element_id": "element-uuid",
  "message": "笔画绘制完成"
}
```

### 3.6 添加形状

```
POST /api/v1/xr/whiteboard/{session_id}/shapes/add
```

**请求体:**
```json
{
  "shape_type": "rectangle",
  "start_x": 100,
  "start_y": 100,
  "end_x": 300,
  "end_y": 200,
  "user_id": 123
}
```

**响应:**
```json
{
  "shape_id": "shape-uuid",
  "message": "形状已添加"
}
```

### 3.7 添加文本

```
POST /api/v1/xr/whiteboard/{session_id}/text/add
```

**请求体:**
```json
{
  "x": 200,
  "y": 150,
  "content": "重要公式：E=mc²",
  "user_id": 123
}
```

**响应:**
```json
{
  "text_id": "text-uuid",
  "message": "文本已添加"
}
```

### 3.8 修改元素

```
PUT /api/v1/xr/whiteboard/{session_id}/elements/{element_id}
```

**请求体:**
```json
{
  "updates": {
    "color": "#00FF00",
    "width": 5.0
  }
}
```

**响应:**
```json
{
  "message": "元素修改成功"
}
```

### 3.9 删除元素

```
DELETE /api/v1/xr/whiteboard/{session_id}/elements/{element_id}
```

**响应:**
```json
{
  "message": "元素删除成功"
}
```

### 3.10 获取页面元素

```
GET /api/v1/xr/whiteboard/{session_id}/elements?page_number=0
```

**响应:**
```json
[
  {
    "id": "element-uuid",
    "element_type": "stroke",
    "data": {
      "stroke_type": "pen",
      "color": "#FF0000",
      "points": [
        {"x": 100, "y": 200, "pressure": 0.8},
        {"x": 150, "y": 220, "pressure": 0.7}
      ]
    },
    "user_id": 123,
    "created_at": "2026-02-27T10:30:00Z"
  }
]
```

### 3.11 添加新页面

```
POST /api/v1/xr/whiteboard/{session_id}/pages/add
```

**响应:**
```json
{
  "page_number": 1,
  "message": "新页面已添加"
}
```

### 3.12 切换页面

```
POST /api/v1/xr/whiteboard/{session_id}/pages/switch
```

**请求体:**
```json
{
  "page_number": 1
}
```

**响应:**
```json
{
  "page_number": 1,
  "message": "页面切换成功"
}
```

### 3.13 获取白板信息

```
GET /api/v1/xr/whiteboard/{session_id}/info
```

**响应:**
```json
{
  "session_id": "whiteboard-session-uuid",
  "board_name": "数学教学白板",
  "owner_id": 123,
  "participants": [123, 456, 789],
  "current_page": 0,
  "total_pages": 3,
  "is_active": true,
  "created_at": "2026-02-27T09:00:00Z",
  "last_activity": "2026-02-27T10:30:00Z"
}
```

### 3.14 关闭白板会话

```
POST /api/v1/xr/whiteboard/{session_id}/close
```

**响应:**
```json
{
  "session_id": "whiteboard-session-uuid",
  "message": "白板会话已关闭"
}
```

### 3.15 WebSocket协作连接

```
WebSocket /api/v1/xr/whiteboard/ws/{session_id}
```

**服务器推送事件:**
```json
{
  "type": "element_added",
  "element": {
    "id": "new-element-uuid",
    "element_type": "text",
    "data": {
      "content": "协作添加的文本",
      "position": {"x": 100, "y": 100}
    }
  },
  "timestamp": "2026-02-27T10:30:00Z"
}
```

## 4. 系统管理API

### 4.1 健康检查

```
GET /api/v1/xr/health
```

**响应:**
```json
{
  "status": "healthy",
  "service": "xr_remote_teaching_system",
  "active_sessions": {
    "gesture": 15,
    "editor": 8,
    "whiteboard": 12
  },
  "timestamp": "2026-02-27T10:30:00Z"
}
```

### 4.2 系统统计

```
GET /api/v1/xr/stats
```

**响应:**
```json
{
  "total_users": 1250,
  "active_sessions": 35,
  "total_elements_created": 15420,
  "average_session_duration": 45.5,
  "system_uptime": "7 days, 14:30:22",
  "timestamp": "2026-02-27T10:30:00Z"
}
```

## 5. WebSocket事件类型

### 5.1 通用事件格式

```json
{
  "type": "event_type",
  "data": {...},
  "timestamp": "ISO8601 timestamp"
}
```

### 5.2 主要事件类型

| 事件类型 | 模块 | 描述 |
|---------|------|------|
| `gesture_event` | 手势识别 | 手势识别事件 |
| `state_update` | VR编辑器 | 状态更新事件 |
| `element_added` | 白板协作 | 元素添加事件 |
| `element_modified` | 白板协作 | 元素修改事件 |
| `element_removed` | 白板协作 | 元素删除事件 |
| `user_joined` | 白板协作 | 用户加入事件 |
| `cursor_update` | 白板协作 | 光标更新事件 |

## 6. 错误处理

### 6.1 标准错误响应

```json
{
  "detail": "具体的错误信息"
}
```

### 6.2 常见错误码

| HTTP状态码 | 错误类型 | 描述 |
|-----------|----------|------|
| 400 | BadRequest | 请求参数错误 |
| 401 | Unauthorized | 未认证或Token过期 |
| 403 | Forbidden | 权限不足 |
| 404 | NotFound | 资源不存在 |
| 409 | Conflict | 资源冲突 |
| 500 | InternalServerError | 服务器内部错误 |
| 503 | ServiceUnavailable | 服务暂时不可用 |

### 6.3 重试策略

```javascript
const retryConfig = {
  maxRetries: 3,
  retryDelay: 1000, // 1秒
  exponentialBackoff: true,
  retryOn: [500, 502, 503, 504]
};
```

## 7. 客户端SDK示例

### 7.1 JavaScript客户端

```javascript
class XRClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async request(endpoint, method = 'GET', data = null) {
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };

    const config = {
      method,
      headers
    };

    if (data) {
      config.body = JSON.stringify(data);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    return await response.json();
  }

  // 手势识别相关方法
  async startGestureSession(userId, deviceId) {
    return this.request('/gesture/sessions/start', 'POST', {
      user_id: userId,
      device_id: deviceId
    });
  }

  // VR编辑器相关方法
  async startEditorSession(userId, deviceId) {
    return this.request('/vr-editor/sessions/start', 'POST', {
      user_id: userId,
      device_id: deviceId
    });
  }

  // 白板协作相关方法
  async createWhiteboard(ownerId, boardName) {
    return this.request('/whiteboard/create', 'POST', {
      owner_id: ownerId,
      board_name: boardName
    });
  }
}

// 使用示例
const client = new XRClient('https://api.imatu.com/api/v1/xr', 'your-jwt-token');

// 启动手势识别
client.startGestureSession(123, 'ar_glasses_001')
  .then(response => console.log('手势会话:', response.session_id))
  .catch(error => console.error('错误:', error));
```

### 7.2 Python客户端

```python
import requests
import json
from typing import Dict, Any

class XRClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _request(self, endpoint: str, method: str = 'GET', 
                 data: Dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        response = requests.request(
            method, url, 
            headers=self.headers,
            json=data if data else None
        )
        
        response.raise_for_status()
        return response.json()

    # 手势识别方法
    def start_gesture_session(self, user_id: int, device_id: str) -> Dict:
        return self._request('/gesture/sessions/start', 'POST', {
            'user_id': user_id,
            'device_id': device_id
        })

    # VR编辑器方法
    def start_editor_session(self, user_id: int, device_id: str) -> Dict:
        return self._request('/vr-editor/sessions/start', 'POST', {
            'user_id': user_id,
            'device_id': device_id
        })

    # 白板协作方法
    def create_whiteboard(self, owner_id: int, board_name: str) -> Dict:
        return self._request('/whiteboard/create', 'POST', {
            'owner_id': owner_id,
            'board_name': board_name
        })

# 使用示例
client = XRClient('https://api.imatu.com/api/v1/xr', 'your-jwt-token')

try:
    # 创建白板
    result = client.create_whiteboard(123, '教学白板')
    print(f"白板会话ID: {result['session_id']}")
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
```

## 8. 性能优化建议

### 8.1 客户端优化

1. **连接复用**: WebSocket连接尽量保持长连接
2. **批量操作**: 对于大量数据操作，使用批量API
3. **本地缓存**: 适当缓存静态数据减少请求
4. **错误重试**: 实现指数退避重试机制

### 8.2 服务端优化

1. **异步处理**: 使用异步框架提高并发处理能力
2. **数据压缩**: WebSocket传输启用压缩
3. **连接池**: 数据库连接池优化
4. **缓存策略**: 合理使用Redis缓存热点数据

## 9. 安全最佳实践

### 9.1 认证安全

- 使用HTTPS加密传输
- 定期轮换JWT密钥
- 实施Token过期和刷新机制
- 限制Token权限范围

### 9.2 数据安全

- 输入数据严格验证
- 防止SQL注入和XSS攻击
- 敏感数据加密存储
- 实施速率限制防止滥用

### 9.3 会话安全

- 会话超时机制
- 多设备登录控制
- 异常登录检测
- 会话状态隔离

---
**API版本**: v1.0  
**最后更新**: 2026年2月27日  
**维护团队**: XR技术团队