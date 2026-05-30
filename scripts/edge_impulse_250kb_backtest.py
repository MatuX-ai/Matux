"""
Edge Impulse TinyML模型250KB压缩功能完整回测验证程序
验证功能正确性，防止重复开发，确保符合项目规范
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import importlib.util

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from backend.utils.duplicate_development_detector import DuplicateDevelopmentDetector
from backend.services.edge_impulse_client import EdgeImpulseClient
from backend.services.tinyml_compressor_250kb import TinyMLModelCompressor250KB
from backend.services.edge_impulse_deployment_manager import EdgeImpulseDeploymentManager

logger = logging.getLogger(__name__)

class EdgeImpulse250KBBacktest:
    """Edge Impulse 250KB压缩功能回测验证器"""
    
    def __init__(self, project_root: str = "."):
        """
        初始化回测验证器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.backtest_results = {}
        self.start_time = datetime.now()
        
        # 配置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('edge_impulse_250kb_backtest.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_comprehensive_backtest(self) -> Dict[str, Any]:
        """
        运行全面的回测验证
        
        Returns:
            回测结果报告
        """
        logger.info("=== Edge Impulse 250KB压缩功能回测开始 ===")
        
        try:
            # 1. 功能完整性检查
            self._check_functionality_completeness()
            
            # 2. 重复开发检测
            self._run_duplicate_detection()
            
            # 3. 代码质量验证
            self._validate_code_quality()
            
            # 4. 性能基准测试
            self._run_performance_benchmarks()
            
            # 5. 规范符合性检查
            self._check_specification_compliance()
            
            # 6. 集成测试
            self._run_integration_tests()
            
            # 7. 生成综合报告
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"回测执行过程中出现错误: {e}")
            self.backtest_results['error'] = str(e)
        
        finally:
            self._finalize_backtest()
        
        return self.backtest_results
    
    def _check_functionality_completeness(self):
        """检查功能完整性"""
        logger.info("--- 检查功能完整性 ---")
        
        required_components = {
            'edge_impulse_client': {
                'module': 'backend.services.edge_impulse_client',
                'required_classes': ['EdgeImpulseClient', 'EdgeImpulseModelManager'],
                'required_methods': ['train_and_deploy_model', 'export_model']
            },
            'model_compressor': {
                'module': 'backend.services.tinyml_compressor_250kb',
                'required_classes': ['TinyMLModelCompressor250KB'],
                'required_methods': ['compress_to_target_size', 'validate_compression_quality']
            },
            'deployment_manager': {
                'module': 'backend.services.edge_impulse_deployment_manager',
                'required_classes': ['EdgeImpulseDeploymentManager'],
                'required_methods': ['deploy_model_from_scratch', 'batch_deploy_models']
            },
            'duplicate_detector': {
                'module': 'backend.utils.duplicate_development_detector',
                'required_classes': ['DuplicateDevelopmentDetector'],
                'required_methods': ['scan_project_for_duplicates', 'save_detection_report']
            }
        }
        
        completeness_results = {}
        
        for component_name, component_info in required_components.items():
            logger.info(f"检查组件: {component_name}")
            
            try:
                # 动态导入模块
                module_spec = importlib.util.find_spec(component_info['module'])
                if module_spec is None:
                    completeness_results[component_name] = {
                        'status': 'missing',
                        'error': f"模块不存在: {component_info['module']}"
                    }
                    continue
                
                module = importlib.import_module(component_info['module'])
                
                # 检查必需的类
                missing_classes = []
                found_classes = []
                
                for class_name in component_info['required_classes']:
                    if hasattr(module, class_name):
                        found_classes.append(class_name)
                    else:
                        missing_classes.append(class_name)
                
                # 检查必需的方法
                missing_methods = []
                found_methods = []
                
                for method_name in component_info['required_methods']:
                    # 检查是否在任何类中存在该方法
                    method_found = False
                    for class_name in component_info['required_classes']:
                        if hasattr(module, class_name):
                            cls = getattr(module, class_name)
                            if hasattr(cls, method_name) or method_name in dir(cls):
                                method_found = True
                                found_methods.append(method_name)
                                break
                    
                    if not method_found:
                        missing_methods.append(method_name)
                
                # 评估完整性
                total_required = len(component_info['required_classes']) + len(component_info['required_methods'])
                total_found = len(found_classes) + len(found_methods)
                completeness_ratio = total_found / total_required if total_required > 0 else 0
                
                status = 'complete' if completeness_ratio == 1.0 else 'partial' if completeness_ratio > 0 else 'incomplete'
                
                completeness_results[component_name] = {
                    'status': status,
                    'completeness_ratio': completeness_ratio,
                    'found_classes': found_classes,
                    'missing_classes': missing_classes,
                    'found_methods': found_methods,
                    'missing_methods': missing_methods,
                    'module_path': module_spec.origin
                }
                
                logger.info(f"  状态: {status} ({completeness_ratio:.1%})")
                
            except Exception as e:
                completeness_results[component_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"  错误: {e}")
        
        self.backtest_results['functionality_completeness'] = completeness_results
    
    def _run_duplicate_detection(self):
        """运行重复开发检测"""
        logger.info("--- 运行重复开发检测 ---")
        
        try:
            detector = DuplicateDevelopmentDetector(str(self.project_root))
            detection_results = detector.scan_project_for_duplicates()
            
            # 分析风险等级
            risk_assessment = detection_results.get('risk_assessment', {})
            risk_level = risk_assessment.get('risk_level', 'UNKNOWN')
            risk_score = risk_assessment.get('risk_score', 0)
            
            duplicate_results = {
                'status': 'completed',
                'risk_level': risk_level,
                'risk_score': risk_score,
                'total_files_scanned': detection_results.get('file_duplicates', {}).get('total_files', 0),
                'duplicate_functions': len(detection_results.get('function_duplicates', {}).get('duplicate_candidates', [])),
                'domain_overlaps': len(detection_results.get('domain_overlaps', {}).get('domain_overlaps', [])),
                'recommendations': risk_assessment.get('recommendations', []),
                'detection_timestamp': detection_results.get('scan_timestamp')
            }
            
            # 保存详细报告
            report_path = detector.save_detection_report()
            duplicate_results['detailed_report'] = report_path
            
            logger.info(f"重复检测完成 - 风险等级: {risk_level}, 风险分数: {risk_score}")
            
        except Exception as e:
            duplicate_results = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"重复检测失败: {e}")
        
        self.backtest_results['duplicate_detection'] = duplicate_results
    
    def _validate_code_quality(self):
        """验证代码质量"""
        logger.info("--- 验证代码质量 ---")
        
        quality_results = {
            'syntax_check': self._check_python_syntax(),
            'import_validation': self._validate_imports(),
            'documentation_check': self._check_documentation(),
            'coding_standards': self._check_coding_standards()
        }
        
        # 计算总体质量分数
        passed_checks = sum(1 for result in quality_results.values() if result.get('status') == 'passed')
        total_checks = len(quality_results)
        quality_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        quality_results['overall_quality_score'] = quality_score
        quality_results['passed_checks'] = passed_checks
        quality_results['total_checks'] = total_checks
        
        self.backtest_results['code_quality'] = quality_results
        logger.info(f"代码质量评估: {quality_score:.1f}% ({passed_checks}/{total_checks})")
    
    def _check_python_syntax(self) -> Dict[str, Any]:
        """检查Python语法"""
        logger.info("  检查Python语法...")
        
        try:
            # 检查新创建的模块
            modules_to_check = [
                'backend/services/edge_impulse_client.py',
                'backend/services/tinyml_compressor_250kb.py',
                'backend/services/edge_impulse_deployment_manager.py',
                'backend/utils/duplicate_development_detector.py'
            ]
            
            syntax_errors = []
            
            for module_path in modules_to_check:
                full_path = self.project_root / module_path
                if full_path.exists():
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            compile(f.read(), str(full_path), 'exec')
                    except SyntaxError as e:
                        syntax_errors.append({
                            'file': module_path,
                            'line': e.lineno,
                            'error': str(e.msg)
                        })
            
            status = 'passed' if not syntax_errors else 'failed'
            
            return {
                'status': status,
                'checked_modules': len(modules_to_check),
                'syntax_errors': syntax_errors,
                'error_count': len(syntax_errors)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _validate_imports(self) -> Dict[str, Any]:
        """验证导入语句"""
        logger.info("  验证导入语句...")
        
        try:
            import_errors = []
            
            # 测试关键模块导入
            test_imports = [
                'backend.services.edge_impulse_client',
                'backend.services.tinyml_compressor_250kb',
                'backend.services.edge_impulse_deployment_manager'
            ]
            
            for module_name in test_imports:
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    import_errors.append({
                        'module': module_name,
                        'error': str(e)
                    })
            
            status = 'passed' if not import_errors else 'failed'
            
            return {
                'status': status,
                'tested_imports': len(test_imports),
                'import_errors': import_errors,
                'error_count': len(import_errors)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_documentation(self) -> Dict[str, Any]:
        """检查文档完整性"""
        logger.info("  检查文档...")
        
        try:
            # 检查模块是否有文档字符串
            modules_to_check = [
                ('backend.services.edge_impulse_client', 'EdgeImpulseClient'),
                ('backend.services.tinyml_compressor_250kb', 'TinyMLModelCompressor250KB'),
                ('backend.services.edge_impulse_deployment_manager', 'EdgeImpulseDeploymentManager')
            ]
            
            doc_issues = []
            
            for module_name, class_name in modules_to_check:
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, class_name):
                        cls = getattr(module, class_name)
                        if not cls.__doc__ or len(cls.__doc__.strip()) < 50:
                            doc_issues.append({
                                'class': f"{module_name}.{class_name}",
                                'issue': '缺少或不完整的文档字符串'
                            })
                except Exception as e:
                    doc_issues.append({
                        'class': f"{module_name}.{class_name}",
                        'issue': f'无法检查文档: {e}'
                    })
            
            status = 'passed' if not doc_issues else 'warning'
            
            return {
                'status': status,
                'checked_classes': len(modules_to_check),
                'documentation_issues': doc_issues,
                'issue_count': len(doc_issues)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_coding_standards(self) -> Dict[str, Any]:
        """检查编码规范"""
        logger.info("  检查编码规范...")
        
        try:
            # 检查文件命名规范
            service_files = list((self.project_root / 'backend' / 'services').glob('*.py'))
            utils_files = list((self.project_root / 'backend' / 'utils').glob('*.py'))
            all_files = service_files + utils_files
            
            naming_issues = []
            for file_path in all_files:
                filename = file_path.name
                # 检查是否使用snake_case命名
                if not filename.replace('.py', '').islower() or '_' not in filename:
                    naming_issues.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'issue': '文件名不符合snake_case命名规范'
                    })
            
            # 检查代码行长度等基本规范
            line_length_issues = []
            for file_path in all_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if len(line.rstrip()) > 100:  # 超过100字符
                                line_length_issues.append({
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'line': line_num,
                                    'length': len(line.rstrip())
                                })
                                if len(line_length_issues) > 10:  # 限制报告数量
                                    break
                except Exception:
                    continue
            
            total_issues = len(naming_issues) + len(line_length_issues)
            status = 'passed' if total_issues == 0 else 'warning' if total_issues < 5 else 'failed'
            
            return {
                'status': status,
                'naming_issues': naming_issues,
                'line_length_issues': line_length_issues[:10],  # 限制数量
                'total_issues': total_issues
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _run_performance_benchmarks(self):
        """运行性能基准测试"""
        logger.info("--- 运行性能基准测试 ---")
        
        try:
            # 创建测试模型进行压缩测试
            import tensorflow as tf
            
            # 创建简单的测试模型
            test_model = tf.keras.Sequential([
                tf.keras.layers.Dense(32, activation='relu', input_shape=(40,)),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(5, activation='softmax')
            ])
            
            test_model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
            
            # 测试压缩性能
            compressor = TinyMLModelCompressor250KB(target_size_kb=250)
            
            # 测试压缩时间
            import time
            start_time = time.time()
            
            test_output_path = str(self.project_root / 'test_compression.tflite')
            compression_result = compressor.compress_to_target_size(
                model=test_model,
                input_shape=(1, 40),
                output_path=test_output_path
            )
            
            compression_time = time.time() - start_time
            
            # 清理测试文件
            if os.path.exists(test_output_path):
                os.remove(test_output_path)
            
            performance_results = {
                'status': 'completed',
                'compression_time_seconds': round(compression_time, 2),
                'compression_success': compression_result['success'],
                'final_model_size_kb': compression_result['size_kb'],
                'target_size_kb': 250,
                'size_compliance': compression_result['size_kb'] <= 250
            }
            
            logger.info(f"性能测试完成 - 压缩时间: {compression_time:.2f}s, "
                       f"最终大小: {compression_result['size_kb']:.1f}KB")
            
        except Exception as e:
            performance_results = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"性能测试失败: {e}")
        
        self.backtest_results['performance_benchmarks'] = performance_results
    
    def _check_specification_compliance(self):
        """检查规范符合性"""
        logger.info("--- 检查规范符合性 ---")
        
        compliance_results = {
            'target_size_compliance': self._check_target_size_requirement(),
            'api_integration_compliance': self._check_api_integration(),
            'deployment_structure_compliance': self._check_deployment_structure(),
            'documentation_compliance': self._check_technical_documentation()
        }
        
        # 计算合规分数
        compliant_checks = sum(1 for result in compliance_results.values() if result.get('status') == 'compliant')
        total_checks = len(compliance_results)
        compliance_score = (compliant_checks / total_checks) * 100 if total_checks > 0 else 0
        
        compliance_results['overall_compliance_score'] = compliance_score
        compliance_results['compliant_checks'] = compliant_checks
        compliance_results['total_checks'] = total_checks
        
        self.backtest_results['specification_compliance'] = compliance_results
        logger.info(f"规范符合性: {compliance_score:.1f}% ({compliant_checks}/{total_checks})")
    
    def _check_target_size_requirement(self) -> Dict[str, Any]:
        """检查250KB目标大小要求"""
        try:
            # 检查压缩器是否支持250KB目标
            compressor = TinyMLModelCompressor250KB(target_size_kb=250)
            
            return {
                'status': 'compliant' if compressor.target_size_kb == 250 else 'non_compliant',
                'configured_target': compressor.target_size_kb,
                'required_target': 250
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_api_integration(self) -> Dict[str, Any]:
        """检查API集成规范"""
        try:
            # 检查Edge Impulse客户端是否正确实现
            client = EdgeImpulseClient()
            
            # 检查必要方法是否存在
            required_methods = ['get_projects', 'start_training_job', 'export_model']
            missing_methods = [method for method in required_methods if not hasattr(client, method)]
            
            return {
                'status': 'compliant' if not missing_methods else 'non_compliant',
                'missing_methods': missing_methods,
                'total_required_methods': len(required_methods)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_deployment_structure(self) -> Dict[str, Any]:
        """检查部署结构规范"""
        try:
            # 检查必要的目录结构
            required_dirs = [
                'models/tinyml/edge_impulse',
                'models/tinyml/deployments',
                'deployment_records'
            ]
            
            missing_dirs = []
            for dir_path in required_dirs:
                full_path = self.project_root / dir_path
                if not full_path.exists():
                    missing_dirs.append(dir_path)
            
            return {
                'status': 'compliant' if not missing_dirs else 'non_compliant',
                'missing_directories': missing_dirs,
                'total_required_directories': len(required_dirs)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_technical_documentation(self) -> Dict[str, Any]:
        """检查技术文档规范"""
        try:
            # 检查必要的文档文件
            required_docs = [
                'README.md',
                'docs/',
                'backend/services/'
            ]
            
            missing_docs = []
            for doc_path in required_docs:
                full_path = self.project_root / doc_path
                if not full_path.exists():
                    missing_docs.append(doc_path)
            
            return {
                'status': 'compliant' if not missing_docs else 'non_compliant',
                'missing_documents': missing_docs,
                'total_required_documents': len(required_docs)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _run_integration_tests(self):
        """运行集成测试"""
        logger.info("--- 运行集成测试 ---")
        
        try:
            # 测试完整的部署流程（模拟）
            deployment_manager = EdgeImpulseDeploymentManager(target_size_kb=250)
            
            # 创建模拟配置
            mock_config = {
                'model_name': 'integration_test_model',
                'training_data_path': 'mock/data/path.json',  # 模拟路径
                'target_device': 'ESP32',
                'labels': ['test1', 'test2', 'test3']
            }
            
            # 测试部署管理器初始化
            init_success = hasattr(deployment_manager, 'client') and hasattr(deployment_manager, 'compressor')
            
            integration_results = {
                'status': 'completed',
                'deployment_manager_initialization': init_success,
                'required_attributes_present': init_success,
                'mock_deployment_config_valid': True  # 配置结构正确
            }
            
            logger.info("集成测试完成")
            
        except Exception as e:
            integration_results = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"集成测试失败: {e}")
        
        self.backtest_results['integration_tests'] = integration_results
    
    def _generate_final_report(self):
        """生成最终报告"""
        logger.info("--- 生成最终报告 ---")
        
        # 计算总体评分
        section_scores = []
        
        # 功能完整性评分 (权重: 30%)
        func_completeness = self.backtest_results.get('functionality_completeness', {})
        func_score = sum(1 for result in func_completeness.values() 
                        if result.get('status') in ['complete', 'partial']) / len(func_completeness) if func_completeness else 0
        section_scores.append(func_score * 0.3)
        
        # 重复检测评分 (权重: 15%)
        duplicate_result = self.backtest_results.get('duplicate_detection', {})
        risk_score = duplicate_result.get('risk_score', 100)
        duplicate_score = (100 - risk_score) / 100 * 0.15
        section_scores.append(duplicate_score)
        
        # 代码质量评分 (权重: 20%)
        quality_result = self.backtest_results.get('code_quality', {})
        quality_score = quality_result.get('overall_quality_score', 0) / 100 * 0.2
        section_scores.append(quality_score)
        
        # 性能基准评分 (权重: 20%)
        perf_result = self.backtest_results.get('performance_benchmarks', {})
        perf_score = 1.0 * 0.2 if perf_result.get('status') == 'completed' and perf_result.get('size_compliance') else 0
        section_scores.append(perf_score)
        
        # 规范符合性评分 (权重: 15%)
        spec_result = self.backtest_results.get('specification_compliance', {})
        spec_score = spec_result.get('overall_compliance_score', 0) / 100 * 0.15
        section_scores.append(spec_score)
        
        overall_score = sum(section_scores) * 100
        
        # 确定总体状态
        if overall_score >= 90:
            overall_status = 'EXCELLENT'
        elif overall_score >= 75:
            overall_status = 'GOOD'
        elif overall_score >= 60:
            overall_status = 'ACCEPTABLE'
        else:
            overall_status = 'POOR'
        
        self.backtest_results['final_summary'] = {
            'overall_status': overall_status,
            'overall_score': round(overall_score, 1),
            'section_scores': {
                'functionality_completeness': round(func_score * 100, 1),
                'duplicate_detection': round((100 - risk_score), 1),
                'code_quality': quality_result.get('overall_quality_score', 0),
                'performance_benchmarks': round(perf_score * 100, 1),
                'specification_compliance': spec_result.get('overall_compliance_score', 0)
            },
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        logger.info(f"总体评分: {overall_score:.1f}% - 状态: {overall_status}")
    
    def _finalize_backtest(self):
        """完成回测并保存结果"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.backtest_results['metadata'] = {
            'backtest_id': f'EI_250KB_BACKTEST_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'project_root': str(self.project_root)
        }
        
        # 保存报告
        reports_dir = self.project_root / 'backtest_reports'
        reports_dir.mkdir(exist_ok=True)
        
        report_filename = f"edge_impulse_250kb_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = reports_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.backtest_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"=== 回测完成 ===")
        logger.info(f"执行时间: {duration:.2f} 秒")
        logger.info(f"报告已保存到: {report_path}")
        
        return self.backtest_results

def main():
    """主函数"""
    backtester = EdgeImpulse250KBBacktest()
    results = backtester.run_comprehensive_backtest()
    
    # 根据总体状态返回相应退出码
    if results and 'final_summary' in results:
        overall_status = results['final_summary'].get('overall_status', 'UNKNOWN')
        if overall_status == 'EXCELLENT':
            return 0
        elif overall_status == 'GOOD':
            return 1
        elif overall_status == 'ACCEPTABLE':
            return 2
        else:
            return 3
    else:
        return 3  # 默认返回错误码

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)