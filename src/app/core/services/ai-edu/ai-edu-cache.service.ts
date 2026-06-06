import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

/**
 * 缂撳瓨閰嶇疆
 */
interface CacheConfig {
  ttl: number; // 缓存时间 (毫秒)
  maxSize: number; // 最大缓存条目数
  prefix?: string; // 缓存键前缀
}

/**
 * 缓存条目
 */
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

/**
 * 缓存统计信息
 */
interface CacheStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  memoryCacheSize: number;
  hitRate: number;
}

/**
 * AI-Edu 缓存服务
 * 提供内存缓存、IndexedDB 持久化缓存 */
@Injectable({
  providedIn: 'root',
})
export class AIEduCacheService {
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 鍒嗛挓
  private readonly DEFAULT_MAX_SIZE = 100;

  // 鍐呭瓨缂撳瓨
  private memoryCache = new Map<string, CacheEntry<unknown>>();

  // IndexedDB 缂撳瓨 (寮傛)
  private indexedDB: IDBDatabase | null = null;
  private dbReady = new BehaviorSubject<boolean>(false);

  // 缂撳瓨缁熻
  private stats = {
    hits: 0,
    misses: 0,
    sets: 0,
    deletes: 0,
  };

  constructor(private http: HttpClient) {
    this.initIndexedDB();
  }

  /**
   * 鍒濆鍖?IndexedDB
   */
  private initIndexedDB(): void {
    if (typeof window === 'undefined' || !window.indexedDB) {
      this.dbReady.next(false);
      return;
    }

    const request = window.indexedDB.open('AIEduCache', 1);

    request.onerror = () => {
      this.dbReady.next(false);
    };

    request.onsuccess = () => {
      this.indexedDB = request.result;
      this.dbReady.next(true);
    };

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      if (!db.objectStoreNames.contains('cache')) {
        const store = db.createObjectStore('cache', { keyPath: 'key' });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('expiresAt', 'expiresAt', { unique: false });
      }
    };
  }

  /**
   * 鑾峰彇缂撳瓨 (浼樺厛鍐呭瓨锛屽叾娆?IndexedDB)
   */
  get<T>(key: string, _config: CacheConfig = this.getDefaultConfig()): Observable<T | null> {
    // 灏濊瘯鍐呭瓨缂撳瓨
    const memoryEntry = this.memoryCache.get(key);
    if (memoryEntry && Date.now() < memoryEntry.expiresAt) {
      this.stats.hits++;
      return new Observable((observer) => {
        observer.next(memoryEntry.data as T);
        observer.complete();
      });
    }

    // 灏濊瘯 IndexedDB
    return new Observable((observer) => {
      if (this.indexedDB) {
        const transaction = this.indexedDB.transaction(['cache'], 'readonly');
        const store = transaction.objectStore('cache');
        const request = store.get(key);

        request.onsuccess = () => {
          const entry = request.result as CacheEntry<T>;
          if (entry && Date.now() < entry.expiresAt) {
            this.stats.hits++;
            // 鍥炲～鍒板唴瀛樼紦瀛?            this.memoryCache.set(key, entry);
            observer.next(entry.data);
          } else {
            this.stats.misses++;
            observer.next(null);
          }
          observer.complete();
        };

        request.onerror = () => {
          this.stats.misses++;
          observer.next(null);
          observer.complete();
        };
      } else {
        this.stats.misses++;
        observer.next(null);
        observer.complete();
      }
    });
  }

  /**
   * 璁剧疆缂撳瓨 (鍚屾椂鍐欏叆鍐呭瓨鍜?IndexedDB)
   */
  set<T>(key: string, data: T, config: CacheConfig = this.getDefaultConfig()): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + config.ttl,
    };

    // 鍐欏叆鍐呭瓨缂撳瓨
    if (this.memoryCache.size >= config.maxSize) {
      // 娓呯悊鏈€鏃х殑鏉＄洰
      const oldestKey = this.memoryCache.keys().next().value;
      if (oldestKey) {
        this.memoryCache.delete(oldestKey);
      }
    }
    this.memoryCache.set(key, entry);

    // 鍐欏叆 IndexedDB
    if (this.indexedDB) {
      const transaction = this.indexedDB.transaction(['cache'], 'readwrite');
      const store = transaction.objectStore('cache');
      store.put({ key, ...entry });
    }

    this.stats.sets++;
  }

  /**
   * 鍒犻櫎缂撳瓨
   */
  delete(key: string): void {
    this.memoryCache.delete(key);

    if (this.indexedDB) {
      const transaction = this.indexedDB.transaction(['cache'], 'readwrite');
      const store = transaction.objectStore('cache');
      store.delete(key);
    }

    this.stats.deletes++;
  }

  /**
   * 清除所有缓存
   */
  clear(pattern?: string): void {
    if (pattern) {
      // 按模式清除
      this.memoryCache.forEach((_, key) => {
        if (key.includes(pattern)) {
          this.memoryCache.delete(key);
        }
      });

      if (this.indexedDB) {
        // IndexedDB 需要遍历
        const transaction = this.indexedDB.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        const request = store.getAllKeys();

        request.onsuccess = () => {
          const keys = request.result as string[];
          keys.forEach((key) => {
            if (key.includes(pattern)) {
              store.delete(key);
            }
          });
        };
      }
    } else {
      // 娓呴櫎鍏ㄩ儴
      this.memoryCache.clear();

      if (this.indexedDB) {
        const transaction = this.indexedDB.transaction(['cache'], 'readwrite');
        const store = transaction.objectStore('cache');
        store.clear();
      }
    }
  }

  /**
   * 妫€鏌ョ紦瀛樻槸鍚︽湁鏁?   */
  isValid(key: string): boolean {
    const entry = this.memoryCache.get(key);
    if (entry && Date.now() < entry.expiresAt) {
      return true;
    }

    // 妫€鏌?IndexedDB (鍚屾鏂瑰紡绠€鍖栧鐞?
    return false;
  }

  /**
   * 鑾峰彇缂撳瓨缁熻淇℃伅
   */
  getStats(): CacheStats {
    return {
      ...this.stats,
      memoryCacheSize: this.memoryCache.size,
      hitRate: (this.stats.hits / (this.stats.hits + this.stats.misses)) * 100 || 0,
    };
  }

  /**
   * 棰勫姞杞芥暟鎹埌缂撳瓨
   */
  preload<T>(
    key: string,
    fetchFn: () => Observable<T>,
    config: CacheConfig = this.getDefaultConfig()
  ): Observable<T> {
    return fetchFn().pipe(
      tap((data) => this.set(key, data, config)),
      catchError((error) => {
        throw error;
      })
    );
  }

  /**
   * 甯︾紦瀛樼殑 HTTP GET 璇锋眰
   */
  httpGet<T>(url: string, config: CacheConfig = this.getDefaultConfig()): Observable<T> {
    const cacheKey = `http:${url}`;

    return new Observable((observer) => {
      this.get<T>(cacheKey, config).subscribe((cached) => {
        if (cached !== null) {
          observer.next(cached);
          observer.complete();
        } else {
          this.http
            .get<T>(url)
            .pipe(
              tap((data) => this.set(cacheKey, data, config)),
              catchError((error) => {
                throw error;
              })
            )
            .subscribe({
              next: (data) => {
                observer.next(data);
                observer.complete();
              },
              error: (error) => observer.error(error),
            });
        }
      });
    });
  }

  /**
   * 鑾峰彇榛樿閰嶇疆
   */
  private getDefaultConfig(): CacheConfig {
    return {
      ttl: this.DEFAULT_TTL,
      maxSize: this.DEFAULT_MAX_SIZE,
    };
  }

  /**
   * 瀵煎嚭缂撳瓨鏁版嵁
   */
  exportCache(): Promise<Record<string, unknown>> {
    const exportData: Record<string, unknown> = {};

    this.memoryCache.forEach((entry, key) => {
      exportData[key] = entry.data;
    });

    return Promise.resolve(exportData);
  }

  /**
   * 瀵煎叆缂撳瓨鏁版嵁
   */
  importCache(data: Record<string, unknown>, config: CacheConfig = this.getDefaultConfig()): void {
    Object.entries(data).forEach(([key, value]) => {
      this.set(key, value, config);
    });
  }
}
