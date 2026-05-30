#!/usr/bin/env python3
"""
KiCad-packages3D 模型爬虫脚本

从 KiCad 官方 3D 模型库爬取常用电子元件模型信息，生成结构化的模型资源索引表。

目标仓库：https://github.com/KiCad/kicad-packages3D

筛选类别:
- Resistors_THT (直插电阻)
- Capacitors_THT (直插电容)
- Package_SO (SOP 封装 IC)
- Package_DIP (DIP 封装 IC)
- Crystal (晶振)
- LED (发光二极管)
- Switch (开关)
- Connector (连接器)

输出字段:
{
  "component_name": "R_Axial_DIN",
  "source_url": "https://...",
  "format": ".step/.wrl",
  "license": "CC BY-SA 4.0",
  "applicability_score": 9.5,
  "category": "resistor",
  "package_type": "axial"
}
"""

import os
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime
import hashlib


class KiCadModelScraper:
    """KiCad 3D 模型爬虫类"""

    # KiCad-packages3D GitHub 仓库基础 URL
    GITHUB_BASE_URL = "https://github.com/KiCad/kicad-packages3D/tree/master"
    RAW_BASE_URL = "https://raw.githubusercontent.com/KiCad/kicad-packages3D/master"

    # 目标类别映射
    CATEGORY_MAPPING = {
        'Resistors_THT': {
            'category': 'resistor',
            'package_types': ['axial', 'radial', 'sod'],
            'keywords': ['R_', 'Resistor']
        },
        'Capacitors_THT': {
            'category': 'capacitor',
            'package_types': ['radial', 'axial', 'snap_mount'],
            'keywords': ['C_', 'Capacitor']
        },
        'Package_SO': {
            'category': 'ic',
            'package_types': ['soic', 'so', 'sos'],
            'keywords': ['SOIC', 'SO-', 'SOP']
        },
        'Package_DIP': {
            'category': 'ic',
            'package_types': ['dip', 'dils'],
            'keywords': ['DIP', 'DIL']
        },
        'Crystal': {
            'category': 'crystal',
            'package_types': ['hc49_up', 'hc49_us', 'smd'],
            'keywords': ['Crystal', 'Quartz']
        },
        'LED': {
            'category': 'led',
            'package_types': ['5mm', '3mm', 'smd'],
            'keywords': ['LED', 'Led']
        },
        'Switch': {
            'category': 'switch',
            'package_types': ['tht', 'smd', 'pushbutton'],
            'keywords': ['SW_', 'Switch']
        },
        'Connector': {
            'category': 'connector',
            'package_types': ['pin_header', 'socket', 'terminal_block'],
            'keywords': ['Conn', 'JST', 'Molex']
        }
    }

    def __init__(self, output_dir: str = 'data'):
        self.output_dir = output_dir
        self.model_index: List[Dict] = []
        self.stats = {
            'total_scanned': 0,
            'total_selected': 0,
            'by_category': {}
        }

    def scan_github_directory(self, category_path: str) -> List[Dict]:
        """
        扫描 GitHub 目录获取模型文件列表

        Args:
            category_path: 类别路径 (如 'Resistors_THT')

        Returns:
            模型文件信息列表
        """
        models = []
        api_url = f"https://api.github.com/repos/KiCad/kicad-packages3D/contents/{category_path}"

        try:
            response = requests.get(api_url, timeout=30)
            if response.status_code == 200:
                contents = response.json()

                for item in contents:
                    if item['type'] == 'dir':
                        # 递归扫描子目录
                        sub_models = self.scan_github_directory(f"{category_path}/{item['name']}")
                        models.extend(sub_models)
                    elif item['type'] == 'file':
                        # 检查是否为 3D 模型文件
                        if self.is_model_file(item['name']):
                            model_info = self.extract_model_info(item, category_path)
                            if model_info:
                                models.append(model_info)

        except Exception as e:
            print(f"扫描目录 {category_path} 时出错：{e}")

        return models

    def is_model_file(self, filename: str) -> bool:
        """检查文件是否为支持的 3D 模型格式"""
        supported_extensions = ['.step', '.stp', '.wrl', '.igs', '.iges']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)

    def extract_model_info(self, file_item: Dict, category_path: str) -> Optional[Dict]:
        """
        从文件信息中提取模型元数据

        Args:
            file_item: GitHub API 返回的文件信息
            category_path: 类别路径

        Returns:
            模型元数据字典
        """
        filename = file_item['name']
        file_url = file_item['html_url']
        download_url = file_item.get('download_url')

        # 解析文件名获取元件信息
        component_name = os.path.splitext(filename)[0]
        file_format = os.path.splitext(filename)[1].lower()

        # 确定类别
        category_info = self.determine_category(category_path, component_name)
        if not category_info:
            return None

        # 计算适用性评分
        applicability_score = self.calculate_applicability_score(
            category_info, component_name, file_format
        )

        # 生成唯一 ID
        model_id = self.generate_model_id(component_name, category_info['category'])

        return {
            'id': model_id,
            'component_name': component_name,
            'source_url': download_url or file_url,
            'github_url': file_url,
            'format': file_format,
            'license': 'CC BY-SA 4.0',
            'license_url': 'https://creativecommons.org/licenses/by-sa/4.0/',
            'applicability_score': applicability_score,
            'category': category_info['category'],
            'package_type': category_info['package_type'],
            'kicad_category': category_path,
            'file_size_bytes': file_item.get('size', 0),
            'last_modified': file_item.get('sha', 'unknown'),
            'indexed_at': datetime.now().isoformat()
        }

    def determine_category(self, kicad_category: str, component_name: str) -> Optional[Dict]:
        """
        根据 KiCad 类别和元件名确定分类信息

        Args:
            kicad_category: KiCad 原始类别
            component_name: 元件名称

        Returns:
            分类信息字典
        """
        if kicad_category not in self.CATEGORY_MAPPING:
            return None

        mapping = self.CATEGORY_MAPPING[kicad_category]

        # 确定具体的 package 类型
        package_type = 'unknown'
        for pkg in mapping['package_types']:
            if pkg.lower() in component_name.lower():
                package_type = pkg
                break

        return {
            'category': mapping['category'],
            'package_type': package_type
        }

    def calculate_applicability_score(self, category_info: Dict,
                                     component_name: str,
                                     file_format: str) -> float:
        """
        计算模型适用性评分 (0-10)

        评分标准:
        - STEP 格式优先 (+2 分)
        - 常用封装类型 (+1-3 分)
        - 命名规范 (+1 分)
        - 文件大小适中 (+1 分)
        """
        score = 5.0  # 基础分

        # 格式评分
        if file_format.lower() in ['.step', '.stp']:
            score += 2.0
        elif file_format.lower() == '.wrl':
            score += 1.0

        # 封装类型评分
        common_packages = ['axial', 'radial', 'dip', 'soic', '5mm']
        if category_info['package_type'] in common_packages:
            score += 2.0

        # 命名规范评分
        if '_' in component_name and len(component_name) > 3:
            score += 1.0

        # 限制最高分
        return min(score, 10.0)

    def generate_model_id(self, component_name: str, category: str) -> str:
        """生成唯一的模型 ID"""
        # 使用组件名称和类别生成哈希
        unique_str = f"{category}_{component_name}"
        hash_obj = hashlib.md5(unique_str.encode())
        short_hash = hash_obj.hexdigest()[:8]
        return f"{category}_{short_hash}"

    def scrape_all_categories(self) -> List[Dict]:
        """爬取所有目标类别的模型"""
        print("开始爬取 KiCad-packages3D 模型库...")

        for category_path in self.CATEGORY_MAPPING.keys():
            print(f"\n正在扫描：{category_path}")

            try:
                models = self.scan_github_directory(category_path)
                print(f"  找到 {len(models)} 个模型文件")

                self.model_index.extend(models)
                self.stats['total_scanned'] += len(models)

                # 统计各类别数量
                category = self.CATEGORY_MAPPING[category_path]['category']
                if category not in self.stats['by_category']:
                    self.stats['by_category'][category] = 0
                self.stats['by_category'][category] += len(models)

            except Exception as e:
                print(f"  扫描失败：{e}")

        # 按适用性评分排序
        self.model_index.sort(key=lambda x: x['applicability_score'], reverse=True)
        self.stats['total_selected'] = len(self.model_index)

        print(f"\n爬取完成！共收集 {len(self.model_index)} 个模型")
        return self.model_index

    def save_index(self, filename: str = 'kicad_model_index.json'):
        """保存模型索引到文件"""
        output_path = os.path.join(self.output_dir, filename)

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        export_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_repository': 'https://github.com/KiCad/kicad-packages3D',
                'license': 'CC BY-SA 4.0',
                'total_models': len(self.model_index),
                'stats': self.stats
            },
            'models': self.model_index
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"模型索引已保存到：{output_path}")

        # 同时保存统计信息
        stats_path = os.path.join(self.output_dir, 'kicad_model_stats.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)

        print(f"统计信息已保存到：{stats_path}")

    def print_summary(self):
        """打印爬取摘要"""
        print("\n" + "="*60)
        print("KiCad 模型爬取摘要")
        print("="*60)
        print(f"总扫描文件数：{self.stats['total_scanned']}")
        print(f"入选模型数：{self.stats['total_selected']}")
        print("\n各类别分布:")
        for category, count in sorted(self.stats['by_category'].items()):
            print(f"  {category}: {count} 个模型")
        print("="*60)


def main():
    """主函数"""
    scraper = KiCadModelScraper(output_dir='data')

    # 爬取所有类别
    models = scraper.scrape_all_categories()

    # 保存索引
    scraper.save_index()

    # 打印摘要
    scraper.print_summary()

    # 生成选择指南文档
    generate_selection_guide(models, 'docs/KICAD_MODEL_SELECTION_GUIDE.md')


def generate_selection_guide(models: List[Dict], output_path: str):
    """生成模型选择指南文档"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    guide_content = f"""# KiCad 3D 模型选择指南

## 概述

本文档说明如何从 KiCad-packages3D 库中选择适合虚拟实验室使用的电子元件 3D 模型。

**数据源**: https://github.com/KiCad/kicad-packages3D
**许可证**: CC BY-SA 4.0
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**模型总数**: {len(models)}

---

## 模型分类统计

| 类别 | 模型数量 | 主要封装类型 |
|------|---------|-------------|
"""

    # 统计各类别
    category_stats = {}
    for model in models:
        cat = model['category']
        if cat not in category_stats:
            category_stats[cat] = {'count': 0, 'packages': set()}
        category_stats[cat]['count'] += 1
        category_stats[cat]['packages'].add(model['package_type'])

    for cat, stats in sorted(category_stats.items()):
        packages = ', '.join(sorted(stats['packages']))
        guide_content += f"| {cat} | {stats['count']} | {packages} |\n"

    guide_content += f"""
---

## 选择标准

### 1. 格式优先级

1. **STEP 格式 (.step/.stp)** - ⭐⭐⭐⭐⭐
   - 精度高，适合工程应用
   - 推荐用于所有可用 STEP 格式的元件

2. **VRML 格式 (.wrl)** - ⭐⭐⭐
   - 颜色信息完整
   - 可作为备选格式

3. **IGES 格式 (.igs/.iges)** - ⭐⭐
   - 较老格式，精度一般
   - 仅在无其他格式时使用

### 2. 适用性评分说明

评分范围：0-10 分

- **9-10 分**: 强烈推荐 - 标准封装，STEP 格式
- **7-8 分**: 推荐 - 常用封装，格式良好
- **5-6 分**: 可用 - 特殊封装或格式一般
- **<5 分**: 不推荐 - 仅在没有更好选择时使用

### 3. 常用元件推荐

#### 电阻 (Resistor)
- **直插轴向**: R_Axial_DIN, Resistor_Axial
- **直插径向**: R_Radial_THT
- **推荐评分**: ≥8.5

#### 电容 (Capacitor)
- **电解电容**: CP_Radial_D5.0mm_L11.0mm
- **瓷片电容**: C_Disc_D5.0mm
- **推荐评分**: ≥8.0

#### IC 芯片
- **DIP 封装**: DIP-8, DIP-14, DIP-20
- **SOP 封装**: SOIC-8, SOIC-14, SOIC-20
- **推荐评分**: ≥9.0

#### LED
- **5mm LED**: LED_D5.0mm
- **3mm LED**: LED_D3.0mm
- **SMD LED**: LED_SMD
- **推荐评分**: ≥8.5

---

## 使用说明

### 引用格式

在项目中使用时，请按以下格式注明来源:

```
3D Model: [Component Name]
Source: KiCad-packages3D Library
URL: https://github.com/KiCad/kicad-packages3D
License: CC BY-SA 4.0
```

### 模型转换

所有选中的模型需要转换为 .glb 格式才能用于虚拟实验室:

```bash
# 使用 Blender 批量转换
python scripts/model_converter.py --input data/kicad_models/ --output models/electronic_components/
```

---

## 完整模型列表

详见数据文件：`data/kicad_model_index.json`

---

*文档由 KiCad 模型爬虫自动生成*
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)

    print(f"模型选择指南已保存到：{output_path}")


if __name__ == '__main__':
    main()
