/**
 * 用户个人资料组件
 *
 * 提供用户个人信息的查看和编辑功能
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { UserProfile } from '../../../core/models/group.models';
import {
  AvatarCropDialogComponent,
  CropDialogResult,
} from '../../../shared/components/avatar-crop-dialog/avatar-crop-dialog.component';
import {
  UpdateUserProfileRequest,
  UserPreferences,
  UserProfileService,
} from '../../services/user-profile.service';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatDividerModule,
    MatButtonToggleModule,
    MatCheckboxModule,
  ],
  templateUrl: './user-profile.component.html',
  styleUrls: ['./user-profile.component.scss'],
})
export class UserProfileComponent implements OnInit, OnDestroy {
  /**
   * 用户个人资料
   */
  userProfile: UserProfile | null = null;

  /**
   * 用户偏好设置
   */
  userPreferences: UserPreferences = {};

  /**
   * 通知设置
   */
  emailNotify = true;
  smsNotify = false;
  pushNotify = true;
  showEmail = false;
  showPhone = false;

  /**
   * 编辑模式
   */
  isEditing = false;

  /**
   * 加载状态
   */
  loading = false;

  /**
   * 保存中状态
   */
  saving = false;

  /**
   * 错误信息
   */
  error: string | null = null;

  /**
   * 表单数据
   */
  formData: UpdateUserProfileRequest = {};

  /**
   * 组件销毁通知
   */
  private destroy$ = new Subject<void>();

  constructor(
    private userProfileService: UserProfileService,
    private snackBar: MatSnackBar,
    private router: Router,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.loadUserProfile();
    this.loadUserPreferences();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载用户个人资料
   */
  loadUserProfile(): void {
    this.loading = true;
    this.error = null;

    this.userProfileService
      .getUserProfile()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (profile) => {
          this.userProfile = profile;
          this.formData = {
            username: profile.username,
            realName: profile.realName,
            phone: profile.phone,
            avatar: profile.avatar,
          };
          this.loading = false;
        },
        error: (error) => {
          this.error = (error as Error).message;
          this.loading = false;
          console.error('加载用户资料失败:', error);
        },
      });
  }

  /**
   * 加载用户偏好设置
   */
  loadUserPreferences(): void {
    this.userProfileService
      .getUserPreferences()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (preferences) => {
          this.userPreferences = preferences;
          // 同步通知和隐私设置到独立变量
          this.emailNotify = preferences.notifications?.email ?? true;
          this.smsNotify = preferences.notifications?.sms ?? false;
          this.pushNotify = preferences.notifications?.push ?? true;
          this.showEmail = preferences.privacy?.showEmail ?? false;
          this.showPhone = preferences.privacy?.showPhone ?? false;
        },
        error: (error) => {
          console.error('加载用户偏好设置失败:', error);
          // 使用默认设置
          this.userPreferences = {
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
          this.emailNotify = true;
          this.smsNotify = false;
          this.pushNotify = true;
          this.showEmail = false;
          this.showPhone = false;
        },
      });
  }

  /**
   * 进入编辑模式
   */
  enterEditMode(): void {
    this.isEditing = true;
    this.error = null;

    // 重置表单数据为当前用户信息
    if (this.userProfile) {
      this.formData = {
        username: this.userProfile.username,
        realName: this.userProfile.realName,
        phone: this.userProfile.phone,
        avatar: this.userProfile.avatar,
      };
    }
  }

  /**
   * 保存个人资料
   */
  saveProfile(): void {
    if (!this.formData.username?.trim()) {
      this.error = '用户名不能为空';
      return;
    }

    this.saving = true;
    this.error = null;

    this.userProfileService
      .updateUserProfile(this.formData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (updatedProfile) => {
          this.userProfile = updatedProfile;
          this.isEditing = false;
          this.saving = false;
          this.snackBar.open('个人资料保存成功', '关闭', { duration: 3000 });
        },
        error: (error) => {
          this.error = (error as Error).message;
          this.saving = false;
          console.error('保存个人资料失败:', error);
        },
      });
  }

  /**
   * 取消编辑
   */
  cancelEdit(): void {
    this.isEditing = false;
    this.error = null;

    // 重置表单数据
    if (this.userProfile) {
      this.formData = {
        username: this.userProfile.username,
        realName: this.userProfile.realName,
        phone: this.userProfile.phone,
        avatar: this.userProfile.avatar,
      };
    }
  }

  /**
   * 上传头像
   * @param event 文件选择事件
   */
  uploadAvatar(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (input.files?.[0]) {
      const file = input.files[0];

      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        this.error = '请选择图片文件';
        return;
      }

      // 验证文件大小（最大 5MB）
      if (file.size > 5 * 1024 * 1024) {
        this.error = '图片文件大小不能超过 5MB';
        return;
      }

      // 打开裁剪对话框
      const dialogRef = this.dialog.open(AvatarCropDialogComponent, {
        data: {
          imageFile: file,
          aspectRatio: 1, // 正方形裁剪
          canvasRotation: 0,
        },
        disableClose: true,
        panelClass: 'crop-dialog-panel',
      });

      dialogRef.afterClosed().subscribe((result: CropDialogResult) => {
        if (result?.croppedImageFile) {
          // 上传裁剪后的图片
          this.saving = true;
          this.error = null;

          this.userProfileService
            .uploadAvatarWithCrop(result.croppedImageFile)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (response) => {
                this.formData.avatar = response.avatarUrl;

                // 同时更新用户资料
                return this.userProfileService
                  .updateUserProfile({ avatar: response.avatarUrl })
                  .pipe(takeUntil(this.destroy$));
              },
              complete: () => {
                if (this.userProfile) {
                  this.userProfile = { ...this.userProfile, avatar: this.formData.avatar };
                }
                this.saving = false;
                this.snackBar.open('头像更新成功', '关闭', { duration: 3000 });
              },
              error: (error: any) => {
                this.error = (error as Error).message || '上传失败';
                this.saving = false;
                console.error('上传头像失败:', error);
              },
            });
        }
      });
    }
  }

  /**
   * 保存偏好设置
   */
  savePreferences(): void {
    this.saving = true;

    // 从独立变量同步到用户偏好设置
    this.userPreferences = {
      ...this.userPreferences,
      notifications: {
        email: this.emailNotify,
        sms: this.smsNotify,
        push: this.pushNotify,
      },
      privacy: {
        showEmail: this.showEmail,
        showPhone: this.showPhone,
      },
    };

    this.userProfileService
      .updateUserPreferences(this.userPreferences)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.saving = false;
          this.snackBar.open('偏好设置保存成功', '关闭', { duration: 3000 });
        },
        error: (error) => {
          this.error = (error as Error).message;
          this.saving = false;
          console.error('保存偏好设置失败:', error);
        },
      });
  }

  /**
   * 跳转到修改密码页面
   */
  changePassword(): void {
    // 在实际应用中，这里应该导航到密码修改页面
    // this.router.navigate(['/user/change-password']);
    this.snackBar.open('密码修改功能即将开放', '关闭', { duration: 3000 });
  }

  /**
   * 获取用户类型标签
   */
  getUserTypeLabel(): string {
    if (!this.userProfile?.userType) {
      return '用户';
    }

    const typeLabels: Record<string, string> = {
      student: '学生',
      parent: '家长',
      teacher: '教师',
      org_admin: '机构管理员',
      school_admin: '学校管理员',
      education_bureau: '教育局',
    };

    return typeLabels[this.userProfile.userType] || '用户';
  }
}
