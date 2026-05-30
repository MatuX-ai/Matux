import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

// 赞助活动接口
export interface Sponsorship {
  id: number;
  org_id: number;
  name: string;
  description: string;
  sponsor_amount: number;
  currency: string;
  start_date: string;
  end_date: string;
  status: string;
  total_exposures: number;
  total_points_earned: number;
  conversion_rate: number;
  created_at: string;
  updated_at: string;
  exposure_types: string[];
  target_audience: Record<string, unknown>;
}

// 品牌曝光接口
export interface BrandExposure {
  id: number;
  sponsorship_id: number;
  exposure_type: string;
  platform: string;
  placement: string;
  view_count: number;
  click_count: number;
  engagement_count: number;
  conversion_count: number;
  ctr: number;
  engagement_rate: number;
  exposed_at: string;
}

// 积分交易接口
export interface PointTransaction {
  id: number;
  sponsorship_id: number;
  transaction_type: string;
  points_amount: number;
  balance_before: number;
  balance_after: number;
  description: string;
  created_at: string;
}

// 转换规则接口
export interface PointConversionRule {
  id: number;
  name: string;
  points_required: number;
  reward_type: string;
  reward_value: unknown;
  min_sponsorship_amount: number;
  applicable_categories: string[];
  validity_period_days: number;
  is_active: boolean;
}

// 分析数据接口
export interface SponsorshipAnalytics {
  period_start: string;
  period_end: string;
  summary: {
    total_sponsorships: number;
    active_sponsorships: number;
    total_amount: number;
    total_exposures: number;
    total_points_earned: number;
    average_conversion_rate: number;
  };
  trends: Array<{
    date: string;
    exposures: number;
    points: number;
  }>;
  top_performing: Array<{
    id: number;
    name: string;
    exposures: number;
    points_earned: number;
    conversion_rate: number;
  }>;
}

// 仪表板数据接口
export interface DashboardData {
  summary: {
    total_sponsorships: number;
    active_sponsorships: number;
    total_sponsorship_amount: number;
    total_exposures: number;
    recent_exposures: number;
    available_points: number;
  };
  recent_activities: Array<{
    type: string;
    message: string;
    time: string;
  }>;
  trends: {
    daily_exposures: number[];
    weekly_growth: number[];
  };
}

@Injectable({
  providedIn: 'root',
})
export class SponsorshipDashboardService {
  private baseUrl = `${environment.apiUrl}/api/v1/sponsorship`;
  private currentOrgId = 1; // 默认组织ID，实际应该从认证服务获取

  constructor(private http: HttpClient) {}

  /**
   * 获取赞助活动列表
   */
  getSponsorships(
    status?: string,
    skip: number = 0,
    limit: number = 50
  ): Observable<Sponsorship[]> {
    let params = new HttpParams().set('skip', skip.toString()).set('limit', limit.toString());

    if (status) {
      params = params.set('status', status);
    }

    return this.http
      .get<
        Sponsorship[]
      >(`${this.baseUrl}/organizations/${this.currentOrgId}/sponsorships`, { params })
      .pipe(
        catchError(() => {
          return of([]);
        })
      );
  }

  /**
   * 获取单个赞助活动详情
   */
  getSponsorship(sponsorshipId: number): Observable<Sponsorship> {
    return this.http.get<Sponsorship>(`${this.baseUrl}/sponsorships/${sponsorshipId}`).pipe(
      catchError((error) => {
        throw error;
      })
    );
  }

  /**
   * 创建新的赞助活动
   */
  createSponsorship(
    sponsorshipData: Omit<
      Sponsorship,
      | 'id'
      | 'org_id'
      | 'created_at'
      | 'updated_at'
      | 'total_exposures'
      | 'total_points_earned'
      | 'conversion_rate'
    >
  ): Observable<Sponsorship> {
    return this.http
      .post<Sponsorship>(
        `${this.baseUrl}/organizations/${this.currentOrgId}/sponsorships`,
        sponsorshipData
      )
      .pipe(
        catchError((_error) => {
          throw _error;
        })
      );
  }

  /**
   * 更新赞助活动
   */
  updateSponsorship(
    sponsorshipId: number,
    updateData: Partial<Sponsorship>
  ): Observable<Sponsorship> {
    return this.http
      .put<Sponsorship>(`${this.baseUrl}/sponsorships/${sponsorshipId}`, updateData)
      .pipe(
        catchError((_error) => {
          throw _error;
        })
      );
  }

  /**
   * 获取品牌曝光记录
   */
  getBrandExposures(
    sponsorshipId: number,
    exposureType?: string,
    startDate?: string,
    endDate?: string,
    skip: number = 0,
    limit: number = 50
  ): Observable<BrandExposure[]> {
    let params = new HttpParams().set('skip', skip.toString()).set('limit', limit.toString());

    if (exposureType) {
      params = params.set('exposure_type', exposureType);
    }
    if (startDate) {
      params = params.set('start_date', startDate);
    }
    if (endDate) {
      params = params.set('end_date', endDate);
    }

    return this.http
      .get<BrandExposure[]>(`${this.baseUrl}/sponsorships/${sponsorshipId}/exposures`, { params })
      .pipe(
        catchError(() => {
          return of([]);
        })
      );
  }

  /**
   * 记录品牌曝光
   */
  recordBrandExposure(
    sponsorshipId: number,
    exposureData: Omit<BrandExposure, 'id' | 'sponsorship_id' | 'ctr' | 'engagement_rate'>
  ): Observable<void> {
    return this.http
      .post<void>(`${this.baseUrl}/sponsorships/${sponsorshipId}/exposures`, exposureData)
      .pipe(
        catchError((_error) => {
          throw _error;
        })
      );
  }

  /**
   * 获取积分余额
   */
  getPointsBalance(sponsorshipId: number): Observable<{ available_points: number }> {
    return this.http
      .get<{
        available_points: number;
      }>(`${this.baseUrl}/sponsorships/${sponsorshipId}/points/balance`)
      .pipe(
        catchError((_error) => {
          return of({ available_points: 0 });
        })
      );
  }

  /**
   * 获取积分转换规则
   */
  getConversionRules(
    isActive: boolean = true,
    category?: string
  ): Observable<PointConversionRule[]> {
    let params = new HttpParams().set('is_active', isActive.toString());
    if (category) {
      params = params.set('category', category);
    }

    return this.http
      .get<PointConversionRule[]>(`${this.baseUrl}/points/conversion-rules`, { params })
      .pipe(
        catchError(() => {
          return of([]);
        })
      );
  }

  /**
   * 转换积分
   */
  convertPoints(
    sponsorshipId: number,
    ruleId: number,
    quantity: number = 1
  ): Observable<{ success: boolean; message?: string; data?: unknown }> {
    return this.http
      .post<{ success: boolean; message?: string; data?: unknown }>(
        `${this.baseUrl}/sponsorships/${sponsorshipId}/points/convert`,
        {
          rule_id: ruleId,
          quantity,
        }
      )
      .pipe(
        catchError((_error) => {
          throw _error;
        })
      );
  }

  /**
   * 获取赞助分析数据
   */
  getAnalytics(startDate?: string, endDate?: string): Observable<SponsorshipAnalytics> {
    let params = new HttpParams();
    if (startDate) {
      params = params.set('start_date', startDate);
    }
    if (endDate) {
      params = params.set('end_date', endDate);
    }

    return this.http
      .get<SponsorshipAnalytics>(`${this.baseUrl}/organizations/${this.currentOrgId}/analytics`, {
        params,
      })
      .pipe(
        catchError(() => {
          // 返回模拟数据
          return of(this.getMockAnalyticsData());
        })
      );
  }

  /**
   * 获取仪表板数据
   */
  getDashboardData(days: number = 30): Observable<DashboardData> {
    const params = new HttpParams().set('days', days.toString());

    return this.http
      .get<DashboardData>(`${this.baseUrl}/organizations/${this.currentOrgId}/dashboard`, {
        params,
      })
      .pipe(
        catchError(() => {
          // 返回模拟数据
          return of(this.getMockDashboardData());
        })
      );
  }

  /**
   * 获取模拟分析数据（用于开发测试）
   */
  private getMockAnalyticsData(): SponsorshipAnalytics {
    return {
      period_start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      period_end: new Date().toISOString(),
      summary: {
        total_sponsorships: 12,
        active_sponsorships: 8,
        total_amount: 150000,
        total_exposures: 250000,
        total_points_earned: 15000,
        average_conversion_rate: 3.2,
      },
      trends: [
        { date: '2026-02-01', exposures: 5000, points: 300 },
        { date: '2026-02-02', exposures: 5200, points: 320 },
        { date: '2026-02-03', exposures: 4800, points: 280 },
        { date: '2026-02-04', exposures: 5500, points: 350 },
        { date: '2026-02-05', exposures: 5100, points: 310 },
      ],
      top_performing: [
        {
          id: 1,
          name: '教育科技赞助计划',
          exposures: 50000,
          points_earned: 2500,
          conversion_rate: 4.5,
        },
        {
          id: 2,
          name: 'AI创新大赛赞助',
          exposures: 45000,
          points_earned: 2200,
          conversion_rate: 3.8,
        },
        {
          id: 3,
          name: '编程教育公益项目',
          exposures: 40000,
          points_earned: 2000,
          conversion_rate: 3.2,
        },
      ],
    };
  }

  /**
   * 获取模拟仪表板数据（用于开发测试）
   */
  private getMockDashboardData(): DashboardData {
    return {
      summary: {
        total_sponsorships: 12,
        active_sponsorships: 8,
        total_sponsorship_amount: 150000,
        total_exposures: 250000,
        recent_exposures: 15000,
        available_points: 8500,
      },
      recent_activities: [
        { type: 'exposure', message: '新增横幅广告曝光 5,000 次', time: '2小时前' },
        { type: 'conversion', message: '积分转换成功：教育资源捐赠', time: '5小时前' },
        { type: 'sponsorship', message: '新赞助活动创建：AI创新实验室', time: '1天前' },
      ],
      trends: {
        daily_exposures: [4500, 4800, 5200, 4900, 5100, 5300, 4700],
        weekly_growth: [2.5, 3.1, 2.8, 3.5, 4.2, 3.8, 4.1],
      },
    };
  }

  /**
   * 设置当前组织ID
   */
  setCurrentOrgId(orgId: number): void {
    this.currentOrgId = orgId;
  }

  /**
   * 获取当前组织ID
   */
  getCurrentOrgId(): number {
    return this.currentOrgId;
  }
}
