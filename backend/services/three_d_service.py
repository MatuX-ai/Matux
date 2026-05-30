"""
3D模型预览服务
使用Three.js提供交互式3D模型展示功能
"""

import json
import logging
import os
from typing import Any, Dict, List

from pygltflib import GLTF2
from sqlalchemy.orm import Session
import trimesh

from models.multimedia import MediaType, MultimediaResource
from services.multimedia_service import StorageConfig

logger = logging.getLogger(__name__)


class ThreeDModelService:
    """3D模型服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.storage_config = StorageConfig()

    def process_3d_model(self, resource_id: int) -> Dict[str, Any]:
        """
        处理3D模型文件，生成预览所需的数据

        Args:
            resource_id: 资源ID

        Returns:
            Dict: 处理结果和预览配置
        """
        try:
            # 获取资源信息
            resource = (
                self.db.query(MultimediaResource)
                .filter(MultimediaResource.id == resource_id)
                .first()
            )

            if not resource:
                raise ValueError(f"资源不存在: {resource_id}")

            if resource.media_type != MediaType.THREE_D_MODEL:
                raise ValueError("资源不是3D模型类型")

            # 下载模型文件
            model_data = self._download_model_file(resource)

            # 分析模型信息
            model_info = self._analyze_model(model_data, resource.file_extension)

            # 生成预览配置
            preview_config = self._generate_preview_config(resource, model_info)

            # 更新资源信息
            resource.model_format = resource.file_extension
            resource.model_dimensions = model_info.get("dimensions", {})
            resource.preview_config = preview_config
            self.db.commit()

            logger.info(f"3D模型处理完成: {resource_id}")

            return {
                "success": True,
                "resource_id": resource_id,
                "model_info": model_info,
                "preview_config": preview_config,
            }

        except Exception as e:
            logger.error(f"3D模型处理失败: {e}")
            raise

    def _download_model_file(self, resource: MultimediaResource) -> bytes:
        """下载模型文件"""
        if self.storage_config.storage_type == "s3":
            return self._download_from_s3(resource.original_url)
        else:
            return self._read_local_file(resource.original_url)

    def _download_from_s3(self, file_url: str) -> bytes:
        """从S3下载文件"""

        # 从URL解析bucket和key
        if file_url.startswith("https://"):
            parts = file_url.split("/")
            bucket = parts[2].split(".")[0]
            key = "/".join(parts[3:])

            s3_client = self.storage_config.get_s3_client()
            response = s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        else:
            raise ValueError("无效的S3 URL格式")

    def _read_local_file(self, file_url: str) -> bytes:
        """读取本地文件"""
        if file_url.startswith("/"):
            file_path = file_url[1:]  # 移除开头的斜杠
        else:
            file_path = file_url

        full_path = os.path.join(os.getcwd(), file_path)
        with open(full_path, "rb") as f:
            return f.read()

    def _analyze_model(self, model_data: bytes, file_extension: str) -> Dict[str, Any]:
        """
        分析3D模型文件，提取基本信息

        Args:
            model_data: 模型文件数据
            file_extension: 文件扩展名

        Returns:
            Dict: 模型信息
        """
        try:
            if file_extension.lower() in ["obj"]:
                return self._analyze_obj_model(model_data)
            elif file_extension.lower() in ["stl"]:
                return self._analyze_stl_model(model_data)
            elif file_extension.lower() in ["glb", "gltf"]:
                return self._analyze_gltf_model(model_data)
            else:
                raise ValueError(f"不支持的模型格式: {file_extension}")

        except Exception as e:
            logger.error(f"模型分析失败: {e}")
            # 返回默认信息
            return {
                "vertices": 0,
                "faces": 0,
                "dimensions": {"width": 100, "height": 100, "depth": 100},
                "format": file_extension,
                "bounding_box": [[-50, -50, -50], [50, 50, 50]],
            }

    def _analyze_obj_model(self, model_data: bytes) -> Dict[str, Any]:
        """分析OBJ格式模型"""
        try:
            # 使用trimesh加载OBJ文件
            import io

            mesh = trimesh.load(io.BytesIO(model_data), file_type="obj")

            # 计算边界框
            bounds = mesh.bounds
            dimensions = {
                "width": float(bounds[1][0] - bounds[0][0]),
                "height": float(bounds[1][1] - bounds[0][1]),
                "depth": float(bounds[1][2] - bounds[0][2]),
            }

            return {
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "dimensions": dimensions,
                "format": "obj",
                "bounding_box": (
                    bounds.tolist() if hasattr(bounds, "tolist") else bounds.tolist()
                ),
            }

        except Exception as e:
            logger.error(f"OBJ模型分析失败: {e}")
            raise

    def _analyze_stl_model(self, model_data: bytes) -> Dict[str, Any]:
        """分析STL格式模型"""
        try:
            import io

            from stl import mesh

            # 加载STL文件
            stl_mesh = mesh.Mesh.from_file(io.BytesIO(model_data))

            # 计算顶点数（每个三角形3个顶点）
            vertices_count = len(stl_mesh.points) * 3
            faces_count = len(stl_mesh.points)

            # 计算边界框
            min_bound = stl_mesh.min_
            max_bound = stl_mesh.max_
            dimensions = {
                "width": float(max_bound[0] - min_bound[0]),
                "height": float(max_bound[1] - min_bound[1]),
                "depth": float(max_bound[2] - min_bound[2]),
            }

            return {
                "vertices": vertices_count,
                "faces": faces_count,
                "dimensions": dimensions,
                "format": "stl",
                "bounding_box": [min_bound.tolist(), max_bound.tolist()],
            }

        except Exception as e:
            logger.error(f"STL模型分析失败: {e}")
            raise

    def _analyze_gltf_model(self, model_data: bytes) -> Dict[str, Any]:
        """分析GLTF/GLB格式模型"""
        try:

            # 加载GLTF文件
            gltf = GLTF2.load_from_bytes(model_data)

            # 提取基本统计信息
            vertices_count = 0
            faces_count = 0

            if gltf.meshes:
                for mesh in gltf.meshes:
                    for primitive in mesh.primitives:
                        if primitive.attributes.POSITION is not None:
                            accessor = gltf.accessors[primitive.attributes.POSITION]
                            vertices_count += accessor.count

                        if primitive.indices is not None:
                            accessor = gltf.accessors[primitive.indices]
                            faces_count += accessor.count // 3  # 三角形面数

            # 计算边界框（简化处理）
            dimensions = {"width": 100.0, "height": 100.0, "depth": 100.0}

            return {
                "vertices": vertices_count,
                "faces": faces_count,
                "dimensions": dimensions,
                "format": "glb" if b"glTF" in model_data[:10] else "gltf",
                "bounding_box": [[-50, -50, -50], [50, 50, 50]],
            }

        except Exception as e:
            logger.error(f"GLTF模型分析失败: {e}")
            raise

    def _generate_preview_config(
        self, resource: MultimediaResource, model_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成Three.js预览配置

        Args:
            resource: 多媒体资源
            model_info: 模型信息

        Returns:
            Dict: 预览配置
        """
        # 计算合适的相机位置
        bounding_box = model_info.get("bounding_box", [[-50, -50, -50], [50, 50, 50]])
        center = [
            (bounding_box[0][0] + bounding_box[1][0]) / 2,
            (bounding_box[0][1] + bounding_box[1][1]) / 2,
            (bounding_box[0][2] + bounding_box[1][2]) / 2,
        ]

        # 计算包围球半径
        radius = (
            max(
                [
                    abs(bounding_box[1][0] - bounding_box[0][0]),
                    abs(bounding_box[1][1] - bounding_box[0][1]),
                    abs(bounding_box[1][2] - bounding_box[0][2]),
                ]
            )
            / 2
        )

        return {
            "modelUrl": resource.original_url,
            "modelFormat": resource.file_extension.lower(),
            "backgroundColor": "#ffffff",
            "showGrid": True,
            "showAxes": True,
            "autoRotate": True,
            "cameraPosition": {
                "x": center[0],
                "y": center[1],
                "z": center[2] + radius * 2,
            },
            "controls": {"enableZoom": True, "enablePan": True, "enableRotate": True},
            "lighting": {
                "ambientLight": 0x404040,
                "directionalLight": 0xFFFFFF,
                "directionalLightPosition": {"x": 1, "y": 1, "z": 1},
            },
            "modelStats": {
                "vertices": model_info.get("vertices", 0),
                "faces": model_info.get("faces", 0),
                "dimensions": model_info.get("dimensions", {}),
            },
        }

    def get_model_preview_html(self, resource_id: int, container_id: str = None) -> str:
        """
        生成3D模型预览的HTML代码

        Args:
            resource_id: 资源ID
            container_id: 容器ID

        Returns:
            str: HTML代码
        """
        try:
            # 获取资源和预览配置
            resource = (
                self.db.query(MultimediaResource)
                .filter(MultimediaResource.id == resource_id)
                .first()
            )

            if not resource or not resource.preview_config:
                raise ValueError("资源或预览配置不存在")

            preview_config = resource.preview_config
            if isinstance(preview_config, str):
                preview_config = json.loads(preview_config)

            # 生成唯一的容器ID
            if not container_id:
                container_id = f"model-viewer-{resource_id}"

            # 更新配置中的容器ID
            preview_config["containerId"] = container_id

            # 生成HTML代码
            html_template = self._get_preview_html_template(preview_config)

            return html_template

        except Exception as e:
            logger.error(f"生成预览HTML失败: {e}")
            raise

    def _get_preview_html_template(self, config: Dict[str, Any]) -> str:
        """获取预览HTML模板"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D模型预览</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <style>
        #{config['containerId']} {{
            width: 100%;
            height: 500px;
            border: 1px solid #ddd;
            position: relative;
        }}
        .model-info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: Arial, sans-serif;
            font-size: 12px;
        }}
        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-family: Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <div id="{config['containerId']}">
        <div class="loading">正在加载3D模型...</div>
        <div class="model-info">
            顶点数: {config['modelStats']['vertices']}<br>
            面数: {config['modelStats']['faces']}<br>
            尺寸: {config['modelStats']['dimensions']['width']:.1f} × {config['modelStats']['dimensions']['height']:.1f} × {config['modelStats']['dimensions']['depth']:.1f}
        </div>
    </div>

    <script>
        // 配置数据
        const config = {json.dumps(config, ensure_ascii=False)};

        // 初始化Three.js场景
        let scene, camera, renderer, controls, model;

        function init() {{
            // 创建场景
            scene = new THREE.Scene();
            scene.background = new THREE.Color(config.backgroundColor);

            // 创建相机
            const aspect = document.getElementById(config.containerId).clientWidth /
                          document.getElementById(config.containerId).clientHeight;
            camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
            camera.position.set(
                config.cameraPosition.x,
                config.cameraPosition.y,
                config.cameraPosition.z
            );

            // 创建渲染器
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(
                document.getElementById(config.containerId).clientWidth,
                document.getElementById(config.containerId).clientHeight
            );
            document.getElementById(config.containerId).innerHTML = '';
            document.getElementById(config.containerId).appendChild(renderer.domElement);

            // 添加控制器
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableZoom = config.controls.enableZoom;
            controls.enablePan = config.controls.enablePan;
            controls.enableRotate = config.controls.enableRotate;

            // 添加光源
            const ambientLight = new THREE.AmbientLight(config.lighting.ambientLight);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(
                config.lighting.directionalLight
            );
            directionalLight.position.set(
                config.lighting.directionalLightPosition.x,
                config.lighting.directionalLightPosition.y,
                config.lighting.directionalLightPosition.z
            );
            scene.add(directionalLight);

            // 添加网格
            if (config.showGrid) {{
                const gridHelper = new THREE.GridHelper(100, 20);
                scene.add(gridHelper);
            }}

            // 添加坐标轴
            if (config.showAxes) {{
                const axesHelper = new THREE.AxesHelper(50);
                scene.add(axesHelper);
            }}

            // 加载模型
            loadModel();

            // 开始渲染循环
            animate();

            // 处理窗口大小调整
            window.addEventListener('resize', onWindowResize, false);
        }}

        function loadModel() {{
            let loader;

            switch(config.modelFormat.toLowerCase()) {{
                case 'obj':
                    loader = new THREE.OBJLoader();
                    break;
                case 'stl':
                    loader = new THREE.STLLoader();
                    break;
                case 'glb':
                case 'gltf':
                    loader = new THREE.GLTFLoader();
                    break;
                default:
                    console.error('不支持的模型格式:', config.modelFormat);
                    return;
            }}

            loader.load(
                config.modelUrl,
                function (loadedModel) {{
                    if (config.modelFormat === 'glb' || config.modelFormat === 'gltf') {{
                        model = loadedModel.scene;
                    }} else {{
                        model = loadedModel;
                    }}

                    scene.add(model);

                    // 自动旋转
                    if (config.autoRotate) {{
                        model.rotation.y = 0;
                    }}
                }},
                function (xhr) {{
                    console.log((xhr.loaded / xhr.total * 100) + '% loaded');
                }},
                function (error) {{
                    console.error('加载模型出错:', error);
                }}
            );
        }}

        function animate() {{
            requestAnimationFrame(animate);

            if (model && config.autoRotate) {{
                model.rotation.y += 0.01;
            }}

            controls.update();
            renderer.render(scene, camera);
        }}

        function onWindowResize() {{
            camera.aspect = document.getElementById(config.containerId).clientWidth /
                           document.getElementById(config.containerId).clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(
                document.getElementById(config.containerId).clientWidth,
                document.getElementById(config.containerId).clientHeight
            );
        }}

        // 初始化
        init();
    </script>
</body>
</html>
        """

    def get_supported_formats(self) -> List[str]:
        """获取支持的3D模型格式"""
        return ["obj", "stl", "glb", "gltf"]

    def validate_model_file(self, file_data: bytes, file_extension: str) -> bool:
        """
        验证3D模型文件格式

        Args:
            file_data: 文件数据
            file_extension: 文件扩展名

        Returns:
            bool: 是否为有效的3D模型文件
        """
        try:
            if file_extension.lower() == "obj":
                return self._validate_obj_file(file_data)
            elif file_extension.lower() == "stl":
                return self._validate_stl_file(file_data)
            elif file_extension.lower() in ["glb", "gltf"]:
                return self._validate_gltf_file(file_data)
            else:
                return False

        except Exception as e:
            logger.error(f"模型文件验证失败: {e}")
            return False

    def _validate_obj_file(self, file_data: bytes) -> bool:
        """验证 OBJ 文件"""
        try:
            content = file_data.decode("utf-8", errors="ignore")
            return "v " in content or "f " in content
        except (UnicodeDecodeError, AttributeError):
            return False

    def _validate_stl_file(self, file_data: bytes) -> bool:
        """验证 STL 文件"""
        try:
            # STL 文件通常以"solid"开头或二进制格式
            if file_data.startswith(b"solid"):
                return True
            # 检查二进制 STL 文件头
            elif len(file_data) >= 84 and file_data[80:84] == b"\x00\x00\x00\x00":
                return True
            return False
        except (AttributeError, TypeError):
            return False

    def _validate_gltf_file(self, file_data: bytes) -> bool:
        """验证 GLTF 文件"""
        try:
            if b"glTF" in file_data[:10]:  # GLB 格式
                return True
            else:  # GLTF 格式（JSON）
                content = file_data.decode("utf-8", errors="ignore")
                return '"asset"' in content and '"version"' in content
        except (UnicodeDecodeError, AttributeError, TypeError):
            return False
