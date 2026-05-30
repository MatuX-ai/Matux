# MatuX 平台网站地图

## 🌐 前端页面结构

### 主应用路由 (src/app/)

```
/
├── /auth                   # 认证相关页面
│   ├── /auth/login         # 登录页
│   ├── /auth/register      # 注册页
│   └── /auth/forgot-password # 忘记密码
├── /dashboard              # 仪表板首页 (根据用户角色动态展示)
│   └── SimpleDashboardModule
├── /admin                  # 管理后台 (系统管理员)
│   ├── /admin/dashboard    # 管理仪表板
│   ├── /admin/users        # 用户管理
│   ├── /admin/organizations # 组织管理
│   ├── /admin/licenses     # 许可证管理
│   ├── /admin/payments     # 支付管理
│   └── /admin/auth         # 认证管理
├── /teacher                # 教师角色Dashboard (新增: 2026-03-21)
│   ├── /teacher/dashboard  # 教师仪表板
│   │   ├── teaching-progress # 跨机构教学进度
│   │   ├── student-overview # 学生学情总览
│   │   └── resource-manager # 教学资源管理
│   └── /teacher/courses    # 教师课程管理
│       ├── /teacher/courses/my-courses # 我的课程
│       └── /teacher/courses/assignments # 作业管理
├── /org-admin              # 机构管理员Dashboard (新增: 2026-03-20)
│   ├── /org-admin/dashboard # 机构仪表板
│   │   ├── org-overview     # 机构概览
│   │   ├── course-operation # 课程运营统计
│   │   ├── teacher-management # 教师管理
│   │   └── student-management # 学员管理
│   └── /org-admin/courses   # 机构课程库
│       ├── /org-admin/courses/all # 所有课程
│       └── /org-admin/courses/enrollment # 报名统计
├── /school-admin           # 学校管理员Dashboard (新增: 2026-03-21)
│   ├── /school-admin/dashboard # 学校仪表板
│   │   ├── grade-class-management # 年级班级管理
│   │   ├── school-curriculum # 校本课程管理
│   │   ├── teacher-workload  # 教师工作量统计
│   │   └── student-growth    # 学生成长档案
│   └── /school-admin/reports # 学校报表
│       ├── /school-admin/reports/attendance # 出勤统计
│       └── /school-admin/reports/achievements # 成绩报告
├── /education-bureau       # 教育局Dashboard (新增: 2026-03-21)
│   ├── /education-bureau/dashboard # 教育局仪表板
│   │   ├── regional-overview # 区域数据概览
│   │   ├── school-comparison # 学校对比分析
│   │   ├── quality-monitoring # 教学质量监控
│   │   └── resource-suggestions # AI资源调配建议
│   └── /education-bureau/reports # 区域报表
│       ├── /education-bureau/reports/export # 数据导出
│       └── /education-bureau/reports/trends # 趋势分析
└── /courses                # 统一课程库 (新增: 2026-03-21)
    ├── /courses/library    # 课程库浏览
    ├── /courses/detail/{id} # 课程详情
    ├── /courses/create     # 创建课程
    ├── /courses/edit/{id}  # 编辑课程
    └── /courses/enrollment # 课程报名管理
```

### 独立演示页面 (docs/)

| 页面名称 | 文件路径 | 描述 |
|---------|---------|------|
| 认证系统演示 | `docs/auth-demo.html` | 展示登录、注册、权限验证等功能 |
| 交互式认证演示 | `docs/auth-interactive-demo.html` | 可操作的认证流程演示 |
| 仪表板演示 | `docs/dashboard-demo.html` | 管理面板功能展示 |
| 简易仪表板 | `docs/simple-dashboard.html` | 基础仪表板界面 |
| 样式游乐场 | `docs/playground.html` | Design System 组件演示 |
| 简易游乐场 | `docs/simple-playground.html` | 精简版组件演示 |

### Flutter移动应用 (flutter_app/)

```
/lib/
├── main.dart               # 应用入口
├── screens/
│   ├── login_screen.dart   # 登录界面
│   ├── dashboard_screen.dart # 移动端仪表板
│   └── profile_screen.dart # 用户个人中心
└── widgets/
    ├── custom_button.dart  # 自定义按钮组件
    └── loading_indicator.dart # 加载指示器
```

## 🔌 后端API端点

### 认证服务 (/api/v1/auth)
```
POST   /auth/token          # 获取访问令牌
POST   /auth/register       # 用户注册
GET    /auth/me            # 获取当前用户信息
PUT    /auth/profile        # 更新个人信息
POST   /auth/password-reset # 重置密码
```

### AI服务 (/api/v1/ai)
```
POST   /ai/generate-code    # AI代码生成
POST   /ai/explain-code     # 代码解释
POST   /ai/refactor-code    # 代码重构
GET    /ai/models          # 可用AI模型列表
```

### 推荐系统 (/api/v1/recommendations)
```
GET    /recommendations/courses # 课程推荐
GET    /recommendations/content # 内容推荐
GET    /recommendations/users   # 用户推荐
POST   /recommendations/feedback # 推荐反馈
```

### 支付系统 (/api/v1/payments)
```
POST   /payments/create     # 创建支付订单
GET    /payments/{id}       # 查询支付状态
POST   /payments/refund     # 申请退款
GET    /payments/history    # 支付历史记录
```

### 订阅系统 (/api/v1/subscriptions)
```
GET    /subscriptions/plans # 订阅计划列表
POST   /subscriptions       # 创建订阅
GET    /subscriptions/me    # 我的订阅信息
PUT    /subscriptions/{id}  # 更新订阅
DELETE /subscriptions/{id}  # 取消订阅
```

### 硬件认证 (/api/v1/hardware)
```
POST   /hardware/register   # 设备注册
POST   /hardware/authenticate # 设备认证
GET    /hardware/{device_id}/status # 设备状态
PUT    /hardware/{device_id} # 更新设备信息
DELETE /hardware/{device_id} # 删除设备
```

### 许可证管理 (/api/v1/licenses)
```
GET    /licenses            # 许可证列表
POST   /licenses            # 创建许可证
GET    /licenses/{id}       # 许可证详情
PUT    /licenses/{id}       # 更新许可证
DELETE /licenses/{id}       # 删除许可证
```

### 用户许可证 (/api/v1/user-licenses)
```
GET    /user-licenses       # 用户许可证列表
POST   /user-licenses       # 分配用户许可证
GET    /user-licenses/{id}  # 用户许可证详情
PUT    /user-licenses/{id}  # 更新用户许可证
DELETE /user-licenses/{id}  # 撤销用户许可证
```

### 课程管理 (/courses)
```
GET    /courses             # 课程列表
POST   /courses             # 创建课程
GET    /courses/{id}        # 课程详情
PUT    /courses/{id}        # 更新课程
DELETE /courses/{id}        # 删除课程
```

### 租户配置 (/tenant-config)
```
GET    /tenant-config/{org_id} # 组织配置信息
PUT    /tenant-config/{org_id} # 更新组织配置
GET    /tenant-config/{org_id}/resources # 资源使用情况
```

### 教育机构管理 (/educational-institutions)
```
GET    /educational-institutions # 机构列表
POST   /educational-institutions # 创建机构
GET    /educational-institutions/{id} # 机构详情
PUT    /educational-institutions/{id} # 更新机构
DELETE /educational-institutions/{id} # 删除机构
```

### 多角色Dashboard API (新增: 2026-03-22)

#### 教师Dashboard API (/api/v1/teacher)
```
GET    /teacher/dashboard              # 教师仪表板数据
GET    /teacher/students-progress      # 学生学情总览
GET    /teacher/cross-institution-progress # 跨机构教学进度
POST   /teacher/resources/upload       # 教学资源上传
GET    /teacher/assignments            # 作业列表
POST   /teacher/assignments            # 创建作业
PUT    /teacher/assignments/{id}       # 批改作业
```

#### 机构管理员Dashboard API (/api/v1/org-admin)
```
GET    /org-admin/dashboard/{org_id}   # 机构仪表板数据
GET    /org-admin/overview/{org_id}    # 机构概览统计
GET    /org-admin/courses/{org_id}     # 机构课程运营统计
GET    /org-admin/teachers/{org_id}    # 机构教师管理
GET    /org-admin/students/{org_id}    # 机构学员管理
POST   /org-admin/courses              # 创建机构课程
PUT    /org-admin/courses/{course_id}  # 更新机构课程
DELETE /org-admin/courses/{course_id}  # 删除机构课程
```

#### 学校管理员Dashboard API (/api/v1/school-admin)
```
GET    /school-admin/dashboard/{school_id} # 学校仪表板数据
GET    /school-admin/grade-classes/{school_id} # 年级班级管理
GET    /school-admin/curriculum/{school_id} # 校本课程管理
GET    /school-admin/teacher-workload/{school_id} # 教师工作量统计
GET    /school-admin/student-growth/{school_id} # 学生成长档案
POST   /school-admin/grade-classes      # 创建年级班级
PUT    /school-admin/grade-classes/{class_id} # 更新班级信息
POST   /school-admin/courses            # 创建校本课程
```

#### 教育局Dashboard API (/api/v1/education-bureau)
```
GET    /education-bureau/dashboard/{region_id} # 教育局仪表板数据
GET    /education-bureau/regional-overview/{region_id} # 区域数据概览
GET    /education-bureau/school-comparison/{region_id} # 学校对比分析
GET    /education-bureau/quality-metrics/{region_id} # 教学质量监控
GET    /education-bureau/score-distributions/{region_id} # 成绩分布统计
POST   /education-bureau/resource-recommendations # AI资源调配建议
GET    /education-bureau/reports/export/{format} # 数据导出(Excel/PDF/CSV)
```

#### 统一课程库API (/api/v1/courses) (新增: 2026-03-21)
```
GET    /courses                        # 课程列表(支持多场景筛选)
POST   /courses                        # 创建课程
GET    /courses/{course_id}            # 课程详情
PUT    /courses/{course_id}            # 更新课程
DELETE /courses/{course_id}            # 删除课程
GET    /courses/{course_id}/chapters   # 课程章节列表
POST   /courses/{course_id}/chapters   # 添加章节
GET    /courses/{course_id}/lessons    # 课程课时列表
POST   /courses/{course_id}/lessons    # 添加课时
POST   /courses/enrollment             # 课程报名
GET    /courses/{course_id}/enrollment # 课程报名统计
POST   /courses/{course_id}/progress   # 更新学习进度
GET    /courses/{course_id}/progress   # 学习进度统计
GET    /courses/search                 # 课程搜索(支持多条件)
GET    /courses/statistics             # 课程统计分析
```

## 📊 系统监控端点

```
GET    /                    # 根路径健康检查
GET    /health              # 健康状态检查
GET    /docs                # Swagger API文档
GET    /redoc               # ReDoc API文档
GET    /metrics             # 系统指标监控
```

## 🔧 开发工具页面

| 工具名称 | 路径 | 用途 |
|---------|------|------|
| API文档 | `/docs` | Swagger UI交互式API文档 |
| API文档 | `/redoc` | ReDoc静态API文档 |
| 数据库管理 | `/admin/` | Django Admin界面 |
| 性能监控 | `/metrics` | Prometheus指标 |
| 日志查看 | `/logs` | 应用日志浏览 |

## 🎨 设计系统资源

### SCSS样式库
```
src/styles/
├── design-tokens/          # Design Tokens
│   ├── _colors.scss       # 颜色系统
│   ├── _fonts.scss        # 字体系统
│   ├── _spacing.scss      # 间距系统
│   └── _index.scss        # 入口文件
├── components/            # 组件样式
│   ├── _buttons.scss     # 按钮组件
│   ├── _forms.scss       # 表单组件
│   └── _cards.scss       # 卡片组件
├── layout.scss           # 布局系统
├── typography.scss       # 排版系统
└── main.scss            # 主样式入口
```

### TypeScript Tokens
```
src/design-tokens/
├── colors.ts             # 颜色变量
├── fonts.ts              # 字体变量
├── spacing.ts            # 间距变量
├── border-radius.ts      # 圆角变量
└── index.ts              # 导出入口
```

## 📱 移动端资源

### Android资源
```
android/
├── app/src/main/res/
│   ├── drawable/         # 图标资源
│   ├── layout/           # 布局文件
│   └── values/           # 字符串、颜色等
└── assets/              # 静态资源
```

### iOS资源
```
ios/
├── Runner/
│   ├── Assets.xcassets/  # 图像资源
│   └── Base.lproj/       # 故事板
└── Flutter/             # Flutter框架
```

## 📁 静态资源目录

```
public/
├── images/               # 图片资源
├── icons/                # 图标文件
├── fonts/                # 字体文件
└── downloads/            # 下载资源
```

## 🔗 外部链接整合

### 第三方服务
- **支付网关**: 支付宝、微信支付、银联
- **云服务**: AWS/Azure/GCP
- **CDN服务**: 阿里云CDN、腾讯云CDN
- **监控服务**: Prometheus + Grafana
- **日志服务**: ELK Stack

### 社交媒体集成
- **微信登录**: OAuth2集成
- **QQ登录**: OAuth2集成
- **微博分享**: SDK集成

## 🗺️ 导航关系图

```mermaid
graph TD
    A[首页 /] --> B[仪表板 /dashboard]
    A --> C[管理后台 /admin]
    A --> D[认证页面 /auth]
    
    B --> B1[数据分析]
    B --> B2[学习进度]
    B --> B3[推荐内容]
    
    C --> C1[用户管理]
    C --> C2[组织管理]
    C --> C3[许可证管理]
    C --> C4[支付管理]
    
    D --> D1[登录 /auth/login]
    D --> D2[注册 /auth/register]
    D --> D3[找回密码 /auth/forgot-password]
    
    C1 --> API1[用户API]
    C2 --> API2[组织API]
    C3 --> API3[许可证API]
    C4 --> API4[支付API]
    
    B1 --> AI1[AI推荐服务]
    B2 --> AI2[学习分析服务]
    B3 --> AI3[内容推荐服务]
```

---
*网站地图版本：v1.0 | 最后更新：2026年2月*
