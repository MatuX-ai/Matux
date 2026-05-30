# 协作编辑系统 API 文档

## 概述

协作编辑系统提供实时协同编辑、评论批注等功能，基于 Operational Transformation (OT) 算法实现并发操作的一致性处理。

## 基础信息

- **Base URL**: `/api/v1/org/{org_id}/courses/{course_id}/collaborative-documents`
- **认证方式**: JWT Token (通过 Authorization Header)
- **内容类型**: `application/json`

## 数据模型

### 协作文档 (CollaborativeDocument)

```json
{
  "id": 1,
  "course_id": 101,
  "org_id": 1,
  "document_name": "教学大纲",
  "document_type": "richtext",
  "content": "文档内容...",
  "version_number": 5,
  "last_commit_hash": "a1b2c3d4e5f6...",
  "is_locked": false,
  "locked_by": null,
  "allow_comments": true,
  "allow_suggestions": true,
  "created_at": "2026-02-26T10:00:00Z",
  "updated_at": "2026-02-26T15:30:00Z"
}
```

### 文档操作 (DocumentOperation)

```json
{
  "id": 101,
  "document_id": 1,
  "user_id": 123,
  "operation_type": "insert",
  "position": 45,
  "content": "新增的文字内容",
  "operation_id": "unique-operation-id",
  "client_id": "user-session-123",
  "revision": 15,
  "timestamp": "2026-02-26T15:30:45Z",
  "transformed_operation": null
}
```

### 文档评论 (DocumentComment)

```json
{
  "id": 201,
  "document_id": 1,
  "user_id": 123,
  "start_position": 100,
  "end_position": 150,
  "content": "这段内容需要修改",
  "comment_type": "comment",
  "referenced_content": "原文内容片段",
  "is_resolved": false,
  "resolved_at": null,
  "resolved_by": null,
  "parent_comment_id": null,
  "replies_count": 3,
  "created_at": "2026-02-26T14:20:00Z",
  "updated_at": "2026-02-26T14:25:00Z"
}
```

### 文档建议 (DocumentSuggestion)

```json
{
  "id": 301,
  "document_id": 1,
  "user_id": 123,
  "start_position": 200,
  "end_position": 250,
  "original_content": "原文内容",
  "suggested_content": "建议修改的内容",
  "suggestion_reason": "修改原因说明",
  "status": "pending",
  "reviewed_at": null,
  "reviewed_by": null,
  "created_at": "2026-02-26T16:00:00Z",
  "updated_at": "2026-02-26T16:00:00Z"
}
```

## API 接口

### 文档管理

#### 创建协作文档

```
POST /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents
```

**请求体:**
```json
{
  "document_name": "教学大纲",
  "document_type": "richtext",
  "content": "初始文档内容",
  "allow_comments": true,
  "allow_suggestions": true
}
```

**响应:**
```json
{
  "id": 1,
  "course_id": 101,
  "org_id": 1,
  "document_name": "教学大纲",
  "document_type": "richtext",
  "content": "初始文档内容",
  "version_number": 1,
  "last_commit_hash": null,
  "is_locked": false,
  "locked_by": null,
  "allow_comments": true,
  "allow_suggestions": true,
  "created_at": "2026-02-26T10:00:00Z",
  "updated_at": "2026-02-26T10:00:00Z"
}
```

#### 获取文档详情

```
GET /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}
```

#### 更新文档内容

```
PUT /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/content
```

**请求体:**
```json
{
  "content": "更新后的完整文档内容"
}
```

### 实时协作

#### 批量应用操作

```
POST /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/operations/batch
```

**请求体:**
```json
[
  {
    "operation_type": "insert",
    "position": 100,
    "content": "插入的内容",
    "client_id": "user-session-123",
    "revision": 15
  },
  {
    "operation_type": "delete",
    "position": 50,
    "content": "要删除的内容",
    "client_id": "user-session-123",
    "revision": 15
  }
]
```

**响应:**
```json
{
  "success": true,
  "transformed_operations": [...],
  "new_content": "应用操作后的新内容",
  "new_version": 16
}
```

#### 获取操作历史

```
GET /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/operations
```

**查询参数:**
- `from_revision` (可选): 起始修订版本号
- `limit` (可选): 返回记录数，默认50，最大1000

### 评论功能

#### 添加评论

```
POST /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/comments
```

**请求体:**
```json
{
  "start_position": 100,
  "end_position": 150,
  "content": "评论内容",
  "comment_type": "comment",
  "referenced_content": "被引用的内容片段"
}
```

#### 获取文档评论

```
GET /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/comments
```

#### 解决评论

```
PUT /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/comments/{comment_id}/resolve
```

### 建议功能

#### 添加建议

```
POST /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/suggestions
```

**请求体:**
```json
{
  "start_position": 200,
  "end_position": 250,
  "original_content": "原文内容",
  "suggested_content": "建议内容",
  "suggestion_reason": "修改理由"
}
```

#### 审核建议

```
PUT /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/suggestions/{suggestion_id}/review
```

**请求体:**
```json
{
  "status": "accepted"  // 或 "rejected"
}
```

### 会话管理

#### 加入文档会话

```
POST /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/sessions
```

**请求体:**
```json
{
  "client_id": "unique-client-identifier"
}
```

#### 更新光标位置

```
PUT /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/sessions/{session_id}/cursor
```

**请求体:**
```json
{
  "cursor_position": 125,
  "selection_start": 120,
  "selection_end": 130
}
```

#### 离开会话

```
DELETE /api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/sessions/{session_id}
```

### WebSocket 实时连接

#### 连接地址

```
WebSocket: ws://localhost:8000/api/v1/org/{org_id}/courses/{course_id}/collaborative-documents/{document_id}/ws?session_id={session_id}
```

#### 消息格式

**客户端发送:**
```json
{
  "type": "heartbeat",
  "timestamp": 1234567890
}
```

**服务器广播:**
```json
{
  "type": "operations_applied",
  "document_id": 1,
  "operations": [...],
  "new_content": "更新后的内容",
  "sender": "user@example.com"
}
```

```json
{
  "type": "comment_added",
  "document_id": 1,
  "comment": {
    "id": 201,
    "user_id": 123,
    "user_name": "张老师",
    "content": "评论内容",
    "start_position": 100,
    "end_position": 150,
    "comment_type": "comment",
    "created_at": "2026-02-26T14:20:00Z"
  }
}
```

```json
{
  "type": "cursor_update",
  "session_id": "session-123",
  "user_id": 123,
  "user_name": "李老师",
  "cursor_position": 250,
  "selection_start": 240,
  "selection_end": 260
}
```

## 错误响应

所有API错误遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

**常见HTTP状态码:**
- `400`: 请求参数错误
- `401`: 未授权访问
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

## OT算法说明

系统采用 Operational Transformation 算法处理并发操作：

1. **插入-插入转换**: 根据位置和客户端ID确定操作顺序
2. **插入-删除转换**: 调整插入位置以适应删除操作
3. **删除-插入转换**: 调整删除范围或分割删除操作
4. **删除-删除转换**: 合并重叠的删除范围

算法确保所有客户端最终达到一致的状态。

## 性能优化建议

1. **批量操作**: 尽可能批量发送操作而非逐个发送
2. **操作压缩**: 对连续的同类操作进行合并
3. **增量同步**: 只同步变化的部分而非整个文档
4. **连接复用**: 保持WebSocket长连接减少握手开销

## 安全考虑

1. 所有API都需要有效的JWT认证
2. 文档访问权限基于组织和课程权限控制
3. 敏感操作(如文档锁定)需要额外权限验证
4. 操作历史完整记录便于审计追溯
