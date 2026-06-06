"""
Markdown 编辑器 - 后端服务

功能:
1. Markdown 解析（支持多种扩展）
2. HTML/PDF 导出
3. 文档管理（CRUD）
4. 模板管理
5. 自动保存
"""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.codehilite import CodeHiliteExtension

logger = logging.getLogger(__name__)


class MarkdownService:
    """Markdown 服务"""
    
    def __init__(self):
        """初始化服务"""
        self.documents_dir = Path(os.path.expanduser("~/.imato/plugin-data/markdown-editor/documents"))
        self.export_dir = Path(os.path.expanduser("~/.imato/plugin-data/markdown-editor/exports"))
        
        # 确保目录存在
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Markdown 服务初始化完成")
        logger.info(f"文档目录: {self.documents_dir}")
        logger.info(f"导出目录: {self.export_dir}")
    
    async def parse(
        self,
        content: str,
        extensions: List[str] = None
    ) -> Dict[str, Any]:
        """
        解析 Markdown 为 HTML
        
        Args:
            content: Markdown 内容
            extensions: 扩展列表
        
        Returns:
            包含 html, toc, metadata 的字典
        """
        if extensions is None:
            extensions = ["extra", "codehilite", "toc"]
        
        # 构建 Markdown 扩展列表
        md_extensions = []
        
        for ext in extensions:
            if ext == "extra":
                md_extensions.append("markdown.extensions.extra")
            elif ext == "codehilite":
                md_extensions.append(CodeHiliteExtension(css_class="highlight"))
            elif ext == "toc":
                md_extensions.append(TocExtension(permalink=True))
            elif ext == "admonition":
                md_extensions.append("markdown.extensions.admonition")
            elif ext == "meta":
                md_extensions.append("markdown.extensions.meta")
            else:
                md_extensions.append(f"markdown.extensions.{ext}")
        
        # 创建 Markdown 实例
        md = markdown.Markdown(extensions=md_extensions)
        
        # 转换
        html = md.convert(content)
        
        # 提取目录
        toc = getattr(md, 'toc', None)
        
        # 提取元数据
        metadata = getattr(md, 'Meta', {})
        
        return {
            "html": html,
            "toc": toc,
            "metadata": metadata
        }
    
    async def export_html(
        self,
        content: str,
        title: str = "Untitled",
        theme: str = "default",
        include_toc: bool = True
    ) -> str:
        """
        导出为 HTML
        
        Args:
            content: Markdown 内容
            title: 文档标题
            theme: 主题名称
            include_toc: 包含目录
        
        Returns:
            完整的 HTML 文档
        """
        # 解析 Markdown
        extensions = ["extra", "codehilite", "toc", "meta"]
        result = await self.parse(content, extensions)
        
        html_body = result["html"]
        toc_html = result.get("toc", "")
        
        # 加载主题 CSS
        theme_css = self._get_theme_css(theme)
        
        # 构建完整 HTML
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{theme_css}
    </style>
</head>
<body>
    <div class="markdown-container">
        {f'<div class="toc">{toc_html}</div>' if include_toc and toc_html else ''}
        <div class="markdown-body">
            {html_body}
        </div>
    </div>
</body>
</html>"""
        
        return html_template
    
    async def export_pdf(
        self,
        html_content: str,
        title: str = "Untitled"
    ) -> Path:
        """
        导出为 PDF
        
        Args:
            html_content: HTML 内容
            title: 文档标题
        
        Returns:
            PDF 文件路径
        
        Raises:
            RuntimeError: 如果 PDF 转换工具不可用
        """
        try:
            # 尝试使用 weasyprint
            from weasyprint import HTML
            
            pdf_path = self.export_dir / f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            HTML(string=html_content).write_pdf(str(pdf_path))
            
            logger.info(f"PDF 导出成功: {pdf_path}")
            return pdf_path
        
        except ImportError:
            # 尝试使用 wkhtmltopdf
            try:
                import pdfkit
                
                pdf_path = self.export_dir / f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                pdfkit.from_string(html_content, str(pdf_path))
                
                logger.info(f"PDF 导出成功 (wkhtmltopdf): {pdf_path}")
                return pdf_path
            
            except Exception as e:
                logger.error(f"PDF 导出失败: 需要安装 weasyprint 或 wkhtmltopdf")
                raise RuntimeError("PDF 导出需要安装 weasyprint 或 wkhtmltopdf") from e
    
    async def save_document(
        self,
        doc_id: Optional[str],
        title: str,
        content: str,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        保存文档
        
        Args:
            doc_id: 文档 ID（更新时使用）
            title: 文档标题
            content: Markdown 内容
            tags: 标签列表
        
        Returns:
            文档信息
        """
        if tags is None:
            tags = []
        
        now = datetime.now().isoformat()
        
        # 创建或更新
        if doc_id:
            # 更新现有文档
            doc_path = self.documents_dir / f"{doc_id}.json"
            
            if not doc_path.exists():
                raise ValueError(f"文档不存在: {doc_id}")
            
            # 读取现有文档
            with open(doc_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
            
            # 更新字段
            document["title"] = title
            document["content"] = content
            document["tags"] = tags
            document["updated_at"] = now
        
        else:
            # 创建新文档
            doc_id = str(uuid.uuid4())
            
            document = {
                "id": doc_id,
                "title": title,
                "content": content,
                "tags": tags,
                "created_at": now,
                "updated_at": now
            }
        
        # 保存
        doc_path = self.documents_dir / f"{doc_id}.json"
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
        
        logger.info(f"文档已保存: {doc_id} ({title})")
        
        return document
    
    async def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取文档列表
        
        Args:
            limit: 最大返回数量
            offset: 偏移量
            tag: 标签过滤
        
        Returns:
            文档列表
        """
        documents = []
        
        # 读取所有文档
        for doc_file in self.documents_dir.glob("*.json"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    doc = json.load(f)
                    documents.append(doc)
            except Exception as e:
                logger.warning(f"读取文档失败 {doc_file}: {e}")
        
        # 按更新时间排序
        documents.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        # 标签过滤
        if tag:
            documents = [d for d in documents if tag in d.get("tags", [])]
        
        # 分页
        documents = documents[offset:offset + limit]
        
        return documents
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            doc_id: 文档 ID
        
        Returns:
            文档信息或 None
        """
        doc_path = self.documents_dir / f"{doc_id}.json"
        
        if not doc_path.exists():
            return None
        
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取文档失败: {e}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档 ID
        
        Returns:
            是否成功
        """
        doc_path = self.documents_dir / f"{doc_id}.json"
        
        if not doc_path.exists():
            return False
        
        try:
            doc_path.unlink()
            logger.info(f"文档已删除: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    def get_export_dir(self) -> Path:
        """获取导出目录"""
        return self.export_dir
    
    def _get_theme_css(self, theme: str = "default") -> str:
        """
        获取主题 CSS
        
        Args:
            theme: 主题名称
        
        Returns:
            CSS 样式
        """
        # 默认主题（GitHub 风格）
        if theme == "default" or theme == "github":
            return """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #24292e;
    background: #ffffff;
    margin: 0;
    padding: 20px;
}

.markdown-container {
    max-width: 960px;
    margin: 0 auto;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
}

.markdown-body h1 {
    font-size: 2em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
}

.markdown-body h2 {
    font-size: 1.5em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 0.3em;
}

.markdown-body code {
    background: #f6f8fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 85%;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    overflow: auto;
}

.markdown-body pre code {
    background: none;
    padding: 0;
}

.markdown-body blockquote {
    border-left: 4px solid #dfe2e5;
    padding: 0 1em;
    color: #6a737d;
    margin: 0 0 16px 0;
}

.markdown-body table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 16px;
}

.markdown-body table th, .markdown-body table td {
    border: 1px solid #dfe2e5;
    padding: 6px 13px;
}

.markdown-body table tr {
    background: #ffffff;
    border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
    background: #f6f8fa;
}

.toc {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 6px;
    margin-bottom: 24px;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc li {
    margin: 4px 0;
}

.toc a {
    color: #0366d6;
    text-decoration: none;
}

.toc a:hover {
    text-decoration: underline;
}
"""
        
        # 深色主题
        elif theme == "dark":
            return """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #c9d1d9;
    background: #0d1117;
    margin: 0;
    padding: 20px;
}

.markdown-container {
    max-width: 960px;
    margin: 0 auto;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
    color: #f0f6fc;
}

.markdown-body h1, .markdown-body h2 {
    border-bottom: 1px solid #21262d;
    padding-bottom: 0.3em;
}

.markdown-body code {
    background: #161b22;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 85%;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
    background: #161b22;
    padding: 16px;
    border-radius: 6px;
    overflow: auto;
}

.markdown-body blockquote {
    border-left: 4px solid #30363d;
    padding: 0 1em;
    color: #8b949e;
    margin: 0 0 16px 0;
}

.markdown-body table th, .markdown-body table td {
    border: 1px solid #30363d;
    padding: 6px 13px;
}

.markdown-body table tr {
    background: #0d1117;
    border-top: 1px solid #21262d;
}

.markdown-body table tr:nth-child(2n) {
    background: #161b22;
}

.toc {
    background: #161b22;
    padding: 16px;
    border-radius: 6px;
    margin-bottom: 24px;
}

.toc a {
    color: #58a6ff;
    text-decoration: none;
}
"""
        
        # 其他主题返回默认
        return self._get_theme_css("default")

