import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  ChangeDetectorRef,
  Component,
  ElementRef,
  HostListener,
  NgZone,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';
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
  simulated?: boolean;
  startTime?: number;
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

  // 【P4-C】Unity WebGL 构建状态检测。CLI 环境下无法直接跑 Unity Editor，
  //   在缺失构建时给出明确提示 + 构建命令文档 + CSS 3D 占位动画。
  //   angular.json 把 src/assets 映射到 /assets/，所以前端路径是 /assets/ar-lab/build/...
  unityBuildAvailable: boolean | null = null; // null=检测中, true=有构建, false=缺失
  readonly unityBuildPath = '/assets/ar-lab/build/ARLabMain.json';

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
    private snackBar: MatSnackBar,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.checkARSupport();
    this.detectUnityBuild();
    this.startSensorDataPolling();
    this.setupFullscreenListener();
  }

  /**
   * 【P4-C】检测 Unity WebGL 构建是否已部署到 /ar-lab/build/。
   *   不能靠加载 UnityLoader 后报错才知道——以体验不佳。
   *   提前 HEAD 探深如果缺失则进入占位模式，让用户看到明确提示。
   *   公开以供“重新检测”按钮调用。
   *
   *   为何不用 Angular HttpClient.head()：Angular 的 XHR backend 对 HEAD 返回的
   *   无 body 响应会记为 ERR_FAILED，即使服务器正确返回 404。所以这里用原生 fetch，
   *   仅检查 status 码。fetch() 同样支持 CORS，默认不发 preflight。
   *
   *   另外：原生 fetch 在 NgZone 外解决，变更后须 cdr.markForCheck() 触发 CD。
   */
  detectUnityBuild(): void {
    this.unityBuildAvailable = null;
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();
    // 加超时，30s 还没返回则视为缺失
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 30_000);
    // 在 zone 外 fetch — Promise 完成后须走 zone.run 触发 Angular CD
    this.zone.runOutsideAngular(() => {
      fetch(this.unityBuildPath, { method: 'HEAD', mode: 'cors', signal: controller.signal })
        .then((r) => {
          window.clearTimeout(timeoutId);
          this.zone.run(() => {
            if (r.ok) {
              this.unityBuildAvailable = true;
              this.isLoading = true;
              this.loadUnityApplication();
            } else {
              this.unityBuildAvailable = false;
              this.isLoading = false;
              this.errorMessage = `未检测到 Unity WebGL 构建 (${this.unityBuildPath})。HTTP ${r.status}。请在 Unity Editor 中 Build 后把产物拷贝到 src/assets/ar-lab/build/ 并重新 ng build。`;
            }
            this.cdr.markForCheck();
          });
        })
        .catch((err) => {
          window.clearTimeout(timeoutId);
          this.zone.run(() => {
            this.unityBuildAvailable = false;
            this.isLoading = false;
            const aborted = err?.name === 'AbortError';
            this.errorMessage = `检测 Unity WebGL 构建失败 (${this.unityBuildPath})。${aborted ? '请求超时' : (err?.message ?? err)}。请确认后端 / SPA 服务器可达。`;
            this.cdr.markForCheck();
          });
        });
    });
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
      gl =
        canvas.getContext('webgl') ??
        (canvas.getContext('experimental-webgl') as WebGLRenderingContext | null);
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
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) as string;
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
        this.errorMessage =
          'Unity WebGL 运行时未加载。请确认 Unity 构建已部署到 /ar-lab/build/ 目录。';
        this.isLoading = false;
        this.snackBar.open(this.errorMessage, '关闭', { duration: 5000 });
        return;
      }

      // 创建Unity实例
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
      this.unityInstance = UnityLoader.instantiate(
        this.unityContainer.nativeElement as HTMLElement,
        this.unityBuildPath,
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
   * 【P2 修复】无硬件时进入"模拟实验"模式,使用预置数据
   */
  startExperiment(): void {
    if (!this.hardwareConnected) {
      // 进入模拟实验模式,避免用户被"必须连接硬件"卡住
      const useSimulation = confirm(
        '未连接硬件设备。\n\n' +
          '点击"确定"进入模拟实验模式(使用预置数据体验完整流程)\n' +
          '点击"取消"返回并继续等待硬件'
      );

      if (!useSimulation) {
        return;
      }

      // 模拟实验模式: 不调真实 API,直接构造实验对象
      this.currentExperiment = {
        id: 'sim-' + Date.now(),
        name: '模拟实验 - LED 闪烁控制',
        status: 'running',
        startTime: Date.now(),
        simulated: true,
      };
      this.isExperimentRunning = true;
      this.hardwareConnected = true; // 模拟模式下视为已连接,解锁 UI
      this.connectionStatus = '模拟模式';
      this.snackBar.open('已进入模拟实验模式(无硬件)', '关闭', { duration: 3000 });
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
        this.snackBar.open('实验启动失败，请重试', '关闭', { duration: 3000 });
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
  // eslint-disable-next-line complexity
  handleKeyboardShortcut(event: KeyboardEvent): void {
    // F11 → 切换全屏
    if (event.key === 'F11') {
      event.preventDefault();
      this.toggleFullscreen();
      return;
    }

    // F 键（非输入框中）→ 切换全屏
    if (
      (event.key === 'f' || event.key === 'F') &&
      !(event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement)
    ) {
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
      void container
        .requestFullscreen()
        .then(() => {
          this.isFullscreen = true;
          // AR体验锁定横屏
          if ((screen.orientation as unknown as { lock?: (o: string) => Promise<void> })?.lock) {
            void (screen.orientation as unknown as { lock: (o: string) => Promise<void> })
              .lock('landscape')
              .catch(() => {});
          }
          this.snackBar.open('全屏模式已启用 (Esc 退出)', '关闭', { duration: 2000 });
        })
        .catch((err) => {
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
