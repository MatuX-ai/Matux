import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

import { OfflineStorageKey } from '../../../shared/models/offline.models';
import { OfflineStorageService } from '../../core/services/offline-storage.service';

/**
 * 学习进度记录
 */
export interface LearningProgress {
  id: string;
  userId: string;
  courseId: string;
  /** 课程总进度百分比 0-100 */
  overallProgress: number;
  /** 已完成课时数 */
  completedLessons: number;
  /** 总课时数 */
  totalLessons: number;
  /** 各课时完成状态 */
  lessonProgress: Record<string, LessonProgress>;
  /** 测验成绩记录 */
  quizScores: QuizScore[];
  /** 学习总时长（秒） */
  totalTimeSpent: number;
  /** 最后学习时间 */
  lastAccessedAt: Date;
  /** 更新时间 */
  updatedAt: Date;
  /** 是否已同步到服务器 */
  synced: boolean;
  /** 数据版本号（冲突解决用） */
  version: number;
}

/**
 * 课时进度
 */
export interface LessonProgress {
  lessonId: string;
  status: 'not_started' | 'in_progress' | 'completed';
  progress: number;
  timeSpent: number;
  lastPosition?: number;
  completedAt?: Date;
}

/**
 * 测验成绩
 */
export interface QuizScore {
  quizId: string;
  score: number;
  totalScore: number;
  percentage: number;
  completedAt: Date;
  synced: boolean;
}

/**
 * 进度同步冲突
 */
export interface ProgressConflict {
  local: LearningProgress;
  remote: LearningProgress;
  resolvedAt?: Date;
  resolutionStrategy?: 'local_wins' | 'remote_wins' | 'merged';
}

/**
 * 离线学习进度存储服务
 *
 * 负责学习进度的离线存储与同步：
 * - 本地进度追踪
 * - 与服务器进度同步
 * - 冲突检测与解决
 * - 合并策略
 */
@Injectable({
  providedIn: 'root',
})
export class OfflineProgressStorageService {
  private syncedProgressSubject = new BehaviorSubject<number>(0);
  public syncedProgress$: Observable<number> = this.syncedProgressSubject.asObservable();

  private conflictsSubject = new BehaviorSubject<ProgressConflict[]>([]);
  public conflicts$: Observable<ProgressConflict[]> = this.conflictsSubject.asObservable();

  constructor(private offlineStorage: OfflineStorageService) {}

  /**
   * 保存或更新学习进度
   */
  async saveProgress(progress: Omit<LearningProgress, 'id' | 'version'>): Promise<void> {
    const existing = await this.getProgress(progress.userId, progress.courseId);

    const record: LearningProgress = {
      ...progress,
      id: existing?.id ?? this.generateId(),
      version: existing ? existing.version + 1 : 1,
    };

    await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, record);
  }

  /**
   * 获取学习进度
   */
  async getProgress(userId: string, courseId: string): Promise<LearningProgress | undefined> {
    const allProgress = await this.offlineStorage.getAllData<LearningProgress>(
      OfflineStorageKey.PROGRESS,
    );
    return allProgress.find((p) => p.userId === userId && p.courseId === courseId);
  }

  /**
   * 获取用户的全部学习进度
   */
  async getUserProgress(userId: string): Promise<LearningProgress[]> {
    const allProgress = await this.offlineStorage.getAllData<LearningProgress>(
      OfflineStorageKey.PROGRESS,
    );
    return allProgress.filter((p) => p.userId === userId);
  }

  /**
   * 获取指定课程的全部用户进度
   */
  async getCourseProgresses(courseId: string): Promise<LearningProgress[]> {
    const allProgress = await this.offlineStorage.getAllData<LearningProgress>(
      OfflineStorageKey.PROGRESS,
    );
    return allProgress.filter((p) => p.courseId === courseId);
  }

  /**
   * 更新课时进度
   */
  async updateLessonProgress(
    userId: string,
    courseId: string,
    lessonId: string,
    updates: Partial<LessonProgress>,
  ): Promise<void> {
    const progress = await this.getProgress(userId, courseId);
    if (!progress) return;

    const existing = progress.lessonProgress[lessonId] ?? {
      lessonId,
      status: 'not_started' as const,
      progress: 0,
      timeSpent: 0,
    };

    progress.lessonProgress[lessonId] = { ...existing, ...updates };
    progress.synced = false;
    progress.updatedAt = new Date();
    progress.version++;

    // 重新计算总体进度
    progress.completedLessons = Object.values(progress.lessonProgress).filter(
      (lp) => lp.status === 'completed',
    ).length;
    progress.overallProgress = Math.round(
      (progress.completedLessons / progress.totalLessons) * 100,
    );

    await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, progress);
  }

  /**
   * 记录测验成绩
   */
  async addQuizScore(
    userId: string,
    courseId: string,
    quizScore: Omit<QuizScore, 'synced'>,
  ): Promise<void> {
    const progress = await this.getProgress(userId, courseId);
    if (!progress) return;

    // 避免重复添加相同测验的记录
    const existingIndex = progress.quizScores.findIndex((q) => q.quizId === quizScore.quizId);
    const newScore: QuizScore = { ...quizScore, synced: false };

    if (existingIndex >= 0) {
      progress.quizScores[existingIndex] = newScore;
    } else {
      progress.quizScores.push(newScore);
    }

    progress.synced = false;
    progress.updatedAt = new Date();
    progress.version++;

    await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, progress);
  }

  /**
   * 更新学习时长
   */
  async addTimeSpent(userId: string, courseId: string, seconds: number): Promise<void> {
    const progress = await this.getProgress(userId, courseId);
    if (!progress) return;

    progress.totalTimeSpent += seconds;
    progress.synced = false;
    progress.updatedAt = new Date();
    progress.lastAccessedAt = new Date();
    progress.version++;

    await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, progress);
  }

  /**
   * 标记进度已同步
   */
  async markAsSynced(userId: string, courseId: string): Promise<void> {
    const progress = await this.getProgress(userId, courseId);
    if (!progress) return;

    progress.synced = true;
    await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, progress);
    await this.updateSyncStats();
  }

  /**
   * 获取所有未同步的进度记录
   */
  async getUnsyncedProgress(): Promise<LearningProgress[]> {
    const allProgress = await this.offlineStorage.getAllData<LearningProgress>(
      OfflineStorageKey.PROGRESS,
    );
    return allProgress.filter((p) => !p.synced);
  }

  /**
   * 同步本地进度到远程服务器
   */
  async syncProgressToServer(
    userId: string,
    courseId: string,
    fetchRemoteProgress: () => Promise<LearningProgress | null>,
    pushLocalProgress: (progress: LearningProgress) => Promise<boolean>,
  ): Promise<'synced' | 'conflict' | 'error'> {
    const local = await this.getProgress(userId, courseId);
    if (!local) return 'synced';

    try {
      const remote = await fetchRemoteProgress();

      if (!remote) {
        // 远程无记录，直接推送
        const success = await pushLocalProgress(local);
        if (success) {
          await this.markAsSynced(userId, courseId);
          return 'synced';
        }
        return 'error';
      }

      // 冲突检测
      if (local.version > remote.version || local.updatedAt > new Date(remote.updatedAt)) {
        // 尝试合并
        const merged = this.mergeProgress(local, remote);
        if (merged) {
          merged.version = Math.max(local.version, remote.version) + 1;
          merged.synced = false;
          await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, merged);

          const success = await pushLocalProgress(merged);
          if (success) {
            await this.markAsSynced(userId, courseId);
            return 'synced';
          }
        } else {
          // 报告冲突
          const conflicts = this.conflictsSubject.value;
          conflicts.push({ local, remote });
          this.conflictsSubject.next([...conflicts]);
          return 'conflict';
        }
      }

      // 远程版本更新，使用远程数据
      await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, remote);
      return 'synced';
    } catch {
      return 'error';
    }
  }

  /**
   * 解决进度冲突
   */
  async resolveConflict(
    userId: string,
    courseId: string,
    strategy: 'local_wins' | 'remote_wins' | 'merged',
    remote?: LearningProgress,
  ): Promise<void> {
    const local = await this.getProgress(userId, courseId);
    if (!local) return;

    const resolved: LearningProgress =
      strategy === 'local_wins'
        ? local
        : strategy === 'remote_wins' && remote
          ? remote
          : this.mergeProgress(local, remote) ?? local;

    resolved.version++;
    resolved.synced = false;
    resolved.lastAccessedAt = new Date();
    resolved.updatedAt = new Date();

    await this.offlineStorage.setData(OfflineStorageKey.PROGRESS, resolved);

    // 从冲突列表中移除
    const remaining = this.conflictsSubject.value.filter(
      (c) => !(c.local.userId === userId && c.local.courseId === courseId),
    );
    this.conflictsSubject.next(remaining);
  }

  /**
   * 获取同步统计
   */
  async getSyncStats(): Promise<{ synced: number; unsynced: number; conflicts: number }> {
    const allProgress = await this.offlineStorage.getAllData<LearningProgress>(
      OfflineStorageKey.PROGRESS,
    );
    const unsynced = allProgress.filter((p) => !p.synced).length;
    return {
      synced: allProgress.length - unsynced,
      unsynced,
      conflicts: this.conflictsSubject.value.length,
    };
  }

  /**
   * 删除进度记录
   */
  async deleteProgress(userId: string, courseId: string): Promise<void> {
    const progress = await this.getProgress(userId, courseId);
    if (progress) {
      await this.offlineStorage.deleteData(OfflineStorageKey.PROGRESS, progress.id);
    }
  }

  /**
   * 合并本地和远程进度（字段级合并）
   */
  private mergeProgress(
    local: LearningProgress,
    remote?: LearningProgress | null,
  ): LearningProgress | null {
    if (!remote) return local;

    // 取较新的各字段值
    return {
      ...remote,
      overallProgress: Math.max(local.overallProgress, remote.overallProgress),
      completedLessons: Math.max(local.completedLessons, remote.completedLessons),
      totalLessons: Math.max(local.totalLessons, remote.totalLessons),
      totalTimeSpent: Math.max(local.totalTimeSpent, remote.totalTimeSpent),
      // 合并课时进度（取最新状态）
      lessonProgress: { ...remote.lessonProgress, ...local.lessonProgress },
      // 合并测验成绩（去重）
      quizScores: this.mergeQuizScores(local.quizScores, remote.quizScores),
      lastAccessedAt:
        local.lastAccessedAt > remote.lastAccessedAt ? local.lastAccessedAt : remote.lastAccessedAt,
      updatedAt: new Date(),
      synced: false,
    };
  }

  private mergeQuizScores(local: QuizScore[], remote: QuizScore[]): QuizScore[] {
    const merged = new Map<string, QuizScore>();
    for (const q of [...remote, ...local]) {
      const existing = merged.get(q.quizId);
      if (!existing || q.completedAt > existing.completedAt) {
        merged.set(q.quizId, q);
      }
    }
    return Array.from(merged.values());
  }

  private async updateSyncStats(): Promise<void> {
    const stats = await this.getSyncStats();
    this.syncedProgressSubject.next(Math.round((stats.synced / (stats.synced + stats.unsynced || 1)) * 100));
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  }
}
