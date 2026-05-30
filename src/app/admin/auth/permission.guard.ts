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
export class PermissionGuard implements CanActivate {
  constructor(
    private adminAuthService: AdminAuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    _state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    // 获取所需的权限
    const requiredPermissions = route.data['permissions'] as string[];
    const requiredRoles = route.data['roles'] as string[];

    // 检查认证状态
    if (!this.adminAuthService.isAuthenticated()) {
      return this.router.createUrlTree(['/admin/login']);
    }

    // 检查角色权限
    if (requiredRoles && requiredRoles.length > 0) {
      const hasRole = requiredRoles.some((role) => this.adminAuthService.hasRole(role));
      if (!hasRole) {
        // 可以重定向到无权限页面或返回403
        return this.router.createUrlTree(['/admin/unauthorized']);
      }
    }

    // 检查具体权限
    if (requiredPermissions && requiredPermissions.length > 0) {
      const hasPermission = requiredPermissions.every((permission) =>
        this.adminAuthService.hasPermission(permission)
      );

      if (!hasPermission) {
        // 可以重定向到无权限页面或返回403
        return this.router.createUrlTree(['/admin/unauthorized']);
      }
    }

    return true;
  }
}
