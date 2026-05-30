#!/usr/bin/env python3
"""
AI-Edu-for-Kids 快速回测验证脚本

验证范围:
- 文件完整性检查
- Python 代码语法检查
- 服务定义验证
- API 路由验证
- 数据模型验证
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 统计信息
stats = {
    'total_tests': 0,
    'passed_tests': 0,
    'failed_tests': [],
    'warnings': []
}

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_test(name, passed, details=""):
    """打印测试结果"""
    global stats
    stats['total_tests'] += 1
    
    icon = "✅" if passed else "❌"
    print(f"\n{icon} {name}")
    
    if details:
        indent = "   "
        print(f"{indent}{details}")
    
    if passed:
        stats['passed_tests'] += 1
    else:
        stats['failed_tests'].append({
            'name': name,
            'details': details
        })

def check_file_exists(file_path, description=""):
    """检查文件是否存在"""
    exists = Path(file_path).exists()
    print_test(
        f"检查文件：{Path(file_path).name}",
        exists,
        f"{description}\n路径：{file_path}" if description else file_path
    )
    return exists

def check_python_syntax(file_path):
    """检查 Python 文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        print_test(f"Python 语法检查：{Path(file_path).name}", True)
        return True
    except SyntaxError as e:
        print_test(
            f"Python 语法检查：{Path(file_path).name}",
            False,
            f"语法错误在第 {e.lineno} 行：{e.msg}"
        )
        return False
    except Exception as e:
        print_test(
            f"Python 语法检查：{Path(file_path).name}",
            False,
            str(e)
        )
        return False

def check_service_definition(service_file, class_name, methods=None):
    """检查服务类定义"""
    try:
        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查类定义
        has_class = f"class {class_name}" in content
        
        # 检查方法
        missing_methods = []
        if methods:
            for method in methods:
                if f"def {method}" not in content:
                    missing_methods.append(method)
        
        success = has_class and len(missing_methods) == 0
        
        details = []
        if has_class:
            details.append(f"✅ 类 {class_name} 已定义")
        else:
            details.append(f"❌ 类 {class_name} 未找到")
        
        if missing_methods:
            details.append(f"❌ 缺少方法：{', '.join(missing_methods)}")
        elif methods:
            details.append(f"✅ 所有必需方法已实现 ({len(methods)}个)")
        
        print_test(
            f"服务定义检查：{class_name}",
            success,
            "\n".join(details)
        )
        
        return success
        
    except Exception as e:
        print_test(
            f"服务定义检查：{class_name}",
            False,
            str(e)
        )
        return False

def check_api_routes(route_file, endpoints=None):
    """检查 API 路由定义"""
    try:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 router 定义
        has_router = "APIRouter" in content
        
        # 检查端点
        found_endpoints = []
        if endpoints:
            for endpoint in endpoints:
                if endpoint in content:
                    found_endpoints.append(endpoint)
        
        success = has_router
        
        details = [
            f"{'✅' if has_router else '❌'} APIRouter {'已定义' if has_router else '未找到'}",
            f"📍 找到 {len(found_endpoints)}/{len(endpoints) if endpoints else '?'} 个端点"
        ]
        
        if endpoints and found_endpoints:
            details.append(f"端点列表：{', '.join(found_endpoints[:5])}")
        
        print_test(
            f"API 路由检查：{Path(route_file).name}",
            success,
            "\n".join(details)
        )
        
        return success
        
    except Exception as e:
        print_test(
            f"API 路由检查：{Path(route_file).name}",
            False,
            str(e)
        )
        return False

def check_database_connection(db_path):
    """检查数据库连接"""
    try:
        from sqlalchemy import create_engine, inspect
        
        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        ai_edu_tables = [t for t in tables if t.startswith('ai_edu_')]
        
        success = len(ai_edu_tables) >= 4
        
        print_test(
            "数据库连接检查",
            success,
            f"找到 {len(ai_edu_tables)} 张 AI-Edu 表:\n{', '.join(ai_edu_tables)}"
        )
        
        return success
        
    except Exception as e:
        print_test(
            "数据库连接检查",
            False,
            str(e)
        )
        return False

def check_data_integrity(db_path):
    """检查数据完整性"""
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(f"sqlite:///{db_path}")
        
        with engine.connect() as conn:
            # 检查模块数量
            result = conn.execute(text("SELECT COUNT(*) FROM ai_edu_modules"))
            module_count = result.scalar()
            
            # 检查课时数量
            result = conn.execute(text("SELECT COUNT(*) FROM ai_edu_lessons"))
            lesson_count = result.scalar()
        
        success = module_count > 0 and lesson_count > 0
        
        print_test(
            "数据完整性检查",
            success,
            f"模块：{module_count} 条\n课时：{lesson_count} 条"
        )
        
        return success
        
    except Exception as e:
        print_test(
            "数据完整性检查",
            False,
            str(e)
        )
        return False

def main():
    """主函数"""
    print_header("AI-Edu-for-Kids 快速回测验证")
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========== 第一组：文件完整性检查 ==========
    print_header("第一组：文件完整性检查")
    
    project_root = Path(__file__).parent.parent
    
    # 后端服务文件
    check_file_exists(
        project_root / "backend" / "services" / "ai_edu_progress_service.py",
        "学习进度服务核心文件"
    )
    
    check_file_exists(
        project_root / "backend" / "routes" / "ai_edu_progress_routes.py",
        "学习进度 API 路由文件"
    )
    
    # 前端文件
    check_file_exists(
        project_root / "src" / "app" / "models" / "ai-edu.models.ts",
        "TypeScript 数据模型"
    )
    
    check_file_exists(
        project_root / "src" / "app" / "core" / "services" / "ai-edu.service.ts",
        "Angular 服务层"
    )
    
    check_file_exists(
        project_root / "src" / "app" / "components" / "ai-edu-course-list" / "ai-edu-course-list.component.ts",
        "课程列表组件"
    )
    
    # 部署脚本
    check_file_exists(
        project_root / "scripts" / "quick_deploy_ai_edu_standalone.py",
        "快速部署脚本"
    )
    
    check_file_exists(
        project_root / "scripts" / "simple_import_ai_edu.py",
        "简化导入工具"
    )
    
    check_file_exists(
        project_root / "scripts" / "verify_ai_edu_database.py",
        "数据库验证工具"
    )
    
    # ========== 第二组：Python 代码语法检查 ==========
    print_header("第二组：Python 代码语法检查")
    
    # 服务层语法检查
    check_python_syntax(project_root / "backend" / "services" / "ai_edu_progress_service.py")
    
    # 路由层语法检查
    check_python_syntax(project_root / "backend" / "routes" / "ai_edu_progress_routes.py")
    
    # 部署脚本语法检查
    check_python_syntax(project_root / "scripts" / "quick_deploy_ai_edu_standalone.py")
    check_python_syntax(project_root / "scripts" / "simple_import_ai_edu.py")
    check_python_syntax(project_root / "scripts" / "verify_ai_edu_database.py")
    
    # ========== 第三组：服务定义验证 ==========
    print_header("第三组：服务定义验证")
    
    check_service_definition(
        project_root / "backend" / "services" / "ai_edu_progress_service.py",
        "AIEduProgressService",
        ["report_progress", "get_user_progress", "complete_lesson_and_award_points"]
    )
    
    # ========== 第四组：API 路由验证 ==========
    print_header("第四组：API 路由验证")
    
    check_api_routes(
        project_root / "backend" / "routes" / "ai_edu_progress_routes.py",
        ["/progress", "/progress/statistics", "/modules"]
    )
    
    # ========== 第五组：数据库验证 ==========
    print_header("第五组：数据库验证")
    
    db_path = project_root / "data" / "ai_edu_standalone.db"
    check_database_connection(db_path)
    check_data_integrity(db_path)
    
    # ========== 第六组：API 服务状态检查 ==========
    print_header("第六组：API 服务状态检查")
    
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print_test(
            "后端服务健康检查",
            response.status_code == 200,
            f"状态码：{response.status_code}"
        )
    except:
        print_test(
            "后端服务健康检查",
            False,
            "服务未启动或无法连接 (http://localhost:8000)"
        )
    
    # ========== 生成回测报告 ==========
    print_header("回测验证完成")
    
    passed = stats['passed_tests']
    total = stats['total_tests']
    failed = len(stats['failed_tests'])
    
    print(f"\n总测试数：{total}")
    print(f"通过：{passed} ✅")
    print(f"失败：{failed} ❌")
    print(f"通过率：{(passed/total*100):.1f}%\n")
    
    if stats['failed_tests']:
        print("\n失败详情:")
        for i, test in enumerate(stats['failed_tests'], 1):
            print(f"\n{i}. {test['name']}")
            if test['details']:
                print(f"   {test['details']}")
    
    # 生成 JSON 报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(passed/total*100, 2) if total > 0 else 0
        },
        'test_results': stats['failed_tests'],
        'status': 'PASSED' if failed == 0 else 'FAILED'
    }
    
    # 保存报告
    report_dir = project_root / "backtest_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = report_dir / f"ai_edu_backtest_{timestamp}.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 回测报告已保存：{report_path}")
    
    # 返回退出码
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
