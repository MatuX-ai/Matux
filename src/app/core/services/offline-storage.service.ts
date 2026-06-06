import { isPlatformBrowser } from '@angular/common';
import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import {
  OfflineOperation,
  OfflineOperationStatus,
  OfflineStorageKey,
  OfflineStorageStats,
  OfflineSyncConfig,
} from '../models/offline.models';

/**
 * 离线数据存储服务
 * 使用IndexedDB存储离线数据，提供数据持久化和同步功能
 *
 * @description
 * 该服务负责：
 * 1. 管理IndexedDB数据库连接
 * 2. 提供数据的增删改查操作
 * 3. 维护离线操作队列
 * 4. 处理数据同步逻辑
 */
@Injectable({
  providedIn: 'root',
})
export class OfflineStorageService {
  /** 数据库名称 */
  private readonly DB_NAME = 'iMatuProject_OfflineDB';
  /** 数据库版本 — v3: 新增 courses(课程内容), progress(学习进度), assets(资源文件) */
  private readonly DB_VERSION = 3;
  /** 数据库实例 */
  private db: IDBDatabase | null = null;
  /** 是否运行在 Electron 环境 */
  private readonly isElectron: boolean;
  /** 大文件分片大小 (1MB) */
  private readonly CHUNK_SIZE = 1024 * 1024;

  /** 同步配置 */
  private syncConfig: OfflineSyncConfig = {
    autoSync: true,
    syncInterval: 30000,
    maxRetryAttempts: 3,
    minimumNetworkQuality: 'fast-3g',
    batchSize: 50,
  };

  /** 存储统计信息 */
  private statsSubject = new BehaviorSubject<OfflineStorageStats>({
    totalSize: 0,
    itemCounts: {},
    pendingOperations: 0,
  });

  /** 存储统计Observable */
  public stats$ = this.statsSubject.asObservable();

  constructor(@Inject(PLATFORM_ID) private platformId: object) {
    this.isElectron = !!(window as unknown as { electronAPI?: unknown }).electronAPI;
    if (isPlatformBrowser(platformId)) {
      this.initializeDatabase()
        .then(() => this.updateStats())
        .catch(() => {});
    }
  }

  /**
   * 初始化IndexedDB数据库
   */
  // eslint-disable-next-line max-lines-per-function, complexity
  private async initializeDatabase(): Promise<void> {
    return new Promise(
      // eslint-disable-next-line max-lines-per-function
      (resolve, reject) => {
        const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

        request.onerror = () => {
          reject(request.error);
        };

        request.onsuccess = () => {
          this.db = request.result;
          resolve();
        };

        // eslint-disable-next-line max-lines-per-function, complexity
        request.onupgradeneeded = (event) => {
          const db = (event.target as IDBOpenDBRequest).result;

          // 创建对象存储
          if (!db.objectStoreNames.contains('userData')) {
            const userStore = db.createObjectStore('userData', { keyPath: 'id' });
            userStore.createIndex('username', 'username', { unique: true });
            userStore.createIndex('email', 'email', { unique: true });
          }

          if (!db.objectStoreNames.contains('courseData')) {
            const courseStore = db.createObjectStore('courseData', { keyPath: 'id' });
            courseStore.createIndex('teacherId', 'teacherId');
            courseStore.createIndex('status', 'status');
          }

          if (!db.objectStoreNames.contains('taskData')) {
            const taskStore = db.createObjectStore('taskData', { keyPath: 'id' });
            taskStore.createIndex('assigneeId', 'assigneeId');
            taskStore.createIndex('status', 'status');
            taskStore.createIndex('dueDate', 'dueDate');
          }

          if (!db.objectStoreNames.contains('settings')) {
            db.createObjectStore('settings', { keyPath: 'key' });
          }

          if (!db.objectStoreNames.contains('cache')) {
            const cacheStore = db.createObjectStore('cache', { keyPath: 'key' });
            cacheStore.createIndex('expiresAt', 'expiresAt');
          }

          if (!db.objectStoreNames.contains('syncQueue')) {
            const queueStore = db.createObjectStore('syncQueue', { keyPath: 'id' });
            queueStore.createIndex('status', 'status');
            queueStore.createIndex('tableName', 'tableName');
            queueStore.createIndex('createdAt', 'createdAt');
          }

          // v2: 大文件分片存储 (Electron 离线实验数据)
          if (!db.objectStoreNames.contains('fileChunks')) {
            const chunkStore = db.createObjectStore('fileChunks', { keyPath: 'id' });
            chunkStore.createIndex('fileId', 'fileId');
            chunkStore.createIndex('chunkIndex', 'chunkIndex');
          }

          // v3: 课程内容离线缓存
          if (!db.objectStoreNames.contains('courses')) {
            const courseStore = db.createObjectStore('courses', { keyPath: 'id' });
            courseStore.createIndex('courseId', 'courseId', { unique: true });
            courseStore.createIndex('downloadedAt', 'downloadedAt');
            courseStore.createIndex('expiresAt', 'expiresAt');
          }

          // v3: 学习进度离线存储
          if (!db.objectStoreNames.contains('progress')) {
            const progressStore = db.createObjectStore('progress', { keyPath: 'id' });
            progressStore.createIndex('userId', 'userId');
            progressStore.createIndex('courseId', 'courseId');
            progressStore.createIndex('synced', 'synced');
            progressStore.createIndex('updatedAt', 'updatedAt');
          }

          // v3: 音频/图片等资源文件 blob 存储
          if (!db.objectStoreNames.contains('assets')) {
            const assetStore = db.createObjectStore('assets', { keyPath: 'id' });
            assetStore.createIndex('resourceUrl', 'resourceUrl', { unique: true });
            assetStore.createIndex('mimeType', 'mimeType');
            assetStore.createIndex('expiresAt', 'expiresAt');
          }
        };
      }
    );
  }

  /**
   * 获取数据库事务
   */
  private getTransaction(
    storeNames: string[],
    mode: IDBTransactionMode = 'readonly'
  ): IDBTransaction {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }
    return this.db.transaction(storeNames, mode);
  }

  /**
   * 获取对象存储
   */
  private getObjectStore(storeName: string, mode: IDBTransactionMode = 'readonly'): IDBObjectStore {
    const transaction = this.getTransaction([storeName], mode);
    return transaction.objectStore(storeName);
  }

  /**
   * 存储数据
   */
  public async setData<T>(key: OfflineStorageKey, data: T): Promise<void> {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(key, 'readwrite');
      const request = store.put(data);

      request.onsuccess = () => {
        void this.updateStats();
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 获取数据
   */
  public async getData<T>(key: OfflineStorageKey, id: string): Promise<T | undefined> {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(key);
      const request = store.get(id);

      request.onsuccess = () => {
        resolve(request.result as T);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 获取所有数据
   */
  public async getAllData<T>(key: OfflineStorageKey): Promise<T[]> {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(key);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 删除数据
   */
  public async deleteData(key: OfflineStorageKey, id: string): Promise<void> {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(key, 'readwrite');
      const request = store.delete(id);

      request.onsuccess = () => {
        void this.updateStats();
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 清空指定存储
   */
  public async clearStore(key: OfflineStorageKey): Promise<void> {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(key, 'readwrite');
      const request = store.clear();

      request.onsuccess = () => {
        void this.updateStats();
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 添加离线操作到队列
   */
  public async addOperation(
    operation: Omit<OfflineOperation, 'id' | 'createdAt' | 'updatedAt' | 'retryCount'>
  ): Promise<string> {
    const operationWithDefaults: OfflineOperation = {
      ...operation,
      id: this.generateId(),
      createdAt: new Date(),
      updatedAt: new Date(),
      retryCount: 0,
      status: OfflineOperationStatus.PENDING,
    };

    await this.setData(OfflineStorageKey.SYNC_QUEUE, operationWithDefaults);
    return operationWithDefaults.id;
  }

  /**
   * 更新操作状态
   */
  public async updateOperationStatus(
    id: string,
    status: OfflineOperationStatus,
    errorMessage?: string
  ): Promise<void> {
    const operation = await this.getData<OfflineOperation>(OfflineStorageKey.SYNC_QUEUE, id);
    if (operation) {
      operation.status = status;
      operation.updatedAt = new Date();
      if (errorMessage) {
        operation.errorMessage = errorMessage;
      }
      if (status === OfflineOperationStatus.FAILED) {
        operation.retryCount++;
      }
      await this.setData(OfflineStorageKey.SYNC_QUEUE, operation);
    }
  }

  /**
   * 获取待处理的操作
   */
  public async getPendingOperations(
    limit: number = this.syncConfig.batchSize
  ): Promise<OfflineOperation[]> {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(OfflineStorageKey.SYNC_QUEUE);
      const index = store.index('status');
      const request = index.getAll(OfflineOperationStatus.PENDING, limit);

      request.onsuccess = () => {
        resolve(request.result || []);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 更新存储统计信息
   */
  private async updateStats(): Promise<void> {
    if (!this.db) return;

    try {
      const itemCounts: Record<string, number> = {};
      let totalSize = 0;
      let pendingOperations = 0;

      // 统计各存储的数据量
      for (const key of Object.values(OfflineStorageKey)) {
        const count = await this.getStoreCount(key);
        itemCounts[key] = count;

        // 简单估算大小（实际应用中可能需要更精确的计算）
        totalSize += count * 1024; // 假设每个记录约1KB
      }

      // 统计待处理操作数
      pendingOperations = await this.getPendingOperationCount();

      this.statsSubject.next({
        totalSize,
        itemCounts,
        pendingOperations,
      });
    } catch {
      /* 统计更新失败不阻塞 */
    }
  }

  /**
   * 获取存储中的记录数
   */
  private async getStoreCount(storeName: string): Promise<number> {
    if (!this.db) return 0;

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(storeName);
      const request = store.count();

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 获取待处理操作数
   */
  private async getPendingOperationCount(): Promise<number> {
    if (!this.db) return 0;

    return new Promise((resolve, reject) => {
      const store = this.getObjectStore(OfflineStorageKey.SYNC_QUEUE);
      const index = store.index('status');
      const request = index.count(OfflineOperationStatus.PENDING);

      request.onsuccess = () => {
        resolve(request.result);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * 获取当前同步配置
   */
  public getSyncConfig(): OfflineSyncConfig {
    return { ...this.syncConfig };
  }

  /**
   * 更新同步配置
   */
  public updateSyncConfig(config: Partial<OfflineSyncConfig>): void {
    this.syncConfig = { ...this.syncConfig, ...config };
  }

  /**
   * 清理过期缓存
   */
  public async cleanupExpiredCache(): Promise<void> {
    if (!this.db) return;

    const now = new Date();
    const store = this.getObjectStore(OfflineStorageKey.CACHE, 'readwrite');
    const index = store.index('expiresAt');

    const expiredItems: Array<{ key: IDBValidKey }> = [];

    return new Promise((resolve, reject) => {
      const request = index.openCursor(IDBKeyRange.upperBound(now));

      request.onsuccess = (event: Event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;
        if (cursor) {
          expiredItems.push(cursor.value as { key: IDBValidKey });
          cursor.continue();
        } else {
          const deletePromises = expiredItems.map(
            (item) =>
              new Promise<void>((delResolve, delReject) => {
                const deleteReq = store.delete(item.key);
                deleteReq.onsuccess = () => delResolve();
                deleteReq.onerror = () => delReject(deleteReq.error);
              })
          );

          Promise.all(deletePromises)
            .then(() => {
              void this.updateStats();
              resolve();
            })
            .catch(reject);
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  // ==================== 大文件分片存储 (Electron 离线模式) ====================

  /**
   * 分片存储大文件（实验数据、课程视频等）
   * @param fileId 文件唯一标识
   * @param data 文件二进制数据
   * @param metadata 文件元数据
   */
  public async storeLargeFile(
    fileId: string,
    data: ArrayBuffer,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    if (!this.db) throw new Error('数据库未初始化');

    const totalChunks = Math.ceil(data.byteLength / this.CHUNK_SIZE);

    for (let i = 0; i < totalChunks; i++) {
      const chunk = data.slice(i * this.CHUNK_SIZE, (i + 1) * this.CHUNK_SIZE);
      await this.storeChunk(fileId, i, chunk);
    }

    // 存储元数据
    await this.setData(OfflineStorageKey.CACHE, {
      key: `file_meta_${fileId}`,
      fileId,
      totalChunks,
      totalSize: data.byteLength,
      metadata,
      storedAt: new Date().toISOString(),
    } as unknown as Record<string, unknown>);
  }

  /**
   * 读取分片大文件
   */
  public async loadLargeFile(fileId: string): Promise<ArrayBuffer | null> {
    if (!this.db) return null;

    const meta = await this.getData<{
      key: string;
      fileId: string;
      totalChunks: number;
      totalSize: number;
    }>(OfflineStorageKey.CACHE, `file_meta_${fileId}`);

    if (!meta) return null;

    const chunks: ArrayBuffer[] = [];
    for (let i = 0; i < meta.totalChunks; i++) {
      const chunk = await this.getChunk(fileId, i);
      if (!chunk) return null;
      chunks.push(chunk);
    }

    // 合并分片
    const result = new Uint8Array(meta.totalSize);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(new Uint8Array(chunk), offset);
      offset += chunk.byteLength;
    }
    return result.buffer;
  }

  /**
   * 删除大文件及其分片
   */
  public async deleteLargeFile(fileId: string): Promise<void> {
    if (!this.db) return;

    const meta = await this.getData<{ key: string; totalChunks: number }>(
      OfflineStorageKey.CACHE,
      `file_meta_${fileId}`
    );

    const deletePromises: Promise<void>[] = [];

    if (meta) {
      for (let i = 0; i < meta.totalChunks; i++) {
        deletePromises.push(this.deleteChunk(fileId, i));
      }
    }

    deletePromises.push(this.deleteData(OfflineStorageKey.CACHE, `file_meta_${fileId}`));

    await Promise.all(deletePromises);
  }

  /** 获取 Electron 环境状态 */
  public get isElectronEnv(): boolean {
    return this.isElectron;
  }

  private storeChunk(fileId: string, chunkIndex: number, data: ArrayBuffer): Promise<void> {
    return new Promise((resolve, reject) => {
      const store = this.getObjectStore('fileChunks', 'readwrite');
      const req = store.put({ id: `${fileId}_${chunkIndex}`, fileId, chunkIndex, data });
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  private getChunk(fileId: string, chunkIndex: number): Promise<ArrayBuffer | null> {
    return new Promise((resolve, reject) => {
      const store = this.getObjectStore('fileChunks', 'readonly');
      const req = store.get(`${fileId}_${chunkIndex}`);
      req.onsuccess = () => {
        const result = req.result as { data?: ArrayBuffer } | undefined;
        resolve(result?.data ?? null);
      };
      req.onerror = () => reject(req.error);
    });
  }

  private deleteChunk(fileId: string, chunkIndex: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const store = this.getObjectStore('fileChunks', 'readwrite');
      const req = store.delete(`${fileId}_${chunkIndex}`);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }
}
