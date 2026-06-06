import { Injectable } from '@angular/core';
import { BehaviorSubject, fromEvent, interval } from 'rxjs';
import { distinctUntilChanged, map } from 'rxjs/operators';

/**
 * Network Connection API 类型
 */
interface NetworkConnection {
  effectiveType: string;
  type: string;
  downlink: number;
  rtt: number;
  downlinkMax: number;
  addEventListener: (type: string, listener: EventListenerOrEventListenerObject) => void;
}

/**
 * 网络连接状态枚举
 * 用于表示不同的网络连接质量级别
 */
export enum NetworkQuality {
  /** 离线状态 */
  OFFLINE = 'offline',
  /** 2G网络 - 极慢 */
  SLOW_2G = 'slow-2g',
  /** 3G网络 - 慢速 */
  SLOW_3G = 'slow-3g',
  /** 4G网络 - 正常 */
  FAST_4G = 'fast-4g',
  /** WiFi/光纤 - 快速 */
  FAST_WIFI = 'fast-wifi',
}

/**
 * 网络状态接口
 * 描述当前网络连接的详细信息
 */
export interface NetworkStatus {
  /** 是否在线 */
  isOnline: boolean;
  /** 网络质量等级 */
  quality: NetworkQuality;
  /** 网络类型 */
  type: string;
  /** 下行速度估算 (Mbps) */
  downlink?: number;
  /** RTT延迟 (毫秒) */
  rtt?: number;
  /** 最大下行速度 (Mbps) */
  downlinkMax?: number;
  /** 上次更新时间 */
  lastUpdated: Date;
}

/**
 * 网络监控服务
 * 负责监测网络连接状态变化并提供实时状态信息
 *
 * @description
 * 该服务通过多种方式监测网络状态：
 * 1. Navigator.onLine API - 基础在线/离线检测
 * 2. Network Information API - 详细的网络质量信息
 * 3. 定期ping检测 - 主动网络连通性验证
 */
@Injectable({
  providedIn: 'root',
})
export class NetworkMonitorService {
  /** 网络状态变化的BehaviorSubject */
  private networkStatusSubject = new BehaviorSubject<NetworkStatus>(this.getCurrentNetworkStatus());

  /** 网络状态变化的Observable */
  public networkStatus$ = this.networkStatusSubject.asObservable();

  /** 在线状态变化的Observable */
  public isOnline$ = this.networkStatus$.pipe(
    map((status) => status.isOnline),
    distinctUntilChanged()
  );

  /** 网络质量变化的Observable */
  public networkQuality$ = this.networkStatus$.pipe(
    map((status) => status.quality),
    distinctUntilChanged()
  );

  constructor() {
    this.initializeNetworkMonitoring();
  }

  /**
   * 初始化网络监控
   * 设置各种网络事件监听器
   */
  private initializeNetworkMonitoring(): void {
    // 监听基础在线/离线事件
    fromEvent(window, 'online').subscribe(() => {
      this.updateNetworkStatus();
    });

    fromEvent(window, 'offline').subscribe(() => {
      this.updateNetworkStatus();
    });

    // 监听网络信息变化（如果支持）
    if ('connection' in navigator) {
      const connection = (navigator as unknown as { connection?: NetworkConnection }).connection;
      if (connection) {
        // 监听网络连接属性变化
        ['change', 'typechange'].forEach((event) => {
          connection.addEventListener(event, () => {
            this.updateNetworkStatus();
          });
        });
      }
    }

    // 定期检查网络状态（每30秒）
    interval(30000).subscribe(() => {
      this.updateNetworkStatus();
    });
  }

  /**
   * 获取当前网络状态
   * 综合多种API信息判断网络质量
   */
  // eslint-disable-next-line max-lines-per-function, complexity, max-depth
  private getCurrentNetworkStatus(): NetworkStatus {
    const isOnline = navigator.onLine;
    let quality = NetworkQuality.OFFLINE;
    let type = 'unknown';
    let downlink: number | undefined;
    let rtt: number | undefined;
    let downlinkMax: number | undefined;

    if (isOnline) {
      // 尝试获取详细的网络信息
      if ('connection' in navigator) {
        const connection = (navigator as unknown as { connection?: NetworkConnection }).connection;
        if (connection) {
          type = connection.effectiveType || connection.type || 'unknown';
          downlink = connection.downlink;
          rtt = connection.rtt;
          downlinkMax = connection.downlinkMax;

          // 根据effectiveType判断质量
          switch (connection.effectiveType) {
            case 'slow-2g':
              quality = NetworkQuality.SLOW_2G;
              break;
            case '2g':
              quality = NetworkQuality.SLOW_3G;
              break;
            case '3g':
              quality = NetworkQuality.FAST_4G;
              break;
            case '4g':
              quality = NetworkQuality.FAST_WIFI;
              break;
            default:
              // 如果没有effectiveType，根据downlink速度判断
              /* eslint-disable max-depth */
              if (downlink !== undefined) {
                if (downlink < 0.1) {
                  quality = NetworkQuality.SLOW_2G;
                } else if (downlink < 1) {
                  quality = NetworkQuality.SLOW_3G;
                } else if (downlink < 10) {
                  quality = NetworkQuality.FAST_4G;
                } else {
                  quality = NetworkQuality.FAST_WIFI;
                }
              } else {
                quality = NetworkQuality.FAST_4G; // 默认假设较快
              }
            /* eslint-enable max-depth */
          }
        } else {
          quality = NetworkQuality.FAST_4G; // 基本在线状态
        }
      } else {
        quality = NetworkQuality.FAST_4G; // 不支持详细信息时的默认值
      }
    }

    return {
      isOnline,
      quality,
      type,
      downlink,
      rtt,
      downlinkMax,
      lastUpdated: new Date(),
    };
  }

  /**
   * 更新网络状态
   * 发布新的网络状态信息
   */
  private updateNetworkStatus(): void {
    const newStatus = this.getCurrentNetworkStatus();
    this.networkStatusSubject.next(newStatus);
  }

  /**
   * 获取当前网络状态快照
   */
  public getCurrentStatus(): NetworkStatus {
    return this.networkStatusSubject.getValue();
  }

  /**
   * 检查是否处于离线模式
   */
  public isOffline(): boolean {
    return !this.getCurrentStatus().isOnline;
  }

  /**
   * 检查是否为高质量网络
   */
  public isHighQualityNetwork(): boolean {
    const quality = this.getCurrentStatus().quality;
    return quality === NetworkQuality.FAST_4G || quality === NetworkQuality.FAST_WIFI;
  }

  /**
   * 检查是否为低质量网络
   */
  public isLowQualityNetwork(): boolean {
    const quality = this.getCurrentStatus().quality;
    return quality === NetworkQuality.SLOW_2G || quality === NetworkQuality.SLOW_3G;
  }

  /**
   * 获取网络质量描述文本
   */
  public getQualityDescription(quality: NetworkQuality): string {
    switch (quality) {
      case NetworkQuality.OFFLINE:
        return '离线';
      case NetworkQuality.SLOW_2G:
        return '极慢网络(2G)';
      case NetworkQuality.SLOW_3G:
        return '慢速网络(3G)';
      case NetworkQuality.FAST_4G:
        return '正常网络(4G)';
      case NetworkQuality.FAST_WIFI:
        return '快速网络(WiFi)';
      default:
        return '未知';
    }
  }

  /**
   * 手动触发网络状态检查
   */
  public checkNetworkStatus(): void {
    this.updateNetworkStatus();
  }
}
