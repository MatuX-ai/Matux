/**
 * 无边框窗口控制按钮组（Windows 11 原生风格）
 *
 * 仅 Electron 主窗口可见：
 * - Web / PWA 环境：window.electronAPI.windowControls 不存在 → 整组不渲染
 * - macOS：使用原生红绿灯（titleBarStyle: hiddenInset）→ 整组不渲染
 *
 * 尺寸遵循 Windows 11 标题栏规范：单键 46×32px，关闭键 hover 变红 #E81123。
 */

import { isPlatformBrowser } from '@angular/common';
import { CommonModule } from '@angular/common';
import {
  Component,
  Inject,
  NgZone,
  OnDestroy,
  OnInit,
  PLATFORM_ID,
} from '@angular/core';

import { WindowControlsAPI } from '../../../core/models/electron-api.model';

@Component({
  selector: 'app-desktop-window-controls',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './desktop-window-controls.component.html',
  styleUrls: ['./desktop-window-controls.component.scss'],
})
export class DesktopWindowControlsComponent implements OnInit, OnDestroy {
  /** 是否渲染按钮组（仅 Electron + 非 macOS） */
  visible = false;

  /** 当前是否最大化，用于切换 □ / ❐ 图标 */
  isMaximized = false;

  private unsubscribeMaximize: (() => void) | null = null;

  constructor(
    @Inject(PLATFORM_ID) private platformId: object,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    const api = this.api;
    if (!isPlatformBrowser(this.platformId) || !api) {
      return;
    }
    // macOS 走原生 traffic lights，不重复渲染自定义按钮
    if (api.platform === 'darwin') {
      return;
    }

    this.visible = true;

    // 首帧状态：窗口可能以最大化启动（还原上次状态）
    void api
      .isMaximized()
      .then((res) => {
        this.zone.run(() => {
          this.isMaximized = Boolean(res?.isMaximized);
        });
      })
      .catch(() => {
        /* 主窗口尚未就绪时忽略：后续 maximize-change 事件会纠正 */
      });

    // 主进程 maximize / unmaximize / Win+↑ 都会广播，事件来自 IPC 而非 zone，
    // 必须手动回到 Angular zone，否则图标不会刷新。
    this.unsubscribeMaximize = api.onMaximizeChange((isMaximized) => {
      this.zone.run(() => {
        this.isMaximized = isMaximized;
      });
    });
  }

  ngOnDestroy(): void {
    if (this.unsubscribeMaximize) {
      this.unsubscribeMaximize();
      this.unsubscribeMaximize = null;
    }
  }

  minimize(): void {
    void this.api?.minimize();
  }

  /** 最大化 / 还原（由主进程根据当前状态自行切换） */
  toggleMaximize(): void {
    void this.api?.maximize();
  }

  close(): void {
    void this.api?.close();
  }

  private get api(): WindowControlsAPI | undefined {
    if (!isPlatformBrowser(this.platformId)) {
      return undefined;
    }
    return window.electronAPI?.windowControls;
  }
}
