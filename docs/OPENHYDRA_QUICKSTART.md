# OpenHydra + XEdu 快速开始指南

## 🚀 5 分钟快速体验

本指南将帮助您在 5 分钟内快速搭建 OpenHydra + XEdu 测试环境。

---

## 前置条件

确保您的系统已安装:

- ✅ Docker Desktop (版本 >= 4.0)
- ✅ Python 3.10+
- ✅ 至少 8GB 内存
- ✅ 至少 20GB 可用磁盘空间

---

## 步骤 1: 部署环境 (2 分钟)

### Windows 用户

打开 PowerShell 或 CMD，进入项目目录:

```bash
cd g:\iMato
.\deploy-openhydra.bat
```

### Linux/Mac用户

```bash
cd /path/to/iMato

# 1. 构建镜像
docker-compose -f docker-compose.openhydra.yml build xedu-notebook

# 2. 启动服务
docker-compose -f docker-compose.openhydra.yml up -d
```

---

## 步骤 2: 等待服务就绪 (1 分钟)

服务启动需要约 60 秒。您可以:

**方式 1: 使用脚本自动检查**

```bash
python backend\tests\test_openhydra_deployment.py
```

**方式 2: 手动查看状态**

```bash
# 查看所有服务状态
docker-compose -f docker-compose.openhydra.yml ps

# 预期输出:
# NAME                    STATUS          PORTS
# openhydra-test          Up (healthy)    0.0.0.0:8080->8080/tcp
# jupyterhub-test         Up              0.0.0.0:8000->8000/tcp
# postgres-openhydra      Up (healthy)    0.0.0.0:5433->5432/tcp
# redis-openhydra         Up              0.0.0.0:6380->6379/tcp
```

---

## 步骤 3: 访问 Web 控制台 (30 秒)

### 3.1 OpenHydra 管理控制台

浏览器访问: **http://localhost:8080**

- 账号：`admin`
- 密码：`admin123`

功能:
- 查看系统概览
- 管理用户和容器
- 监控系统资源

### 3.2 JupyterHub 学生实训平台

浏览器访问: **http://localhost:8000**

- 账号：`xedudemo`
- 密码：`demo123`

功能:
- 启动个人 AI 实验室
- 编写和运行 Python 代码
- 使用 XEdu AI 工具链

---

## 步骤 4: 运行第一个 AI 实验 (2 分钟)

### 4.1 启动 JupyterLab

1. 登录 JupyterHub (http://localhost:8000)
2. 点击 **"Start My Server"** 按钮
3. 等待 30 秒，自动进入 JupyterLab 界面

### 4.2 打开示例 Notebook

在 JupyterLab 文件浏览器中找到:

```
notebooks/01_mmedu_image_classification.ipynb
```

双击打开

### 4.3 运行代码

1. 点击第一个代码单元格
2. 按 `Shift + Enter` 执行
3. 依次向下执行所有单元格

**预期结果**:
- ✅ 成功导入 MMEdu 库
- ✅ 构建 ResNet-18 模型
- ✅ 完成 10 个 epoch 训练
- ✅ 显示训练曲线图
- ✅ 保存训练好的模型

---

## 🎉 恭喜！您已成功完成首次实验

现在您已经:
- ✅ 搭建了完整的 OpenHydra + XEdu 环境
- ✅ 启动了 AI 实训平台
- ✅ 运行了第一个图像分类实验

---

## 下一步学习路径

### 📚 推荐学习顺序

1. **MMEdu 图像分类** (已完成)
   - 文件：`01_mmedu_image_classification.ipynb`
   - 技能：卷积神经网络、图像识别

2. **BaseNN 神经网络** ⏭️
   - 文件：`02_basenn_neural_network.ipynb` (待创建)
   - 技能：多层感知机、手写数字识别

3. **BaseML 机器学习** ⏭️
   - 文件：`03_baseml_machine_learning.ipynb` (待创建)
   - 技能：传统 ML 算法、数据预处理

4. **XEduHub 模型库** ⏭️
   - 文件：`04_xeduhub_model_zoo.ipynb` (待创建)
   - 技能：SOTA 模型调用、迁移学习

5. **XEduLLM 对话助手** ⏭️
   - 文件：`05_xedullm_chat_assistant.ipynb` (待创建)
   - 技能：大语言模型、AI 问答

### 🏆 挑战任务

完成基础学习后，尝试:

1. **积分奖励挑战**
   - 完成所有基础练习：+500 XP
   - 模型准确率达到 85%: +300 XP
   - 优化训练速度提升 50%: +200 XP

2. **创新项目**
   - 使用真实数据集训练
   - 部署模型到生产环境
   - 与硬件设备集成

---

## 常用命令速查

### 服务管理

```bash
# 启动所有服务
docker-compose -f docker-compose.openhydra.yml up -d

# 停止所有服务
docker-compose -f docker-compose.openhydra.yml down

# 重启单个服务
docker-compose -f docker-compose.openhydra.yml restart jupyterhub

# 查看日志
docker-compose -f docker-compose.openhydra.yml logs -f openhydra-server

# 查看实时日志 (所有服务)
docker-compose -f docker-compose.openhydra.yml logs -f
```

### 镜像管理

```bash
# 重建镜像 (不使用缓存)
docker-compose -f docker-compose.openhydra.yml build --no-cache xedu-notebook

# 查看镜像列表
docker images | grep xedu

# 删除镜像
docker rmi xedu/notebook:latest
```

### 数据库操作

```bash
# 连接到 PostgreSQL
docker exec -it openhydra-db psql -U openhydra -d openhydra

# 查看表
\dt

# 查看用户数据
SELECT * FROM users;

# 退出
\q
```

---

## 故障排查

### 问题 1: 端口被占用

**错误信息**: `Bind for 0.0.0.0:8080 failed: port is already allocated`

**解决方案**:

```bash
# Windows: 查找并结束占用进程
netstat -ano | findstr :8080
taskkill /PID <进程 ID> /F

# Linux/Mac: 
lsof -ti:8080 | xargs kill -9
```

### 问题 2: JupyterHub 无法启动容器

**可能原因**: Docker Socket 权限问题

**解决方案**:

```bash
# 检查 Docker Socket 是否挂载
docker-compose -f docker-compose.openhydra.yml config

# 确认 /var/run/docker.sock 存在
ls -la /var/run/docker.sock
```

### 问题 3: XEdu 模块导入失败

**错误信息**: `ModuleNotFoundError: No module named 'mmedu'`

**解决方案**:

```bash
# 重新构建镜像
docker-compose -f docker-compose.openhydra.yml build --no-cache xedu-notebook

# 重新启动服务
docker-compose -f docker-compose.openhydra.yml up -d

# 在 JupyterLab 中检查已安装的包
!pip list | grep mmedu
```

### 问题 4: 内存不足

**错误信息**: `Cannot start service jupyterhub: oci runtime error`

**解决方案**:

1. Docker Desktop -> Settings -> Resources
2. 增加内存限制到 8GB 以上
3. 重启 Docker Desktop

---

## 获取帮助

### 📖 文档资源

- **完整集成方案**: [OPENHYDRA_XEDU_INTEGRATION_PLAN.md](../OPENHYDRA_XEDU_INTEGRATION_PLAN.md)
- **部署详细报告**: [OPENHYDRA_DEPLOYMENT_REPORT_O1.1.md](./OPENHYDRA_DEPLOYMENT_REPORT_O1.1.md)
- **实施进度报告**: [OPENHYDRA_XEDU_IMPLEMENTATION_STATUS_20260303.md](./OPENHYDRA_XEDU_IMPLEMENTATION_STATUS_20260303.md)

### 🔗 外部资源

- **OpenHydra 官网**: https://openhydra.org
- **XEdu 官方文档**: https://xedu.readthedocs.io
- **OpenHydra GitHub**: https://github.com/open-hydra
- **XEdu GitHub**: https://github.com/PaddlePaddle/XEdu

### 💬 社区支持

- OpenHydra 论坛：https://forum.openhydra.org
- XEdu 讨论区：https://github.com/PaddlePaddle/XEdu/discussions

---

## 总结检查清单

完成本快速指南后，请确认:

- [ ] ✅ Docker 服务全部正常运行
- [ ] ✅ 能够访问 OpenHydra 控制台 (http://localhost:8080)
- [ ] ✅ 能够访问 JupyterHub (http://localhost:8000)
- [ ] ✅ 能够启动 JupyterLab 个人服务器
- [ ] ✅ 成功运行 MMEdu 图像分类示例
- [ ] ✅ 查看训练结果图表
- [ ] ✅ 了解后续学习路径

**全部完成？🎉 您已经是 OpenHydra + XEdu 的初级用户了!**

继续学习下一个 Notebook，向 AI 专家迈进！🚀

---

**最后更新**: 2026-03-03  
**维护者**: iMato AI Assistant
