/**
 * Token 系统类型定义文件
 *
 * 定义�?Token 管理、计费系统相关的 TypeScript 接口和类�?
 * 支持多种计费模式：Token 计费、订阅制、按量计费等
 *
 * @packageDocumentation
 */

// ==================== Token 套餐类型 ====================

/**
 * Token 套餐类型
 */
export type PackageType = 'starter' | 'basic' | 'pro' | 'enterprise' | 'custom';

/**
 * 计费周期类型
 */
export type BillingCycle = 'one-time' | 'monthly' | 'yearly';

/**
 * Token 套餐信息
 */
export interface TokenPackage {
  /** 套餐 ID */
  id: string;
  /** 套餐名称 */
  name: string;
  /** 套餐描述 */
  description?: string;
  /** 套餐类型 */
  packageType: PackageType;
  /** Token 数量 */
  tokenAmount: number;
  /** 套餐价格（分�?*/
  priceCents: number;
  /** 原价（分，用于显示折扣） */
  originalPriceCents?: number;
  /** 计费周期 */
  billingCycle: BillingCycle;
  /** 是否热门套餐 */
  isPopular?: boolean;
  /** 是否推荐 */
  isRecommended?: boolean;
  /** 折扣比例�?-1�?*/
  discount?: number;
  /** 有效期（天，0 表示永久�?*/
  validityDays?: number;
  /** 功能特性列�?*/
  features?: string[];
  /** 使用限制 */
  limits?: PackageLimits;
  /** 图标 URL */
  iconUrl?: string;
  /** 是否上架 */
  isActive: boolean;
  /** 创建时间 */
  createdAt?: string;
  /** 更新时间 */
  updatedAt?: string;
}

/**
 * 套餐使用限制
 */
export interface PackageLimits {
  /** 每日最大调用次�?*/
  dailyCallLimit?: number;
  /** 每月最大调用次�?*/
  monthlyCallLimit?: number;
  /** 单次请求最�?Token �?*/
  maxTokensPerRequest?: number;
  /** 并发请求数限�?*/
  concurrentRequestLimit?: number;
  /** 支持�?AI 模型列表 */
  allowedModels?: string[];
  /** 支持的功能列�?*/
  allowedFeatures?: string[];
  /** 是否支持 API 访问 */
  apiAccessEnabled?: boolean;
  /** 是否支持批量处理 */
  batchProcessingEnabled?: boolean;
}

// ==================== 用户 Token 余额类型 ====================

/**
 * Token 来源类型
 */
export type TokenSourceType = 'purchase' | 'reward' | 'refund' | 'transfer' | 'promotion';

/**
 * 用户 Token 余额信息
 */
export interface UserTokenBalance {
  /** 用户 ID */
  userId: string;
  /** 可用 Token 数量 */
  availableBalance: number;
  /** 冻结 Token 数量（正在使用中的） */
  frozenBalance: number;
  /** �?Token 数量（可�?+ 冻结�?*/
  totalBalance: number;
  /** 累计充�?Token �?*/
  totalPurchased: number;
  /** 累计消费 Token �?*/
  totalConsumed: number;
  /** 累计获赠 Token �?*/
  totalRewarded: number;
  /** 累计退�?Token �?*/
  totalRefunded: number;
  /** 最后充值时�?*/
  lastPurchaseAt?: string;
  /** 最后消费时�?*/
  lastConsumedAt?: string;
  /** 余额过期时间（如果有�?*/
  expiresAt?: string;
  /** 更新时间 */
  updatedAt?: string;
}

/**
 * Token 流水记录
 */
export interface TokenTransaction {
  /** 交易 ID */
  id: string;
  /** 用户 ID */
  userId: string;
  /** 交易类型 */
  type: 'income' | 'expense' | 'freeze' | 'unfreeze' | 'expire';
  /** Token 变化数量（正数表示增加，负数表示减少�?*/
  amount: number;
  /** 交易后余�?*/
  balanceAfter: number;
  /** 交易来源 */
  source: TokenSourceType;
  /** 关联订单 ID（如果是购买�?*/
  orderId?: string;
  /** 关联使用记录 ID（如果是消费�?*/
  usageRecordId?: string;
  /** 交易描述 */
  description?: string;
  /** 元数据 */
  metadata?: Record<string, unknown>;
  /** 创建时间 */
  createdAt: string;
}

// ==================== Token 使用记录类型 ====================

/**
 * AI 功能类型
 */
export type AIFeatureType =
  | 'ai-code-completion'
  | 'ai-code-generation'
  | 'ai-chat'
  | 'ai-image-generation'
  | 'ai-voice-synthesis'
  | 'ai-video-generation'
  | 'ai-data-analysis'
  | 'ai-content-moderation'
  | 'custom';

/**
 * Token 使用记录
 */
export interface TokenUsageRecord {
  /** 使用记录 ID */
  id: string;
  /** 用户 ID */
  userId: string;
  /** 功能类型 */
  featureType: AIFeatureType;
  /** 使用�?AI 模型 */
  model?: string;
  /** 消�?Token 数量 */
  tokensUsed: number;
  /** 输入 Token �?*/
  inputTokens?: number;
  /** 输出 Token �?*/
  outputTokens?: number;
  /** 请求参数 */
  requestParams?: Record<string, unknown>;
  /** 响应结果摘要 */
  responseSummary?: string;
  /** 请求耗时（毫秒） */
  durationMs?: number;
  /** 请求状�?*/
  status: 'success' | 'failed' | 'cancelled';
  /** 错误消息（如果失败） */
  errorMessage?: string;
  /** 错误�?*/
  errorCode?: string;
  /** IP 地址 */
  ipAddress?: string;
  /** 用户代理 */
  userAgent?: string;
  /** 会话 ID */
  sessionId?: string;
  /** 项目 ID */
  projectId?: string;
  /** 创建时间 */
  createdAt: string;
}

/**
 * Token 使用统计查询参数
 */
export interface UsageQueryParams {
  /** 开始日�?*/
  startDate?: string;
  /** 结束日期 */
  endDate?: string;
  /** 功能类型过滤 */
  featureType?: AIFeatureType;
  /** 分页 - 页码 */
  page?: number;
  /** 分页 - 每页数量 */
  limit?: number;
  /** 排序字段 */
  sortBy?: 'createdAt' | 'tokensUsed' | 'durationMs';
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc';
}

/**
 * Token 使用统计响应
 */
export interface UsageStatsResponse {
  /** 使用记录列表 */
  data: TokenUsageRecord[];
  /** 总数 */
  total: number;
  /** 当前页码 */
  page: number;
  /** 每页数量 */
  limit: number;
  /** 总页�?*/
  totalPages: number;
}

// ==================== 统计信息类型 ====================

/**
 * Token 统计信息（按时间维度�?
 */
export interface TokenTimeStats {
  /** 日期 */
  date: string;
  /** 消费 Token �?*/
  consumed: number;
  /** 充�?Token �?*/
  purchased: number;
  /** 净变化（充�?- 消费�?*/
  netChange: number;
  /** 日均消费（最�?7 �?30 天） */
  averageDailyConsumption?: number;
  /** 预计可用天数 */
  estimatedDaysRemaining?: number;
}

/**
 * Token 统计信息（按功能维度�?
 */
export interface TokenFeatureStats {
  /** 功能类型 */
  featureType: AIFeatureType;
  /** 调用次数 */
  callCount: number;
  /** 消费 Token �?*/
  tokensConsumed: number;
  /** 平均每次调用消�?*/
  averageTokensPerCall: number;
  /** 成功次数 */
  successCount: number;
  /** 失败次数 */
  failureCount: number;
  /** 成功�?*/
  successRate: number;
  /** 平均响应时间（毫秒） */
  averageDurationMs: number;
}

/**
 * 综合统计信息
 */
export interface TokenStats {
  /** 基础统计 */
  summary: {
    /** 总充值金额（分） */
    totalSpentCents: number;
    /** 总节省金额（分，相比原价�?*/
    totalSavedCents: number;
    /** 账户创建天数 */
    accountAgeDays: number;
    /** 首次充值时�?*/
    firstPurchaseDate?: string;
  };
  /** 时间维度统计 */
  timeStats: TokenTimeStats[];
  /** 功能维度统计 */
  featureStats: TokenFeatureStats[];
  /** Top N 使用记录 */
  topUsageRecords?: TokenUsageRecord[];
}

// ==================== 订单相关类型 ====================

/**
 * 订单状�?
 */
export type OrderStatus = 'pending' | 'paid' | 'failed' | 'refunded' | 'cancelled' | 'expired';

/**
 * 支付方式
 */
export type PaymentMethod = 'alipay' | 'wechat' | 'credit_card' | 'bank_transfer' | 'balance';

/**
 * 订单信息
 */
export interface TokenOrder {
  /** 订单 ID */
  id: string;
  /** 订单�?*/
  orderNo: string;
  /** 用户 ID */
  userId: string;
  /** 套餐 ID */
  packageId: string;
  /** 套餐信息快照 */
  packageSnapshot: {
    name: string;
    tokenAmount: number;
    originalPriceCents: number;
    discount?: number;
  };
  /** 订单金额（分�?*/
  amountCents: number;
  /** 实付金额（分�?*/
  paidAmountCents?: number;
  /** 获取 Token �?*/
  tokensObtained: number;
  /** 支付方式 */
  paymentMethod?: PaymentMethod;
  /** 支付流水�?*/
  transactionId?: string;
  /** 订单状�?*/
  status: OrderStatus;
  /** 支付时间 */
  paidAt?: string;
  /** 过期时间 */
  expiresAt?: string;
  /** 退款时�?*/
  refundedAt?: string;
  /** 退款原�?*/
  refundReason?: string;
  /** 用户备注 */
  userNote?: string;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

/**
 * 创建订单请求
 */
export interface CreateOrderRequest {
  /** 套餐 ID */
  packageId: string;
  /** 支付方式 */
  paymentMethod: PaymentMethod;
  /** 优惠券代码（可选） */
  couponCode?: string;
  /** 用户备注（可选） */
  userNote?: string;
}

/**
 * 创建订单响应
 */
export interface CreateOrderResponse {
  /** 订单信息 */
  order: TokenOrder;
  /** 支付二维�?URL（如果需要扫码支付） */
  qrCodeUrl?: string;
  /** 支付跳转 URL（如果需要网页支付） */
  paymentUrl?: string;
}

// ==================== 成本预估类型 ====================

/**
 * 成本预估参数
 */
export interface CostEstimateParams {
  /** 功能类型 */
  featureType: AIFeatureType;
  /** AI 模型（可选） */
  model?: string;
  /** 输入 Token 数（可选） */
  inputTokens?: number;
  /** 输出 Token 数（可选） */
  outputTokens?: number;
  /** 请求参数（可选） */
  params?: Record<string, unknown>;
}

/**
 * 成本预估响应
 */
export interface CostEstimateResponse {
  /** 预估消�?Token �?*/
  estimatedTokens: number;
  /** 预估成本（分�?*/
  estimatedCostCents: number;
  /** 计算详情 */
  breakdown?: {
    /** 输入 Token 成本 */
    inputCostCents: number;
    /** 输出 Token 成本 */
    outputCostCents: number;
    /** 基础费用 */
    baseFeeCents: number;
    /** 折扣 */
    discountCents: number;
  };
  /** 说明 */
  note?: string;
}

// ==================== 优惠券相关类�?====================

/**
 * 优惠券类�?
 */
export type CouponType = 'discount' | 'fixed' | 'gift' | 'trial';

/**
 * 优惠券信�?
 */
export interface Coupon {
  /** 优惠�?ID */
  id: string;
  /** 优惠券代�?*/
  code: string;
  /** 优惠券名�?*/
  name: string;
  /** 优惠券描�?*/
  description?: string;
  /** 优惠券类�?*/
  type: CouponType;
  /** 折扣比例（折扣券使用�?-1�?*/
  discount?: number;
  /** 固定金额（固定券使用，分�?*/
  fixedAmountCents?: number;
  /** 赠�?Token 数（赠券使用�?*/
  giftTokens?: number;
  /** 最低消费金额（分） */
  minPurchaseCents?: number;
  /** 最高抵扣金额（分） */
  maxDiscountCents?: number;
  /** 适用套餐列表 */
  applicablePackages?: string[];
  /** 每人限用次数 */
  limitPerUser?: number;
  /** 已使用次�?*/
  usedCount?: number;
  /** 剩余数量�? 表示不限量） */
  totalLimit?: number;
  /** 生效时间 */
  validFrom: string;
  /** 过期时间 */
  validUntil: string;
  /** 是否启用 */
  isActive: boolean;
  /** 创建时间 */
  createdAt: string;
}

/**
 * 应用优惠券请�?
 */
export interface ApplyCouponRequest {
  /** 优惠券代�?*/
  couponCode: string;
  /** 订单金额（分�?*/
  orderAmountCents: number;
  /** 套餐 ID 列表 */
  packageIds: string[];
}

/**
 * 应用优惠券响�?
 */
export interface ApplyCouponResponse {
  /** 是否可用 */
  applicable: boolean;
  /** 优惠金额（分�?*/
  discountCents: number;
  /** 最终金额（分） */
  finalAmountCents: number;
  /** 错误消息（如果不可用�?*/
  errorMessage?: string;
}

// ==================== API Key 类型 ====================

/**
 * API Key 权限级别
 */
export type APIKeyPermission = 'read' | 'write' | 'admin' | 'billing';

/**
 * API Key 信息
 */
export interface APIKey {
  /** API Key ID */
  id: string;
  /** Key 名称 */
  name: string;
  /** API Key（仅创建时返回一次） */
  key?: string;
  /** Key 前缀（用于展示） */
  keyPrefix?: string;
  /** 权限列表 */
  permissions: APIKeyPermission[];
  /** 允许�?IP 白名�?*/
  ipWhitelist?: string[];
  /** 允许�?Referer 白名�?*/
  refererWhitelist?: string[];
  /** 速率限制（次/分钟�?*/
  rateLimit?: number;
  /** 是否启用 */
  isActive: boolean;
  /** 最后使用时�?*/
  lastUsedAt?: string;
  /** 过期时间 */
  expiresAt?: string;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

/**
 * 创建 API Key 请求
 */
export interface CreateAPIKeyRequest {
  /** Key 名称 */
  name: string;
  /** 权限列表 */
  permissions: APIKeyPermission[];
  /** IP 白名单（可选） */
  ipWhitelist?: string[];
  /** Referer 白名单（可选） */
  refererWhitelist?: string[];
  /** 速率限制（可选） */
  rateLimit?: number;
  /** 过期时间（可选） */
  expiresAt?: string;
}
