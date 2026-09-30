/**
 * AI 助手面板开关服务
 *
 * 用于跨组件控制 AI 助手浮窗的显隐:
 * - `FloatingAiAssistantComponent` 点击 → 调用 toggle()
 * - `UserPageLayoutComponent` 订阅 panelOpen$ 控制 .ai-panel.show
 *
 * 这样 FAB 点击只需切面板，不再跳 `/ai-edu/coding` 路由
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AiAssistantToggleService {
  private readonly panelOpenSubject = new BehaviorSubject<boolean>(false);

  /** AI 助手面板显隐状态流 */
  readonly panelOpen$: Observable<boolean> = this.panelOpenSubject.asObservable();

  /** 当前是否打开 */
  isOpen(): boolean {
    return this.panelOpenSubject.value;
  }

  /** 切换 */
  toggle(): void {
    this.panelOpenSubject.next(!this.panelOpenSubject.value);
  }

  /** 强制打开 */
  open(): void {
    this.panelOpenSubject.next(true);
  }

  /** 强制关闭 */
  close(): void {
    this.panelOpenSubject.next(false);
  }
}
