/**
 * Vircadia 场景查看器组件
 *
 * 用于在 Angular 应用中显示和交互 Vircadia 3D 场景
 * 支持场景加载、对象交互、用户控制等功能
 */

import { CommonModule } from '@angular/common';
import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { Subject } from 'rxjs';

import { createVircadiaSdk, VircadiaSdkService } from '../../core/services/vircadia-sdk.service';
import {
  GameObject,
  NetworkStats,
  PerformanceStats,
  Quaternion,
  SceneInfo,
  UserInfo,
  Vector3,
  VircadiaSDKConfig,
} from '../../models/vircadia.models';

@Component({
  selector: 'app-vircadia-scene-viewer',
  templateUrl: './vircadia-scene-viewer.component.html',
  styleUrls: ['./vircadia-scene-viewer.component.scss'],
  imports: [CommonModule],
})
export class VircadiaSceneViewerComponent implements OnInit, OnDestroy {
  @Input() serverUrl: string = 'http://localhost:9000';
  @Input() accessToken?: string;
  @Input() debugMode: boolean = false;
  @Input() autoConnect: boolean = true;

  @Output() connected = new EventEmitter<UserInfo>();
  @Output() disconnected = new EventEmitter<void>();
  @Output() sceneLoaded = new EventEmitter<SceneInfo>();
  @Output() error = new EventEmitter<Error | string>();
  @Output() performanceUpdate = new EventEmitter<PerformanceStats>();

  @ViewChild('sceneContainer') sceneContainer!: ElementRef;

  private sdk: VircadiaSdkService | null = null;
  private destroy$ = new Subject<void>();
  public currentScene: SceneInfo | null = null;
  public selectedObject: GameObject | null = null;
  private isInitialized = false;
  private renderLoopId: number | null = null;

  // UI 状态
  isLoading = false;
  isConnected = false;
  connectionProgress = 0;
  connectionStatusText = '';
  showDebugPanel = false;
  performanceStats: PerformanceStats | null = null;
  networkStats: NetworkStats | null = null;

  // 场景中的对象
  sceneObjects: GameObject[] = [];

  constructor() {}

  ngOnInit(): void {
    this.initializeSdk();

    if (this.autoConnect && this.accessToken) {
      void this.connect();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();

    if (this.renderLoopId) {
      cancelAnimationFrame(this.renderLoopId);
    }

    if (this.sdk) {
      void this.sdk.logout();
    }
  }

  /**
   * 初始化 SDK
   */
  private initializeSdk(): void {
    const config: VircadiaSDKConfig = {
      serverUrl: this.serverUrl,
      accessToken: this.accessToken,
      timeout: 30000,
      debug: this.debugMode,
      websocket: {
        autoReconnect: true,
        reconnectInterval: 5000,
        maxReconnectAttempts: 3,
      },
    };

    this.sdk = createVircadiaSdk(config);
    this.isInitialized = true;
  }

  /**
   * 连接到 Vircadia 服务器
   */
  async connect(): Promise<void> {
    if (!this.sdk || !this.accessToken) {
      this.error.emit('未配置访问令牌');
      return;
    }

    try {
      this.isLoading = true;
      this.connectionProgress = 10;
      this.connectionStatusText = '正在连接服务器...';

      // 登录
      await this.sdk.login({
        username: 'user', // TODO: 从 token 中提取
        password: '', // TODO: 使用 OAuth2 或其他方式
      });

      this.connectionProgress = 50;
      this.connectionStatusText = '认证成功，建立 WebSocket 连接...';

      // 监听连接状态变化
      this.sdk.onConnectionStatusChange((status) => {
        this.isConnected = status === 'connected';

        if (status === 'connected') {
          this.connectionProgress = 100;
          this.connectionStatusText = '已连接';

          if (this.sdk) {
            const user = this.sdk.getCurrentUser();
            if (user) {
              this.connected.emit(user);
            }
          }
        } else if (status === 'disconnected') {
          this.disconnected.emit();
        }
      });

      // 监听事件
      this.setupEventListeners();

      // 加载默认场景
      await this.loadDefaultScene();

      // 启动渲染循环
      this.startRenderLoop();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      this.connectionStatusText = `连接失败：${errorMessage}`;
      this.error.emit(err instanceof Error ? err : new Error(String(err)));
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 断开连接
   */
  async disconnect(): Promise<void> {
    if (!this.sdk) return;

    try {
      await this.sdk.logout();
      this.isConnected = false;
      this.sceneObjects = [];
      this.currentScene = null;
      this.selectedObject = null;

      if (this.renderLoopId) {
        cancelAnimationFrame(this.renderLoopId);
        this.renderLoopId = null;
      }

      this.disconnected.emit();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err : new Error(String(err));
      this.error.emit(errorMessage);
    }
  }

  /**
   * 加载场景
   */
  async loadScene(sceneId: string): Promise<void> {
    if (!this.sdk || !this.isConnected) {
      this.error.emit('未连接到服务器');
      return;
    }

    try {
      this.isLoading = true;
      this.connectionStatusText = '正在加载场景...';

      const scene = await this.sdk.loadScene({ sceneId }, (progress, status) => {
        this.connectionProgress = progress;
        this.connectionStatusText = status;
      });

      this.currentScene = scene;
      this.sceneLoaded.emit(scene);

      // 加载场景中的对象
      await this.loadSceneObjects();

      this.connectionStatusText = '场景加载完成';
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      this.connectionStatusText = `场景加载失败：${errorMessage}`;
      this.error.emit(err instanceof Error ? err : new Error(String(err)));
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * 切换场景
   */
  async switchScene(sceneId: string): Promise<void> {
    await this.loadScene(sceneId);
  }

  /**
   * 与对象交互
   */
  async interactWithObject(
    objectId: string,
    interactionType: 'click' | 'hover' | 'grab' | 'use'
  ): Promise<void> {
    if (!this.sdk) return;

    try {
      const response = await this.sdk.interact({
        objectId,
        interactionType,
        data: { timestamp: Date.now() },
      });

      if (!response.success) {
        // 交互失败，静默处理
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err : new Error(String(err));
      this.error.emit(errorMessage);
    }
  }

  /**
   * 选择对象
   */
  selectObject(object: GameObject): void {
    this.selectedObject = object;
  }

  /**
   * 设置相机位置
   */
  setCameraPosition(position: Vector3, rotation?: Quaternion): void {
    if (!this.sdk) return;

    try {
      this.sdk.setCameraPosition(position, rotation);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err : new Error(String(err));
      this.error.emit(errorMessage);
    }
  }

  /**
   * 获取性能统计
   */
  updatePerformanceStats(): void {
    if (!this.sdk) return;

    try {
      this.performanceStats = this.sdk.getPerformanceStats();
      this.networkStats = this.sdk.getNetworkStats();
      this.performanceUpdate.emit(this.performanceStats);
    } catch (err: unknown) {
      // 获取性能统计失败，静默处理
      const _errorMessage = err instanceof Error ? err.message : String(err);
    }
  }

  /**
   * 切换调试面板
   */
  toggleDebugPanel(): void {
    this.showDebugPanel = !this.showDebugPanel;
    if (this.showDebugPanel) {
      void this.updatePerformanceStats();
    }
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    if (!this.sdk) return;

    // 监听用户加入事件
    this.sdk.on('user.joined', (_event) => {
      // TODO: 实现用户加入逻辑
    });

    // 监听用户离开事件
    this.sdk.on('user.left', (_event) => {
      // TODO: 实现用户离开逻辑
    });

    // 监听对象状态变更事件
    this.sdk.on('object.stateChanged', (_event) => {
      // 更新本地对象列表
      this.refreshSceneObjects().catch((_err) => {
        // 刷新失败，静默处理
      });
    });

    // 监听聊天消息事件
    this.sdk.on('chat.message', (_event) => {
      // TODO: 实现聊天消息处理
    });
  }

  /**
   * 加载默认场景
   */
  private async loadDefaultScene(): Promise<void> {
    // TODO: 从配置中读取默认场景 ID
    const defaultSceneId = 'default-classroom';
    await this.loadScene(defaultSceneId);
  }

  /**
   * 加载场景对象
   */
  private async loadSceneObjects(): Promise<void> {
    if (!this.sdk) return;

    try {
      this.sceneObjects = await this.sdk.getObjects();
    } catch (err: unknown) {
      // 加载场景对象失败，静默处理
      const _errorMessage = err instanceof Error ? err.message : String(err);
    }
  }

  /**
   * 刷新场景对象
   */
  private async refreshSceneObjects(): Promise<void> {
    await this.loadSceneObjects();
  }

  /**
   * 启动渲染循环
   */
  private startRenderLoop(): void {
    const render = (): void => {
      // TODO: 实现 3D 渲染逻辑
      // 这里应该使用 Three.js 或其他 3D 引擎进行渲染

      // 定期更新性能统计（不阻塞渲染）
      if (this.showDebugPanel) {
        void this.updatePerformanceStats();
      }

      this.renderLoopId = requestAnimationFrame(render);
    };

    render();
  }

  /**
   * 处理画布点击事件
   */
  onCanvasClick(_event: MouseEvent): void {
    // TODO: 实现射线检测，选择点击的 3D 对象
  }

  /**
   * 处理鼠标移动事件
   */
  onMouseMove(_event: MouseEvent): void {
    // TODO: 实现相机控制和对象悬停检测
  }

  /**
   * 处理鼠标滚轮事件
   */
  onMouseWheel(_event: WheelEvent): void {
    // TODO: 实现缩放功能
  }
}
