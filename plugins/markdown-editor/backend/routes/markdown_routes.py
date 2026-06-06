"""
Markdown 编辑器 - 后端路由

提供 Markdown 解析、导出等功能:
- POST /api/v1/markdown/parse - 解析 Markdown 为 HTML
- POST /api/v1/markdown/export/html - 导出为 HTML
- POST /api/v1/markdown/export/pdf - 导出为 PDF
- GET /api/v1/markdown/templates - 获取模板列表
- POST /api/v1/markdown/save - 保存文档
- GET /api/v1/markdown/documents - 获取文档列表
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import markdown
import logging
import os
from datetime import datetime
from pathlib import Path

from backend.services.markdown_service import MarkdownService

# ==================== 配置 ====================

router = APIRouter()
logger = logging.getLogger(__name__)

# Markdown 服务实例
markdown_service = MarkdownService()

# ==================== 请求/响应模型 ====================


class MarkdownParseRequest(BaseModel):
    """Markdown 解析请求"""
    content: str = Field(..., description="Markdown 内容")
    extensions: List[str] = Field(
        default=["extra", "codehilite", "toc"],
        description="Markdown 扩展"
    )


class MarkdownParseResponse(BaseModel):
    """Markdown 解析响应"""
    html: str = Field(..., description="HTML 内容")
    toc: Optional[str] = Field(None, description="目录")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class MarkdownExportRequest(BaseModel):
    """Markdown 导出请求"""
    content: str = Field(..., description="Markdown 内容")
    title: str = Field(default="Untitled", description="文档标题")
    theme: str = Field(default="default", description="主题")
    include_toc: bool = Field(default=True, description="包含目录")


class MarkdownDocument(BaseModel):
    """Markdown 文档"""
    id: str
    title: str
    content: str
    created_at: str
    updated_at: str
    tags: List[str] = []


class MarkdownSaveRequest(BaseModel):
    """保存文档请求"""
    id: Optional[str] = Field(None, description="文档 ID（更新时使用）")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="Markdown 内容")
    tags: List[str] = Field(default=[], description="标签")


# ==================== 路由 ====================


@router.post("/api/v1/markdown/parse", response_model=MarkdownParseResponse)
async def parse_markdown(request: MarkdownParseRequest):
    """
    解析 Markdown 为 HTML
    
    支持多种扩展:
    - extra: 表格、脚注等
    - codehilite: 代码高亮
    - toc: 目录生成
    - admonition: 提示框
    """
    try:
        result = await markdown_service.parse(
            content=request.content,
            extensions=request.extensions
        )
        
        return MarkdownParseResponse(
            html=result["html"],
            toc=result.get("toc"),
            metadata=result.get("metadata", {})
        )
    
    except Exception as e:
        logger.error(f"Markdown 解析失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v1/markdown/export/html")
async def export_to_html(request: MarkdownExportRequest):
    """
    导出 Markdown 为 HTML 文件
    
    返回 HTML 文件下载链接
    """
    try:
        html_content = await markdown_service.export_html(
            content=request.content,
            title=request.title,
            theme=request.theme,
            include_toc=request.include_toc
        )
        
        # 保存到临时文件
        export_dir = markdown_service.get_export_dir()
        file_path = export_dir / f"{request.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        file_path.write_text(html_content, encoding="utf-8")
        
        return {
            "success": True,
            "downloadUrl": f"/api/v1/markdown/download/{file_path.name}",
            "fileName": file_path.name,
            "fileSize": file_path.stat().st_size
        }
    
    except Exception as e:
        logger.error(f"HTML 导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/markdown/export/pdf")
async def export_to_pdf(request: MarkdownExportRequest):
    """
    导出 Markdown 为 PDF 文件
    
    需要 wkhtmltopdf 或 weasyprint
    """
    try:
        # 先转换为 HTML
        html_content = await markdown_service.export_html(
            content=request.content,
            title=request.title,
            theme=request.theme,
            include_toc=request.include_toc
        )
        
        # 转换为 PDF
        pdf_path = await markdown_service.export_pdf(
            html_content=html_content,
            title=request.title
        )
        
        return {
            "success": True,
            "downloadUrl": f"/api/v1/markdown/download/{pdf_path.name}",
            "fileName": pdf_path.name,
            "fileSize": pdf_path.stat().st_size
        }
    
    except Exception as e:
        logger.error(f"PDF 导出失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/markdown/save", response_model=MarkdownDocument)
async def save_document(request: MarkdownSaveRequest):
    """
    保存 Markdown 文档
    
    如果提供 id 则更新，否则创建新文档
    """
    try:
        document = await markdown_service.save_document(
            doc_id=request.id,
            title=request.title,
            content=request.content,
            tags=request.tags
        )
        
        return MarkdownDocument(**document)
    
    except Exception as e:
        logger.error(f"保存文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/markdown/documents", response_model=List[MarkdownDocument])
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    tag: Optional[str] = None
):
    """
    获取文档列表
    
    支持分页和标签过滤
    """
    try:
        documents = await markdown_service.list_documents(
            limit=limit,
            offset=offset,
            tag=tag
        )
        
        return [MarkdownDocument(**doc) for doc in documents]
    
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/markdown/documents/{doc_id}", response_model=MarkdownDocument)
async def get_document(doc_id: str):
    """获取指定文档"""
    try:
        document = await markdown_service.get_document(doc_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return MarkdownDocument(**document)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/v1/markdown/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    try:
        success = await markdown_service.delete_document(doc_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {"success": True, "message": "文档已删除"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/markdown/templates")
async def get_templates():
    """
    获取模板列表
    
    返回预定义的 Markdown 模板
    """
    templates = [
        {
            "id": "blank",
            "name": "空白文档",
            "content": "# 标题\n\n开始编写内容..."
        },
        {
            "id": "article",
            "name": "文章",
            "content": """# 文章标题

> 摘要或引言

## 第一节

正文内容...

## 第二节

正文内容...

## 参考

- [链接](https://example.com)
"""
        },
        {
            "id": "meeting-notes",
            "name": "会议记录",
            "content": """# 会议记录

**日期**: 2026-06-06  
**参会人**: 

## 议程

1. 
2. 

## 讨论要点

### 要点 1

- 

### 要点 2

- 

## 行动项

- [ ] 任务 1 @负责人
- [ ] 任务 2 @负责人

## 下次会议

**日期**: 
"""
        },
        {
            "id": "technical-doc",
            "name": "技术文档",
            "content": """# 技术文档标题

## 概述

简要描述...

## 架构

```
架构图或说明
```

## API 接口

### GET /api/endpoint

**请求参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | ID |

**响应**:

```json
{
  "success": true
}
```

## 部署说明

1. 步骤 1
2. 步骤 2
"""
        }
    ]
    
    return {"success": True, "templates": templates}
