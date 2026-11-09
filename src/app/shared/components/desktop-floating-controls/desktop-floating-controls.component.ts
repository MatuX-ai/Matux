/**
 * 无导航栏页面的浮动窗口控制条
 *
 * 登录页 / ar-lab / exam / coming-soon 等页面没有 user-page-layout 的绿色导航栏，
 * 这些页面同样需要最小化 / 最大化 / 关闭入口。这里渲染一条贴顶右对齐的深色浮动条，
 * 保证白色描边图标在浅色页面上也清晰可见。
 *
 * 导航栏页面（已内联按钮）会通过 DesktopChromeService 登记，此时本组件自动隐藏，
 * 避免出现两套窗口控制按钮。
 */

import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Component, Inject, OnDestroy, OnInit, PLATFORM_ID } from '@angular/core';
import { Subscription } from 'rxjs';

import { DesktopChromeService } from '../../../core/services/desktop-chrome.service';
import { DesktopWindowControlsComponent } from '../desktop-window-controls/desktop-window-controls.component';

@Component({
  selector: 'app-desktop-floating-controls',
  standalone: true,
  imports: [CommonModule, DesktopWindowControlsComponent],
  templateUrl: './desktop-floating-controls.component.html',
  styleUrls: ['./desktop-floating-controls.component.scss'],
})
export class DesktopFloatingControlsComponent implements OnInit, OnDestroy {
  /** 是否渲染浮动条（仅 Electron 非 macOS，且当前页面没有内联按钮） */
  visible = false;

  private subscription: Subscription | null = null;

  constructor(
    @Inject(PLATFORM_ID) private platformId: object,
    private chrome: DesktopChromeService
  ) {}

  ngOnInit(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    const api = window.electronAPI?.windowControls;
    if (!api || api.platform === 'darwin') {
      return;
    }

    // 首帧用同步值，避免「先显示浮动条再隐藏」的闪烁
    this.visible = !this.chrome.hasInlineControls;
    this.subscription = this.chrome.hasInlineControls$.subscribe((hasInline) => {
      this.visible = !hasInline;
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    this.subscription = null;
  }
}
