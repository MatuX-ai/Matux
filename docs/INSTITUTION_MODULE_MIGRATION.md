# 机构管理模块解耦迁移记录

## 迁移日期
2026-05-13

## 迁移概述
将机构管理模块从 iMato 项目解耦到独立的 OpenMTEduInst 开源项目。

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

## iMato 项目清理详情

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

### iMato 项目
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

### iMato 项目可选优化
1. 如需未来集成，可创建 API stub 接口
2. 更新项目文档，说明机构管理功能已独立
3. 在 admin 菜单中添加外部链接（可选）

## 注意事项
⚠️ **重要**: 
- 两个项目现在完全独立，可以分别开发和维护
- 如需恢复机构管理功能到 iMato，可从备份目录恢复文件
- 确保 OpenMTEduInst 项目的 API 端点配置正确
