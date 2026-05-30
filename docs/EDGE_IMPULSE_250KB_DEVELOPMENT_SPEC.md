# Edge Impulse 250KB压缩开发规范

## 📋 规范文畴

本文档规定了Edge Impulse平台TinyML模型250KB压缩功能的开发规范，确保代码质量、功能一致性和团队协作效率。

## 🎯 核心原则

### 1. 功能唯一性原则
- 每个功能模块必须有明确的单一职责
- 避免功能重叠和重复实现
- 新功能开发前必须运行重复检测

### 2. 目标导向原则
- 严格遵守250KB压缩目标
- 优先保证模型质量，其次考虑压缩率
- 所有实现必须经过目标大小验证

### 3. 标准化原则
- 统一的代码风格和命名规范
- 标准化的目录结构
- 规范的文档格式

## 📁 目录结构规范

```
backend/
├── services/                           # 核心服务模块
│   ├── edge_impulse_client.py         # Edge Impulse API客户端 (必填注释)
│   ├── tinyml_compressor_250kb.py     # 250KB压缩器 (必填注释)
│   └── edge_impulse_deployment_manager.py  # 部署管理器 (必填注释)
├── utils/                              # 工具模块
│   └── duplicate_development_detector.py   # 重复开发检测器 (必填注释)
└── ai_service/                         # AI服务扩展
    └── model_compressor.py             # 现有压缩框架增强

scripts/
├── edge_impulse_250kb_backtest.py     # 回测验证程序 (必填注释)
└── model_benchmark.py                  # 基准测试工具

models/
└── tinyml/
    ├── edge_impulse/                   # Edge Impulse模型存储
    │   ├── voice_commands/            # 语音命令模型
    │   ├── gesture_recognition/       # 手势识别模型
    │   └── anomaly_detection/         # 异常检测模型
    └── deployments/                    # 部署包目录

docs/
├── EDGE_IMPULSE_250KB_INTEGRATION_TECHNICAL_DOC.md  # 技术文档
└── EDGE_IMPULSE_250KB_DEVELOPMENT_SPEC.md          # 开发规范(本文档)

deployment_records/                     # 部署记录
backtest_reports/                       # 回测报告
```

## 💻 代码规范

### 命名规范

#### 文件命名
```python
# ✅ 正确示例
edge_impulse_client.py          # 功能描述 + 类型
tinyml_compressor_250kb.py      # 功能描述 + 目标规格
duplicate_development_detector.py  # 功能描述 + 检测类型

# ❌ 错误示例
ei_client.py                    # 缩写不明确
compressor.py                   # 缺少功能描述
detector.py                     # 过于宽泛
```

#### 类命名
```python
# ✅ 正确示例
class EdgeImpulseClient:           # PascalCase，描述清楚
class TinyMLModelCompressor250KB:  # 包含关键规格信息
class DuplicateDevelopmentDetector: # 功能完整描述

# ❌ 错误示例
class EI_Client:                   # 使用下划线分隔
class Compressor:                  # 过于简单
class Detector:                    # 缺少上下文
```

#### 方法命名
```python
# ✅ 正确示例
def compress_to_target_size(self, model, target_size_kb=250):
def validate_compression_quality(self, original_model, compressed_model_path):
def detect_potential_duplicates(self):

# ❌ 错误示例
def compress(self):                # 缺少参数说明
def validate(self):                # 功能不明确
def check(self):                   # 过于宽泛
```

### 注释规范

#### 模块级注释（必填）
```python
"""
Edge Impulse API客户端集成模块
提供与Edge Impulse平台的完整API交互能力
支持模型训练、部署、压缩和管理功能

作者: iMato开发团队
版本: 1.0.0
创建日期: 2026-03-01
"""
```

#### 类级注释（必填）
```python
class EdgeImpulseClient:
    """
    Edge Impulse API客户端
    提供完整的Edge Impulse平台API封装
    
    主要功能:
    - 项目管理和模型训练
    - 数据上传和作业监控  
    - 模型导出和压缩优化
    - 设备适配部署
    
    使用示例:
    >>> client = EdgeImpulseClient(api_key="key", project_id="id")
    >>> projects = client.get_projects()
    """
```

#### 方法级注释（必填）
```python
def compress_to_target_size(self, 
                          model: tf.keras.Model,
                          input_shape: Tuple[int, ...],
                          output_path: str) -> Dict[str, Any]:
    """
    压缩模型到目标大小
    
    Args:
        model: 待压缩的Keras模型
        input_shape: 输入形状，例如 (1, 40)
        output_path: 压缩后模型保存路径
        
    Returns:
        压缩结果字典，包含:
        - success: 是否成功
        - size_kb: 最终大小(KB)
        - strategy_used: 使用的压缩策略
        - quality_metrics: 质量评估指标
        
    Raises:
        Exception: 压缩失败时抛出异常
        
    Example:
        >>> compressor = TinyMLModelCompressor250KB(target_size_kb=250)
        >>> result = compressor.compress_to_target_size(model, (1,40), "model.tflite")
        >>> print(f"压缩后大小: {result['size_kb']}KB")
    """
```

#### 行内注释（关键逻辑必填）
```python
# 应用激进量化策略以达到250KB目标
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.representative_dataset = representative_dataset

# 配置INT8量化以最小化模型大小
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8

# 验证压缩后大小是否符合要求
size_kb = os.path.getsize(temp_path) / 1024
success = size_kb <= self.target_size_kb  # 250KB硬性限制
```

### 代码风格规范

#### 导入顺序
```python
# 标准库导入
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# 第三方库导入
import numpy as np
import tensorflow as tf
try:
    import tensorflow_model_optimization as tfmot
except ImportError:
    tfmot = None

# 本地模块导入
from .edge_impulse_client import EdgeImpulseClient
from .tinyml_compressor_250kb import TinyMLModelCompressor250KB
```

#### 常量定义
```python
# ✅ 正确示例
TARGET_COMPRESSION_SIZE_KB = 250  # 目标压缩大小(KB) - 项目核心要求
MAX_COMPRESSION_ATTEMPTS = 4      # 最大压缩尝试次数
DEFAULT_INPUT_SHAPE = (1, 40)     # 默认输入形状

# ❌ 错误示例
target_size = 250                 # 缺少单位说明
max_attempts = 4                  # 缺少上下文
input_shape = (1, 40)             # 缺少用途说明
```

#### 异常处理
```python
# ✅ 正确示例
def critical_operation(self):
    """关键操作 - 必须包含完整异常处理"""
    try:
        # 核心逻辑
        result = self._perform_compression()
        
        # 验证结果
        if not self._validate_result(result):
            raise ValueError("压缩结果验证失败")
            
        return result
        
    except tf.errors.InvalidArgumentError as e:
        logger.error(f"TensorFlow参数错误: {e}")
        raise CompressionError(f"模型压缩参数无效: {e}") from e
        
    except OSError as e:
        logger.error(f"文件操作失败: {e}")
        raise CompressionError(f"无法访问模型文件: {e}") from e
        
    except Exception as e:
        logger.critical(f"未预期的压缩错误: {e}")
        raise CompressionError(f"压缩过程发生未知错误: {e}") from e

# ❌ 错误示例
def bad_example(self):
    try:
        return self._compress()  # 缺少具体异常处理
    except:
        pass  # 忽略所有异常
```

## 🔧 开发流程规范

### 1. 功能开发前检查
```bash
# 1. 运行重复开发检测
python scripts/edge_impulse_250kb_backtest.py --check-duplicates

# 2. 检查现有功能
python -c "
from backend.utils.duplicate_development_detector import DuplicateDevelopmentDetector
detector = DuplicateDevelopmentDetector()
results = detector.scan_project_for_duplicates()
print(f'重复风险等级: {results[\"risk_assessment\"][\"risk_level\"]}')
"

# 3. 验证开发环境
python -c "
import tensorflow as tf
import tensorflow_model_optimization as tfmot
print('环境检查通过')
"
```

### 2. 代码实现要求
- 每个新功能必须包含完整的文档字符串
- 关键算法必须添加行内注释说明
- 复杂逻辑需要提供使用示例
- 所有外部依赖必须进行异常处理

### 3. 测试验证流程
```bash
# 1. 语法检查
python -m py_compile backend/services/*.py

# 2. 导入验证
python -c "import backend.services.edge_impulse_client; print('导入成功')"

# 3. 功能测试
python -c "
from backend.services.tinyml_compressor_250kb import TinyMLModelCompressor250KB
compressor = TinyMLModelCompressor250KB()
print('压缩器初始化成功')
"

# 4. 完整回测
python scripts/edge_impulse_250kb_backtest.py
```

### 4. 文档更新要求
- 新增功能必须同步更新技术文档
- 修改接口需要更新使用示例
- 重要变更需要记录在CHANGELOG中
- 部署相关修改需要更新部署指南

## 📊 质量门禁标准

### 代码质量指标
| 指标 | 要求 | 说明 |
|------|------|------|
| 语法正确性 | 100% | 必须通过语法检查 |
| 导入可用性 | 100% | 所有模块必须可导入 |
| 文档覆盖率 | ≥90% | 类和公有方法必须有文档 |
| 注释密度 | ≥15% | 关键逻辑必须有注释 |
| 测试通过率 | 100% | 核心功能必须通过测试 |

### 功能质量指标
| 指标 | 要求 | 说明 |
|------|------|------|
| 目标大小达成率 | 100% | 必须≤250KB |
| 压缩成功率 | ≥95% | 95%以上模型能成功压缩 |
| 质量保持率 | ≥85% | 准确率下降不超过15% |
| API调用成功率 | ≥99% | Edge Impulse API调用成功率 |

### 性能指标
| 指标 | 要求 | 说明 |
|------|------|------|
| 压缩时间 | ≤60秒 | 单个模型压缩时间 |
| 内存使用 | ≤500MB | 压缩过程峰值内存 |
| CPU使用率 | ≤80% | 系统资源占用 |
| 并发处理 | ≥5个 | 同时处理模型数量 |

## ⚠️ 禁止行为

### 代码层面
- ❌ 禁止忽略异常处理
- ❌ 禁止使用魔法数字（Magic Numbers）
- ❌ 禁止硬编码API密钥
- ❌ 禁止重复实现已有功能
- ❌ 禁止不添加注释的关键逻辑

### 流程层面
- ❌ 禁止跳过重复开发检测
- ❌ 禁止绕过质量检查
- ❌ 禁止不更新文档的代码修改
- ❌ 禁止不经过测试的生产部署

### 协作层面
- ❌ 禁止不沟通的功能重叠开发
- ❌ 禁止不遵循命名规范
- ❌ 禁止提交破坏现有功能的代码
- ❌ 禁止不处理代码审查意见

## 🔄 持续改进机制

### 定期评审
- **每周**: 代码质量抽查
- **每月**: 重复开发风险评估
- **每季度**: 技术债务梳理
- **每年**: 架构合理性复审

### 反馈收集
- 建立问题反馈渠道
- 定期收集用户使用反馈
- 跟踪性能监控数据
- 分析故障和异常日志

### 优化迭代
- 根据反馈调整实现策略
- 优化性能瓶颈
- 完善异常处理机制
- 更新最佳实践指南

---

**规范版本**: v1.0.0  
**生效日期**: 2026年3月1日  
**维护周期**: 每季度评审更新