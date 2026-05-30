/**
 * Retry Utils
 *
 * HTTP 请求重试工具函数
 * 提供指数退避、延迟重试等策略
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Observable, of, OperatorFunction, throwError, timer } from 'rxjs';
import { catchError, mergeMap, retryWhen } from 'rxjs/operators';

/**
 * 重试配置选项
 */
export interface RetryOptions {
  /** 最大重试次数，默认 3 次 */
  maxRetries?: number;
  /** 初始延迟（毫秒），默认 1000ms */
  initialDelay?: number;
  /** 最大延迟（毫秒），默认 10000ms */
  maxDelay?: number;
  /** 是否使用指数退避，默认 true */
  exponentialBackoff?: boolean;
}

/**
 * 智能重试操作符
 *
 * 使用指数退避策略进行重试
 * 适用于网络不稳定、服务器临时故障等场景
 *
 * @param options 重试配置
 * @returns RxJS OperatorFunction
 *
 * @example
 * http.get(url).pipe(
 *   retryWithBackoff({ maxRetries: 3, initialDelay: 1000 })
 * )
 */
export function retryWithBackoff<T>(options: RetryOptions = {}): OperatorFunction<T, T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    exponentialBackoff = true,
  } = options;

  return retryWhen((errors: Observable<unknown>) =>
    errors.pipe(
      mergeMap((error: unknown, attempt) => {
        // 超过最大重试次数，抛出错误
        if (attempt >= maxRetries) {
          return throwError(() => error as Error);
        }

        // 计算延迟时间
        let delay: number;
        if (exponentialBackoff) {
          // 指数退避：1s, 2s, 4s, 8s...
          delay = Math.min(initialDelay * Math.pow(2, attempt), maxDelay);
        } else {
          // 固定延迟
          delay = initialDelay;
        }

        // 延迟后重试
        return timer(delay);
      })
    )
  );
}

/**
 * 条件重试操作符
 *
 * 仅在满足特定条件时重试
 *
 * @param predicate 判断是否重试的函数
 * @param maxRetries 最大重试次数
 * @returns RxJS OperatorFunction
 *
 * @example
 * http.get(url).pipe(
 *   retryIf(
 *     error => error.status === 503, // 仅在服务器不可用时重试
 *     3
 *   )
 * )
 */
export function retryIf<T>(
  predicate: (error: unknown) => boolean,
  maxRetries = 3
): OperatorFunction<T, T> {
  return retryWhen((errors: Observable<unknown>) =>
    errors.pipe(
      mergeMap((error: unknown, attempt) => {
        if (attempt >= maxRetries || !predicate(error)) {
          return throwError(() => error as Error);
        }

        return timer(1000);
      })
    )
  );
}

/**
 * 捕获错误并返回默认值
 *
 * 当请求失败时返回提供的默认值，避免中断数据流
 *
 * @param defaultValue 默认值
 * @param logError 是否记录错误日志，默认 true
 * @returns RxJS OperatorFunction
 *
 * @example
 * http.get<Data>(url).pipe(
 *   catchErrorAndReturn([]) // 失败时返回空数组
 * )
 */
export function catchErrorAndReturn<T>(defaultValue: T, logError = true): OperatorFunction<T, T> {
  return catchError((error: unknown) => {
    if (logError) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error('[Catch Error]', errorMessage);
    }
    return of(defaultValue);
  });
}
