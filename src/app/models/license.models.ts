/**
 * 许可证管理相关的数据模型
 */

/**
 * 许可证类型
 */
export type LicenseType =
  | 'cloud_hosted' // 云托管版
  | 'enterprise' // 企业版
  | 'education' // 教育版
  | 'trial'; // 试用版

/**
 * 许可证状态
 */
export type LicenseStatus =
  | 'active' // 活跃
  | 'expiring' // 即将过期
  | 'expired' // 已过期
  | 'revoked'; // 已撤销

/**
 * 许可证详情接口
 */
export interface LicenseDetail {
  /** 许可证 ID */
  id: number;

  /** 许可证密钥 */
  license_key: string;

  /** 许可证类型 */
  license_type: LicenseType;

  /** 许可证状态 */
  status: LicenseStatus;

  /** 颁发日期 */
  issued_at: string;

  /** 到期日期 */
  expires_at: string;

  /** 最大用户数 */
  max_users: number;

  /** 当前用户数 */
  current_users: number;

  /** 功能特性列表 */
  features: string[];

  /** 距离到期天数 */
  days_until_expiry: number;

  /** 组织名称 */
  organization_name: string;
}

/**
 * 许可证分配请求
 */
export interface LicenseAssignRequest {
  /** 许可证 ID */
  licenseId: number;

  /** 用户 ID 列表 */
  userIds: number[];

  /** 用户角色 */
  role: 'admin' | 'user';

  /** 备注 */
  notes?: string;
}

/**
 * Token 套餐信息
 */
export interface TokenPackage {
  /** 套餐 ID */
  id: number;

  /** 套餐名称 */
  name: string;

  /** Token 数量 */
  tokenAmount: number;

  /** 价格（元） */
  price: number;

  /** 有效期（天） */
  validityDays: number;

  /** 套餐描述 */
  description: string;

  /** 是否推荐 */
  isRecommended?: boolean;

  /** 适合场景 */
  suitableFor: string;
}

/**
 * Token 交易记录
 */
export interface TokenTransaction {
  /** 交易 ID */
  id: number;

  /** 交易类型 */
  type: 'purchase' | 'consumption' | 'refund' | 'bonus';

  /** Token 数量 */
  amount: number;

  /** 交易后余额 */
  balanceAfter: number;

  /** 交易时间 */
  createdAt: string;

  /** 交易描述 */
  description: string;

  /** 关联订单 ID（如果有） */
  orderId?: number;
}

/**
 * Token 余额信息
 */
export interface TokenBalance {
  /** 当前余额 */
  balance: number;

  /** 本月购买 */
  purchasedThisMonth: number;

  /** 本月消费 */
  consumedThisMonth: number;

  /** 自动续费状态 */
  autoRenewalEnabled: boolean;

  /** 下次扣款日期 */
  nextBillingDate?: string;
}
