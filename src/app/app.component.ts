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
   * 【P2 修复】挂载全局错误日志服务
   * providedIn: 'root' 的副作用: 构造即启动监听器
   */
  private readonly errorLogger = inject(ErrorLoggerService);
}
