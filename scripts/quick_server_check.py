"""
快速服务器连接检查工具

轻量级版本，仅检查基本的 HTTP 连接和健康端点
"""

import requests
import sys
from typing import Dict, Any

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


def check_server_connection(base_url: str = "http://localhost:8000", timeout: int = 5) -> Dict[str, Any]:
    """
    快速检查服务器连接
    
    Args:
        base_url: 服务器基础 URL
        timeout: 超时时间 (秒)
    
    Returns:
        检查结果字典
    """
    print_header("=" * 80)
    print_header("  服务器快速连接检查")
    print_header("=" * 80)
    print_info(f"目标服务器：{base_url}")
    print_info(f"超时设置：{timeout}秒\n")
    
    results = {
        "root_endpoint": False,
        "health_endpoint": False,
    }
    
    # 1. 检查根端点
    print_header("\n📡 检查根端点 (/)...")
    try:
        response = requests.get(base_url, timeout=timeout)
        if response.status_code == 200:
            print_success(f"根端点响应正常 - {base_url}")
            print_info(f"服务信息：{response.json()}")
            results["root_endpoint"] = True
        else:
            print_error(f"根端点响应异常：{response.status_code}")
    except requests.exceptions.ConnectionError:
        print_error(f"无法连接到服务器 - {base_url}")
        print_warning("服务器可能未启动")
    except Exception as e:
        print_error(f"根端点检查失败：{e}")
    
    # 2. 检查健康端点
    print_header("\n🏥 检查健康检查端点 (/health)...")
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
        if response.status_code == 200:
            print_success("健康检查端点响应正常")
            print_info(f"健康状态：{response.json()}")
            results["health_endpoint"] = True
        else:
            print_error(f"健康检查端点响应异常：{response.status_code}")
    except requests.exceptions.ConnectionError:
        print_error("健康检查端点无法访问")
    except Exception as e:
        print_error(f"健康检查失败：{e}")
    
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
    elif passed_checks > 0:
        print_warning("⚠️  部分检查通过，服务器可能存在配置问题")
        return {"success": True, "results": results, "partial": True}
    else:
        print_error("❌ 服务器未运行或无法访问")
        print_troubleshooting_tips(base_url)
        return {"success": False, "results": results}


def print_troubleshooting_tips(base_url: str):
    """打印故障排查建议"""
    port = base_url.split(":")[-1].rstrip("/")
    
    print_header("\n💡 故障排查建议:")
    print("-" * 80)
    print("1. 确认后端服务已启动:")
    print("   cd g:\\iMato\\backend")
    print("   python main_ai_edu_full.py")
    print("\n2. 检查端口是否被占用:")
    print(f"   netstat -ano | findstr :{port}")
    print("\n3. 检查防火墙设置:")
    print(f"   确保端口 {port} 未被防火墙阻止")
    print("\n4. 查看后端日志:")
    print("   检查 backend/logs/ 目录下的日志文件")
    print("\n5. 检查配置文件:")
    print("   确认 backend/config/settings.py 中的 PORT 配置")
    print("-" * 80)


def main():
    """主函数"""
    # 从命令行参数获取 URL，默认使用 localhost:8000
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    result = check_server_connection(base_url)
    
    # 退出码
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
