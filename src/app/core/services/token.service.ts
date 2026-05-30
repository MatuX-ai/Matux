/**
 * Token 管理服务
 *
 * 提供 Token 相关�?HTTP请求服务，包括：
 * - Token 套餐管理
 * - 余额查询
 * - 使用记录查询
 * - 订单管理
 * - 成本预估
 * - API Key 管理
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { delay, Observable, of, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import {
  APIKey,
  ApplyCouponRequest,
  ApplyCouponResponse,
  CostEstimateParams,
  CostEstimateResponse,
  Coupon,
  CreateAPIKeyRequest,
  CreateOrderRequest,
  CreateOrderResponse,
  PackageType,
  TokenFeatureStats,
  TokenOrder,
  TokenPackage,
  TokenStats,
  TokenTimeStats,
  TokenTransaction,
  TokenUsageRecord,
  UsageQueryParams,
  UsageStatsResponse,
  UserTokenBalance,
} from '../../models/token.models';

// 导入PackageType用于类型断言
const PackageTypeEnum = {
  ONE_TIME: 'one-time' as PackageType,
  MONTHLY: 'monthly' as PackageType,
  YEARLY: 'yearly' as PackageType,
};

/**
 * 是否使用模拟数据
 */
const USE_MOCK_DATA = true;

/**
 * Token 管理服务�?
 */
@Injectable({
  providedIn: 'root',
})
export class TokenService {
  private readonly API_BASE_URL = '/api/token';

  constructor(private http: HttpClient) {}

  // ==================== Token 套餐管理 ====================

  /**
   * 获取所有可用的 Token 套餐列表
   * @param packageType 套餐类型过滤（可选）
   * @param billingCycle 计费周期过滤（可选）
   */
  getTokenPackages(
    packageType?: PackageType,
    billingCycle?: 'one-time' | 'monthly' | 'yearly'
  ): Observable<TokenPackage[]> {
    if (USE_MOCK_DATA) {
      const mockPackages: TokenPackage[] = [
        {
          id: 'pkg001',
          name: '入门套餐',
          description: '适合个人学习和轻度使用的用户',
          tokenAmount: 100,
          priceCents: 990,
          originalPriceCents: 1990,
          discount: 0.5,
          packageType: PackageTypeEnum.ONE_TIME,
          billingCycle: 'one-time' as any,
          isActive: true,
          features: ['AI对话', '基础课程访问', '标准响应速度'],
          isPopular: true,
        },
        {
          id: 'pkg002',
          name: '标准套餐',
          description: '适合中等强度使用的用户',
          tokenAmount: 500,
          priceCents: 4990,
          originalPriceCents: 9990,
          discount: 0.5,
          packageType: PackageTypeEnum.ONE_TIME,
          billingCycle: 'one-time' as any,
          isActive: true,
          features: ['AI对话', '课程访问', '快速响应', '优先支持'],
          isPopular: false,
        },
        {
          id: 'pkg003',
          name: '专业套餐',
          description: '适合重度用户和企业团队',
          tokenAmount: 1000,
          priceCents: 9990,
          originalPriceCents: 19990,
          discount: 0.5,
          packageType: PackageTypeEnum.ONE_TIME,
          billingCycle: 'one-time' as any,
          isActive: true,
          features: ['AI对话', '课程访问', '极速响应', '专属支持', 'API访问'],
          isPopular: false,
        },
        {
          id: 'monthly001',
          name: '月度会员',
          description: '包月更划算，持续享受优惠',
          tokenAmount: 200,
          priceCents: 1990,
          originalPriceCents: undefined,
          discount: undefined,
          packageType: PackageTypeEnum.MONTHLY,
          billingCycle: 'monthly' as any,
          isActive: true,
          features: ['每月自动充值', '专属客服', '月度报表'],
          isPopular: true,
        },
      ];
      return of(mockPackages).pipe(delay(500));
    }
    const url = `${this.API_BASE_URL}/packages`;
    const params: Record<string, string> = {};

    if (packageType) {
      params['packageType'] = packageType;
    }

    if (billingCycle) {
      params['billingCycle'] = billingCycle;
    }

    return this.http.get<TokenPackage[]>(url, { params }).pipe(catchError(this.handleError));
  }

  /**
   * 获取单个套餐详情
   * @param packageId 套餐 ID
   */
  getPackageById(packageId: string): Observable<TokenPackage> {
    return this.http
      .get<TokenPackage>(`${this.API_BASE_URL}/packages/${packageId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 购买 Token 套餐
   * @param packageId 套餐 ID
   * @param paymentMethod 支付方式
   * @param couponCode 优惠券代码（可选）
   * @param userNote 用户备注（可选）
   */
  purchasePackage(
    packageId: string,
    paymentMethod: 'alipay' | 'wechat' | 'credit_card' | 'bank_transfer' | 'balance',
    couponCode?: string,
    userNote?: string
  ): Observable<CreateOrderResponse> {
    const requestBody: CreateOrderRequest = {
      packageId,
      paymentMethod,
    };

    if (couponCode) {
      requestBody.couponCode = couponCode;
    }

    if (userNote) {
      requestBody.userNote = userNote;
    }

    return this.http
      .post<CreateOrderResponse>(`${this.API_BASE_URL}/orders`, requestBody)
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== 余额查询 ====================

  /**
   * 获取用户当前 Token 余额信息
   */
  getBalance(): Observable<UserTokenBalance> {
    if (USE_MOCK_DATA) {
      const mockBalance: UserTokenBalance = {
        userId: 'user001',
        availableBalance: 1250,
        frozenBalance: 0,
        totalBalance: 1250,
        totalPurchased: 2000,
        totalConsumed: 750,
        totalRewarded: 0,
        totalRefunded: 0,
        lastPurchaseAt: '2025-03-15T10:00:00',
        lastConsumedAt: '2025-03-18T16:30:00',
      };
      return of(mockBalance).pipe(delay(100));
    }
    return this.http
      .get<UserTokenBalance>(`${this.API_BASE_URL}/balance`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 获取用户 Token 流水记录
   * @param page 页码
   * @param limit 每页数量
   */
  getTransactions(
    page: number = 1,
    limit: number = 20
  ): Observable<{
    data: TokenTransaction[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  }> {
    if (USE_MOCK_DATA) {
      const mockTransactions: TokenTransaction[] = [
        {
          id: 'txn001',
          userId: 'user001',
          type: 'income',
          amount: 1000,
          balanceAfter: 1250,
          source: 'purchase',
          description: '购买入门套餐',
          createdAt: '2025-03-15T10:00:00',
        },
        {
          id: 'txn002',
          userId: 'user001',
          type: 'expense',
          amount: -50,
          balanceAfter: 1200,
          source: 'purchase',
          description: 'AI对话消耗',
          createdAt: '2025-03-18T14:30:00',
        },
        {
          id: 'txn003',
          userId: 'user001',
          type: 'expense',
          amount: -30,
          balanceAfter: 1170,
          source: 'purchase',
          description: '课程学习消耗',
          createdAt: '2025-03-18T16:00:00',
        },
      ];
      return of({
        data: mockTransactions,
        total: 3,
        page: 1,
        limit: 20,
        totalPages: 1,
      }).pipe(delay(100));
    }
    const params = {
      page: page.toString(),
      limit: limit.toString(),
    };

    return this.http
      .get<{
        data: TokenTransaction[];
        total: number;
        page: number;
        limit: number;
        totalPages: number;
      }>(`${this.API_BASE_URL}/transactions`, { params })
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== 使用记录查询 ====================

  /**
   * 获取 Token 使用历史记录
   * @param page 页码
   * @param limit 每页数量
   * @param params 查询参数（可选）
   */
  getUsageHistory(
    page: number = 1,
    limit: number = 20,
    params?: UsageQueryParams
  ): Observable<UsageStatsResponse> {
    const queryParams: Record<string, string> = {
      page: page.toString(),
      limit: limit.toString(),
    };

    if (params) {
      if (params.startDate) queryParams['startDate'] = params.startDate;
      if (params.endDate) queryParams['endDate'] = params.endDate;
      if (params.featureType) queryParams['featureType'] = params.featureType;
      if (params.sortBy) queryParams['sortBy'] = params.sortBy;
      if (params.sortOrder) queryParams['sortOrder'] = params.sortOrder;
    }

    return this.http
      .get<UsageStatsResponse>(`${this.API_BASE_URL}/usage`, { params: queryParams })
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 获取单次使用记录详情
   * @param recordId 使用记录 ID
   */
  getUsageRecord(recordId: string): Observable<TokenUsageRecord> {
    return this.http
      .get<TokenUsageRecord>(`${this.API_BASE_URL}/usage/${recordId}`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== 统计信息 ====================

  /**
   * 获取综合统计信息
   * @param startDate 开始日期（可选）
   * @param endDate 结束日期（可选）
   */
  getStats(startDate?: string, endDate?: string): Observable<TokenStats> {
    const params: Record<string, string> = {};

    if (startDate) {
      params['startDate'] = startDate;
    }

    if (endDate) {
      params['endDate'] = endDate;
    }

    return this.http
      .get<TokenStats>(`${this.API_BASE_URL}/stats`, { params })
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 获取时间维度统计
   * @param startDate 开始日期
   * @param endDate 结束日期
   */
  getTimeStats(startDate: string, endDate: string): Observable<TokenTimeStats[]> {
    if (USE_MOCK_DATA) {
      // 生成过去7天的模拟数据
      const mockTimeStats: TokenTimeStats[] = [];
      const start = new Date(startDate);
      const end = new Date(endDate);

      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        const consumed = Math.floor(Math.random() * 50) + 10; // 10-60之间的随机消费
        const purchased = Math.random() > 0.8 ? Math.floor(Math.random() * 200) + 100 : 0; // 20%概率有充值
        const netChange = purchased - consumed;

        mockTimeStats.push({
          date: dateStr,
          consumed,
          purchased,
          netChange,
        });
      }

      return of(mockTimeStats).pipe(delay(300));
    }
    const params = {
      startDate,
      endDate,
    };

    return this.http
      .get<TokenTimeStats[]>(`${this.API_BASE_URL}/stats/time`, { params })
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 获取功能维度统计
   * @param startDate 开始日期（可选）
   * @param endDate 结束日期（可选）
   */
  getFeatureStats(startDate?: string, endDate?: string): Observable<TokenFeatureStats[]> {
    const params: Record<string, string> = {};

    if (startDate) {
      params['startDate'] = startDate;
    }

    if (endDate) {
      params['endDate'] = endDate;
    }

    return this.http
      .get<TokenFeatureStats[]>(`${this.API_BASE_URL}/stats/features`, { params })
      .pipe(catchError(this.handleError));
  }

  // ==================== 订单管理 ====================

  /**
   * 获取用户订单列表
   * @param page 页码
   * @param limit 每页数量
   * @param status 订单状态过滤（可选）
   */
  getOrders(
    page: number = 1,
    limit: number = 20,
    status?: 'pending' | 'paid' | 'failed' | 'refunded' | 'cancelled' | 'expired'
  ): Observable<{
    data: TokenOrder[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  }> {
    const params: Record<string, string> = {
      page: page.toString(),
      limit: limit.toString(),
    };

    if (status) {
      params['status'] = status;
    }

    return this.http
      .get<{
        data: TokenOrder[];
        total: number;
        page: number;
        limit: number;
        totalPages: number;
      }>(`${this.API_BASE_URL}/orders`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取订单详情
   * @param orderId 订单 ID
   */
  getOrder(orderId: string): Observable<TokenOrder> {
    return this.http
      .get<TokenOrder>(`${this.API_BASE_URL}/orders/${orderId}`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 取消订单
   * @param orderId 订单 ID
   */
  cancelOrder(orderId: string): Observable<void> {
    return this.http
      .post<void>(`${this.API_BASE_URL}/orders/${orderId}/cancel`, {})
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== 成本预估 ====================

  /**
   * 预估使用成本
   * @param params 预估参数
   */
  estimateCost(params: CostEstimateParams): Observable<CostEstimateResponse> {
    return this.http
      .post<CostEstimateResponse>(`${this.API_BASE_URL}/estimate`, params)
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== 优惠券管�?====================

  /**
   * 获取可用优惠券列�?
   */
  getAvailableCoupons(): Observable<Coupon[]> {
    return this.http
      .get<Coupon[]>(`${this.API_BASE_URL}/coupons`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 应用优惠�?
   * @param request 应用优惠券请�?
   */
  applyCoupon(request: ApplyCouponRequest): Observable<ApplyCouponResponse> {
    return this.http
      .post<ApplyCouponResponse>(`${this.API_BASE_URL}/coupons/apply`, request)
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== API Key 管理 ====================

  /**
   * 获取用户�?API Key 列表
   */
  getAPIKeys(): Observable<APIKey[]> {
    return this.http
      .get<APIKey[]>(`${this.API_BASE_URL}/api-keys`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 创建新的 API Key
   * @param request 创建 API Key 请求
   */
  createAPIKey(request: CreateAPIKeyRequest): Observable<{ apiKey: APIKey; key: string }> {
    return this.http
      .post<{ apiKey: APIKey; key: string }>(`${this.API_BASE_URL}/api-keys`, request)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 更新 API Key
   * @param keyId API Key ID
   * @param updates 更新数据
   */
  updateAPIKey(
    keyId: string,
    updates: { name?: string; permissions?: string[]; isActive?: boolean }
  ): Observable<APIKey> {
    return this.http
      .put<APIKey>(`${this.API_BASE_URL}/api-keys/${keyId}`, updates)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 删除 API Key
   * @param keyId API Key ID
   */
  deleteAPIKey(keyId: string): Observable<void> {
    return this.http
      .delete<void>(`${this.API_BASE_URL}/api-keys/${keyId}`)
      .pipe(catchError((error) => this.handleError(error)));
  }

  /**
   * 重置 API Key（生成新的密钥）
   * @param keyId API Key ID
   */
  resetAPIKey(keyId: string): Observable<{ apiKey: APIKey; key: string }> {
    return this.http
      .post<{ apiKey: APIKey; key: string }>(`${this.API_BASE_URL}/api-keys/${keyId}/reset`, {})
      .pipe(catchError((error) => this.handleError(error)));
  }

  // ==================== 辅助方法 ====================

  /**
   * 统一错误处理
   */
  private handleError(error: unknown): Observable<never> {
    let errorMessage = '操作失败';

    if (typeof error === 'object' && error !== null && 'error' in error) {
      const errorObj = error as { error?: { message?: string } };
      if (errorObj.error?.message) {
        errorMessage = errorObj.error.message;
      }
    }

    if (typeof error === 'object' && error !== null && 'status' in error) {
      const errorWithStatus = error as { status?: number };
      if (errorWithStatus.status === 401) {
        errorMessage = '未授权，请先登录';
      } else if (errorWithStatus.status === 403) {
        errorMessage = '权限不足';
      } else if (errorWithStatus.status === 404) {
        errorMessage = '资源不存在';
      } else if (errorWithStatus.status === 500) {
        errorMessage = '服务器错误';
      }
    }

    console.error('[TokenService] Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
