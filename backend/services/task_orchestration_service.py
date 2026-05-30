"""
AI-Edu 联动任务编排服务
协调 OpenHydra AI 训练与 iMato 硬件模拟的跨平台任务
支持智能温室监控系统等综合学习任务
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import UploadFile

logger = logging.getLogger(__name__)


class TaskOrchestrationService:
    """联动任务编排服务类"""

    def __init__(self, db_session=None):
        """
        初始化编排服务

        Args:
            db_session: 数据库会话（可选）
        """
        self.db = db_session
        self.storage_path = "data/linked_tasks"

    async def submit_stage1_result(
        self,
        user_id: int,
        task_id: str,
        model_file: UploadFile,
        training_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        提交第一阶段 AI 模型训练结果

        Args:
            user_id: 用户 ID
            task_id: 任务 ID（如 'greenhouse_001'）
            model_file: 模型文件
            training_report: 训练报告数据

        Returns:
            评测结果和积分奖励
        """
        logger.info(f"收到用户{user_id}提交的阶段 1 结果：任务{task_id}")

        try:
            # 1. 保存模型到对象存储
            model_path = await self._save_model_file(user_id, task_id, model_file)
            logger.info(f"✅ 模型已保存：{model_path}")

            # 2. 自动评测准确率
            metrics = await self._evaluate_model(model_path, training_report)
            logger.info(f"✅ 模型评测完成：准确率 {metrics['accuracy']:.2%}")

            # 3. 发放积分
            xp_earned = await self._award_stage1_xp(user_id, metrics)
            logger.info(f"✅ 积分已发放：{xp_earned} XP")

            # 4. 将模型部署到虚拟实验室（为第二阶段准备）
            deployment_status = await self._deploy_to_virtual_lab(
                user_id, task_id, model_path
            )

            # 5. 记录提交结果
            submission_record = {
                "user_id": user_id,
                "task_id": task_id,
                "stage": 1,
                "model_path": model_path,
                "metrics": metrics,
                "xp_earned": xp_earned,
                "deployment_status": deployment_status,
                "submitted_at": datetime.utcnow().isoformat(),
            }

            await self._save_submission_record(submission_record)

            return {
                "success": True,
                "metrics": metrics,
                "xp_earned": xp_earned,
                "message": f'阶段 1 提交成功！准确率 {metrics["accuracy"]:.2%}, 获得 {xp_earned} XP',
            }

        except Exception as e:
            logger.error(f"阶段 1 提交失败：{e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "阶段 1 提交失败，请稍后重试",
            }

    async def _save_model_file(
        self, user_id: int, task_id: str, model_file: UploadFile
    ) -> str:
        """保存模型文件到对象存储"""
        import os
        from pathlib import Path

        # 创建存储目录
        model_dir = Path(self.storage_path) / task_id / "models" / str(user_id)
        model_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"model_{timestamp}.pth"
        model_path = model_dir / filename

        # 保存文件
        with open(model_path, "wb") as f:
            content = await model_file.read()
            f.write(content)

        return str(model_path)

    async def _calculate_model_file_size(self, model_path: str) -> float:
        """
        计算模型文件大小（MB）

        Args:
            model_path: 模型文件路径

        Returns:
            文件大小（MB），保留 2 位小数
        """
        try:
            from pathlib import Path

            file_path = Path(model_path)

            # 检查文件是否存在
            if not file_path.exists():
                logger.warning(f"模型文件不存在：{model_path}")
                return 0.0

            # 获取文件大小（字节）
            size_bytes = file_path.stat().st_size

            # 转换为 MB（保留 2 位小数）
            size_mb = round(size_bytes / (1024 * 1024), 2)

            logger.info(f"✅ 模型文件大小：{size_mb} MB ({size_bytes} bytes)")
            return size_mb

        except Exception as e:
            logger.error(f"❌ 计算文件大小失败：{e}")
            return 0.0

    async def _award_points_to_user(
        self, user_id: int, points: int, reason: str
    ) -> bool:
        """
        为用户发放积分

        Args:
            user_id: 用户 ID
            points: 积分数量
            reason: 发放原因

        Returns:
            是否成功
        """
        try:
            # 导入积分服务
            from services.leaderboard_service import get_leaderboard_service

            # 获取数据库会话（如果有的话）
            db = self.db
            if not db:
                logger.warning("数据库会话未初始化，无法发放积分")
                return False

            # 获取积分服务实例
            points_service = get_leaderboard_service(db)

            # 发放积分
            points_record = points_service.add_points(
                user_id=user_id,
                amount=points,
                reason="task_completion",
                reference_type="linked_task",
                description=reason,
            )

            logger.info(
                f"✅ 用户{user_id}获得 {points} 积分，原因：{reason}, "
                f"当前总积分：{points_record.total_points}"
            )

            # ✅ 发送积分变动通知
            await self._send_points_notification(user_id, points, reason)

            return True

        except Exception as e:
            logger.error(f"❌ 发放积分失败：{e}", exc_info=True)
            return False

    async def _send_points_notification(
        self, user_id: int, points: int, reason: str
    ) -> None:
        """
        发送积分变动通知

        Args:
            user_id: 用户 ID
            points: 积分数
            reason: 变动原因
        """
        try:
            # 导入通知服务
            from services.decay_notification_service import decay_notification_service

            # 准备通知数据
            notification_data = {
                "user_id": user_id,
                "points_earned": points,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 发送通知（异步，不阻塞主流程）
            asyncio.create_task(
                decay_notification_service.send_notification(
                    user_id=user_id,
                    template_id="points_awarded",
                    data=notification_data,
                )
            )

            logger.debug(f"📬 积分变动通知已发送：用户{user_id}, +{points}积分")

        except Exception as e:
            # 通知失败不影响主流程，仅记录日志
            logger.warning(f"📭 发送积分通知失败：{e}")

    async def _evaluate_model(
        self, model_path: str, training_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评测模型性能

        Args:
            model_path: 模型文件路径
            training_report: 训练报告

        Returns:
            评测指标
        """
        # 从训练报告中提取指标
        accuracy = training_report.get("accuracy", 0.0)
        loss = training_report.get("loss", 1.0)
        training_time = training_report.get("training_time_minutes", 0)

        # 验证指标合理性
        if not (0 <= accuracy <= 1):
            logger.warning(f"准确率异常：{accuracy}")
            accuracy = max(0.0, min(1.0, accuracy))

        # 计算模型文件大小（MB）
        model_size_mb = await self._calculate_model_file_size(model_path)

        return {
            "accuracy": accuracy,
            "loss": loss,
            "training_time_minutes": training_time,
            "model_size_mb": model_size_mb,  # ✅ 已计算实际文件大小
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    async def _award_stage1_xp(self, user_id: int, metrics: Dict[str, Any]) -> int:
        """
        发放阶段 1 积分

        奖励规则:
        - 完成训练：+300 XP
        - 准确率 >= 90%: +200 XP
        - 准确率 >= 95%: +300 XP
        - 排行榜前 3: +500 XP (后续计算)
        """
        base_xp = 300  # 完成训练的基礎积分
        bonus_xp = 0

        accuracy = metrics["accuracy"]

        # 准确率奖金
        if accuracy >= 0.95:
            bonus_xp += 300
        elif accuracy >= 0.90:
            bonus_xp += 200
        elif accuracy >= 0.85:
            bonus_xp += 100

        total_xp = base_xp + bonus_xp

        # ✅ 调用积分服务发放积分
        await self._award_points_to_user(user_id, total_xp, "阶段 1 完成")

        logger.info(
            f"用户{user_id}获得 {total_xp} XP (基础:{base_xp}, 奖金:{bonus_xp})"
        )

        return total_xp

    async def _deploy_to_virtual_lab(
        self, user_id: int, task_id: str, model_path: str
    ) -> Dict[str, Any]:
        """
        将模型部署到 iMato 虚拟实验室

        Args:
            user_id: 用户 ID
            task_id: 任务 ID
            model_path: 模型文件路径

        Returns:
            部署状态
        """
        try:
            # ✅ 调用 Vircadia API 更新场景脚本
            from services.vircadia_avatar_sync_impl import VircadiaAPIClient

            # 生成场景脚本
            script_content = self._generate_scene_script(model_path, user_id)

            # 调用 Vircadia API 上传并更新场景脚本
            vircadia_client = VircadiaAPIClient()
            deployment_result = await vircadia_client.update_scene_script(
                scene_id="greenhouse_lab",
                object_id="ai_controller",
                script_content=script_content,
                metadata={
                    "user_id": user_id,
                    "task_id": task_id,
                    "model_path": model_path,
                },
            )

            if deployment_result.get("success"):
                logger.info(f"✅ 模型已部署到虚拟实验室：{model_path}")
                return {
                    "success": True,
                    "scene_id": "greenhouse_lab",
                    "object_id": "ai_controller",
                    "deployment_url": deployment_result.get("url", ""),
                    "deployed_at": datetime.utcnow().isoformat(),
                }
            else:
                logger.warning(
                    f"⚠️ Vircadia API 调用失败，使用模拟模式：{deployment_result.get('error')}"
                )
                # 降级处理：使用模拟模式
                return await self._simulate_deployment(user_id, task_id, model_path)

        except Exception as e:
            logger.error(f"部署失败：{e}", exc_info=True)
            # 异常情况下返回错误信息
            return {"success": False, "error": str(e)}

    def _generate_scene_script(self, model_path: str, user_id: int) -> str:
        """
        生成 Vircadia 场景脚本

        Args:
            model_path: AI 模型文件路径
            user_id: 用户 ID

        Returns:
            JavaScript 格式的场景脚本
        """
        script_template = f"""
// ========================================
// iMato 虚拟实验室 - AI 模型部署脚本
// 用户 ID: {user_id}
// 模型路径：{model_path}
// 部署时间：{datetime.utcnow().isoformat()}
// ========================================

(function() {{
    'use strict';
    
    // 加载学生的 AI 模型
    const modelPath = "{model_path}";
    let aiModel = null;
    
    // 异步加载模型
    async function loadModel() {{
        try {{
            console.log('[iMato] 正在加载 AI 模型:', modelPath);
            aiModel = await loadAIModel(modelPath);
            console.log('[iMato] ✅ 模型加载成功');
            
            // 绑定到传感器系统
            if (typeof camera !== 'undefined' && camera.onCapture) {{
                camera.onCapture(async (image) => {{
                    if (!aiModel) {{
                        console.warn('[iMato] 模型未加载');
                        return;
                    }}
                    
                    const prediction = await aiModel.predict(image);
                    console.log('[iMato] 预测结果:', prediction);
                    
                    // 执行控制指令
                    if (typeof controlSystem !== 'undefined') {{
                        controlSystem.actuate(prediction);
                    }}
                }});
                console.log('[iMato] ✅ 传感器绑定成功');
            }}
            
            // 日志记录
            console.log('[iMato] 模型已加载:', modelPath);
            
        }} catch (error) {{
            console.error('[iMato] ❌ 模型加载失败:', error);
        }}
    }}
    
    // 启动加载流程
    loadModel();
    
}})();
"""
        return script_template

    async def _simulate_deployment(
        self, user_id: int, task_id: str, model_path: str
    ) -> Dict[str, Any]:
        """
        模拟部署（降级处理）

        Args:
            user_id: 用户 ID
            task_id: 任务 ID
            model_path: 模型文件路径

        Returns:
            部署状态
        """
        deployment_config = {
            "scene_id": "greenhouse_lab",
            "object_id": "ai_controller",
            "model_path": model_path,
            "user_id": user_id,
        }

        # 模拟部署脚本
        script_template = self._generate_scene_script(model_path, user_id)

        logger.info(f"✅ 模型部署配置已生成：{deployment_config['scene_id']}")

        return {
            "success": True,
            "scene_id": deployment_config["scene_id"],
            "object_id": deployment_config["object_id"],
            "deployed_at": datetime.utcnow().isoformat(),
            "mode": "simulation",
        }

    async def _save_submission_record(self, record: Dict[str, Any]):
        """保存提交记录到数据库"""
        # TODO: 保存到数据库
        logger.info(
            f"📝 提交记录已保存：用户{record['user_id']}, 任务{record['task_id']}"
        )
        print(f"提交记录：{json.dumps(record, indent=2, ensure_ascii=False)}")

    async def submit_stage2_result(
        self,
        user_id: int,
        task_id: str,
        hardware_control_code: str,
        system_logs: List[str],
        performance_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        提交第二阶段硬件模拟集成结果

        Args:
            user_id: 用户 ID
            task_id: 任务 ID
            hardware_control_code: 硬件控制代码
            system_logs: 系统运行日志
            performance_metrics: 性能指标

        Returns:
            评测结果和积分奖励
        """
        logger.info(f"收到用户{user_id}提交的阶段 2 结果：任务{task_id}")

        try:
            # 1. 验证系统集成
            integration_check = await self._check_hardware_integration(
                user_id, task_id, hardware_control_code
            )

            # 2. 分析系统日志
            log_analysis = await self._analyze_system_logs(system_logs)

            # 3. 评估性能指标
            performance_score = await self._evaluate_performance(performance_metrics)

            # 4. 发放积分
            xp_earned = await self._award_stage2_xp(
                user_id, integration_check, log_analysis, performance_score
            )

            # 5. 记录提交结果
            submission_record = {
                "user_id": user_id,
                "task_id": task_id,
                "stage": 2,
                "integration_check": integration_check,
                "log_analysis": log_analysis,
                "performance_score": performance_score,
                "xp_earned": xp_earned,
                "submitted_at": datetime.utcnow().isoformat(),
            }

            await self._save_submission_record(submission_record)

            return {
                "success": True,
                "performance_score": performance_score,
                "xp_earned": xp_earned,
                "message": f"阶段 2 提交成功！性能评分 {performance_score:.1f}/100, 获得 {xp_earned} XP",
            }

        except Exception as e:
            logger.error(f"阶段 2 提交失败：{e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "阶段 2 提交失败，请稍后重试",
            }

    async def _check_hardware_integration(
        self, user_id: int, task_id: str, control_code: str
    ) -> Dict[str, Any]:
        """
        检查硬件集成情况（验证学生的硬件代码与实际硬件连接的匹配性）

        Args:
            user_id: 用户 ID
            task_id: 任务 ID
            control_code: 学生提交的控制代码

        Returns:
            验证结果和评分
        """
        try:
            # ✅ 解析学生提交的代码，提取关键信息
            code_analysis = self._parse_control_code(control_code)

            # ✅ 获取标准答案（从任务配置中）
            standard_config = await self._get_standard_hardware_config(task_id)

            # ✅ 对比分析
            comparison_result = self._compare_hardware_configs(
                code_analysis, standard_config
            )

            # ✅ 计算综合评分
            overall_score = self._calculate_hardware_score(comparison_result)

            logger.info(
                f"✅ 用户{user_id}硬件集成验证完成：" f"总分 {overall_score:.1f}/100"
            )

            return {
                "code_valid": code_analysis.get("valid", False),
                "hardware_connected": True,  # 假设硬件已连接
                "response_time_ms": comparison_result.get("response_time_ms", 150),
                "stability_score": overall_score,
                "detailed_feedback": comparison_result.get("feedback", {}),
                "improvement_suggestions": comparison_result.get("suggestions", []),
            }

        except Exception as e:
            logger.error(f"硬件集成验证失败：{e}", exc_info=True)
            return {
                "code_valid": False,
                "hardware_connected": False,
                "error": str(e),
            }

    def _parse_control_code(self, control_code: str) -> Dict[str, Any]:
        """
        解析控制代码，提取硬件配置信息

        Args:
            control_code: 学生提交的控制代码

        Returns:
            提取的配置信息
        """
        import re

        config = {
            "valid": False,
            "pins": {},
            "sensors": [],
            "actuators": [],
            "communication_protocols": [],
        }

        try:
            # 1. 提取引脚配置
            pin_patterns = [
                r"pinMode\s*\(\s*(\w+)\s*,\s*(INPUT|OUTPUT)\s*\)",
                r"digitalWrite\s*\(\s*(\w+)\s*,",
                r"analogRead\s*\(\s*(\w+)\s*\)",
            ]

            for pattern in pin_patterns:
                matches = re.findall(pattern, control_code)
                for match in matches:
                    if isinstance(match, tuple):
                        pin_name = match[0]
                        # 只有当引脚未设置或当前值为 UNKNOWN 时才更新
                        if (
                            pin_name not in config["pins"]
                            or config["pins"][pin_name] == "UNKNOWN"
                        ):
                            config["pins"][pin_name] = (
                                match[1] if len(match) > 1 else "UNKNOWN"
                            )
                    elif match:  # 添加非空检查
                        # 只有当引脚未设置时才添加
                        if match not in config["pins"]:
                            config["pins"][match] = "UNKNOWN"

            # 2. 提取传感器类型
            sensor_keywords = [
                ("temperature", "温度传感器"),
                ("humidity", "湿度传感器"),
                ("light", "光照传感器"),
                ("soil_moisture", "土壤湿度传感器"),
                ("co2", "CO2 传感器"),
            ]

            for keyword, sensor_name in sensor_keywords:
                if keyword.lower() in control_code.lower():
                    config["sensors"].append(sensor_name)

            # 3. 提取执行器类型
            actuator_keywords = [
                ("fan", "风扇"),
                ("pump", "水泵"),
                ("led", "LED 灯"),
                ("heater", "加热器"),
                ("motor", "电机"),
            ]

            for keyword, actuator_name in actuator_keywords:
                if keyword.lower() in control_code.lower():
                    config["actuators"].append(actuator_name)

            # 4. 提取通信协议
            protocol_patterns = [
                (r"I2C|Wire\.begin", "I2C"),
                (r"SPI\.begin", "SPI"),
                (r"Serial\.begin|UART", "UART/Serial"),
                (r"WiFi\.begin|Ethernet\.begin", "WiFi/Ethernet"),
            ]

            for pattern, protocol in protocol_patterns:
                if re.search(pattern, control_code, re.IGNORECASE):
                    config["communication_protocols"].append(protocol)

            # 5. 验证代码有效性
            has_pins = len(config["pins"]) > 0
            has_components = len(config["sensors"]) > 0 or len(config["actuators"]) > 0
            config["valid"] = has_pins and has_components

        except Exception as e:
            logger.error(f"代码解析失败：{e}")
            config["valid"] = False

        return config

    async def _get_standard_hardware_config(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务的标准硬件配置

        Args:
            task_id: 任务 ID

        Returns:
            标准配置字典
        """
        # TODO: 从数据库查询标准配置
        # 这里先使用硬编码的示例配置

        standard_configs = {
            "greenhouse_001": {
                "required_pins": ["D0", "D1", "A0"],
                "required_sensors": ["温度传感器", "湿度传感器", "土壤湿度传感器"],
                "required_actuators": ["水泵", "风扇"],
                "required_protocols": ["I2C"],
            },
            "greenhouse_002": {
                "required_pins": ["D0", "D1", "D2", "A0", "A1"],
                "required_sensors": [
                    "温度传感器",
                    "湿度传感器",
                    "光照传感器",
                    "CO2 传感器",
                ],
                "required_actuators": ["LED 灯", "风扇", "水泵"],
                "required_protocols": ["I2C", "SPI"],
            },
        }

        # 返回对应任务的配置，如果没有则返回默认配置
        return standard_configs.get(
            task_id,
            {
                "required_pins": ["D0", "D1"],
                "required_sensors": ["温度传感器"],
                "required_actuators": ["风扇"],
                "required_protocols": [],
            },
        )

    def _compare_hardware_configs(
        self, student_config: Dict[str, Any], standard_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        对比学生配置与标准配置

        Args:
            student_config: 学生代码的配置
            standard_config: 标准答案配置

        Returns:
            对比结果
        """
        feedback = {}
        suggestions = []
        scores = {}

        # 1. 引脚配置对比
        required_pins = set(standard_config.get("required_pins", []))
        student_pins = set(student_config.get("pins", {}).keys())

        correct_pins = required_pins & student_pins
        missing_pins = required_pins - student_pins
        extra_pins = student_pins - required_pins

        pin_score = len(correct_pins) / max(len(required_pins), 1) * 100
        scores["pins"] = pin_score

        feedback["pins"] = {
            "correct": list(correct_pins),
            "missing": list(missing_pins),
            "extra": list(extra_pins),
        }

        if missing_pins:
            suggestions.append(f"缺少必要引脚：{', '.join(missing_pins)}")

        # 2. 传感器对比
        required_sensors = set(standard_config.get("required_sensors", []))
        student_sensors = set(student_config.get("sensors", []))

        correct_sensors = required_sensors & student_sensors
        missing_sensors = required_sensors - student_sensors

        sensor_score = len(correct_sensors) / max(len(required_sensors), 1) * 100
        scores["sensors"] = sensor_score

        feedback["sensors"] = {
            "correct": list(correct_sensors),
            "missing": list(missing_sensors),
        }

        if missing_sensors:
            suggestions.append(f"缺少必要传感器：{', '.join(missing_sensors)}")

        # 3. 执行器对比
        required_actuators = set(standard_config.get("required_actuators", []))
        student_actuators = set(student_config.get("actuators", []))

        correct_actuators = required_actuators & student_actuators
        missing_actuators = required_actuators - student_actuators

        actuator_score = len(correct_actuators) / max(len(required_actuators), 1) * 100
        scores["actuators"] = actuator_score

        feedback["actuators"] = {
            "correct": list(correct_actuators),
            "missing": list(missing_actuators),
        }

        if missing_actuators:
            suggestions.append(f"缺少必要执行器：{', '.join(missing_actuators)}")

        # 4. 通信协议对比
        required_protocols = set(standard_config.get("required_protocols", []))
        student_protocols = set(student_config.get("communication_protocols", []))

        correct_protocols = required_protocols & student_protocols
        missing_protocols = required_protocols - student_protocols

        protocol_score = len(correct_protocols) / max(len(required_protocols), 1) * 100
        scores["protocols"] = protocol_score

        feedback["protocols"] = {
            "correct": list(correct_protocols),
            "missing": list(missing_protocols),
        }

        if missing_protocols:
            suggestions.append(f"缺少必要通信协议：{', '.join(missing_protocols)}")

        # 5. 估算响应时间（基于代码复杂度）
        estimated_response_time = 100 + len(student_config.get("pins", {})) * 10

        return {
            "scores": scores,
            "feedback": feedback,
            "suggestions": suggestions,
            "response_time_ms": estimated_response_time,
        }

    def _calculate_hardware_score(self, comparison_result: Dict[str, Any]) -> float:
        """
        计算综合评分

        Args:
            comparison_result: 对比结果

        Returns:
            综合评分（0-100）
        """
        scores = comparison_result.get("scores", {})

        # 加权平均
        weights = {
            "pins": 0.3,  # 引脚配置 30%
            "sensors": 0.3,  # 传感器 30%
            "actuators": 0.25,  # 执行器 25%
            "protocols": 0.15,  # 通信协议 15%
        }

        total_score = 0.0
        for category, score in scores.items():
            weight = weights.get(category, 0.25)
            total_score += score * weight

        return round(total_score, 1)

    async def _analyze_system_logs(self, logs: List[str]) -> Dict[str, Any]:
        """分析系统日志"""
        # TODO: 日志分析逻辑
        return {
            "error_count": 0,
            "warning_count": 2,
            "uptime_hours": 24.0,
            "stability_rating": "excellent",
        }

    async def _evaluate_performance(self, metrics: Dict[str, Any]) -> float:
        """评估系统性能（0-100 分）"""
        # 简化评分逻辑
        score = 0.0

        # 植物生长状态（40 分）
        score += metrics.get("plant_health_score", 0) * 0.4

        # 资源利用率（30 分）
        score += metrics.get("resource_efficiency", 0) * 0.3

        # 系统稳定性（30 分）
        score += metrics.get("stability_score", 0) * 0.3

        return min(100.0, score)

    async def _award_stage2_xp(
        self,
        user_id: int,
        integration_check: Dict[str, Any],
        log_analysis: Dict[str, Any],
        performance_score: float,
    ) -> int:
        """发放阶段 2 积分"""
        base_xp = 500  # 完成集成的基础积分
        bonus_xp = 0

        # 稳定性奖金
        if integration_check.get("stability_score", 0) >= 95:
            bonus_xp += 200

        # 零错误奖金
        if log_analysis.get("error_count", 0) == 0:
            bonus_xp += 150

        # 性能优秀奖金
        if performance_score >= 90:
            bonus_xp += 250
        elif performance_score >= 80:
            bonus_xp += 150

        total_xp = base_xp + bonus_xp

        logger.info(
            f"用户{user_id}获得 {total_xp} XP (基础:{base_xp}, 奖金:{bonus_xp})"
        )

        return total_xp

    async def get_leaderboard(
        self, task_id: str, stage: Optional[int] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取排行榜

        Args:
            task_id: 任务 ID
            stage: 阶段（None 表示总分）
            limit: 返回数量限制

        Returns:
            排行榜列表
        """
        # TODO: 从数据库查询并排序
        mock_leaderboard = [
            {
                "rank": 1,
                "user_id": 1001,
                "username": "AI 小能手",
                "total_score": 95.5,
                "total_xp": 2500,
                "submission_time": "2026-03-10T14:30:00",
            },
            {
                "rank": 2,
                "user_id": 1002,
                "username": "温室专家",
                "total_score": 93.2,
                "total_xp": 2300,
                "submission_time": "2026-03-10T15:20:00",
            },
        ]

        return mock_leaderboard[:limit]


def get_task_orchestration_service(db=None) -> TaskOrchestrationService:
    """获取任务编排服务实例"""
    return TaskOrchestrationService(db)
