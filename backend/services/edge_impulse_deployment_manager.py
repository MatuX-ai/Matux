"""
Edge Impulse模型管理和部署工具
提供完整的模型生命周期管理，包括训练、压缩、验证和部署
"""

from datetime import datetime
import json
import logging
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List

from .edge_impulse_client import EdgeImpulseClient, EdgeImpulseModelManager
from .tinyml_compressor_250kb import TinyMLModelCompressor250KB

logger = logging.getLogger(__name__)


class EdgeImpulseDeploymentManager:
    """Edge Impulse模型部署管理器"""

    def __init__(
        self, api_key: str = None, project_id: str = None, target_size_kb: int = 250
    ):
        """
        初始化部署管理器

        Args:
            api_key: Edge Impulse API密钥
            project_id: 项目ID
            target_size_kb: 目标模型大小(KB)
        """
        self.client = EdgeImpulseClient(api_key, project_id)
        self.model_manager = EdgeImpulseModelManager(self.client)
        self.compressor = TinyMLModelCompressor250KB(target_size_kb)
        self.target_size_kb = target_size_kb

        # 创建必要的目录
        self.models_base_dir = Path("models/tinyml")
        self.edge_impulse_dir = self.models_base_dir / "edge_impulse"
        self.deployment_dir = self.models_base_dir / "deployments"

        for directory in [self.edge_impulse_dir, self.deployment_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def deploy_model_from_scratch(
        self,
        model_name: str,
        training_data_path: str,
        target_device: str = "ESP32",
        labels: List[str] = None,
    ) -> Dict[str, Any]:
        """
        从头开始部署模型：训练 -> 压缩 -> 验证 -> 部署

        Args:
            model_name: 模型名称
            training_data_path: 训练数据路径
            target_device: 目标设备
            labels: 类别标签列表

        Returns:
            部署结果信息
        """
        logger.info(f"开始从头部署模型: {model_name}")

        deployment_result = {
            "model_name": model_name,
            "target_device": target_device,
            "target_size_kb": self.target_size_kb,
            "phases": {},
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 阶段1: Edge Impulse训练
            logger.info("阶段1: Edge Impulse模型训练...")
            train_result = self.model_manager.train_and_deploy_model(
                training_data_path=training_data_path,
                model_name=f"{model_name}_ei_raw",
                target_size_kb=self.target_size_kb * 2,  # 先训练稍大的模型
                target_device=target_device,
            )
            deployment_result["phases"]["training"] = train_result

            # 阶段2: 本地压缩优化
            logger.info("阶段2: 本地压缩优化至250KB...")
            compressed_result = self._compress_model_locally(
                train_result["local_path"], model_name
            )
            deployment_result["phases"]["compression"] = compressed_result

            # 阶段3: 质量验证
            logger.info("阶段3: 模型质量验证...")
            validation_result = self._validate_model_quality(
                compressed_result["local_path"], labels
            )
            deployment_result["phases"]["validation"] = validation_result

            # 阶段4: 部署准备
            logger.info("阶段4: 部署包准备...")
            deployment_package = self._prepare_deployment_package(
                model_name, compressed_result["local_path"], labels, target_device
            )
            deployment_result["phases"]["deployment"] = deployment_package

            # 更新总体状态
            deployment_result["success"] = True
            deployment_result["final_model_path"] = compressed_result["local_path"]
            deployment_result["final_size_kb"] = compressed_result["size_kb"]

            logger.info(f"模型部署成功: {model_name}")

        except Exception as e:
            logger.error(f"模型部署失败: {e}")
            deployment_result["success"] = False
            deployment_result["error"] = str(e)

        # 保存部署记录
        self._save_deployment_record(deployment_result)
        return deployment_result

    def batch_deploy_models(
        self, deployment_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量部署多个模型

        Args:
            deployment_configs: 部署配置列表

        Returns:
            部署结果列表
        """
        results = []

        for config in deployment_configs:
            try:
                result = self.deploy_model_from_scratch(**config)
                results.append(result)
                if result["success"]:
                    logger.info(f"✅ 模型 {config['model_name']} 部署成功")
                else:
                    logger.error(
                        f"❌ 模型 {config['model_name']} 部署失败: {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                error_result = {
                    "model_name": config.get("model_name", "Unknown"),
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                results.append(error_result)
                logger.error(
                    f"❌ 模型 {config.get('model_name', 'Unknown')} 部署异常: {e}"
                )

        return results

    def _compress_model_locally(
        self, model_path: str, model_name: str
    ) -> Dict[str, Any]:
        """本地压缩模型到目标大小"""

        # 加载模型
        import tensorflow as tf

        model = tf.keras.models.load_model(model_path.replace(".tflite", "_keras"))

        # 确定输出路径
        compressed_path = str(self.edge_impulse_dir / f"{model_name}_250kb.tflite")

        # 执行压缩
        compression_result = self.compressor.compress_to_target_size(
            model=model,
            input_shape=(1, 40),  # 默认输入形状
            output_path=compressed_path,
        )

        # 验证压缩质量
        quality_result = self.compressor.validate_compression_quality(
            model, compressed_path
        )

        return {
            "local_path": compressed_path,
            "size_kb": compression_result["size_kb"],
            "strategy_used": compression_result["strategy"],
            "quality_metrics": quality_result,
            "compression_success": compression_result["success"],
        }

    def _validate_model_quality(
        self, model_path: str, labels: List[str] = None
    ) -> Dict[str, Any]:
        """验证模型质量"""

        validation_result = {
            "model_path": model_path,
            "file_size_kb": os.path.getsize(model_path) / 1024,
            "meets_size_requirement": os.path.getsize(model_path) / 1024
            <= self.target_size_kb,
            "labels": labels or [],
            "validation_timestamp": datetime.now().isoformat(),
        }

        # 基本验证
        try:
            import tensorflow as tf

            interpreter = tf.lite.Interpreter(model_path=model_path)
            interpreter.allocate_tensors()

            # 获取模型信息
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            validation_result.update(
                {
                    "input_shape": input_details[0]["shape"].tolist(),
                    "output_shape": output_details[0]["shape"].tolist(),
                    "input_type": str(input_details[0]["dtype"]),
                    "output_type": str(output_details[0]["dtype"]),
                }
            )

            validation_result["basic_validation_passed"] = True

        except Exception as e:
            validation_result["basic_validation_passed"] = False
            validation_result["validation_error"] = str(e)

        return validation_result

    def _prepare_deployment_package(
        self, model_name: str, model_path: str, labels: List[str], target_device: str
    ) -> Dict[str, Any]:
        """准备部署包"""

        # 创建部署目录
        deployment_path = self.deployment_dir / model_name
        deployment_path.mkdir(exist_ok=True)

        # 复制模型文件
        model_filename = f"{model_name}.tflite"
        shutil.copy2(model_path, deployment_path / model_filename)

        # 创建元数据文件
        metadata = {
            "model_name": model_name,
            "model_version": "1.0.0",
            "target_device": target_device,
            "labels": labels or [],
            "input_shape": [1, 40],
            "created_at": datetime.now().isoformat(),
            "file_size_kb": os.path.getsize(model_path) / 1024,
            "checksum": self._calculate_checksum(model_path),
        }

        metadata_path = deployment_path / f"{model_name}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # 创建部署说明
        readme_content = self._generate_deployment_readme(model_name, metadata)
        readme_path = deployment_path / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        return {
            "deployment_path": str(deployment_path),
            "model_file": model_filename,
            "metadata_file": f"{model_name}_metadata.json",
            "readme_file": "README.md",
            "package_size_kb": self._get_directory_size(deployment_path) / 1024,
        }

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        import hashlib

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_directory_size(self, directory: Path) -> int:
        """获取目录总大小"""
        total_size = 0
        for item in directory.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    def _generate_deployment_readme(
        self, model_name: str, metadata: Dict[str, Any]
    ) -> str:
        """生成部署说明文档"""
        readme_template = f"""# {model_name} 部署包

## 模型信息
- **模型名称**: {metadata['model_name']}
- **版本**: {metadata['model_version']}
- **目标设备**: {metadata['target_device']}
- **创建时间**: {metadata['created_at']}

## 技术规格
- **输入形状**: {metadata['input_shape']}
- **输出类别**: {len(metadata['labels'])}
- **标签列表**: {', '.join(metadata['labels'])}
- **文件大小**: {metadata['file_size_kb']:.1f} KB
- **校验和**: {metadata['checksum']}

## 部署说明

### ESP32部署
```cpp
#include <TensorFlowLite.h>
#include "{model_name}.h"

// 初始化解释器
tflite::MicroInterpreter interpreter;

// 输入数据准备
float input_data[{metadata['input_shape'][1]}];

// 执行推理
interpreter.Invoke();

// 获取结果
float* output = interpreter.output(0)->data.f;
```

### Arduino部署
1. 将 `.tflite` 文件转换为Arduino库
2. 在Arduino IDE中包含生成的库
3. 按照示例代码进行推理

## 性能指标
- **模型大小**: {metadata['file_size_kb']:.1f} KB (≤ {self.target_size_kb} KB)
- **内存需求**: ~{(metadata['file_size_kb'] * 3):.0f} KB (估算)
- **推理时间**: 设备相关

## 注意事项
- 确保目标设备有足够的Flash和RAM空间
- 部署前请验证模型在目标设备上的兼容性
- 建议在实际应用前进行充分测试

---
自动生成于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return readme_template

    def _save_deployment_record(self, deployment_result: Dict[str, Any]):
        """保存部署记录"""
        records_dir = Path("deployment_records")
        records_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        record_filename = (
            f"deployment_{deployment_result['model_name']}_{timestamp}.json"
        )
        record_path = records_dir / record_filename

        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(deployment_result, f, indent=2, ensure_ascii=False)

        logger.info(f"部署记录已保存: {record_path}")


# 使用示例
def demo_deployment_manager():
    """演示部署管理器功能"""
    print("=== Edge Impulse部署管理器演示 ===")

    try:
        # 初始化管理器
        manager = EdgeImpulseDeploymentManager(target_size_kb=250)

        print("✅ 部署管理器初始化成功")

        # 演示单个模型部署
        print("\n1. 演示单个模型部署...")
        # 注意：这里需要真实的训练数据路径
        # deployment_result = manager.deploy_model_from_scratch(
        #     model_name="demo_voice_commands",
        #     training_data_path="path/to/training/data.json",
        #     target_device="ESP32",
        #     labels=["开灯", "关灯", "播放音乐", "停止播放", "其他"]
        # )
        # print(f"   部署结果: {deployment_result['success']}")

        # 演示批量部署配置
        print("\n2. 演示批量部署配置...")
        batch_configs = [
            {
                "model_name": "voice_commands_v1",
                "training_data_path": "data/voice_commands_train.json",
                "target_device": "ESP32",
                "labels": ["on", "off", "play", "stop", "other"],
            },
            {
                "model_name": "gesture_recognition_v1",
                "training_data_path": "data/gesture_train.json",
                "target_device": "Arduino Nano 33 BLE",
                "labels": ["up", "down", "left", "right", "tap"],
            },
        ]

        print("   批量部署配置:")
        for config in batch_configs:
            print(f"   - {config['model_name']} -> {config['target_device']}")

        print("\n=== 演示完成 ===")
        print("💡 实际使用时请提供真实的训练数据路径和API密钥")

    except Exception as e:
        print(f"❌ 演示失败: {e}")


if __name__ == "__main__":
    demo_deployment_manager()
