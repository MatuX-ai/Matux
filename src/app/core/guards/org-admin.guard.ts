import { Injectable } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';
import { Observable } from 'rxjs';

import { AuthService } from '../services/auth.service';

/**
 * 机构管理员路由守卫
 * 验证用户是否有机构管理权限
 */
@Injectable({
  providedIn: 'root',
})
export class OrgAdminGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    const user = this.authService.getCurrentUser();

    // 检查用户是否已认证
    if (!user) {
      // 未认证，跳转到登录页并保存原始URL
      return this.router.createUrlTree(['/auth/login'], {
        queryParams: { returnUrl: state.url },
      });
    }

    // 检查用户是否有机构管理员权限
    const userType = (user as any).userType;
    const allowedTypes = ['org_admin', 'school_admin', 'education_bureau', 'super_admin'];

    if (allowedTypes.includes(userType)) {
      // 获取机构ID（从路由参数或用户数据）
      const orgId = route.params['id'] || (user as any).organizationId;

      if (orgId) {
        return true;
      } else {
        // 用户没有关联机构ID，跳转到机构列表（已解耦到 OpenMTEduInst 项目）
        // return this.router.createUrlTree(['/admin/organizations']);
        return this.router.createUrlTree(['/admin/dashboard']);
      }
    }

    // 用户没有权限，显示拒绝访问
    return this.router.createUrlTree(['/unauthorized'], {
      queryParams: {
        message: '您没有机构管理权限',
        returnUrl: state.url,
      },
    });
  }
}
