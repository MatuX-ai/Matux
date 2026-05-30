"""
Edge Impulse API客户端集成模块
提供与Edge Impulse平台的完整API交互能力
支持模型训练、部署、压缩和管理功能
"""

import base64
from datetime import datetime
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)


class EdgeImpulseClient:
    """Edge Impulse API客户端"""

    def __init__(self, api_key: str = None, project_id: str = None):
        """
        初始化Edge Impulse客户端

        Args:
            api_key: Edge Impulse API密钥
            project_id: 项目ID
        """
        self.api_key = api_key or os.getenv("EDGE_IMPULSE_API_KEY")
        self.project_id = project_id or os.getenv("EDGE_IMPULSE_PROJECT_ID")
        self.base_url = "https://studio.edgeimpulse.com/v1/api"
        self.headers = (
            {"x-api-key": self.api_key, "Content-Type": "application/json"}
            if self.api_key
            else {}
        )

        if not self.api_key:
            logger.warning("未设置Edge Impulse API密钥，部分功能将受限")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败 {method} {endpoint}: {e}")
            raise

    def get_projects(self) -> List[Dict[str, Any]]:
        """获取项目列表"""
        response = self._make_request("GET", "/projects")
        return response.get("projects", [])

    def get_project_info(self, project_id: str = None) -> Dict[str, Any]:
        """获取项目信息"""
        project_id = project_id or self.project_id
        if not project_id:
            raise ValueError("必须提供项目ID")

        response = self._make_request("GET", f"/projects/{project_id}")
        return response

    def upload_training_data(
        self, data_path: str, category: str = "training"
    ) -> Dict[str, Any]:
        """
        上传训练数据

        Args:
            data_path: 数据文件路径
            category: 数据类别 (training/validation/testing)
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"数据文件不存在: {data_path}")

        # 读取数据文件
        with open(data_path, "rb") as f:
            file_content = f.read()

        # 准备上传数据
        payload = {
            "data": base64.b64encode(file_content).decode("utf-8"),
            "filename": os.path.basename(data_path),
            "category": category,
        }

        response = self._make_request(
            "POST", f"/projects/{self.project_id}/raw-data", json=payload
        )

        logger.info(f"数据上传成功: {data_path}")
        return response

    def start_training_job(
        self,
        model_type: str = "classification",
        input_shape: List[int] = None,
        output_classes: int = None,
        architecture: str = "MobileNetV2",
        target_device: str = "ESP32",
    ) -> Dict[str, Any]:
        """
        启动模型训练作业

        Args:
            model_type: 模型类型 (classification/regression/anomaly)
            input_shape: 输入形状 [batch_size, features]
            output_classes: 输出类别数
            architecture: 网络架构
            target_device: 目标设备
        """
        if not input_shape:
            input_shape = [1, 40]  # 默认语音特征维度

        if not output_classes:
            output_classes = 5  # 默认类别数

        training_config = {
            "modelType": model_type,
            "inputShape": input_shape,
            "outputClasses": output_classes,
            "neuralNetwork": {
                "blockTypes": [architecture],
                "learningRate": 0.001,
                "epochs": 100,
                "validationSplit": 0.2,
            },
            "targetDevice": target_device,
            "optimizeFor": "latency",
        }

        response = self._make_request(
            "POST",
            f"/projects/{self.project_id}/jobs",
            json={"jobType": "train", "config": training_config},
        )

        job_id = response.get("id")
        logger.info(f"训练作业已启动，作业ID: {job_id}")
        return response

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """获取作业状态"""
        response = self._make_request(
            "GET", f"/projects/{self.project_id}/jobs/{job_id}"
        )
        return response

    def wait_for_job_completion(
        self, job_id: str, timeout: int = 3600
    ) -> Dict[str, Any]:
        """等待作业完成"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            job_state = status.get("job", {}).get("status")

            if job_state == "completed":
                logger.info(f"作业 {job_id} 已完成")
                return status
            elif job_state == "failed":
                raise Exception(f"作业 {job_id} 失败: {status}")
            elif job_state == "running":
                logger.info(f"作业 {job_id} 运行中...")
                time.sleep(30)  # 每30秒检查一次
            else:
                logger.info(f"作业 {job_id} 状态: {job_state}")
                time.sleep(10)

        raise TimeoutError(f"作业 {job_id} 超时未完成")

    def export_model(
        self,
        model_id: str,
        format: str = "tflite",
        quantization: str = "int8",
        compression_target_kb: int = 250,
    ) -> Dict[str, Any]:
        """
        导出训练好的模型

        Args:
            model_id: 模型ID
            format: 导出格式 (tflite/onnx/tensorflow)
            quantization: 量化类型 (int8/float32)
            compression_target_kb: 压缩目标大小(KB)
        """
        export_config = {
            "modelId": model_id,
            "format": format,
            "quantization": quantization,
            "compression": {
                "enabled": True,
                "targetSizeKb": compression_target_kb,
                "strategy": "aggressive",  # 激进压缩策略以达到250KB目标
            },
        }

        response = self._make_request(
            "POST", f"/projects/{self.project_id}/models/export", json=export_config
        )

        export_id = response.get("id")
        logger.info(f"模型导出已启动，导出ID: {export_id}")
        return response

    def download_exported_model(self, export_id: str, save_path: str) -> str:
        """下载导出的模型"""
        # 首先检查导出状态
        export_status = self._make_request(
            "GET", f"/projects/{self.project_id}/models/export/{export_id}"
        )

        if export_status.get("status") != "completed":
            raise Exception(f"导出未完成: {export_status}")

        # 下载模型文件
        download_url = export_status.get("downloadUrl")
        if not download_url:
            raise Exception("未找到下载URL")

        response = requests.get(download_url)
        response.raise_for_status()

        # 保存文件
        with open(save_path, "wb") as f:
            f.write(response.content)

        file_size_kb = os.path.getsize(save_path) / 1024
        logger.info(f"模型已下载到: {save_path} ({file_size_kb:.1f}KB)")
        return save_path

    def optimize_model_for_edge(
        self, model_path: str, target_size_kb: int = 250, target_device: str = "ESP32"
    ) -> Dict[str, Any]:
        """
        为边缘设备优化模型

        Args:
            model_path: 模型文件路径
            target_size_kb: 目标大小(KB)
            target_device: 目标设备
        """
        # 上传模型进行优化
        with open(model_path, "rb") as f:
            model_content = f.read()

        optimize_config = {
            "model": base64.b64encode(model_content).decode("utf-8"),
            "targetSizeKb": target_size_kb,
            "targetDevice": target_device,
            "optimizationLevel": "maximum",  # 最大优化级别
        }

        response = self._make_request(
            "POST", f"/projects/{self.project_id}/models/optimize", json=optimize_config
        )

        optimization_id = response.get("id")
        logger.info(f"模型优化已启动，优化ID: {optimization_id}")
        return response

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        response = self._make_request(
            "GET", f"/projects/{self.project_id}/models/{model_id}"
        )
        return response

    def list_models(self) -> List[Dict[str, Any]]:
        """列出所有模型"""
        response = self._make_request("GET", f"/projects/{self.project_id}/models")
        return response.get("models", [])

    def delete_model(self, model_id: str) -> bool:
        """删除模型"""
        try:
            self._make_request(
                "DELETE", f"/projects/{self.project_id}/models/{model_id}"
            )
            logger.info(f"模型 {model_id} 已删除")
            return True
        except Exception as e:
            logger.error(f"删除模型失败: {e}")
            return False


class EdgeImpulseModelManager:
    """Edge Impulse模型管理器"""

    def __init__(self, client: EdgeImpulseClient):
        self.client = client
        self.models_dir = Path("models/tinyml/edge_impulse")
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def train_and_deploy_model(
        self,
        training_data_path: str,
        model_name: str,
        target_size_kb: int = 250,
        target_device: str = "ESP32",
    ) -> Dict[str, Any]:
        """
        训练并部署模型到指定大小

        Args:
            training_data_path: 训练数据路径
            model_name: 模型名称
            target_size_kb: 目标大小(KB)
            target_device: 目标设备
        """
        logger.info(f"开始训练模型: {model_name}")

        # 1. 上传训练数据
        self.client.upload_training_data(training_data_path)

        # 2. 启动训练作业
        train_response = self.client.start_training_job(
            model_type="classification", target_device=target_device
        )

        job_id = train_response.get("id")

        # 3. 等待训练完成
        job_result = self.client.wait_for_job_completion(job_id)

        # 4. 获取训练好的模型ID
        model_id = job_result.get("job", {}).get("modelId")
        if not model_id:
            raise Exception("未找到训练完成的模型ID")

        # 5. 导出并压缩模型
        export_response = self.client.export_model(
            model_id=model_id,
            format="tflite",
            quantization="int8",
            compression_target_kb=target_size_kb,
        )

        export_id = export_response.get("id")

        # 6. 等待导出完成并下载
        export_result = self.client.wait_for_job_completion(export_id)
        export_result.get("downloadUrl")

        # 7. 保存模型文件
        model_save_path = self.models_dir / f"{model_name}.tflite"
        downloaded_path = self.client.download_exported_model(
            export_id, str(model_save_path)
        )

        # 8. 验证模型大小
        actual_size_kb = os.path.getsize(downloaded_path) / 1024
        if actual_size_kb > target_size_kb:
            logger.warning(
                f"模型大小超出目标: {actual_size_kb:.1f}KB > {target_size_kb}KB"
            )

        result = {
            "model_name": model_name,
            "model_id": model_id,
            "export_id": export_id,
            "local_path": downloaded_path,
            "size_kb": actual_size_kb,
            "target_size_kb": target_size_kb,
            "compression_ratio": (
                target_size_kb / actual_size_kb if actual_size_kb > 0 else 1.0
            ),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"模型训练部署完成: {model_name}")
        return result

    def batch_process_models(
        self, model_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量处理多个模型"""
        results = []

        for config in model_configs:
            try:
                result = self.train_and_deploy_model(**config)
                results.append(result)
                logger.info(f"模型 {config['model_name']} 处理完成")
            except Exception as e:
                logger.error(
                    f"模型 {config.get('model_name', 'Unknown')} 处理失败: {e}"
                )
                results.append(
                    {
                        "model_name": config.get("model_name", "Unknown"),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results


# 使用示例和测试函数
def demo_edge_impulse_integration():
    """演示Edge Impulse集成功能"""
    print("=== Edge Impulse API集成演示 ===")

    # 初始化客户端
    try:
        client = EdgeImpulseClient()
        EdgeImpulseModelManager(client)

        print("✅ Edge Impulse客户端初始化成功")

        # 检查项目信息
        try:
            project_info = client.get_project_info()
            print(f"项目信息: {project_info.get('name', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  无法获取项目信息: {e}")

        # 列出模型
        try:
            models = client.list_models()
            print(f"现有模型数量: {len(models)}")
        except Exception as e:
            print(f"⚠️  无法列出模型: {e}")

    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        return

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    demo_edge_impulse_integration()
