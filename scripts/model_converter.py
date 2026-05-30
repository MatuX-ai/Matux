#!/usr/bin/env python3
"""
KiCad 模型批量转换器

使用 Blender 将 STEP/VRML/IGES 格式批量转换为 GLB/GLTF 格式

技术栈:
- Blender 3.6+ (命令行批处理模式)
- Python 脚本自动化
- COLLADA2GLTF (备选方案)

输入：data/kicad_models/ (原始 STEP/VRML 文件)
输出：models/electronic_components/ (GLB 文件集)
验收标准:
- 转换成功率 > 95%
- 单个模型文件大小 < 2MB
- 材质和纹理正确保留
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/model_converter.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelConverter:
    """模型转换器类"""

    # 支持的输入格式
    SUPPORTED_FORMATS = {
        '.step': 'STEP',
        '.stp': 'STEP',
        '.wrl': 'VRML',
        '.igs': 'IGES',
        '.iges': 'IGES'
    }

    # 最大输出文件大小 (MB)
    MAX_FILE_SIZE_MB = 2.0

    def __init__(self,
                 input_dir: str,
                 output_dir: str,
                 blender_path: Optional[str] = None):
        """
        初始化转换器

        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            blender_path: Blender 可执行文件路径 (可选)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.blender_path = blender_path or self._find_blender()

        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_size_mb': 0.0,
            'errors': []
        }

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 创建日志目录
        Path('logs').mkdir(exist_ok=True)

    def _find_blender(self) -> str:
        """自动查找 Blender 可执行文件"""
        # Windows 常见安装路径
        common_paths = [
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.4\blender.exe",
            r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                logger.info(f"找到 Blender: {path}")
                return path

        # 尝试在 PATH 中查找
        blender_in_path = shutil.which('blender')
        if blender_in_path:
            logger.info(f"在 PATH 中找到 Blender: {blender_in_path}")
            return blender_in_path

        raise FileNotFoundError(
            "未找到 Blender 可执行文件。请安装 Blender 3.6+ 或指定 --blender-path 参数"
        )

    def find_model_files(self) -> List[Path]:
        """查找所有待转换的模型文件"""
        model_files = []

        for ext in self.SUPPORTED_FORMATS.keys():
            pattern = f"**/*{ext}"
            files = list(self.input_dir.glob(pattern))
            model_files.extend(files)

        logger.info(f"找到 {len(model_files)} 个模型文件")
        self.stats['total_files'] = len(model_files)

        return sorted(model_files)

    def convert_step_to_glb(self, input_path: Path, output_path: Path) -> bool:
        """
        使用 Blender 将 STEP 文件转换为 GLB

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径

        Returns:
            是否转换成功
        """
        # Blender Python 脚本
        blender_script = f"""
import bpy
import os

# 清除默认场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入 STEP 文件
input_path = r"{input_path}"
try:
    bpy.ops.import_mesh.step(filepath=input_path)
except Exception as e:
    print(f"导入 STEP 失败：{{e}}")
    exit(1)

# 获取所有网格对象
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

if not objects:
    print("未找到网格对象")
    exit(1)

# 应用平滑着色
for obj in objects:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

# 优化网格 - 减面 modifier
for obj in objects:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='DECIMATE')
    obj.modifiers["Decimate"].ratio = 0.5  # 减少 50% 面数
    bpy.ops.object.modifier_apply(modifier="Decimate")

# 设置原点为几何中心
for obj in objects:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

# 导出 GLB
output_path = r"{output_path}"
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    export_apply=True,
    export_materials='EXPORT',
    export_colors=True,
    export_normals=True,
    export_tangents=True,
    export_uv=True,
    export_cameras=False,
    export_lights=False
)

print(f"成功导出：{{output_path}}")
"""

        try:
            # 执行 Blender 命令行
            cmd = [
                self.blender_path,
                '--background',  # 后台模式
                '--python-expr', blender_script
            ]

            logger.info(f"转换：{input_path.name} -> {output_path.name}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 分钟超时
            )

            if result.returncode == 0:
                logger.info(f"✓ 转换成功：{output_path.name}")
                return True
            else:
                error_msg = f"Blender 错误：{result.stderr}"
                logger.error(error_msg)
                self.stats['errors'].append({
                    'file': str(input_path),
                    'error': error_msg
                })
                return False

        except subprocess.TimeoutExpired:
            error_msg = "转换超时 (>5 分钟)"
            logger.error(error_msg)
            self.stats['errors'].append({
                'file': str(input_path),
                'error': error_msg
            })
            return False
        except Exception as e:
            error_msg = f"转换异常：{str(e)}"
            logger.error(error_msg)
            self.stats['errors'].append({
                'file': str(input_path),
                'error': error_msg
            })
            return False

    def validate_output(self, output_path: Path) -> bool:
        """验证输出文件是否符合要求"""
        if not output_path.exists():
            return False

        # 检查文件大小
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            logger.warning(f"文件过大：{output_path.name} ({file_size_mb:.2f}MB)")
            return False

        self.stats['total_size_mb'] += file_size_mb
        return True

    def convert_all(self) -> Dict:
        """批量转换所有模型文件"""
        logger.info("="*60)
        logger.info("开始批量转换模型")
        logger.info(f"输入目录：{self.input_dir}")
        logger.info(f"输出目录：{self.output_dir}")
        logger.info(f"Blender 路径：{self.blender_path}")
        logger.info("="*60)

        start_time = datetime.now()

        model_files = self.find_model_files()

        for i, input_file in enumerate(model_files, 1):
            logger.info(f"\n进度：[{i}/{len(model_files)}]")

            # 生成输出文件名
            output_filename = input_file.stem + '.glb'
            output_file = self.output_dir / output_filename

            # 跳过已存在的文件
            if output_file.exists():
                logger.info(f"跳过已存在的文件：{output_filename}")
                self.stats['skipped'] += 1
                continue

            # 执行转换
            success = self.convert_step_to_glb(input_file, output_file)

            if success:
                # 验证输出
                if self.validate_output(output_file):
                    self.stats['successful'] += 1
                else:
                    self.stats['failed'] += 1
                    logger.error(f"验证失败：{output_filename}")
            else:
                self.stats['failed'] += 1

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # 打印统计信息
        self.print_statistics(elapsed_time)

        # 保存转换日志
        self.save_conversion_log()

        return self.stats

    def print_statistics(self, elapsed_time: float):
        """打印转换统计信息"""
        logger.info("\n" + "="*60)
        logger.info("转换统计")
        logger.info("="*60)
        logger.info(f"总文件数：{self.stats['total_files']}")
        logger.info(f"成功：{self.stats['successful']}")
        logger.info(f"失败：{self.stats['failed']}")
        logger.info(f"跳过：{self.stats['skipped']}")
        logger.info(f"成功率：{self.stats['successful'] / max(self.stats['total_files'], 1) * 100:.1f}%")
        logger.info(f"总输出大小：{self.stats['total_size_mb']:.2f} MB")
        logger.info(f"平均文件大小：{self.stats['total_size_mb'] / max(self.stats['successful'], 1):.2f} MB")
        logger.info(f"耗时：{elapsed_time:.1f} 秒")
        logger.info("="*60)

    def save_conversion_log(self, filename: str = 'conversion_log.json'):
        """保存转换日志"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'blender_version': self._get_blender_version(),
            'statistics': self.stats
        }

        log_path = Path('logs') / filename
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"转换日志已保存到：{log_path}")

    def _get_blender_version(self) -> str:
        """获取 Blender 版本"""
        try:
            result = subprocess.run(
                [self.blender_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            # 提取版本信息 (第一行)
            version_line = result.stdout.split('\n')[0]
            return version_line
        except:
            return "unknown"


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='KiCad 模型批量转换器')
    parser.add_argument('--input', '-i', default='data/kicad_models',
                       help='输入目录 (默认：data/kicad_models)')
    parser.add_argument('--output', '-o', default='models/electronic_components',
                       help='输出目录 (默认：models/electronic_components)')
    parser.add_argument('--blender-path', '-b',
                       help='Blender 可执行文件路径')
    parser.add_argument('--max-size', '-m', type=float, default=2.0,
                       help='最大输出文件大小 MB (默认：2.0)')

    args = parser.parse_args()

    # 创建转换器
    converter = ModelConverter(
        input_dir=args.input,
        output_dir=args.output,
        blender_path=args.blender_path
    )

    converter.MAX_FILE_SIZE_MB = args.max_size

    # 执行批量转换
    stats = converter.convert_all()

    # 返回退出码
    if stats['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
