/**
 * 用户中心服务
 *
 * 提供用户中心相关的数据服务和状态管理
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { ROUTES } from '../../routes.const';
import { User } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';

export interface UserCenterMenuItem {
  icon: string;
  label: string;
  route: string;
  children?: UserCenterMenuItem[];
}

@Injectable({
  providedIn: 'root',
})
export class UserCenterService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private authService: AuthService) {
    // 订阅认证服务中的用户状态
    this.authService.currentUser$.subscribe((user) => {
      this.currentUserSubject.next(user);
    });
  }

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * 获取当前用户类型
   */
  getCurrentUserType(): string | undefined {
    const user = this.getCurrentUser();
    return user?.userType;
  }

  /**
   * 判断是否为指定用户类型
   */
  isUserType(type: string): boolean {
    return this.getCurrentUserType() === type;
  }

  /**
   * 是否为学生
   */
  isStudent(): boolean {
    return this.isUserType('student');
  }

  /**
   * 获取侧边栏菜单（学生端固定菜单）
   */
  // eslint-disable-next-line max-lines-per-function
  getSidebarMenu(): UserCenterMenuItem[] {
    return [
      {
        icon: 'dashboard',
        label: '学习仪表板',
        route: ROUTES.USER.DASHBOARD,
      },
      {
        icon: 'menu_book',
        label: '我的课程',
        route: ROUTES.USER.COURSES,
      },
      {
        icon: 'psychology',
        label: '学习画像',
        route: ROUTES.USER.LEARNING_PROFILE,
      },
      {
        icon: 'trending_up',
        label: '我的成长',
        route: ROUTES.USER.GROWTH_TRAJECTORY,
      },
      {
        icon: 'assessment',
        label: '学习报告',
        route: ROUTES.USER.REPORTS,
      },
      {
        icon: 'tips_and_updates',
        label: '教学建议',
        route: ROUTES.USER.TEACHING_SUGGESTIONS,
      },
      {
        icon: 'emoji_events',
        label: '成就系统',
        route: ROUTES.USER.ACHIEVEMENTS,
      },
      {
        icon: 'token',
        label: 'Token管理',
        route: ROUTES.USER.TOKEN,
      },
      {
        icon: 'person',
        label: '个人资料',
        route: ROUTES.USER.PROFILE,
      },
      {
        icon: 'smart_toy',
        label: 'AI教师设置',
        route: ROUTES.USER.AI_TEACHER_SETTINGS,
      },
      {
        icon: 'favorite',
        label: '情感陪伴',
        route: ROUTES.USER.EMOTIONAL_COMPANION,
      },
    ];
  }

  /**
   * 登出
   */
  logout(): void {
    this.authService.logout();
  }
}
