import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, throwError, TimeoutError } from 'rxjs';
import { catchError, timeout } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

/**
 * HTTP 超时拦截器
 * 为所有 HTTP 请求添加超时控制，开发环境下使用较短的超时时间
 * 使 Mock 降级能够快速生效，提升开发体验
 */
@Injectable()
export class HttpTimeoutInterceptor implements HttpInterceptor {
  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const timeoutMs = environment.httpTimeout ?? 30000;

    return next.handle(request).pipe(
      timeout(timeoutMs),
      catchError((error: Error) => {
        if (error instanceof TimeoutError) {
          console.warn(`[HTTP Timeout] 请求超时 (${timeoutMs}ms): ${request.url}`);
          return throwError(() => new Error(`请求超时，已等待 ${timeoutMs}ms`));
        }
        return throwError(() => error);
      })
    );
  }
}
