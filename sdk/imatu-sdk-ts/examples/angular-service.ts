// Angular服务示例 - 展示如何在Angular项目中使用SDK
import { Injectable } from '@angular/core';
import { Observable, from } from 'rxjs';
import { map } from 'rxjs/operators';
import { createSDK, SDKInstance, User, Course, CodeGenerationRequest } from '@imatuproject/sdk';

@Injectable({
  providedIn: 'root'
})
export class ImatuApiService {
  private sdk: SDKInstance;

  constructor() {
    // 初始化SDK
    this.sdk = createSDK({
      baseURL: 'http://localhost:8000',
      timeout: 10000,
      onUnauthorized: () => {
        // 处理未授权情况，比如跳转到登录页面
        console.warn('用户未授权，请重新登录');
        // this.router.navigate(['/login']);
      }
    });
  }

  // 认证相关方法
  login(username: string, password: string): Observable<any> {
    return from(this.sdk.auth.login({ username, password }));
  }

  logout(): Observable<void> {
    return from(this.sdk.auth.logout());
  }

  // 用户相关方法
  getCurrentUser(): Observable<User> {
    return from(this.sdk.users.getCurrentUser()).pipe(
      map(response => response.data!)
    );
  }

  getUsers(page: number = 1, limit: number = 20): Observable<{ users: User[], total: number }> {
    return from(this.sdk.users.getUsers({ page, limit })).pipe(
      map(response => ({
        users: response.data!.data,
        total: response.data!.total
      }))
    );
  }

  // 课程相关方法
  getCourseById(id: string): Observable<Course> {
    return from(this.sdk.courses.getCourseById(id)).pipe(
      map(response => response.data!)
    );
  }

  searchCourses(query: string, page: number = 1): Observable<{ courses: Course[], total: number }> {
    return from(this.sdk.courses.searchCourses(query, { page, limit: 20 })).pipe(
      map(response => ({
        courses: response.data!.data,
        total: response.data!.total
      }))
    );
  }

  // AI相关方法
  generateCode(request: CodeGenerationRequest): Observable<any> {
    return from(this.sdk.ai.generateCode(request)).pipe(
      map(response => response.data!)
    );
  }

  // 访问令牌管理
  setAccessToken(token: string): void {
    this.sdk.setAccessToken(token);
  }

  clearAccessToken(): void {
    this.sdk.clearAccessToken();
  }
}