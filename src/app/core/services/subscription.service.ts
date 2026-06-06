/**
 * 订阅服务 (Angular)
 * 提供订阅计划管理、用户订阅、支付处理等核心功能
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

import {
  BillingCycle,
  CreateSubscriptionPlanRequest,
  SubscribeRequest,
  SubscriptionDashboardData,
  SubscriptionPayment,
  SubscriptionPlan,
  SubscriptionPlanType,
  SubscriptionStatistics,
  SubscriptionStatus,
  UserSubscription,
} from '../models/subscription.models';

@Injectable({
  providedIn: 'root',
})
export class SubscriptionService {
  private baseUrl = '/api/v1/subscriptions';

  // 当前用户订阅状态管理
  private currentSubscriptionsSubject = new BehaviorSubject<UserSubscription[]>([]);
  public currentSubscriptions$ = this.currentSubscriptionsSubject.asObservable();

  // 活跃订阅
  private activeSubscriptionsSubject = new BehaviorSubject<UserSubscription[]>([]);
  public activeSubscriptions$ = this.activeSubscriptionsSubject.asObservable();

  constructor(private http: HttpClient) {
    // 初始化时加载用户订阅
    this.loadUserSubscriptions();
  }

  /**
   * 创建订阅计划（管理员权限）
   */
  createSubscriptionPlan(planData: CreateSubscriptionPlanRequest): Observable<SubscriptionPlan> {
    return this.http
      .post<SubscriptionPlan>(`${this.baseUrl}/plans`, planData)
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取所有订阅计划
   */
  getSubscriptionPlans(
    isActive: boolean = true,
    planType?: SubscriptionPlanType
  ): Observable<SubscriptionPlan[]> {
    let params = new HttpParams().set('is_active', isActive.toString());
    if (planType) {
      params = params.set('plan_type', planType);
    }

    return this.http
      .get<SubscriptionPlan[]>(`${this.baseUrl}/plans`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * 用户订阅
   */
  createSubscription(
    planId: string,
    paymentMethod: string,
    autoRenew: boolean = true
  ): Observable<UserSubscription> {
    const subscribeRequest: SubscribeRequest = {
      planId,
      paymentMethod,
      autoRenew,
      customConfig: {},
    };

    return this.http.post<UserSubscription>(`${this.baseUrl}`, subscribeRequest).pipe(
      tap(() => this.loadUserSubscriptions()),
      catchError(this.handleError)
    );
  }

  /**
   * 获取当前用户的所有订阅
   */
  getUserSubscriptions(status?: SubscriptionStatus): Observable<UserSubscription[]> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }

    return this.http.get<UserSubscription[]>(`${this.baseUrl}`, { params }).pipe(
      tap((subscriptions) => {
        this.currentSubscriptionsSubject.next(subscriptions);

        // 更新活跃订阅
        const activeSubs = subscriptions.filter((sub) => sub.status === SubscriptionStatus.ACTIVE);
        this.activeSubscriptionsSubject.next(activeSubs);
      }),
      catchError(this.handleError)
    );
  }

  /**
   * 获取订阅详情
   */
  getSubscriptionDetail(subscriptionId: string): Observable<UserSubscription> {
    return this.http
      .get<UserSubscription>(`${this.baseUrl}/${subscriptionId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 取消订阅
   */
  cancelSubscription(subscriptionId: string): Observable<{
    message: string;
    subscriptionId: string;
    cancelledAt: string;
  }> {
    return this.http
      .post<{
        message: string;
        subscriptionId: string;
        cancelledAt: string;
      }>(`${this.baseUrl}/${subscriptionId}/cancel`, {})
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取订阅支付记录
   */
  getSubscriptionPayments(subscriptionId: string): Observable<SubscriptionPayment[]> {
    return this.http
      .get<SubscriptionPayment[]>(`${this.baseUrl}/${subscriptionId}/payments`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取订阅统计信息
   */
  getSubscriptionStatistics(): Observable<SubscriptionStatistics> {
    return this.http
      .get<SubscriptionStatistics>(`${this.baseUrl}/statistics`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取订阅仪表板数据
   */
  getDashboardData(): Observable<SubscriptionDashboardData> {
    return this.http
      .get<SubscriptionDashboardData>(`${this.baseUrl}/dashboard`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 管理员获取指定用户的订阅
   */
  getUserSubscriptionsAdmin(
    userId: string,
    status?: SubscriptionStatus
  ): Observable<UserSubscription[]> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }

    return this.http
      .get<UserSubscription[]>(`${this.baseUrl}/user/${userId}/subscriptions`, {
        params,
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 重新激活订阅（管理员）
   */
  reactivateSubscription(subscriptionId: string): Observable<unknown> {
    return this.http
      .post(`${this.baseUrl}/${subscriptionId}/reactivate`, {})
      .pipe(catchError(this.handleError));
  }

  /**
   * 加载用户订阅（私有方法）
   */
  private loadUserSubscriptions(): void {
    this.getUserSubscriptions().subscribe({
      error: (error) => console.error('加载用户订阅失败:', error),
    });
  }

  /**
   * 统一错误处理
   */
  private handleError = (error: Error): Observable<never> => {
    console.error('订阅服务错误:', error);
    return throwError(() => error);
  };

  /**
   * 检查是否有活跃订阅
   */
  hasActiveSubscription(): boolean {
    return this.activeSubscriptionsSubject.value.length > 0;
  }

  /**
   * 获取特定计划类型的活跃订阅
   */
  getActiveSubscriptionsByPlanType(planType: SubscriptionPlanType): UserSubscription[] {
    return this.activeSubscriptionsSubject.value.filter((sub) => sub.plan?.planType === planType);
  }

  /**
   * 检查订阅是否即将到期
   */
  isSubscriptionExpiringSoon(subscription: UserSubscription, daysThreshold: number = 7): boolean {
    if (!subscription.endDate) return false;

    const endDate = new Date(subscription.endDate);
    const thresholdDate = new Date();
    thresholdDate.setDate(thresholdDate.getDate() + daysThreshold);

    return endDate <= thresholdDate && endDate >= new Date();
  }

  /**
   * 格式化货币显示
   */
  formatCurrency(amount: number, currency: string = 'CNY'): string {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency,
    }).format(amount);
  }

  /**
   * 格式化计费周期显示
   */
  formatBillingCycle(billingCycle: BillingCycle): string {
    const cycleMap = {
      [BillingCycle.WEEKLY]: '每周',
      [BillingCycle.MONTHLY]: '每月',
      [BillingCycle.QUARTERLY]: '每季度',
      [BillingCycle.YEARLY]: '每年',
      [BillingCycle.CUSTOM]: '自定义周期',
    };
    return cycleMap[billingCycle] || billingCycle;
  }

  /**
   * 计算订阅剩余天数
   */
  getRemainingDays(subscription: UserSubscription): number {
    if (!subscription.endDate) return 0;

    const endDate = new Date(subscription.endDate);
    const today = new Date();
    const diffTime = endDate.getTime() - today.getTime();
    return Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
  }

  /**
   * 获取订阅状态的中文描述
   */
  getStatusDescription(status: SubscriptionStatus): string {
    const statusMap = {
      [SubscriptionStatus.ACTIVE]: '激活中',
      [SubscriptionStatus.PENDING]: '待激活',
      [SubscriptionStatus.CANCELLED]: '已取消',
      [SubscriptionStatus.EXPIRED]: '已过期',
      [SubscriptionStatus.SUSPENDED]: '已暂停',
    };
    return statusMap[status] || status;
  }

  /**
   * 验证订阅是否有效
   */
  isSubscriptionValid(subscription: UserSubscription): boolean {
    if (subscription.status !== SubscriptionStatus.ACTIVE) {
      return false;
    }

    if (!subscription.endDate) {
      return true; // 无结束日期表示永久有效
    }

    const endDate = new Date(subscription.endDate);
    return endDate >= new Date();
  }
}
