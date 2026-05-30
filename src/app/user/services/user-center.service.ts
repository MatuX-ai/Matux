/**
 * 用户中心服务
 *
 * 提供用户中心相关的数据服务和状态管理
 */

import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { User } from '../../core/models/auth.models';
import { UserType } from '../../core/models/group.models';
import { AuthService } from '../../core/services/auth.service';

export interface UserCenterMenuItem {
  icon: string;
  label: string;
  route: string;
  userTypes?: UserType[]; // 哪些用户类型可以看到此菜单
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
   * 是否为管理员
   */
  isAdmin(): boolean {
    const userType = this.getCurrentUserType();
    return (
      userType === 'org_admin' || userType === 'school_admin' || userType === 'education_bureau'
    );
  }

  /**
   * 是否为教师
   */
  isTeacher(): boolean {
    return this.isUserType('teacher');
  }

  /**
   * 是否为学生
   */
  isStudent(): boolean {
    return this.isUserType('student');
  }

  /**
   * 是否为家长
   */
  isParent(): boolean {
    return this.isUserType('parent');
  }

  /**
   * 根据用户类型获取侧边栏菜单
   */
  getSidebarMenu(): UserCenterMenuItem[] {
    const userType = this.getCurrentUserType() as UserType;

    const baseMenu: UserCenterMenuItem[] = [
      {
        icon: 'dashboard',
        label: '仪表板',
        route: '/user/dashboard',
      },
      {
        icon: 'person',
        label: '个人资料',
        route: '/user/profile',
      },
      {
        icon: 'token',
        label: 'Token管理',
        route: '/user/token',
      },
    ];

    // 根据不同用户类型添加特定菜单
    const userTypeMenus: Record<string, UserCenterMenuItem[]> = {
      student: [
        {
          icon: 'school',
          label: '我的课程',
          route: '/user/courses',
        },
        {
          icon: 'emoji_events',
          label: '成就系统',
          route: '/user/achievements',
        },
      ],
      teacher: [
        {
          icon: 'class',
          label: '教学管理',
          route: '/user/teaching',
        },
        {
          icon: 'people',
          label: '学生管理',
          route: '/user/students',
        },
        {
          icon: 'menu_book',
          label: '课程管理',
          route: '/user/teacher-courses',
        },
      ],
      parent: [
        {
          icon: 'family_restroom',
          label: '孩子管理',
          route: '/user/children',
        },
        {
          icon: 'assessment',
          label: '学习报告',
          route: '/user/reports',
        },
      ],
      school_admin: [
        {
          icon: 'school',
          label: '学校概览',
          route: '/user/dashboard',
        },
        {
          icon: 'groups',
          label: '年级班级管理',
          route: '/user/classes',
        },
        {
          icon: 'menu_book',
          label: '校本课程',
          route: '/user/school-courses',
        },
        {
          icon: 'assessment',
          label: '教学质量监控',
          route: '/user/quality',
        },
        {
          icon: 'people',
          label: '教师工作量',
          route: '/user/teacher-workload',
        },
      ],
      education_bureau: [
        {
          icon: 'domain',
          label: '区域概览',
          route: '/user/dashboard',
        },
        {
          icon: 'account_balance',
          label: '学校管理',
          route: '/user/schools',
        },
        {
          icon: 'assessment',
          label: '教学质量监控',
          route: '/user/quality',
        },
        {
          icon: 'pie_chart',
          label: '数据分析',
          route: '/user/analysis',
        },
        {
          icon: 'download',
          label: '报表导出',
          route: '/user/reports-export',
        },
      ],
      // org_admin: [  // 已解耦到 OpenMTEduInst 项目
      //   {
      //     icon: 'business',
      //     label: '机构概览',
      //     route: '/admin/organizations/dashboard',
      //   },
      //   {
      //     icon: 'people',
      //     label: '教师管理',
      //     route: '/admin/organizations/teachers',
      //   },
      //   {
      //     icon: 'school',
      //     label: '学员管理',
      //     route: '/admin/organizations/students',
      //   },
      //   {
      //     icon: 'menu_book',
      //     label: '课程管理',
      //     route: '/admin/organizations/courses',
      //   },
      //   {
      //     icon: 'assessment',
      //     label: '运营统计',
      //     route: '/admin/organizations/stats',
      //   },
      // ],
    };

    const specificMenu = userType && userTypeMenus[userType] ? userTypeMenus[userType] : [];

    return [...baseMenu, ...specificMenu];
  }

  /**
   * 登出
   */
  logout(): void {
    this.authService.logout();
  }
}
