/**
 * 仪表板数据模型
 */

// 仪表板统计数据接口
export interface DashboardStatistics {
  /** 总用户数 */
  totalUsers: number;
  /** 活跃用户数 */
  activeUsers: number;
  /** 总许可证数 */
  totalLicenses: number;
  /** 活跃许可证数 */
  activeLicenses: number;
  /** 总订阅数 */
  totalSubscriptions: number;
  /** 活跃订阅数 */
  activeSubscriptions: number;
  /** 总收入 */
  totalRevenue: number;
  /** 本月收入 */
  monthlyRevenue: number;
  /** 总AI请求数 */
  totalAIRequests: number;
  /** 成功AI请求数 */
  successfulAIRequests: number;
}

// 图表数据点接口
export interface ChartDataPoint {
  /** 时间戳或标签 */
  label: string;
  /** 数值 */
  value: number;
}

// 趋势数据接口
export interface TrendData {
  /** 数据点数组 */
  dataPoints: ChartDataPoint[];
  /** 趋势方向 */
  trendDirection: 'up' | 'down' | 'stable';
  /** 趋势百分比 */
  trendPercentage: number;
}

// 仪表板概览数据接口
export interface DashboardOverview {
  /** 统计数据 */
  statistics: DashboardStatistics;
  /** 用户增长趋势 */
  userGrowthTrend: TrendData;
  /** 收入趋势 */
  revenueTrend: TrendData;
  /** AI使用趋势 */
  aiUsageTrend: TrendData;
  /** 许可证状态分布 */
  licenseStatusDistribution: {
    active: number;
    expired: number;
    revoked: number;
  };
  /** 订阅计划分布 */
  subscriptionPlanDistribution: {
    basic: number;
    professional: number;
    enterprise: number;
  };
}

// 筛选条件接口
export interface DashboardFilter {
  /** 时间范围 */
  dateRange: {
    startDate: Date;
    endDate: Date;
  };
  /** 数据维度 */
  dimensions: string[];
  /** 用户角色过滤 */
  userRoles?: string[];
}

// 导出数据接口
export interface ExportData {
  /** 文件名 */
  fileName: string;
  /** 数据内容 */
  data: Record<string, unknown>[];
  /** 导出格式 */
  format: 'pdf' | 'excel';
}

// 权限配置接口
export interface PermissionConfig {
  /** 角色 */
  role: string;
  /** 可访问的数据类型 */
  accessibleDataTypes: string[];
  /** 可见的图表类型 */
  visibleChartTypes: string[];
  /** 可导出的数据范围 */
  exportableDataRange: string;
}

// 仪表板服务接口
export interface DashboardServiceInterface {
  /** 获取仪表板概览数据 */
  getDashboardOverview(filter?: DashboardFilter): Promise<DashboardOverview>;
  /** 获取实时统计数据 */
  getRealTimeStatistics(filter?: DashboardFilter): Promise<DashboardStatistics>;
  /** 获取历史趋势数据 */
  getHistoricalTrends(
    days?: number,
    filter?: DashboardFilter
  ): Promise<{
    userTrend: ChartDataPoint[];
    revenueTrend: ChartDataPoint[];
    aiRequestTrend: ChartDataPoint[];
  }>;
  /** 导出数据 */
  exportData(data: ExportData): Promise<void>;
  /** 检查权限 */
  checkPermission(requiredPermission: string): boolean;
}
