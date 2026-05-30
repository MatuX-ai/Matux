/**
 * 订阅系统数据模型
 */

// 计费周期枚举
export enum BillingCycle {
  /** 每周 */
  WEEKLY = 'weekly',
  /** 每月 */
  MONTHLY = 'monthly',
  /** 每季度 */
  QUARTERLY = 'quarterly',
  /** 每年 */
  YEARLY = 'yearly',
  /** 自定义周期 */
  CUSTOM = 'custom',
}

// 订阅状态枚举
export enum SubscriptionStatus {
  /** 激活中 */
  ACTIVE = 'active',
  /** 待激活 */
  PENDING = 'pending',
  /** 已取消 */
  CANCELLED = 'cancelled',
  /** 已过期 */
  EXPIRED = 'expired',
  /** 已暂停 */
  SUSPENDED = 'suspended',
}

// 订阅计划类型枚举
export enum SubscriptionPlanType {
  /** 基础版 */
  BASIC = 'basic',
  /** 专业版 */
  PROFESSIONAL = 'professional',
  /** 企业版 */
  ENTERPRISE = 'enterprise',
  /** 自定义 */
  CUSTOM = 'custom',
}

// 订阅计划接口
export interface SubscriptionPlan {
  /** 计划ID */
  planId: string;
  /** 计划名称 */
  name: string;
  /** 计划描述 */
  description: string;
  /** 计划类型 */
  planType: SubscriptionPlanType;

  /** 价格 */
  price: number;
  /** 计费周期 */
  billingCycle: BillingCycle;
  /** 货币单位 */
  currency: string;

  /** 功能列表 */
  features: string[];
  /** 限制配置 */
  limits: Record<string, any>;
  /** 是否推荐 */
  isPopular: boolean;
  /** 是否启用 */
  isActive: boolean;

  /** 试用期天数 */
  trialPeriodDays: number;
  /** 开通费用 */
  setupFee: number;

  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

// 用户订阅接口
export interface UserSubscription {
  /** 订阅ID */
  subscriptionId: string;
  /** 用户ID */
  userId: string;
  /** 计划ID */
  planId: string;

  /** 订阅状态 */
  status: SubscriptionStatus;

  /** 开始日期 */
  startDate: string;
  /** 结束日期 */
  endDate: string;
  /** 下次计费日期 */
  nextBillingDate: string;
  /** 取消时间 */
  cancelledAt?: string;

  /** 是否自动续费 */
  autoRenew: boolean;
  /** 续费次数 */
  renewalCount: number;

  /** 订阅时的价格快照 */
  priceSnapshot: number;
  /** 货币快照 */
  currencySnapshot: string;

  /** 自定义配置 */
  customConfig: Record<string, any>;
  /** 元数据 */
  metadata: Record<string, any>;

  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;

  /** 关联的计划信息（可选） */
  plan?: SubscriptionPlan;
}

// 订阅支付记录接口
export interface SubscriptionPayment {
  /** 支付ID */
  paymentId: string;
  /** 订阅ID */
  subscriptionId: string;

  /** 支付金额 */
  amount: number;
  /** 货币 */
  currency: string;
  /** 支付方式 */
  paymentMethod: string;

  /** 计费周期开始 */
  billingCycleStart: string;
  /** 计费周期结束 */
  billingCycleEnd: string;

  /** 支付状态 */
  status: string;
  /** 第三方交易ID */
  transactionId?: string;
  /** 支付凭证 */
  paymentProof?: string;

  /** 网关响应 */
  gatewayResponse: Record<string, any>;
  /** 是否收到通知 */
  notificationReceived: boolean;

  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 处理时间 */
  processedAt?: string;
}

// 订阅周期配置接口
export interface SubscriptionCycle {
  /** 周期ID */
  cycleId: string;
  /** 计划ID */
  planId: string;

  /** 计费周期 */
  billingCycle: BillingCycle;
  /** 间隔数量 */
  intervalCount: number;

  /** 价格倍数 */
  priceMultiplier: number;
  /** 折扣率 */
  discountRate: number;

  /** 生效开始时间 */
  effectiveFrom: string;
  /** 生效结束时间 */
  effectiveTo?: string;

  /** 是否激活 */
  isActive: boolean;

  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

// 创建订阅计划请求接口
export interface CreateSubscriptionPlanRequest {
  /** 计划名称 */
  name: string;
  /** 计划描述 */
  description: string;
  /** 计划类型 */
  planType: SubscriptionPlanType;
  /** 价格 */
  price: number;
  /** 计费周期 */
  billingCycle: BillingCycle;
  /** 功能列表 */
  features?: string[];
  /** 限制配置 */
  limits?: Record<string, any>;
  /** 试用期天数 */
  trialPeriodDays?: number;
  /** 开通费用 */
  setupFee?: number;
  /** 货币单位 */
  currency?: string;
  /** 是否推荐 */
  isPopular?: boolean;
}

// 用户订阅请求接口
export interface SubscribeRequest {
  /** 订阅计划ID */
  planId: string;
  /** 支付方式 */
  paymentMethod: string;
  /** 是否自动续费 */
  autoRenew?: boolean;
  /** 自定义配置 */
  customConfig?: Record<string, any>;
}

// 订阅统计接口
export interface SubscriptionStatistics {
  /** 总订阅数 */
  totalSubscriptions: number;
  /** 激活订阅数 */
  activeSubscriptions: number;
  /** 取消订阅数 */
  cancelledSubscriptions: number;
  /** 本月新增订阅数 */
  newSubscriptionsThisMonth: number;
  /** 本月收入 */
  revenueThisMonth: number;
  /** 按计划类型的统计 */
  planTypeStats: {
    planType: SubscriptionPlanType;
    count: number;
    revenue: number;
  }[];
  /** 按计费周期的统计 */
  billingCycleStats: {
    billingCycle: BillingCycle;
    count: number;
    revenue: number;
  }[];
}

// 订阅管理过滤选项
export interface SubscriptionFilterOptions {
  /** 订阅状态 */
  status?: SubscriptionStatus;
  /** 计划类型 */
  planType?: SubscriptionPlanType;
  /** 计费周期 */
  billingCycle?: BillingCycle;
  /** 搜索关键词 */
  search?: string;
  /** 日期范围 - 开始 */
  dateFrom?: string;
  /** 日期范围 - 结束 */
  dateTo?: string;
}

// 订阅仪表板数据接口
export interface SubscriptionDashboardData {
  /** 订阅统计数据 */
  statistics: SubscriptionStatistics;
  /** 最近订阅 */
  recentSubscriptions: UserSubscription[];
  /** 即将到期的订阅 */
  expiringSoon: UserSubscription[];
  /** 收入趋势 */
  revenueTrend: {
    date: string;
    amount: number;
  }[];
}
