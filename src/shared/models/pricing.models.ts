/**
 * 统一价格系统数据模型
 *
 * 整合 Token 套餐、订阅计划、课程价格等所有价格相关数据
 */

// ==================== 基础类型 ====================

/**
 * 价格类型枚举
 */
export enum PriceType {
  /** Token 套餐 */
  TOKEN_PACKAGE = 'token_package',
  /** 订阅计划 */
  SUBSCRIPTION_PLAN = 'subscription_plan',
  /** 课程/内容价格 */
  CONTENT_PRICE = 'content_price',
  /** 产品套餐 */
  PRODUCT_PACKAGE = 'product_package',
}

/**
 * 计费周期枚举
 */
export enum BillingCycle {
  /** 一次性 */
  ONE_TIME = 'one_time',
  /** 每月 */
  MONTHLY = 'monthly',
  /** 每季度 */
  QUARTERLY = 'quarterly',
  /** 每年 */
  YEARLY = 'yearly',
  /** 每周 */
  WEEKLY = 'weekly',
}

/**
 * 产品层级枚举
 */
export enum ProductTier {
  /** 免费版 */
  FREE = 'free',
  /** 基础版 */
  BASIC = 'basic',
  /** 专业版 */
  PROFESSIONAL = 'professional',
  /** 企业版 */
  ENTERPRISE = 'enterprise',
  /** 自定义 */
  CUSTOM = 'custom',
}

// ==================== 统一价格接口 ====================

/**
 * 统一价格项接口
 */
export interface UnifiedPriceItem {
  /** 唯一标识 */
  id: string;
  /** 价格类型 */
  type: PriceType;
  /** 名称 */
  name: string;
  /** 描述 */
  description?: string;

  /** 价格信息 */
  price: {
    /** 当前价格（分） */
    current: number;
    /** 原价（分，用于显示折扣） */
    original?: number;
    /** 货币代码 */
    currency: string;
    /** 计费周期 */
    billingCycle: BillingCycle;
    /** 折扣比例 0-1 */
    discount?: number;
  };

  /** 产品层级 */
  tier?: ProductTier;
  /** 是否热门/推荐 */
  isPopular?: boolean;
  /** 是否推荐 */
  isRecommended?: boolean;
  /** 是否启用 */
  isActive: boolean;

  /** 功能特性列表 */
  features?: string[];
  /** 使用限制 */
  limits?: Record<string, any>;

  /** 附加数据 */
  metadata: {
    /** Token 数量（仅适用于 Token 套餐） */
    tokenAmount?: number;
    /** 课程 ID（仅适用于课程价格） */
    contentId?: string;
    /** 订阅计划 ID（仅适用于订阅计划） */
    planId?: string;
    /** 有效期天数（0表示永久） */
    validityDays?: number;
    /** 试用期天数 */
    trialDays?: number;
    [key: string]: any;
  };

  /** 创建时间 */
  createdAt?: string;
  /** 更新时间 */
  updatedAt?: string;
}

/**
 * 价格分组接口
 */
export interface PriceGroup {
  /** 分组 ID */
  id: string;
  /** 分组名称 */
  name: string;
  /** 分组描述 */
  description?: string;
  /** 分组类型 */
  type: PriceType;
  /** 该组的价格项 */
  items: UnifiedPriceItem[];
  /** 默认选中的价格项 ID */
  defaultItemId?: string;
  /** 排序权重 */
  sortWeight: number;
}

/**
 * 价格配置接口
 */
export interface PricingConfig {
  /** 配置版本 */
  version: string;
  /** 货币配置 */
  currency: {
    /** 默认货币 */
    default: string;
    /** 支持的货币列表 */
    supported: string[];
  };
  /** 价格分组 */
  groups: PriceGroup[];
  /** 全局折扣活动 */
  promotions?: {
    id: string;
    name: string;
    description: string;
    discountRate: number;
    validFrom: string;
    validTo: string;
    applicableTypes: PriceType[];
  }[];
}

/**
 * 价格比较结果接口
 */
export interface PriceComparison {
  /** 项目 A */
  itemA: UnifiedPriceItem;
  /** 项目 B */
  itemB: UnifiedPriceItem;
  /** 价格差异（分） */
  priceDifference: number;
  /** 价格差异百分比 */
  priceDifferencePercentage: number;
  /** 性价比指标 */
  valueScore: {
    a: number;
    b: number;
    winner: 'a' | 'b' | 'tie';
  };
}

// ==================== 请求/响应接口 ====================

/**
 * 获取价格列表请求
 */
export interface GetPricesRequest {
  /** 价格类型筛选 */
  types?: PriceType[];
  /** 产品层级筛选 */
  tiers?: ProductTier[];
  /** 是否只返回启用的 */
  activeOnly?: boolean;
  /** 是否只返回推荐的 */
  recommendedOnly?: boolean;
  /** 排序方式 */
  sortBy?: 'price' | 'name' | 'tier' | 'popularity';
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc';
}

/**
 * 获取价格列表响应
 */
export interface GetPricesResponse {
  /** 价格配置 */
  config: PricingConfig;
  /** 筛选后的价格项 */
  items: UnifiedPriceItem[];
  /** 分组后的价格项 */
  groupedItems: PriceGroup[];
  /** 元数据 */
  metadata: {
    totalCount: number;
    filteredCount: number;
    currency: string;
  };
}

/**
 * 计算价格请求
 */
export interface CalculatePriceRequest {
  /** 价格项 ID */
  itemId: string;
  /** 数量 */
  quantity?: number;
  /** 优惠码 */
  couponCode?: string;
  /** 用户 ID（用于个性化定价） */
  userId?: string;
}

/**
 * 计算价格响应
 */
export interface CalculatePriceResponse {
  /** 原始价格（分） */
  originalPrice: number;
  /** 折扣金额（分） */
  discountAmount: number;
  /** 最终价格（分） */
  finalPrice: number;
  /** 货币 */
  currency: string;
  /** 价格明细 */
  breakdown: {
    /** 项目价格 */
    itemPrice: number;
    /** 数量 */
    quantity: number;
    /** 小计 */
    subtotal: number;
    /** 折扣 */
    discount: number;
    /** 税费 */
    tax?: number;
    /** 手续费 */
    serviceFee?: number;
  };
  /** 适用的促销活动 */
  appliedPromotions?: string[];
}

// ==================== 价格工具函数 ====================

/**
 * 格式化价格显示
 */
export function formatPrice(priceCents: number, currency: string = 'CNY'): string {
  const amount = priceCents / 100;

  switch (currency) {
    case 'CNY':
      return `¥${amount.toFixed(2)}`;
    case 'USD':
      return `$${amount.toFixed(2)}`;
    case 'EUR':
      return `€${amount.toFixed(2)}`;
    default:
      return `${amount.toFixed(2)} ${currency}`;
  }
}

/**
 * 计算月均价格
 */
export function calculateMonthlyPrice(priceCents: number, billingCycle: BillingCycle): number {
  switch (billingCycle) {
    case BillingCycle.ONE_TIME:
      return priceCents;
    case BillingCycle.MONTHLY:
      return priceCents;
    case BillingCycle.QUARTERLY:
      return Math.round(priceCents / 3);
    case BillingCycle.YEARLY:
      return Math.round(priceCents / 12);
    case BillingCycle.WEEKLY:
      return Math.round(priceCents * 4.33); // 近似月价格
    default:
      return priceCents;
  }
}

/**
 * 获取价格显示周期
 */
export function getBillingCycleDisplay(billingCycle: BillingCycle): string {
  const displayMap = {
    [BillingCycle.ONE_TIME]: '一次性',
    [BillingCycle.MONTHLY]: '/月',
    [BillingCycle.QUARTERLY]: '/季度',
    [BillingCycle.YEARLY]: '/年',
    [BillingCycle.WEEKLY]: '/周',
  };
  return displayMap[billingCycle] || '';
}

/**
 * 获取层级显示名称
 */
export function getTierDisplayName(tier: ProductTier): string {
  const displayMap = {
    [ProductTier.FREE]: '免费版',
    [ProductTier.BASIC]: '基础版',
    [ProductTier.PROFESSIONAL]: '专业版',
    [ProductTier.ENTERPRISE]: '企业版',
    [ProductTier.CUSTOM]: '自定义',
  };
  return displayMap[tier] || tier;
}
