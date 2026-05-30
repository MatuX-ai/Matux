# XEdu 工具链测试 Notebooks

## 📚 测试大纲

本目录包含用于验证 XEdu 各模块功能的 Jupyter Notebook 示例

### 文件结构

```
notebooks/
├── 01_mmedu_image_classification.ipynb    # MMEdu 图像分类测试
├── 02_basenn_neural_network.ipynb         # BaseNN 神经网络测试
├── 03_baseml_machine_learning.ipynb       # BaseML 机器学习测试
├── 04_xeduhub_model_zoo.ipynb             # XEduHub 模型库测试
├── 05_xedullm_chat_assistant.ipynb        # XEduLLM 对话助手测试
├── 06_easytrain_no_code.ipynb             # EasyTrain 无代码训练测试
└── 07_hardware_integration.ipynb          # 硬件集成测试
```

### 快速开始

1. 启动 OpenHydra 环境:
   ```bash
   docker-compose -f docker-compose.openhydra.yml up -d
   ```

2. 访问 JupyterHub: http://localhost:8000
   - 用户名：xedudemo
   - 密码：demo123

3. 在 notebooks/ 目录打开示例进行练习

### Notebook 列表

| 编号 | 名称 | 模块 | 预计用时 | XP 奖励 |
|------|------|------|----------|--------|
| 01 | 图像分类测试 | MMEdu | 15-20 分钟 | +300 XP |
| 02 | 神经网络测试 | BaseNN | 20-25 分钟 | +350 XP |
| 03 | 机器学习测试 | BaseML | 20-25 分钟 | +350 XP |
| 04 | 模型库测试 | XEduHub | 15-20 分钟 | +300 XP |
| 05 | 对话助手测试 | XEduLLM | 15-20 分钟 | +300 XP |
| 06 | 无代码训练 | EasyTrain | 15-20 分钟 | +400 XP |
| 07 | 硬件集成测试 | BaseDeploy | 25-30 分钟 | +450 XP |

**总学时**: 2-2.5 小时  
**总 XP**: 2450 XP

### 测试要点

- ✅ 模块导入是否正常
- ✅ API 调用是否流畅
- ✅ 模型加载速度
- ✅ 训练收敛情况
- ✅ 推理准确率
- ✅ 内存占用情况

### 预期结果

所有测试应在 5 分钟内完成，并无错误执行。
