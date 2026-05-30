/**
 * Repository 基础接口定义
 *
 * 提供数据访问层的抽象接口，支持 CRUD 操作和高级查询
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Observable } from 'rxjs';

/**
 * 分页响应数据结构
 */
export interface PaginatedResponse<T> {
  /** 数据列表 */
  data: T[];
  /** 总记录数 */
  total: number;
  /** 当前页码 */
  page: number;
  /** 每页大小 */
  size: number;
  /** 总页数 */
  totalPages: number;
}

/**
 * 查询条件接口
 */
export interface QueryCondition<T> {
  /** 筛选条件 */
  where?: Partial<T>;
  /** 排序字段 */
  orderBy?: keyof T | string;
  /** 排序方向 */
  order?: 'ASC' | 'DESC';
  /** 返回数量限制 */
  limit?: number;
  /** 偏移量 */
  offset?: number;
}

/**
 * Repository 基础接口
 *
 * @template T - 实体类型
 * @template ID - 主键类型 (默认为 number)
 */
export interface IRepository<T, ID = number> {
  /**
   * 根据 ID 查找实体
   * @param id 实体 ID
   * @returns 实体 Observable
   */
  findById(id: ID): Observable<T>;

  /**
   * 查找所有实体 (支持分页)
   * @param page 页码 (默认 1)
   * @param size 每页大小 (默认 10)
   * @returns 分页响应 Observable
   */
  findAll(page?: number, size?: number): Observable<PaginatedResponse<T>>;

  /**
   * 创建实体
   * @param entity 实体数据 (部分属性)
   * @returns 创建的实体 Observable
   */
  create(entity: Partial<T>): Observable<T>;

  /**
   * 更新实体
   * @param id 实体 ID
   * @param entity 更新的实体数据 (部分属性)
   * @returns 更新后的实体 Observable
   */
  update(id: ID, entity: Partial<T>): Observable<T>;

  /**
   * 删除实体
   * @param id 实体 ID
   * @returns Void Observable
   */
  delete(id: ID): Observable<void>;

  /**
   * 根据条件查询实体列表
   * @param condition 查询条件
   * @returns 实体列表 Observable
   */
  findByCondition(condition: QueryCondition<T>): Observable<T[]>;

  /**
   * 根据条件查询单个实体
   * @param condition 查询条件
   * @returns 实体 Observable (不存在则为 null)
   */
  findOne(condition: QueryCondition<T>): Observable<T | null>;

  /**
   * 统计实体数量
   * @param condition 查询条件 (可选)
   * @returns 数量 Observable
   */
  count(condition?: QueryCondition<T>): Observable<number>;
}
