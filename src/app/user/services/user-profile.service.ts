/**
 * 用户个人资料服务
 *
 * 提供用户个人资料相关的 HTTP 请求服务，包括：
 * - 用户信息获取
 * - 用户信息更新
 * - 密码修改
 * - 用户偏好设置
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { delay, Observable, of, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { UserProfile, UserType, UserTypeGroup } from '../../core/models/group.models';

/**
 * 是否使用模拟数据
 */
const USE_MOCK_DATA = true;

/**
 * 用户个人资料更新请求
 */
export interface UpdateUserProfileRequest {
  /** 用户名 */
  username?: string;
  /** 真实姓名 */
  realName?: string;
  /** 手机号 */
  phone?: string;
  /** 头像 URL */
  avatar?: string;
  /** 个人简介 */
  bio?: string;
}

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  /** 当前密码 */
  currentPassword: string;
  /** 新密码 */
  newPassword: string;
  /** 确认新密码 */
  confirmPassword: string;
}

/**
 * 用户偏好设置
 */
export interface UserPreferences {
  /** 主题设置: light | dark | auto */
  theme?: string;
  /** 语言设置: zh-CN | en-US */
  language?: string;
  /** 通知设置 */
  notifications?: {
    email?: boolean;
    sms?: boolean;
    push?: boolean;
  };
  /** 隐私设置 */
  privacy?: {
    showEmail?: boolean;
    showPhone?: boolean;
  };
}

/**
 * 用户个人资料服务
 */
@Injectable({
  providedIn: 'root',
})
export class UserProfileService {
  private readonly API_BASE_URL = '/api/user/profile';

  constructor(private http: HttpClient) {}

  /**
   * 获取当前用户个人资料
   */
  getUserProfile(): Observable<UserProfile> {
    if (USE_MOCK_DATA) {
      const mockProfile: UserProfile = {
        id: 'user001',
        username: 'parent_demo',
        email: 'parent@imato.com',
        realName: '张家长',
        phone: '138****8888',
        avatar: '/assets/images/default-avatar.png',
        createdAt: new Date('2024-01-15T10:00:00'),
        updatedAt: new Date('2025-03-18T16:30:00'),
        userType: UserType.STUDENT,
        userTypeGroup: UserTypeGroup.PERSONAL,
      };
      return of(mockProfile).pipe(delay(400));
    }
    return this.http
      .get<UserProfile>(`${this.API_BASE_URL}`)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 更新用户个人资料
   * @param profileData 更新的资料数据
   */
  updateUserProfile(profileData: UpdateUserProfileRequest): Observable<UserProfile> {
    if (USE_MOCK_DATA) {
      const updatedProfile: UserProfile = {
        id: 'user001',
        username: profileData.username ?? 'parent_demo',
        email: 'parent@imato.com',
        realName: profileData.realName ?? '张家长',
        phone: profileData.phone ?? '138****8888',
        avatar: profileData.avatar ?? '/assets/images/default-avatar.png',
        createdAt: new Date('2024-01-15T10:00:00'),
        updatedAt: new Date(),
        userType: UserType.STUDENT,
        userTypeGroup: UserTypeGroup.PERSONAL,
      };
      return of(updatedProfile).pipe(delay(600));
    }
    return this.http
      .put<UserProfile>(`${this.API_BASE_URL}`, profileData)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 修改用户密码
   * @param passwordData 密码数据
   */
  changePassword(passwordData: ChangePasswordRequest): Observable<{ message: string }> {
    if (USE_MOCK_DATA) {
      if (passwordData.newPassword !== passwordData.confirmPassword) {
        return throwError(() => new Error('两次输入的密码不一致'));
      }
      if (passwordData.currentPassword === passwordData.newPassword) {
        return throwError(() => new Error('新密码不能与当前密码相同'));
      }
      return of({ message: '密码修改成功，请重新登录' }).pipe(delay(800));
    }
    return this.http
      .post<{ message: string }>(`${this.API_BASE_URL}/change-password`, passwordData)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 上传用户头像
   * @param file 图片文件
   */
  uploadAvatar(file: File): Observable<{ avatarUrl: string }> {
    if (USE_MOCK_DATA) {
      const mockAvatarUrl = `/assets/uploaded-avatar-${Date.now()}.png`;
      return of({ avatarUrl: mockAvatarUrl }).pipe(delay(1000));
    }
    const formData = new FormData();
    formData.append('avatar', file);

    return this.http
      .post<{ avatarUrl: string }>(`${this.API_BASE_URL}/avatar`, formData)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 上传裁剪后的头像
   * @param file 裁剪后的图片文件
   * @param cropData 裁剪参数 (可选)
   */
  uploadAvatarWithCrop(
    file: File,
    cropData?: Record<string, unknown>
  ): Observable<{ avatarUrl: string }> {
    if (USE_MOCK_DATA) {
      const mockAvatarUrl = `/assets/uploaded-avatar-cropped-${Date.now()}.png`;
      return of({ avatarUrl: mockAvatarUrl }).pipe(delay(1500));
    }

    const formData = new FormData();
    formData.append('avatar', file);

    if (cropData) {
      formData.append('crop_data', JSON.stringify(cropData));
    }

    return this.http
      .post<{ avatarUrl: string }>(`${this.API_BASE_URL}/avatar/crop`, formData)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 获取头像上传 URL(用于直接上传到 CDN)
   */
  getAvatarUploadUrl(): Observable<{ uploadUrl: string; fields?: Record<string, unknown> }> {
    if (USE_MOCK_DATA) {
      return of({
        uploadUrl: `https://cdn.imato.com/avatars/upload/${Date.now()}`,
        fields: {},
      }).pipe(delay(500));
    }

    return this.http
      .get<{
        uploadUrl: string;
        fields?: Record<string, unknown>;
      }>(`${this.API_BASE_URL}/avatar/upload-url`)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 获取用户偏好设置
   */
  getUserPreferences(): Observable<UserPreferences> {
    if (USE_MOCK_DATA) {
      const mockPreferences: UserPreferences = {
        theme: 'light',
        language: 'zh-CN',
        notifications: {
          email: true,
          sms: false,
          push: true,
        },
        privacy: {
          showEmail: false,
          showPhone: false,
        },
      };
      return of(mockPreferences).pipe(delay(100));
    }
    return this.http
      .get<UserPreferences>(`${this.API_BASE_URL}/preferences`)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 更新用户偏好设置
   * @param preferences 偏好设置
   */
  updateUserPreferences(preferences: UserPreferences): Observable<UserPreferences> {
    if (USE_MOCK_DATA) {
      return of(preferences).pipe(delay(500));
    }
    return this.http
      .put<UserPreferences>(`${this.API_BASE_URL}/preferences`, preferences)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * 错误处理
   * @param error HTTP 错误响应
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, complexity
  private handleError(error: any): Observable<never> {
    let errorMessage = '操作失败';

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    if (error.error instanceof ErrorEvent) {
      // 客户端错误
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      errorMessage = `客户端错误：${error.error.message}`;
    } else {
      // 服务端错误
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      if (error.status === 400) {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
        errorMessage = error.error?.message || '请求参数错误';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      } else if (error.status === 401) {
        errorMessage = '未授权，请重新登录';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      } else if (error.status === 403) {
        errorMessage = '无权执行此操作';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      } else if (error.status === 404) {
        errorMessage = '用户资料不存在';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      } else if (error.status === 409) {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
        errorMessage = error.error?.message || '数据冲突';
        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
      } else if (error.status === 500) {
        errorMessage = '服务器错误，请稍后重试';
      } else {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
        errorMessage = error.error?.message || `错误码：${error.status}`;
      }
    }

    console.error('UserProfileService Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
