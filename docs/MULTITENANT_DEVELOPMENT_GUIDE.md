# 多租户开发指南

## 🎯 概述

本指南面向在 iMatu 多租户架构下开发的工程师，提供从环境搭建到代码实现的全流程指导。

### 适用场景
- 新增管理功能模块
- 修改现有权限逻辑
- 开发跨租户复用的组件
- 调试数据隔离问题

---

## 📁 项目结构快速参考

### 完整目录结构

```
src/app/
├── platform-admin/                 # 平台行政管理端
│   ├── institutions/               # 机构审批与监管
│   │   ├── institution-list/
│   │   │   ├── institution-list.component.ts
│   │   │   ├── institution-list.component.html
│   │   │   └── institution-list.component.scss
│   │   ├── institution-detail/
│   │   └── institution-approval/
│   ├── licenses/                   # 许可证管理
│   ├── users/                      # 用户管理
│   ├── analytics/                  # 数据分析
│   └── admin-layout.component.ts   # 布局组件
│
├── tenant-management/              # 租户自主运营端
│   ├── organization-portal/        # 企业/培训机构
│   │   ├── org-finance/
│   │   ├── org-classroom/
│   │   ├── org-teacher/
│   │   ├── org-student/
│   │   └── organization-layout.component.ts
│   ├── school-portal/              # 学校
│   │   ├── classes/
│   │   ├── curriculum/
│   │   └── exam-management/
│   ├── education-bureau-portal/    # 教育局
│   │   ├── schools-overview/
│   │   └── data-analytics/
│   └── tenant-layout.component.ts
│
├── public-portal/                  # 公共服务端
│   ├── marketing/                  # 营销网站
│   │   ├── home/
│   │   ├── features/
│   │   ├── pricing/
│   │   └── about/
│   └── user-center/                # 用户中心
│       ├── dashboard/
│       ├── courses/
│       └── achievements/
│
├── shared/                         # 共享组件库 ⭐
│   ├── admin-components/           # 行政管理端复用组件
│   │   ├── data-table/
│   │   ├── stats-card/
│   │   ├── approval-workflow/
│   │   └── license-selector/
│   ├── tenant-components/          # 租户端复用组件
│   │   ├── side-nav/
│   │   ├── schedule-calendar/
│   │   ├── finance-chart/
│   │   └── student-progress/
│   ├── common-components/          # 通用业务组件
│   │   ├── dashboard-header/
│   │   ├── empty-state/
│   │   └── loading-spinner/
│   └── shared.module.ts            # 共享模块定义
│
├── core/                           # 核心服务
│   ├── guards/
│   │   ├── role.guard.ts          # ⭐ 统一角色守卫
│   │   ├── auth.guard.ts
│   │   └── org-admin.guard.ts     # (已废弃)
│   ├── services/
│   │   ├── auth.service.ts        # ⭐ 统一认证服务
│   │   ├── login-redirect.service.ts
│   │   └── http.service.ts
│   └── interceptors/
│       └── auth.interceptor.ts
│
└── app-routing.module.ts           # ⭐ 根路由配置
```

---

## 🔐 权限控制实现

### 步骤 1: 确定所需角色

首先明确你的功能需要哪些角色访问：

```typescript
// 示例需求：创建一个"机构财务分析"页面

// ✅ 正确分析：
// - 使用者：机构管理员、学校管理员
// - 数据范围：仅本机构
// - 所属门户：Tenant Management Portal

// ❌ 错误分析：
// - 认为是平台管理员功能 → 错误！
// - 放在 admin 目录下 → 错误！
```

### 步骤 2: 配置路由守卫

```typescript
// src/app/tenant-management/organization-portal/org-finance/org-finance-routing.module.ts

const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./org-finance.component').then(m => m.OrgFinanceComponent),
    canActivate: [RoleGuard],  // ⭐ 使用统一守卫
    data: {
      requiredRoles: ['org_admin', 'school_admin'],  // ⭐ 明确角色
      requiredModule: 'tenant-management'             // ⭐ 明确模块
    }
  }
];
```

### 步骤 3: 后端 API 权限验证

```python
# backend/routes/tenant/finance_routes.py

from fastapi import APIRouter, Depends
from backend.middleware.auth import require_role

router = APIRouter(prefix="/my-org/finance", tags=["Tenant Finance"])

@router.get("/stats")
async def get_financial_stats(
    current_user: User = Depends(require_role(['org_admin', 'school_admin'])),
    db: AsyncSession = Depends(get_db)
):
    # ✅ 自动验证角色，无需手动检查
    # ✅ 自动注入 current_user.organization_id
    
    stats = await calculate_org_finance(db, current_user.organization_id)
    return stats
```

---

## 🧩 组件开发最佳实践

### 场景 1: 开发可复用组件

**需求**: 创建一个数据统计卡片，Admin 和 Tenant 都要用

#### Step 1: 抽取到 shared/common-components

```bash
# 创建目录结构
src/app/shared/common-components/stats-card/
├── stats-card.component.ts
├── stats-card.component.html
├── stats-card.component.scss
└── stats-card.models.ts  # ⭐ 类型定义
```

#### Step 2: 实现通用逻辑

```typescript
// stats-card.component.ts
@Component({
  selector: 'app-stats-card',
  templateUrl: './stats-card.component.html',
  styleUrls: ['./stats-card.component.scss'],
  // ⭐ 不依赖特定主题，保持中立
})
export class StatsCardComponent implements OnInit {
  @Input() title!: string;
  @Input() value!: number | string;
  @Input() trend?: 'up' | 'down' | 'neutral';
  @Input() icon?: string;
  
  ngOnInit() {
    // ✅ 无门户相关逻辑
  }
}
```

#### Step 3: 在两个门户中使用

```typescript
// Admin Portal 中使用
import { StatsCardComponent } from '../../shared/common-components/stats-card/stats-card.component';

@NgModule({
  imports: [StatsCardComponent]
})
export class AdminDashboardModule {}

// Tenant Portal 中使用
import { StatsCardComponent } from '../../shared/common-components/stats-card/stats-card.component';

@NgModule({
  imports: [StatsCardComponent]
})
export class OrgDashboardModule {}
```

---

### 场景 2: 开发门户专属组件

**需求**: 创建"机构审批工作流"组件 (仅 Admin Portal 使用)

#### Step 1: 放在对应门户目录下

```bash
src/app/platform-admin/institutions/institution-approval/
├── institution-approval.component.ts
├── institution-approval.component.html
├── institution-approval.component.scss
└── approval-workflow.service.ts
```

#### Step 2: 仅在 Admin 模块中注册

```typescript
// src/app/platform-admin/platform-admin.module.ts

@NgModule({
  imports: [
    CommonModule,
    PlatformAdminRoutingModule,
    InstitutionApprovalComponent,  // ⭐ 仅在此注册
    // ...其他 Admin 专属组件
  ]
})
export class PlatformAdminModule {}
```

#### Step 3: **不要**在 Tenant 模块中引用

```typescript
// ❌ 错误：不要在 Tenant 模块中引用 Admin 专属组件
@NgModule({
  imports: [
    InstitutionApprovalComponent,  // ❌ 错误！
  ]
})
export class TenantManagementModule {}
```

---

## 🔄 数据隔离实现

### 前端：自动注入租户上下文

```typescript
// src/app/core/services/tenant-context.service.ts

@Injectable({ providedIn: 'root' })
export class TenantContextService {
  private currentOrgIdSubject = new BehaviorSubject<number | null>(null);
  public currentOrgId$ = this.currentOrgIdSubject.asObservable();

  constructor(private authService: AuthService) {
    // 初始化时获取当前用户的组织 ID
    const user = this.authService.getCurrentUser();
    if (user && user.organizationId) {
      this.currentOrgIdSubject.next(user.organizationId);
    }
  }

  getCurrentOrgId(): number | null {
    return this.currentOrgIdSubject.value;
  }

  setOrgId(orgId: number): void {
    this.currentOrgIdSubject.next(orgId);
  }
}
```

### 使用示例：API 调用自动带租户 ID

```typescript
// src/app/tenant-management/organization-portal/org-teacher/org-teacher.service.ts

@Injectable({ providedIn: 'root' })
export class OrgTeacherService {
  private readonly apiUrl = '/api/v1/tenant';

  constructor(
    private http: HttpClient,
    private tenantContext: TenantContextService  // ⭐ 注入上下文
  ) {}

  getTeachers(): Observable<Teacher[]> {
    const orgId = this.tenantContext.getCurrentOrgId();
    
    // ✅ URL 自动包含租户 ID
    return this.http.get<Teacher[]>(`${this.apiUrl}/my-org/${orgId}/teachers`);
  }

  addTeacher(teacher: CreateTeacherDto): Observable<Teacher> {
    const orgId = this.tenantContext.getCurrentOrgId();
    
    return this.http.post<Teacher>(
      `${this.apiUrl}/my-org/${orgId}/teachers`,
      teacher
    );
  }
}
```

---

## 🎨 主题切换实现

### 在组件中应用主题

```typescript
// src/app/platform-admin/admin-layout.component.ts

@Component({
  selector: 'app-admin-layout',
  templateUrl: './admin-layout.component.html',
  styleUrls: ['./admin.styles.scss'],
  host: { 
    'class': 'admin-theme',  // ⭐ 添加主题类
    '[attr.data-module]': "'platform-admin'"  // ⭐ 标记模块类型
  }
})
export class AdminLayoutComponent {}
```

```scss
// src/app/platform-admin/admin.styles.scss

// ✅ 使用 CSS 变量，支持主题切换
.admin-theme {
  --primary-color: #1976d2;
  --accent-color: #ff4081;
  
  .mat-toolbar {
    background: var(--primary-color);
  }
  
  .mat-button.mat-primary {
    color: var(--primary-color);
  }
}
```

---

## 🧪 测试策略

### 单元测试：模拟不同角色

```typescript
// src/app/core/guards/role.guard.spec.ts

describe('RoleGuard', () => {
  let guard: RoleGuard;
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let mockRouter: jasmine.SpyObj<Router>;

  beforeEach(() => {
    mockAuthService = jasmine.createSpyObj('AuthService', ['isAuthenticated', 'getCurrentUser']);
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);
    
    TestBed.configureTestingModule({
      providers: [
        RoleGuard,
        { provide: AuthService, useValue: mockAuthService },
        { provide: Router, useValue: mockRouter }
      ]
    });
    
    guard = TestBed.inject(RoleGuard);
  });

  it('应该允许超级管理员访问 Admin Portal', () => {
    mockAuthService.isAuthenticated.and.returnValue(true);
    mockAuthService.getCurrentUser.and.returnValue({ 
      role: 'super_admin',
      permissions: ['*']
    });
    
    const route = new ActivatedRouteSnapshot();
    route.data = { 
      requiredRoles: ['super_admin', 'admin'],
      requiredModule: 'platform-admin'
    };
    
    expect(guard.canActivate(route, {} as RouterStateSnapshot)).toBe(true);
  });

  it('应该拒绝机构管理员访问 Admin Portal', () => {
    mockAuthService.isAuthenticated.and.returnValue(true);
    mockAuthService.getCurrentUser.and.returnValue({ 
      role: 'org_admin',
      organizationId: 1
    });
    
    const route = new ActivatedRouteSnapshot();
    route.data = { 
      requiredRoles: ['super_admin', 'admin'],
      requiredModule: 'platform-admin'
    };
    
    expect(guard.canActivate(route, {} as RouterStateSnapshot)).toBe(false);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/unauthorized']);
  });
});
```

---

## 🐛 常见问题排查

### 问题 1: "无权访问"但预期应该可以访问

**排查步骤**:
1. 检查路由守卫的 `data` 配置
```typescript
// ❌ 错误：角色拼写错误
data: { requiredRoles: ['rog_admin'] }  // 应该是 'org_admin'

// ✅ 正确
data: { requiredRoles: ['org_admin'] }
```

2. 检查后端 API 依赖
```python
# ❌ 错误：缺少依赖注入
@router.get("/my-org/stats")
async def get_stats(request: Request):  # ❌ 没有验证角色
    pass

# ✅ 正确
@router.get("/my-org/stats")
async def get_stats(
    current_user: User = Depends(require_role(['org_admin']))  # ✅ 验证角色
):
    pass
```

3. 检查用户实际角色
```typescript
// 调试：打印当前用户信息
console.log('Current user:', this.authService.getCurrentUser());
// 输出：{ role: 'student', ... } → 发现不是预期的 org_admin
```

---

### 问题 2: 数据串户（看到其他机构数据）

**排查步骤**:
1. 检查后端是否自动注入租户 ID
```python
# ❌ 错误：直接查询所有数据
courses = await db.execute(select(Course))  # ❌ 没有限制 organization_id

# ✅ 正确：自动过滤
org_id = current_user.organization_id
courses = await db.execute(
    select(Course).where(Course.organization_id == org_id)
)
```

2. 检查前端 URL 参数
```typescript
// ❌ 错误：硬编码机构 ID
this.http.get(`/api/v1/tenant/my-org/1/teachers`);  // ❌ 固定为 1

// ✅ 正确：动态获取
const orgId = this.tenantContext.getCurrentOrgId();
this.http.get(`/api/v1/tenant/my-org/${orgId}/teachers`);
```

---

### 问题 3: 主题色不生效

**排查步骤**:
1. 检查组件是否添加主题类
```typescript
// ❌ 错误：忘记在 host 中添加
@Component({
  selector: 'app-admin-layout',
  templateUrl: './admin-layout.component.html'
  // ❌ 缺少 host 配置
})

// ✅ 正确
@Component({
  selector: 'app-admin-layout',
  templateUrl: './admin-layout.component.html',
  host: { 'class': 'admin-theme' }  // ✅ 添加主题类
})
```

2. 检查样式文件是否导入主题
```scss
// ❌ 错误：scope 限制
.admin-theme {
  .mat-toolbar {  // ❌ 可能被封装
    background: #1976d2;
  }
}

// ✅ 正确：使用 ::ng-deep 或全局样式
::ng-deep .admin-theme .mat-toolbar {
  background: #1976d2 !important;
}
```

---

## 📦 部署配置

### 环境变量区分门户

```typescript
// src/environments/environment.ts

export const environment = {
  production: false,
  
  // API 基础地址
  apiBaseUrl: 'http://localhost:8000',
  
  // 门户类型标识（用于日志和监控）
  portalType: 'platform-admin' | 'tenant-management' | 'public',
  
  // 功能开关
  features: {
    enableMultiTenant: true,
    enableCustomTheme: true,
    enableAuditLog: true
  }
};
```

### Docker 部署时的配置

```yaml
# docker-compose.yml

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      # ⭐ 通过环境变量指定门户类型
      - PORTAL_TYPE=platform-admin  # 或 tenant-management
      - API_BASE_URL=http://backend:8000
    ports:
      - "80:80"
```

---

## 🔗 相关资源

### 内部文档
- [`ADMIN_VS_MANAGEMENT_GUIDE.md`](./ADMIN_VS_MANAGEMENT_GUIDE.md) - Admin vs Management 使用指南
- [`PERMISSION_SYSTEM_DESIGN.md`](../documentation/shared/architecture/PERMISSION_SYSTEM_DESIGN.md) - 权限系统设计
- [`MULTI_TENANT_ARCHITECTURE.md`](../documentation/shared/architecture/MULTI_TENANT_ARCHITECTURE.md) - 多租户架构设计

### 外部资源
- [Angular 路由守卫官方文档](https://angular.io/guide/router#milestone-5-route-guards)
- [FastAPI 依赖注入系统](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [RBAC 最佳实践](https://docs.auth0.com/authorization/concepts/rbac)

---

## 📝 检查清单

### 新功能开发完成后的自检

- [ ] 路由守卫配置正确（requiredRoles, requiredModule）
- [ ] 后端 API 添加了角色验证
- [ ] 数据查询自动过滤租户 ID
- [ ] 组件主题正确应用
- [ ] 单元测试覆盖不同角色场景
- [ ] E2E 测试验证跨门户访问被拒绝
- [ ] 文档更新（README、API 文档）

---

*文档版本：v1.0  
创建日期：2026-04-03  
维护者：iMatu Development Team*
