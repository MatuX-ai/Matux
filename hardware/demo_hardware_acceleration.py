"""
硬件加速功能演示脚本
展示FPGA和OpenCL硬件加速的实际效果
"""

import sys
import os
import numpy as np
import time
import logging
from datetime import datetime
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demonstrate_edge_detection():
    """演示边缘检测功能"""
    logger.info("开始边缘检测演示...")
    
    try:
        from hardware.hal.fpga_driver import FPGADriver
        
        # 创建测试图像
        logger.info("创建测试图像...")
        # 创建一个简单的几何图形用于边缘检测
        image = np.zeros((200, 200), dtype=np.uint8)
        
        # 添加一些几何形状
        image[50:150, 50:150] = 255  # 正方形
        image[75:125, 75:125] = 128  # 内部正方形
        image[25:35, 25:175] = 200   # 水平线
        image[25:175, 25:35] = 200   # 垂直线
        
        logger.info(f"测试图像尺寸: {image.shape}")
        
        # 初始化FPGA驱动
        logger.info("初始化FPGA驱动...")
        fpga = FPGADriver()
        if not fpga.initialize():
            logger.error("FPGA初始化失败")
            return False
        
        # 执行边缘检测
        logger.info("执行硬件加速边缘检测...")
        start_time = time.time()
        edge_result = fpga.detect_edges(image, threshold=100)
        fpga_time = time.time() - start_time
        
        logger.info(f"FPGA边缘检测完成，耗时: {fpga_time*1000:.2f}ms")
        
        # 显示结果
        logger.info("显示处理结果...")
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        axes[0].imshow(image, cmap='gray')
        axes[0].set_title('原始图像')
        axes[0].axis('off')
        
        axes[1].imshow(edge_result, cmap='gray')
        axes[1].set_title(f'边缘检测结果\n(阈值=100, 耗时={fpga_time*1000:.2f}ms)')
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig('edge_detection_demo.png', dpi=150, bbox_inches='tight')
        logger.info("结果已保存到 edge_detection_demo.png")
        
        # 统计边缘像素
        edge_pixels = np.sum(edge_result == 255)
        total_pixels = edge_result.size
        edge_ratio = edge_pixels / total_pixels * 100
        
        logger.info(f"边缘像素统计: {edge_pixels}/{total_pixels} ({edge_ratio:.1f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"边缘检测演示失败: {str(e)}")
        return False

def demonstrate_matrix_operations():
    """演示矩阵运算加速"""
    logger.info("开始矩阵运算演示...")
    
    try:
        from hardware.matrix_lib.accelerated_matrix import AcceleratedMatrix
        from hardware.matrix_lib.cpu_matrix import CPUMatrix
        
        # 创建测试矩阵
        logger.info("创建测试矩阵...")
        size = 500
        a_data = np.random.random((size, size)).astype(np.float32)
        b_data = np.random.random((size, size)).astype(np.float32)
        
        logger.info(f"矩阵尺寸: {size}×{size}")
        
        # CPU矩阵运算
        logger.info("执行CPU矩阵运算...")
        cpu_a = CPUMatrix(a_data)
        cpu_b = CPUMatrix(b_data)
        
        start_time = time.time()
        cpu_result = cpu_a.multiply(cpu_b)
        cpu_time = time.time() - start_time
        
        logger.info(f"CPU矩阵乘法耗时: {cpu_time*1000:.2f}ms")
        
        # 硬件加速矩阵运算
        logger.info("执行硬件加速矩阵运算...")
        accel_a = AcceleratedMatrix(a_data)
        accel_b = AcceleratedMatrix(b_data)
        
        start_time = time.time()
        accel_result = accel_a.multiply(accel_b)
        accel_time = time.time() - start_time
        
        logger.info(f"硬件加速矩阵乘法耗时: {accel_time*1000:.2f}ms")
        
        # 性能对比
        speedup = cpu_time / accel_time if accel_time > 0 else 0
        logger.info(f"性能加速比: {speedup:.2f}x")
        
        # 结果验证
        logger.info("验证计算结果...")
        comparison = cpu_result.compare_with(accel_result.to_numpy())
        
        if comparison['is_numerically_close']:
            logger.info("✓ 计算结果验证通过")
            logger.info(f"  最大差异: {comparison['max_difference']:.2e}")
            logger.info(f"  平均差异: {comparison['mean_difference']:.2e}")
        else:
            logger.warning("✗ 计算结果存在较大差异")
            logger.warning(f"  最大差异: {comparison['max_difference']:.2e}")
        
        # 显示性能对比图表
        logger.info("生成性能对比图表...")
        operations = ['矩阵乘法']
        cpu_times = [cpu_time*1000]
        accel_times = [accel_time*1000]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(operations))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, cpu_times, width, label='CPU', alpha=0.8, color='skyblue')
        bars2 = ax.bar(x + width/2, accel_times, width, label='硬件加速', alpha=0.8, color='lightcoral')
        
        ax.set_ylabel('执行时间 (毫秒)')
        ax.set_title('矩阵运算性能对比')
        ax.set_xticks(x)
        ax.set_xticklabels(operations)
        ax.legend()
        
        # 在柱状图上显示数值
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}ms',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),  # 3 points vertical offset
                       textcoords="offset points",
                       ha='center', va='bottom')
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}ms\n({speedup:.1f}x)',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('matrix_performance_demo.png', dpi=150, bbox_inches='tight')
        logger.info("性能对比图表已保存到 matrix_performance_demo.png")
        
        return True
        
    except Exception as e:
        logger.error(f"矩阵运算演示失败: {str(e)}")
        return False

def demonstrate_accelerator_management():
    """演示加速器管理功能"""
    logger.info("开始加速器管理演示...")
    
    try:
        from hardware.hal.accelerator_manager import default_manager
        
        # 配置加速器
        logger.info("配置硬件加速器...")
        configs = [
            {
                "type": "fpga",
                "name": "demo_fpga",
                "config": {"device_path": "/dev/fpga_demo"}
            }
        ]
        
        # 初始化加速器
        logger.info("初始化加速器管理器...")
        success = default_manager.initialize_accelerators(configs)
        
        if not success:
            logger.error("加速器初始化失败")
            return False
        
        # 显示加速器状态
        logger.info("获取加速器状态...")
        status = default_manager.get_accelerator_status()
        
        logger.info("=== 加速器状态报告 ===")
        logger.info(f"活跃加速器: {status['active_accelerator']}")
        logger.info(f"总加速器数: {status['total_accelerators']}")
        logger.info(f"可用加速器数: {len(status['available_accelerators'])}")
        
        for accel in status['available_accelerators']:
            logger.info(f"  - {accel['name']} ({accel['type']})")
        
        # 显示详细信息
        logger.info("\n=== 详细加速器信息 ===")
        for name, details in status['accelerator_details'].items():
            logger.info(f"{name}:")
            logger.info(f"  类型: {details['type']}")
            logger.info(f"  状态: {details['status']}")
            if details['initialized_at']:
                logger.info(f"  初始化时间: {details['initialized_at']}")
        
        # 执行一些操作来收集性能数据
        logger.info("\n执行测试操作以收集性能数据...")
        test_image = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        default_manager.detect_edges(test_image, threshold=128)
        
        # 显示性能摘要
        logger.info("\n=== 性能摘要 ===")
        performance = default_manager.get_performance_summary()
        logger.info(f"总操作数: {performance['total_operations']}")
        
        if performance['recent_operations']:
            logger.info("最近操作:")
            for op in performance['recent_operations'][-3:]:  # 显示最近3个操作
                logger.info(f"  {op['operation']} - {op['duration_ms']:.2f}ms")
        
        return True
        
    except Exception as e:
        logger.error(f"加速器管理演示失败: {str(e)}")
        return False

def main():
    """主演示函数"""
    logger.info("="*60)
    logger.info("硬件加速功能演示开始")
    logger.info("="*60)
    
    start_time = datetime.now()
    
    # 执行各项演示
    demos = [
        ("边缘检测演示", demonstrate_edge_detection),
        ("矩阵运算演示", demonstrate_matrix_operations),
        ("加速器管理演示", demonstrate_accelerator_management)
    ]
    
    results = []
    for demo_name, demo_func in demos:
        logger.info(f"\n{'-'*40}")
        logger.info(f"执行: {demo_name}")
        logger.info(f"{'-'*40}")
        
        try:
            success = demo_func()
            results.append((demo_name, success))
        except Exception as e:
            logger.error(f"{demo_name}执行出错: {str(e)}")
            results.append((demo_name, False))
    
    # 总结
    total_duration = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"\n{'='*60}")
    logger.info("演示总结")
    logger.info(f"{'='*60}")
    logger.info(f"总耗时: {total_duration:.2f}秒")
    logger.info("")
    
    passed_count = 0
    for demo_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"{status}: {demo_name}")
        if success:
            passed_count += 1
    
    logger.info("")
    logger.info(f"成功率: {passed_count}/{len(results)} ({passed_count/len(results)*100:.1f}%)")
    
    if passed_count == len(results):
        logger.info("🎉 所有演示均成功完成！")
    else:
        logger.warning("⚠️  部分演示未能成功完成")
    
    logger.info("="*60)

if __name__ == "__main__":
    main()