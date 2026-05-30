# KiCad 3D 模型选择指南

## 概述

本文档说明如何从 KiCad-packages3D 库中选择适合虚拟实验室使用的电子元件 3D 模型。

**数据源**: https://github.com/KiCad/kicad-packages3D  
**许可证**: CC BY-SA 4.0  
**生成时间**: 2026-03-03  
**模型总数**: 256

---

## 模型分类统计

| 类别 | 模型数量 | 主要封装类型 |
|------|---------|-------------|
| resistor (电阻) | 48 | axial, radial, sod |
| capacitor (电容) | 42 | radial, axial, snap_mount |
| ic (集成电路) | 68 | dip, soic, sop |
| crystal (晶振) | 18 | hc49_up, hc49_us, smd |
| led (发光二极管) | 32 | 5mm, 3mm, smd |
| switch (开关) | 24 | tht, smd, pushbutton |
| connector (连接器) | 24 | pin_header, socket, terminal_block |

---

## 选择标准

### 1. 格式优先级

1. **STEP 格式 (.step/.stp)** - ⭐⭐⭐⭐⭐
   - 精度高，适合工程应用
   - 推荐用于所有可用 STEP 格式的元件
   - 转换 GLB 后质量损失最小

2. **VRML 格式 (.wrl)** - ⭐⭐⭐
   - 颜色信息完整
   - 可作为备选格式
   - 需要额外的纹理处理

3. **IGES 格式 (.igs/.iges)** - ⭐⭐
   - 较老格式，精度一般
   - 仅在无其他格式时使用
   - 可能需要手动修复

### 2. 适用性评分说明

评分范围：0-10 分

- **9-10 分**: 强烈推荐 - 标准封装，STEP 格式，命名规范
- **7-8 分**: 推荐 - 常用封装，格式良好
- **5-6 分**: 可用 - 特殊封装或格式一般
- **<5 分**: 不推荐 - 仅在没有更好选择时使用

### 3. 常用元件推荐

#### 电阻 (Resistor)
- **直插轴向**: R_Axial_DIN, Resistor_Axial
- **直插径向**: R_Radial_THT
- **推荐评分**: ≥8.5
- **典型应用**: 电路限流、分压、负载电阻

#### 电容 (Capacitor)
- **电解电容**: CP_Radial_D5.0mm_L11.0mm
- **瓷片电容**: C_Disc_D5.0mm
- **推荐评分**: ≥8.0
- **典型应用**: 滤波、耦合、去耦

#### IC 芯片
- **DIP 封装**: DIP-8, DIP-14, DIP-20
- **SOP 封装**: SOIC-8, SOIC-14, SOIC-20
- **推荐评分**: ≥9.0
- **典型应用**: 运算放大器、定时器、逻辑门

#### LED
- **5mm LED**: LED_D5.0mm
- **3mm LED**: LED_D3.0mm
- **SMD LED**: LED_SMD
- **推荐评分**: ≥8.5
- **典型应用**: 指示灯、显示屏、照明

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

### 模型转换流程

1. **下载 STEP 文件**
   ```bash
   # 使用爬虫脚本批量下载
   python scripts/kicad_model_scraper.py
   ```

2. **转换为 GLB 格式**
   ```bash
   # 使用 Blender 批量转换
   python scripts/model_converter.py --input data/kicad_models/ --output models/electronic_components/
   ```

3. **生成 LOD 级别**
   ```bash
   # 为每个模型生成高、中、低三个 LOD 级别
   python scripts/lod_generator.py --input models/electronic_components/
   ```

### 质量控制检查清单

- [ ] 模型完整性：无缺失的几何体
- [ ] 尺寸准确性：与实际元件尺寸一致
- [ ] 材质正确性：引脚、本体材质区分清晰
- [ ] 面数合理性：高模 < 5000 triangles
- [ ] 坐标准确性：原点在元件几何中心
- [ ] 命名规范性：符合项目命名标准

---

## 完整模型列表

详见数据文件：`data/kicad_model_index.json`

索引文件包含以下字段:
- `id`: 唯一模型标识符
- `component_name`: 元件名称
- `source_url`: 源文件 URL
- `format`: 文件格式
- `license`: 许可证信息
- `applicability_score`: 适用性评分
- `category`: 类别
- `package_type`: 封装类型
- `file_size_bytes`: 文件大小

---

## 更新维护

### 定期更新

建议每季度更新一次模型索引，以获取 KiCad 库的最新内容:

```bash
# 重新运行爬虫
python scripts/kicad_model_scraper.py

# 查看更新日志
cat data/kicad_model_stats.json
```

### 新增元件

如需添加新的元件类别:

1. 在 `scripts/kicad_model_scraper.py` 的 `CATEGORY_MAPPING` 中添加新类别
2. 定义筛选规则和关键词
3. 重新运行爬虫脚本
4. 更新本文档的统计表

---

## 常见问题

### Q: 为什么某些模型的评分较低？
A: 评分基于格式质量、封装通用性、命名规范等因素。低分模型可能是特殊封装或格式不佳。

### Q: 可以手动修改模型吗？
A: 可以。根据 CC BY-SA 4.0 许可证，允许修改，但需注明原始来源并以相同许可证发布。

### Q: 如何报告模型问题？
A: 在项目的 Issue  tracker 中提交问题，附上模型 ID 和具体问题描述。

---

*文档由 KiCad 模型爬虫自动生成 - 最后更新：2026-03-03*
