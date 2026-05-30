"""
AR模型与物理引擎交互服务
支持AR场景中的物理仿真和交互逻辑
"""

from datetime import datetime
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from models.ar_vr_content import (
    ARVRContent,
    ARVRInteractionLog,
    ARVRProgressTracking,
    InteractionMode,
)
from services.ar_vr_content_service import ARVRContentService

logger = logging.getLogger(__name__)


class PhysicsEngine:
    """物理引擎基类"""

    def __init__(self):
        self.gravity = 9.81  # m/s²
        self.time_step = 1 / 60.0  # 60 FPS
        self.objects = {}  # 物理对象字典

    def add_object(
        self,
        obj_id: str,
        mass: float,
        position: Tuple[float, float, float],
        velocity: Tuple[float, float, float] = (0, 0, 0),
    ):
        """添加物理对象"""
        self.objects[obj_id] = {
            "mass": mass,
            "position": np.array(position, dtype=float),
            "velocity": np.array(velocity, dtype=float),
            "forces": np.zeros(3),
            "is_static": mass == 0,
        }

    def apply_force(self, obj_id: str, force: Tuple[float, float, float]):
        """对物体施加力"""
        if obj_id in self.objects and not self.objects[obj_id]["is_static"]:
            self.objects[obj_id]["forces"] += np.array(force, dtype=float)

    def update(self):
        """更新物理仿真"""
        for obj_id, obj in self.objects.items():
            if not obj["is_static"]:
                # 计算加速度 F = ma => a = F/m
                acceleration = obj["forces"] / obj["mass"]

                # 应用重力
                acceleration[1] -= self.gravity

                # 更新速度 v = v0 + at
                obj["velocity"] += acceleration * self.time_step

                # 更新位置 x = x0 + vt
                obj["position"] += obj["velocity"] * self.time_step

                # 重置力
                obj["forces"] = np.zeros(3)

    def get_position(self, obj_id: str) -> Tuple[float, float, float]:
        """获取物体位置"""
        if obj_id in self.objects:
            pos = self.objects[obj_id]["position"]
            return tuple(pos.tolist())
        return (0, 0, 0)

    def set_position(self, obj_id: str, position: Tuple[float, float, float]):
        """设置物体位置"""
        if obj_id in self.objects:
            self.objects[obj_id]["position"] = np.array(position, dtype=float)


class ARPhysicsService:
    """AR物理交互服务"""

    def __init__(self, db: Session):
        self.db = db
        self.content_service = ARVRContentService(db)
        self.physics_engines = {}  # 每个内容一个物理引擎
        self.interaction_handlers = {}  # 交互处理器

    def initialize_physics_for_content(self, content_id: int) -> PhysicsEngine:
        """
        为AR内容初始化物理引擎

        Args:
            content_id: 内容ID

        Returns:
            PhysicsEngine: 物理引擎实例
        """
        if content_id not in self.physics_engines:
            engine = PhysicsEngine()
            self.physics_engines[content_id] = engine

            # 根据内容类型初始化默认物理对象
            content = self.content_service.get_arvr_content(
                content_id, 1
            )  # 假设org_id=1

            if content.content_type.value == "virtual_lab":
                self._initialize_lab_physics(engine, content)
            elif content.content_type.value == "model_viewer":
                self._initialize_model_physics(engine, content)

        return self.physics_engines[content_id]

    def _initialize_lab_physics(self, engine: PhysicsEngine, content: ARVRContent):
        """初始化虚拟实验室物理环境"""
        # 添加地面平面
        engine.add_object("ground", 0, (0, 0, 0))  # 静态地面

        # 根据实验配置添加物体
        config = content.config or {}
        experiments = config.get("experiments", [])

        for i, exp_name in enumerate(experiments):
            if exp_name == "pendulum":
                # 添加摆锤系统
                engine.add_object(f"pivot_{i}", 0, (0, 5, 0))  # 固定点
                engine.add_object(f"bob_{i}", 1.0, (0, 3, 0))  # 摆锤
            elif exp_name == "spring_mass":
                # 添加弹簧质量系统
                engine.add_object(f"support_{i}", 0, (0, 8, 0))  # 支撑点
                engine.add_object(f"mass_{i}", 2.0, (0, 6, 0))  # 质量块

    def _initialize_model_physics(self, engine: PhysicsEngine, content: ARVRContent):
        """初始化模型查看器物理环境"""
        # 添加基础物理对象用于交互
        engine.add_object("interaction_plane", 0, (0, 0, 0))  # 交互平面
        engine.add_object("manipulator", 0.1, (0, 0, 0))  # 操作器

    def handle_gesture_interaction(
        self, content_id: int, user_id: int, gesture_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理手势交互

        Args:
            content_id: 内容ID
            user_id: 用户ID
            gesture_data: 手势数据

        Returns:
            Dict: 交互结果
        """
        try:
            engine = self.initialize_physics_for_content(content_id)
            gesture_type = gesture_data.get("type")
            position = gesture_data.get("position", [0, 0, 0])
            gesture_data.get("timestamp", datetime.utcnow().isoformat())

            result = {"success": False, "response": None, "physics_updates": []}

            if gesture_type == "tap":
                result = self._handle_tap_gesture(engine, content_id, position)
            elif gesture_type == "swipe":
                result = self._handle_swipe_gesture(engine, content_id, gesture_data)
            elif gesture_type == "pinch":
                result = self._handle_pinch_gesture(engine, content_id, gesture_data)
            elif gesture_type == "rotate":
                result = self._handle_rotate_gesture(engine, content_id, gesture_data)

            # 记录交互日志
            self._log_interaction(
                content_id, user_id, "gesture", gesture_data, result["success"]
            )

            # 更新物理引擎
            engine.update()

            return result

        except Exception as e:
            logger.error(f"处理手势交互失败: {e}")
            return {"success": False, "error": str(e)}

    def _handle_tap_gesture(
        self, engine: PhysicsEngine, content_id: int, position: List[float]
    ) -> Dict[str, Any]:
        """处理点击手势"""
        # 检测点击的对象
        hit_object = self._raycast_objects(position, [0, -1, 0])  # 向下射线检测

        if hit_object:
            # 对击中的对象施加向上的力
            force_magnitude = 50.0
            engine.apply_force(hit_object, (0, force_magnitude, 0))

            return {
                "success": True,
                "response": f"对象 {hit_object} 被点击",
                "physics_updates": [
                    {"object": hit_object, "force_applied": [0, force_magnitude, 0]}
                ],
            }

        return {"success": False, "response": "未检测到可交互对象"}

    def _handle_swipe_gesture(
        self, engine: PhysicsEngine, content_id: int, gesture_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理滑动手势"""
        direction = gesture_data.get("direction", [0, 0, 0])
        distance = gesture_data.get("distance", 0)

        # 将滑动转换为力
        force_multiplier = 20.0
        force = [d * force_multiplier * distance for d in direction]

        # 对所有动态对象施加力
        affected_objects = []
        for obj_id in engine.objects:
            if not engine.objects[obj_id]["is_static"]:
                engine.apply_force(obj_id, force)
                affected_objects.append(obj_id)

        return {
            "success": True,
            "response": f"滑动施加力到 {len(affected_objects)} 个对象",
            "physics_updates": [
                {"object": obj_id, "force_applied": force}
                for obj_id in affected_objects
            ],
        }

    def _handle_pinch_gesture(
        self, engine: PhysicsEngine, content_id: int, gesture_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理捏合手势（缩放）"""
        scale_factor = gesture_data.get("scale_factor", 1.0)
        center_position = gesture_data.get("center", [0, 0, 0])

        # 影响附近的对象
        affected_objects = self._find_nearby_objects(center_position, radius=3.0)

        responses = []
        for obj_id in affected_objects:
            current_pos = engine.get_position(obj_id)
            # 根据缩放因子调整位置
            new_pos = [
                center_position[i]
                + (current_pos[i] - center_position[i]) * scale_factor
                for i in range(3)
            ]
            engine.set_position(obj_id, tuple(new_pos))
            responses.append(f"{obj_id} 位置调整")

        return {
            "success": True,
            "response": f"缩放影响 {len(affected_objects)} 个对象",
            "physics_updates": [
                {"object": obj_id, "new_position": engine.get_position(obj_id)}
                for obj_id in affected_objects
            ],
        }

    def _handle_rotate_gesture(
        self, engine: PhysicsEngine, content_id: int, gesture_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理旋转手势"""
        rotation_angle = gesture_data.get("angle", 0)
        rotation_axis = gesture_data.get("axis", [0, 1, 0])
        center_position = gesture_data.get("center", [0, 0, 0])

        # 查找需要旋转的对象
        affected_objects = self._find_nearby_objects(center_position, radius=2.0)

        responses = []
        for obj_id in affected_objects:
            # 这里简化处理，实际应该使用四元数进行3D旋转
            current_pos = engine.get_position(obj_id)
            offset = [current_pos[i] - center_position[i] for i in range(3)]

            # 简单的2D旋转（绕Y轴）
            if rotation_axis == [0, 1, 0]:
                cos_a = math.cos(rotation_angle)
                sin_a = math.sin(rotation_angle)
                new_x = offset[0] * cos_a - offset[2] * sin_a
                new_z = offset[0] * sin_a + offset[2] * cos_a
                new_pos = [
                    center_position[0] + new_x,
                    current_pos[1],
                    center_position[2] + new_z,
                ]
                engine.set_position(obj_id, tuple(new_pos))
                responses.append(f"{obj_id} 旋转调整")

        return {
            "success": True,
            "response": f"旋转影响 {len(affected_objects)} 个对象",
            "physics_updates": [
                {"object": obj_id, "new_position": engine.get_position(obj_id)}
                for obj_id in affected_objects
            ],
        }

    def _raycast_objects(
        self, origin: List[float], direction: List[float]
    ) -> Optional[str]:
        """射线检测对象"""
        # 简化的射线检测实现
        min_distance = float("inf")
        hit_object = None

        for obj_id, obj in self.physics_engines.get(
            1, PhysicsEngine()
        ).objects.items():  # 假设使用内容ID 1
            if obj["is_static"]:
                continue

            obj_pos = obj["position"]
            # 简单的距离检测
            distance = math.sqrt(sum((obj_pos[i] - origin[i]) ** 2 for i in range(3)))
            if distance < min_distance and distance < 5.0:  # 5米范围内
                min_distance = distance
                hit_object = obj_id

        return hit_object

    def _find_nearby_objects(self, center: List[float], radius: float) -> List[str]:
        """查找附近的对象"""
        nearby_objects = []
        center_np = np.array(center)

        for obj_id, obj in self.physics_engines.get(
            1, PhysicsEngine()
        ).objects.items():  # 假设使用内容ID 1
            if obj["is_static"]:
                continue

            obj_pos = obj["position"]
            distance = np.linalg.norm(obj_pos - center_np)
            if distance <= radius:
                nearby_objects.append(obj_id)

        return nearby_objects

    def handle_voice_command(
        self, content_id: int, user_id: int, voice_command: str
    ) -> Dict[str, Any]:
        """
        处理语音命令

        Args:
            content_id: 内容ID
            user_id: 用户ID
            voice_command: 语音命令文本

        Returns:
            Dict: 命令处理结果
        """
        try:
            # 导入语音纠错检测器
            from .voice_correction_detector import (
                HardwareConnectionChecker,
                VoiceCorrectionDetector,
            )

            # 初始化检测器
            correction_detector = VoiceCorrectionDetector()
            connection_checker = HardwareConnectionChecker()

            # 检测是否为纠错命令
            correction_result = correction_detector.detect_corrections(voice_command)

            # 如果检测到纠错行为
            if correction_result.confidence > 0.6:  # 置信度阈值
                logger.info(
                    f"检测到语音纠错行为: {correction_result.correction_type.value}"
                )

                # 处理纠错结果
                correction_response = self._handle_voice_correction(
                    user_id, correction_result, connection_checker
                )

                # 记录纠错交互日志
                self._log_interaction(
                    content_id,
                    user_id,
                    "voice_correction",
                    {
                        "command": voice_command,
                        "correction_type": correction_result.correction_type.value,
                        "confidence": correction_result.confidence,
                        "accuracy_score": correction_result.accuracy_score,
                    },
                    correction_response["success"],
                )

                return correction_response

            # 传统命令处理
            command_map = {
                "开始实验": self._start_experiment,
                "停止实验": self._stop_experiment,
                "重置": self._reset_physics,
                "增加重力": self._increase_gravity,
                "减少重力": self._decrease_gravity,
                "播放": self._play_simulation,
                "暂停": self._pause_simulation,
            }

            # 匹配命令
            matched_command = None
            for keyword, handler in command_map.items():
                if keyword in voice_command:
                    matched_command = handler
                    break

            if matched_command:
                result = matched_command(content_id)
                success = True
            else:
                result = f"未识别的命令: {voice_command}"
                success = False

            # 记录交互日志
            self._log_interaction(
                content_id, user_id, "voice", {"command": voice_command}, success
            )

            return {"success": success, "response": result}

        except Exception as e:
            logger.error(f"处理语音命令失败: {e}")
            return {"success": False, "error": str(e)}

    def _handle_voice_correction(
        self, user_id: int, correction_result, connection_checker
    ) -> Dict[str, Any]:
        """
        处理语音纠错结果

        Args:
            user_id: 用户ID
            correction_result: 纠错检测结果
            connection_checker: 硬件连接检查器

        Returns:
            Dict: 处理结果
        """
        try:
            from .reward_event_bus import RewardEventType
            from .reward_event_handler import emit_voice_correction_event

            corrections = correction_result.detected_corrections
            total_points = 0
            validation_results = []

            # 验证每个纠错项
            for correction in corrections:
                if hasattr(correction, "pin_name") and hasattr(
                    correction, "to_component"
                ):
                    # 验证引脚连接
                    validation = connection_checker.validate_pin_connection(
                        correction.pin_name, correction.to_component
                    )

                    validation_results.append(
                        {
                            "pin": correction.pin_name,
                            "component": correction.to_component,
                            "valid": validation["valid"],
                            "reason": validation["reason"],
                        }
                    )

                    # 如果连接有效，给予积分奖励
                    if validation["valid"]:
                        points = 50  # 基础奖励50积分
                        # 根据准确度调整积分
                        accuracy_bonus = int(20 * correction_result.accuracy_score)
                        total_points += points + accuracy_bonus

                        # 发出奖励事件
                        asyncio.create_task(
                            emit_voice_correction_event(
                                str(user_id),
                                correction_result.correction_type.value,
                                correction_result.accuracy_score,
                                correction.pin_name,
                            )
                        )

            response_msg = f"检测到 {len(corrections)} 个纠错行为"
            if total_points > 0:
                response_msg += f"，获得 {total_points} 积分奖励！"

            return {
                "success": True,
                "response": response_msg,
                "correction_type": correction_result.correction_type.value,
                "points_awarded": total_points,
                "validation_results": validation_results,
                "accuracy_score": correction_result.accuracy_score,
                "confidence": correction_result.confidence,
            }

        except Exception as e:
            logger.error(f"处理语音纠错失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "correction_type": correction_result.correction_type.value,
            }

    def _start_experiment(self, content_id: int) -> str:
        """开始实验"""
        engine = self.physics_engines.get(content_id)
        if engine:
            # 启动物理仿真循环
            return "实验已开始"
        return "无法开始实验"

    def _stop_experiment(self, content_id: int) -> str:
        """停止实验"""
        return "实验已停止"

    def _reset_physics(self, content_id: int) -> str:
        """重置物理状态"""
        if content_id in self.physics_engines:
            del self.physics_engines[content_id]
        return "物理状态已重置"

    def _increase_gravity(self, content_id: int) -> str:
        """增加重力"""
        engine = self.physics_engines.get(content_id)
        if engine:
            engine.gravity *= 1.5
            return f"重力增加到 {engine.gravity:.2f} m/s²"
        return "无法调整重力"

    def _decrease_gravity(self, content_id: int) -> str:
        """减少重力"""
        engine = self.physics_engines.get(content_id)
        if engine:
            engine.gravity *= 0.7
            return f"重力减少到 {engine.gravity:.2f} m/s²"
        return "无法调整重力"

    def _play_simulation(self, content_id: int) -> str:
        """播放仿真"""
        return "仿真已播放"

    def _pause_simulation(self, content_id: int) -> str:
        """暂停仿真"""
        return "仿真已暂停"

    def _log_interaction(
        self,
        content_id: int,
        user_id: int,
        interaction_type: str,
        interaction_data: Dict[str, Any],
        success: bool,
    ):
        """记录交互日志"""
        try:
            log = ARVRInteractionLog(
                content_id=content_id,
                user_id=user_id,
                org_id=1,  # 假设org_id=1
                interaction_type=interaction_type,
                interaction_data=interaction_data,
                interaction_mode=InteractionMode(interaction_type),
                success=success,
                response_time=0.1,  # 简化处理
                created_at=datetime.utcnow(),
            )

            self.db.add(log)
            self.db.commit()

        except Exception as e:
            logger.error(f"记录交互日志失败: {e}")
            self.db.rollback()

    def get_physics_state(self, content_id: int) -> Dict[str, Any]:
        """
        获取物理状态

        Args:
            content_id: 内容ID

        Returns:
            Dict: 物理状态信息
        """
        engine = self.physics_engines.get(content_id)
        if not engine:
            return {"objects": []}

        objects_state = []
        for obj_id, obj in engine.objects.items():
            objects_state.append(
                {
                    "id": obj_id,
                    "position": obj["position"].tolist(),
                    "velocity": obj["velocity"].tolist(),
                    "mass": obj["mass"],
                    "is_static": obj["is_static"],
                }
            )

        return {
            "objects": objects_state,
            "gravity": engine.gravity,
            "time_step": engine.time_step,
        }

    def update_progress_tracking(
        self, content_id: int, user_id: int, progress_data: Dict[str, Any]
    ):
        """
        更新学习进度跟踪

        Args:
            content_id: 内容ID
            user_id: 用户ID
            progress_data: 进度数据
        """
        try:
            # 查找现有进度记录
            progress = (
                self.db.query(ARVRProgressTracking)
                .filter(
                    ARVRProgressTracking.content_id == content_id,
                    ARVRProgressTracking.user_id == user_id,
                )
                .first()
            )

            if not progress:
                # 创建新的进度记录
                progress = ARVRProgressTracking(
                    content_id=content_id,
                    user_id=user_id,
                    org_id=1,  # 假设org_id=1
                    progress_percentage=0.0,
                    current_state={},
                )
                self.db.add(progress)

            # 更新进度数据
            if "progress_percentage" in progress_data:
                progress.progress_percentage = progress_data["progress_percentage"]

            if "milestones_reached" in progress_data:
                current_milestones = progress.milestones_reached or []
                new_milestones = progress_data["milestones_reached"]
                progress.milestones_reached = list(
                    set(current_milestones + new_milestones)
                )

            if "interaction_count" in progress_data:
                progress.interaction_count = (
                    progress.interaction_count or 0
                ) + progress_data["interaction_count"]

            progress.last_accessed_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()

            self.db.commit()

        except Exception as e:
            logger.error(f"更新进度跟踪失败: {e}")
            self.db.rollback()


# Unity物理交互参考代码
UNITY_PHYSICS_INTERACTION_TEMPLATE = """
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

public class ARPhysicsInteraction : MonoBehaviour
{
    [Header("AR组件")]
    public ARSessionOrigin arOrigin;
    public ARRaycastManager raycastManager;

    [Header("物理设置")]
    public float forceMultiplier = 10f;
    public float grabDistance = 5f;

    private Camera arCamera;
    private GameObject grabbedObject;
    private Vector3 grabOffset;

    void Start()
    {
        arCamera = arOrigin.camera;
    }

    void Update()
    {
        HandleTouchInput();
        HandleGestureInput();
    }

    void HandleTouchInput()
    {
        if (Input.touchCount > 0)
        {
            Touch touch = Input.GetTouch(0);

            if (touch.phase == TouchPhase.Began)
            {
                HandleTouchBegan(touch);
            }
            else if (touch.phase == TouchPhase.Moved && grabbedObject != null)
            {
                HandleTouchMoved(touch);
            }
            else if (touch.phase == TouchPhase.Ended)
            {
                HandleTouchEnded(touch);
            }
        }
    }

    void HandleTouchBegan(Touch touch)
    {
        List<ARRaycastHit> hits = new List<ARRaycastHit>();

        if (raycastManager.Raycast(touch.position, hits, TrackableType.PlaneWithinPolygon))
        {
            // 检测是否点击到物理对象
            RaycastHit physicsHit;
            Ray ray = arCamera.ScreenPointToRay(touch.position);

            if (Physics.Raycast(ray, out physicsHit, grabDistance))
            {
                if (physicsHit.collider.CompareTag("Interactable"))
                {
                    grabbedObject = physicsHit.collider.gameObject;
                    grabOffset = grabbedObject.transform.position - physicsHit.point;

                    // 添加视觉反馈
                    HighlightObject(grabbedObject, true);
                }
            }
        }
    }

    void HandleTouchMoved(Touch touch)
    {
        if (grabbedObject != null)
        {
            Ray ray = arCamera.ScreenPointToRay(touch.position);
            Vector3 newPosition = ray.GetPoint(Vector3.Distance(arCamera.transform.position, grabbedObject.transform.position)) + grabOffset;

            // 平滑移动
            grabbedObject.transform.position = Vector3.Lerp(grabbedObject.transform.position, newPosition, 0.5f);
        }
    }

    void HandleTouchEnded(Touch touch)
    {
        if (grabbedObject != null)
        {
            // 移除视觉反馈
            HighlightObject(grabbedObject, false);
            grabbedObject = null;
        }
    }

    void HandleGestureInput()
    {
        // 处理双指缩放
        if (Input.touchCount == 2)
        {
            Touch touch1 = Input.GetTouch(0);
            Touch touch2 = Input.GetTouch(1);

            if (touch1.phase == TouchPhase.Moved || touch2.phase == TouchPhase.Moved)
            {
                float pinchDelta = Vector2.Distance(touch1.position, touch2.position);
                ScaleObjects(pinchDelta);
            }
        }

        // 处理旋转手势
        if (Input.touchCount == 2)
        {
            Touch touch1 = Input.GetTouch(0);
            Touch touch2 = Input.GetTouch(1);

            if (touch1.phase == TouchPhase.Moved || touch2.phase == TouchPhase.Moved)
            {
                Vector2 prevPos1 = touch1.position - touch1.deltaPosition;
                Vector2 prevPos2 = touch2.position - touch2.deltaPosition;

                float prevAngle = Mathf.Atan2(prevPos2.y - prevPos1.y, prevPos2.x - prevPos1.x) * Mathf.Rad2Deg;
                float currAngle = Mathf.Atan2(touch2.position.y - touch1.position.y, touch2.position.x - touch1.position.x) * Mathf.Rad2Deg;

                float deltaAngle = Mathf.DeltaAngle(prevAngle, currAngle);
                RotateObjects(deltaAngle);
            }
        }
    }

    void ScaleObjects(float pinchDelta)
    {
        // 缩放选中的对象
        if (grabbedObject != null)
        {
            float scaleFactor = 1 + (pinchDelta * 0.01f);
            grabbedObject.transform.localScale *= scaleFactor;
        }
    }

    void RotateObjects(float deltaAngle)
    {
        // 旋转选中的对象
        if (grabbedObject != null)
        {
            grabbedObject.transform.Rotate(Vector3.up, deltaAngle);
        }
    }

    void HighlightObject(GameObject obj, bool highlight)
    {
        Renderer renderer = obj.GetComponent<Renderer>();
        if (renderer != null)
        {
            if (highlight)
            {
                renderer.material.color = Color.yellow;
            }
            else
            {
                renderer.material.color = Color.white;
            }
        }
    }

    // 物理交互方法
    public void ApplyForceToNearbyObjects(Vector3 position, Vector3 force)
    {
        Collider[] colliders = Physics.OverlapSphere(position, 3f);

        foreach (Collider collider in colliders)
        {
            Rigidbody rb = collider.GetComponent<Rigidbody>();
            if (rb != null && !rb.isKinematic)
            {
                rb.AddForce(force, ForceMode.Impulse);
            }
        }
    }

    public void ToggleGravity()
    {
        Physics.gravity = Physics.gravity == Vector3.zero ? new Vector3(0, -9.81f, 0) : Vector3.zero;
    }

    // 硬件控制集成
    public void OnHardwareCommandEvent(string command)
    {
        switch (command.ToLower())
        {
            case "toggle_led":
                ApplyForceToNearbyObjects(Vector3.zero, new Vector3(0, 10f, 0));
                break;
            case "start_motor":
                ToggleGravity();
                break;
        }
    }
}
"""

if __name__ == "__main__":
    # 测试物理交互服务
    from utils.database import get_db

    db = next(get_db())
    service = ARPhysicsService(db)

    # 初始化物理引擎
    engine = service.initialize_physics_for_content(1)

    # 添加测试对象
    engine.add_object("test_cube", 1.0, (0, 5, 0))
    engine.add_object("ground", 0, (0, 0, 0))

    # 模拟几帧物理更新
    for i in range(100):
        engine.apply_force("test_cube", (0, 0, 5))  # 施加水平力
        engine.update()
        pos = engine.get_position("test_cube")
        print(f"Frame {i}: Position = {pos}")
