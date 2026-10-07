#!/usr/bin/env python3
"""
简单的 HTTP 静态服务器，托管 Angular 构建产物
- /assets/*, /api/* → 直接返回文件或代理到后端
- 其他路径 → 返回 index.html (SPA fallback)
"""

import http.server
import socketserver
import os
import urllib.request
import urllib.parse
import sys
from pathlib import Path

PORT = 8080
FRONTEND_DIR = Path(__file__).parent.parent / "dist" / "imatuproject"
BACKEND_URL = "http://localhost:8000"


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        # 代理 API 请求到 Python 后端
        if self.path.startswith("/api/") or self.path.startswith("/health") or \
           self.path.startswith("/metrics") or self.path.startswith("/registry") or \
           self.path.startswith("/ws"):
            return self._proxy_to_backend()

        # 移除查询字符串
        path_no_query = urllib.parse.urlparse(self.path).path
        # 文件请求 - 直接返回
        file_path = FRONTEND_DIR / path_no_query.lstrip("/")
        if file_path.is_file():
            return super().do_GET()

        # SPA fallback - 返回 index.html
        self.path = "/index.html"
        return super().do_GET()

    # 【P1 修复 #2】同时代理 OPTIONS / POST / PUT / DELETE / PATCH。
    #   SimpleHTTPRequestHandler 只默认处理 GET / HEAD，其它动词直接 501。
    #   浏览器跨域 POST 之前会先发 OPTIONS 预检；之前 spa-server 会让 501，
    #   导致 Browser agent 端到端验证 CORS 时看不到真正的预检结果。
    def do_OPTIONS(self):
        # 【P1 修复 #2】预检直接在本地响应，不必打到后端。
        # 后端 FastAPI 对预检返回不标准；浏览器只需要 ACAO/ACAM/ACAH 三个头即可通过。
        return self._serve_preflight()

    def do_POST(self):
        if self.path.startswith("/api/") or self.path.startswith("/health") or \
           self.path.startswith("/metrics") or self.path.startswith("/registry") or \
           self.path.startswith("/ws"):
            return self._proxy_to_backend()
        return self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        return self._proxy_or_405()

    def do_DELETE(self):
        return self._proxy_or_405()

    def do_PATCH(self):
        return self._proxy_or_405()

    def do_HEAD(self):
        # 【P4-C 修复】HEAD 必须返回真实状态码，不要被 SPA fallback 吃掉。
        #   Angular 的 detectUnityBuild() 用 HEAD 探测 Unity WebGL 构建，
        #   如果不存在必须得到 404 才能触发占位 UI。
        #   否则所有 HEAD 都会 fall through 到 index.html 返回 200，前端误判成功。
        if self.path.startswith("/api/") or self.path.startswith("/health") or \
           self.path.startswith("/metrics") or self.path.startswith("/registry") or \
           self.path.startswith("/ws"):
            return self._proxy_to_backend()
        path_no_query = urllib.parse.urlparse(self.path).path
        file_path = FRONTEND_DIR / path_no_query.lstrip("/")
        if file_path.is_file():
            return super().do_HEAD()
        # 资源不存在 — 返回 404（不退回 index.html）
        return self.send_error(404, "File not found")

    def _proxy_or_405(self):
        if self.path.startswith("/api/") or self.path.startswith("/health") or \
           self.path.startswith("/metrics") or self.path.startswith("/registry") or \
           self.path.startswith("/ws"):
            return self._proxy_to_backend()
        return self.send_error(405, "Method Not Allowed")

    def _serve_preflight(self):
        """直接在本地响应 CORS 预检，不必打到后端"""
        self.send_response(204)
        origin = self.headers.get("Origin", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, Authorization, X-Requested-With, Accept, *")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _proxy_to_backend(self):
        target_url = BACKEND_URL + self.path
        try:
            # 【P1 修复 #2】重建请求并转发 method / headers / body
            parsed = urllib.parse.urlparse(target_url)
            body = None
            content_length = int(self.headers.get("Content-Length", 0) or 0)
            if content_length > 0:
                body = self.rfile.read(content_length)
            req = urllib.request.Request(
                target_url,
                data=body,
                method=self.command,
                headers={k: v for k, v in self.headers.items()
                         if k.lower() not in ("host", "content-length")},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.send_response(resp.status)
                forwarded = False
                for key, val in resp.headers.items():
                    if key.lower() in ("transfer-encoding", "connection"):
                        continue
                    self.send_header(key, val)
                    forwarded = True
                # 【P1 修复 #2】若后端未返回 ACAO，回填一层方便浏览器代理层调试
                if not any(k.lower() == "access-control-allow-origin"
                           for k in resp.headers.keys()):
                    origin = self.headers.get("Origin", "")
                    if origin:
                        self.send_header("Access-Control-Allow-Origin", origin)
                        self.send_header("Vary", "Origin")
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, f"Backend proxy error: {e}")

    def log_message(self, format, *args):
        # 简洁日志格式
        print(f"[{self.log_date_time_string()}] {format % args}", flush=True)


if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    print(f"SPA Server: serving {FRONTEND_DIR} at http://localhost:{PORT}")
    print(f"Backend proxy target: {BACKEND_URL}")
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), SPAHandler) as httpd:
        httpd.serve_forever()