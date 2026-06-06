"""
设备评估 API 路由

提供设备能力评估报告的查询接口，供前端插件商店使用。
注意：实际设备评估在 Electron 主进程执行，后端仅提供数据转发和存储。
"""

import logging
import os
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["设备评估"])

# 设备评估报告文件路径（与 Electron 共享 userData 目录）
# 生产环境：{userData}/device-profile.json
# 开发环境：从环境变量或默认路径读取
DEVICE_PROFILE_PATH = os.environ.get(
    "DEVICE_PROFILE_PATH",
    str(Path.home() / "AppData" / "Roaming" /
        "imato-desktop" / "device-profile.json")
    if os.name == "nt"
    else str(Path.home() / ".config" / "imato-desktop" / "device-profile.json"),
)


def _load_device_profile() -> Optional[dict]:
    """加载设备评估报告"""
    try:
        if os.path.exists(DEVICE_PROFILE_PATH):
            with open(DEVICE_PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载设备评估报告失败: {e}")
    return None


@router.get("/api/v1/device/profile")
async def get_device_profile():
    """
    获取设备评估报告

    返回 Electron 主进程生成的设备评估结果，包括：
    - 硬件指标（CPU/内存/GPU/存储/外设/网络）
    - 软件环境（Python/Docker/Redis/CLI工具）
    - 设备评级（Basic/Standard/Advanced/Professional）
    - 插件兼容性分析

    响应示例:
    {
      "success": true,
      "profile": {
        "version": "1.0",
        "assessedAt": "2026-06-06T10:00:00Z",
        "hardware": { ... },
        "software": { ... },
        "assessment": {
          "deviceClass": "advanced",
          "score": 82,
          "compatiblePluginTiers": ["tier-a", "tier-b", "tier-c"],
          "recommendedPlugins": ["ai-tutor", "ar-vr-lab"],
          "incompatiblePlugins": ["federated-learning"],
          "warnings": []
        }
      }
    }
    """
    profile = _load_device_profile()

    if not profile:
        return {
            "success": False,
            "error": "设备评估报告不存在，请先在桌面客户端启动应用以自动评估",
        }

    return {"success": True, "profile": profile}


@router.post("/api/v1/device/reassess")
async def trigger_reassess():
    """
    触发重新评估设备

    注意：此端点仅通知 Electron 主进程重新评估，
    实际评估由 Electron 通过 IPC 执行。
    前端应直接调用 window.pluginAPI.reassessDevice()。

    返回:
    {
      "success": true,
      "message": "已触发重新评估，请通过 IPC 监听结果"
    }
    """
    return {
        "success": True,
        "message": "重新评估应由 Electron 主进程执行，请调用 window.pluginAPI.reassessDevice()",
    }


@router.get("/api/v1/device/compatibility/{plugin_id}")
async def check_plugin_compatibility(plugin_id: str):
    """
    检查指定插件与当前设备的兼容性

    基于设备评估报告中的 compatiblePluginTiers 和 incompatiblePlugins 判断。

    路径参数:
    - plugin_id: 插件 ID（如 "ar-vr-lab"）

    响应示例:
    {
      "success": true,
      "compatible": true,
      "deviceClass": "advanced",
      "reason": "设备满足 Advanced 级要求",
      "warnings": []
    }
    """
    profile = _load_device_profile()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="设备评估报告不存在，无法检查兼容性",
        )

    assessment = profile.get("assessment", {})
    device_class = assessment.get("deviceClass", "basic")
    compatible_tiers = assessment.get("compatiblePluginTiers", [])
    incompatible_plugins = assessment.get("incompatiblePlugins", [])
    recommended_plugins = assessment.get("recommendedPlugins", [])

    # 检查插件是否在不兼容列表中
    if plugin_id in incompatible_plugins:
        return {
            "success": True,
            "compatible": False,
            "deviceClass": device_class,
            "reason": f"插件 {plugin_id} 与当前设备不兼容",
            "warnings": assessment.get("warnings", []),
        }

    # 检查插件是否在推荐列表中（可选增强）
    is_recommended = plugin_id in recommended_plugins

    return {
        "success": True,
        "compatible": True,
        "deviceClass": device_class,
        "isRecommended": is_recommended,
        "compatibleTiers": compatible_tiers,
        "reason": f"设备等级 {device_class} 兼容该插件",
        "warnings": assessment.get("warnings", []),
    }
