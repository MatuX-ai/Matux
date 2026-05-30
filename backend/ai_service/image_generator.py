"""
DALL-E 3图像生成服务
集成OpenAI DALL-E 3 API，提供创意图像生成功能
"""

import asyncio
import base64
import io
import logging
import time
from typing import Any, Dict, List

from PIL import Image  # type: ignore[import-untyped]
import httpx

from config.settings import settings
from models.creativity_models import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageStyle,
)

logger = logging.getLogger(__name__)


class DalleImageGenerator:
    """DALL-E 3图像生成器"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.timeout = 30  # 30秒超时
        self._validate_configuration()

    def _validate_configuration(self):
        """验证配置"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 未配置")

        if not self.api_key.startswith("sk-"):
            logger.warning("OpenAI API密钥格式可能不正确")

    async def generate_images(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """
        生成创意图像

        Args:
            request: 图像生成请求

        Returns:
            ImageGenerationResponse: 图像生成响应
        """
        start_time = time.time()
        logger.info(f"开始生成图像: {request.prompt[:50]}...")

        try:
            # 验证请求参数
            self._validate_request(request)

            # 构建API请求
            api_payload = self._build_api_payload(request)

            # 调用DALL-E API
            api_response = await self._call_dalle_api(api_payload)

            # 处理响应数据
            images_data = self._process_api_response(api_response)

            # 计算成本和处理时间
            processing_time = time.time() - start_time
            total_cost = self._calculate_cost(
                len(images_data), request.quality
            )

            response = ImageGenerationResponse(
                images=images_data,
                processing_time=processing_time,
                total_cost=total_cost,
            )

            logger.info(
                f"图像生成完成，生成{len(images_data)}张图片，耗时: {processing_time:.2f}秒"
            )
            return response

        except Exception as e:
            logger.error(f"图像生成失败: {str(e)}")
            raise

    def _validate_request(self, request: ImageGenerationRequest):
        """验证请求参数"""
        # 验证Prompt长度
        if len(request.prompt) < 10:
            raise ValueError("Prompt长度不能少于10个字符")

        if len(request.prompt) > 1000:
            raise ValueError("Prompt长度不能超过1000个字符")

        # 验证图像尺寸
        if not self._is_valid_size(request.size):
            raise ValueError(f"不支持的图像尺寸: {request.size}")

        # 验证生成数量
        if request.n < 1 or request.n > 10:
            raise ValueError("生成数量必须在1-10之间")

        # 内容安全检查
        if self._contains_inappropriate_content(request.prompt):
            raise ValueError("Prompt包含不当内容")

    def _is_valid_size(self, size: str) -> bool:
        """验证图像尺寸"""
        supported_sizes = ["1024x1024", "1024x1792", "1792x1024"]
        return size in supported_sizes

    def _contains_inappropriate_content(self, prompt: str) -> bool:
        """检查是否包含不当内容"""
        inappropriate_keywords = [
            "暴力",
            "血腥",
            "色情",
            "成人",
            "仇恨",
            "歧视",
            "violence",
            "blood",
            "porn",
            "adult",
            "hate",
            "discrimination",
        ]

        prompt_lower = prompt.lower()
        return any(
            keyword in prompt_lower for keyword in inappropriate_keywords
        )

    def _build_api_payload(
        self, request: ImageGenerationRequest
    ) -> Dict[str, Any]:
        """构建API请求载荷"""
        # 将图像风格映射到DALL-E支持的风格
        style_mapping = {
            ImageStyle.REALISTIC: "natural",
            ImageStyle.ARTISTIC: "vivid",
            ImageStyle.CARTOON: "vivid",
            ImageStyle.PHOTOGRAPHIC: "natural",
            ImageStyle.DIGITAL_ART: "vivid",
            ImageStyle.THREE_D_RENDER: "vivid",
        }

        payload = {
            "model": "dall-e-3",
            "prompt": request.prompt,
            "n": request.n,
            "size": request.size,
            "quality": request.quality,
            "style": style_mapping.get(request.style, "vivid"),
        }

        # 添加响应格式
        payload["response_format"] = "url"  # 或者 "b64_json"

        return payload

    async def _call_dalle_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """调用DALL-E API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                logger.error("DALL-E API调用超时")
                raise TimeoutError("图像生成超时，请稍后重试")
            except httpx.HTTPStatusError as e:
                error_detail = e.response.json()
                logger.error(f"DALL-E API错误: {error_detail}")
                err_msg = error_detail.get("error", {}).get(
                    "message", "未知错误"
                )
                raise RuntimeError(f"API调用失败: {err_msg}")
            except Exception as e:
                logger.error(f"DALL-E API调用异常: {str(e)}")
                raise

    def _process_api_response(
        self, api_response: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """处理API响应数据"""
        images_data = []

        for i, image_info in enumerate(api_response.get("data", [])):
            image_data = {
                "url": image_info.get("url", ""),
                "revised_prompt": image_info.get("revised_prompt", ""),
                "index": i,
            }

            # 如果返回的是base64编码的数据
            if "b64_json" in image_info:
                image_data["b64_data"] = image_info["b64_json"]
                image_data["url"] = self._save_base64_image(
                    image_info["b64_json"], i
                )

            images_data.append(image_data)

        return images_data

    def _save_base64_image(self, b64_data: str, index: int) -> str:
        """保存base64编码的图像"""
        try:
            # 解码base64数据
            image_data = base64.b64decode(b64_data)

            # 创建图像对象
            Image.open(io.BytesIO(image_data))

            # 生成文件名
            filename = f"dalle_generated_{int(time.time())}_{index}.png"

            # 保存图像（这里简化处理，实际应用中可能需要保存到云存储）
            # image.save(f"./generated_images/{filename}")

            return f"/generated_images/{filename}"

        except Exception as e:
            logger.error(f"保存图像失败: {str(e)}")
            return ""

    def _calculate_cost(self, image_count: int, quality: str) -> float:
        """计算生成成本"""
        # DALL-E 3定价（2024年标准）
        base_prices = {
            "standard": 0.040,  # 每张标准质量图片
            "hd": 0.080,  # 每张高清质量图片
        }

        price_per_image = base_prices.get(quality, base_prices["standard"])
        return round(image_count * price_per_image, 4)

    async def generate_image_variations(
        self, image_url: str, n: int = 1
    ) -> List[Dict[str, str]]:
        """
        生成图像变体

        Args:
            image_url: 原始图像URL
            n: 生成变体数量

        Returns:
            List[Dict[str, str]]: 变体图像数据列表
        """
        logger.info(f"生成图像变体: {image_url}")

        try:
            # 下载原始图像
            original_image = await self._download_image(image_url)

            # 转换为base64
            b64_image = self._image_to_base64(original_image)

            # 构建变体请求
            payload = {
                "model": "dall-e-2",  # DALL-E 2支持变体生成
                "image": b64_image,
                "n": min(n, 10),
                "size": "1024x1024",
            }

            # 调用变体API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/images/variations",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                api_response = response.json()
                return self._process_api_response(api_response)

        except Exception as e:
            logger.error(f"生成图像变体失败: {str(e)}")
            raise

    async def _download_image(self, url: str) -> bytes:
        """下载图像"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def _image_to_base64(self, image_data: bytes) -> str:
        """将图像数据转换为base64"""
        return base64.b64encode(image_data).decode("utf-8")

    async def batch_generate_images(
        self, requests: List[ImageGenerationRequest]
    ) -> List[ImageGenerationResponse]:
        """
        批量生成图像

        Args:
            requests: 图像生成请求列表

        Returns:
            List[ImageGenerationResponse]: 批量生成响应列表
        """
        logger.info(f"开始批量生成{len(requests)}组图像")

        # 并发执行生成任务
        tasks = [self.generate_images(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(
                    f"第{i + 1}组图像生成失败: {str(response)}"
                )
                results.append(None)
            else:
                results.append(response)

        return results

    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        获取使用统计信息

        Returns:
            Dict[str, Any]: 使用统计
        """
        # 这里应该集成实际的使用统计，比如通过数据库记录
        return {
            "total_generations": 0,
            "total_cost": 0.0,
            "average_processing_time": 0.0,
            "popular_sizes": {},
            "style_preferences": {},
        }


# 创建全局实例（按需实例化，避免启动时验证配置）
