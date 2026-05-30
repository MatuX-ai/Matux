/**
 * 统一价格服务
 *
 * 管理所有价格相关数据：Token套餐、订阅计划、课程价格等
 * 提供统一的价格获取、计算和格式化接口
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, combineLatest, Observable, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

import { TokenPackage } from '../../models/token.models';
import {
  CalculatePriceRequest,
  CalculatePriceResponse,
  formatPrice,
  GetPricesRequest,
  GetPricesResponse,
  PriceGroup,
  PriceType,
  PricingConfig,
  UnifiedPriceItem,
} from '../models/pricing.models';
import { SubscriptionPlan } from '../models/subscription.models';

@Injectable({
  providedIn: 'root',
})
export class PricingService {
  /** 价格配置缓存 */
  private pricingConfig$ = new BehaviorSubject<PricingConfig | null>(null);

  /** 所有价格项的缓存 */
  private allPrices$ = new BehaviorSubject<UnifiedPriceItem[]>([]);

  /** 分组价格的缓存 */
  private groupedPrices$ = new BehaviorSubject<PriceGroup[]>([]);

  /** 默认价格配置 */
  private defaultConfig: PricingConfig = {
    version: '1.0.0',
    currency: {
      default: 'CNY',
      supported: ['CNY', 'USD', 'EUR'],
    },
    groups: [],
  };

  constructor(private http: HttpClient) {
    // 初始化时加载默认配置
    this.loadDefaultPrices();
  }

  // ==================== 公共API方法 ====================

  /**
   * 获取所有价格项
   */
  getAllPrices(request?: GetPricesRequest): Observable<GetPricesResponse> {
    return this.allPrices$.pipe(
      map((items) => this.filterAndSortPrices(items, request)),
      map((filteredItems) => this.groupPrices(filteredItems)),
      map((groupedItems) => ({
        config: this.pricingConfig$.value || this.defaultConfig,
        items: this.allPrices$.value,
        groupedItems,
        metadata: {
          totalCount: this.allPrices$.value.length,
          filteredCount: groupedItems.reduce((sum, group) => sum + group.items.length, 0),
          currency: this.defaultConfig.currency.default,
        },
      }))
    );
  }

  /**
   * 获取特定类型的价格项
   */
  getPricesByType(type: PriceType, request?: GetPricesRequest): Observable<UnifiedPriceItem[]> {
    return this.getAllPrices({
      ...request,
      types: [type],
    }).pipe(map((response) => response.items.filter((item) => item.type === type)));
  }

  /**
   * 获取分组价格
   */
  getGroupedPrices(): Observable<PriceGroup[]> {
    return this.groupedPrices$.asObservable();
  }

  /**
   * 获取价格配置
   */
  getPricingConfig(): Observable<PricingConfig> {
    return this.pricingConfig$.pipe(map((config) => config || this.defaultConfig));
  }

  /**
   * 根据ID获取价格项
   */
  getPriceItemById(id: string): Observable<UnifiedPriceItem | null> {
    return this.allPrices$.pipe(map((items) => items.find((item) => item.id === id) || null));
  }

  /**
   * 计算价格
   */
  calculatePrice(request: CalculatePriceRequest): Observable<CalculatePriceResponse> {
    return this.getPriceItemById(request.itemId).pipe(
      map((item) => {
        if (!item) {
          throw new Error(`未找到价格项: ${request.itemId}`);
        }

        const quantity = request.quantity || 1;
        const subtotal = item.price.current * quantity;

        // 简单折扣计算（实际项目中可能更复杂）
        const discountRate = item.price.discount || 0;
        const discountAmount = Math.round(subtotal * discountRate);
        const finalPrice = subtotal - discountAmount;

        return {
          originalPrice: subtotal,
          discountAmount,
          finalPrice,
          currency: item.price.currency,
          breakdown: {
            itemPrice: item.price.current,
            quantity,
            subtotal,
            discount: discountAmount,
            tax: 0,
            serviceFee: 0,
          },
          appliedPromotions: discountRate > 0 ? ['item_discount'] : [],
        };
      })
    );
  }

  /**
   * 格式化价格显示
   */
  formatPrice(priceCents: number, currency?: string): string {
    return formatPrice(priceCents, currency);
  }

  /**
   * 获取价格比较
   */
  comparePrices(itemIdA: string, itemIdB: string): Observable<any> {
    return combineLatest([this.getPriceItemById(itemIdA), this.getPriceItemById(itemIdB)]).pipe(
      map(([itemA, itemB]) => {
        if (!itemA || !itemB) {
          throw new Error('比较的价格项不存在');
        }

        const priceA = itemA.price.current;
        const priceB = itemB.price.current;
        const priceDifference = priceB - priceA;
        const priceDifferencePercentage = priceA > 0 ? (priceDifference / priceA) * 100 : 0;

        // 简单的性价比计算（根据功能和价格）
        const featuresA = itemA.features?.length || 0;
        const featuresB = itemB.features?.length || 0;
        const valueScoreA = priceA > 0 ? featuresA / priceA : Infinity;
        const valueScoreB = priceB > 0 ? featuresB / priceB : Infinity;

        return {
          itemA,
          itemB,
          priceDifference,
          priceDifferencePercentage,
          valueScore: {
            a: valueScoreA,
            b: valueScoreB,
            winner: valueScoreA > valueScoreB ? 'a' : valueScoreB > valueScoreA ? 'b' : 'tie',
          },
        };
      })
    );
  }

  /**
   * 刷新价格数据
   */
  refreshPrices(): Observable<boolean> {
    return this.loadPricesFromServer().pipe(
      tap((success) => {
        if (success) {
          console.log('价格数据刷新成功');
        }
      }),
      catchError((error) => {
        console.error('刷新价格数据失败:', error);
        return of(false);
      })
    );
  }

  // ==================== 私有方法 ====================

  /**
   * 加载默认价格数据
   */
  private loadDefaultPrices(): void {
    // 从多个来源加载价格数据并统一格式
    const tokenPackages = this.getDefaultTokenPackages();
    const subscriptionPlans = this.getDefaultSubscriptionPlans();
    const contentPrices = this.getDefaultContentPrices();

    const allPrices: UnifiedPriceItem[] = [
      ...tokenPackages,
      ...subscriptionPlans,
      ...contentPrices,
    ];

    this.allPrices$.next(allPrices);
    this.groupedPrices$.next(this.groupPrices(allPrices));

    // 更新配置
    const config: PricingConfig = {
      ...this.defaultConfig,
      groups: this.createDefaultGroups(),
    };
    this.pricingConfig$.next(config);
  }

  /**
   * 从服务器加载价格数据
   */
  private loadPricesFromServer(): Observable<boolean> {
    // 实际项目中这里会调用API
    // return this.http.get<PricingConfig>('/api/v1/pricing/config').pipe(
    //   tap(config => {
    //     this.pricingConfig$.next(config);
    //     // 根据配置加载具体价格项
    //   }),
    //   map(() => true),
    //   catchError(() => of(false))
    // );

    // 暂时返回成功
    return of(true);
  }

  /**
   * 过滤和排序价格项
   */
  private filterAndSortPrices(
    items: UnifiedPriceItem[],
    request?: GetPricesRequest
  ): UnifiedPriceItem[] {
    let filtered = [...items];

    // 类型过滤
    if (request?.types?.length) {
      filtered = filtered.filter((item) => request.types!.includes(item.type));
    }

    // 层级过滤
    if (request?.tiers?.length) {
      filtered = filtered.filter((item) => item.tier && request.tiers!.includes(item.tier));
    }

    // 启用状态过滤
    if (request?.activeOnly) {
      filtered = filtered.filter((item) => item.isActive);
    }

    // 推荐状态过滤
    if (request?.recommendedOnly) {
      filtered = filtered.filter((item) => item.isRecommended);
    }

    // 排序
    if (request?.sortBy) {
      filtered.sort((a, b) => {
        let valueA, valueB;

        switch (request.sortBy) {
          case 'price':
            valueA = a.price.current;
            valueB = b.price.current;
            break;
          case 'name':
            valueA = a.name;
            valueB = b.name;
            break;
          case 'tier':
            valueA = a.tier || '';
            valueB = b.tier || '';
            break;
          case 'popularity':
            valueA = a.isPopular ? 1 : 0;
            valueB = b.isPopular ? 1 : 0;
            break;
          default:
            return 0;
        }

        const order = request.sortOrder === 'desc' ? -1 : 1;
        if (valueA < valueB) return -1 * order;
        if (valueA > valueB) return 1 * order;
        return 0;
      });
    }

    return filtered;
  }

  /**
   * 分组价格项
   */
  private groupPrices(items: UnifiedPriceItem[]): PriceGroup[] {
    const groups: PriceGroup[] = [];

    // 按类型分组
    const byType = new Map<PriceType, UnifiedPriceItem[]>();
    items.forEach((item) => {
      if (!byType.has(item.type)) {
        byType.set(item.type, []);
      }
      byType.get(item.type)!.push(item);
    });

    // 转换为PriceGroup
    byType.forEach((groupItems, type) => {
      const group: PriceGroup = {
        id: `group_${type}`,
        name: this.getGroupName(type),
        type,
        items: groupItems.sort((a, b) => a.price.current - b.price.current),
        sortWeight: this.getGroupSortWeight(type),
      };

      // 设置默认选中项（第一个启用的）
      const defaultItem = group.items.find((item) => item.isActive);
      if (defaultItem) {
        group.defaultItemId = defaultItem.id;
      }

      groups.push(group);
    });

    // 按权重排序
    return groups.sort((a, b) => a.sortWeight - b.sortWeight);
  }

  /**
   * 获取分组名称
   */
  private getGroupName(type: PriceType): string {
    const nameMap = {
      [PriceType.TOKEN_PACKAGE]: 'Token 套餐',
      [PriceType.SUBSCRIPTION_PLAN]: '订阅计划',
      [PriceType.CONTENT_PRICE]: '课程价格',
      [PriceType.PRODUCT_PACKAGE]: '产品套餐',
    };
    return nameMap[type] || '其他';
  }

  /**
   * 获取分组排序权重
   */
  private getGroupSortWeight(type: PriceType): number {
    const weightMap = {
      [PriceType.PRODUCT_PACKAGE]: 1,
      [PriceType.SUBSCRIPTION_PLAN]: 2,
      [PriceType.TOKEN_PACKAGE]: 3,
      [PriceType.CONTENT_PRICE]: 4,
    };
    return weightMap[type] || 99;
  }

  /**
   * 创建默认分组
   */
  private createDefaultGroups(): PriceGroup[] {
    return [
      {
        id: 'group_product',
        name: '产品套餐',
        type: PriceType.PRODUCT_PACKAGE,
        items: [],
        sortWeight: 1,
      },
      {
        id: 'group_subscription',
        name: '订阅计划',
        type: PriceType.SUBSCRIPTION_PLAN,
        items: [],
        sortWeight: 2,
      },
      {
        id: 'group_token',
        name: 'Token 套餐',
        type: PriceType.TOKEN_PACKAGE,
        items: [],
        sortWeight: 3,
      },
    ];
  }

  // ==================== 默认数据生成 ====================

  /**
   * 获取默认Token套餐
   */
  private getDefaultTokenPackages(): UnifiedPriceItem[] {
    return [
      {
        id: 'token_starter',
        type: PriceType.TOKEN_PACKAGE,
        name: '入门套餐',
        description: '适合初次体验的用户',
        price: {
          current: 9900, // ¥99
          original: 14900, // ¥149
          currency: 'CNY',
          billingCycle: 'one_time' as any,
          discount: 0.34,
        },
        tier: 'basic' as any,
        isPopular: true,
        isRecommended: true,
        isActive: true,
        features: ['1000 Token', '基础AI功能', '7天有效'],
        metadata: {
          tokenAmount: 1000,
          validityDays: 7,
        },
      },
      {
        id: 'token_pro',
        type: PriceType.TOKEN_PACKAGE,
        name: '专业套餐',
        description: '适合经常使用的用户',
        price: {
          current: 29900, // ¥299
          original: 39900, // ¥399
          currency: 'CNY',
          billingCycle: 'one_time' as any,
          discount: 0.25,
        },
        tier: 'professional' as any,
        isPopular: true,
        isRecommended: false,
        isActive: true,
        features: ['5000 Token', '高级AI功能', '30天有效', '优先支持'],
        metadata: {
          tokenAmount: 5000,
          validityDays: 30,
        },
      },
    ];
  }

  /**
   * 获取默认订阅计划
   */
  private getDefaultSubscriptionPlans(): UnifiedPriceItem[] {
    return [
      {
        id: 'sub_basic',
        type: PriceType.SUBSCRIPTION_PLAN,
        name: '基础版',
        description: '适合个人学习使用',
        price: {
          current: 2990, // ¥29.9
          currency: 'CNY',
          billingCycle: 'monthly' as any,
        },
        tier: 'basic' as any,
        isPopular: false,
        isRecommended: false,
        isActive: true,
        features: ['基础课程访问', '社区支持', '每月更新'],
        metadata: {
          trialDays: 7,
          planId: 'basic',
        },
      },
      {
        id: 'sub_pro',
        type: PriceType.SUBSCRIPTION_PLAN,
        name: '专业版',
        description: '适合专业开发者',
        price: {
          current: 9990, // ¥99.9
          original: 12990, // ¥129.9
          currency: 'CNY',
          billingCycle: 'monthly' as any,
          discount: 0.23,
        },
        tier: 'professional' as any,
        isPopular: true,
        isRecommended: true,
        isActive: true,
        features: ['所有课程访问', '一对一指导', '项目实战', '优先支持'],
        metadata: {
          trialDays: 14,
          planId: 'professional',
        },
      },
    ];
  }

  /**
   * 获取默认课程价格
   */
  private getDefaultContentPrices(): UnifiedPriceItem[] {
    return [
      {
        id: 'course_python',
        type: PriceType.CONTENT_PRICE,
        name: 'Python全栈开发实战',
        description: '从零开始学习Python全栈开发',
        price: {
          current: 19900, // ¥199
          original: 29900, // ¥299
          currency: 'CNY',
          billingCycle: 'one_time' as any,
          discount: 0.33,
        },
        tier: 'professional' as any,
        isPopular: true,
        isRecommended: true,
        isActive: true,
        features: ['完整项目实战', '源代码下载', '终身访问'],
        metadata: {
          contentId: 'python_course_001',
        },
      },
    ];
  }

  // ==================== 工具方法 ====================

  /**
   * 转换Token套餐为统一格式
   */
  convertTokenPackage(tokenPackage: TokenPackage): UnifiedPriceItem {
    return {
      id: `token_${tokenPackage.id}`,
      type: PriceType.TOKEN_PACKAGE,
      name: tokenPackage.name,
      description: tokenPackage.description,
      price: {
        current: tokenPackage.priceCents,
        original: tokenPackage.originalPriceCents,
        currency: 'CNY',
        billingCycle: tokenPackage.billingCycle as any,
        discount: tokenPackage.discount,
      },
      tier: this.mapPackageTypeToTier(tokenPackage.packageType),
      isPopular: tokenPackage.isPopular,
      isRecommended: tokenPackage.isRecommended,
      isActive: tokenPackage.isActive || true,
      features: tokenPackage.features,
      limits: tokenPackage.limits,
      metadata: {
        tokenAmount: tokenPackage.tokenAmount,
        validityDays: tokenPackage.validityDays,
      },
    };
  }

  /**
   * 转换订阅计划为统一格式
   */
  convertSubscriptionPlan(plan: SubscriptionPlan): UnifiedPriceItem {
    return {
      id: `sub_${plan.planId}`,
      type: PriceType.SUBSCRIPTION_PLAN,
      name: plan.name,
      description: plan.description,
      price: {
        current: plan.price * 100, // 转换为分
        currency: plan.currency || 'CNY',
        billingCycle: plan.billingCycle as any,
      },
      tier: plan.planType as any,
      isPopular: plan.isPopular,
      isRecommended: false,
      isActive: plan.isActive,
      features: plan.features,
      limits: plan.limits,
      metadata: {
        planId: plan.planId,
        trialDays: plan.trialPeriodDays,
      },
    };
  }

  /**
   * 映射PackageType到ProductTier
   */
  private mapPackageTypeToTier(packageType: string): any {
    const map: Record<string, any> = {
      starter: 'basic',
      basic: 'basic',
      pro: 'professional',
      enterprise: 'enterprise',
      custom: 'custom',
    };
    return map[packageType] || 'custom';
  }

  /**
   * 获取分组价格数据
   */
  async getPriceGroups(): Promise<PriceGroup[]> {
    try {
      const response = await this.getAllPrices().toPromise();
      if (response?.items && response.items.length > 0) {
        return this.groupPrices(response.items);
      }
      return [];
    } catch (error) {
      console.error('获取分组价格失败:', error);
      return [];
    }
  }
}
