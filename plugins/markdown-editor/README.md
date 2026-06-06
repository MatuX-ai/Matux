# Markdown 编辑器插件

> **插件 ID**: `markdown-editor`  
> **版本**: 1.0.0  
> **分级**: Tier A（通用插件，所有设备兼容）  
> **分类**: 编辑器、生产力工具

---

## 📋 功能特性

这是一个功能丰富的 Markdown 编辑器插件，提供完整的文档编写、预览和导出功能。

### ✨ 核心功能

- ✅ **实时预览** - 分屏编辑，左侧编写 Markdown，右侧实时查看渲染效果
- ✅ **语法高亮** - 代码块自动语法高亮，支持 100+ 编程语言
- ✅ **丰富工具栏** - 一键插入标题、粗体、列表、代码块、链接、图片等
- ✅ **文档管理** - 创建、保存、打开、删除文档，支持标签分类
- ✅ **模板系统** - 内置 4 种模板（空白、文章、会议记录、技术文档）
- ✅ **自动保存** - 智能防丢，停止输入 2 秒后自动保存，30 秒定时备份
- ✅ **多主题** - 编辑器支持浅色/深色主题，预览支持 3 种样式
- ✅ **导出功能** - 导出为 HTML（开箱即用）和 PDF（需安装额外工具）
- ✅ **滚动同步** - 编辑器和预览面板滚动同步
- ✅ **统计信息** - 实时显示词数、字符数、行数、保存状态

### 📝 Markdown 扩展支持

- **Extra** - 表格、脚注、定义列表等
- **CodeHilite** - 代码语法高亮
- **TOC** - 自动生成目录
- **Admonition** - 提示框（警告、提示、注意等）
- **Meta** - 文档元数据

---

## 🚀 快速开始

### 1. 安装插件

通过插件商店安装：

```bash
# 在插件商店搜索 "Markdown 编辑器"
# 点击"安装"按钮
```

### 2. 创建文档

打开插件后，默认显示欢迎文档。点击工具栏的"新建文档"按钮开始编写。

### 3. 使用模板

点击工具栏的"模板"按钮，选择预定义模板快速开始：

- **空白文档** - 从头开始
- **文章** - 适合博客文章、技术文档
- **会议记录** - 结构化会议记录模板
- **技术文档** - API 文档、架构文档模板

### 4. 编写 Markdown

使用工具栏按钮或直接输入 Markdown 语法：

```markdown
# 一级标题
## 二级标题

**粗体文本** 和 *斜体文本*

- 无序列表项 1
- 无序列表项 2

1. 有序列表项 1
2. 有序列表项 2

> 引用文本

`行内代码`

```python
# 代码块
def hello():
    print("Hello, World!")
```

| 列 1 | 列 2 | 列 3 |
|------|------|------|
| 数据 | 数据 | 数据 |

[链接](https://example.com)

![图片](image.png)
```

### 5. 导出文档

点击工具栏的"导出"按钮：

- **导出为 HTML** - 生成独立的 HTML 文件，可在浏览器中查看
- **导出为 PDF** - 生成 PDF 文件（需要安装 `weasyprint` 或 `wkhtmltopdf`）

---

## 🎨 主题和配置

### 编辑器主题

- **浅色主题** - 默认，适合白天使用
- **深色主题** - 适合夜间使用，保护眼睛

### 预览主题

- **默认/GitHub** - GitHub 风格样式
- **深色** - 深色预览主题

### 自动保存

默认启用自动保存：

- **防抖保存** - 停止输入 2 秒后自动保存
- **定时保存** - 每 30 秒自动保存一次

可在设置中调整或关闭。

---

## 📁 文件结构

```
plugins/markdown-editor/
├── manifest.json                      # 插件清单
├── README.md                          # 本文档
├── backend/
│   ├── routes/
│   │   └── markdown_routes.py         # API 路由
│   ├── services/
│   │   └── markdown_service.py        # Markdown 服务
│   └── hooks/
│       ├── on_install.py              # 安装钩子
│       └── on_uninstall.py            # 卸载钩子
├── frontend/
│   └── components/
│       ├── markdown-editor.component.ts    # 组件逻辑
│       ├── markdown-editor.component.html  # 模板
│       └── markdown-editor.component.scss  # 样式
└── resources/
    └── icon.svg                       # 插件图标
```

---

## 🔧 API 参考

### 后端 API

#### 解析 Markdown

```http
POST /api/v1/markdown/parse
Content-Type: application/json

{
  "content": "# Hello\n\nWorld",
  "extensions": ["extra", "codehilite", "toc"]
}
```

**响应**:

```json
{
  "html": "<h1>Hello</h1><p>World</p>",
  "toc": "<ul>...</ul>",
  "metadata": {}
}
```

#### 导出 HTML

```http
POST /api/v1/markdown/export/html
Content-Type: application/json

{
  "content": "# Title",
  "title": "My Document",
  "theme": "default",
  "include_toc": true
}
```

**响应**:

```json
{
  "success": true,
  "downloadUrl": "/api/v1/markdown/download/file.html",
  "fileName": "file.html",
  "fileSize": 1234
}
```

#### 导出 PDF

```http
POST /api/v1/markdown/export/pdf
Content-Type: application/json

{
  "content": "# Title",
  "title": "My Document",
  "theme": "default",
  "include_toc": true
}
```

#### 保存文档

```http
POST /api/v1/markdown/save
Content-Type: application/json

{
  "id": "doc-123",  // 可选，更新时使用
  "title": "My Document",
  "content": "# Hello",
  "tags": ["tutorial"]
}
```

#### 获取文档列表

```http
GET /api/v1/markdown/documents?limit=50&offset=0&tag=tutorial
```

#### 获取文档

```http
GET /api/v1/markdown/documents/{doc_id}
```

#### 删除文档

```http
DELETE /api/v1/markdown/documents/{doc_id}
```

#### 获取模板列表

```http
GET /api/v1/markdown/templates
```

---

## 📦 依赖

### 必需依赖

- `markdown` >= 3.4 - Markdown 解析器

### 可选依赖（推荐安装）

- `pygments` >= 2.15 - 代码语法高亮
- `weasyprint` >= 60 - PDF 导出（推荐）
- `pdfkit` >= 1.0 - PDF 导出（备选，需要 `wkhtmltopdf`）

### 安装依赖

```bash
# 必需依赖
pip install markdown

# 推荐依赖
pip install pygments weasyprint

# 或备选方案
pip install pdfkit
# 然后安装 wkhtmltopdf: https://wkhtmltopdf.org/
```

---

## 💾 数据存储

插件数据存储在用户目录：

```
~/.imato/plugin-data/markdown-editor/
├── documents/          # 文档文件（JSON 格式）
├── exports/            # 导出文件（HTML/PDF）
├── templates/          # 自定义模板
├── themes/             # 自定义主题
├── backups/            # 自动备份
└── config.json         # 插件配置
```

### 文档格式

每个文档保存为独立的 JSON 文件：

```json
{
  "id": "doc-uuid",
  "title": "文档标题",
  "content": "# Markdown 内容",
  "tags": ["tag1", "tag2"],
  "created_at": "2026-06-06T12:00:00",
  "updated_at": "2026-06-06T12:30:00"
}
```

---

## 🔒 权限

插件需要以下权限：

- `file:read` - 读取本地文件
- `file:write` - 写入本地文件
- `storage:local` - 本地存储

---

## 🛠️ 开发指南

### 本地开发

1. 克隆插件代码
2. 修改代码
3. 使用打包工具打包：

```bash
npm run build-plugin ./plugins/markdown-editor
```

4. 安装测试：

```bash
# 通过插件商店安装本地 .mxp 文件
```

### 扩展功能

#### 添加新模板

在 `backend/routes/markdown_routes.py` 的 `get_templates()` 函数中添加：

```python
{
    "id": "my-template",
    "name": "我的模板",
    "content": "# 模板内容\n\n..."
}
```

#### 添加新主题

在 `backend/services/markdown_service.py` 的 `_get_theme_css()` 方法中添加：

```python
elif theme == "my-theme":
    return """
    /* 自定义 CSS */
    """
```

#### 自定义 Markdown 扩展

在 `frontend/components/markdown-editor.component.ts` 中修改扩展列表：

```typescript
extensions: ['extra', 'codehilite', 'toc', 'my-extension']
```

---

## ❓ 常见问题

### Q: PDF 导出失败？

A: PDF 导出需要额外工具。安装以下任一工具：

```bash
# 方案 1: weasyprint（推荐）
pip install weasyprint

# 方案 2: pdfkit + wkhtmltopdf
pip install pdfkit
# 然后从 https://wkhtmltopdf.org/ 下载并安装 wkhtmltopdf
```

### Q: 代码没有语法高亮？

A: 安装 Pygments：

```bash
pip install pygments
```

### Q: 如何恢复误删的文档？

A: 插件会自动备份。查看 `~/.imato/plugin-data/markdown-editor/backups/` 目录。

### Q: 如何同步文档到其他设备？

A: 文档存储在本地，可通过云盘同步 `~/.imato/plugin-data/markdown-editor/documents/` 目录。

### Q: 支持哪些 Markdown 语法？

A: 支持标准 Markdown + GitHub Flavored Markdown（表格、任务列表等）+ 扩展语法（脚注、定义列表等）。

---

## 📜 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 联系方式

- **问题反馈**: https://github.com/imato/markdown-editor/issues
- **文档**: https://github.com/imato/markdown-editor/docs

---

**祝你使用愉快！** 🚀
