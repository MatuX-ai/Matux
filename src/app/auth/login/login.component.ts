import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { environment } from '../../../environments/environment';
import { LoginRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { I18nService } from '../../core/services/i18n.service';
import { ROUTES } from '../../routes.const';

// 测试账号配置（仅用于演示，敏感信息不应在前端硬编码）
interface TestAccount {
  username: string;
  password: string;
  role: string;
  description: string;
  icon: string;
}

const TEST_ACCOUNTS: TestAccount[] = [
  {
    username: 'test_admin',
    password: 'TestAdmin123!',
    role: '管理员',
    description: '完整管理权限',
    icon: 'admin_panel_settings',
  },
  {
    username: 'test_teacher',
    password: 'TestTeacher123!',
    role: '教师',
    description: '教学管理权限',
    icon: 'school',
  },
  {
    username: 'test_student',
    password: 'TestStudent123!',
    role: '学生',
    description: '学习体验权限',
    icon: 'person',
  },
];

// 登录阶段定义（与 splash 启动阶段对齐：每个阶段有进度 + XP 奖励）
interface LoginPhase {
  key: string;
  text: string;
  type: 'info' | 'success' | 'warn' | 'error';
  progress: number;
  exp: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  label?: string;
}

const LOGIN_PHASES: Record<string, LoginPhase> = {
  validating: {
    key: 'validating',
    text: 'Validating credentials...',
    type: 'info',
    progress: 20,
    exp: 5,
    rarity: 'common',
  },
  contacting: {
    key: 'contacting',
    text: 'Contacting auth server...',
    type: 'info',
    progress: 40,
    exp: 5,
    rarity: 'common',
  },
  verifying: {
    key: 'verifying',
    text: 'Verifying token signature...',
    type: 'info',
    progress: 60,
    exp: 10,
    rarity: 'common',
  },
  loading: {
    key: 'loading',
    text: 'Loading user profile...',
    type: 'info',
    progress: 80,
    exp: 25,
    rarity: 'rare',
    label: '加载画像',
  },
  ready: {
    key: 'ready',
    text: 'Welcome to MatuX!',
    type: 'success',
    progress: 100,
    exp: 100,
    rarity: 'legendary',
    label: '登录完成',
  },
  failed: {
    key: 'failed',
    text: 'Authentication failed',
    type: 'error',
    progress: 100,
    exp: 0,
    rarity: 'common',
  },
};

interface TerminalLine {
  text: string;
  type: 'info' | 'success' | 'warn' | 'error';
  typing: boolean;
  complete: boolean;
  timestamp: number;
}

interface XpToast {
  id: number;
  exp: number;
  label?: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  left: number;
  top: number;
}

interface ParticleConfig {
  top: number;
  duration: number;
  delay: number;
  cyan: boolean;
}

interface ConfettiConfig {
  id: number;
  dx: number;
  dy: number;
  rot: string;
  color: string;
  size: number;
  round: boolean;
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCheckboxModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent implements OnInit, OnDestroy {
  credentials: LoginRequest = { email: '', password: '' };
  rememberMe = true;
  loading = false;
  errorMessage = '';
  hidePassword = true;

  readonly isProduction = environment.production;
  readonly ROUTES = ROUTES;

  // 游戏化状态
  loaded = false;
  loginPhase = '';
  loginButtonText = '登录';
  progressPercent = 0;
  progressText = '0%';
  milestone = false;
  totalXP = 0;
  streakDays = 0;
  showCelebrate = false;

  terminalLines: TerminalLine[] = [];
  xpToasts: XpToast[] = [];
  particles: ParticleConfig[] = [];
  confettis: ConfettiConfig[] = [];

  private xpToastSeq = 0;
  private confettiSeq = 0;
  private timers: ReturnType<typeof setTimeout>[] = [];
  private readonly prefersReducedMotion =
    typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  constructor(
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    public i18n: I18nService,
    private cdr: ChangeDetectorRef
  ) {
    this.rememberMe = this.authService.isRememberMe();

    const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
    if (returnUrl && returnUrl !== '/auth/login') {
      try {
        sessionStorage.setItem('pre_login_return_url', returnUrl);
      } catch {
        /* sessionStorage 不可用 */
      }
    }
  }

  ngOnInit(): void {
    // 触发入场动画（与 splash fadeIn 一致）
    setTimeout(() => (this.loaded = true), 50);

    // 生成背景粒子（参考 splash spawnParticles，最多 16 个，性能友好）
    this.particles = Array.from({ length: 16 }, () => ({
      top: 5 + Math.random() * 90,
      duration: 6 + Math.random() * 6,
      delay: Math.random() * 8,
      cyan: Math.random() > 0.7,
    }));

    // 计算连续登录天数（localStorage）
    this.streakDays = this.computeStreakDays();

    // 根据邮箱是否填充，动态调整按钮文案
    this.updateButtonText();

    // 【P1 修复 #13】主动订阅 i18n snapshots$，确保 HTTP 加载完翻译包后
    //   模板中的 i18n.translate(...) 调用能拿到新文案并刷新视图。
    //   仅依赖 ApplicationRef.tick() 在某些场景下（特别是路由重用 / 组件被冻结）
    //   不触发该组件的变更检测，这里补一道 markForCheck() 作为保险。
    this.i18n.snapshots$.subscribe(() => {
      try {
        this.cdr.markForCheck();
      } catch {
        /* 组件已销毁 */
      }
    });
  }

  ngOnDestroy(): void {
    this.timers.forEach((t) => clearTimeout(t));
  }

  // ============ trackBy 函数 ============
  trackParticle(_i: number, p: ParticleConfig): number {
    return p.top * 1000 + p.delay;
  }
  trackLine(_i: number, line: TerminalLine): number {
    return line.timestamp;
  }
  trackXp(_i: number, t: XpToast): number {
    return t.id;
  }
  trackConfetti(_i: number, c: ConfettiConfig): number {
    return c.id;
  }

  // ============ 按钮文案动态化 ============
  updateButtonText(): void {
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.credentials.email);
    const passOk = (this.credentials.password?.length ?? 0) >= 8;
    if (!emailOk && !passOk) this.loginButtonText = '登录';
    else if (emailOk && !passOk) this.loginButtonText = '继续 → 密码';
    else if (!emailOk && passOk) this.loginButtonText = '继续 → 邮箱';
    else this.loginButtonText = '🚀 启动引擎';
  }

  // ============ 阶段状态机 ============
  private pushLine(text: string, type: TerminalLine['type'] = 'info'): void {
    const line: TerminalLine = {
      text,
      type,
      typing: true,
      complete: false,
      timestamp: Date.now() + Math.random(),
    };
    this.terminalLines = [...this.terminalLines, line];
    // 限制最多 6 行，超出则清理最早的
    if (this.terminalLines.length > 6) {
      this.terminalLines = this.terminalLines.slice(-6);
    }
    // 完成打字（这里用 CSS animation 模拟逐字效果，简化模型：立即标记 complete）
    const t = setTimeout(() => {
      line.typing = false;
      line.complete = true;
      this.terminalLines = [...this.terminalLines];
    }, 350);
    this.timers.push(t);
  }

  private setProgress(percent: number): void {
    this.progressPercent = percent;
    this.progressText = `${percent}%`;
    // 25/50/75 触发金色里程碑脉冲
    const milestones = [25, 50, 75, 100];
    if (milestones.includes(percent)) {
      this.milestone = true;
      const t = setTimeout(() => (this.milestone = false), 1200);
      this.timers.push(t);
    }
  }

  private triggerXP(exp: number, rarity: XpToast['rarity'], label?: string): void {
    if (exp <= 0) return;
    const toast: XpToast = {
      id: ++this.xpToastSeq,
      exp,
      label,
      rarity,
      left: 60 + Math.random() * 10,
      top: 50 + Math.random() * 6,
    };
    this.xpToasts = [...this.xpToasts, toast];
    this.totalXP += exp;

    const t = setTimeout(() => {
      this.xpToasts = this.xpToasts.filter((x) => x.id !== toast.id);
    }, 1400);
    this.timers.push(t);
  }

  private async runLoginSequence(doLogin: () => Promise<void> | void): Promise<void> {
    this.loading = true;
    this.errorMessage = '';
    this.loginPhase = 'validating';
    this.terminalLines = [];
    this.totalXP = 0;

    const runPhase = (phase: LoginPhase) => {
      this.loginPhase = phase.key;
      this.pushLine(phase.text, phase.type);
      this.setProgress(phase.progress);
      this.triggerXP(phase.exp, phase.rarity, phase.label);
    };

    runPhase(LOGIN_PHASES['validating']);
    await this.delay(this.prefersReducedMotion ? 60 : 250);
    runPhase(LOGIN_PHASES['contacting']);

    try {
      await this.delay(this.prefersReducedMotion ? 80 : 350);
      runPhase(LOGIN_PHASES['verifying']);
      await this.delay(this.prefersReducedMotion ? 100 : 350);
      runPhase(LOGIN_PHASES['loading']);
      await this.delay(this.prefersReducedMotion ? 80 : 250);

      // 30 秒兜底：防止后端挂起导致 loading 卡死
      await Promise.race([
        doLogin(),
        this.delay(30000).then(() => {
          throw new Error('登录请求超时，请检查网络后重试');
        }),
      ]);

      runPhase(LOGIN_PHASES['ready']);
      this.celebrate();
      await this.delay(900);
      this.navigateAfterLogin();
    } catch (err) {
      const msg = (err as { message?: string })?.message ?? '登录失败，请检查邮箱和密码';
      this.errorMessage = msg;
      this.pushLine(`ERROR: ${msg}`, 'error');
      this.setProgress(0);
      this.progressPercent = 0;
      this.progressText = '0%';
      this.loading = false;
    }
  }

  private celebrate(): void {
    if (this.prefersReducedMotion) return;
    this.showCelebrate = true;
    const colors = ['#f59e0b', '#fde047', '#22c55e', '#3b82f6', '#a855f7', '#ec4899'];
    const total = this.prefersReducedMotion ? 12 : 40;
    this.confettis = Array.from({ length: total }, (_, i) => {
      const angle = (i / total) * Math.PI * 2 + Math.random() * 0.5;
      const dist = 220 + Math.random() * 280;
      return {
        id: ++this.confettiSeq,
        dx: Math.cos(angle) * dist,
        dy: Math.sin(angle) * dist,
        rot: `${Math.random() * 720 - 360}deg`,
        color: colors[i % colors.length],
        size: 4 + Math.random() * 8,
        round: Math.random() > 0.5,
      };
    });
    const t = setTimeout(() => {
      this.showCelebrate = false;
      this.confettis = [];
    }, 1500);
    this.timers.push(t);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((r) => {
      const t = setTimeout(r, ms);
      this.timers.push(t);
    });
  }

  private computeStreakDays(): number {
    try {
      const last = localStorage.getItem('matux-last-login');
      const today = new Date().toDateString();
      const stored = parseInt(localStorage.getItem('matux-login-streak') || '0', 10);
      if (last === today) return stored;
      const yesterday = new Date(Date.now() - 86400000).toDateString();
      let next: number;
      if (last === yesterday) next = stored + 1;
      else if (last) next = 1;
      else next = 1;
      // 注意：仅在登录成功时再写入，避免打开页面就重置
      // 这里只在显示时计算，真实写入在 navigateAfterLogin 后
      this._pendingStreakWrite = { today, next };
      return next;
    } catch {
      return 0;
    }
  }
  private _pendingStreakWrite?: { today: string; next: number };

  // ============ 路由跳转 ============
  private navigateAfterLogin(): void {
    // 写入连续登录天数
    try {
      if (this._pendingStreakWrite) {
        localStorage.setItem('matux-last-login', this._pendingStreakWrite.today);
        localStorage.setItem('matux-login-streak', String(this._pendingStreakWrite.next));
      }
    } catch {
      /* ignore */
    }

    const sessionReturnUrl = sessionStorage.getItem('pre_login_return_url');
    if (sessionReturnUrl) {
      sessionStorage.removeItem('pre_login_return_url');
      void this.router.navigateByUrl(sessionReturnUrl);
    } else {
      void this.router.navigate([ROUTES.USER.DASHBOARD]);
    }
  }

  // ============ 登录入口 ============
  async onLogin(): Promise<void> {
    if (this.loading) return;
    await this.runLoginSequence(async () => {
      await new Promise<void>((resolve, reject) => {
        this.authService.setRememberMe(this.rememberMe);
        this.authService.signIn(this.credentials).subscribe({
          next: () => resolve(),
          error: (err: unknown) => reject(err),
        });
      });
    });
  }

  // ============ OAuth 入口（保持原有逻辑） ============
  loginWithQQ(): void {
    this.authService.signInWithQQ();
  }
  loginWithWechat(): void {
    this.authService.signInWithWeChat();
  }
  loginWithGoogle(): void {
    this.authService.signInWithGoogle();
  }
  loginWithGithub(): void {
    this.authService.signInWithGitHub();
  }

  /**
   * 一键登录：使用测试学生账号快速登录（仅开发/演示环境）
   */
  loginAsTestUser(): void {
    if (environment.production) {
      this.errorMessage = '演示功能在生产环境不可用';
      return;
    }
    if (this.loading) return;

    // 测试登录额外奖励 +50 EXP（按钮已标注 "+50 EXP"）
    void this.runLoginSequence(async () => {
      const studentAccount = TEST_ACCOUNTS.find((a) => a.role === '学生') ?? TEST_ACCOUNTS[2];
      this.triggerXP(50, 'rare', '一键测试登录');
      await new Promise<void>((resolve, reject) => {
        this.authService.setRememberMe(true);
        this.authService
          .signIn({ email: studentAccount.username, password: studentAccount.password })
          .subscribe({ next: () => resolve(), error: (e) => reject(e) });
      });
    });
  }
}
