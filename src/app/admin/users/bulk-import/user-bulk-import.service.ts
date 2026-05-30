import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export interface ImportResult {
  success_count: number;
  failed_count: number;
  conflicts_count: number;
  errors: string[];
  conflicts: any;
  imported_users: any[];
}

@Injectable({
  providedIn: 'root',
})
export class UserBulkImportService {
  private readonly API_BASE_URL = '/api/v1/auth';

  constructor(private http: HttpClient) {}

  /**
   * 批量导入用户
   */
  importUsers(
    file: File,
    conflictResolution: string = 'skip',
    generatePassword: boolean = true
  ): Observable<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conflict_resolution', conflictResolution);
    formData.append('generate_password', generatePassword.toString());

    return this.http
      .post<ImportResult>(`${this.API_BASE_URL}/bulk-import`, formData)
      .pipe(catchError(this.handleError));
  }

  /**
   * 下载导入模板
   */
  downloadTemplate(): void {
    // 创建CSV模板
    const templateData = [
      ['username', 'email', 'role'],
      ['张三', 'zhangsan@example.com', 'user'],
      ['李四', 'lisi@example.com', 'admin'],
      ['王五', 'wangwu@example.com', 'user'],
    ];

    const csvContent = templateData
      .map((row) => row.map((field) => `"${field}"`).join(','))
      .join('\n');

    // 创建并下载文件
    const blob = new Blob(['\uFEFF' + csvContent], {
      type: 'text/csv;charset=utf-8;',
    });

    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', '用户导入模板.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * 错误处理
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = '导入过程中发生未知错误';

    if (error.error instanceof ErrorEvent) {
      // 客户端错误
      errorMessage = `客户端错误: ${error.error.message}`;
    } else {
      // 服务器错误
      if (error.error?.detail) {
        errorMessage = error.error.detail;
      } else if (error.status === 403) {
        errorMessage = '权限不足，只有管理员才能执行批量导入操作';
      } else if (error.status === 400) {
        errorMessage = '请求参数错误，请检查文件格式和内容';
      } else if (error.status === 500) {
        errorMessage = '服务器内部错误，请稍后重试';
      }
    }

    return throwError(() => new Error(errorMessage));
  }
}
