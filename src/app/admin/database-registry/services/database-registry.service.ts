import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, throwError, timer } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

// Models
export interface ModuleInfo {
  name: string;
  table_name: string;
  category: string;
  version: string;
  description?: string;
  dependencies: string[];
  is_active: boolean;
  has_instance: boolean;
  is_initialized: boolean;
  class_name: string;
}

export interface RegistryStats {
  registry_stats: {
    total_modules: number;
    active_modules: number;
    inactive_modules: number;
    total_instances: number;
    categories: number;
    tables: number;
    initialized: boolean;
  };
  modules_by_category: { [key: string]: ModuleInfo[] };
  total_categories: number;
  mode?: string;
}

export interface RegistryHealth {
  registry_status: 'healthy' | 'degraded' | 'uninitialized';
  stats: any;
  modules_status: Array<{
    name: string;
    registered: boolean;
    instance_created: boolean;
    initialized: boolean;
    active: boolean;
  }>;
  issues: string[];
  status?: string;
  database_registry_error?: string;
}

@Injectable({
  providedIn: 'root',
})
export class DatabaseRegistryService {
  private readonly baseUrl = '/api/v1'; // 根据实际API路径调整
  private refreshSubject = new BehaviorSubject<void>(undefined);

  constructor(private http: HttpClient) {}

  // 获取注册表统计信息
  getRegistryStats(): Observable<RegistryStats> {
    return this.http
      .get<RegistryStats>(`${this.baseUrl}/registry/stats`)
      .pipe(catchError(this.handleError));
  }

  // 获取注册表健康状态
  getRegistryHealth(): Observable<RegistryHealth> {
    return this.http.get<any>(`${this.baseUrl}/health`).pipe(
      map((response) => {
        // 处理不同的响应格式
        if (response.database_registry) {
          return response.database_registry as RegistryHealth;
        } else if (response.registry_status) {
          return response as RegistryHealth;
        } else {
          // 如果都不匹配，返回一个基本的健康状态
          return {
            registry_status: 'healthy' as const,
            stats: response,
            modules_status: [],
            issues: [],
          };
        }
      }),
      catchError(this.handleError)
    );
  }

  // 获取所有注册模块
  getRegistryModules(category?: string): Observable<ModuleInfo[]> {
    const params: any = {};
    if (category) {
      params.category = category;
    }

    return this.http
      .get<{
        modules: ModuleInfo[];
        filter_category?: string;
      }>(`${this.baseUrl}/registry/modules`, { params })
      .pipe(
        map((response) => response.modules || []),
        catchError(this.handleError)
      );
  }

  // 切换模块状态
  toggleModuleStatus(moduleName: string, isActive: boolean): Observable<any> {
    // 这里需要根据后端API来实现状态切换
    // 暂时返回一个模拟的成功响应
    return this.http
      .patch(`${this.baseUrl}/registry/modules/${moduleName}/status`, {
        is_active: isActive,
      })
      .pipe(catchError(this.handleError));
  }

  // 刷新间隔（用于定时刷新数据）
  refreshInterval(): Observable<number> {
    return timer(0, 30000); // 每30秒刷新一次，返回数字序列
  }

  // 手动刷新触发器
  triggerRefresh(): void {
    this.refreshSubject.next();
  }

  private handleError(error: HttpErrorResponse) {
    let errorMessage = '发生未知错误';

    if (error.error instanceof ErrorEvent) {
      // 客户端错误
      errorMessage = `客户端错误: ${error.error.message}`;
    } else {
      // 服务器错误
      switch (error.status) {
        case 404:
          errorMessage = '请求的资源不存在';
          break;
        case 500:
          errorMessage = '服务器内部错误';
          break;
        case 0:
          errorMessage = '无法连接到服务器';
          break;
        default:
          errorMessage = `服务器错误: ${error.status} - ${error.message}`;
      }
    }

    console.error('DatabaseRegistryService Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
