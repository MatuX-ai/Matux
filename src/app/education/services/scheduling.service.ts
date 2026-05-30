/**
 * 排课服务 - 提供课表相关的 API 调用
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  CourseSchedule,
  ScheduleGenerationRequest,
  ScheduleGenerationResponse,
} from '../models/scheduling.models';

@Injectable({
  providedIn: 'root',
})
export class ScheduleService {
  private apiUrl = '/api/v1/schedules';

  constructor(private http: HttpClient) {}

  /**
   * 生成课表
   */
  generateSchedule(request: ScheduleGenerationRequest): Observable<ScheduleGenerationResponse> {
    return this.http.post<ScheduleGenerationResponse>(`${this.apiUrl}/generate`, request);
  }

  /**
   * 查询课表列表
   */
  getSchedules(params?: {
    [key: string]: string | number | boolean;
  }): Observable<CourseSchedule[]> {
    let httpParams = new HttpParams();

    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] !== undefined && params[key] !== null) {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }

    return this.http.get<CourseSchedule[]>(this.apiUrl, { params: httpParams });
  }

  /**
   * 获取课表冲突
   */
  getConflicts(scheduleId?: number): Observable<unknown> {
    const params = scheduleId ? { schedule_id: scheduleId.toString() } : undefined;
    return this.http.get(`${this.apiUrl}/conflicts`, { params });
  }

  /**
   * 调整课表
   */
  adjustSchedule(scheduleId: string, newTimeSlot: { [key: string]: unknown }): Observable<unknown> {
    return this.http.put(`${this.apiUrl}/${scheduleId}/adjust`, {
      schedule_id: scheduleId,
      new_time_slot: newTimeSlot,
    });
  }

  /**
   * 获取统计信息
   */
  getStatistics(): Observable<unknown> {
    return this.http.get(`${this.apiUrl}/statistics`);
  }
}
