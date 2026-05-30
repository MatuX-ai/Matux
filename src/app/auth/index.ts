/**
 * 认证系统入口文件
 * 导出所有认证相关的模块和服务
 */

// 核心模型
export * from '@core/models/auth.models';

// 核心服务
export * from '@core/services/auth-http-client';
export * from '@core/services/auth-main-service';
export { AuthStateChangeListener, authStateManager } from '@core/services/auth-state-manager';

// 认证服务实例
import { AuthService, getDefaultAuthService } from '@core/services/auth-main-service';

/**
 * 获取认证服务实例
 * @returns AuthService实例
 */
export function getAuthService(): AuthService {
  return getDefaultAuthService();
}

/**
 * 认证系统初始化配置
 */
export interface AuthInitOptions {
  apiUrl?: string;
  timeout?: number;
  autoRefreshThreshold?: number;
  githubClientId?: string;
  googleClientId?: string;
}

/**
 * 初始化认证系统
 * @param options 初始化选项
 */
export function initAuth(options: AuthInitOptions = {}): AuthService {
  const authService = getDefaultAuthService();
  authService.updateConfig(options);
  return authService;
}

/**
 * 认证状态钩子（适用于 React/Vue 等框架）
 */
export function useAuth(): {
  user: ReturnType<AuthService['getCurrentUser']>;
  isAuthenticated: boolean;
  accessToken: string | null;
  signIn: AuthService['signIn'];
  signUp: AuthService['signUp'];
  logout: AuthService['logout'];
  signInWithGitHub: AuthService['signInWithGitHub'];
  signInWithGoogle: AuthService['signInWithGoogle'];
  signInWithWeChat: AuthService['signInWithWeChat'];
  signInWithQQ: AuthService['signInWithQQ'];
  updateUser: AuthService['updateUser'];
  changePassword: AuthService['changePassword'];
  hasPermission: AuthService['hasPermission'];
} {
  const authService = getAuthService();

  return {
    // 当前用户
    user: authService.getCurrentUser(),
    // 是否已认证
    isAuthenticated: authService.isAuthenticated(),
    // 访问令牌
    accessToken: authService.getAccessToken(),

    // 认证方法
    signIn: authService.signIn.bind(authService),
    signUp: authService.signUp.bind(authService),
    logout: authService.logout.bind(authService),

    // OAuth 方法
    signInWithGitHub: authService.signInWithGitHub.bind(authService),
    signInWithGoogle: authService.signInWithGoogle.bind(authService),
    signInWithWeChat: authService.signInWithWeChat.bind(authService),
    signInWithQQ: authService.signInWithQQ.bind(authService),

    // 工具方法
    updateUser: authService.updateUser.bind(authService),
    changePassword: authService.changePassword.bind(authService),
    hasPermission: authService.hasPermission.bind(authService),
  };
}

/**
 * 认证守卫中间件
 * @param requiredPermissions 所需权限
 * @returns 是否允许访问
 */
export async function authGuard(requiredPermissions: string[] = []): Promise<boolean> {
  const authService = getAuthService();

  // 检查是否已认证
  if (!authService.isAuthenticated()) {
    return false;
  }

  // 如果不需要特定权限，直接通过
  if (requiredPermissions.length === 0) {
    return true;
  }

  // 检查权限
  try {
    for (const permission of requiredPermissions) {
      const hasPerm = await authService.hasPermission(permission);
      if (!hasPerm) {
        return false;
      }
    }
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * 自动刷新令牌中间件
 */
export function setupAutoTokenRefresh(): void {
  const authService = getAuthService();

  // 监听网络请求错误
  if (typeof window !== 'undefined') {
    window.addEventListener('auth:error', ((event: Event) => {
      const customEvent = event as CustomEvent<{ error?: { status?: number } }>;
      const error = customEvent.detail?.error;
      if (error?.status === 401) {
        // 401 错误时尝试刷新令牌
        void authService.refreshToken().catch(() => {
          // 刷新失败则登出
          void authService.logout();
        });
      }
    }) as EventListener);
  }
}

/**
 * 认证事件监听器
 */
export function setupAuthEventListeners(): AuthService {
  const authService = getAuthService();

  if (typeof window !== 'undefined') {
    // 登出事件
    window.addEventListener('auth:logout', () => {
      // 可以在这里添加登出后的处理逻辑
      // 比如重定向到登录页面
    });

    // 错误事件
    window.addEventListener('auth:error', ((event: Event) => {
      const customEvent = event as CustomEvent<{ error?: unknown }>;
      // eslint-disable-next-line @typescript-eslint/no-unused-vars, @typescript-eslint/no-unsafe-assignment
      const _error = customEvent.detail?.error;

      // 可以在这里添加全局错误处理
    }) as EventListener);
  }

  return authService;
}

// 默认导出
export default {
  getAuthService,
  initAuth,
  useAuth,
  authGuard,
  setupAutoTokenRefresh,
  setupAuthEventListeners,
};
