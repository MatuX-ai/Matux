/**
 * 支付相关数据模型
 */

// 购物车项目接口
export interface CartItem {
  /** 商品ID */
  productId: string;
  /** 商品名称 */
  productName: string;
  /** 商品价格 */
  price: number;
  /** 数量 */
  quantity: number;
  /** 商品图片URL */
  imageUrl?: string;
  /** 商品描述 */
  description?: string;
}

// 支付请求接口
export interface PaymentRequest {
  /** 购物车项目列表 */
  items: CartItem[];
  /** 总金额 */
  total: number;
  /** 用户ID */
  userId: string;
  /** 支付方式 */
  paymentMethod: PaymentMethod;
  /** 收货地址 */
  shippingAddress?: ShippingAddress;
  /** 用户备注 */
  note?: string;
}

// 支付方式枚举
export enum PaymentMethod {
  /** 微信支付 */
  WECHAT_PAY = 'wechat_pay',
  /** 支付宝 */
  ALIPAY = 'alipay',
  /** 银行卡 */
  BANK_CARD = 'bank_card',
  /** 余额支付 */
  BALANCE = 'balance',
}

// 收货地址接口
export interface ShippingAddress {
  /** 收货人姓名 */
  recipientName: string;
  /** 手机号码 */
  phone: string;
  /** 省份 */
  province: string;
  /** 城市 */
  city: string;
  /** 区县 */
  district: string;
  /** 详细地址 */
  detailAddress: string;
  /** 邮政编码 */
  postalCode?: string;
}

// 支付响应接口
export interface PaymentResponse {
  /** 支付ID */
  paymentId: string;
  /** 订单ID */
  orderId: string;
  /** 支付状态 */
  status: PaymentStatus;
  /** 支付金额 */
  amount: number;
  /** 支付方式 */
  paymentMethod: PaymentMethod;
  /** 支付时间 */
  paymentTime?: string;
  /** 交易流水号 */
  transactionId?: string;
  /** 支付凭证 */
  paymentProof?: string;
}

// 支付状态枚举
export enum PaymentStatus {
  /** 待支付 */
  PENDING = 'pending',
  /** 支付成功 */
  SUCCESS = 'success',
  /** 支付失败 */
  FAILED = 'failed',
  /** 已取消 */
  CANCELLED = 'cancelled',
  /** 退款中 */
  REFUNDING = 'refunding',
  /** 已退款 */
  REFUNDED = 'refunded',
}

// 订单接口
export interface Order {
  /** 订单ID */
  orderId: string;
  /** 用户ID */
  userId: string;
  /** 订单项目 */
  items: OrderItem[];
  /** 总金额 */
  totalAmount: number;
  /** 实际支付金额 */
  paidAmount: number;
  /** 订单状态 */
  status: OrderStatus;
  /** 支付状态 */
  paymentStatus: PaymentStatus;
  /** 收货地址 */
  shippingAddress?: ShippingAddress;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 完成时间 */
  completedAt?: string;
}

// 订单项目接口
export interface OrderItem {
  /** 商品ID */
  productId: string;
  /** 商品名称 */
  productName: string;
  /** 单价 */
  unitPrice: number;
  /** 数量 */
  quantity: number;
  /** 小计 */
  subtotal: number;
}

// 订单状态枚举
export enum OrderStatus {
  /** 待付款 */
  PENDING_PAYMENT = 'pending_payment',
  /** 待发货 */
  PENDING_SHIPMENT = 'pending_shipment',
  /** 已发货 */
  SHIPPED = 'shipped',
  /** 已完成 */
  COMPLETED = 'completed',
  /** 已取消 */
  CANCELLED = 'cancelled',
}

// 支付网关响应接口
export interface PaymentGatewayResponse {
  /** 是否成功 */
  success: boolean;
  /** 交易ID */
  transactionId?: string;
  /** 错误信息 */
  errorMessage?: string;
  /** 支付凭证 */
  paymentProof?: string;
  /** 重定向URL（如需要） */
  redirectUrl?: string;
}

// 支付配置接口
export interface PaymentConfig {
  /** 微信支付配置 */
  wechatPay?: WechatPayConfig;
  /** 支付宝配置 */
  alipay?: AlipayConfig;
  /** 银行卡支付配置 */
  bankCard?: BankCardConfig;
}

// 微信支付配置
export interface WechatPayConfig {
  /** App ID */
  appId: string;
  /** 商户号 */
  mchId: string;
  /** API密钥 */
  apiKey: string;
  /** 通知URL */
  notifyUrl: string;
}

// 支付宝配置
export interface AlipayConfig {
  /** 应用ID */
  appId: string;
  /** 私钥 */
  privateKey: string;
  /** 公钥 */
  publicKey: string;
  /** 通知URL */
  notifyUrl: string;
}

// 银行卡支付配置
export interface BankCardConfig {
  /** 商户ID */
  merchantId: string;
  /** 终端ID */
  terminalId: string;
  /** 加密密钥 */
  encryptKey: string;
}

// 支付统计接口
export interface PaymentStatistics {
  /** 总交易额 */
  totalAmount: number;
  /** 总订单数 */
  totalOrders: number;
  /** 成功交易数 */
  successfulPayments: number;
  /** 成功率 */
  successRate: number;
  /** 按支付方式统计 */
  paymentMethodStats: {
    method: PaymentMethod;
    count: number;
    amount: number;
  }[];
}
