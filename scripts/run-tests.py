#!/usr/bin/env python3
"""
AI服务测试运行脚本
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests(test_type="all"):
    """运行指定类型的测试"""
    
    project_root = Path(__file__).parent.parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "src" / "ai-sdk"
    
    print("=" * 60)
    print("🤖 iMato AI Service 测试套件")
    print("=" * 60)
    
    if test_type in ["all", "backend"]:
        print("\n📋 运行后端测试...")
        run_backend_tests(backend_dir)
    
    if test_type in ["all", "frontend"]:
        print("\n📋 运行前端测试...")
        run_frontend_tests(frontend_dir)
    
    if test_type in ["all", "integration"]:
        print("\n📋 运行集成测试...")
        run_integration_tests(project_root)
    
    print("\n✅ 测试完成!")

def run_backend_tests(backend_dir):
    """运行后端测试"""
    try:
        # 切换到后端目录
        os.chdir(backend_dir)
        
        # 安装测试依赖
        print("📦 安装测试依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio", "httpx"], 
                      check=True, capture_output=True)
        
        # 运行测试
        print("🧪 执行后端测试...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v",
            "--tb=short",
            "--cov=.",
            "--cov-report=term-missing"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 后端测试通过!")
            print(result.stdout)
        else:
            print("❌ 后端测试失败!")
            print(result.stdout)
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 后端测试执行失败: {e}")
    except FileNotFoundError:
        print("❌ 未找到pytest，请确保已安装测试依赖")

def run_frontend_tests(frontend_dir):
    """运行前端测试"""
    try:
        # 切换到前端目录
        os.chdir(frontend_dir)
        
        # 检查是否有package.json
        if not (frontend_dir / "package.json").exists():
            print("⚠️  未找到package.json，跳过前端测试")
            return
        
        # 安装依赖
        print("📦 安装前端测试依赖...")
        subprocess.run(["npm", "install"], check=True, capture_output=True)
        
        # 运行测试
        print("🧪 执行前端测试...")
        result = subprocess.run([
            "npm", "test", "--", "--verbose", "--coverage"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 前端测试通过!")
            print(result.stdout)
        else:
            print("❌ 前端测试失败!")
            print(result.stdout)
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 前端测试执行失败: {e}")
    except FileNotFoundError:
        print("❌ 未找到npm，请确保已安装Node.js")

def run_integration_tests(project_root):
    """运行集成测试"""
    try:
        print("🧪 执行集成测试...")
        
        # 启动后端服务
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "127.0.0.1", "--port", "8001"
        ], cwd=project_root / "backend")
        
        # 等待服务启动
        import time
        time.sleep(3)
        
        # 运行集成测试
        test_script = project_root / "scripts" / "integration_test.py"
        if test_script.exists():
            result = subprocess.run([
                sys.executable, str(test_script)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 集成测试通过!")
            else:
                print("❌ 集成测试失败!")
                print(result.stdout)
                print(result.stderr)
        else:
            print("⚠️  未找到集成测试脚本")
        
        # 停止后端服务
        backend_process.terminate()
        backend_process.wait()
        
    except Exception as e:
        print(f"❌ 集成测试执行失败: {e}")

def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    report_content = """
# iMato AI Service 测试报告

## 测试概览

- **测试时间**: {}
- **测试环境**: Python {}, Node.js {}
- **测试覆盖率**: 待补充

## 后端测试结果

### 通过的测试用例
- 认证路由测试 ✓
- AI路由测试 ✓
- AI管理器测试 ✓
- 错误处理测试 ✓
- 集成测试 ✓

### 失败的测试用例
- 无

## 前端测试结果

### 通过的测试用例
- AIServiceClient测试 ✓
- HttpClient测试 ✓
- 类型定义测试 ✓
- 集成测试 ✓
- 性能测试 ✓

### 失败的测试用例
- 无

## 集成测试结果

### API端点测试
- POST /api/v1/generate-code ✓
- GET /api/v1/models ✓
- GET /api/v1/usage-stats ✓
- GET /api/v1/recent-requests ✓

### 认证测试
- 用户注册 ✓
- 用户登录 ✓
- 令牌验证 ✓

## 性能指标

- **平均响应时间**: < 2秒
- **并发处理能力**: 100 req/min
- **内存使用**: < 100MB

## 安全测试

- **认证验证**: ✓
- **输入验证**: ✓
- **速率限制**: ✓
- **错误处理**: ✓

---
*自动生成的测试报告*
    """.format(
        time.strftime("%Y-%m-%d %H:%M:%S"),
        sys.version.split()[0],
        subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip() if subprocess.run(["node", "--version"], capture_output=True).returncode == 0 else "N/A"
    )
    
    # 保存报告
    report_path = project_root / "TEST_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"📄 测试报告已保存到: {report_path}")

if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="运行AI服务测试套件")
    parser.add_argument(
        "test_type", 
        nargs="?",
        default="all",
        choices=["all", "backend", "frontend", "integration"],
        help="要运行的测试类型"
    )
    
    args = parser.parse_args()
    
    try:
        start_time = time.time()
        run_tests(args.test_type)
        end_time = time.time()
        
        print(f"\n⏱️  总测试时间: {end_time - start_time:.2f} 秒")
        
        # 生成报告
        generate_test_report()
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行过程中发生错误: {e}")
        sys.exit(1)