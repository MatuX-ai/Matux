import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { jsPDF } from 'jspdf';
import { forkJoin, Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import * as XLSX from 'xlsx';

import { environment } from '../../../../environments/environment';
import {
  ChartDataPoint,
  DashboardFilter,
  DashboardOverview,
  DashboardStatistics,
  ExportData,
  PermissionConfig,
  TrendData,
} from '../models/dashboard.models';

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private baseUrl = `${environment.apiUrl}/api/v1`;
  private currentUserRole = 'admin'; // 当前用户角色

  // 权限配置
  private permissionConfigs: PermissionConfig[] = [
    {
      role: 'admin',
      accessibleDataTypes: ['users', 'licenses', 'subscriptions', 'payments', 'ai'],
      visibleChartTypes: ['line', 'bar', 'pie', 'doughnut'],
      exportableDataRange: 'full',
    },
    {
      role: 'manager',
      accessibleDataTypes: ['users', 'licenses', 'subscriptions'],
      visibleChartTypes: ['line', 'bar'],
      exportableDataRange: 'limited',
    },
    {
      role: 'analyst',
      accessibleDataTypes: ['users', 'ai'],
      visibleChartTypes: ['line', 'pie'],
      exportableDataRange: 'view_only',
    },
  ];

  constructor(private http: HttpClient) {}

  /**
   * 获取完整的仪表板概览数据
   */
  getDashboardOverview(filter?: DashboardFilter): Observable<DashboardOverview> {
    // 并行获取多个数据源
    return forkJoin({
      statistics: this.getRealTimeStatistics(filter),
      trends: this.getHistoricalTrends(30, filter),
      licenseStats: this.getLicenseStatistics(filter),
      subscriptionStats: this.getSubscriptionStatistics(filter),
    }).pipe(
      map(({ statistics, trends, licenseStats, subscriptionStats }) => {
        return {
          statistics,
          userGrowthTrend: this.calculateTrend(trends.userTrend),
          revenueTrend: this.calculateTrend(trends.revenueTrend),
          aiUsageTrend: this.calculateTrend(trends.aiRequestTrend),
          licenseStatusDistribution: licenseStats.statusDistribution,
          subscriptionPlanDistribution: subscriptionStats.planDistribution,
        };
      }),
      catchError((_error) => {
        // 返回默认数据以确保 UI 正常显示
        return of(this.getDefaultDashboardOverview());
      })
    );
  }

  /**
   * 获取实时统计数据
   */
  getRealTimeStatistics(filter?: DashboardFilter): Observable<DashboardStatistics> {
    // 构建查询参数
    let params = new HttpParams();
    if (filter) {
      params = params.set('startDate', filter.dateRange.startDate.toISOString().split('T')[0]);
      params = params.set('endDate', filter.dateRange.endDate.toISOString().split('T')[0]);
    }

    return this.http
      .get<{
        users?: { total?: number; active?: number };
        licenses?: { total?: number; active?: number };
        subscriptions?: { total?: number; active?: number };
        payments?: { totalRevenue?: number; monthlyRevenue?: number };
        ai?: { totalRequests?: number; successfulRequests?: number };
      }>(`${this.baseUrl}/dashboard/statistics`, { params })
      .pipe(
        // eslint-disable-next-line complexity
        map((response) => {
          return {
            totalUsers: response.users?.total ?? 0,
            activeUsers: response.users?.active ?? 0,
            totalLicenses: response.licenses?.total ?? 0,
            activeLicenses: response.licenses?.active ?? 0,
            totalSubscriptions: response.subscriptions?.total ?? 0,
            activeSubscriptions: response.subscriptions?.active ?? 0,
            totalRevenue: response.payments?.totalRevenue ?? 0,
            monthlyRevenue: response.payments?.monthlyRevenue ?? 0,
            totalAIRequests: response.ai?.totalRequests ?? 0,
            successfulAIRequests: response.ai?.successfulRequests ?? 0,
          } as DashboardStatistics;
        }),
        catchError(() => {
          // 回退到模拟数据
          return this.getMockRealTimeStatistics();
        })
      );
  }

  /**
   * 获取历史趋势数据
   */
  getHistoricalTrends(
    days: number = 30,
    filter?: DashboardFilter
  ): Observable<{
    userTrend: ChartDataPoint[];
    revenueTrend: ChartDataPoint[];
    aiRequestTrend: ChartDataPoint[];
  }> {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    // 构建查询参数
    let params = new HttpParams()
      .set('days', days.toString())
      .set('startDate', startDate.toISOString().split('T')[0])
      .set('endDate', endDate.toISOString().split('T')[0]);

    if (filter?.dimensions) {
      params = params.set('dimensions', filter.dimensions.join(','));
    }

    return this.http
      .get<{
        userTrend?: ChartDataPoint[];
        revenueTrend?: ChartDataPoint[];
        aiRequestTrend?: ChartDataPoint[];
      }>(`${this.baseUrl}/dashboard/trends`, { params })
      .pipe(
        map((response) => ({
          userTrend: response.userTrend ?? [],
          revenueTrend: response.revenueTrend ?? [],
          aiRequestTrend: response.aiRequestTrend ?? [],
        })),
        catchError(() => {
          // 回退到模拟数据
          return this.getMockHistoricalTrends(days);
        })
      );
  }

  /**
   * 计算趋势数据
   */
  private calculateTrend(dataPoints: ChartDataPoint[]): TrendData {
    if (dataPoints.length < 2) {
      return {
        dataPoints,
        trendDirection: 'stable',
        trendPercentage: 0,
      };
    }

    const firstValue = dataPoints[0].value;
    const lastValue = dataPoints[dataPoints.length - 1].value;
    const percentageChange = firstValue !== 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;

    let trendDirection: 'up' | 'down' | 'stable' = 'stable';
    if (percentageChange > 5) {
      trendDirection = 'up';
    } else if (percentageChange < -5) {
      trendDirection = 'down';
    }

    return {
      dataPoints,
      trendDirection,
      trendPercentage: Math.abs(percentageChange),
    };
  }

  /**
   * 获取默认仪表板数据（用于错误情况）
   */
  private getDefaultDashboardOverview(): DashboardOverview {
    return {
      statistics: {
        totalUsers: 0,
        activeUsers: 0,
        totalLicenses: 0,
        activeLicenses: 0,
        totalSubscriptions: 0,
        activeSubscriptions: 0,
        totalRevenue: 0,
        monthlyRevenue: 0,
        totalAIRequests: 0,
        successfulAIRequests: 0,
      },
      userGrowthTrend: {
        dataPoints: [],
        trendDirection: 'stable',
        trendPercentage: 0,
      },
      revenueTrend: {
        dataPoints: [],
        trendDirection: 'stable',
        trendPercentage: 0,
      },
      aiUsageTrend: {
        dataPoints: [],
        trendDirection: 'stable',
        trendPercentage: 0,
      },
      licenseStatusDistribution: {
        active: 0,
        expired: 0,
        revoked: 0,
      },
      subscriptionPlanDistribution: {
        basic: 0,
        professional: 0,
        enterprise: 0,
      },
    };
  }

  // 模拟数据方法
  private getMockRealTimeStatistics(): Observable<DashboardStatistics> {
    return of({
      totalUsers: 1250,
      activeUsers: 890,
      totalLicenses: 980,
      activeLicenses: 756,
      totalSubscriptions: 650,
      activeSubscriptions: 520,
      totalRevenue: 125000,
      monthlyRevenue: 15600,
      totalAIRequests: 3420,
      successfulAIRequests: 3150,
    });
  }

  private getMockHistoricalTrends(days: number): Observable<{
    userTrend: ChartDataPoint[];
    revenueTrend: ChartDataPoint[];
    aiRequestTrend: ChartDataPoint[];
  }> {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - days);

    return forkJoin({
      userTrend: this.getHistoricalUserData(startDate, endDate),
      revenueTrend: this.getHistoricalRevenueData(startDate, endDate),
      aiRequestTrend: this.getHistoricalAIRequestData(startDate, endDate),
    });
  }

  private getHistoricalUserData(startDate: Date, endDate: Date): Observable<ChartDataPoint[]> {
    // 模拟用户增长数据
    const data: ChartDataPoint[] = [];
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    for (let i = 0; i < days; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      data.push({
        label: date.toISOString().split('T')[0],
        value: 800 + Math.floor(Math.random() * 500) + i * 5,
      });
    }

    return of(data);
  }

  private getHistoricalRevenueData(startDate: Date, endDate: Date): Observable<ChartDataPoint[]> {
    // 模拟收入数据
    const data: ChartDataPoint[] = [];
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    for (let i = 0; i < days; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      data.push({
        label: date.toISOString().split('T')[0],
        value: 1000 + Math.floor(Math.random() * 2000) + i * 20,
      });
    }

    return of(data);
  }

  private getHistoricalAIRequestData(startDate: Date, endDate: Date): Observable<ChartDataPoint[]> {
    // 模拟AI请求数据
    const data: ChartDataPoint[] = [];
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    for (let i = 0; i < days; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      data.push({
        label: date.toISOString().split('T')[0],
        value: 50 + Math.floor(Math.random() * 100) + i * 3,
      });
    }

    return of(data);
  }

  // 带筛选的真实 API 调用方法
  private getLicenseStatistics(filter?: DashboardFilter): Observable<{
    total: number;
    active: number;
    statusDistribution: { active: number; expired: number; revoked: number };
  }> {
    let params = new HttpParams();
    if (filter) {
      params = params.set('startDate', filter.dateRange.startDate.toISOString().split('T')[0]);
      params = params.set('endDate', filter.dateRange.endDate.toISOString().split('T')[0]);
    }

    return this.http
      .get<{
        total?: number;
        active?: number;
        byStatus?: { active?: number; expired?: number; revoked?: number };
      }>(`${this.baseUrl}/licenses/stats`, { params })
      .pipe(
        map((response) => ({
          total: response.total ?? 0,
          active: response.active ?? 0,
          statusDistribution: {
            active: response.byStatus?.active ?? 0,
            expired: response.byStatus?.expired ?? 0,
            revoked: response.byStatus?.revoked ?? 0,
          },
        })),
        catchError(() => this.getMockLicenseStatistics())
      );
  }

  private getMockLicenseStatistics(): Observable<{
    total: number;
    active: number;
    statusDistribution: { active: number; expired: number; revoked: number };
  }> {
    return of({
      total: 980,
      active: 756,
      statusDistribution: {
        active: 756,
        expired: 180,
        revoked: 44,
      },
    });
  }

  private getSubscriptionStatistics(filter?: DashboardFilter): Observable<{
    total: number;
    active: number;
    planDistribution: { basic: number; professional: number; enterprise: number };
  }> {
    let params = new HttpParams();
    if (filter) {
      params = params.set('startDate', filter.dateRange.startDate.toISOString().split('T')[0]);
      params = params.set('endDate', filter.dateRange.endDate.toISOString().split('T')[0]);
    }

    return this.http
      .get<{
        total?: number;
        active?: number;
        byPlan?: { basic?: number; professional?: number; enterprise?: number };
      }>(`${this.baseUrl}/subscriptions/stats`, { params })
      .pipe(
        map((response) => ({
          total: response.total ?? 0,
          active: response.active ?? 0,
          planDistribution: {
            basic: response.byPlan?.basic ?? 0,
            professional: response.byPlan?.professional ?? 0,
            enterprise: response.byPlan?.enterprise ?? 0,
          },
        })),
        catchError(() => this.getMockSubscriptionStatistics())
      );
  }

  private getMockSubscriptionStatistics(): Observable<{
    total: number;
    active: number;
    planDistribution: { basic: number; professional: number; enterprise: number };
  }> {
    return of({
      total: 650,
      active: 520,
      planDistribution: {
        basic: 200,
        professional: 250,
        enterprise: 170,
      },
    });
  }

  // 导出功能
  private exportToPDF(data: ExportData): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const doc = new jsPDF();

        // 设置文档标题
        doc.setFontSize(20);
        doc.text(data.fileName, 20, 20);

        // 添加生成时间
        doc.setFontSize(12);
        doc.text(`生成时间：${new Date().toLocaleString()}`, 20, 30);

        // 添加数据表格
        if (Array.isArray(data.data) && data.data.length > 0) {
          const headers = Object.keys(data.data[0]);
          const rows = data.data.map((item) => headers.map((header) => String(item[header] || '')));

          /* eslint-disable @typescript-eslint/no-explicit-any */
          /* eslint-disable @typescript-eslint/no-unsafe-call */
          /* eslint-disable @typescript-eslint/no-unsafe-member-access */
          (doc as any).autoTable({
            head: [headers],
            body: rows,
            startY: 40,
            styles: { fontSize: 8 },
          });
          /* eslint-enable @typescript-eslint/no-explicit-any */
          /* eslint-enable @typescript-eslint/no-unsafe-call */
          /* eslint-enable @typescript-eslint/no-unsafe-member-access */
        }

        // 保存文件
        doc.save(`${data.fileName}.pdf`);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  private exportToExcel(data: ExportData): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 创建工作簿
        const workbook = XLSX.utils.book_new();

        // 将数据转换为工作表
        const worksheet = XLSX.utils.json_to_sheet(data.data);

        // 添加工作表到工作簿
        XLSX.utils.book_append_sheet(workbook, worksheet, '数据');

        // 添加元数据
        const metadata = [
          ['报告名称', data.fileName],
          ['生成时间', new Date().toLocaleString()],
          ['数据记录数', data.data.length],
        ];
        const metaSheet = XLSX.utils.aoa_to_sheet(metadata);
        XLSX.utils.book_append_sheet(workbook, metaSheet, '元数据');

        // 导出文件
        XLSX.writeFile(workbook, `${data.fileName}.xlsx`);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  exportData(data: ExportData): Promise<void> {
    switch (data.format) {
      case 'pdf':
        return this.exportToPDF(data);
      case 'excel':
        return this.exportToExcel(data);
      default:
        return Promise.reject(new Error('不支持的导出格式'));
    }
  }

  // 权限控制
  checkPermission(requiredPermission: string): boolean {
    const userConfig = this.permissionConfigs.find(
      (config) => config.role === this.currentUserRole
    );
    if (!userConfig) return false;

    // 检查数据类型权限
    if (requiredPermission.startsWith('data:')) {
      const dataType = requiredPermission.split(':')[1];
      return userConfig.accessibleDataTypes.includes(dataType);
    }

    // 检查图表类型权限
    if (requiredPermission.startsWith('chart:')) {
      const chartType = requiredPermission.split(':')[1];
      return userConfig.visibleChartTypes.includes(chartType);
    }

    // 检查导出权限
    if (requiredPermission === 'export') {
      return userConfig.exportableDataRange !== 'view_only';
    }

    return false;
  }

  getCurrentUserRole(): string {
    return this.currentUserRole;
  }

  setCurrentUserRole(role: string): void {
    this.currentUserRole = role;
  }
}
