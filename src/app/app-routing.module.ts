import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { ModuleActiveGuard } from './core/guards/module-active.guard';
import { CustomPreloadingStrategy } from './core/services/custom-preloading.strategy';
import { ROUTES } from './routes.const';

const routes: Routes = [
  // 首页重定向到用户仪表板
  {
    path: '',
    redirectTo: ROUTES.USER.DASHBOARD,
    pathMatch: 'full',
  },
  {
    path: 'ar-lab',
    loadComponent: () => import('./ar-lab/ar-lab.component').then((m) => m.ARLabComponent),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'ar_lab' },
  },
  {
    path: 'offline-mode',
    loadChildren: () =>
      import('./offline-mode/offline-mode.module').then((m) => m.OfflineModeModule),
  },
  {
    path: 'ai-edu',
    loadChildren: () =>
      import('./components/ai-edu-feature.module').then((m) => m.AIEduFeatureModule),
  },
  {
    path: 'arvr-course/:id',
    loadChildren: () =>
      import('./shared/components/arvr-course-player/arvr-course-player.module').then(
        (m) => m.ARVRCoursePlayerModule
      ),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'ar_vr' },
  },
  {
    path: 'digital-twin-lab',
    loadChildren: () =>
      import('./shared/components/digital-twin-lab/digital-twin-lab.module').then(
        (m) => m.DigitalTwinLabModule
      ),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'digital_twin' },
  },
  // 许可证管理模块已解耦至 OpenMTEduInst 项目，路由已移除
  {
    path: 'content-store',
    loadChildren: () =>
      import('./shared/components/content-store/content-store.module').then(
        (m) => m.ContentStoreModule
      ),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'content_store' },
  },
  {
    path: 'creativity-engine',
    loadChildren: () =>
      import('./creativity-engine/creativity-engine.module').then((m) => m.CreativityEngineModule),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'creativity' },
  },
  // Auth Module - 认证模块
  {
    path: 'auth',
    loadChildren: () => import('./auth/auth-routing.module').then((m) => m.AuthRoutingModule),
  },
  // User Center Module - 用户中心
  {
    path: 'user',
    loadChildren: () => import('./user/user.module').then((m) => m.UserModule),
  },
  // Management Portals Module - 管理门户已解耦至 OpenMTEduInst 项目，路由已移除

  // Exam Module - 在线测验（懒加载）
  {
    path: 'exam',
    loadChildren: () => import('./exam/exam.module').then((m) => m.ExamModule),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'exam' },
  },
  // Vircadia Module - 元宇宙教室（懒加载）
  {
    path: 'vircadia',
    loadChildren: () => import('./vircadia/vircadia.module').then((m) => m.VircadiaModule),
    canActivate: [ModuleActiveGuard],
    data: { requiredModule: 'ar_vr' },
  },
  // OpenSciEDU Module - 公共课程（懒加载）
  // 【P0 修复 #13】补齐 catalog / knowledge-graph 子路由，避免 404 落入 ** 兜底
  {
    path: 'opensciedu',
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./opensciedu/opensciedu-page.component').then((m) => m.OpenscieduPageComponent),
      },
      {
        path: 'catalog',
        loadComponent: () =>
          import('./shared/components/opensciedu-catalog/opensciedu-catalog.component').then(
            (m) => m.OpenscieduCatalogComponent
          ),
      },
      {
        path: 'knowledge-graph',
        loadComponent: () =>
          import('./shared/components/opensciedu-graph/opensciedu-graph.component').then(
            (m) => m.OpenscieduGraphComponent
          ),
      },
    ],
  },
  // 【P1 修复】占位路由: 未实现的模块指向 ComingSoon,避免 404
  {
    path: 'plugins',
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./features/plugin-store/plugin-store.component').then(
            (m) => m.PluginStoreComponent
          ),
      },
      {
        path: 'installed',
        loadComponent: () =>
          import('./shared/components/coming-soon/coming-soon.component').then(
            (m) => m.ComingSoonComponent
          ),
        data: {
          title: '已安装插件管理',
          subtitle: '即将上线',
          description:
            '已安装插件的详细管理(启用/禁用/卸载/版本)正在规划中,暂时先返回插件商店浏览。',
        },
      },
    ],
  },
  {
    path: 'store',
    loadComponent: () =>
      import('./shared/components/coming-soon/coming-soon.component').then(
        (m) => m.ComingSoonComponent
      ),
    data: {
      title: '内容商店',
      subtitle: '正在对接',
      description:
        '内容商店正在与 OpenMTSciEd 资源平台对接,正式上线后会展示可订阅的课程、模板与资源。',
    },
  },
  {
    path: 'subscription',
    loadComponent: () =>
      import('./shared/components/coming-soon/coming-soon.component').then(
        (m) => m.ComingSoonComponent
      ),
    data: {
      title: '订阅计划',
      subtitle: '暂未开放',
      description: '订阅计划目前走 Token 即用即付模式,后续会引入基础版/专业版订阅套餐。',
    },
  },
  // 【P3 修复】帮助中心与关于页统一指向 ComingSoon
  {
    path: 'help',
    loadComponent: () =>
      import('./shared/components/coming-soon/coming-soon.component').then(
        (m) => m.ComingSoonComponent
      ),
    data: {
      title: '帮助中心',
      subtitle: '正在建设',
      description: '帮助中心将提供使用指南、常见问题解答与联系支持入口。',
    },
  },
  {
    path: 'about',
    loadComponent: () =>
      import('./shared/components/coming-soon/coming-soon.component').then(
        (m) => m.ComingSoonComponent
      ),
    data: {
      title: '关于 MatuX',
      subtitle: '正在编写',
      description: '关于页面将介绍 MatuX 项目团队、技术架构与开源协议信息。',
    },
  },
  // 兜底: 任意未匹配路由 → ComingSoon 而非 404
  {
    path: '**',
    loadComponent: () =>
      import('./shared/components/coming-soon/coming-soon.component').then(
        (m) => m.ComingSoonComponent
      ),
    data: {
      title: '页面走丢了',
      subtitle: '404 Not Found',
      description: '你访问的页面不存在或已被迁移,可以从首页或课程列表继续浏览。',
    },
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, {
      preloadingStrategy: CustomPreloadingStrategy,
    }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule {}
