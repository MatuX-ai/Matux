# 3D 模型库开发环境本地部署指南

## 📋 部署概述

本指南详细说明如何在本地开发环境部署虚拟实验室 3D 模型库系统。

**部署路径**: `G:\iMato`  
**部署时间**: 预计 1-2 小时  
**难度等级**: 中等

---

## 🔧 环境要求

### 必需软件

| 软件 | 版本要求 | 下载地址 | 是否必需 |
|------|----------|----------|----------|
| Python | 3.9+ | https://python.org | ✅ 必需 |
| Node.js | 18+ | https://nodejs.org | ✅ 必需 |
| Blender | 3.6+ | https://blender.org | ⚠️ 转换模型时需要 |
| Git | 最新 | https://git-scm.com | ✅ 推荐 |

### 系统要求

- **操作系统**: Windows 10/11 (64 位)
- **内存**: ≥8GB (推荐 16GB)
- **硬盘空间**: ≥5GB 可用空间
- **显卡**: 支持 WebGL 2.0

---

## 📦 步骤 1: 验证基础环境

### 1.1 检查 Python 安装

```powershell
# PowerShell 命令
python --version
```

**预期输出**: `Python 3.9.x` 或更高

❌ **如果未找到 Python**:
```powershell
# 方法 1: 从 Microsoft Store 安装
winget install Python.Python.3.11

# 方法 2: 下载安装
# 访问 https://python.org/downloads/windows
# 下载并运行安装程序，勾选 "Add to PATH"
```

### 1.2 检查 Node.js 安装

```powershell
node --version
npm --version
```

**预期输出**: 
- `v18.x.x` 或更高
- `9.x.x` 或更高

❌ **如果未找到 Node.js**:
```powershell
# 下载安装
winget install OpenJS.NodeJS.LTS
```

### 1.3 检查 Blender 安装 (可选)

```powershell
blender --version
```

**预期输出**: `Blender 3.6.x`

❌ **如果未找到 Blender**:
```powershell
# 下载安装
winget install BlenderFoundation.Blender

# 或手动添加到 PATH
$env:Path += ";C:\Program Files\Blender Foundation\Blender 3.6"
```

---

## 🚀 步骤 2: 安装 Python 依赖

### 2.1 安装核心依赖

```powershell
cd G:\iMato

# 安装 requests (爬虫需要)
pip install requests

# 验证安装
python -c "import requests; print('requests version:', requests.__version__)"
```

### 2.2 安装开发工具 (推荐)

```powershell
# 代码格式化
pip install black flake8 mypy

# 测试框架
pip install pytest pytest-cov

# 类型检查
pip install types-requests
```

---

## 📦 步骤 3: 安装 Angular 前端依赖

### 3.1 安装 Three.js

```powershell
cd G:\iMato

# 安装 Three.js 和类型定义
npm install three @types/three --save

# 验证安装
npm list three
```

### 3.2 安装其他依赖 (如果项目需要)

```powershell
# WebSocket 支持 (可选)
npm install ws @types/ws --save

# RxJS (通常已包含在 Angular 中)
npm install rxjs --save
```

---

## 🗂️ 步骤 4: 配置项目结构

### 4.1 创建必要目录

```powershell
cd G:\iMato

# 模型存储目录
mkdir -p models\electronic_components
mkdir -p models\electronic_components_lod

# 数据目录
mkdir -p data\kicad_models

# 日志目录
mkdir -p logs
```

### 4.2 复制资源文件

```powershell
# 将模型索引复制到 assets 目录 (如果使用 Angular CLI)
mkdir -p src\assets\models
Copy-Item data\kicad_model_index.json src\assets\models\

# 如果使用 Webpack 或其他构建工具，相应调整路径
```

---

## 🔍 步骤 5: 验证部署

### 5.1 运行验证脚本

```powershell
cd G:\iMato

# 运行完整验证
python scripts\validate_3d_model_implementation.py
```

**预期输出**:
```
✅ Python 语法：scripts/kicad_model_scraper.py: 语法正确
...
总计：16 项检查
通过：16 项 ✅
通过率：100.0%
```

### 5.2 测试模型爬虫

```powershell
# 测试爬虫脚本 (不实际下载)
python scripts\kicad_model_scraper.py --help

# 查看帮助信息确认脚本可执行
```

### 5.3 测试转换脚本

```powershell
# 测试转换器
python scripts\model_converter.py --help
```

---

## 🎯 步骤 6: 获取模型数据

### 6.1 生成模型索引

```powershell
cd G:\iMato

# 运行爬虫生成索引
python scripts\kicad_model_scraper.py

# 检查输出
dir data\kicad_model_index.json
```

### 6.2 下载 KiCad 模型 (可选)

**方法 A: 使用 Git 克隆部分仓库**

```powershell
cd G:\iMato\data

# 只克隆需要的类别 (节省空间)
git clone --depth 1 --filter=blob:none --sparse https://github.com/KiCad/kicad-packages3D.git kicad_models_source

# 进入目录设置稀疏检出
cd kicad_models_source
git sparse-checkout init --cone
git sparse-checkout set Resistors_THT Capacitors_THT LED Package_DIP
```

**方法 B: 手动下载示例模型**

从 [KiCad-packages3D](https://github.com/KiCad/kicad-packages3D) 手动下载少量模型用于测试。

---

## 🔄 步骤 7: 转换模型格式

### 7.1 批量转换 (如果有 Blender)

```powershell
cd G:\iMato

# 转换所有模型
python scripts\model_converter.py `
  --input data\kicad_models_source `
  --output models\electronic_components `
  --max-size 2.0

# 查看日志
Get-Content logs\model_converter.log -Tail 50
```

### 7.2 生成 LOD

```powershell
# 为转换后的模型生成 LOD
python scripts\lod_generator.py `
  --input models\electronic_components `
  --output models\electronic_components_lod
```

---

## 🧪 步骤 8: 集成测试

### 8.1 启动 Angular 开发服务器

```powershell
cd G:\iMato

# 如果使用 Angular CLI
ng serve --open

# 或使用 npm scripts
npm start
```

### 8.2 测试组件加载

在浏览器访问 `http://localhost:4200`,测试:

1. ✅ 页面正常加载
2. ✅ Three.js 无报错
3. ✅ 控制台无 TypeScript 错误

### 8.3 测试模型加载

```typescript
// 在组件中测试
async testModelLoading() {
  try {
    const model = await this.modelLoader.loadComponentModel(
      'resistor_a1b2c3d4',
      'medium'
    );
    console.log('✅ 模型加载成功:', model);
  } catch (error) {
    console.error('❌ 模型加载失败:', error);
  }
}
```

---

## ⚙️ 步骤 9: 配置环境变量

### 9.1 创建环境配置文件

创建 `.env.local` 文件:

```bash
# 3D 模型库配置
MODEL_LIBRARY_PATH=G:/iMato/models/electronic_components_lod
MODEL_INDEX_URL=/assets/models/kicad_model_index.json

# Vircadia 服务器 (本地测试)
VIRCADIA_SERVER_URL=http://localhost:9000

# Blender 路径 (Windows)
BLENDER_PATH=C:/Program Files/Blender Foundation/Blender 3.6/blender.exe

# 日志级别
LOG_LEVEL=debug
```

### 9.2 在 Angular 中使用

```typescript
// environments/environment.ts
export const environment = {
  production: false,
  modelLibraryPath: '/assets/models/',
  vircadiaServerUrl: 'http://localhost:9000'
};
```

---

## 🐛 常见问题排查

### 问题 1: Python 命令不可用

**症状**: `python : 无法将"python"项识别为 cmdlet、函数、脚本文件或可运行程序的名称`

**解决方案**:
```powershell
# 方法 1: 使用 python3
python3 --version

# 方法 2: 添加 PATH
$env:Path += ";C:\Users\你的用户名\AppData\Local\Programs\Python\Python311"

# 永久添加：系统属性 → 环境变量 → Path → 编辑 → 新建
```

### 问题 2: npm 安装失败

**症状**: `npm ERR! code ENOENT`

**解决方案**:
```powershell
# 清理缓存
npm cache clean --force

# 删除 node_modules 重新安装
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### 问题 3: Blender 找不到命令

**症状**: `FileNotFoundError: 未找到 Blender 可执行文件`

**解决方案**:
```powershell
# 指定完整路径
python scripts\model_converter.py `
  --blender-path "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
```

### 问题 4: TypeScript 编译错误

**症状**: `Cannot find module 'three'`

**解决方案**:
```powershell
# 确保在项目根目录安装
cd G:\iMato
npm install three @types/three --save

# 重启 VSCode 或 IDE
```

### 问题 5: 模型转换超时

**症状**: `转换超时 (>5 分钟)`

**解决方案**:
1. 检查 STEP 文件是否损坏
2. 减少并发转换数量
3. 增加超时时间:
```python
# 修改 model_converter.py
result = subprocess.run(
    cmd,
    timeout=600  # 改为 10 分钟
)
```

---

## 📊 部署检查清单

完成以下检查确认部署成功:

- [ ] ✅ Python 3.9+ 已安装并可访问
- [ ] ✅ Node.js 18+ 已安装并可访问
- [ ] ✅ Blender 3.6+ 已安装 (可选但推荐)
- [ ] ✅ `pip install requests` 成功
- [ ] ✅ `npm install three @types/three` 成功
- [ ] ✅ 目录结构已创建
- [ ] ✅ 验证脚本通过率 100%
- [ ] ✅ 模型索引已生成
- [ ] ✅ 至少有一个测试模型可用
- [ ] ✅ Angular 应用可启动
- [ ] ✅ 无控制台错误

---

## 🎯 下一步行动

部署完成后:

1. **开发调试**
   ```powershell
   # 启动开发服务器
   ng serve
   
   # 监控日志
   Get-Content logs\*.log -Wait
   ```

2. **获取真实模型**
   ```powershell
   # 运行爬虫
   python scripts\kicad_model_scraper.py
   
   # 转换模型
   python scripts\model_converter.py
   ```

3. **功能测试**
   - 测试物理引擎
   - 测试电路仿真
   - 测试积分奖励

---

## 📞 获取帮助

如遇到问题:

1. **查看文档**
   - `docs/QUICK_START_3D_MODEL_LIBRARY.md`
   - `docs/KICAD_MODEL_SELECTION_GUIDE.md`

2. **检查日志**
   ```powershell
   Get-Content logs\*.log -Tail 100
   ```

3. **运行诊断**
   ```powershell
   python scripts\validate_3d_model_implementation.py --verbose
   ```

---

*最后更新：2026-03-03*  
*文档版本：v1.0*
