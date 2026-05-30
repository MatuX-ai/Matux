"""
AI-Edu 前后端联调测试启动器

1. 检查后端服务是否运行
2. 启动静态文件服务器
3. 自动打开浏览器
"""

import http.server
import socketserver
import webbrowser
import threading
import time
import requests
from pathlib import Path

PORT = 8080
TEST_FILE = Path(__file__).parent / 'ai_edu_integration_test.html'
BACKEND_URL = 'http://localhost:8000'

def check_backend():
    """检查后端服务是否运行"""
    print("🔍 检查后端服务状态...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"⚠️  后端服务响应异常：{response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 后端服务未启动！")
        print("\n💡 请先启动后端服务:")
        print("   cd g:\\iMato\\backend")
        print("   python main_ai_edu_full.py")
        return False

def start_http_server():
    """启动 HTTP 服务器"""
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n🌐 测试页面地址：http://localhost:{PORT}")
        print(f"📄 测试文件：{TEST_FILE}")
        print("\n按 Ctrl+C 停止服务器")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n服务器已停止")

def open_browser():
    """延迟打开浏览器"""
    time.sleep(1)  # 等待服务器启动
    webbrowser.open(f'http://localhost:{PORT}')
    print(f"\n🚀 已打开浏览器")

if __name__ == '__main__':
    print("=" * 80)
    print("  AI-Edu-for-Kids 前后端联调测试")
    print("=" * 80)
    
    # 切换到测试目录
    import os
    os.chdir(Path(__file__).parent)
    
    # 检查后端服务
    if not check_backend():
        print("\n⚠️  测试中止，请先启动后端服务")
        exit(1)
    
    # 启动 HTTP 服务器（在后台）
    server_thread = threading.Thread(target=start_http_server, daemon=True)
    server_thread.start()
    
    # 打开浏览器
    open_browser()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n退出测试")
