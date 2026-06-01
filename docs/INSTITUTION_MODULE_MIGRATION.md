# 模块解耦迁移记录

本文件记录了 MatuX 项目模块解耦至独立开源项目的完整迁移过程。

---

## 迁移一：课件管理模块 → OpenMTSciEd

### 迁移日期
2026-05

### 迁移概述
将课件管理模块从 MatuX 项目解耦到独立的 OpenMTSciEd 开源项目（开放STEM教育资源平台）。

### 目标项目
- **项目名称**: OpenMTSciEd
- **项目定位**: 开放STEM教育资源平台（课件管理）
- **技术栈**: Next.js + Neo4j
- **仓库路径**: `G:\OpenMTSciEd`
- **API 端点**: `localhost:3000/api/v1`

### 迁移内容
- 课件 CRUD 功能（24种课件类型）
- 教程管理
- 知识图谱
- 硬件项目资源管理
- 统一课程库相关功能

### MatuX 项目清理
- `material_routes.py` 保留为兼容性存根
- 前端课件管理组件已移除
- API 路由标记为「已解耦」

### 验证清单
- [x] 后端存根保留
- [x] 路由标记为已解耦
- [ ] 编译测试（待执行）
- [ ] 功能测试（待执行）

---

## 迁移二：机构管理模块 → OpenMTEduInst

## 迁移日期
2026-05-13

## 迁移概述
将机构管理模块从 MatuX 项目解耦到独立的 OpenMTEduInst 开源项目。

### 目标项目
- **项目名称**: OpenMTEduInst
- **项目定位**: STEM教育机构管理工具
- **技术栈**: FastAPI + Angular
- **仓库路径**: `G:\OpenMTEduInst`

## 迁移内容

### 已迁移到 OpenMTEduInst 的文件
**目标路径**: `G:\OpenMTEduInst\frontend\src\app\admin\institution-management`

#### 核心模块文件 (9个)
1. `institution-dashboard.component.ts` (16KB) - 机构仪表板组件
2. `institution-dashboard.service.ts` (9KB) - 机构仪表板服务
3. `institution-list.component.ts` (14.5KB) - 机构列表组件
4. `institution-list.service.ts` (3.1KB) - 机构列表服务
5. `institution-management-routing.module.ts` - 路由模块
6. `institution-management.module.ts` - 主模块
7. `mock-dashboard-data.ts` - 模拟数据
8. `organization.repository.ts` (5.3KB) - 组织数据仓库
9. `services/dashboard-statistics.service.ts` (10KB) - 仪表板统计服务

#### 核心基础设施文件 (4个)
**目标路径**: `G:\OpenMTEduInst\frontend\src\app\core`

1. `services/repository-cache.service.ts` - Repository 缓存服务
2. `utils/retry.utils.ts` - HTTP 重试工具
3. `repositories/base.repository.ts` - Repository 基础接口
4. `repositories/http-repository.base.ts` - HTTP Repository 基类

### MatuX 项目清理详情

### ✅ 已完成的操作

#### 1. 路由配置清理
- **admin-routing.module.ts**: institutions 路由已注释（第 37-42 行）
- **admin-layout.config.ts**: 
  - ROUTE_PATHS.ORGANIZATIONS 已注释（第 11 行）
  - PAGE_TITLE_MAP '/admin/institutions' 已注释（第 26 行）
  - ROUTE_TITLE_MAP 'institutions' 已注释（第 42 行）
- **routes.const.ts**: ADMIN.ORGANIZATIONS 已注释（第 55 行）

#### 2. 模块引用清理
- **core/repositories/index.ts**: OrganizationRepository 导出已注释（第 10 行）
- **admin-sidebar.config.ts**: 机构管理菜单项之前已注释（第 48-53 行）

#### 3. 文件删除
- ❌ `src/app/admin/institution-management/` - 整个目录已删除
- ❌ `src/app/core/repositories/organization.repository.ts` - 文件已删除

### 📦 备份位置
所有原始文件已备份到：`G:\iMato\temp_migration\institution-management`

## 验证清单

### MatuX 项目验证
- [x] 路由配置已清理
- [x] 模块引用已移除
- [x] 相关文件已删除
- [x] 代码已备份
- [ ] 编译测试（待执行）
- [ ] 功能测试（待执行）

### OpenMTEduInst 项目
- [x] 文件已复制
- [ ] 依赖调整（待执行）
- [ ] 独立运行测试（待执行）

## 后续工作

### OpenMTEduInst 项目需要完成
1. ✅ 核心模块文件已迁移 (9个)
2. ✅ 核心基础设施已迁移 (4个)
3. ⚠️ 调整 Angular 模块导入路径（从 iMato 路径改为本地路径）
4. ⚠️ 配置独立的环境变量（检查 environment.ts）
5. ⚠️ 设置 API 端点配置
6. ⚠️ 安装缺失的依赖包（已在 package.json 中）
7. ⚠️ 测试所有功能正常工作
8. ⚠️ 编写项目 README 文档

### MatuX 项目可选优化
1. ✅ 已创建 API 存根接口（material_routes.py, educational_institution_routes.py 等）
2. ✅ 已更新项目文档，说明机构管理功能已独立
3. ⚠️ 可在菜单中添加外部链接（可选）

---

## 三项目互联互通架构

### 学生账号互联互通

三个项目（MatuX、OpenMTSciEd、OpenMTEduInst）的学生账号通过共享 JWT 实现单点登录：

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   MatuX     │     │   OpenMTSciEd    │     │  OpenMTEduInst   │
│  (学生端)    │     │  (课件资源)       │     │  (机构管理)       │
└──────┬──────┘     └────────┬─────────┘     └────────┬─────────┘
       │                     │                        │
       └─────────────────────┼────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  共享 JWT 认证    │
                    │  学生账号互联     │
                    └─────────────────┘
```

### API 调用关系

- **MatuX → OpenMTSciEd**: 获取课件/教程/知识图谱数据
- **MatuX → OpenMTEduInst**: 获取学生所属机构/课程/排课信息
- **OpenMTSciEd → MatuX**: 学生学习进度回调
- **OpenMTEduInst → MatuX**: 学生学习记录同步

### 环境变量配置

```bash
# MatuX 环境变量
OPENMTSCIED_API_URL=http://localhost:3000/api/v1
OPENMTEDUINST_API_URL=http://localhost:8001/api/v1
```

## 注意事项

⚠️ **重要**:
- 三个项目现在完全独立，可以分别开发和维护
- 学生账号在三项目间互联互通
- 课件管理功能请在 OpenMTSciEd 中开发，不在 MatuX 中重复
- 机构管理功能请在 OpenMTEduInst 中开发，不在 MatuX 中重复
- 如需恢复已解耦功能到 MatuX，可从备份目录恢复文件
- 确保各项目的 API 端点配置正确
