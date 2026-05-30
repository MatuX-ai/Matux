/**
 * 共享数据模型入口文件
 *
 * 导出所有框架无关的核心数据模型，供 Angular/React/Flutter 等多端使用
 */

// ==================== 认证与用户 ====================
export * from './auth.models';
export * from './group.models';

// ==================== 课程与学习 ====================
export * from './course.models';
export * from './unified-material.models';

// ==================== 订阅与支付 ====================
// subscription.models 和 pricing.models 都有 BillingCycle 枚举(不同值)，显式导出避免冲突
export {
  SubscriptionStatus,
  SubscriptionPlanType,
  SubscriptionPlan,
  UserSubscription,
  SubscriptionPayment,
  SubscriptionCycle,
  CreateSubscriptionPlanRequest,
  SubscribeRequest,
  SubscriptionStatistics,
  SubscriptionFilterOptions,
  SubscriptionDashboardData,
  BillingCycle,
} from './subscription.models';
export * from './payment.models';

// ==================== 定价 ====================
export * from './pricing.models';

// ==================== 离线 ====================
export * from './offline.models';
