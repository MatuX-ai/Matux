/**
 * HTTP Repository 抽象基类
 *
 * 实现 IRepository 接口的通用 HTTP 客户端逻辑
 * 提供统一的 CRUD 操作和查询功能
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { IRepository, PaginatedResponse, QueryCondition } from './base.repository';

/**
 * HTTP Repository 抽象基类
 *
 * @template T - 实体类型
 * @template ID - 主键类型 (默认为 number)
 */
export abstract class HttpRepositoryBase<T, ID = number> implements IRepository<T, ID> {
  /** API 基础 URL */
  protected readonly apiUrl: string;

  /**
   * 构造函数
   * @param baseUrl API 基础 URL (如 '/api/v1')
   * @param entityName 实体名称 (如 'organizations')
   */
  constructor(
    protected baseUrl: string,
    protected entityName: string,
    protected http: HttpClient
  ) {
    this.apiUrl = `${baseUrl}/${entityName}`;
  }

  /**
   * 根据 ID 查找实体
   * @param id 实体 ID
   * @returns 实体 Observable
   */
  findById(id: ID): Observable<T> {
    return this.http.get<T>(`${this.apiUrl}/${id as string | number}`);
  }

  /**
   * 查找所有实体 (支持分页)
   * @param page 页码 (默认 1)
   * @param size 每页大小 (默认 10)
   * @returns 分页响应 Observable
   */
  findAll(page: number = 1, size: number = 10): Observable<PaginatedResponse<T>> {
    const params = new HttpParams().set('page', page.toString()).set('size', size.toString());

    return this.http.get<PaginatedResponse<T>>(this.apiUrl, { params });
  }

  /**
   * 创建实体
   * @param entity 实体数据
   * @returns 创建的实体 Observable
   */
  create(entity: Partial<T>): Observable<T> {
    return this.http.post<T>(this.apiUrl, entity);
  }

  /**
   * 更新实体
   * @param id 实体 ID
   * @param entity 更新的实体数据
   * @returns 更新后的实体 Observable
   */
  update(id: ID, entity: Partial<T>): Observable<T> {
    return this.http.put<T>(`${this.apiUrl}/${id as string | number}`, entity);
  }

  /**
   * 删除实体
   * @param id 实体 ID
   * @returns Void Observable
   */
  delete(id: ID): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id as string | number}`);
  }

  /**
   * 根据条件查询实体列表
   * @param condition 查询条件
   * @returns 实体列表 Observable
   */
  findByCondition(condition: QueryCondition<T>): Observable<T[]> {
    let params = new HttpParams();

    // 构建筛选条件
    if (condition.where) {
      Object.entries(condition.where).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params = params.set(key, String(value));
        }
      });
    }

    // 设置排序
    if (condition.orderBy) {
      params = params.set('orderBy', String(condition.orderBy));
      params = params.set('order', condition.order ?? 'ASC');
    }

    // 设置限制和偏移
    if (condition.limit) {
      params = params.set('limit', condition.limit.toString());
    }
    if (condition.offset) {
      params = params.set('offset', condition.offset.toString());
    }

    return this.http.get<T[]>(this.apiUrl, { params });
  }

  /**
   * 根据条件查询单个实体
   * @param condition 查询条件
   * @returns 实体 Observable (不存在则为 null)
   */
  findOne(condition: QueryCondition<T>): Observable<T | null> {
    condition.limit = 1;
    return this.findByCondition(condition).pipe(
      map((results) => (results.length > 0 ? results[0] : null))
    );
  }

  /**
   * 统计实体数量
   * @param condition 查询条件 (可选)
   * @returns 数量 Observable
   */
  count(condition?: QueryCondition<T>): Observable<number> {
    let params = new HttpParams();

    if (condition?.where) {
      Object.entries(condition.where).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params = params.set(key, String(value));
        }
      });
    }

    return this.http
      .get<{ count: number }>(`${this.apiUrl}/count`, { params })
      .pipe(map((response) => response.count));
  }
}
