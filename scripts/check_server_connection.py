"""
服务器连接检查工具

用于检查后端服务的连接状态，包括:
1. HTTP 服务可达性
2. 健康检查端点响应
3. WebSocket 连接测试
4. 数据库连接状态
"""

import httpx
import asyncio
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_header(msg):
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")


class ServerConnectionChecker:
    """服务器连接检查器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 5.0  # 超时时间 (秒)
        
    async def check_http_connection(self) -> bool:
        """检查 HTTP 连接"""
        print_header("\n📡 检查 HTTP 连接...")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url)
                if response.status_code == 200:
                    print_success(f"HTTP 服务运行正常 - {self.base_url}")
                    print_info(f"响应内容：{response.json()}")
                    return True
                else:
                    print_error(f"HTTP 服务响应异常：{response.status_code}")
                    return False
        except httpx.ConnectError as e:
            print_error(f"无法连接到 HTTP 服务：{e}")
            return False
        except Exception as e:
            print_error(f"HTTP 连接检查失败：{e}")
            return False
    
    async def check_health_endpoint(self) -> bool:
        """检查健康检查端点"""
        print_header("\n🏥 检查健康检查端点 (/health)...")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    print_success("健康检查端点响应正常")
                    print_info(f"健康状态：{response.json()}")
                    return True
                else:
                    print_error(f"健康检查端点响应异常：{response.status_code}")
                    return False
        except httpx.ConnectError as e:
            print_error(f"健康检查端点无法访问：{e}")
            return False
        except Exception as e:
            print_error(f"健康检查失败：{e}")
            return False
    
    async def check_api_version(self) -> bool:
        """检查 API 版本信息"""
        print_header("\n📋 检查 API 版本...")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/version")
                if response.status_code == 200:
                    print_success("API 版本信息获取成功")
                    print_info(f"版本详情：{response.json()}")
                    return True
                else:
                    print_warning(f"API 版本端点响应：{response.status_code}")
                    return False
        except Exception as e:
            print_warning(f"API 版本检查失败 (可能未实现): {e}")
            return False
    
    async def check_database_connection(self) -> bool:
        """检查数据库连接 (如果支持)"""
        print_header("\n🗄️  检查数据库连接...")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/v1/health/database")
                if response.status_code == 200:
                    print_success("数据库连接正常")
                    print_info(f"数据库状态：{response.json()}")
                    return True
                elif response.status_code == 404:
                    print_warning("数据库检查端点不存在 (可选)")
                    return True
                else:
                    print_error(f"数据库检查异常：{response.status_code}")
                    return False
        except Exception as e:
            print_warning(f"数据库连接检查失败：{e}")
            return False
    
    async def check_websocket_connection(self) -> bool:
        """检查 WebSocket 连接"""
        print_header("\n🔌 检查 WebSocket 连接...")
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        try:
            # 使用 websockets 库
            import websockets
            async with websockets.connect(f"{ws_url}/ws", open_timeout=self.timeout) as websocket:
                await websocket.send('{"type": "ping"}')
                response = await websocket.recv()
                print_success(f"WebSocket 连接正常 - {ws_url}")
                print_info(f"响应：{response}")
                return True
        except ImportError:
            print_warning("websockets 库未安装，跳过 WebSocket 检查")
            return False
        except Exception as e:
            print_warning(f"WebSocket 连接测试失败：{e}")
            return False
    
    async def run_full_check(self) -> Dict[str, Any]:
        """运行完整检查"""
        print_header("=" * 80)
        print_header("  服务器连接状态检查")
        print_header("=" * 80)
        print_info(f"目标服务器：{self.base_url}")
        print_info(f"超时设置：{self.timeout}秒\n")
        
        results = {
            "http_connection": False,
            "health_endpoint": False,
            "api_version": False,
            "database_connection": False,
            "websocket_connection": False,
        }
        
        # 执行检查
        results["http_connection"] = await self.check_http_connection()
        results["health_endpoint"] = await self.check_health_endpoint()
        results["api_version"] = await self.check_api_version()
        results["database_connection"] = await self.check_database_connection()
        results["websocket_connection"] = await self.check_websocket_connection()
        
        # 汇总结果
        print_header("\n" + "=" * 80)
        print_header("  检查结果汇总")
        print_header("=" * 80)
        
        total_checks = len(results)
        passed_checks = sum(results.values())
        
        for check_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            check_display = check_name.replace("_", " ").title()
            print(f"{check_display}: {status}")
        
        print(f"\n总计：{passed_checks}/{total_checks} 检查通过")
        
        if passed_checks == total_checks:
            print_success("🎉 所有检查项通过！服务器连接正常")
            return {"success": True, "results": results}
        elif passed_checks >= total_checks * 0.6:
            print_warning("⚠️  大部分检查通过，但部分功能可能不可用")
            return {"success": True, "results": results, "partial": True}
        else:
            print_error("❌ 服务器连接存在严重问题")
            self._print_troubleshooting_tips()
            return {"success": False, "results": results}
    
    def _print_troubleshooting_tips(self):
        """打印故障排查建议"""
        print_header("\n💡 故障排查建议:")
        print("-" * 80)
        print("1. 确认后端服务已启动:")
        print("   cd g:\\iMato\\backend")
        print("   python main_ai_edu_full.py")
        print("\n2. 检查端口是否被占用:")
        print("   netstat -ano | findstr :8000")
        print("\n3. 检查防火墙设置:")
        print("   确保端口 8000 未被防火墙阻止")
        print("\n4. 查看后端日志:")
        print("   检查 backend/logs/ 目录下的日志文件")
        print("-" * 80)


async def main():
    """主函数"""
    # 从命令行参数获取 URL，默认使用 localhost:8000
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    checker = ServerConnectionChecker(base_url)
    result = await checker.run_full_check()
    
    # 退出码
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    asyncio.run(main())
