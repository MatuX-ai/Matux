"""
Edge Impulse 250KB功能基础验证程序
不依赖TensorFlow的轻量级验证工具
"""

import os
import sys
import json
import ast
import importlib.util
from pathlib import Path
from datetime import datetime
import hashlib

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def validate_file_structure():
    """验证文件结构完整性"""
    print("📁 验证文件结构...")
    
    required_files = [
        "backend/services/edge_impulse_client.py",
        "backend/services/tinyml_compressor_250kb.py", 
        "backend/services/edge_impulse_deployment_manager.py",
        "backend/utils/duplicate_development_detector.py",
        "scripts/edge_impulse_250kb_backtest.py",
        "docs/EDGE_IMPULSE_250KB_INTEGRATION_TECHNICAL_DOC.md",
        "docs/EDGE_IMPULSE_250KB_DEVELOPMENT_SPEC.md"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            existing_files.append(file_path)
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path}")
    
    return {
        'total_required': len(required_files),
        'existing_files': len(existing_files),
        'missing_files': missing_files,
        'completeness': len(existing_files) / len(required_files) * 100
    }

def validate_python_syntax():
    """验证Python语法"""
    print("\n🔍 验证Python语法...")
    
    python_files = [
        "backend/services/edge_impulse_client.py",
        "backend/services/tinyml_compressor_250kb.py",
        "backend/services/edge_impulse_deployment_manager.py",
        "backend/utils/duplicate_development_detector.py",
        "scripts/edge_impulse_250kb_backtest.py"
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        if not Path(file_path).exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                ast.parse(content)
            print(f"  ✅ {file_path}")
        except SyntaxError as e:
            syntax_errors.append({
                'file': file_path,
                'line': e.lineno,
                'error': str(e.msg)
            })
            print(f"  ❌ {file_path} - 行{e.lineno}: {e.msg}")
        except Exception as e:
            syntax_errors.append({
                'file': file_path,
                'error': str(e)
            })
            print(f"  ⚠️ {file_path} - {e}")
    
    return {
        'total_files': len(python_files),
        'syntax_errors': syntax_errors,
        'syntax_correct': len(syntax_errors) == 0
    }

def validate_import_structure():
    """验证模块导入结构"""
    print("\n🔌 验证模块导入...")
    
    # 检查模块是否可以被找到
    modules_to_check = [
        'backend.services.edge_impulse_client',
        'backend.services.tinyml_compressor_250kb', 
        'backend.services.edge_impulse_deployment_manager',
        'backend.utils.duplicate_development_detector'
    ]
    
    import_results = []
    
    for module_name in modules_to_check:
        try:
            module_spec = importlib.util.find_spec(module_name)
            if module_spec is not None:
                import_results.append({
                    'module': module_name,
                    'status': 'found',
                    'path': module_spec.origin
                })
                print(f"  ✅ {module_name}")
            else:
                import_results.append({
                    'module': module_name,
                    'status': 'not_found'
                })
                print(f"  ❌ {module_name} - 未找到模块")
        except Exception as e:
            import_results.append({
                'module': module_name,
                'status': 'error',
                'error': str(e)
            })
            print(f"  ⚠️ {module_name} - {e}")
    
    return {
        'modules_checked': len(modules_to_check),
        'successful_imports': len([r for r in import_results if r['status'] == 'found']),
        'import_results': import_results
    }

def validate_class_and_method_existence():
    """验证关键类和方法是否存在"""
    print("\n🧪 验证关键类和方法...")
    
    checks = [
        {
            'module': 'backend.services.edge_impulse_client',
            'class': 'EdgeImpulseClient',
            'required_methods': ['__init__', 'get_projects', 'start_training_job', 'export_model']
        },
        {
            'module': 'backend.services.tinyml_compressor_250kb',
            'class': 'TinyMLModelCompressor250KB',
            'required_methods': ['__init__', 'compress_to_target_size', 'validate_compression_quality']
        },
        {
            'module': 'backend.services.edge_impulse_deployment_manager',
            'class': 'EdgeImpulseDeploymentManager',
            'required_methods': ['__init__', 'deploy_model_from_scratch', 'batch_deploy_models']
        },
        {
            'module': 'backend.utils.duplicate_development_detector',
            'class': 'DuplicateDevelopmentDetector',
            'required_methods': ['__init__', 'scan_project_for_duplicates', 'save_detection_report']
        }
    ]
    
    validation_results = []
    
    for check in checks:
        try:
            module = importlib.import_module(check['module'])
            
            if hasattr(module, check['class']):
                cls = getattr(module, check['class'])
                found_methods = []
                missing_methods = []
                
                for method in check['required_methods']:
                    if hasattr(cls, method):
                        found_methods.append(method)
                    else:
                        missing_methods.append(method)
                
                status = 'complete' if not missing_methods else 'partial' if found_methods else 'incomplete'
                
                validation_results.append({
                    'module': check['module'],
                    'class': check['class'],
                    'status': status,
                    'found_methods': found_methods,
                    'missing_methods': missing_methods,
                    'completeness': len(found_methods) / len(check['required_methods'])
                })
                
                status_icon = '✅' if status == 'complete' else '⚠️' if status == 'partial' else '❌'
                print(f"  {status_icon} {check['class']} - {len(found_methods)}/{len(check['required_methods'])} 方法")
                
            else:
                validation_results.append({
                    'module': check['module'],
                    'class': check['class'],
                    'status': 'class_not_found'
                })
                print(f"  ❌ {check['class']} - 类不存在")
                
        except Exception as e:
            validation_results.append({
                'module': check['module'],
                'class': check['class'],
                'status': 'error',
                'error': str(e)
            })
            print(f"  ⚠️ {check['class']} - {e}")
    
    return validation_results

def validate_documentation():
    """验证文档完整性"""
    print("\n📚 验证文档...")
    
    doc_files = [
        "docs/EDGE_IMPULSE_250KB_INTEGRATION_TECHNICAL_DOC.md",
        "docs/EDGE_IMPULSE_250KB_DEVELOPMENT_SPEC.md"
    ]
    
    doc_results = []
    
    for doc_file in doc_files:
        if Path(doc_file).exists():
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    # 检查基本结构
                    has_title = any(line.startswith('# ') for line in lines[:10])
                    has_sections = content.count('## ') >= 3
                    has_code_blocks = '```' in content
                    
                    doc_results.append({
                        'file': doc_file,
                        'status': 'complete',
                        'has_title': has_title,
                        'has_sections': has_sections,
                        'has_code_blocks': has_code_blocks,
                        'line_count': len(lines)
                    })
                    
                    print(f"  ✅ {doc_file}")
                    print(f"    标题: {'✅' if has_title else '❌'}, 章节: {'✅' if has_sections else '❌'}, 代码块: {'✅' if has_code_blocks else '❌'}")
                    
            except Exception as e:
                doc_results.append({
                    'file': doc_file,
                    'status': 'error',
                    'error': str(e)
                })
                print(f"  ⚠️ {doc_file} - {e}")
        else:
            doc_results.append({
                'file': doc_file,
                'status': 'missing'
            })
            print(f"  ❌ {doc_file} - 文件不存在")
    
    return doc_results

def validate_naming_conventions():
    """验证命名规范"""
    print("\n🔤 验证命名规范...")
    
    # 检查Python文件命名
    service_files = list(Path('backend/services').glob('*.py')) if Path('backend/services').exists() else []
    utils_files = list(Path('backend/utils').glob('*.py')) if Path('backend/utils').exists() else []
    script_files = list(Path('scripts').glob('*.py')) if Path('scripts').exists() else []
    
    all_py_files = service_files + utils_files + script_files
    
    naming_issues = []
    
    for file_path in all_py_files:
        filename = file_path.name
        # 检查是否符合snake_case命名规范
        if not filename.replace('.py', '').islower() or '_' not in filename.replace('.py', ''):
            if filename != '__init__.py':  # 允许特殊文件
                naming_issues.append({
                    'file': str(file_path),
                    'issue': '不符合snake_case命名规范'
                })
                print(f"  ⚠️ {file_path} - 命名规范问题")
    
    print(f"  检查了 {len(all_py_files)} 个Python文件")
    print(f"  发现 {len(naming_issues)} 个命名问题")
    
    return {
        'total_files': len(all_py_files),
        'naming_issues': naming_issues,
        'issues_count': len(naming_issues)
    }

def calculate_overall_score(validation_results):
    """计算总体评分"""
    
    scores = []
    
    # 文件结构完整性 (20%)
    file_result = validation_results['file_structure']
    scores.append(file_result['completeness'] * 0.2)
    
    # 语法正确性 (20%)
    syntax_result = validation_results['syntax_validation']
    syntax_score = 100 if syntax_result['syntax_correct'] else (100 - len(syntax_result['syntax_errors']) * 10)
    scores.append(max(0, syntax_score) * 0.2)
    
    # 导入结构 (15%)
    import_result = validation_results['import_validation']
    import_score = (import_result['successful_imports'] / import_result['modules_checked']) * 100
    scores.append(import_score * 0.15)
    
    # 类方法完整性 (25%)
    class_results = validation_results['class_method_validation']
    completeness_scores = [r.get('completeness', 0) * 100 for r in class_results if 'completeness' in r]
    if completeness_scores:
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        scores.append(avg_completeness * 0.25)
    
    # 文档完整性 (10%)
    doc_results = validation_results['documentation_validation']
    doc_complete = len([d for d in doc_results if d['status'] == 'complete'])
    doc_score = (doc_complete / len(doc_results)) * 100 if doc_results else 0
    scores.append(doc_score * 0.1)
    
    # 命名规范 (10%)
    naming_result = validation_results['naming_validation']
    naming_score = max(0, 100 - (naming_result['issues_count'] * 5))  # 每个问题扣5分
    scores.append(naming_score * 0.1)
    
    overall_score = sum(scores)
    
    # 确定等级
    if overall_score >= 90:
        grade = 'EXCELLENT'
    elif overall_score >= 75:
        grade = 'GOOD'
    elif overall_score >= 60:
        grade = 'ACCEPTABLE'
    else:
        grade = 'POOR'
    
    return {
        'overall_score': round(overall_score, 1),
        'grade': grade,
        'detailed_scores': {
            'file_structure': round(file_result['completeness'], 1),
            'syntax_correctness': round(syntax_score, 1),
            'import_structure': round(import_score, 1),
            'class_method_completeness': round(avg_completeness if completeness_scores else 0, 1),
            'documentation': round(doc_score, 1),
            'naming_convention': round(naming_score, 1)
        }
    }

def generate_validation_report(validation_results):
    """生成验证报告"""
    print("\n" + "="*60)
    print("📊 Edge Impulse 250KB功能验证报告")
    print("="*60)
    
    # 总体评分
    overall = validation_results['overall_assessment']
    print(f"\n📈 总体评分: {overall['overall_score']}/100 ({overall['grade']})")
    
    # 详细分数
    scores = overall['detailed_scores']
    print(f"\n📋 详细评分:")
    print(f"  文件结构完整性: {scores['file_structure']}/100")
    print(f"  语法正确性: {scores['syntax_correctness']}/100")
    print(f"  导入结构: {scores['import_structure']}/100")
    print(f"  类方法完整性: {scores['class_method_completeness']}/100")
    print(f"  文档完整性: {scores['documentation']}/100")
    print(f"  命名规范: {scores['naming_convention']}/100")
    
    # 功能完整性摘要
    class_results = validation_results['class_method_validation']
    complete_classes = len([r for r in class_results if r['status'] == 'complete'])
    total_classes = len(class_results)
    print(f"\n🔧 功能完整性: {complete_classes}/{total_classes} 个核心类完整")
    
    # 建议和改进点
    print(f"\n💡 建议和改进:")
    
    if scores['file_structure'] < 100:
        print("  • 补充缺失的必需文件")
    
    if scores['syntax_correctness'] < 100:
        print("  • 修复语法错误")
    
    if scores['import_structure'] < 100:
        print("  • 检查模块导入路径")
    
    if scores['class_method_completeness'] < 100:
        missing_methods = []
        for result in class_results:
            if result['status'] != 'complete' and 'missing_methods' in result:
                missing_methods.extend(result['missing_methods'])
        if missing_methods:
            print(f"  • 实现缺失的方法: {', '.join(set(missing_methods))}")
    
    if scores['documentation'] < 100:
        print("  • 完善技术文档内容")
    
    if scores['naming_convention'] < 100:
        print("  • 修正文件命名规范")
    
    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'edge_impulse_validation_report_{timestamp}.json'
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 验证报告已保存: {report_filename}")
    
    return overall['grade']

def main():
    """主验证函数"""
    print("🚀 Edge Impulse 250KB功能基础验证程序")
    print("版本: 1.0.0")
    print("日期: 2026年3月1日")
    print()
    
    validation_results = {}
    
    # 执行各项验证
    validation_results['file_structure'] = validate_file_structure()
    validation_results['syntax_validation'] = validate_python_syntax()
    validation_results['import_validation'] = validate_import_structure()
    validation_results['class_method_validation'] = validate_class_and_method_existence()
    validation_results['documentation_validation'] = validate_documentation()
    validation_results['naming_validation'] = validate_naming_conventions()
    
    # 计算总体评分
    validation_results['overall_assessment'] = calculate_overall_score(validation_results)
    
    # 生成报告
    final_grade = generate_validation_report(validation_results)
    
    print(f"\n🎉 验证完成! 最终等级: {final_grade}")
    
    # 根据等级返回退出码
    exit_codes = {'EXCELLENT': 0, 'GOOD': 1, 'ACCEPTABLE': 2, 'POOR': 3}
    return exit_codes.get(final_grade, 3)

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)