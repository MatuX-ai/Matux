# Cursor项目配置

这是为iMato项目定制的Cursor开发工具配置。

## 目录结构

```
.cursor/
├── settings.json          # 工作区设置和AI助手配置
├── tasks/                 # 任务模板
│   └── templates.json     # 标准任务模板
└── snippets/              # 代码片段
    └── code-snippets.json # 常用代码片段
```

## 功能特性

### 1. 智能代码助手
- 集成OpenAI GPT-4模型
- 支持代码生成、重构和解释
- 智能命名规则和代码规范

### 2. 任务管理模板
- 功能开发任务模板
- Bug修复任务模板  
- 代码重构任务模板
- 文档编写任务模板

### 3. 代码片段库
- Angular服务模板
- FastAPI路由模板
- TypeScript接口模板
- Python类模板

## 快捷键配置

- `Ctrl+Shift+D` - 生成文档
- `Ctrl+Shift+R` - 代码重构
- `Ctrl+Shift+E` - 解释代码
- `Ctrl+Shift+B` - 查找Bug

## 推荐扩展

- Python开发工具
- TypeScript/JavaScript支持
- Angular模板支持
- TailwindCSS支持
- Prettier代码格式化

## 使用说明

1. 将此配置复制到你的Cursor工作区
2. 安装推荐的扩展
3. 根据项目需求调整配置参数
4. 使用任务模板规范化开发流程