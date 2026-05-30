# AR/VR课程集成API文档

## 概述

本文档描述了AR/VR课程集成系统的API接口，包括内容管理、传感器数据传输、物理引擎交互和学习进度跟踪等功能。

## 基础信息

- **API版本**: v1
- **基础URL**: `/api/v1/org/{org_id}/arvr`
- **认证方式**: JWT Token
- **数据格式**: JSON

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

## 数据模型

### ARVRContent (AR/VR内容)

```json
{
  "id": 1,
  "org_id": 1,
  "course_id": 1,
  "lesson_id": 1,
  "title": "Unity WebGL 3D分子模型",
  "description": "基于Unity WebGL构建的交互式3D分子结构可视化",
  "content_type": "unity_webgl",
  "platform": "web_browser",
  "build_file_url": "/arvr/builds/content_1/build/index.html",
  "manifest_url": "/arvr/builds/content_1/build/Build/content_1.json",
  "thumbnail_url": "/arvr/thumbnails/thumb_1.jpg",
  "config": {
    "width": 800,
    "height": 600,
    "backgroundColor": "#000000"
  },
  "required_sensors": ["touch"],
  "interaction_modes": ["gesture", "controller"],
  "file_size": 15728640,
  "estimated_load_time": 3.5,
  "is_active": true,
  "is_public": true,
  "access_level": "lesson",
  "view_count": 150,
  "completion_count": 85,
  "average_rating": 4.5,
  "is_featured": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### SensorData (传感器数据)

```json
{
  "id": 1,
  "content_id": 1,
  "user_id": 1,
  "org_id": 1,
  "sensor_type": "accelerometer",
  "data_payload": {
    "x": 0.5,
    "y": -0.2,
    "z": 9.8,
    "timestamp": 1642235400000
  },
  "captured_at": "2024-01-15T10:30:00Z",
  "session_id": "session_123456789",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "altitude": 43.5
}
```

### ProgressTracking (进度跟踪)

```json
{
  "id": 1,
  "content_id": 1,
  "user_id": 1,
  "org_id": 1,
  "progress_percentage": 75.0,
  "current_state": {
    "current_molecule": "H2O",
    "view_mode": "wireframe"
  },
  "milestones_reached": ["water_molecule_loaded", "bond_angles_measured"],
  "started_at": "2024-01-15T09:00:00Z",
  "last_accessed_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "time_spent": 15.5,
  "interaction_count": 42,
  "assessment_score": 85.0
}
```

## API接口

### 1. 内容管理

#### 创建AR/VR内容

```
POST /api/v1/org/{org_id}/arvr/contents
```

**请求体:**
```json
{
  "course_id": 1,
  "lesson_id": 1,
  "title": "Unity WebGL 3D分子模型",
  "description": "交互式3D分子结构可视化",
  "content_type": "unity_webgl",
  "platform": "web_browser",
  "config": {
    "width": 800,
    "height": 600
  },
  "required_sensors": ["touch"],
  "interaction_modes": ["gesture", "controller"],
  "is_public": true,
  "access_level": "lesson"
}
```

**响应:**
返回创建的ARVRContent对象

#### 获取内容列表

```
GET /api/v1/org/{org_id}/arvr/contents
```

**查询参数:**
- `course_id` (可选): 课程ID
- `lesson_id` (可选): 课时ID
- `content_type` (可选): 内容类型 (unity_webgl, threejs_scene, model_viewer, interactive_demo, virtual_lab, ar_marker)
- `platform` (可选): 平台类型 (web_browser, mobile_ar, vr_headset, desktop_vr)

**响应:**
返回ARVRContent对象数组

#### 获取内容详情

```
GET /api/v1/org/{org_id}/arvr/contents/{content_id}
```

**响应:**
返回指定ID的ARVRContent对象

#### 更新内容

```
PUT /api/v1/org/{org_id}/arvr/contents/{content_id}
```

**请求体:**
```json
{
  "title": "更新后的标题",
  "description": "更新后的描述",
  "is_active": true
}
```

#### 删除内容

```
DELETE /api/v1/org/{org_id}/arvr/contents/{content_id}
```

#### 上传Unity构建文件

```
POST /api/v1/org/{org_id}/arvr/contents/{content_id}/upload-build
```

**表单数据:**
- `build_file`: Unity WebGL构建文件 (ZIP格式)
- `thumbnail_file` (可选): 缩略图文件

### 2. 传感器数据

#### 创建传感器数据记录

```
POST /api/v1/org/{org_id}/arvr/contents/{content_id}/sensor-data
```

**请求体:**
```json
{
  "sensor_type": "accelerometer",
  "data_payload": {
    "x": 0.5,
    "y": -0.2,
    "z": 9.8
  },
  "session_id": "session_123456789",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "altitude": 43.5
}
```

#### 获取传感器数据列表

```
GET /api/v1/org/{org_id}/arvr/contents/{content_id}/sensor-data
```

**查询参数:**
- `sensor_type` (可选): 传感器类型
- `session_id` (可选): 会话ID
- `limit` (可选): 返回记录数限制，默认100，最大1000

### 3. 交互日志

#### 记录交互日志

```
POST /api/v1/org/{org_id}/arvr/contents/{content_id}/interactions
```

**请求体:**
```json
{
  "interaction_type": "tap",
  "interaction_data": {
    "position": [0.5, 0.3],
    "object_id": "molecule_H2O"
  },
  "interaction_mode": "gesture",
  "success": true,
  "response_time": 150.5,
  "feedback_score": 4.5,
  "session_id": "session_123456789",
  "duration": 2.3
}
```

### 4. 进度跟踪

#### 更新学习进度

```
POST /api/v1/org/{org_id}/arvr/contents/{content_id}/progress
```

**请求体:**
```json
{
  "progress_percentage": 75.0,
  "current_state": {
    "current_molecule": "H2O"
  },
  "milestones_reached": ["water_molecule_loaded"],
  "time_spent": 15.5,
  "interaction_count": 42,
  "assessment_score": 85.0
}
```

#### 获取学习进度

```
GET /api/v1/org/{org_id}/arvr/contents/{content_id}/progress
```

### 5. 物理引擎

#### 获取物理状态

```
GET /api/v1/org/{org_id}/arvr/contents/{content_id}/physics-state
```

**响应:**
```json
{
  "objects": [
    {
      "id": "test_cube",
      "position": [0.0, 5.0, 0.0],
      "velocity": [0.0, -2.0, 0.0],
      "mass": 1.0,
      "is_static": false
    }
  ],
  "gravity": 9.81,
  "time_step": 0.016666666666666666
}
```

#### 处理语音命令

```
POST /api/v1/org/{org_id}/arvr/contents/{content_id}/voice-command
```

**请求体:**
```json
{
  "command": "开始实验",
  "user_id": 1
}
```

#### 处理手势交互

```
POST /api/v1/org/{org_id}/arvr/contents/{content_id}/gesture
```

**请求体:**
```json
{
  "type": "tap",
  "position": [0.5, 0.3, 0.0],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 6. 统计信息

#### 获取内容统计

```
GET /api/v1/org/{org_id}/arvr/contents/{content_id}/statistics
```

**响应:**
```json
{
  "view_count": 150,
  "completion_count": 85,
  "average_rating": 4.5,
  "interaction_count": 1200
}
```

### 7. 推荐系统

#### 获取内容推荐

```
GET /api/v1/org/{org_id}/arvr/recommendations
```

**查询参数:**
- `user_id` (可选): 用户ID
- `limit` (可选): 推荐数量，默认10，最大50

## WebSocket接口

### 传感器数据流

```
WebSocket /api/v1/org/{org_id}/arvr/ws/sensor-stream/{content_id}
```

**连接参数:**
- `session_id`: 会话ID
- `user_id`: 用户ID

**消息格式:**
```json
{
  "sensor_type": "accelerometer",
  "payload": {
    "x": 0.5,
    "y": -0.2,
    "z": 9.8
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 枚举类型

### 内容类型 (ARVRContentType)
- `unity_webgl`: Unity WebGL构建
- `threejs_scene`: Three.js场景
- `model_viewer`: 3D模型查看器
- `interactive_demo`: 交互式演示
- `virtual_lab`: 虚拟实验室
- `ar_marker`: AR标记识别

### 平台类型 (ARVRPlatform)
- `web_browser`: 网页浏览器
- `mobile_ar`: 移动端AR
- `vr_headset`: VR头显
- `desktop_vr`: 桌面VR

### 传感器类型 (SensorType)
- `accelerometer`: 加速度计
- `gyroscope`: 陀螺仪
- `magnetometer`: 磁力计
- `gps`: GPS定位
- `camera`: 摄像头
- `microphone`: 麦克风
- `touch`: 触摸屏
- `custom`: 自定义传感器

### 交互模式 (InteractionMode)
- `gesture`: 手势识别
- `voice`: 语音控制
- `controller`: 控制器
- `gaze`: 注视点
- `physical`: 物理交互

## 使用示例

### JavaScript客户端示例

```javascript
// 创建AR/VR内容
async function createARVRContent() {
  const response = await fetch('/api/v1/org/1/arvr/contents', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      course_id: 1,
      title: '3D分子模型',
      content_type: 'unity_webgl',
      platform: 'web_browser'
    })
  });
  return await response.json();
}

// 上传Unity构建
async function uploadUnityBuild(contentId, buildFile, thumbnailFile) {
  const formData = new FormData();
  formData.append('build_file', buildFile);
  if (thumbnailFile) {
    formData.append('thumbnail_file', thumbnailFile);
  }
  
  const response = await fetch(`/api/v1/org/1/arvr/contents/${contentId}/upload-build`, {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token
    },
    body: formData
  });
  return await response.json();
}

// WebSocket传感器数据流
function connectSensorStream(contentId) {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/org/1/arvr/ws/sensor-stream/${contentId}?session_id=session123&user_id=1`);
  
  ws.onopen = () => {
    console.log('传感器流已连接');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('接收到传感器数据:', data);
  };
  
  // 发送传感器数据
  function sendSensorData(sensorType, payload) {
    ws.send(JSON.stringify({
      sensor_type: sensorType,
      payload: payload
    }));
  }
}
```

### Unity客户端示例

```csharp
// Unity中调用API
public class ARVRApiClient : MonoBehaviour
{
    private string baseUrl = "http://localhost:8000/api/v1/org/1/arvr";
    private string authToken;
    
    async void Start()
    {
        // 获取认证Token
        authToken = await GetAuthToken();
    }
    
    async Task<string> GetAuthToken()
    {
        // 实现认证逻辑
        return "your-jwt-token";
    }
    
    public async void SendInteractionData(string contentId, string interactionType, object data)
    {
        var payload = new Dictionary<string, object>
        {
            ["interaction_type"] = interactionType,
            ["interaction_data"] = data,
            ["interaction_mode"] = "gesture",
            ["success"] = true
        };
        
        var json = JsonConvert.SerializeObject(payload);
        var request = new UnityWebRequest($"{baseUrl}/contents/{contentId}/interactions", "POST");
        request.SetRequestHeader("Authorization", $"Bearer {authToken}");
        request.SetRequestHeader("Content-Type", "application/json");
        request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        request.downloadHandler = new DownloadHandlerBuffer();
        
        await request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("交互数据发送成功");
        }
    }
}
```

## 错误处理

常见错误代码及解决方案:

- `400 Bad Request`: 检查请求参数格式和必填字段
- `401 Unauthorized`: 确认JWT Token有效且未过期
- `403 Forbidden`: 检查用户权限
- `404 Not Found`: 确认资源ID正确
- `500 Internal Server Error`: 服务器内部错误，请联系管理员

## 性能优化建议

1. **批量操作**: 对于大量传感器数据，建议使用批量上传
2. **数据压缩**: WebSocket传输时可启用数据压缩
3. **缓存策略**: 合理使用HTTP缓存头
4. **分页查询**: 大量数据查询时使用分页参数
5. **连接复用**: WebSocket连接尽量复用，避免频繁建立/断开

## 版本历史

- **v1.0.0** (2024-01-15): 初始版本发布