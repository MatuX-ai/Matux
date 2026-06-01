/**
 * 核心服务索引文件
 *
 * 导出所有核心服务以便于导入
 */

// ==================== Auth相关服务 ====================
export { AuthService } from './auth.service';
export { AuthHttpClient } from './auth-http-client';
export { AuthStateManager } from './auth-state-manager';
export { TokenService } from './token.service';

// ==================== AI教育相关服务 ====================
export { AIEduService } from './ai-edu.service';
export { AiEduWebSocketService } from './ai-edu-websocket.service';
export { AIEduAntiCheatingService } from './ai-edu/ai-edu-anti-cheating.service';
export { AIEduCacheService } from './ai-edu/ai-edu-cache.service';
export { AIEduErrorHandlerService } from './ai-edu/ai-edu-error-handler.service';
export { AIEduLearningService } from './ai-edu/ai-edu-learning.service';
export { AIEduShortcutService } from './ai-edu/ai-edu-shortcut.service';
export { EditorContextService } from './ai-edu/editor-context.service';
export { CodeCompletionService } from './ai-edu/code-completion.service';

// ==================== 学习与课程服务 ====================
export { MultiSourceLearningService } from './multi-source-learning.service';
export { UnifiedCourseService } from './unified-course.service';
export { CourseEnrollmentService } from './course-enrollment.service';

// ==================== 应用状态服务 ====================
export { AppStateService } from './app-state.service';

// ==================== 国际化服务 ====================
export { I18nService, I18nTranslations } from './i18n.service';

// ==================== 网络与离线服务 ====================
export { NetworkMonitorService } from './network-monitor.service';
export { OfflineStorageService } from './offline-storage.service';
export { WebSocketNotificationService } from './websocket-notification.service';

// ==================== 性能监控与PWA ====================
export { PerformanceMonitorService } from './performance-monitor.service';
export { PwaService } from './pwa.service';

// ==================== 显示与主题 ====================
export { ThemeService } from './theme.service';
export { SEOService } from './seo.service';
export { EnhancedToastService } from './enhanced-toast.service';

// ==================== 订阅与授权 ====================
export { SubscriptionService } from './subscription.service';
// 许可证服务已随许可证管理模块一并移除（已解耦至 OpenMTEduInst 项目）

// ==================== 电路相关服务 ====================
export { CircuitAssemblyService } from './circuit-assembly.service';
export { CircuitIntegralService } from './circuit-integral.service';
export { CircuitSimulatorService } from './circuit-simulator.service';

// ==================== 业务服务 ====================
export { ABTestingService } from './ab-testing.service';
export { EcommerceService } from './ecommerce.service';
export { PricingService } from './pricing.service';
export { GroupService } from './group.service';
export { NotificationService } from './notification.service';
export { RepositoryCacheService } from './repository-cache.service';

// ==================== Vircadia相关服务 ====================
export { VircadiaModelLoaderService } from './vircadia-model-loader.service';
export { VircadiaPhysicsService } from './vircadia-physics.service';
export { VircadiaSdkService } from './vircadia-sdk.service';

// ==================== HTTP客户端 ====================
export { UnifiedHttpClient } from './unified-http-client';

// ==================== OpenHydra服务 ====================
export { OpenHydraService } from './openhydra.service';

// ==================== Electron 桌面服务 ====================
export { ElectronService } from './electron.service';

// ==================== 自定义策略 ====================
export { CustomPreloadingStrategy } from './custom-preloading.strategy';
