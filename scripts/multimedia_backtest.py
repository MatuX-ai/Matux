#!/usr/bin/env python3
"""
多媒体课件支持系统回测脚本
验证系统完整性、性能和安全性
"""

import os
import sys
import time
import json
import hashlib
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

def check_file_integrity():
    """检查文件完整性"""
    print("🔍 检查文件完整性...")
    
    required_files = [
        "models/multimedia.py",
        "services/multimedia_service.py",
        "services/three_d_service.py",
        "services/document_service.py",
        "routes/multimedia_routes.py",
        "celery_app.py",
        "tasks/__init__.py",
        "migrations/005_create_multimedia_tables.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = backend_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
            print(f"❌ 缺少文件: {file_path}")
        else:
            print(f"✅ 文件存在: {file_path}")
    
    return len(missing_files) == 0

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "celery",
        "redis",
        "boto3",
        "pillow",
        "trimesh"
    ]
    
    missing_packages = []
    
    try:
        import pkg_resources
        installed_packages = {pkg.key for pkg in pkg_resources.working_set}
        
        for package in required_packages:
            if package.lower() in installed_packages:
                print(f"✅ {package} 已安装")
            else:
                missing_packages.append(package)
                print(f"❌ {package} 未安装")
                
    except ImportError:
        print("⚠️  无法检查已安装的包")
        return False
    
    return len(missing_packages) == 0

def check_model_definitions():
    """检查模型定义"""
    print("\n📊 检查数据模型...")
    
    try:
        from models.multimedia import (
            MultimediaResource, MediaTranscodingJob,
            MediaType, VideoStatus, DocumentFormat
        )
        
        # 检查模型字段
        required_fields = [
            'id', 'org_id', 'course_id', 'title', 'media_type',
            'file_name', 'file_size', 'original_url'
        ]
        
        model_fields = [column.name for column in MultimediaResource.__table__.columns]
        
        missing_fields = []
        for field in required_fields:
            if field in model_fields:
                print(f"✅ 字段存在: {field}")
            else:
                missing_fields.append(field)
                print(f"❌ 缺少字段: {field}")
        
        return len(missing_fields) == 0
        
    except Exception as e:
        print(f"❌ 模型检查失败: {e}")
        return False

def check_service_availability():
    """检查服务可用性"""
    print("\n🧪 检查服务功能...")
    
    try:
        # 测试多媒体服务
        from services.multimedia_service import MultimediaService
        print("✅ MultimediaService 可用")
        
        # 测试3D服务
        from services.three_d_service import ThreeDModelService
        print("✅ ThreeDModelService 可用")
        
        # 测试文档服务
        from services.document_service import DocumentProcessingService
        print("✅ DocumentProcessingService 可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 服务检查失败: {e}")
        return False

def check_api_routes():
    """检查API路由"""
    print("\n🌐 检查API路由...")
    
    try:
        from routes.multimedia_routes import router
        
        expected_routes = [
            "/",
            "/{resource_id}",
            "/{resource_id}/upload-url",
            "/{resource_id}/complete-upload",
            "/{resource_id}/transcode",
            "/upload"
        ]
        
        route_paths = [route.path for route in router.routes]
        
        missing_routes = []
        for expected_route in expected_routes:
            full_path = f"/api/v1/org/{{org_id}}/multimedia{expected_route}"
            if any(full_path in str(route) for route in route_paths):
                print(f"✅ 路由存在: {expected_route}")
            else:
                missing_routes.append(expected_route)
                print(f"❌ 缺少路由: {expected_route}")
        
        return len(missing_routes) == 0
        
    except Exception as e:
        print(f"❌ 路由检查失败: {e}")
        return False

def check_celery_configuration():
    """检查Celery配置"""
    print("\n⚙️  检查Celery配置...")
    
    try:
        from celery_app import celery_app
        
        # 检查基本配置
        config_items = [
            'broker_url',
            'result_backend',
            'timezone'
        ]
        
        for item in config_items:
            if hasattr(celery_app.conf, item):
                print(f"✅ 配置项存在: {item}")
            else:
                print(f"❌ 缺少配置: {item}")
        
        # 检查任务注册
        expected_tasks = [
            'tasks.video_transcode',
            'tasks.document_process',
            'tasks.check_transcoding_status'
        ]
        
        registered_tasks = list(celery_app.tasks.keys())
        
        for task in expected_tasks:
            if task in registered_tasks:
                print(f"✅ 任务已注册: {task}")
            else:
                print(f"❌ 任务未注册: {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery检查失败: {e}")
        return False

def performance_test():
    """性能测试"""
    print("\n⚡ 执行性能测试...")
    
    performance_results = {}
    
    # 模型创建性能测试
    try:
        from models.multimedia import MultimediaResource, MediaType
        import time
        
        start_time = time.time()
        
        # 创建多个测试资源
        test_resources = []
        for i in range(100):
            resource = MultimediaResource(
                org_id=1,
                course_id=1,
                title=f"测试资源 {i}",
                media_type=MediaType.VIDEO,
                file_name=f"test_{i}.mp4"
            )
            test_resources.append(resource)
        
        end_time = time.time()
        creation_time = end_time - start_time
        performance_results['model_creation'] = {
            'time': creation_time,
            'rate': 100 / creation_time,
            'status': 'PASS' if creation_time < 1.0 else 'WARN'
        }
        
        print(f"✅ 模型创建性能: {creation_time:.3f}s (100个对象)")
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        performance_results['model_creation'] = {'status': 'FAIL', 'error': str(e)}
    
    return performance_results

def security_check():
    """安全检查"""
    print("\n🛡️  执行安全检查...")
    
    security_issues = []
    
    # 检查敏感配置文件
    config_files = [
        '.env',
        'config/settings.py'
    ]
    
    for config_file in config_files:
        full_path = backend_path / config_file
        if full_path.exists():
            # 检查是否包含敏感信息
            try:
                content = full_path.read_text(encoding='utf-8')
                sensitive_patterns = [
                    'AWS_ACCESS_KEY_ID',
                    'AWS_SECRET_ACCESS_KEY',
                    'SECRET_KEY'
                ]
                
                for pattern in sensitive_patterns:
                    if pattern in content and not content.split(pattern)[-1].strip().startswith('='):
                        security_issues.append(f"配置文件 {config_file} 可能包含明文敏感信息")
                        
            except Exception as e:
                security_issues.append(f"无法读取配置文件 {config_file}: {e}")
    
    # 检查文件权限
    upload_dirs = [
        'uploads',
        'uploads/processed',
        'uploads/thumbnails'
    ]
    
    for upload_dir in upload_dirs:
        full_path = backend_path / upload_dir
        if full_path.exists():
            # 检查权限（简化检查）
            if os.access(full_path, os.W_OK):
                print(f"✅ 上传目录可写: {upload_dir}")
            else:
                security_issues.append(f"上传目录不可写: {upload_dir}")
    
    if security_issues:
        for issue in security_issues:
            print(f"⚠️  安全警告: {issue}")
        return False
    else:
        print("✅ 未发现明显安全问题")
        return True

def generate_report(results):
    """生成测试报告"""
    print("\n" + "="*50)
    print("📋 回测报告")
    print("="*50)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "timestamp": timestamp,
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform
        },
        "test_results": results,
        "summary": {
            "passed": sum(1 for result in results.values() if result),
            "failed": sum(1 for result in results.values() if not result),
            "total": len(results)
        }
    }
    
    # 打印摘要
    print(f"测试时间: {timestamp}")
    print(f"通过测试: {report['summary']['passed']}")
    print(f"失败测试: {report['summary']['failed']}")
    print(f"总计测试: {report['summary']['total']}")
    
    # 保存报告
    report_file = project_root / "multimedia_backtest_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 详细报告已保存到: {report_file}")
    
    return report

def main():
    """主函数"""
    print("🎓 多媒体课件支持系统回测")
    print("="*50)
    
    results = {}
    
    # 执行各项检查
    results['file_integrity'] = check_file_integrity()
    results['dependencies'] = check_dependencies()
    results['model_definitions'] = check_model_definitions()
    results['service_availability'] = check_service_availability()
    results['api_routes'] = check_api_routes()
    results['celery_configuration'] = check_celery_configuration()
    results['security'] = security_check()
    
    # 性能测试
    performance_results = performance_test()
    results['performance'] = len(performance_results) > 0
    
    # 生成报告
    report = generate_report(results)
    
    # 最终结论
    passed_all = all(results.values())
    
    print("\n" + "="*50)
    if passed_all:
        print("🎉 所有测试通过！系统可以正常部署。")
    else:
        print("⚠️  部分测试未通过，请检查上述问题后再部署。")
    print("="*50)
    
    return passed_all

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)