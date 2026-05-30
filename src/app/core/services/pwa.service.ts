import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { filter, fromEvent, interval, map, Observable, startWith, switchMap } from 'rxjs';

import { AppStateService } from './app-state.service';

@Injectable({
  providedIn: 'root',
})
export class PwaService {
  constructor(
    private swUpdate: SwUpdate,
    private snackBar: MatSnackBar,
    private appState: AppStateService
  ) {
    this.initPwa();
  }

  /**
   * 初始化PWA功能
   */
  private initPwa(): void {
    // 检查Service Worker更新
    this.checkForUpdates();

    // 定期检查更新 (每小时)
    interval(60 * 60 * 1000)
      .pipe(
        startWith(0),
        switchMap(() => this.swUpdate.checkForUpdate())
      )
      .subscribe();
  }

  /**
   * 检查应用更新
   */
  private checkForUpdates(): void {
    if (!this.swUpdate.isEnabled) {
      console.log('Service Worker 未启用');
      return;
    }

    // 监听更新可用事件
    this.swUpdate.versionUpdates
      .pipe(filter((evt): evt is VersionReadyEvent => evt.type === 'VERSION_READY'))
      .subscribe((evt) => {
        const currentVersion = evt.currentVersion.hash.substring(0, 7);
        const newVersion = evt.latestVersion.hash.substring(0, 7);
        this.showUpdateNotification(currentVersion, newVersion);
      });

    // 监听更新事件
    this.swUpdate.versionUpdates
      .pipe(filter((event) => event.type === 'VERSION_READY'))
      .subscribe((event) => {
        console.log('新版本已准备就绪:', event);
        this.showUpdateSuccess();
      });
  }

  /**
   * 显示更新提示
   */
  private showUpdateNotification(currentVersion: string, newVersion: string): void {
    const duration = 300000; // 5分钟

    const snackBarRef = this.snackBar.open(`发现新版本 (v${newVersion})，点击立即更新`, '更新', {
      duration,
      horizontalPosition: 'center',
      verticalPosition: 'bottom',
    });

    snackBarRef.onAction().subscribe(() => {
      this.activateUpdate();
    });
  }

  /**
   * 显示更新成功提示
   */
  private showUpdateSuccess(): void {
    this.snackBar.open('应用已更新到最新版本！', '确定', {
      duration: 3000,
      horizontalPosition: 'center',
      verticalPosition: 'bottom',
    });
  }

  /**
   * 激活更新
   */
  public activateUpdate(): Promise<boolean> {
    return this.swUpdate
      .activateUpdate()
      .then(() => {
        window.location.reload();
        return true;
      })
      .catch((error) => {
        console.error('更新激活失败:', error);
        return false;
      });
  }

  /**
   * 检查应用是否支持离线
   */
  public checkOfflineSupport(): Promise<boolean> {
    return new Promise((resolve) => {
      if ('serviceWorker' in navigator && 'caches' in window) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  }

  /**
   * 获取离线状态
   */
  public getOfflineStatus(): Observable<boolean> {
    return fromEvent(window, 'offline').pipe(
      startWith(!navigator.onLine),
      map(() => !navigator.onLine)
    );
  }

  /**
   * 手动检查更新
   */
  public async manualCheckUpdate(): Promise<boolean> {
    if (!this.swUpdate.isEnabled) {
      this.snackBar.open('Service Worker未启用，无法检查更新', '确定', {
        duration: 3000,
      });
      return false;
    }

    const hasUpdate = await this.swUpdate.checkForUpdate();

    if (hasUpdate) {
      this.snackBar.open('发现新版本，正在下载...', '确定', {
        duration: 3000,
      });
    } else {
      this.snackBar.open('已是最新版本', '确定', {
        duration: 2000,
      });
    }

    return hasUpdate;
  }

  /**
   * 清除应用缓存
   */
  public async clearCache(): Promise<boolean> {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));

        this.snackBar.open('缓存已清除，正在重新加载...', '确定', {
          duration: 2000,
        });

        setTimeout(() => {
          window.location.reload();
        }, 2000);

        return true;
      }
      return false;
    } catch (error) {
      console.error('清除缓存失败:', error);
      return false;
    }
  }

  /**
   * 检查PWA安装条件
   */
  public canInstallPwa(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches === false;
  }

  /**
   * 添加安装提示监听器
   */
  public addInstallListener(): Observable<any> {
    return new Observable((observer) => {
      let deferredPrompt: any;

      const handleBeforeInstall = (e: Event) => {
        e.preventDefault();
        deferredPrompt = e;
        observer.next(deferredPrompt);
      };

      window.addEventListener('beforeinstallprompt', handleBeforeInstall);

      return () => {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      };
    });
  }

  /**
   * 提示用户安装PWA
   */
  public async promptInstall(prompt: any): Promise<boolean> {
    if (!prompt) {
      return false;
    }

    try {
      const { outcome } = await prompt.prompt();

      if (outcome === 'accepted') {
        this.snackBar.open('安装成功！', '确定', {
          duration: 3000,
        });
        return true;
      } else {
        this.snackBar.open('已取消安装', '确定', {
          duration: 2000,
        });
        return false;
      }
    } catch (error) {
      console.error('安装失败:', error);
      return false;
    }
  }

  /**
   * 获取应用版本信息
   */
  public getAppVersion(): string {
    const versionElement = document.querySelector('meta[name="version"]');
    return versionElement?.getAttribute('content') || '1.0.0';
  }

  /**
   * 预缓存关键资源
   */
  public async precacheCriticalResources(): Promise<void> {
    if (!('serviceWorker' in navigator)) {
      return;
    }

    try {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration?.active) {
        // 发送消息给Service Worker预缓存资源
        registration.active.postMessage({
          type: 'PRECACHE',
          resources: [
            '/',
            '/dashboard',
          ],
        });
      }
    } catch (error) {
      console.error('预缓存失败:', error);
    }
  }

  /**
   * 检查网络连接状态
   */
  public getNetworkStatus(): Observable<'online' | 'offline' | 'slow'> {
    return new Observable((observer) => {
      const checkStatus = () => {
        if (!navigator.onLine) {
          observer.next('offline');
        } else {
          // 使用navigator.connection检测网络质量(如果支持)
          const connection = (navigator as any).connection;
          if (connection?.effectiveType) {
            const slowTypes = ['slow-2g', '2g'];
            observer.next(slowTypes.includes(connection.effectiveType) ? 'slow' : 'online');
          } else {
            observer.next('online');
          }
        }
      };

      checkStatus();

      const handleOnline = () => checkStatus();
      const handleOffline = () => checkStatus();

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    });
  }

  /**
   * 添加离线监听器
   */
  public addOfflineListener(callback: (isOffline: boolean) => void): () => void {
    const handleOnline = () => callback(false);
    const handleOffline = () => callback(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // 立即检查一次
    callback(!navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }

  /**
   * 估算离线缓存大小
   */
  public async estimateCacheSize(): Promise<{ size: number; count: number }> {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        let totalSize = 0;
        let count = 0;

        for (const cacheName of cacheNames) {
          const cache = await caches.open(cacheName);
          const keys = await cache.keys();
          count += keys.length;

          for (const request of keys) {
            const response = await cache.match(request);
            if (response) {
              const blob = await response.blob();
              totalSize += blob.size;
            }
          }
        }

        return {
          size: totalSize,
          count,
        };
      }
      return { size: 0, count: 0 };
    } catch (error) {
      console.error('估算缓存大小失败:', error);
      return { size: 0, count: 0 };
    }
  }

  /**
   * 显示离线提示
   */
  public showOfflineBanner(): void {
    this.snackBar.open('当前处于离线状态，部分功能可能不可用', '知道了', {
      duration: 5000,
      horizontalPosition: 'center',
      verticalPosition: 'bottom',
    });
  }

  /**
   * 显示重新连接提示
   */
  public showReconnectedBanner(): void {
    this.snackBar.open('网络已重新连接', '确定', {
      duration: 3000,
      horizontalPosition: 'center',
      verticalPosition: 'bottom',
    });
  }

  /**
   * 检查是否为PWA运行模式
   */
  public isStandalone(): boolean {
    return (
      window.matchMedia('(display-mode: standalone)').matches ||
      (window.navigator as any).standalone === true
    );
  }

  /**
   * 获取应用安装状态
   */
  public getInstallState(): 'installed' | 'installable' | 'not-supported' {
    if (this.isStandalone()) {
      return 'installed';
    }
    if (this.canInstallPwa()) {
      return 'installable';
    }
    return 'not-supported';
  }

  /**
   * 配置Service Worker更新策略
   */
  public configureUpdateStrategy(strategy: 'immediate' | 'manual' | 'background'): void {
    this.appState.setPwaUpdateStrategy(strategy);
  }

  /**
   * 检查后台同步支持
   */
  public async checkBackgroundSyncSupport(): Promise<boolean> {
    return 'serviceWorker' in navigator && 'SyncManager' in window;
  }

  /**
   * 注册后台同步任务
   */
  public async registerBackgroundSync(tag: string): Promise<boolean> {
    try {
      const registration = await navigator.serviceWorker.ready;
      // 使用类型断言避免 TypeScript 错误
      const syncRegistration = registration as any;
      if (syncRegistration.sync) {
        await syncRegistration.sync.register(tag);
        return true;
      }
      console.warn('后台同步 API 不可用');
      return false;
    } catch (error) {
      console.error('注册后台同步失败:', error);
      return false;
    }
  }
}
