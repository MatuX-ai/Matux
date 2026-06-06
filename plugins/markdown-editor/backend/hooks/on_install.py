"""
Markdown 编辑器 - 安装钩子

在安装时执行:
1. 创建必要的目录
2. 初始化默认配置
3. 创建示例文档
4. 验证依赖
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def on_install(plugin_info: dict, data_dir: str) -> bool:
    """
    安装钩子
    
    Args:
        plugin_info: 插件信息（manifest）
        data_dir: 插件数据目录
    
    Returns:
        是否成功
    """
    try:
        logger.info("开始安装 Markdown 编辑器插件...")
        
        # 1. 创建目录结构
        logger.info("创建目录结构...")
        base_dir = Path(data_dir)
        
        directories = [
            base_dir / "documents",
            base_dir / "exports",
            base_dir / "templates",
            base_dir / "themes",
            base_dir / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"  ✓ 创建目录: {directory}")
        
        # 2. 创建默认配置
        logger.info("创建默认配置...")
        config = {
            "editor": {
                "theme": "light",
                "fontSize": 14,
                "lineHeight": 1.6,
                "tabSize": 4,
                "wordWrap": True,
                "showLineNumbers": True,
                "showMinimap": True
            },
            "preview": {
                "theme": "default",
                "syncScroll": True,
                "autoRefresh": True
            },
            "autoSave": {
                "enabled": True,
                "interval": 30000,  # 30 秒
                "maxBackups": 10
            },
            "export": {
                "defaultFormat": "html",
                "includeToc": True,
                "pdfEngine": "weasyprint"  # weasyprint 或 wkhtmltopdf
            },
            "extensions": {
                "enabled": [
                    "extra",
                    "codehilite",
                    "toc",
                    "admonition"
                ]
            }
        }
        
        config_path = base_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"  ✓ 配置文件: {config_path}")
        
        # 3. 创建示例文档
        logger.info("创建示例文档...")
        
        sample_docs = [
            {
                "id": "welcome",
                "title": "欢迎使用 Markdown 编辑器",
                "content": """# 欢迎使用 Markdown 编辑器 🎉

这是一个功能丰富的 Markdown 编辑器插件。

## 功能特性

- ✅ **实时预览** - 所见即所得的编辑体验
- ✅ **语法高亮** - 代码块自动语法高亮
- ✅ **多种主题** - 支持浅色/深色主题
- ✅ **导出功能** - 导出为 HTML/PDF
- ✅ **自动保存** - 不用担心丢失内容
- ✅ **模板系统** - 快速创建文档

## 快速开始

### 1. 编写 Markdown

```markdown
# 标题

这是一段正文。

## 二级标题

- 列表项 1
- 列表项 2

> 引用文本

`行内代码`

```python
# 代码块
print("Hello, World!")
```
```

### 2. 实时预览

编辑器右侧会实时显示渲染后的效果。

### 3. 导出文档

点击工具栏的"导出"按钮，选择导出格式：
- HTML - 网页格式
- PDF - 便携式文档

## Markdown 语法参考

### 标题

```
# 一级标题
## 二级标题
### 三级标题
```

### 强调

```
**粗体**
*斜体*
~~删除线~~
```

### 列表

```
- 无序列表项 1
- 无序列表项 2

1. 有序列表项 1
2. 有序列表项 2
```

### 链接和图片

```
[链接文本](https://example.com)

![图片描述](image.png)
```

### 代码

行内代码: `code`

代码块:

```python
def hello():
    print("Hello, World!")
```

### 表格

```
| 列 1 | 列 2 | 列 3 |
|------|------|------|
| 数据 | 数据 | 数据 |
```

### 引用

```
> 引用文本
> 多行引用
```

## 提示和技巧

💡 **提示 1**: 使用 `Ctrl+S` 快速保存  
💡 **提示 2**: 使用 `Ctrl+P` 快速导出  
💡 **提示 3**: 拖拽图片到编辑器自动插入  

## 获取帮助

如果遇到问题，请查看：
- [文档](https://github.com/imato/markdown-editor/docs)
- [问题反馈](https://github.com/imato/markdown-editor/issues)

---

**祝你使用愉快！** 🚀
""",
                "tags": ["tutorial", "welcome"]
            },
            {
                "id": "cheatsheet",
                "title": "Markdown 速查表",
                "content": """# Markdown 速查表

## 基础语法

| 语法 | 效果 | 代码 |
|------|------|------|
| 粗体 | **粗体** | `**粗体**` |
| 斜体 | *斜体* | `*斜体*` |
| 删除线 | ~~删除~~ | `~~删除~~` |
| 链接 | [链接](url) | `[链接](url)` |
| 图片 | ![alt](img) | `![alt](img)` |

## 标题

```markdown
# H1
## H2
### H3
#### H4
```

## 列表

无序列表:
```
- 项目 1
- 项目 2
  - 子项目
```

有序列表:
```
1. 第一项
2. 第二项
```

## 代码

行内代码: `` `code` ``

代码块:
````
```python
print("Hello")
```
````

## 引用

```
> 引用内容
```

## 表格

```
| 左对齐 | 居中 | 右对齐 |
|:-------|:----:|-------:|
| 内容 | 内容 | 内容 |
```

## 分割线

```
---
```

## 复选框

```
- [ ] 未完成
- [x] 已完成
```

## 数学公式（需要扩展）

行内: `$E = mc^2$`

块级:
```
$$
\\sum_{i=1}^{n} x_i
$$
```
""",
                "tags": ["reference", "cheatsheet"]
            }
        ]
        
        documents_dir = base_dir / "documents"
        
        for doc in sample_docs:
            doc_path = documents_dir / f"{doc['id']}.json"
            
            from datetime import datetime
            doc_data = {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc.get("tags", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"  ✓ 创建示例文档: {doc['title']}")
        
        # 4. 检查可选依赖
        logger.info("检查可选依赖...")
        
        optional_deps = {
            "markdown": "Markdown 解析",
            "weasyprint": "PDF 导出（推荐）",
            "pdfkit": "PDF 导出（备选）",
            "pygments": "代码高亮"
        }
        
        for package, description in optional_deps.items():
            try:
                __import__(package)
                logger.info(f"  ✓ {package} ({description})")
            except ImportError:
                logger.warning(f"  ✗ {package} 未安装 ({description})")
                if package == "markdown":
                    logger.error("  ⚠️  markdown 是必需依赖！")
                    return False
        
        logger.info("✅ Markdown 编辑器插件安装成功！")
        logger.info(f"📁 数据目录: {base_dir}")
        logger.info(f"📄 示例文档: {len(sample_docs)} 个")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ 安装失败: {e}", exc_info=True)
        return False
