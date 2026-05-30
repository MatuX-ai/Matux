"""
模型基准测试API路由
提供Edge Impulse与TensorFlow Lite模型性能对比服务
"""

from datetime import datetime
import os
import shutil
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from utils.logger import setup_logger

router = APIRouter(prefix="/api/v1", tags=["模型基准测试"])

logger = setup_logger("INFO")


class BenchmarkRequest(BaseModel):
    """基准测试请求模型"""

    model_paths: List[str]
    input_shape: str = "(1,40)"
    iterations: int = 100
    temp_test_minutes: int = 2
    hardware_targets: List[str] = ["esp32", "nano", "desktop"]


class BenchmarkResult(BaseModel):
    """基准测试结果模型"""

    test_id: str
    status: str
    results: Optional[Dict[Any, Any]] = None
    created_at: str
    completed_at: Optional[str] = None


# 存储测试结果
benchmark_results = {}


@router.post("/model-benchmark/start", response_model=BenchmarkResult)
async def start_model_benchmark(
    request: BenchmarkRequest, background_tasks: BackgroundTasks
):
    """
    启动模型基准测试

    Args:
        request: 基准测试配置参数
        background_tasks: 后台任务处理器

    Returns:
        BenchmarkResult: 测试任务信息
    """
    test_id = str(uuid.uuid4())

    # 验证模型文件存在
    for model_path in request.model_paths:
        if not os.path.exists(model_path):
            raise HTTPException(status_code=400, detail=f"模型文件不存在: {model_path}")

    # 创建测试任务
    benchmark_results[test_id] = {
        "test_id": test_id,
        "status": "running",
        "request": request.dict(),
        "results": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }

    # 在后台执行测试
    background_tasks.add_task(run_benchmark_async, test_id, request)

    logger.info(f"启动基准测试任务: {test_id}")
    return BenchmarkResult(**benchmark_results[test_id])


@router.get("/model-benchmark/{test_id}", response_model=BenchmarkResult)
async def get_benchmark_result(test_id: str):
    """
    获取基准测试结果

    Args:
        test_id: 测试任务ID

    Returns:
        BenchmarkResult: 测试结果
    """
    if test_id not in benchmark_results:
        raise HTTPException(status_code=404, detail="测试任务不存在")

    return BenchmarkResult(**benchmark_results[test_id])


@router.get("/model-benchmark/results")
async def list_benchmark_results(limit: int = 10):
    """
    列出最近的基准测试结果

    Args:
        limit: 返回结果数量限制

    Returns:
        List[BenchmarkResult]: 测试结果列表
    """
    results = list(benchmark_results.values())[-limit:]
    return [BenchmarkResult(**result) for result in results]


@router.post("/model-benchmark/upload")
async def upload_model_for_benchmark(
    model_file: UploadFile = File(...),
    model_name: str = Form(...),
    model_type: str = Form("tflite"),
):
    """
    上传模型文件用于基准测试

    Args:
        model_file: 模型文件
        model_name: 模型名称
        model_type: 模型类型 (tflite, keras, savedmodel)

    Returns:
        dict: 上传结果和文件路径
    """
    try:
        # 创建上传目录
        upload_dir = os.path.join("uploads", "models")
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_extension = model_file.filename.split(".")[-1]
        safe_filename = f"{model_name}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(model_file.file, buffer)

        logger.info(f"模型文件上传成功: {file_path}")

        return {
            "filename": model_file.filename,
            "saved_path": file_path,
            "model_name": model_name,
            "model_type": model_type,
            "file_size": os.path.getsize(file_path),
        }

    except Exception as e:
        logger.error(f"模型文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/model-benchmark/templates")
async def get_benchmark_templates():
    """
    获取基准测试模板配置

    Returns:
        dict: 预定义的测试模板
    """
    templates = {
        "voice_recognition": {
            "name": "语音识别基准测试",
            "description": "测试语音命令识别模型性能",
            "default_input_shape": "(1,40)",
            "default_iterations": 100,
            "recommended_hardware": ["esp32", "nano"],
            "sample_models": [
                "models/tinyml/tensorflow_lite/voice_model.tflite",
                "models/tinyml/edge_impulse/voice_commands/ei-voice-model-v1.0.0/ei-voice-model-v1.0.0.tflite",
            ],
        },
        "gesture_recognition": {
            "name": "手势识别基准测试",
            "description": "测试手势识别模型性能",
            "default_input_shape": "(1,60)",
            "default_iterations": 50,
            "recommended_hardware": ["nano", "desktop"],
            "sample_models": ["models/tinyml/tensorflow_lite/gesture_model.tflite"],
        },
        "anomaly_detection": {
            "name": "异常检测基准测试",
            "description": "测试异常检测模型性能",
            "default_input_shape": "(1,32)",
            "default_iterations": 200,
            "recommended_hardware": ["esp32", "desktop"],
            "sample_models": ["models/tinyml/tensorflow_lite/anomaly_model.tflite"],
        },
    }

    return templates


@router.get("/model-benchmark/hardware-profiles")
async def get_hardware_profiles():
    """
    获取硬件平台配置信息

    Returns:
        dict: 硬件平台详细信息
    """
    profiles = {
        "esp32": {
            "name": "ESP32-WROOM-32",
            "cpu": "Xtensa LX6 (双核)",
            "ram": "520KB SRAM",
            "flash": "4MB SPI Flash",
            "max_frequency": "240MHz",
            "power_consumption": "120mA (active)",
            "typical_use_cases": ["语音识别", "传感器数据处理", "IoT应用"],
            "constraints": {
                "max_model_size_mb": 2.0,
                "max_ram_usage_kb": 400,
                "min_inference_fps": 5,
            },
        },
        "nano": {
            "name": "Arduino Nano 33 BLE Sense",
            "cpu": "ARM Cortex-M4F",
            "ram": "256KB RAM",
            "flash": "1MB Flash",
            "max_frequency": "64MHz",
            "power_consumption": "80mA (active)",
            "typical_use_cases": ["简单分类", "运动检测", "环境监测"],
            "constraints": {
                "max_model_size_mb": 1.0,
                "max_ram_usage_kb": 200,
                "min_inference_fps": 10,
            },
        },
        "desktop": {
            "name": "Desktop/Laptop CPU",
            "cpu": "Intel/AMD x86_64",
            "ram": f"{os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') // (1024**3)}GB RAM",
            "flash": "SSD/HDD Storage",
            "max_frequency": "Variable",
            "power_consumption": "5000mA (estimate)",
            "typical_use_cases": ["模型训练", "复杂推理", "批量处理"],
            "constraints": {
                "max_model_size_mb": 1000,
                "max_ram_usage_kb": float("inf"),
                "min_inference_fps": 1000,
            },
        },
    }

    return profiles


async def run_benchmark_async(test_id: str, request: BenchmarkRequest):
    """
    异步执行基准测试

    Args:
        test_id: 测试任务ID
        request: 测试请求参数
    """
    try:
        logger.info(f"开始执行基准测试: {test_id}")

        # 导入基准测试模块
        import sys

        sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

        from model_benchmark import ModelBenchmark

        # 创建基准测试实例
        benchmark = ModelBenchmark()

        # 解析输入形状
        try:
            input_shape = tuple(map(int, request.input_shape.strip("()").split(",")))
        except Exception as e:
            raise ValueError(f"输入形状解析失败: {e}")

        # 执行对比测试
        results = benchmark.compare_models(request.model_paths, input_shape)

        # 生成完整报告
        report = {
            "test_id": test_id,
            "test_timestamp": datetime.now().isoformat(),
            "test_parameters": {
                "input_shape": request.input_shape,
                "iterations": request.iterations,
                "temperature_test_minutes": request.temp_test_minutes,
                "hardware_targets": request.hardware_targets,
            },
            "comparison_results": results,
            "summary": (
                benchmark.generate_summary(results)
                if hasattr(benchmark, "generate_summary")
                else {}
            ),
            "recommendations": generate_recommendations(results),
        }

        # 更新测试结果
        benchmark_results[test_id].update(
            {
                "status": "completed",
                "results": report,
                "completed_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"基准测试完成: {test_id}")

    except Exception as e:
        logger.error(f"基准测试执行失败 {test_id}: {e}")
        benchmark_results[test_id].update(
            {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat(),
            }
        )


def generate_recommendations(results: Dict) -> List[str]:
    """
    基于测试结果生成推荐建议

    Args:
        results: 测试结果数据

    Returns:
        List[str]: 推荐建议列表
    """
    recommendations = []

    for model_name, metrics in results.items():
        # 基于模型大小的建议
        size_mb = metrics.get("size_metrics", {}).get("file_size_mb", 0)
        if size_mb > 2.0:
            recommendations.append(f"{model_name}: 模型过大({size_mb}MB)，建议量化优化")
        elif size_mb > 1.0:
            recommendations.append(f"{model_name}: 模型适中({size_mb}MB)，适合ESP32")
        else:
            recommendations.append(
                f"{model_name}: 模型较小({size_mb}MB)，适合Nano等资源受限设备"
            )

        # 基于推理速度的建议
        avg_latency = metrics.get("speed_metrics", {}).get("avg_latency_ms", 1000)
        if avg_latency > 500:
            recommendations.append(
                f"{model_name}: 推理较慢({avg_latency}ms)，建议模型压缩"
            )
        elif avg_latency > 200:
            recommendations.append(f"{model_name}: 推理速度一般({avg_latency}ms)")
        else:
            recommendations.append(f"{model_name}: 推理速度快({avg_latency}ms)")

        # 基于稳定性的建议
        stability_score = metrics.get("temperature_stability", {}).get(
            "stability_score", 0
        )
        if stability_score < 70:
            recommendations.append(
                f"{model_name}: 稳定性较差({stability_score}分)，建议优化"
            )
        elif stability_score < 90:
            recommendations.append(f"{model_name}: 稳定性良好({stability_score}分)")
        else:
            recommendations.append(f"{model_name}: 稳定性优秀({stability_score}分)")

    return recommendations
