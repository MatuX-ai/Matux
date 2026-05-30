/**
 * 侧边栏服务
 * 用于管理侧边栏的打开/关闭状态
 */

import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class SidebarService {
  private sidebarOpenSubject = new Subject<boolean>();

  // 侧边栏状态变化事件
  sidebarOpen$ = this.sidebarOpenSubject.asObservable();

  // 当前状态
  private _isOpen = false;

  /**
   * 切换侧边栏状态
   */
  toggleSidebar(): void {
    this._isOpen = !this._isOpen;
    this.sidebarOpenSubject.next(this._isOpen);
  }

  /**
   * 打开侧边栏
   */
  openSidebar(): void {
    this._isOpen = true;
    this.sidebarOpenSubject.next(true);
  }

  /**
   * 关闭侧边栏
   */
  closeSidebar(): void {
    this._isOpen = false;
    this.sidebarOpenSubject.next(false);
  }

  /**
   * 获取当前状态
   */
  get isOpen(): boolean {
    return this._isOpen;
  }
}
