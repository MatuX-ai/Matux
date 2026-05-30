# iMato 开源社区版 - 部署文档索引

**版本**: v1.0  
**类型**: 开源免费版本  
**目标用户**: 学校、培训机构自行部署

---

## 📋 内容概览

本目录包含 iMato 开源社区版的完整部署文档和脚本。

### **目录结构**

```
open_source/
├── docker/                 # Docker 部署配置
│   ├── docker-compose.yml  # 一键启动脚本
│   ├── Dockerfile          # 自定义镜像构建
│   └── .env.example        # 环境变量模板
│
├── docs/                   # 详细文档
│   ├── QUICK_START.md      # 5 分钟快速开始
│   ├── INSTALLATION.md     # 完整安装指南
│   ├── CONFIGURATION.md    # 配置说明
│   └── FAQ.md              # 常见问题
│
└── scripts/                # 自动化脚本
    ├── install.sh          # Linux/Mac 安装脚本
    ├── install.bat         # Windows 安装脚本
    └── backup.sh           # 数据备份脚本
```

---

## 🚀 快速开始

### **方式一：Docker 一键部署（推荐）**

```bash
# 1. 克隆项目
git clone https://github.com/your-org/imato.git
cd imato/pricing_modes/open_source

# 2. 复制环境变量
cp docker/.env.example docker/.env

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# http://localhost:8080
```

### **方式二：手动部署**

详见 `docs/INSTALLATION.md`

---

## 🎯 功能特性

### ✅ 包含的功能
- 基础课程管理系统
- 用户管理（RBAC 权限）
- 课程内容编辑
- 学习进度追踪
- 班级管理
- 基础数据统计

### ❌ 不包含的功能
- AI 智能教师（需 Token）
- 虚拟实验室（3D 场景）
- 区块链证书认证
- 高级数据分析
- 多租户 SaaS 支持

---

## 📦 系统要求

### **最低配置**
- CPU: 2 核心
- 内存：4GB RAM
- 硬盘：20GB 可用空间
- 操作系统：Windows 10 / Ubuntu 18.04+

### **推荐配置**
- CPU: 4 核心
- 内存：8GB RAM
- 硬盘：50GB SSD
- 操作系统：Ubuntu 20.04 LTS / CentOS 8

---

## 🔧 技术栈

- **前端**: Angular 16 + TypeScript + SCSS
- **后端**: FastAPI (Python 3.11)
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **容器**: Docker 20+ / Docker Compose 2.0+

---

## 📞 技术支持

- **文档**: `/pricing_modes/open_source/docs/`
- **Issue**: GitHub Issues
- **社区**: Discord / QQ 群

---

## 📄 许可证

GPL-3.0 License

**注意**: 此版本为免费开源版本，不得用于商业盈利目的。商业用途请选择 Windows 本地版或云托管版。
