/**
 * 电商支付服务 (Angular)
 * 提供购物车、订单、支付等电商核心功能
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import {
  CartItem,
  Order,
  PaymentMethod,
  PaymentRequest,
  PaymentResponse,
  PaymentStatistics,
  PaymentStatus,
  ShippingAddress,
} from '../models/payment.models';

import { unifiedHttpClient } from './unified-http-client';

@Injectable({
  providedIn: 'root',
})
export class EcommerceService {
  private baseUrl = '/api/v1/payments';

  // 购物车状态管理
  private cartItemsSubject = new BehaviorSubject<CartItem[]>([]);
  public cartItems$ = this.cartItemsSubject.asObservable();

  // 购物车总价
  private cartTotalSubject = new BehaviorSubject<number>(0);
  public cartTotal$ = this.cartTotalSubject.asObservable();

  constructor() {
    // 初始化购物车（从localStorage加载）
    this.loadCartFromStorage();
  }

  /**
   * 添加商品到购物车
   */
  addToCart(item: CartItem): void {
    const currentItems = this.cartItemsSubject.value;
    const existingItemIndex = currentItems.findIndex((i) => i.productId === item.productId);

    if (existingItemIndex >= 0) {
      // 更新已有商品数量
      const updatedItems = [...currentItems];
      updatedItems[existingItemIndex].quantity += item.quantity;
      this.cartItemsSubject.next(updatedItems);
    } else {
      // 添加新商品
      this.cartItemsSubject.next([...currentItems, item]);
    }

    this.updateCartTotal();
    this.saveCartToStorage();
  }

  /**
   * 从购物车移除商品
   */
  removeFromCart(productId: string): void {
    const updatedItems = this.cartItemsSubject.value.filter((item) => item.productId !== productId);
    this.cartItemsSubject.next(updatedItems);
    this.updateCartTotal();
    this.saveCartToStorage();
  }

  /**
   * 更新购物车商品数量
   */
  updateQuantity(productId: string, quantity: number): void {
    if (quantity <= 0) {
      this.removeFromCart(productId);
      return;
    }

    const updatedItems = this.cartItemsSubject.value.map((item) =>
      item.productId === productId ? { ...item, quantity } : item
    );

    this.cartItemsSubject.next(updatedItems);
    this.updateCartTotal();
    this.saveCartToStorage();
  }

  /**
   * 清空购物车
   */
  clearCart(): void {
    this.cartItemsSubject.next([]);
    this.cartTotalSubject.next(0);
    this.saveCartToStorage();
  }

  /**
   * 获取购物车项目数量
   */
  getCartItemCount(): number {
    return this.cartItemsSubject.value.reduce((total, item) => total + item.quantity, 0);
  }

  /**
   * 计算购物车总价
   */
  private updateCartTotal(): void {
    const total = this.cartItemsSubject.value.reduce(
      (sum, item) => sum + item.price * item.quantity,
      0
    );
    this.cartTotalSubject.next(total);
  }

  /**
   * 保存购物车到本地存储
   */
  private saveCartToStorage(): void {
    try {
      localStorage.setItem('ecommerce_cart', JSON.stringify(this.cartItemsSubject.value));
    } catch {
      /* 存储失败不阻塞 */
    }
  }

  /**
   * 从本地存储加载购物车
   */
  private loadCartFromStorage(): void {
    try {
      const savedCart = localStorage.getItem('ecommerce_cart');
      if (savedCart) {
        const cartItems = JSON.parse(savedCart) as CartItem[];
        this.cartItemsSubject.next(cartItems);
        this.updateCartTotal();
      }
    } catch {
      /* JSON 解析失败使用空购物车 */
      this.cartItemsSubject.next([]);
    }
  }

  /**
   * 结账支付
   */
  async checkout(
    cartItems: CartItem[],
    paymentMethod: PaymentMethod,
    shippingAddress?: ShippingAddress,
    note?: string
  ): Promise<PaymentResponse> {
    const total = this.calculateTotal(cartItems);

    const paymentRequest: PaymentRequest = {
      items: cartItems,
      total,
      userId: '', // 实际应用中应从认证服务获取
      paymentMethod,
      shippingAddress,
      note,
    };

    const response = await unifiedHttpClient.post<PaymentResponse>(
      `${this.baseUrl}/checkout`,
      paymentRequest
    );

    // 支付成功后清空购物车
    if (response.data.status === PaymentStatus.SUCCESS) {
      this.clearCart();
    }
    return response.data;
  }

  /**
   * 计算总价
   */
  calculateTotal(items: CartItem[]): number {
    return items.reduce((total, item) => total + item.price * item.quantity, 0);
  }

  /**
   * 获取用户订单列表
   */
  async getUserOrders(
    limit: number = 20,
    offset: number = 0
  ): Promise<{
    orders: Order[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await unifiedHttpClient.get<{
      orders: Order[];
      total: number;
      limit: number;
      offset: number;
    }>(`${this.baseUrl}/orders?limit=${limit}&offset=${offset}`);

    return response.data;
  }

  /**
   * 获取订单详情
   */
  async getOrder(orderId: string): Promise<Order> {
    const response = await unifiedHttpClient.get<Order>(`${this.baseUrl}/orders/${orderId}`);
    return response.data;
  }

  /**
   * 取消订单
   */
  async cancelOrder(orderId: string): Promise<{ message: string; orderId: string }> {
    const response = await unifiedHttpClient.post<{ message: string; orderId: string }>(
      `${this.baseUrl}/orders/${orderId}/cancel`,
      {}
    );
    return response.data;
  }

  /**
   * 获取支付统计信息
   */
  async getPaymentStatistics(): Promise<{ statistics: PaymentStatistics }> {
    const response = await unifiedHttpClient.get<{ statistics: PaymentStatistics }>(
      `${this.baseUrl}/statistics`
    );
    return response.data;
  }

  /**
   * 获取支持的支付方式
   */
  async getPaymentMethods(): Promise<{
    payment_methods: { method: string; name: string; description: string }[];
  }> {
    const response = await unifiedHttpClient.get<{
      payment_methods: { method: string; name: string; description: string }[];
    }>(`${this.baseUrl}/payment-methods`);
    return response.data;
  }

  /**
   * 获取支付状态
   */
  async getPaymentStatus(paymentId: string): Promise<Record<string, unknown>> {
    const response = await unifiedHttpClient.get<Record<string, unknown>>(
      `${this.baseUrl}/payment-status/${paymentId}`
    );
    return response.data;
  }

  /**
   * 模拟支付（测试用）
   */
  async simulatePayment(orderId: string, paymentMethod: PaymentMethod): Promise<PaymentResponse> {
    const response = await unifiedHttpClient.post<PaymentResponse>(
      `${this.baseUrl}/simulate-payment`,
      {
        order_id: orderId,
        payment_method: paymentMethod,
      }
    );
    return response.data;
  }

  /**
   * 处理支付结果
   */
  handlePaymentResult(paymentResponse: PaymentResponse): void {
    if (paymentResponse.status === PaymentStatus.SUCCESS) {
      // 可以在这里触发成功通知或其他业务逻辑
    } else {
      // 可以在这里触发失败通知
    }
  }

  /**
   * 格式化货币显示
   */
  formatCurrency(amount: number): string {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
    }).format(amount);
  }

  /**
   * 验证收货地址
   */
  validateShippingAddress(address: ShippingAddress): boolean {
    return !!(
      address.recipientName &&
      address.phone &&
      address.province &&
      address.city &&
      address.district &&
      address.detailAddress
    );
  }

  /**
   * 获取购物车商品
   */
  getCartItems(): CartItem[] {
    return this.cartItemsSubject.value;
  }

  /**
   * 获取购物车总价
   */
  getCartTotal(): number {
    return this.cartTotalSubject.value;
  }
}
