import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

import { OfflineStorageKey } from '../../../shared/models/offline.models';
import { OfflineStorageService } from '../../core/services/offline-storage.service';

/**
 * 课程资源类型
 */
export interface OfflineCourseResource {
  id: string;
  courseId: string;
  /** 资源URL */
  resourceUrl: string;
  /** MIME类型 */
  mimeType: string;
  /** Blob数据 */
  data: Blob;
  /** 文件大小 */
  size: number;
  /** 过期时间 */
  expiresAt: Date;
  /** 下载时间 */
  downloadedAt: Date;
}

/**
 * 离线课程内容缓存
 */
export interface CachedCourse {
  id: string;
  courseId: string;
  title: string;
  description?: string;
  /** 完整课程数据JSON */
  data: Record<string, unknown>;
  /** 下载时间 */
  downloadedAt: Date;
  /** 过期时间（默认7天） */
  expiresAt: Date;
  /** 课程版本号 */
  version: string;
  /** 资源列表 */
  resources: { url: string; mimeType: string; size: number }[];
  /** 资源下载进度 0-100 */
  downloadProgress: number;
}

/**
 * 离线课程存储服务
 *
 * 负责课程内容的离线缓存管理：
 * - 课程元数据缓存
 * - 课程资源文件（音频/图片/视频）的 Blob 存储
 * - 缓存过期清理
 * - 下载进度追踪
 */
@Injectable({
  providedIn: 'root',
})
export class OfflineCourseStorageService {
  private cachedCoursesSubject = new BehaviorSubject<CachedCourse[]>([]);
  public cachedCourses$: Observable<CachedCourse[]> = this.cachedCoursesSubject.asObservable();

  private downloadProgressSubject = new BehaviorSubject<Record<string, number>>({});
  public downloadProgress$: Observable<Record<string, number>> =
    this.downloadProgressSubject.asObservable();

  constructor(private offlineStorage: OfflineStorageService) {}

  /**
   * 缓存课程内容到 IndexedDB
   */
  async cacheCourse(
    courseId: string,
    title: string,
    data: Record<string, unknown>,
    resources: { url: string; mimeType: string; size: number }[] = [],
    ttlMs = 7 * 24 * 60 * 60 * 1000
  ): Promise<void> {
    const now = new Date();
    const course: CachedCourse = {
      id: this.generateId(),
      courseId,
      title,
      data,
      downloadedAt: now,
      expiresAt: new Date(now.getTime() + ttlMs),
      version: '1',
      resources,
      downloadProgress: 0,
    };

    await this.offlineStorage.setData(OfflineStorageKey.COURSES, course);
    await this.refreshCacheList();
  }

  /**
   * 获取缓存的课程列表
   */
  async getCachedCourses(): Promise<CachedCourse[]> {
    return this.offlineStorage.getAllData<CachedCourse>(OfflineStorageKey.COURSES);
  }

  /**
   * 获取指定课程的缓存
   */
  async getCachedCourse(courseId: string): Promise<CachedCourse | undefined> {
    const courses = await this.getCachedCourses();
    return courses.find((c) => c.courseId === courseId);
  }

  /**
   * 删除课程缓存
   */
  async removeCachedCourse(courseId: string): Promise<void> {
    const courses = await this.getCachedCourses();
    const course = courses.find((c) => c.courseId === courseId);
    if (course) {
      await this.offlineStorage.deleteData(OfflineStorageKey.COURSES, course.id);
      // 同时清理相关资源
      await this.clearCourseResources(courseId);
      await this.refreshCacheList();
    }
  }

  /**
   * 存储课程资源文件（Blob）
   */
  async cacheResource(
    courseId: string,
    resourceUrl: string,
    data: Blob,
    mimeType: string
  ): Promise<void> {
    const resource: OfflineCourseResource = {
      id: this.generateId(),
      courseId,
      resourceUrl,
      mimeType,
      data,
      size: data.size,
      downloadedAt: new Date(),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    };
    await this.offlineStorage.setData(OfflineStorageKey.ASSETS, resource);

    // 更新课程下载进度
    await this.updateDownloadProgress(courseId);
  }

  /**
   * 获取缓存的课程资源
   */
  async getCachedResource(resourceUrl: string): Promise<OfflineCourseResource | undefined> {
    const assets = await this.offlineStorage.getAllData<OfflineCourseResource>(
      OfflineStorageKey.ASSETS
    );
    return assets.find((a) => a.resourceUrl === resourceUrl);
  }

  /**
   * 获取课程的所有缓存资源
   */
  async getCourseResources(courseId: string): Promise<OfflineCourseResource[]> {
    const assets = await this.offlineStorage.getAllData<OfflineCourseResource>(
      OfflineStorageKey.ASSETS
    );
    return assets.filter((a) => a.courseId === courseId);
  }

  /**
   * 检查课程是否已缓存
   */
  async isCourseCached(courseId: string): Promise<boolean> {
    const course = await this.getCachedCourse(courseId);
    return !!course && new Date(course.expiresAt) > new Date();
  }

  /**
   * 清理过期课程缓存
   */
  async cleanupExpiredCourses(): Promise<number> {
    const courses = await this.getCachedCourses();
    const now = new Date();
    let cleaned = 0;

    for (const course of courses) {
      if (new Date(course.expiresAt) <= now) {
        await this.offlineStorage.deleteData(OfflineStorageKey.COURSES, course.id);
        await this.clearCourseResources(course.courseId);
        cleaned++;
      }
    }

    await this.refreshCacheList();
    return cleaned;
  }

  /**
   * 获取缓存统计
   */
  async getCacheStats(): Promise<{
    courseCount: number;
    resourceCount: number;
    totalSize: number;
  }> {
    const courses = await this.getCachedCourses();
    const assets = await this.offlineStorage.getAllData<OfflineCourseResource>(
      OfflineStorageKey.ASSETS
    );

    const totalSize = assets.reduce((sum, a) => sum + a.size, 0);

    return {
      courseCount: courses.length,
      resourceCount: assets.length,
      totalSize,
    };
  }

  /**
   * 批量下载资源文件
   */
  async batchDownloadResources(
    courseId: string,
    resources: { url: string; mimeType: string }[]
  ): Promise<void> {
    let completed = 0;
    const total = resources.length;

    for (const resource of resources) {
      try {
        const response = await fetch(resource.url);
        const blob = await response.blob();
        await this.cacheResource(courseId, resource.url, blob, resource.mimeType);
      } catch {
        console.warn(`[OfflineCourseStorage] 资源下载失败: ${resource.url}`);
      }

      completed++;
      const progress = Math.round((completed / total) * 100);
      const progressMap = this.downloadProgressSubject.value;
      progressMap[courseId] = progress;
      this.downloadProgressSubject.next({ ...progressMap });
    }
  }

  private async clearCourseResources(courseId: string): Promise<void> {
    const assets = await this.getCourseResources(courseId);
    for (const asset of assets) {
      await this.offlineStorage.deleteData(OfflineStorageKey.ASSETS, asset.id);
    }
  }

  private async updateDownloadProgress(courseId: string): Promise<void> {
    const course = await this.getCachedCourse(courseId);
    if (!course || course.resources.length === 0) return;

    const resources = await this.getCourseResources(courseId);
    const progress = Math.round((resources.length / course.resources.length) * 100);

    course.downloadProgress = progress;
    await this.offlineStorage.setData(OfflineStorageKey.COURSES, course);
    await this.refreshCacheList();
  }

  private async refreshCacheList(): Promise<void> {
    const courses = await this.getCachedCourses();
    this.cachedCoursesSubject.next(courses);
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  }
}
