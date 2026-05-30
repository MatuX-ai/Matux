/**
 * Repository Cache Service
 *
 * 通用缓存服务，为 Repository 层提供内存缓存功能
 * 支持 TTL（Time To Live）过期策略
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { shareReplay } from 'rxjs/operators';

/**
 * 缓存项接口
 */
interface CacheItem<T> {
  /** 缓存的数据 */
  data: T;
  /** 过期时间戳 */
  expiresAt: number;
}

/**
 * 缓存配置选项
 */
export interface CacheOptions {
  /** 缓存时间（毫秒），默认 5 分钟 */
  ttl?: number;
  /** 是否共享缓存（RxJS shareReplay），默认 true */
  share?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class RepositoryCacheService {
  /** 缓存存储 Map */
  private cache = new Map<string, CacheItem<unknown>>();

  /** 默认缓存时间：5 分钟 */
  private readonly DEFAULT_TTL = 5 * 60 * 1000;

  /**
   * 从缓存获取数据
   * @param key 缓存键
   * @returns 缓存的数据（如果存在且未过期）
   */
  get<T>(key: string): T | null {
    const item = this.cache.get(key) as CacheItem<T> | undefined;

    if (!item) {
      return null;
    }

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  /**
   * 设置缓存
   * @param key 缓存键
   * @param data 要缓存的数据
   * @param options 缓存配置
   */
  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const ttl = options.ttl ?? this.DEFAULT_TTL;
    const expiresAt = Date.now() + ttl;

    this.cache.set(key, {
      data,
      expiresAt,
    } as CacheItem<T>);
  }

  /**
   * 删除缓存
   * @param key 缓存键
   */
  delete(key: string): void {
    this.cache.delete(key);
  }

  /**
   * 清除所有缓存
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * 清除匹配特定前缀的缓存
   * @param prefix 键前缀
   */
  clearByPrefix(prefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 检查缓存是否存在
   * @param key 缓存键
   * @returns 是否存在
   */
  has(key: string): boolean {
    const item = this.cache.get(key);

    if (!item) {
      return false;
    }

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  /**
   * 将 Observable 结果缓存
   * @param key 缓存键
   * @param observable 源 Observable
   * @param options 缓存配置
   * @returns 带缓存的 Observable
   */
  cacheObservable<T>(
    key: string,
    observable: Observable<T>,
    options: CacheOptions = {}
  ): Observable<T> {
    // 如果缓存中存在，直接返回
    const cachedData = this.get<T>(key);
    if (cachedData !== null) {
      return of(cachedData);
    }

    // 订阅并缓存结果
    const shared$ = observable.pipe(shareReplay({ bufferSize: 1, refCount: false }));

    shared$.subscribe({
      next: (data) => {
        this.set(key, data, options);
      },
      error: () => {
        // 发生错误时不缓存
      },
    });

    return shared$;
  }

  /**
   * 强制刷新缓存
   * @param key 缓存键
   * @param fetchFn 获取数据的函数
   * @param options 缓存配置
   * @returns 刷新后的 Observable
   */
  refresh<T>(key: string, fetchFn: () => Observable<T>, options: CacheOptions = {}): Observable<T> {
    // 先删除旧缓存
    this.delete(key);

    // 获取新数据并缓存
    return this.cacheObservable(key, fetchFn(), options);
  }
}
