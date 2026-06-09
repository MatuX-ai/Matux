# TensorFlow Lite量化剪枝使用说明

## 快速开始

### 1. 环境准备

确保已安装必要的依赖：
```bash
pip install tensorflow tensorflow-model-optimization numpy
```

### 2. 基本使用流程

#### 方法一：命令行工具
```bash
# 基本量化
python scripts/model_optimizer.py \
    --model-path your_model.h5 \
    --output-dir ./optimized_models \
    --quantize \
    --target-size-kb 280

# 包含剪枝
python scripts/model_optimizer.py \
    --model-path your_model.h5 \
    --output-dir ./optimized_models \
    --quantize --prune \
    --sparsity 0.5 \
    --target-size-kb 280 \
    --benchmark
```

#### 方法二：Python API
```python
from scripts.model_optimizer import ModelOptimizer

# 初始化
optimizer = ModelOptimizer('your_model.h5')

# 分析模型
optimizer.load_and_analyze_model()

# 量化处理
success = optimizer.convert_to_quantized_tflite(
    'output_model.tflite',
    target_size_kb=280
)

# 性能测试
results = optimizer.benchmark_models(target_size_kb=280)
```

### 3. 验证模型合规性

```bash
# 完整验证（需要TensorFlow）
python scripts/tflite_quantization_pruning_validator.py \
    --model-path your_model.tflite \
    --target-size-kb 280

# 模拟验证（无需TensorFlow）
python scripts/tflite_quantization_pruning_validator_mock.py \
    --model-path your_model.tflite \
    --target-size-kb 280
```

### 4. 运行回测验证

```bash
# 全面功能检查
python scripts/tflite_quantization_pruning_backtest.py
```

## 参数说明

### model_optimizer.py 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--model-path` | string | 必需 | 输入模型路径 |
| `--output-dir` | string | `./optimized_models` | 输出目录 |
| `--quantize` | flag | false | 启用量化 |
| `--prune` | flag | false | 启用剪枝 |
| `--sparsity` | float | 0.5 | 剪枝稀疏度 (0.0-0.9) |
| `--target-size-kb` | int | 280 | 目标模型大小(KB) |
| `--benchmark` | flag | false | 执行基准测试 |
| `--create-header` | flag | false | 创建C++头文件 |

## 输出文件说明

优化完成后会生成以下文件：

```
optimized_models/
├── model_float32.tflite      # 浮点模型
├── model_quantized.tflite    # 量化模型
├── model_pruned.h5          # 剪枝后的Keras模型（如启用剪枝）
├── benchmark_results.json    # 性能测试结果
└── voice_model_data.h       # C++头文件（如启用）
```

## 合规性检查

### 自动合规性验证
系统会在每次优化后自动检查：
- ✅ 模型大小 ≤ 目标限制
- ✅ 量化有效性
- ✅ 性能基准达标

### 手动验证方法
```python
# Python方式
validator = TFLiteQuantizationPruningValidator(target_size_kb=280)
is_compliant = validator.validate_model_compliance('your_model.tflite')

# 命令行方式
python scripts/tflite_quantization_pruning_validator.py \
    --model-path your_model.tflite \
    --target-size-kb 280
```

## 故障排除

### 常见问题

1. **量化失败**
   ```
   错误: Representative dataset range issue
   解决: 检查输入数据范围，确保代表数据集覆盖实际输入范围
   ```

2. **模型超限**
   ```
   警告: 模型大小超出限制
   解决: 
   - 增加剪枝稀疏度 (--sparsity 0.7)
   - 使用激进量化策略
   - 减少模型复杂度
   ```

3. **依赖缺失**
   ```
   ModuleNotFoundError: No module named 'tensorflow'
   解决: pip install tensorflow tensorflow-model-optimization
   ```

### 性能调优建议

1. **初始参数设置**
   ```bash
   --sparsity 0.3 --target-size-kb 280
   ```

2. **如不满足要求，逐步增加**
   ```bash
   --sparsity 0.5 --target-size-kb 280
   --sparsity 0.7 --target-size-kb 280
   ```

3. **最终备选方案**
   ```bash
   使用激进量化模式（自动触发）
   ```

## 最佳实践

### 开发流程推荐

```
1. 训练基础模型
   ↓
2. 初步量化测试 (--sparsity 0.3)
   ↓
3. 合规性检查
   ↓
4. 如不符合要求，调整参数
   ↓
5. 运行完整回测验证
   ↓
6. 部署生产环境
```

### 代码集成示例

```python
def optimize_model_for_deployment(model_path, target_kb=280):
    """生产环境模型优化函数"""
    
    optimizer = ModelOptimizer(model_path)
    
    if not optimizer.load_and_analyze_model():
        raise Exception("模型加载失败")
    
    # 尝试标准量化
    output_path = f"optimized_{Path(model_path).stem}.tflite"
    success = optimizer.convert_to_quantized_tflite(
        output_path, 
        target_size_kb=target_kb
    )
    
    if not success:
        raise Exception("量化失败且无法满足内存限制")
    
    # 验证合规性
    validator = TFLiteQuantizationPruningValidator(target_kb)
    if not validator.validate_model_compliance(output_path):
        raise Exception("模型不满足合规要求")
    
    # 性能基准测试
    benchmark_results = optimizer.benchmark_models(target_kb)
    
    return {
        'model_path': output_path,
        'benchmark_results': benchmark_results,
        'is_compliant': True
    }

# 使用示例
try:
    result = optimize_model_for_deployment('my_model.h5', 280)
    print(f"优化完成: {result['model_path']}")
    print(f"推理速度: {result['benchmark_results']['int8']['throughput_fps']} FPS")
except Exception as e:
    print(f"优化失败: {e}")
```

## 监控和维护

### 定期检查清单

- [ ] 模型大小仍在限制范围内
- [ ] 推理性能满足要求  
- [ ] 无功能重复实现
- [ ] 依赖库版本兼容

### 自动化脚本示例

```bash
#!/bin/bash
# model_validation_pipeline.sh

echo "开始模型验证流程..."

# 1. 运行回测
python scripts/tflite_quantization_pruning_backtest.py
if [ $? -ne 0 ]; then
    echo "回测失败，停止流程"
    exit 1
fi

# 2. 验证关键模型
for model in models/production/*.tflite; do
    python scripts/tflite_quantization_pruning_validator_mock.py \
        --model-path "$model" \
        --target-size-kb 280
done

echo "验证完成"
```

## 技术支持

如有问题，请参考：
- [完整技术文档](./TFLITE_QUANTIZATION_PRUNING_TECHNICAL_DOCUMENTATION.md)
- [回测报告](../backtest_reports/)
- [验证报告](../validation_reports/)