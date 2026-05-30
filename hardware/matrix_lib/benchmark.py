"""
矩阵运算性能基准测试
对比硬件加速和CPU实现的性能差异
"""

import logging
import time
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import matplotlib.pyplot as plt

from .accelerated_matrix import AcceleratedMatrix
from .cpu_matrix import CPUMatrix

logger = logging.getLogger(__name__)


class MatrixBenchmark:
    """矩阵运算性能基准测试类"""
    
    def __init__(self):
        self.results = []
        self.test_configurations = []
        
    def add_test_configuration(self, name: str, matrix_sizes: List[Tuple[int, int]], 
                             operations: List[str] = None):
        """
        添加测试配置
        
        Args:
            name: 测试名称
            matrix_sizes: 矩阵尺寸列表 [(rows, cols), ...]
            operations: 要测试的操作列表 ['multiply', 'add', 'inverse', ...]
        """
        if operations is None:
            operations = ['multiply', 'add']
            
        self.test_configurations.append({
            'name': name,
            'matrix_sizes': matrix_sizes,
            'operations': operations
        })
    
    def run_benchmark(self, iterations: int = 5) -> Dict[str, Any]:
        """
        运行完整基准测试
        
        Args:
            iterations: 每个测试重复次数
            
        Returns:
            Dict: 测试结果汇总
        """
        logger.info("开始矩阵运算基准测试...")
        start_time = datetime.now()
        
        all_results = []
        
        for config in self.test_configurations:
            config_results = self._run_configuration_test(config, iterations)
            all_results.extend(config_results)
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        summary = self._generate_summary(all_results, total_duration)
        
        logger.info(f"基准测试完成，总耗时: {total_duration:.2f}秒")
        return summary
    
    def _run_configuration_test(self, config: Dict, iterations: int) -> List[Dict]:
        """运行单个配置的测试"""
        results = []
        
        logger.info(f"运行测试配置: {config['name']}")
        
        for size in config['matrix_sizes']:
            logger.info(f"  测试矩阵尺寸: {size}")
            
            for operation in config['operations']:
                test_result = self._run_single_test(size, operation, iterations)
                if test_result:
                    results.append(test_result)
        
        return results
    
    def _run_single_test(self, matrix_size: Tuple[int, int], 
                        operation: str, iterations: int) -> Optional[Dict]:
        """运行单次测试"""
        try:
            rows, cols = matrix_size
            
            # 生成测试数据
            if operation in ['multiply']:
                # 矩阵乘法需要可相乘的维度
                a = np.random.random((rows, cols)).astype(np.float32)
                b = np.random.random((cols, rows)).astype(np.float32)
                cpu_a, cpu_b = CPUMatrix(a), CPUMatrix(b)
                accel_a, accel_b = AcceleratedMatrix(a), AcceleratedMatrix(b)
            else:
                # 其他操作使用方阵
                size = min(rows, cols)
                a = np.random.random((size, size)).astype(np.float32)
                cpu_a = CPUMatrix(a)
                accel_a = AcceleratedMatrix(a)
                b = None
                cpu_b = None
                accel_b = None
            
            # CPU测试
            cpu_times = []
            cpu_result = None
            
            for i in range(iterations):
                start_time = time.time()
                
                if operation == 'multiply':
                    cpu_result = cpu_a.multiply(cpu_b)
                elif operation == 'add':
                    cpu_result = cpu_a.add(cpu_a)  # 自加
                elif operation == 'inverse':
                    cpu_result = cpu_a.inverse()
                elif operation == 'transpose':
                    cpu_result = cpu_a.transpose()
                elif operation == 'determinant':
                    cpu_result = cpu_a.determinant()
                elif operation == 'eigenvalues':
                    cpu_result = cpu_a.eigenvalues()
                
                cpu_times.append(time.time() - start_time)
            
            # 硬件加速测试
            accel_times = []
            accel_result = None
            
            for i in range(iterations):
                start_time = time.time()
                
                if operation == 'multiply':
                    accel_result = accel_a.multiply(accel_b)
                elif operation == 'add':
                    accel_result = accel_a.add(accel_a)
                elif operation == 'inverse':
                    accel_result = accel_a.inverse()
                elif operation == 'transpose':
                    accel_result = accel_a.transpose()
                elif operation == 'determinant':
                    # 行列式计算仍在CPU上执行
                    accel_result = accel_a.determinant()
                elif operation == 'eigenvalues':
                    # 特征值计算仍在CPU上执行
                    accel_result = accel_a.eigenvalues()
                
                accel_times.append(time.time() - start_time)
            
            # 结果验证（如果适用）
            validation_passed = True
            if operation in ['multiply', 'add', 'inverse', 'transpose'] and cpu_result is not None:
                try:
                    if isinstance(cpu_result, CPUMatrix) and accel_result is not None:
                        comparison = cpu_result.compare_with(accel_result.to_numpy())
                        validation_passed = comparison['is_numerically_close']
                except Exception as e:
                    logger.warning(f"结果验证失败: {str(e)}")
                    validation_passed = False
            
            # 计算统计信息
            result = {
                'matrix_size': matrix_size,
                'operation': operation,
                'iterations': iterations,
                'cpu_stats': {
                    'times': cpu_times,
                    'mean_time': np.mean(cpu_times),
                    'std_time': np.std(cpu_times),
                    'min_time': np.min(cpu_times),
                    'max_time': np.max(cpu_times)
                },
                'accelerator_stats': {
                    'times': accel_times,
                    'mean_time': np.mean(accel_times),
                    'std_time': np.std(accel_times),
                    'min_time': np.min(accel_times),
                    'max_time': np.max(accel_times)
                },
                'performance_ratio': np.mean(cpu_times) / np.mean(accel_times) if np.mean(accel_times) > 0 else float('inf'),
                'validation_passed': validation_passed,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"测试执行失败 - 尺寸:{matrix_size}, 操作:{operation}: {str(e)}")
            return None
    
    def _generate_summary(self, results: List[Dict], total_duration: float) -> Dict[str, Any]:
        """生成测试摘要"""
        if not results:
            return {'error': '没有有效的测试结果'}
        
        # 按操作类型分组统计
        operation_stats = {}
        for result in results:
            op = result['operation']
            if op not in operation_stats:
                operation_stats[op] = {
                    'count': 0,
                    'total_cpu_time': 0,
                    'total_accel_time': 0,
                    'speedup_sum': 0,
                    'validations_passed': 0,
                    'validations_total': 0
                }
            
            stats = operation_stats[op]
            stats['count'] += 1
            stats['total_cpu_time'] += result['cpu_stats']['mean_time']
            stats['total_accel_time'] += result['accelerator_stats']['mean_time']
            stats['speedup_sum'] += result['performance_ratio']
            stats['validations_total'] += 1
            if result['validation_passed']:
                stats['validations_passed'] += 1
        
        # 计算汇总统计
        summary_stats = {
            'total_tests': len(results),
            'successful_validations': sum(1 for r in results if r['validation_passed']),
            'validation_success_rate': sum(1 for r in results if r['validation_passed']) / len(results),
            'average_speedup': np.mean([r['performance_ratio'] for r in results if r['performance_ratio'] != float('inf')]),
            'best_speedup': max([r['performance_ratio'] for r in results if r['performance_ratio'] != float('inf')]),
            'worst_speedup': min([r['performance_ratio'] for r in results if r['performance_ratio'] != float('inf')])
        }
        
        return {
            'summary': summary_stats,
            'operation_details': operation_stats,
            'individual_results': results,
            'total_duration': total_duration,
            'test_timestamp': datetime.now().isoformat()
        }
    
    def print_report(self, summary: Dict[str, Any]):
        """打印测试报告"""
        print("\n" + "="*60)
        print("矩阵运算性能基准测试报告")
        print("="*60)
        
        if 'error' in summary:
            print(f"错误: {summary['error']}")
            return
        
        # 摘要信息
        summary_info = summary['summary']
        print(f"\n测试摘要:")
        print(f"  总测试数: {summary_info['total_tests']}")
        print(f"  验证通过率: {summary_info['validation_success_rate']:.2%}")
        print(f"  平均加速比: {summary_info['average_speedup']:.2f}x")
        print(f"  最佳加速比: {summary_info['best_speedup']:.2f}x")
        print(f"  最差加速比: {summary_info['worst_speedup']:.2f}x")
        print(f"  总耗时: {summary['total_duration']:.2f}秒")
        
        # 操作详细统计
        print(f"\n各操作性能统计:")
        for operation, stats in summary['operation_details'].items():
            avg_cpu_time = stats['total_cpu_time'] / stats['count']
            avg_accel_time = stats['total_accel_time'] / stats['count']
            avg_speedup = stats['speedup_sum'] / stats['count']
            validation_rate = stats['validations_passed'] / stats['validations_total']
            
            print(f"  {operation.upper()}:")
            print(f"    测试次数: {stats['count']}")
            print(f"    平均CPU时间: {avg_cpu_time*1000:.2f}ms")
            print(f"    平均加速时间: {avg_accel_time*1000:.2f}ms")
            print(f"    平均加速比: {avg_speedup:.2f}x")
            print(f"    验证通过率: {validation_rate:.2%}")
        
        print("="*60)
    
    def plot_results(self, summary: Dict[str, Any], save_path: str = None):
        """绘制性能对比图表"""
        try:
            results = summary['individual_results']
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('矩阵运算性能基准测试结果', fontsize=16)
            
            # 1. 加速比对比
            operations = list(summary['operation_details'].keys())
            speedups = [summary['operation_details'][op]['speedup_sum'] / 
                       summary['operation_details'][op]['count'] for op in operations]
            
            axes[0, 0].bar(operations, speedups)
            axes[0, 0].set_title('各操作平均加速比')
            axes[0, 0].set_ylabel('加速比 (倍)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # 2. 执行时间对比
            cpu_times = [r['cpu_stats']['mean_time']*1000 for r in results]
            accel_times = [r['accelerator_stats']['mean_time']*1000 for r in results]
            test_labels = [f"{r['operation']}\n{r['matrix_size']}" for r in results[:10]]  # 只显示前10个
            
            x = range(len(test_labels))
            width = 0.35
            
            axes[0, 1].bar([i - width/2 for i in x], cpu_times[:10], width, label='CPU', alpha=0.8)
            axes[0, 1].bar([i + width/2 for i in x], accel_times[:10], width, label='加速器', alpha=0.8)
            axes[0, 1].set_title('执行时间对比 (前10个测试)')
            axes[0, 1].set_ylabel('时间 (毫秒)')
            axes[0, 1].set_xticks(x)
            axes[0, 1].set_xticklabels(test_labels, rotation=45, ha='right')
            axes[0, 1].legend()
            
            # 3. 性能提升分布
            ratios = [r['performance_ratio'] for r in results if r['performance_ratio'] != float('inf')]
            axes[1, 0].hist(ratios, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            axes[1, 0].set_title('加速比分布')
            axes[1, 0].set_xlabel('加速比')
            axes[1, 0].set_ylabel('频次')
            axes[1, 0].axvline(summary['summary']['average_speedup'], color='red', linestyle='--', 
                              label=f'平均值: {summary["summary"]["average_speedup"]:.2f}x')
            axes[1, 0].legend()
            
            # 4. 验证成功率
            validation_rates = []
            labels = []
            for op, stats in summary['operation_details'].items():
                rate = stats['validations_passed'] / stats['validations_total']
                validation_rates.append(rate)
                labels.append(op)
            
            axes[1, 1].bar(labels, validation_rates)
            axes[1, 1].set_title('各操作验证成功率')
            axes[1, 1].set_ylabel('成功率')
            axes[1, 1].set_ylim(0, 1.1)
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            # 在柱状图上显示数值
            for i, v in enumerate(validation_rates):
                axes[1, 1].text(i, v + 0.02, f'{v:.1%}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"图表已保存到: {save_path}")
            else:
                plt.show()
                
        except Exception as e:
            logger.error(f"绘图失败: {str(e)}")

# 预定义的测试配置
def get_standard_benchmark_config():
    """获取标准基准测试配置"""
    benchmark = MatrixBenchmark()
    
    # 小规模测试
    benchmark.add_test_configuration(
        name="小规模矩阵测试",
        matrix_sizes=[(100, 100), (200, 200), (500, 500)],
        operations=['multiply', 'add', 'transpose']
    )
    
    # 中等规模测试
    benchmark.add_test_configuration(
        name="中等规模矩阵测试",
        matrix_sizes=[(1000, 1000), (1500, 1500)],
        operations=['multiply', 'add', 'inverse']
    )
    
    # 大规模测试
    benchmark.add_test_configuration(
        name="大规模矩阵测试",
        matrix_sizes=[(2000, 2000)],
        operations=['multiply', 'add']
    )
    
    return benchmark