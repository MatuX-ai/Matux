import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/**
 * 桌面端窗口外壳（无边框自定义标题栏）协调服务
 *
 * 背景：frame:false 后窗口控制按钮必须由渲染进程提供。主应用的可视外壳有两种：
 * 1. 带顶部导航栏的页面（user-page-layout）：按钮内联在绿色导航栏右侧
 * 2. 无导航栏的页面（登录页 / ar-lab / exam / coming-soon ...）：按钮走浮动条
 *
 * 为了不出现两套按钮，内联外壳挂载时在这里登记，浮动条据此隐藏自己。
 */
@Injectable({ providedIn: 'root' })
export class DesktopChromeService {
  private inlineCount = 0;

  private readonly hasInlineControlsSubject = new BehaviorSubject<boolean>(false);

  /** 当前页面是否已内联渲染窗口控制按钮 */
  readonly hasInlineControls$: Observable<boolean> = this.hasInlineControlsSubject.asObservable();

  /** 内联外壳挂载（UserNavbarComponent.ngOnInit） */
  registerInlineControls(): void {
    this.inlineCount += 1;
    this.emit();
  }

  /** 内联外壳卸载（UserNavbarComponent.ngOnDestroy，路由离开导航栏页面） */
  unregisterInlineControls(): void {
    this.inlineCount = Math.max(0, this.inlineCount - 1);
    this.emit();
  }

  /** 同步读取（浮动条首帧判断，避免 Observable 首帧闪烁） */
  get hasInlineControls(): boolean {
    return this.inlineCount > 0;
  }

  private emit(): void {
    this.hasInlineControlsSubject.next(this.inlineCount > 0);
  }
}
