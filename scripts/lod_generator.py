#!/usr/bin/env python3
"""
模型轻量化与 LOD (Level of Detail) 生成器

使用 Blender 或 MeshLab 为每个模型生成 3 个 LOD 级别:
- High: 原始质量 (5000 triangles)
- Medium: 中等质量 (1500 triangles)
- Low: 低质量 (500 triangles, 10-20% 面数)

输入：models/electronic_components/ (GLB 文件集)
输出：models/electronic_components_lod/ (包含 LOD 的模型文件)
验收标准:
- 低模面数降至高模的 10%-20%
- 视觉无明显失真
- LOD 切换距离合理配置
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LODGenerator:
    """LOD 生成器类"""

    # LOD 配置
    LOD_CONFIGS = {
        'high': {
            'ratio': 1.0,      # 100% 面数
            'target_tris': 5000,
            'suffix': '_high'
        },
        'medium': {
            'ratio': 0.3,      # 30% 面数
            'target_tris': 1500,
            'suffix': '_medium'
        },
        'low': {
            'ratio': 0.1,      # 10% 面数
            'target_tris': 500,
            'suffix': '_low'
        }
    }

    def __init__(self,
                 input_dir: str,
                 output_dir: str,
                 blender_path: Optional[str] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.blender_path = blender_path or self._find_blender()

        self.stats = {
            'total_models': 0,
            'successful': 0,
            'failed': 0,
            'lod_stats': {}
        }

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _find_blender(self) -> str:
        """自动查找 Blender 可执行文件"""
        common_paths = [
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        blender_in_path = shutil.which('blender')
        if blender_in_path:
            return blender_in_path

        raise FileNotFoundError("未找到 Blender 可执行文件")

    def generate_lod_for_model(self, input_path: Path) -> bool:
        """
        为单个模型生成所有 LOD 级别

        Args:
            input_path: 输入 GLB 文件路径

        Returns:
            是否成功
        """
        logger.info(f"处理模型：{input_path.name}")

        base_name = input_path.stem
        model_stats = {}

        for lod_level, config in self.LOD_CONFIGS.items():
            output_filename = f"{base_name}{config['suffix']}.glb"
            output_path = self.output_dir / output_filename

            success = self._generate_single_lod(
                input_path, output_path, lod_level, config
            )

            if success:
                # 统计三角形数量
                tri_count = self._count_triangles(output_path)
                file_size_mb = output_path.stat().st_size / (1024 * 1024)

                model_stats[lod_level] = {
                    'file': output_filename,
                    'triangles': tri_count,
                    'size_mb': round(file_size_mb, 2)
                }

                logger.info(f"  ✓ {lod_level}: {tri_count} tris, {file_size_mb:.2f}MB")
            else:
                logger.error(f"  ✗ {lod_level} 失败")
                return False

        self.stats['lod_stats'][base_name] = model_stats
        return True

    def _generate_single_lod(self,
                            input_path: Path,
                            output_path: Path,
                            lod_level: str,
                            config: Dict) -> bool:
        """生成单个 LOD 级别"""

        blender_script = f"""
import bpy
import bmesh

# 清除默认场景
bpy.ops.wm.read_factory_settings(use_empty=True)

# 导入 GLB 文件
input_path = r"{input_path}"
bpy.ops.import_scene.gltf(filepath=input_path)

# 获取所有网格对象
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

if not objects:
    print("未找到网格对象")
    exit(1)

# 应用 Decimate modifier 减面
ratio = {config['ratio']}

for obj in objects:
    bpy.context.view_layer.objects.active = obj

    # 添加减面修改器
    bpy.ops.object.modifier_add(type='DECIMATE')
    modifier = obj.modifiers["Decimate"]
    modifier.ratio = ratio

    # 应用修改器
    bpy.ops.object.modifier_apply(modifier="Decimate")

    # 重新计算法线
    bpy.ops.object.shade_smooth()

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
    export_uv=True
)

print(f"LOD {{lod_level}} 导出成功：{{output_path}}")
"""

        try:
            cmd = [
                self.blender_path,
                '--background',
                '--python-expr', blender_script
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return True
            else:
                logger.error(f"Blender 错误：{result.stderr}")
                return False

        except Exception as e:
            logger.error(f"生成 LOD 失败：{str(e)}")
            return False

    def _count_triangles(self, glb_path: Path) -> int:
        """统计 GLB 文件的三角形数量"""
        blender_script = f"""
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"{glb_path}")

total_tris = 0
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        mesh = obj.data
        total_tris += len(mesh.polygons)

print(total_tris)
"""

        try:
            result = subprocess.run(
                [self.blender_path, '--background', '--python-expr', blender_script],
                capture_output=True,
                text=True,
                timeout=60
            )

            # 提取最后一行的数字
            lines = result.stdout.strip().split('\n')
            for line in reversed(lines):
                if line.isdigit():
                    return int(line)

            return 0
        except:
            return 0

    def generate_all(self) -> Dict:
        """批量生成所有模型的 LOD"""
        logger.info("="*60)
        logger.info("开始生成 LOD")
        logger.info(f"输入目录：{self.input_dir}")
        logger.info(f"输出目录：{self.output_dir}")
        logger.info("="*60)

        start_time = datetime.now()

        # 查找所有 GLB 文件 (排除已生成的 LOD 文件)
        glb_files = [
            f for f in self.input_dir.glob('*.glb')
            if not any(suffix in f.stem for suffix in ['_high', '_medium', '_low'])
        ]

        self.stats['total_models'] = len(glb_files)
        logger.info(f"找到 {len(glb_files)} 个模型文件")

        for i, glb_file in enumerate(glb_files, 1):
            logger.info(f"\n进度：[{i}/{len(glb_files)}]")

            success = self.generate_lod_for_model(glb_file)

            if success:
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1

        elapsed_time = (datetime.now() - start_time).total_seconds()

        self.print_statistics(elapsed_time)
        self.save_lod_log()

        return self.stats

    def print_statistics(self, elapsed_time: float):
        """打印统计信息"""
        logger.info("\n" + "="*60)
        logger.info("LOD 生成统计")
        logger.info("="*60)
        logger.info(f"总模型数：{self.stats['total_models']}")
        logger.info(f"成功：{self.stats['successful']}")
        logger.info(f"失败：{self.stats['failed']}")
        logger.info(f"成功率：{self.stats['successful'] / max(self.stats['total_models'], 1) * 100:.1f}%")
        logger.info(f"耗时：{elapsed_time:.1f} 秒")

        # 显示部分模型的 LOD 详情
        if self.stats['lod_stats']:
            logger.info("\nLOD 详情示例:")
            for model_name, lods in list(self.stats['lod_stats'].items())[:3]:
                logger.info(f"\n{model_name}:")
                for lod_level, stats in lods.items():
                    logger.info(f"  {lod_level}: {stats['triangles']} tris, {stats['size_mb']}MB")

        logger.info("="*60)

    def save_lod_log(self, filename: str = 'lod_generation_log.json'):
        """保存 LOD 生成日志"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'statistics': self.stats
        }

        log_path = Path('logs') / filename
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"LOD 日志已保存到：{log_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='模型 LOD 生成器')
    parser.add_argument('--input', '-i', default='models/electronic_components',
                       help='输入目录')
    parser.add_argument('--output', '-o', default='models/electronic_components_lod',
                       help='输出目录')
    parser.add_argument('--blender-path', '-b', help='Blender 路径')

    args = parser.parse_args()

    generator = LODGenerator(
        input_dir=args.input,
        output_dir=args.output,
        blender_path=args.blender_path
    )

    stats = generator.generate_all()

    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
