import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, HostListener, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { interval, Observable, Subject } from 'rxjs';
import { switchMap, takeUntil } from 'rxjs/operators';

// UnityLoader 接口定义
interface UnityLoaderStatic {
  instantiate(
    element: HTMLElement,
    buildUrl: string,
    options?: {
      onProgress?: (instance: UnityInstance, progress: number) => void;
      onError?: (error: Error) => void;
      onSuccess?: () => void;
      [key: string]: unknown;
    }
  ): UnityInstance;
}

// 声明全局 Unity 变量
declare const UnityLoader: UnityLoaderStatic;

// Unity实例接口
interface UnityInstance {
  Quit(): void;
  SendMessage(gameObject: string, methodName: string, parameter?: string): void;
}

// 传感器数据接口
interface SensorData {
  [key: string]: unknown;
}

// 实验数据接口
interface ExperimentData {
  id?: string;
  name?: string;
  status?: string;
  [key: string]: unknown;
}

/**
 * AR实验室组件
 * 负责加载和管理Unity WebGL AR实验室应用
 */
@Component({
  selector: 'app-ar-lab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatFormFieldModule,
  ],
  templateUrl: './ar-lab.component.html',
  styleUrls: ['./ar-lab.component.scss'],
})
export class ARLabComponent implements OnInit, OnDestroy {
  @ViewChild('unityContainer') unityContainer!: ElementRef;

  // Unity实例管理
  unityInstance: UnityInstance | null = null;
  isUnityLoaded = false;
  isLoading = true;
  errorMessage = '';

  // AR状态控制
  isARSupported = false;
  isTracking = false;
  arStatusMessage = '';
  gpuAccelerationLevel: 'webgl2' | 'webgl1' | 'none' = 'none';
  gpuRendererInfo = '';

  // 硬件连接状态
  hardwareConnected = false;
  connectionStatus = '未连接';
  availablePorts: string[] = [];
  selectedPort: string = '';

  // 实验数据
  experimentData: ExperimentData[] = [];
  currentExperiment: ExperimentData | null = null;
  isExperimentRunning = false;

  // 传感器数据
  sensorData: SensorData = {};
  lastUpdateTime = Date.now();

  // 全屏状态
  isFullscreen = false;

  // 组件生命周期管理
  private destroy$ = new Subject<void>();

  constructor(
    private http: HttpClient,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.checkARSupport();
    this.loadUnityApplication();
    this.startSensorDataPolling();
    this.setupFullscreenListener();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    // 清理 Unity实例
    if (this.unityInstance) {
      this.unityInstance.Quit();
      this.unityInstance = null;
    }
  }

  /**
   * 检查AR支持情况（含 GPU 加速检测和 WebGL2 降级策略）
   * PRD F-08 桌面端适配：GPU 加速
   */
  private checkARSupport(): void {
    // 优先检测 WebGL2（GPU 加速渲染），降级到 WebGL1
    const canvas = document.createElement('canvas');
    let gl: WebGL2RenderingContext | WebGLRenderingContext | null = canvas.getContext('webgl2');

    if (gl) {
      // WebGL2 可用，GPU 加速支持最佳
      this.isARSupported = true;
      this.gpuAccelerationLevel = 'webgl2';
    } else {
      // 降级到 WebGL1
      gl = canvas.getContext('webgl') as WebGLRenderingContext | null
        ?? canvas.getContext('experimental-webgl') as WebGLRenderingContext | null;
      if (gl) {
        this.isARSupported = true;
        this.gpuAccelerationLevel = 'webgl1';
      } else {
        this.isARSupported = false;
        this.arStatusMessage = '您的浏览器不支持WebGL';
        return;
      }
    }

    // 检查 GPU 渲染器信息（调试用）
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        this.gpuRendererInfo = String(renderer);
      }
    }

    // 检查摄像头权限
    if (navigator.mediaDevices?.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ video: true })
        .then((stream) => {
          stream.getTracks().forEach((track) => track.stop());
          this.isARSupported = true;
          this.arStatusMessage = 'AR功能可用';
        })
        .catch(() => {
          this.isARSupported = false;
          this.arStatusMessage = '需要摄像头权限才能使用AR功能';
        });
    } else {
      this.isARSupported = false;
      this.arStatusMessage = '您的浏览器不支持媒体设备API';
    }
  }

  /**
   * 加载 Unity WebGL 应用程序
   */
  loadUnityApplication(): void {
    try {
      // 检查 UnityLoader 是否可用
      if (typeof UnityLoader === 'undefined') {
        this.errorMessage = 'Unity WebGL 运行时未加载。请确认 Unity 构建已部署到 /ar-lab/build/ 目录。';
        this.isLoading = false;
        this.snackBar.open(this.errorMessage, '关闭', { duration: 5000 });
        return;
      }

      // Unity 构建文件路径
      const buildUrl = '/ar-lab/build/ARLabMain.json';

      // 创建Unity实例
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
      this.unityInstance = UnityLoader.instantiate(
        this.unityContainer.nativeElement as HTMLElement,
        buildUrl,
        {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onProgress: (_instance: any, progress: number) => {
            this.handleUnityProgress(progress);
          },
          onError: (error: Error) => {
            this.handleUnityError(error);
          },
          onSuccess: () => {
            this.handleUnitySuccess();
          },
        }
      );
    } catch (error) {
      this.handleUnityError(error);
    }
  }

  /**
   * 处理Unity加载进度
   */
  private handleUnityProgress(progress: number): void {
    if (progress >= 1) {
      this.isLoading = false;
    }
  }

  /**
   * 处理Unity加载成功
   */
  private handleUnitySuccess(): void {
    this.isUnityLoaded = true;
    this.isLoading = false;
    this.snackBar.open('AR实验室加载成功', '关闭', { duration: 3000 });
  }

  /**
   * 处理 Unity 加载错误
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private handleUnityError(error: any): void {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    this.errorMessage = `Unity 加载失败：${error.message ?? error}`;
    this.isLoading = false;
    this.snackBar.open(this.errorMessage, '关闭', { duration: 5000 });
  }

  /**
   * 开始传感器数据轮询
   */
  private startSensorDataPolling(): void {
    interval(1000) // 每秒更新一次
      .pipe(
        takeUntil(this.destroy$),
        switchMap(() => this.fetchSensorData())
      )
      .subscribe({
        next: (data) => {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
          this.sensorData = data;
          this.lastUpdateTime = Date.now();
        },
        error: (_error) => {},
      });
  }

  /**
   * 获取传感器数据
   */
  private fetchSensorData(): Observable<SensorData> {
    return this.http.get<SensorData>('/api/v1/sensor-data/latest');
  }

  /**
   * 搜索可用的串口设备
   */
  searchHardwareDevices(): void {
    this.http.get<string[]>('/api/v1/hardware/ports').subscribe({
      next: (ports) => {
        this.availablePorts = ports;
        this.snackBar.open(`发现 ${ports.length} 个可用设备`, '关闭', { duration: 2000 });
      },
      error: (_error) => {
        this.snackBar.open('设备搜索失败', '关闭', { duration: 3000 });
      },
    });
  }

  /**
   * 连接硬件设备
   */
  connectHardware(port: string): void {
    this.http
      .post<{ connected: boolean; message?: string }>('/api/v1/hardware/connect', { port })
      .subscribe({
        next: (response) => {
          if (response && typeof response.connected === 'boolean') {
            this.hardwareConnected = response.connected;
            this.connectionStatus = response.connected ? '已连接' : '连接失败';
            this.snackBar.open(response.connected ? '硬件连接成功' : '硬件连接失败', '关闭', {
              duration: 3000,
            });
          }
        },
        error: (_error) => {
          this.connectionStatus = '连接错误';
          this.snackBar.open('连接过程中发生错误', '关闭', { duration: 3000 });
        },
      });
  }

  /**
   * 断开硬件连接
   */
  disconnectHardware(): void {
    this.http.post('/api/v1/hardware/disconnect', {}).subscribe({
      next: () => {
        this.hardwareConnected = false;
        this.connectionStatus = '未连接';
        this.snackBar.open('硬件已断开连接', '关闭', { duration: 2000 });
      },
      error: (_error) => {},
    });
  }

  /**
   * 开始实验
   */
  startExperiment(): void {
    if (!this.hardwareConnected) {
      this.snackBar.open('请先连接硬件设备', '关闭', { duration: 3000 });
      return;
    }

    this.http.post('/api/v1/experiments/start', {}).subscribe({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment
      next: (experiment: any) => {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        this.currentExperiment = experiment;
        this.isExperimentRunning = true;
        this.snackBar.open('实验开始', '关闭', { duration: 2000 });
      },
      error: (_error) => {
        this.snackBar.open('实验启动失败', '关闭', { duration: 3000 });
      },
    });
  }

  /**
   * 停止实验
   */
  stopExperiment(): void {
    this.http.post('/api/v1/experiments/stop', {}).subscribe({
      next: () => {
        this.isExperimentRunning = false;
        this.currentExperiment = null;
        this.snackBar.open('实验已停止', '关闭', { duration: 2000 });
      },
      error: (_error) => {},
    });
  }

  /**
   * 重置 AR 场景
   */
  resetARScene(): void {
    if (this.unityInstance) {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
      this.unityInstance.SendMessage('ARManager', 'ResetScene');
      this.snackBar.open('AR 场景已重置', '关闭', { duration: 2000 });
    }
  }

  /**
   * 切换AR跟踪模式
   */
  toggleARTracking(): void {
    this.isTracking = !this.isTracking;
    if (this.unityInstance) {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
      this.unityInstance.SendMessage('ARManager', 'ToggleTracking', this.isTracking.toString());
    }
    this.snackBar.open(this.isTracking ? 'AR 跟踪已启用' : 'AR 跟踪已禁用', '关闭', {
      duration: 2000,
    });
  }

  /**
   * 监听全屏变化事件，同步状态
   */
  private setupFullscreenListener(): void {
    document.addEventListener('fullscreenchange', () => {
      this.isFullscreen = !!document.fullscreenElement;
    });
  }

  /**
   * 键盘快捷键处理（F11 / F / Esc）
   */
  @HostListener('document:keydown', ['$event'])
  handleKeyboardShortcut(event: KeyboardEvent): void {
    // F11 → 切换全屏
    if (event.key === 'F11') {
      event.preventDefault();
      this.toggleFullscreen();
      return;
    }

    // F 键（非输入框中）→ 切换全屏
    if ((event.key === 'f' || event.key === 'F') &&
        !(event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement)) {
      event.preventDefault();
      this.toggleFullscreen();
      return;
    }

    // Esc 退出全屏时提示
    if (event.key === 'Escape' && document.fullscreenElement) {
      this.snackBar.open('已退出全屏模式', '关闭', { duration: 1000 });
    }

    // Ctrl+Shift+R 重置 AR 场景
    if (event.key === 'R' && event.ctrlKey && event.shiftKey) {
      event.preventDefault();
      this.resetARScene();
    }
  }

  /**
   * 获取状态信息
   */
  getStatusInfo(): {
    unityLoaded: boolean;
    arSupported: boolean;
    arTracking: boolean;
    hardwareConnected: boolean;
    experimentRunning: boolean;
    lastUpdate: number;
  } {
    return {
      unityLoaded: this.isUnityLoaded,
      arSupported: this.isARSupported,
      arTracking: this.isTracking,
      hardwareConnected: this.hardwareConnected,
      experimentRunning: this.isExperimentRunning,
      lastUpdate: this.lastUpdateTime,
    };
  }

  /**
   * 获取传感器数值（用于模板显示）
   */
  getSensorValue(key: string): number | null {
    const value = this.sensorData[key];
    return typeof value === 'number' ? value : null;
  }

  /**
   * 获取实验开始时间（用于模板显示）
   */
  getExperimentStartTime(): number | null {
    if (!this.currentExperiment) return null;
    const startTime = this.currentExperiment['startTime'];
    return typeof startTime === 'number' ? startTime : null;
  }

  /**
   * 切换全屏模式（AR实验室大屏适配）
   */
  toggleFullscreen(): void {
    const container = document.querySelector('.ar-lab-container') as HTMLElement;
    if (!container) return;

    if (!document.fullscreenElement) {
      void container.requestFullscreen().then(() => {
        this.isFullscreen = true;
        // AR体验锁定横屏
        if ((screen.orientation as unknown as { lock?: (o: string) => Promise<void> })?.lock) {
          void (screen.orientation as unknown as { lock: (o: string) => Promise<void> }).lock('landscape').catch(() => {});
        }
        this.snackBar.open('全屏模式已启用 (Esc 退出)', '关闭', { duration: 2000 });
      }).catch((err) => {
        console.warn('[AR Lab] 全屏请求失败:', err);
      });
    } else {
      void document.exitFullscreen().then(() => {
        this.isFullscreen = false;
        if ((screen.orientation as unknown as { unlock?: () => void })?.unlock) {
          (screen.orientation as unknown as { unlock: () => void }).unlock();
        }
      });
    }
  }
}
