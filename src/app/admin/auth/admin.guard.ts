import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { Observable } from 'rxjs';

import { AdminAuthService } from './admin-auth.service';

@Injectable({
  providedIn: 'root',
})
export class AdminAuthGuard implements CanActivate {
  constructor(
    private adminAuthService: AdminAuthService,
    private router: Router
  ) {}

  canActivate(
    _route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    console.log('[AdminAuthGuard] Activating route:', _route.url);
    console.log('[AdminAuthGuard] Current state:', state.url);

    // 检查是否已认证
    const isAuthenticated = this.adminAuthService.isAuthenticated();
    console.log('[AdminAuthGuard] Is authenticated:', isAuthenticated);

    if (isAuthenticated) {
      console.log('[AdminAuthGuard] User is authenticated, allowing access');
      return true;
    }

    // 未认证，重定向到登录页
    console.log('[AdminAuthGuard] User is not authenticated, redirecting to login');
    return this.router.createUrlTree(['/admin/login']);
  }
}
