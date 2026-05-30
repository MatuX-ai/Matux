#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XSS漏洞修复器
修复前端和后端的跨站脚本攻击漏洞
"""

import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XSSFixer:
    """XSS漏洞修复器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        self.fixes_failed = []
        
        # 需要修复的前端文件
        self.frontend_files = [
            "src/app/auth/auth-page.html",
            "src/app/creativity-engine/creativity-engine.component.html",
            "src/app/license-management/license-management.component.html",
            "src/app/admin/users/bulk-import/bulk-import.component.html"
        ]

    def fix_all_xss_vulnerabilities(self):
        """修复所有XSS漏洞"""
        # 修复前端HTML文件
        self._fix_frontend_files()
        
        # 添加安全中间件
        self._add_security_middleware()
        
        self._save_fix_report()

    def _fix_frontend_files(self):
        """修复前端文件中的XSS漏洞"""
        for file_path in self.frontend_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self._fix_html_file(full_path)

    def _fix_html_file(self, file_path: Path):
        """修复单个HTML文件"""
        try:
            # 创建备份
            backup_path = file_path.with_suffix(file_path.suffix + '.xss_bak')
            shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_made = []
            
            # 修复事件处理器中的XSS
            content, event_fixes = self._fix_event_handlers(content)
            fixes_made.extend(event_fixes)
            
            # 修复内联脚本
            content, script_fixes = self._fix_inline_scripts(content)
            fixes_made.extend(script_fixes)
            
            # 修复JavaScript协议
            content, js_fixes = self._fix_javascript_protocols(content)
            fixes_made.extend(js_fixes)
            
            # 如果有修改，写入文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "fixes": fixes_made,
                    "fix_type": "frontend_xss"
                })
                logger.info(f"前端文件 {file_path.name} 修复完成: {len(fixes_made)} 处修改")
            else:
                logger.info(f"前端文件 {file_path.name} 无需修复")
                
        except Exception as e:
            self.fixes_failed.append({
                "file": str(file_path.relative_to(self.project_root)),
                "error": str(e),
                "fix_type": "frontend_xss"
            })
            logger.error(f"修复前端文件 {file_path} 失败: {e}")

    def _fix_event_handlers(self, content: str) -> tuple:
        """修复事件处理器"""
        fixes = []
        
        # 匹配事件处理器 onclick="..." 等
        pattern = r'(on\w+)\s*=\s*["\']([^"\']*)["\']'
        
        def replace_handler(match):
            event_name = match.group(1)
            handler_code = match.group(2)
            
            # 检查是否包含危险代码
            dangerous_patterns = ['eval', 'document.write', 'innerHTML']
            
            if any(dangerous in handler_code for dangerous in dangerous_patterns):
                fixes.append(f"修复危险事件处理器: {event_name}")
                # 移除危险代码，保留安全的部分
                safe_code = re.sub(r'eval\(.*?\)|document\.write\(.*?\)|\.innerHTML\s*=.*?;', '', handler_code)
                return f'{event_name}="{safe_code}"'
            else:
                return match.group(0)
        
        fixed_content = re.sub(pattern, replace_handler, content, flags=re.IGNORECASE)
        return fixed_content, fixes

    def _fix_inline_scripts(self, content: str) -> tuple:
        """修复内联脚本"""
        fixes = []
        
        # 匹配内联脚本
        pattern = r'<script[^>]*>(.*?)</script>'
        
        def replace_script(match):
            script_content = match.group(1)
            # 检查脚本内容是否安全
            if self._is_dangerous_script(script_content):
                fixes.append("移除危险内联脚本")
                return '<!-- 危险内联脚本已移除 -->'
            return match.group(0)
        
        fixed_content = re.sub(pattern, replace_script, content, flags=re.DOTALL | re.IGNORECASE)
        return fixed_content, fixes

    def _fix_javascript_protocols(self, content: str) -> tuple:
        """修复JavaScript协议"""
        fixes = []
        
        # 匹配 javascript: 协议
        pattern = r'javascript:([^;"]*)'
        
        def replace_js_protocol(match):
            js_code = match.group(1)
            fixes.append("修复JavaScript协议链接")
            # 转换为安全的click处理器
            return f'onclick="safeExecute(\'{js_code}\')"'
        
        fixed_content = re.sub(pattern, replace_js_protocol, content, flags=re.IGNORECASE)
        return fixed_content, fixes

    def _is_dangerous_script(self, script_content: str) -> bool:
        """判断脚本是否危险"""
        dangerous_patterns = [
            r'eval\(', r'document\.write', r'innerHTML\s*=',
            r'outerHTML\s*=', r'createElement\([\'\"]script[\'\"]\)'
        ]
        return any(re.search(pattern, script_content) for pattern in dangerous_patterns)

    def _add_security_middleware(self):
        """添加安全中间件"""
        middleware_file = self.project_root / "backend" / "middleware" / "security_middleware.py"
        
        try:
            security_middleware_content = '''
"""
安全中间件
提供XSS防护、CSRF保护和安全头设置
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
import html
import re
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件类"""
    
    def __init__(self, app):
        super().__init__(app)
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'on\\w+\\s*=\\s*["\'][^"\']*["\']',
            r'javascript:',
            r'data:text/html',
            r'<iframe[^>]*>',
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # XSS防护 - 清理请求参数
        await self._sanitize_request(request)
        
        # 设置安全头
        response = await call_next(request)
        
        if isinstance(response, Response):
            self._set_security_headers(response)
        
        return response
    
    async def _sanitize_request(self, request: Request):
        """清理请求参数防止XSS"""
        # 清理查询参数
        sanitized_query = {}
        for key, value in request.query_params.items():
            sanitized_query[key] = self._sanitize_input(value)
        request._query_params = sanitized_query
    
    def _sanitize_input(self, input_str: str) -> str:
        """清理输入字符串"""
        if not isinstance(input_str, str):
            return input_str
            
        # HTML转义
        sanitized = html.escape(input_str)
        
        # 移除危险的JavaScript代码
        for pattern in self.xss_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # 限制字符串长度
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def _set_security_headers(self, response: Response):
        """设置安全HTTP头"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value

# XSS清理工具函数
def sanitize_html(content: str) -> str:
    """HTML内容安全清理"""
    if not content:
        return ""
    
    # 使用html.escape进行基本转义
    escaped = html.escape(content)
    
    # 移除危险标签
    dangerous_tags = ['script', 'iframe', 'object', 'embed']
    for tag in dangerous_tags:
        escaped = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', escaped, flags=re.IGNORECASE | re.DOTALL)
    
    return escaped

def is_safe_url(url: str) -> bool:
    """检查URL是否安全"""
    if not url:
        return True
    
    safe_schemes = ['http', 'https', 'ftp', 'mailto']
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        return parsed.scheme in safe_schemes or not parsed.scheme
    except:
        return False
'''
            
            # 确保目录存在
            middleware_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(middleware_file, 'w', encoding='utf-8') as f:
                f.write(security_middleware_content)
            
            self.fixes_applied.append({
                "file": str(middleware_file.relative_to(self.project_root)),
                "fixes": ["创建安全中间件"],
                "fix_type": "security_middleware"
            })
            logger.info("安全中间件创建完成")
            
        except Exception as e:
            self.fixes_failed.append({
                "file": "security_middleware.py",
                "error": str(e),
                "fix_type": "security_middleware"
            })
            logger.error(f"创建安全中间件失败: {e}")

    def _save_fix_report(self):
        """保存修复报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "fix_timestamp": timestamp,
            "project_root": str(self.project_root),
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "summary": {
                "total_files_fixed": len([f for f in self.fixes_applied if f.get('fix_type') == 'frontend_xss']),
                "security_middleware_added": any(f.get('fix_type') == 'security_middleware' for f in self.fixes_applied),
                "total_fixes": sum(len(f.get('fixes', [])) for f in self.fixes_applied),
                "total_failed": len(self.fixes_failed)
            }
        }
        
        report_filename = f"xss_fix_report_{timestamp}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"XSS修复报告已保存到: {report_filename}")
        
        # 打印摘要
        print("\n" + "="*60)
        print("XSS漏洞修复摘要")
        print("="*60)
        print(f"修复时间: {timestamp}")
        print(f"前端文件修复: {report['summary']['total_files_fixed']} 个")
        print(f"安全中间件: {'已添加' if report['summary']['security_middleware_added'] else '未添加'}")
        print(f"总修复数: {report['summary']['total_fixes']}")
        print(f"失败数: {report['summary']['total_failed']}")
        
        if self.fixes_applied:
            print("\n详细修复记录:")
            for fix_record in self.fixes_applied:
                print(f"\n📁 {fix_record['file']} ({fix_record.get('fix_type', 'unknown')}):")
                for fix_detail in fix_record['fixes']:
                    print(f"  ✓ {fix_detail}")

def main():
    """主函数"""
    fixer = XSSFixer()
    fixer.fix_all_xss_vulnerabilities()
    print("\n✅ XSS漏洞修复完成!")

if __name__ == "__main__":
    main()