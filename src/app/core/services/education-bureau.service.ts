/**
 * @deprecated 教育局管理功能将逐步迁移到 OpenMTEduInst 子项目。
 * 当前保留用于 iMato 学习端的教育局数据展示需求。
 * 未来版本中此服务将移至 OpenMTEduInst 项目维护。
 * 教育局服务
 * 提供教育局Dashboard相关API调用封装，包括区域数据概览、学校数据对比、教学质量监控等功能
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, map, retry, timeout } from 'rxjs/operators';

import { ApiResponse } from '../../models/education-management.models';

// ==================== 数据模型接口 ====================

/** 区域数据概览 */
export interface RegionalOverview {
  district_id: number;
  district_name: string;
  total_schools: number;
  total_students: number;
  total_teachers: number;
  total_classes: number;
  avg_students_per_school: number;
  avg_teachers_per_school: number;
  student_teacher_ratio: number;
  school_density_per_100k: number;
  urban_rural_breakdown: {
    urban_schools: number;
    rural_schools: number;
    urban_students: number;
    rural_students: number;
  };
  enrollment_trend: {
    current_year: number;
    previous_year: number;
    growth_rate: number;
  };
  created_at: string;
  updated_at: string;
}

/** 学校对比数据 */
export interface SchoolComparison {
  school_id: number;
  school_name: string;
  district: string;
  school_type: 'public' | 'private' | 'charter';
  establishment_year: number;
  total_students: number;
  total_teachers: number;
  teacher_student_ratio: number;
  graduation_rate: number;
  college_acceptance_rate: number;
  avg_test_score: number;
  qualification_rate: number; // 合格率
  excellent_rate: number; // 优秀率
  teacher_qualifications: {
    bachelor_degree: number;
    master_degree: number;
    phd_degree: number;
    certified_teachers: number;
  };
  resource_allocation: {
    total_funding: number;
    funding_per_student: number;
    classroom_count: number;
    lab_count: number;
    library_size: number;
  };
  performance_rank: number; // 区域排名
  created_at: string;
  updated_at: string;
}

/** 教学质量监控指标 */
export interface TeachingQualityMetric {
  metric_id: number;
  metric_name: string;
  metric_type: 'academic' | 'attendance' | 'discipline' | 'infrastructure';
  current_value: number;
  target_value: number;
  unit: string;
  status: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  trend: 'improving' | 'stable' | 'declining';
  last_updated: string;
  schools_meeting_target: number;
  schools_below_target: number;
  historical_data: Array<{
    period: string;
    value: number;
  }>;
}

/** 成绩分布统计 */
export interface ScoreDistribution {
  district_id: number;
  academic_year: string;
  subject: string;
  grade_level: string;
  total_students: number;
  score_ranges: Array<{
    range: string;
    count: number;
    percentage: number;
  }>;
  avg_score: number;
  median_score: number;
  pass_rate: number;
  excellent_rate: number;
  subject_rank: number; // 在区域中的排名
  trend_analysis: {
    compared_to_last_year: 'improved' | 'declined' | 'stable';
    improvement_rate: number;
  };
}

/** AI资源调配建议 */
export interface ResourceAllocationRecommendation {
  recommendation_id: number;
  priority_level: 'high' | 'medium' | 'low';
  category: 'staffing' | 'funding' | 'infrastructure' | 'curriculum';
  title: string;
  description: string;
  justification: string;
  suggested_action: string;
  estimated_cost: number;
  expected_impact: {
    metric: string;
    current_value: number;
    projected_value: number;
    improvement: number;
  };
  affected_schools: number[];
  timeline: {
    immediate: string[];
    short_term: string[];
    long_term: string[];
  };
  created_at: string;
}

/** 教育局Dashboard聚合数据 */
export interface EducationBureauDashboard {
  regional_overview: RegionalOverview;
  school_comparisons: SchoolComparison[];
  quality_metrics: TeachingQualityMetric[];
  score_distributions: ScoreDistribution[];
  recommendations: ResourceAllocationRecommendation[];
  alerts: Array<{
    id: number;
    type: 'performance_alert' | 'resource_alert' | 'safety_alert';
    title: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    affected_schools: number[];
    created_at: string;
  }>;
  generated_at: string;
}

/** 数据导出选项 */
export interface ExportOptions {
  format: 'excel' | 'pdf' | 'csv';
  data_type: 'overview' | 'comparisons' | 'metrics' | 'scores' | 'recommendations' | 'all';
  include_charts: boolean;
  time_range?: {
    start_date: string;
    end_date: string;
  };
}

// ==================== 服务实现 ====================

@Injectable({
  providedIn: 'root',
})
export class EducationBureauService {
  private readonly EDUCATION_BUREAU_API_BASE = '/api/v1/education_bureau';
  private readonly SIMULATION_MODE = true; // 开发环境下使用模拟数据

  constructor(private http: HttpClient) {}

  /**
   * 获取区域数据概览
   */
  getRegionalOverview(districtId: number): Observable<RegionalOverview> {
    if (this.SIMULATION_MODE) {
      return this.getSimulatedRegionalOverview(districtId);
    }

    return this.http
      .get<
        ApiResponse<RegionalOverview>
      >(`${this.EDUCATION_BUREAU_API_BASE}/district/${districtId}/overview`, { headers: this.getAuthHeaders() })
      .pipe(
        timeout(10000), // 10秒超时
        retry(2), // 失败重试2次
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取区域数据概览失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取区域数据概览失败，回退到模拟数据:', err);
          return this.getSimulatedRegionalOverview(districtId);
        })
      );
  }

  /**
   * 获取学校对比数据
   */
  getSchoolComparisons(districtId: number): Observable<SchoolComparison[]> {
    if (this.SIMULATION_MODE) {
      return this.getSimulatedSchoolComparisons(districtId);
    }

    return this.http
      .get<
        ApiResponse<SchoolComparison[]>
      >(`${this.EDUCATION_BUREAU_API_BASE}/district/${districtId}/schools/comparisons`, { headers: this.getAuthHeaders() })
      .pipe(
        timeout(15000), // 15秒超时（数据量较大）
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取学校对比数据失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取学校对比数据失败，回退到模拟数据:', err);
          return this.getSimulatedSchoolComparisons(districtId);
        })
      );
  }

  /**
   * 获取教学质量监控指标
   */
  getTeachingQualityMetrics(districtId: number): Observable<TeachingQualityMetric[]> {
    if (this.SIMULATION_MODE) {
      return this.getSimulatedTeachingQualityMetrics(districtId);
    }

    return this.http
      .get<
        ApiResponse<TeachingQualityMetric[]>
      >(`${this.EDUCATION_BUREAU_API_BASE}/district/${districtId}/quality/metrics`, { headers: this.getAuthHeaders() })
      .pipe(
        timeout(10000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取教学质量监控指标失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取教学质量监控指标失败，回退到模拟数据:', err);
          return this.getSimulatedTeachingQualityMetrics(districtId);
        })
      );
  }

  /**
   * 获取成绩分布统计
   */
  getScoreDistributions(districtId: number): Observable<ScoreDistribution[]> {
    if (this.SIMULATION_MODE) {
      return this.getSimulatedScoreDistributions(districtId);
    }

    return this.http
      .get<
        ApiResponse<ScoreDistribution[]>
      >(`${this.EDUCATION_BUREAU_API_BASE}/district/${districtId}/scores/distributions`, { headers: this.getAuthHeaders() })
      .pipe(
        timeout(15000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取成绩分布统计失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取成绩分布统计失败，回退到模拟数据:', err);
          return this.getSimulatedScoreDistributions(districtId);
        })
      );
  }

  /**
   * 获取AI资源调配建议
   */
  getResourceRecommendations(districtId: number): Observable<ResourceAllocationRecommendation[]> {
    if (this.SIMULATION_MODE) {
      return this.getSimulatedResourceRecommendations(districtId);
    }

    return this.http
      .get<
        ApiResponse<ResourceAllocationRecommendation[]>
      >(`${this.EDUCATION_BUREAU_API_BASE}/district/${districtId}/recommendations`, { headers: this.getAuthHeaders() })
      .pipe(
        timeout(12000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取资源调配建议失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取资源调配建议失败，回退到模拟数据:', err);
          return this.getSimulatedResourceRecommendations(districtId);
        })
      );
  }

  /**
   * 获取教育局Dashboard完整数据
   */
  getEducationBureauDashboard(districtId: number): Observable<EducationBureauDashboard> {
    if (this.SIMULATION_MODE) {
      return this.getSimulatedDashboard(districtId);
    }

    return this.http
      .get<
        ApiResponse<EducationBureauDashboard>
      >(`${this.EDUCATION_BUREAU_API_BASE}/district/${districtId}/dashboard`, { headers: this.getAuthHeaders() })
      .pipe(
        timeout(20000), // 20秒超时（完整Dashboard数据）
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取教育局Dashboard失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取教育局Dashboard失败，回退到模拟数据:', err);
          return this.getSimulatedDashboard(districtId);
        })
      );
  }

  /**
   * 导出数据报表
   */
  exportReport(options: ExportOptions): Observable<Blob> {
    if (this.SIMULATION_MODE) {
      console.log('模拟数据导出:', options);
      // 返回模拟的Excel文件
      return of(
        new Blob(['Simulated export data'], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
      );
    }

    return this.http
      .post(`${this.EDUCATION_BUREAU_API_BASE}/export`, options, {
        headers: this.getAuthHeaders(),
        responseType: 'blob',
      })
      .pipe(
        timeout(30000), // 30秒超时（生成报表可能需要时间）
        retry(1),
        catchError((err) => {
          console.error('数据导出失败:', err);
          throw new Error('数据导出失败，请稍后重试');
        })
      );
  }

  /**
   * 获取授权头信息
   */
  private getAuthHeaders(): Record<string, string> {
    // TODO: 从AuthService获取实际的token
    const token = localStorage.getItem('access_token') || 'mock-token-for-development';
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  // ==================== 模拟数据方法 ====================

  private getSimulatedRegionalOverview(districtId: number): Observable<RegionalOverview> {
    const overview: RegionalOverview = {
      district_id: districtId,
      district_name: '示例行政区',
      total_schools: 24,
      total_students: 15680,
      total_teachers: 980,
      total_classes: 420,
      avg_students_per_school: 653.33,
      avg_teachers_per_school: 40.83,
      student_teacher_ratio: 16.0,
      school_density_per_100k: 3.8,
      urban_rural_breakdown: {
        urban_schools: 16,
        rural_schools: 8,
        urban_students: 11200,
        rural_students: 4480,
      },
      enrollment_trend: {
        current_year: 15680,
        previous_year: 15200,
        growth_rate: 3.16,
      },
      created_at: '2026-03-21T10:00:00Z',
      updated_at: '2026-03-21T10:00:00Z',
    };

    return of(overview);
  }

  private getSimulatedSchoolComparisons(districtId: number): Observable<SchoolComparison[]> {
    const schools: SchoolComparison[] = [
      {
        school_id: 1,
        school_name: '第一中学',
        district: '东城区',
        school_type: 'public',
        establishment_year: 1950,
        total_students: 1200,
        total_teachers: 85,
        teacher_student_ratio: 14.12,
        graduation_rate: 98.5,
        college_acceptance_rate: 92.3,
        avg_test_score: 86.5,
        qualification_rate: 94.2,
        excellent_rate: 28.5,
        teacher_qualifications: {
          bachelor_degree: 60,
          master_degree: 23,
          phd_degree: 2,
          certified_teachers: 78,
        },
        resource_allocation: {
          total_funding: 2850000,
          funding_per_student: 2375,
          classroom_count: 36,
          lab_count: 8,
          library_size: 15000,
        },
        performance_rank: 1,
        created_at: '2026-03-21T10:00:00Z',
        updated_at: '2026-03-21T10:00:00Z',
      },
      {
        school_id: 2,
        school_name: '第二中学',
        district: '西城区',
        school_type: 'public',
        establishment_year: 1965,
        total_students: 980,
        total_teachers: 68,
        teacher_student_ratio: 14.41,
        graduation_rate: 96.8,
        college_acceptance_rate: 88.7,
        avg_test_score: 82.3,
        qualification_rate: 91.5,
        excellent_rate: 22.1,
        teacher_qualifications: {
          bachelor_degree: 52,
          master_degree: 15,
          phd_degree: 1,
          certified_teachers: 62,
        },
        resource_allocation: {
          total_funding: 2150000,
          funding_per_student: 2194,
          classroom_count: 28,
          lab_count: 6,
          library_size: 12000,
        },
        performance_rank: 2,
        created_at: '2026-03-21T10:00:00Z',
        updated_at: '2026-03-21T10:00:00Z',
      },
      {
        school_id: 3,
        school_name: '实验中学',
        district: '南城区',
        school_type: 'charter',
        establishment_year: 1980,
        total_students: 750,
        total_teachers: 55,
        teacher_student_ratio: 13.64,
        graduation_rate: 99.2,
        college_acceptance_rate: 95.8,
        avg_test_score: 88.7,
        qualification_rate: 96.5,
        excellent_rate: 32.8,
        teacher_qualifications: {
          bachelor_degree: 40,
          master_degree: 14,
          phd_degree: 1,
          certified_teachers: 52,
        },
        resource_allocation: {
          total_funding: 1850000,
          funding_per_student: 2467,
          classroom_count: 24,
          lab_count: 5,
          library_size: 18000,
        },
        performance_rank: 3,
        created_at: '2026-03-21T10:00:00Z',
        updated_at: '2026-03-21T10:00:00Z',
      },
      {
        school_id: 4,
        school_name: '私立英才学校',
        district: '北城区',
        school_type: 'private',
        establishment_year: 1995,
        total_students: 600,
        total_teachers: 48,
        teacher_student_ratio: 12.5,
        graduation_rate: 100,
        college_acceptance_rate: 98.2,
        avg_test_score: 91.5,
        qualification_rate: 99.1,
        excellent_rate: 45.3,
        teacher_qualifications: {
          bachelor_degree: 35,
          master_degree: 12,
          phd_degree: 1,
          certified_teachers: 48,
        },
        resource_allocation: {
          total_funding: 3200000,
          funding_per_student: 5333,
          classroom_count: 20,
          lab_count: 4,
          library_size: 22000,
        },
        performance_rank: 4,
        created_at: '2026-03-21T10:00:00Z',
        updated_at: '2026-03-21T10:00:00Z',
      },
      {
        school_id: 5,
        school_name: '乡村中学',
        district: '郊区',
        school_type: 'public',
        establishment_year: 1975,
        total_students: 420,
        total_teachers: 32,
        teacher_student_ratio: 13.13,
        graduation_rate: 92.5,
        college_acceptance_rate: 78.3,
        avg_test_score: 75.8,
        qualification_rate: 86.2,
        excellent_rate: 15.4,
        teacher_qualifications: {
          bachelor_degree: 28,
          master_degree: 4,
          phd_degree: 0,
          certified_teachers: 25,
        },
        resource_allocation: {
          total_funding: 950000,
          funding_per_student: 2262,
          classroom_count: 16,
          lab_count: 2,
          library_size: 6000,
        },
        performance_rank: 5,
        created_at: '2026-03-21T10:00:00Z',
        updated_at: '2026-03-21T10:00:00Z',
      },
    ];

    return of(schools);
  }

  private getSimulatedTeachingQualityMetrics(
    districtId: number
  ): Observable<TeachingQualityMetric[]> {
    const metrics: TeachingQualityMetric[] = [
      {
        metric_id: 1,
        metric_name: '学生平均成绩',
        metric_type: 'academic',
        current_value: 84.6,
        target_value: 85.0,
        unit: '分数',
        status: 'good',
        trend: 'improving',
        last_updated: '2026-03-21T10:00:00Z',
        schools_meeting_target: 18,
        schools_below_target: 6,
        historical_data: [
          { period: '2025-09', value: 82.3 },
          { period: '2025-12', value: 83.5 },
          { period: '2026-03', value: 84.6 },
        ],
      },
      {
        metric_id: 2,
        metric_name: '学生出勤率',
        metric_type: 'attendance',
        current_value: 95.8,
        target_value: 96.0,
        unit: '百分比',
        status: 'good',
        trend: 'stable',
        last_updated: '2026-03-21T10:00:00Z',
        schools_meeting_target: 20,
        schools_below_target: 4,
        historical_data: [
          { period: '2025-09', value: 95.2 },
          { period: '2025-12', value: 95.6 },
          { period: '2026-03', value: 95.8 },
        ],
      },
      {
        metric_id: 3,
        metric_name: '教师专业资格达标率',
        metric_type: 'academic',
        current_value: 88.4,
        target_value: 90.0,
        unit: '百分比',
        status: 'fair',
        trend: 'improving',
        last_updated: '2026-03-21T10:00:00Z',
        schools_meeting_target: 16,
        schools_below_target: 8,
        historical_data: [
          { period: '2025-09', value: 85.6 },
          { period: '2025-12', value: 87.2 },
          { period: '2026-03', value: 88.4 },
        ],
      },
      {
        metric_id: 4,
        metric_name: '教室设施合格率',
        metric_type: 'infrastructure',
        current_value: 82.3,
        target_value: 85.0,
        unit: '百分比',
        status: 'fair',
        trend: 'declining',
        last_updated: '2026-03-21T10:00:00Z',
        schools_meeting_target: 14,
        schools_below_target: 10,
        historical_data: [
          { period: '2025-09', value: 84.5 },
          { period: '2025-12', value: 83.2 },
          { period: '2026-03', value: 82.3 },
        ],
      },
      {
        metric_id: 5,
        metric_name: '校园安全事件率',
        metric_type: 'discipline',
        current_value: 2.8,
        target_value: 2.0,
        unit: '每千名学生',
        status: 'poor',
        trend: 'stable',
        last_updated: '2026-03-21T10:00:00Z',
        schools_meeting_target: 12,
        schools_below_target: 12,
        historical_data: [
          { period: '2025-09', value: 3.2 },
          { period: '2025-12', value: 3.0 },
          { period: '2026-03', value: 2.8 },
        ],
      },
    ];

    return of(metrics);
  }

  private getSimulatedScoreDistributions(districtId: number): Observable<ScoreDistribution[]> {
    const distributions: ScoreDistribution[] = [
      {
        district_id: districtId,
        academic_year: '2025-2026',
        subject: '数学',
        grade_level: '高中三年级',
        total_students: 1250,
        score_ranges: [
          { range: '90-100', count: 280, percentage: 22.4 },
          { range: '80-89', count: 375, percentage: 30.0 },
          { range: '70-79', count: 325, percentage: 26.0 },
          { range: '60-69', count: 175, percentage: 14.0 },
          { range: '0-59', count: 95, percentage: 7.6 },
        ],
        avg_score: 78.6,
        median_score: 80.0,
        pass_rate: 92.4,
        excellent_rate: 22.4,
        subject_rank: 1,
        trend_analysis: {
          compared_to_last_year: 'improved',
          improvement_rate: 3.2,
        },
      },
      {
        district_id: districtId,
        academic_year: '2025-2026',
        subject: '语文',
        grade_level: '高中三年级',
        total_students: 1250,
        score_ranges: [
          { range: '90-100', count: 225, percentage: 18.0 },
          { range: '80-89', count: 400, percentage: 32.0 },
          { range: '70-79', count: 350, percentage: 28.0 },
          { range: '60-69', count: 200, percentage: 16.0 },
          { range: '0-59', count: 75, percentage: 6.0 },
        ],
        avg_score: 76.8,
        median_score: 78.0,
        pass_rate: 94.0,
        excellent_rate: 18.0,
        subject_rank: 2,
        trend_analysis: {
          compared_to_last_year: 'stable',
          improvement_rate: 0.8,
        },
      },
      {
        district_id: districtId,
        academic_year: '2025-2026',
        subject: '英语',
        grade_level: '高中三年级',
        total_students: 1250,
        score_ranges: [
          { range: '90-100', count: 200, percentage: 16.0 },
          { range: '80-89', count: 325, percentage: 26.0 },
          { range: '70-79', count: 400, percentage: 32.0 },
          { range: '60-69', count: 225, percentage: 18.0 },
          { range: '0-59', count: 100, percentage: 8.0 },
        ],
        avg_score: 74.5,
        median_score: 76.0,
        pass_rate: 92.0,
        excellent_rate: 16.0,
        subject_rank: 3,
        trend_analysis: {
          compared_to_last_year: 'improved',
          improvement_rate: 2.5,
        },
      },
    ];

    return of(distributions);
  }

  private getSimulatedResourceRecommendations(
    districtId: number
  ): Observable<ResourceAllocationRecommendation[]> {
    const recommendations: ResourceAllocationRecommendation[] = [
      {
        recommendation_id: 1,
        priority_level: 'high',
        category: 'staffing',
        title: '提高乡村学校教师薪酬',
        description: '乡村学校教师流失率较高，建议提高薪酬吸引和保留优秀教师',
        justification: '数据分析显示，乡村学校教师平均工资比城区低15%，离职率比城区高25%',
        suggested_action: '为乡村学校教师提供额外津贴，幅度为基本工资的10-15%',
        estimated_cost: 1800000,
        expected_impact: {
          metric: '教师流失率',
          current_value: 12.5,
          projected_value: 8.0,
          improvement: 36.0,
        },
        affected_schools: [5, 6, 7, 8],
        timeline: {
          immediate: ['制定津贴标准'],
          short_term: ['预算审批', '教师薪酬调整'],
          long_term: ['评估教师流失率变化'],
        },
        created_at: '2026-03-21T10:00:00Z',
      },
      {
        recommendation_id: 2,
        priority_level: 'medium',
        category: 'infrastructure',
        title: '更新老旧实验室设备',
        description: '部分学校实验室设备使用超过10年，影响教学质量',
        justification: '实验室设备评估报告显示，30%的设备已超期服役，维护成本逐年增加',
        suggested_action: '分批次更新物理、化学、生物实验室设备',
        estimated_cost: 3500000,
        expected_impact: {
          metric: '实验课程完成率',
          current_value: 85.0,
          projected_value: 95.0,
          improvement: 11.8,
        },
        affected_schools: [2, 5, 9, 12],
        timeline: {
          immediate: ['设备需求评估'],
          short_term: ['采购招标', '设备安装调试'],
          long_term: ['教师设备使用培训'],
        },
        created_at: '2026-03-21T10:00:00Z',
      },
      {
        recommendation_id: 3,
        priority_level: 'medium',
        category: 'curriculum',
        title: '引入STEM课程试点项目',
        description: '加强科学、技术、工程、数学教育，提升学生创新实践能力',
        justification: '国际教育评估显示，本地区学生在STEM领域的竞争力有待提升',
        suggested_action: '在5所学校开展STEM课程试点，配备专门教材和师资',
        estimated_cost: 1200000,
        expected_impact: {
          metric: 'STEM课程参与率',
          current_value: 32.0,
          projected_value: 45.0,
          improvement: 40.6,
        },
        affected_schools: [1, 3, 10, 15, 18],
        timeline: {
          immediate: ['学校选拔'],
          short_term: ['师资培训', '教材开发'],
          long_term: ['试点评估推广'],
        },
        created_at: '2026-03-21T10:00:00Z',
      },
    ];

    return of(recommendations);
  }

  private getSimulatedDashboard(districtId: number): Observable<EducationBureauDashboard> {
    return of({
      regional_overview: {
        district_id: districtId,
        district_name: '示例行政区',
        total_schools: 24,
        total_students: 15680,
        total_teachers: 980,
        total_classes: 420,
        avg_students_per_school: 653.33,
        avg_teachers_per_school: 40.83,
        student_teacher_ratio: 16.0,
        school_density_per_100k: 3.8,
        urban_rural_breakdown: {
          urban_schools: 16,
          rural_schools: 8,
          urban_students: 11200,
          rural_students: 4480,
        },
        enrollment_trend: {
          current_year: 15680,
          previous_year: 15200,
          growth_rate: 3.16,
        },
        created_at: '2026-03-21T10:00:00Z',
        updated_at: '2026-03-21T10:00:00Z',
      },
      school_comparisons: [
        {
          school_id: 1,
          school_name: '第一中学',
          district: '东城区',
          school_type: 'public',
          establishment_year: 1950,
          total_students: 1200,
          total_teachers: 85,
          teacher_student_ratio: 14.12,
          graduation_rate: 98.5,
          college_acceptance_rate: 92.3,
          avg_test_score: 86.5,
          qualification_rate: 94.2,
          excellent_rate: 28.5,
          teacher_qualifications: {
            bachelor_degree: 60,
            master_degree: 23,
            phd_degree: 2,
            certified_teachers: 78,
          },
          resource_allocation: {
            total_funding: 2850000,
            funding_per_student: 2375,
            classroom_count: 36,
            lab_count: 8,
            library_size: 15000,
          },
          performance_rank: 1,
          created_at: '2026-03-21T10:00:00Z',
          updated_at: '2026-03-21T10:00:00Z',
        },
      ],
      quality_metrics: [
        {
          metric_id: 1,
          metric_name: '学生平均成绩',
          metric_type: 'academic',
          current_value: 84.6,
          target_value: 85.0,
          unit: '分数',
          status: 'good',
          trend: 'improving',
          last_updated: '2026-03-21T10:00:00Z',
          schools_meeting_target: 18,
          schools_below_target: 6,
          historical_data: [
            { period: '2025-09', value: 82.3 },
            { period: '2025-12', value: 83.5 },
            { period: '2026-03', value: 84.6 },
          ],
        },
      ],
      score_distributions: [
        {
          district_id: districtId,
          academic_year: '2025-2026',
          subject: '数学',
          grade_level: '高中三年级',
          total_students: 1250,
          score_ranges: [
            { range: '90-100', count: 280, percentage: 22.4 },
            { range: '80-89', count: 375, percentage: 30.0 },
            { range: '70-79', count: 325, percentage: 26.0 },
            { range: '60-69', count: 175, percentage: 14.0 },
            { range: '0-59', count: 95, percentage: 7.6 },
          ],
          avg_score: 78.6,
          median_score: 80.0,
          pass_rate: 92.4,
          excellent_rate: 22.4,
          subject_rank: 1,
          trend_analysis: {
            compared_to_last_year: 'improved',
            improvement_rate: 3.2,
          },
        },
      ],
      recommendations: [
        {
          recommendation_id: 1,
          priority_level: 'high',
          category: 'staffing',
          title: '提高乡村学校教师薪酬',
          description: '乡村学校教师流失率较高，建议提高薪酬吸引和保留优秀教师',
          justification: '数据分析显示，乡村学校教师平均工资比城区低15%，离职率比城区高25%',
          suggested_action: '为乡村学校教师提供额外津贴，幅度为基本工资的10-15%',
          estimated_cost: 1800000,
          expected_impact: {
            metric: '教师流失率',
            current_value: 12.5,
            projected_value: 8.0,
            improvement: 36.0,
          },
          affected_schools: [5, 6, 7, 8],
          timeline: {
            immediate: ['制定津贴标准'],
            short_term: ['预算审批', '教师薪酬调整'],
            long_term: ['评估教师流失率变化'],
          },
          created_at: '2026-03-21T10:00:00Z',
        },
      ],
      alerts: [
        {
          id: 1,
          type: 'performance_alert',
          title: '三所学校教学质量指标下降',
          description: '第5、8、12号学校的平均成绩连续两学期下降超过5%',
          severity: 'medium',
          affected_schools: [5, 8, 12],
          created_at: '2026-03-20T14:30:00Z',
        },
      ],
      generated_at: '2026-03-21T10:00:00Z',
    });
  }
}
