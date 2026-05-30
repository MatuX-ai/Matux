# iMatu 前端路由结构详解

## 1. 路由总体架构

### 1.1 路由层次结构

```
App Root (/)
├── Public Routes (无需认证)
│   ├── /login
│   ├── /register
│   ├── /forgot-password
│   └── /reset-password/:token
├── Protected Routes (需要认证)
│   ├── /dashboard
│   ├── /profile
│   ├── /courses
│   ├── /learning
│   └── /admin (管理员专属)
└── Error Routes
    ├── /404
    ├── /403
    └── /500
```

### 1.2 路由守卫配置

```typescript
// 路由守卫策略
const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    canActivate: [AuthGuard], // 认证守卫
    canActivateChild: [PermissionGuard], // 权限守卫
    children: [
      {
        path: 'dashboard',
        component: DashboardComponent,
        data: { 
          title: '仪表板',
          permissions: ['DASHBOARD_VIEW']
        }
      },
      {
        path: 'admin',
        loadChildren: () => import('./admin/admin.module').then(m => m.AdminModule),
        canActivate: [RoleGuard], // 角色守卫
        data: { 
          roles: ['ADMIN', 'SUPER_ADMIN']
        }
      }
    ]
  },
  {
    path: 'auth',
    loadChildren: () => import('./auth/auth.module').then(m => m.AuthModule),
    canActivate: [GuestGuard] // 游客守卫
  }
];
```

## 2. 主要模块路由详情

### 2.1 认证模块路由 (src/app/auth/)

```typescript
// auth-routing.module.ts
const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    component: LoginComponent,
    data: { title: '用户登录' }
  },
  {
    path: 'register',
    component: RegisterComponent,
    data: { title: '用户注册' }
  },
  {
    path: 'forgot-password',
    component: ForgotPasswordComponent,
    data: { title: '忘记密码' }
  },
  {
    path: 'reset-password/:token',
    component: ResetPasswordComponent,
    data: { title: '重置密码' }
  },
  {
    path: 'verify-email/:token',
    component: VerifyEmailComponent,
    data: { title: '邮箱验证' }
  }
];
```

**组件对应关系：**
- `LoginComponent` - 登录表单，支持用户名/邮箱登录
- `RegisterComponent` - 注册表单，包含验证码功能
- `ForgotPasswordComponent` - 忘记密码，发送重置邮件
- `ResetPasswordComponent` - 密码重置页面
- `VerifyEmailComponent` - 邮箱激活验证

### 2.2 仪表板模块路由 (src/app/simple-dashboard/)

```typescript
// simple-dashboard-routing.module.ts
const routes: Routes = [
  {
    path: '',
    component: SimpleDashboardComponent,
    children: [
      {
        path: '',
        redirectTo: 'overview',
        pathMatch: 'full'
      },
      {
        path: 'overview',
        component: OverviewComponent,
        data: { title: '概览' }
      },
      {
        path: 'analytics',
        component: AnalyticsComponent,
        data: { title: '数据分析' }
      },
      {
        path: 'recommendations',
        component: RecommendationsComponent,
        data: { title: '推荐内容' }
      },
      {
        path: 'notifications',
        component: NotificationsComponent,
        data: { title: '通知中心' }
      }
    ]
  }
];
```

### 2.3 管理后台路由 (src/app/admin/)

```typescript
// admin-routing.module.ts
const routes: Routes = [
  {
    path: '',
    component: AdminLayoutComponent,
    canActivate: [AdminAuthGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      },
      {
        path: 'dashboard',
        loadChildren: () => import('./dashboard/dashboard.module').then(m => m.DashboardModule)
      },
      {
        path: 'users',
        loadChildren: () => import('./users/users.module').then(m => m.UsersModule)
      },
      {
        path: 'organizations',
        loadChildren: () => import('./organizations/organizations.module').then(m => m.OrganizationsModule)
      },
      {
        path: 'licenses',
        loadChildren: () => import('./licenses/licenses.module').then(m => m.LicensesModule)
      },
      {
        path: 'payments',
        loadChildren: () => import('./payments/payments.module').then(m => m.PaymentsModule)
      },
      {
        path: 'settings',
        loadChildren: () => import('./settings/settings.module').then(m => m.SettingsModule)
      }
    ]
  }
];
```

#### 管理员子模块详细路由：

**用户管理模块 (admin/users/)**
```typescript
const routes: Routes = [
  {
    path: '',
    component: UsersListComponent,
    data: { title: '用户列表' }
  },
  {
    path: 'create',
    component: UserCreateComponent,
    data: { title: '创建用户' }
  },
  {
    path: ':id',
    component: UserDetailsComponent,
    data: { title: '用户详情' }
  },
  {
    path: ':id/edit',
    component: UserEditComponent,
    data: { title: '编辑用户' }
  }
];
```

**组织管理模块 (admin/organizations/)**
```typescript
const routes: Routes = [
  {
    path: '',
    component: OrganizationsListComponent,
    data: { title: '组织列表' }
  },
  {
    path: 'create',
    component: OrganizationCreateComponent,
    data: { title: '创建组织' }
  },
  {
    path: ':id',
    component: OrganizationDetailsComponent,
    data: { title: '组织详情' }
  },
  {
    path: ':id/dashboard',
    component: OrganizationDashboardComponent,
    data: { title: '组织仪表板' }
  }
];
```

### 2.4 AI代码生成模块路由 (src/app/ai-code-generator/)

```typescript
const routes: Routes = [
  {
    path: '',
    component: AiCodeGeneratorComponent,
    children: [
      {
        path: '',
        redirectTo: 'editor',
        pathMatch: 'full'
      },
      {
        path: 'editor',
        component: CodeEditorComponent,
        data: { title: 'AI代码编辑器' }
      },
      {
        path: 'templates',
        component: TemplatesComponent,
        data: { title: '代码模板' }
      },
      {
        path: 'history',
        component: GenerationHistoryComponent,
        data: { title: '生成历史' }
      }
    ]
  }
];
```

## 3. 路由参数和查询参数

### 3.1 路径参数示例

```typescript
// 获取路由参数
constructor(private route: ActivatedRoute) {
  // 方式1：快照获取
  const userId = this.route.snapshot.paramMap.get('id');
  
  // 方式2：订阅获取（响应式）
  this.route.paramMap.subscribe(params => {
    const id = params.get('id');
    this.loadUserData(id);
  });
}

// 路由定义示例
{
  path: 'users/:id',
  component: UserProfileComponent
}
```

### 3.2 查询参数处理

```typescript
// 处理查询参数
constructor(private route: ActivatedRoute, private router: Router) {
  // 获取查询参数
  this.route.queryParams.subscribe(params => {
    this.searchTerm = params['search'] || '';
    this.page = +params['page'] || 1;
    this.pageSize = +params['size'] || 10;
  });
}

// 导航时传递查询参数
navigateWithQuery() {
  this.router.navigate(['/courses'], {
    queryParams: {
      category: 'programming',
      level: 'beginner',
      sort: 'popularity'
    }
  });
}
```

## 4. 路由懒加载配置

### 4.1 模块懒加载

```typescript
// 主路由配置中的懒加载
{
  path: 'admin',
  loadChildren: () => import('./admin/admin.module').then(m => m.AdminModule),
  canActivate: [AdminGuard]
}

// 管理模块内部的懒加载
{
  path: 'users',
  loadChildren: () => import('./users/users.module').then(m => m.UsersModule)
}
```

### 4.2 预加载策略

```typescript
// 自定义预加载策略
@Injectable()
export class CustomPreloadingStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<any>): Observable<any> {
    // 根据路由数据决定是否预加载
    if (route.data && route.data['preload']) {
      return load();
    }
    return of(null);
  }
}

// 在路由模块中配置
@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      preloadingStrategy: CustomPreloadingStrategy
    })
  ]
})
export class AppRoutingModule { }
```

## 5. 路由状态管理和导航

### 5.1 路由状态服务

```typescript
@Injectable({
  providedIn: 'root'
})
export class NavigationService {
  private navigationHistory: NavigationItem[] = [];
  
  constructor(
    private router: Router,
    private location: Location
  ) {
    // 监听路由变化
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        this.addToHistory(event.url);
      });
  }
  
  navigateTo(path: string, data?: any) {
    return this.router.navigate([path], { state: data });
  }
  
  goBack() {
    if (this.navigationHistory.length > 1) {
      this.location.back();
    } else {
      this.router.navigate(['/dashboard']);
    }
  }
}
```

### 5.2 路由动画配置

```typescript
// 路由动画定义
export const slideInAnimation = trigger('routeAnimations', [
  transition('* <=> *', [
    style({ position: 'relative' }),
    query(':enter, :leave', [
      style({
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%'
      })
    ], { optional: true }),
    query(':enter', [
      style({ transform: 'translateX(100%)' })
    ], { optional: true }),
    sequence([
      query(':leave', [
        animate('300ms ease-out', style({ transform: 'translateX(-100%)' }))
      ], { optional: true }),
      query(':enter', [
        animate('300ms ease-out', style({ transform: 'translateX(0)' }))
      ], { optional: true })
    ])
  ])
]);

// 在组件中使用
@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  animations: [slideInAnimation]
})
export class AppComponent {
  prepareRoute(outlet: RouterOutlet) {
    return outlet && outlet.activatedRouteData && outlet.activatedRouteData['animation'];
  }
}
```

## 6. 错误处理和备用路由

### 6.1 404页面路由

```typescript
// 全局错误路由配置
const fallbackRoutes: Routes = [
  {
    path: '404',
    component: NotFoundComponent,
    data: { title: '页面未找到' }
  },
  {
    path: '403',
    component: ForbiddenComponent,
    data: { title: '访问被拒绝' }
  },
  {
    path: '500',
    component: ServerErrorComponent,
    data: { title: '服务器错误' }
  },
  // 通配符路由，必须放在最后
  {
    path: '**',
    redirectTo: '/404'
  }
];

// 在主路由中引入
const routes: Routes = [
  // ... 其他路由
  ...fallbackRoutes
];
```

### 6.2 路由错误处理

```typescript
@Injectable()
export class RoutingErrorHandler implements ErrorHandler {
  handleError(error: any) {
    if (error instanceof NavigationError) {
      console.error('Navigation Error:', error);
      // 记录错误并跳转到错误页面
      this.router.navigate(['/500']);
    }
  }
}
```

## 7. 路由测试策略

### 7.1 单元测试示例

```typescript
describe('Routing', () => {
  let router: Router;
  let location: Location;
  let fixture: ComponentFixture<AppComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule.withRoutes(testRoutes)],
      declarations: [AppComponent, TestComponent]
    });

    router = TestBed.inject(Router);
    location = TestBed.inject(Location);
    fixture = TestBed.createComponent(AppComponent);
    router.initialNavigation();
  });

  it('should navigate to dashboard', fakeAsync(() => {
    router.navigate(['/dashboard']);
    tick();
    expect(location.path()).toBe('/dashboard');
  }));

  it('should handle route parameters', fakeAsync(() => {
    router.navigate(['/users/123']);
    tick();
    expect(location.path()).toBe('/users/123');
  }));
});
```

### 7.2 端到端测试

```typescript
describe('Navigation Flow', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should navigate through main flows', () => {
    // 测试登录流程
    cy.get('[data-cy=login-btn]').click();
    cy.url().should('include', '/auth/login');
    
    // 测试仪表板访问
    cy.login('test@example.com', 'password');
    cy.url().should('include', '/dashboard');
    
    // 测试导航菜单
    cy.get('[data-cy=nav-menu]').click();
    cy.get('[data-cy=menu-item]').contains('用户管理').click();
    cy.url().should('include', '/admin/users');
  });
});
```

## 8. 性能优化建议

### 8.1 路由预加载优化

```typescript
// 关键路由立即加载
{
  path: 'dashboard',
  loadChildren: () => import('./dashboard/dashboard.module').then(m => m.DashboardModule),
  data: { preload: true }
}

// 非关键路由延迟加载
{
  path: 'reports',
  loadChildren: () => import('./reports/reports.module').then(m => m.ReportsModule),
  data: { preload: false }
}
```

### 8.2 路由懒加载最佳实践

```typescript
// 按功能模块分割
const routes: Routes = [
  // 核心功能 - 立即加载
  {
    path: 'core',
    loadChildren: () => import('./core/core.module').then(m => m.CoreModule)
  },
  // 辅助功能 - 按需加载
  {
    path: 'tools',
    loadChildren: () => import('./tools/tools.module').then(m => m.ToolsModule)
  }
];
```

---
*路由文档版本：v1.0 | 最后更新：2026年2月*