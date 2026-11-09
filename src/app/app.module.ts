import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';
import { NgModule, provideZoneChangeDetection } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ServiceWorkerModule } from '@angular/service-worker';
import { NgxEchartsModule } from 'ngx-echarts';
import { MonacoEditorModule } from 'ngx-monaco-editor-v2';

import { environment } from '../environments/environment';

import { BackendLoadingBannerComponent } from './core/components/backend-loading-banner/backend-loading-banner.component';
import { HttpAuthInterceptor } from './core/interceptors/http-auth.interceptor';
import { HttpTimeoutInterceptor } from './core/interceptors/http-timeout.interceptor';
import { AiTeacherLiveToastComponent } from './shared/components/ai-teacher-live-toast/ai-teacher-live-toast.component';
import { DesktopFloatingControlsComponent } from './shared/components/desktop-floating-controls/desktop-floating-controls.component';
import { StatusBarComponent } from './shared/components/status-bar/status-bar.component';
import { SharedModule } from './shared/shared.module';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    ReactiveFormsModule,
    // Material Modules
    MatToolbarModule,
    MatButtonModule,
    MatSidenavModule,
    MatIconModule,
    MatListModule,
    MatMenuModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatFormFieldModule,
    MatInputModule,
    MatCheckboxModule,
    MatCardModule,
    MatTooltipModule,
    SharedModule,
    AppRoutingModule,
    StatusBarComponent,
    // 【无边框窗口 P3】无导航栏页面的窗口控制按钮
    DesktopFloatingControlsComponent,
    // 【P3-B】AI 教师实时推送 toast
    AiTeacherLiveToastComponent,
    // 【启动优化 P3】学习优先模式：在主窗口顶部显示后端后台启动横幅
    BackendLoadingBannerComponent,
    // 【P2 修复】启用 ServiceWorker (PWA),仅生产环境生效
    ServiceWorkerModule.register('ngsw-worker.js', {
      enabled: environment.production,
      // 应用稳定后或 30 秒内注册
      registrationStrategy: 'registerWhenStable:30000',
    }),
    MonacoEditorModule.forRoot(),
    // 【P1-BUG01 修复】GrowthTrajectoryComponent 使用 NgxEchartsModule 渲染雷达图，
    // 必须在 AppModule 根模块注册 NGX_ECHARTS_CONFIG provider,否则组件构造期
    // 会触发 NG0201 NullInjectorError,导致 6s setTimeout 兑底不生效。
    NgxEchartsModule.forRoot({
      echarts: () => import('echarts'),
    }),
  ],
  providers: [
    // 【CD 止血】Angular 21 默认注入 zoneless CD，zone 时代写法（subscribe 回调直接改字段）
    // 不会触发变更检测。此处显式恢复 zone 驱动 CD，后续再按 Issue G 的四阶段迁移回 zoneless。
    provideZoneChangeDetection({ eventCoalescing: true, runCoalescing: true }),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpAuthInterceptor,
      multi: true,
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: HttpTimeoutInterceptor,
      multi: true,
    },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
