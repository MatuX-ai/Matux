import { Component, inject } from '@angular/core';

import { routeTransition } from './animations/route.animations';
import { ErrorLoggerService } from './core/services/error-logger.service';

@Component({
  selector: 'app-root',
  standalone: false,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  animations: [routeTransition],
})
export class AppComponent {
  title = 'imatuproject';

  /**
   * 【无边框窗口 P3】是否运行在 Electron 无边框外壳中
   * 顶部全局拖拽条只在桌面端注入，避免 Web/PWA 下吞掉页面顶部 12px 的点击
   */
  readonly isDesktopShell = AppComponent.detectDesktopShell();

  private static detectDesktopShell(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }
    return Boolean(window.electronAPI?.windowControls);
  }

  /**
   * 【P2 修复】挂载全局错误日志服务
   * providedIn: 'root' 的副作用: 构造即启动监听器
   */
  private readonly errorLogger = inject(ErrorLoggerService);
}
