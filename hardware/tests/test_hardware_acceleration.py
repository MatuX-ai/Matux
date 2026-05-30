"""
硬件加速模块综合测试套件
验证所有功能的正确性和性能表现
"""

import unittest
import numpy as np
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from hardware.hal.hal_interface import AcceleratorFactory
from hardware.hal.fpga_driver import FPGADriver
from hardware.hal.accelerator_manager import default_manager
from hardware.matrix_lib.accelerated_matrix import AcceleratedMatrix
from hardware.matrix_lib.cpu_matrix import CPUMatrix
from hardware.matrix_lib.benchmark import MatrixBenchmark

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHardwareAcceleration(unittest.TestCase):
    """硬件加速功能测试"""
    
    def setUp(self):
        """测试前置设置"""
        logger.info("开始硬件加速测试")
        
    def tearDown(self):
        """测试后置清理"""
        logger.info("硬件加速测试完成")
    
    def test_hal_interface_registration(self):
        """测试HAL接口注册"""
        logger.info("测试HAL接口注册...")
        
        # 检查加速器是否已注册
        available_accelerators = AcceleratorFactory.get_available_accelerators()
        self.assertIn("fpga", available_accelerators)
        self.assertIn("gpu_opencl", available_accelerators)
        
        logger.info(f"可用加速器: {available_accelerators}")
    
    def test_fpga_driver_initialization(self):
        """测试FPGA驱动初始化"""
        logger.info("测试FPGA驱动初始化...")
        
        fpga_driver = FPGADriver(device_path="/dev/fpga_test")
        self.assertIsNotNone(fpga_driver)
        
        # 测试初始化
        init_success = fpga_driver.initialize()
        self.assertTrue(init_success)
        
        # 检查状态
        status = fpga_driver.get_status()
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["type"], "fpga")
        
        logger.info("FPGA驱动初始化测试通过")
    
    def test_edge_detection_functionality(self):
        """测试边缘检测功能"""
        logger.info("测试边缘检测功能...")
        
        # 创建测试图像
        test_image = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        
        # 初始化FPGA驱动
        fpga_driver = FPGADriver()
        self.assertTrue(fpga_driver.initialize())
        
        # 执行边缘检测
        threshold = 128
        result = fpga_driver.detect_edges(test_image, threshold)
        
        # 验证结果
        self.assertEqual(result.shape, test_image.shape)
        self.assertEqual(result.dtype, np.uint8)
        
        # 验证输出值范围
        self.assertTrue(np.all((result == 0) | (result == 255)))
        
        logger.info("边缘检测功能测试通过")
    
    def test_matrix_multiplication(self):
        """测试矩阵乘法功能"""
        logger.info("测试矩阵乘法功能...")
        
        # 创建测试矩阵
        a = np.random.random((100, 150)).astype(np.float32)
        b = np.random.random((150, 80)).astype(np.float32)
        
        # 初始化FPGA驱动
        fpga_driver = FPGADriver()
        self.assertTrue(fpga_driver.initialize())
        
        # 执行矩阵乘法
        result = fpga_driver.matrix_multiply(a, b)
        
        # 验证结果维度
        self.assertEqual(result.shape, (100, 80))
        
        # 与NumPy结果比较
        expected = np.dot(a, b)
        np.testing.assert_array_almost_equal(result, expected, decimal=4)
        
        logger.info("矩阵乘法功能测试通过")
    
    def test_accelerator_manager(self):
        """测试加速器管理器"""
        logger.info("测试加速器管理器...")
        
        # 配置加速器
        configs = [
            {
                "type": "fpga",
                "name": "test_fpga",
                "config": {"device_path": "/dev/fpga_test"}
            }
        ]
        
        # 初始化管理器
        success = default_manager.initialize_accelerators(configs)
        self.assertTrue(success)
        
        # 检查状态
        status = default_manager.get_accelerator_status()
        self.assertGreater(status["total_accelerators"], 0)
        self.assertIsNotNone(status["active_accelerator"])
        
        logger.info("加速器管理器测试通过")


class TestMatrixOperations(unittest.TestCase):
    """矩阵运算测试"""
    
    def setUp(self):
        """测试前置设置"""
        logger.info("开始矩阵运算测试")
    
    def tearDown(self):
        """测试后置清理"""
        logger.info("矩阵运算测试完成")
    
    def test_accelerated_matrix_creation(self):
        """测试加速矩阵创建"""
        logger.info("测试加速矩阵创建...")
        
        # 从NumPy数组创建
        data = np.random.random((50, 50))
        accel_matrix = AcceleratedMatrix(data)
        
        self.assertEqual(accel_matrix.shape, (50, 50))
        # 使用近似相等比较，因为浮点数精度可能存在微小差异
        np.testing.assert_array_almost_equal(accel_matrix.to_numpy(), data, decimal=6)
        
        logger.info("加速矩阵创建测试通过")
    
    def test_matrix_multiplication_comparison(self):
        """测试矩阵乘法对比"""
        logger.info("测试矩阵乘法对比...")
        
        # 创建测试矩阵
        a_data = np.random.random((100, 120)).astype(np.float32)
        b_data = np.random.random((120, 80)).astype(np.float32)
        
        # CPU计算
        cpu_a = CPUMatrix(a_data)
        cpu_b = CPUMatrix(b_data)
        cpu_result = cpu_a.multiply(cpu_b)
        
        # 硬件加速计算
        accel_a = AcceleratedMatrix(a_data)
        accel_b = AcceleratedMatrix(b_data)
        accel_result = accel_a.multiply(accel_b)
        
        # 结果比较
        comparison = cpu_result.compare_with(accel_result.to_numpy())
        self.assertTrue(comparison["is_numerically_close"])
        
        logger.info("矩阵乘法对比测试通过")
    
    def test_matrix_addition(self):
        """测试矩阵加法"""
        logger.info("测试矩阵加法...")
        
        # 创建测试矩阵
        data = np.random.random((50, 50)).astype(np.float32)
        
        cpu_matrix = CPUMatrix(data)
        accel_matrix = AcceleratedMatrix(data)
        
        # CPU加法
        cpu_result = cpu_matrix.add(cpu_matrix)
        
        # 硬件加速加法
        accel_result = accel_matrix.add(accel_matrix)
        
        # 验证结果
        comparison = cpu_result.compare_with(accel_result.to_numpy())
        self.assertTrue(comparison["is_numerically_close"])
        
        logger.info("矩阵加法测试通过")
    
    def test_matrix_transpose(self):
        """测试矩阵转置"""
        logger.info("测试矩阵转置...")
        
        data = np.random.random((30, 40)).astype(np.float32)
        
        cpu_matrix = CPUMatrix(data)
        accel_matrix = AcceleratedMatrix(data)
        
        cpu_transpose = cpu_matrix.transpose()
        accel_transpose = accel_matrix.transpose()
        
        comparison = cpu_transpose.compare_with(accel_transpose.to_numpy())
        self.assertTrue(comparison["is_numerically_close"])
        
        logger.info("矩阵转置测试通过")


class TestPerformanceBenchmark(unittest.TestCase):
    """性能基准测试"""
    
    def setUp(self):
        """测试前置设置"""
        logger.info("开始性能基准测试")
    
    def tearDown(self):
        """测试后置清理"""
        logger.info("性能基准测试完成")
    
    def test_benchmark_execution(self):
        """测试基准测试执行"""
        logger.info("测试基准测试执行...")
        
        # 创建小型基准测试
        benchmark = MatrixBenchmark()
        benchmark.add_test_configuration(
            name="小型测试",
            matrix_sizes=[(50, 50), (100, 100)],
            operations=['multiply', 'add']
        )
        
        # 运行测试
        results = benchmark.run_benchmark(iterations=2)
        
        # 验证结果结构
        self.assertIn('summary', results)
        self.assertIn('individual_results', results)
        self.assertGreater(len(results['individual_results']), 0)
        
        logger.info("基准测试执行测试通过")
    
    def test_performance_statistics(self):
        """测试性能统计"""
        logger.info("测试性能统计...")
        
        # 简单的性能测试
        size = (100, 100)
        a = np.random.random(size).astype(np.float32)
        b = np.random.random(size).astype(np.float32)
        
        # CPU测试
        cpu_a = CPUMatrix(a)
        cpu_b = CPUMatrix(b)
        
        start_time = datetime.now()
        cpu_result = cpu_a.multiply(cpu_b)
        cpu_time = (datetime.now() - start_time).total_seconds()
        
        # 硬件加速测试
        accel_a = AcceleratedMatrix(a)
        accel_b = AcceleratedMatrix(b)
        
        start_time = datetime.now()
        accel_result = accel_a.multiply(accel_b)
        accel_time = (datetime.now() - start_time).total_seconds()
        
        # 性能比较
        if accel_time > 0:
            speedup = cpu_time / accel_time
            logger.info(f"CPU时间: {cpu_time*1000:.2f}ms, 加速时间: {accel_time*1000:.2f}ms, 加速比: {speedup:.2f}x")
        
        # 结果验证
        comparison = cpu_result.compare_with(accel_result.to_numpy())
        self.assertTrue(comparison["is_numerically_close"])
        
        logger.info("性能统计测试通过")


def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行硬件加速模块完整测试套件...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestHardwareAcceleration))
    test_suite.addTest(loader.loadTestsFromTestCase(TestMatrixOperations))
    test_suite.addTest(loader.loadTestsFromTestCase(TestPerformanceBenchmark))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出测试总结
    logger.info("="*50)
    logger.info("测试执行总结:")
    logger.info(f"  运行测试数: {result.testsRun}")
    logger.info(f"  失败数: {len(result.failures)}")
    logger.info(f"  错误数: {len(result.errors)}")
    logger.info(f"  成功率: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    logger.info("="*50)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)