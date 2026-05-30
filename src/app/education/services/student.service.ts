/**
 * 学员管理服务 - 提供学员相关的 API 调用
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { StudentFilters, StudentListResponse, StudentProfile } from '../models/student.models';

@Injectable({
  providedIn: 'root',
})
export class StudentService {
  private apiUrl = '/api/v1/students';

  constructor(private http: HttpClient) {}

  /**
   * 查询学员列表
   */
  getStudents(filters?: StudentFilters): Observable<StudentListResponse> {
    let params = new HttpParams();

    if (filters) {
      Object.keys(filters).forEach((key) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
        const value = (filters as any)[key];
        if (value !== undefined && value !== null) {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
          params = params.set(key, value.toString());
        }
      });
    }

    return this.http.get<StudentListResponse>(this.apiUrl, { params });
  }

  /**
   * 获取学员详情
   */
  getStudentById(id: string): Observable<StudentProfile> {
    return this.http.get<StudentProfile>(`${this.apiUrl}/${id}`);
  }

  /**
   * 新增学员
   */
  createStudent(student: Partial<StudentProfile>): Observable<StudentProfile> {
    return this.http.post<StudentProfile>(this.apiUrl, student);
  }

  /**
   * 更新学员信息
   */
  updateStudent(id: string, student: Partial<StudentProfile>): Observable<StudentProfile> {
    return this.http.put<StudentProfile>(`${this.apiUrl}/${id}`, student);
  }

  /**
   * 删除学员
   */
  deleteStudent(id: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.apiUrl}/${id}`);
  }

  /**
   * 获取学员的家长信息
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getStudentParents(studentId: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/${studentId}/parents`);
  }
}
