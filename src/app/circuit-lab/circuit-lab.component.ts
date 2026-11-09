import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  HostListener,
  NgZone,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { I18nService } from '../core/services/i18n.service';

/**
 * CircuitJS 产物入口（相对应用 base href 解析，兼容 Electron app:// 协议）
 */
const CIRCUITJS_ENTRY = 'assets/circuitjs/circuitjs1.html';

/**
 * CircuitJS 启动参数（依据 vendored 产物源码核验，参数名见 CircuitJS QueryParameters）：
 * - hideSidebar=false：必须保留右侧面板，否则「重置/RUN/信息栏」全部消失
 * - hideMenu=false：必须保留顶部菜单与工具栏，元件调色板（Add Resistor 等）只存在于工具栏/绘制菜单
 * - hideInfoBox=false：保留画布底部信息区，选中元件后可看到 V/I/R
 * - editable=true：允许放置、拖动与编辑元件
 * - running=true：页面打开即开始仿真
 */
const CIRCUITJS_QUERY =
  '?hideSidebar=false&hideMenu=false&hideInfoBox=false&editable=true&running=true&whiteBackground=false';

/** iframe 加载看门狗：超时仍未 load 视为失败，避免用户面对纯白区域 */
const LOAD_TIMEOUT_MS = 20000;

/**
 * 电路虚拟实验页
 *
 * Phase 1 采用 CircuitJS1（GPL-2.0）Web 产物以 iframe 方式内嵌：
 * 元件拖拽、实时仿真、电压/电流读数全部由 CircuitJS 内核算出，
 * MatuX 侧只负责页面骨架、加载/错误态与开源合规入口。
 */
@Component({
  selector: 'app-circuit-lab',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatTooltipModule],
  templateUrl: './circuit-lab.component.html',
  styleUrls: ['./circuit-lab.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CircuitLabComponent implements OnInit, OnDestroy {
  @ViewChild('frame') frameRef?: ElementRef<HTMLIFrameElement>;

  /** iframe 入口地址（相对路径，由浏览器按 base href 解析）
   *  Angular 的 RESOURCE_URL 安全上下文不接受普通字符串（NG0904），
   *  这里只是常量静态路径，无任何用户输入拼接，故显式标记为可信资源 URL。 */
  readonly src: SafeResourceUrl;

  loading = true;
  failed = false;
  showLicense = false;
  isFullscreen = false;

  private loadTimer?: ReturnType<typeof setTimeout>;
  /** 重载计数：追加为查询参数以强制 iframe 重新加载同一页面 */
  private reloadToken = 0;

  constructor(
    public i18n: I18nService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone,
    private sanitizer: DomSanitizer
  ) {
    this.src = this.sanitizer.bypassSecurityTrustResourceUrl(CIRCUITJS_ENTRY + CIRCUITJS_QUERY);
  }

  ngOnInit(): void {
    // iframe 可能在组件初始化前就已完成 load（缓存命中），先挂看门狗兜底
    this.armLoadTimeout();
  }

  ngOnDestroy(): void {
    this.clearLoadTimer();
  }

  /** iframe 触发 load：同源探测 canvas 判断 CircuitJS 是否真的跑起来了 */
  onFrameLoad(): void {
    this.clearLoadTimer();
    const el = this.frameRef?.nativeElement;
    let ok = false;
    try {
      const doc = el?.contentDocument;
      ok = !!doc && (!!doc.querySelector('canvas') || /CircuitJS/i.test(doc.title || ''));
    } catch {
      // 跨域/协议异常：视为加载失败，交由错误态提示
      ok = false;
    }
    this.loading = false;
    this.failed = !ok;
    this.zone.run(() => this.cdr.markForCheck());
  }

  /** 重置电路：重新加载 iframe（Phase 1 不持久化电路，等价于新建空白实验） */
  resetCircuit(): void {
    const el = this.frameRef?.nativeElement;
    if (!el) {
      return;
    }
    this.reloadToken += 1;
    this.loading = true;
    this.failed = false;
    this.armLoadTimeout();
    el.src = `${CIRCUITJS_ENTRY}${CIRCUITJS_QUERY}&_reload=${this.reloadToken}`;
    this.cdr.markForCheck();
  }

  /** 重新加载（错误态「重试」） */
  retry(): void {
    this.resetCircuit();
  }

  toggleFullscreen(): void {
    this.isFullscreen = !this.isFullscreen;
    this.cdr.markForCheck();
  }

  openLicense(): void {
    this.showLicense = true;
  }

  closeLicense(): void {
    this.showLicense = false;
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.showLicense) {
      this.showLicense = false;
      this.cdr.markForCheck();
      return;
    }
    if (this.isFullscreen) {
      this.isFullscreen = false;
      this.cdr.markForCheck();
    }
  }

  private armLoadTimeout(): void {
    this.clearLoadTimer();
    this.zone.runOutsideAngular(() => {
      this.loadTimer = setTimeout(() => {
        if (!this.loading) {
          return;
        }
        this.loading = false;
        this.failed = true;
        this.zone.run(() => this.cdr.markForCheck());
      }, LOAD_TIMEOUT_MS);
    });
  }

  private clearLoadTimer(): void {
    if (this.loadTimer) {
      clearTimeout(this.loadTimer);
      this.loadTimer = undefined;
    }
  }
}
