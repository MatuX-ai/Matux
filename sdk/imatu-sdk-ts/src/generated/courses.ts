// Auto-generated Courses API Client

import { APIClient } from '../client';
import { BaseResponse, PaginatedResponse, Course, CreateCourseRequest, UpdateCourseRequest, Chapter, SearchParams } from '../types';

export class CoursesAPI {
  constructor(private client: APIClient) {}

  // 获取课程列表
  async getCourses(params?: SearchParams & { 
    category?: string;
    level?: string;
  }): Promise<BaseResponse<PaginatedResponse<Course>>> {
    const response = await this.client.get<PaginatedResponse<Course>>('/api/v1/courses', { params });
    return response.data;
  }

  // 获取单个课程
  async getCourseById(id: string): Promise<BaseResponse<Course>> {
    const response = await this.client.get<Course>(`/api/v1/courses/${id}`);
    return response.data;
  }

  // 创建课程
  async createCourse(courseData: CreateCourseRequest): Promise<BaseResponse<Course>> {
    const response = await this.client.post<Course>('/api/v1/courses', courseData);
    return response.data;
  }

  // 更新课程
  async updateCourse(id: string, courseData: UpdateCourseRequest): Promise<BaseResponse<Course>> {
    const response = await this.client.put<Course>(`/api/v1/courses/${id}`, courseData);
    return response.data;
  }

  // 删除课程
  async deleteCourse(id: string): Promise<BaseResponse<void>> {
    const response = await this.client.delete<void>(`/api/v1/courses/${id}`);
    return response.data;
  }

  // 获取课程章节
  async getCourseChapters(courseId: string): Promise<BaseResponse<Chapter[]>> {
    const response = await this.client.get<Chapter[]>(`/api/v1/courses/${courseId}/chapters`);
    return response.data;
  }

  // 注册课程
  async enrollCourse(courseId: string): Promise<BaseResponse<any>> {
    const response = await this.client.post<any>(`/api/v1/courses/${courseId}/enroll`);
    return response.data;
  }

  // 获取我的课程
  async getMyCourses(): Promise<BaseResponse<Course[]>> {
    const response = await this.client.get<Course[]>('/api/v1/courses/my');
    return response.data;
  }

  // 搜索课程
  async searchCourses(query: string, params?: Omit<SearchParams, 'q'>): Promise<BaseResponse<PaginatedResponse<Course>>> {
    const searchParams = { ...params, q: query };
    const response = await this.client.get<PaginatedResponse<Course>>('/api/v1/courses/search', { params: searchParams });
    return response.data;
  }

  // 获取课程统计信息
  async getCourseStats(courseId: string): Promise<BaseResponse<any>> {
    const response = await this.client.get<any>(`/api/v1/courses/${courseId}/stats`);
    return response.data;
  }
}

// 导出实例创建函数
export function createCoursesAPI(client: APIClient) {
  return new CoursesAPI(client);
}