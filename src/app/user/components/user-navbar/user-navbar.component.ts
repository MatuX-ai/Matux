/* eslint-disable @typescript-eslint/explicit-function-return-type */
/**
 * 学习端全局导航栏组件（桌面端）
 *
 * 按照 PRD 第 6.5 节布局规范：
 * - 64px 高度深色导航栏
 * - Logo + 水平导航菜单
 * - 搜索、通知、用户菜单
 */

import { CommonModule } from '@angular/common';
import { isPlatformBrowser } from '@angular/common';
import { ChangeDetectorRef, Component, Inject, OnDestroy, OnInit, PLATFORM_ID } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NavigationExtras, Router, RouterModule } from '@angular/router';
import { debounceTime, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { I18nService } from '../../../core/services/i18n.service';
import { ROUTES } from '../../../routes.const';
import { UserCenterService } from '../../services/user-center.service';

// 确认对话框配置接口（用于后续集成 ConfirmDialogComponent）
// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface _ConfirmDialogConfig {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
}

interface NavItem {
  route: string;
  label: string;
  icon: string;
}

// 常量定义
const MOBILE_BREAKPOINT = 768;
const RESIZE_DEBOUNCE_MS = 100;
const DEFAULT_AVATAR = 'assets/icons/user.svg';

// 安全净化函数：防止XSS
function sanitizeUrl(url: string | null | undefined): string {
  if (!url) {
    return DEFAULT_AVATAR;
  }
  // 仅允许 http/https/data URI
  if (/^(https?:\/\/|data:image\/)/i.test(url)) {
    return url;
  }
  // 阻止 javascript: 协议和其他危险URL
  if (/^\s*(javascript:|data:|blob:)/i.test(url)) {
    return DEFAULT_AVATAR;
  }
  return DEFAULT_AVATAR;
}

// 安全净化函数：防止XSS文本注入
function sanitizeText(text: string | null | undefined): string {
  if (!text) return '';
  // 转义 HTML 特殊字符
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

@Component({
  selector: 'app-user-navbar',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatDividerModule,
    MatTooltipModule,
  ],
  templateUrl: './user-navbar.component.html',
  styleUrls: ['./user-navbar.component.scss'],
})
export class UserNavbarComponent implements OnInit, OnDestroy {
  currentUser: User | null = null;
  userType: string = '用户'; // 有默认值，避免undefined
  isMobile = false;
  unreadNotifications = 0;
  showSearch = false;

  readonly ROUTES = ROUTES;

  // 外部路由常量（避免硬编码字符串）
  readonly EXTERNAL_ROUTES = {
    AI_CODING: '/ai-edu/coding',
    AR_LAB: '/ar-lab',
    CREATIVITY: '/creativity-engine',
  } as const;

  // 按照 PRD 第 6.5 节规范的导航菜单
  // 【P2 修复】label 改为翻译键,在 ngOnInit 中根据当前语言解析
  navItems: NavItem[] = [
    { route: ROUTES.USER.DASHBOARD, label: 'userNav.home', icon: 'home' },
    { route: ROUTES.USER.COURSES, label: '课程', icon: 'school' },
    { route: this.EXTERNAL_ROUTES.AI_CODING, label: 'AI 编程', icon: 'code' },
    { route: this.EXTERNAL_ROUTES.AR_LAB, label: 'AR 实验室', icon: 'view_in_ar' },
    { route: this.EXTERNAL_ROUTES.CREATIVITY, label: '创作', icon: 'palette' },
  ];

  /**
   * 【P2】解析后的导航 label(将翻译键转为当前语言文案)
   * 模板绑定 getNavLabel(item) 时使用
   */
  getNavLabel(item: NavItem): string {
    // 兼容旧硬编码: 如果 label 不包含 "." 则直接返回
    if (!item.label.includes('.')) return item.label;
    return this.i18n.translate(item.label);
  }

  private destroy$ = new Subject<void>();
  private resizeSubject$ = new Subject<void>();
  // 保存 resize handler 引用，用于正确移除监听器
  private boundCheckScreenWidth = () => {
    this.resizeSubject$.next();
  };

  constructor(
    private userCenterService: UserCenterService,
    private authService: AuthService,
    private router: Router,
    public i18n: I18nService,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: object
  ) {}

  ngOnInit(): void {
    // 先建立 takeUntil 订阅链，确保 destroy$ 优先就绪
    this.setupSubscriptions();
    this.loadUserData();
    this.initResizeListener();
  }

  private setupSubscriptions(): void {
    // 防抖处理 resize 事件
    this.resizeSubject$
      .pipe(debounceTime(RESIZE_DEBOUNCE_MS), takeUntil(this.destroy$))
      .subscribe(() => {
        this.updateMobileState();
      });

    // 【P1 修复 #13】订阅 i18n snapshots$，让翻译包加载完后模板刷新。
    this.i18n.snapshots$
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        try {
          this.cdr.markForCheck();
        } catch {
          /* 组件已销毁 */
        }
      });
  }

  private initResizeListener(): void {
    // SSR 兼容：仅在浏览器环境添加监听器
    if (isPlatformBrowser(this.platformId)) {
      this.checkScreenWidth();
      window.addEventListener('resize', this.boundCheckScreenWidth);
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    // SSR 兼容：仅在浏览器环境移除监听器
    if (isPlatformBrowser(this.platformId)) {
      window.removeEventListener('resize', this.boundCheckScreenWidth);
    }
  }

  private loadUserData(): void {
    try {
      this.currentUser = this.userCenterService.getCurrentUser();
      this.userType = this.currentUser?.userType ?? '用户'; // 有默认值

      // 订阅前确保 takeUntil 已就绪
      this.userCenterService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe({
        next: (user) => {
          this.currentUser = user;
          this.userType = user?.userType ?? '用户';
        },
        error: (err) => {
          console.error('[UserNavbar] 订阅用户数据失败:', err);
          // 降级：保持当前用户数据，不清空
        },
      });
    } catch (error) {
      console.error('[UserNavbar] 加载用户数据失败:', error);
      // 降级：使用空用户对象
      this.currentUser = null;
      this.userType = '用户';
    }
  }

  /**
   * 获取安全净化的显示名称（防止XSS）
   */
  get safeDisplayName(): string {
    const name = this.currentUser?.username;
    return sanitizeText(name) || '用户';
  }

  /**
   * 获取用户类型翻译文本
   * 把后端返回的 userType (student/teacher/admin/enterprise) 映射到 i18n key
   */
  getUserTypeLabel(): string {
    const map: Record<string, string> = {
      student: 'userNav.userTypeStudent',
      teacher: 'userNav.userTypeTeacher',
      admin: 'userNav.userTypeAdmin',
      enterprise: 'userNav.userTypeEnterprise',
    };
    const key = map[this.userType] ?? 'userNav.userTypeDefault';
    return this.i18n.translate(key);
  }

  /**
   * 获取安全净化的头像URL
   */
  get safeAvatar(): string {
    return sanitizeUrl(this.currentUser?.avatar);
  }

  /**
   * 头像加载失败时的fallback处理
   */
  onAvatarError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = DEFAULT_AVATAR;
    img.onerror = null; // 防止死循环
  }

  navigateTo(path: string): Promise<boolean> {
    const navigationExtras: NavigationExtras = {
      replaceUrl: false,
    };
    return this.router
      .navigate([path], navigationExtras)
      .then((result) => {
        if (!result) {
          console.warn(`[UserNavbar] 导航到 ${path} 失败`);
        }
        return result;
      })
      .catch((err) => {
        console.error(`[UserNavbar] 导航到 ${path} 异常:`, err);
        return false;
      });
  }

  toggleSearch(): void {
    this.showSearch = !this.showSearch;
  }

  /**
   * 退出登录（带确认对话框，防止误触）
   * TODO: 后续应替换为 ConfirmDialogComponent 以保持UI一致性
   */
  logout(): void {
    if (isPlatformBrowser(this.platformId)) {
      // 使用浏览器原生确认对话框（可替换为 ConfirmDialogComponent）
      if (confirm('确定要退出当前登录吗？')) {
        this.performLogout();
      }
    } else {
      // SSR 环境直接登出
      this.performLogout();
    }
  }

  private performLogout(): void {
    try {
      this.userCenterService.logout();
    } catch (error) {
      console.error('[UserNavbar] 登出失败:', error);
      // 即使失败也强制跳转首页
      if (isPlatformBrowser(this.platformId)) {
        void this.router.navigate(['/']);
      }
    }
  }

  checkScreenWidth(): void {
    // 仅在浏览器环境执行
    if (isPlatformBrowser(this.platformId)) {
      this.updateMobileState();
    }
  }

  private updateMobileState(): void {
    this.isMobile = window.innerWidth <= MOBILE_BREAKPOINT;
  }
}
