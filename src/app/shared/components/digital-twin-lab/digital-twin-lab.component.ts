import { CommonModule, DecimalPipe, NgClass } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';

import { ElectronService } from '../../../core/services/electron.service';
import { CircuitShortcutRegistrar } from '../../../core/services/circuit-shortcut-registrar.service';
import { CircuitShortcutHelpDialogComponent } from './circuit-shortcut-help-dialog.component';

interface CircuitElement {
  element_id: string;
  element_type: string;
  voltage: number;
  current: number;
  power: number;
  node1: string;
  node2: string;
  parameter_value: number;
}

interface CircuitState {
  session_id: string;
  elements: CircuitElement[];
  total_power: number;
  total_current: number;
  simulation_time: number;
  timestamp: string;
}

interface DeviceState {
  device_id: string;
  device_type: string;
  voltage: number;
  current: number;
  temperature: number;
  is_connected: boolean;
  custom_properties?: Record<string, unknown>;
  timestamp: string;
}

interface SessionInfo {
  session_id: string;
  host_user_id: number;
  participant_count: number;
  created_at: string;
  is_active: boolean;
}

// Unity WebGL 类型定义
interface UnityInstanceType {
  SendMessage(objectName: string, methodName: string, value?: string): void;
  Quit(): void;
}

interface UnityConfigType {
  dataUrl: string;
  frameworkUrl: string;
  codeUrl: string;
  streamingAssetsUrl: string;
  companyName: string;
  productName: string;
  productVersion: string;
  showBanner: boolean;
}

interface WindowWithUnity extends Window {
  createUnityInstance?: (
    canvas: HTMLCanvasElement,
    config: UnityConfigType,
    onProgress?: (progress: number) => void
  ) => Promise<UnityInstanceType>;
  sendToUnity?: (objectName: string, methodName: string, value: string) => void;
  receiveFromUnity?: (message: string) => void;
}

@Component({
  selector: 'app-digital-twin-lab',
  templateUrl: './digital-twin-lab.component.html',
  styleUrls: ['./digital-twin-lab.component.scss'],
  imports: [
    MatIconModule,
    MatCardModule,
    MatSlideToggleModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    FormsModule,
    CommonModule,
    DecimalPipe,
    NgClass,
    CircuitShortcutHelpDialogComponent,
  ],
})
export class DigitalTwinLabComponent implements OnInit, OnDestroy {
  @ViewChild('unityContainer') unityContainer!: ElementRef;

  sessionId!: string;
  sessionInfo!: SessionInfo;
  isLoading = true;
  errorMessage = '';

  // Unity WebGL 相关
  unityInstance: UnityInstanceType | null = null;
  isUnityLoaded = false;

  // 网络状态
  isConnected = false;
  participantCount = 1;

  // 电路状态
  circuitState: CircuitState | null = null;
  deviceStates: Map<string, DeviceState> = new Map();

  // 控制面板状态
  isSimulationRunning = false;
  isDeviceSyncEnabled = true;
  isFullscreen = false;

  private destroy$ = new Subject<void>();
  private webSocket!: WebSocket;
  private baseUrl = '/api/v1'; // 代理到后端

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private http: HttpClient,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private electronService: ElectronService,
    private shortcutRegistrar: CircuitShortcutRegistrar,
  ) {}

  ngOnInit(): void {
    this.sessionId = this.route.snapshot.paramMap.get('id') ?? '';
    this.loadSession();
    this.initializeWebSocket();
    this.setupKeyboardShortcuts();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.shortcutRegistrar.unregister();
    this.cleanupConnections();
  }

  loadSessionPublic(): void {
    this.loadSession();
  }

  private loadSession(): void {
    this.http
      .get<SessionInfo>(`${this.baseUrl}/digital-twin/sessions/${this.sessionId}`)
      .subscribe({
        next: (session) => {
          this.sessionInfo = session;
          this.isLoading = false;
          this.loadUnityContent();
          this.snackBar.open('数字孪生实验室已加载', '关闭', { duration: 2000 });
        },
        error: (_error) => {
          this.errorMessage = '加载会话失败';
          this.isLoading = false;
          this.snackBar.open('会话加载失败', '关闭', { duration: 3000 });
        },
      });
  }

  private loadUnityContent(): void {
    // 动态加载Unity WebGL构建
    const script = document.createElement('script');
    script.src = `/digital-twin/builds/lab/index.html`;
    script.onload = () => {
      this.initializeUnityPlayer();
    };
    script.onerror = () => {
      this.snackBar.open('Unity内容加载失败', '关闭', { duration: 3000 });
    };
    document.head.appendChild(script);
  }

  private initializeUnityPlayer(): void {
    // Unity WebGL 初始化配置
    const unityConfig: UnityConfigType = {
      dataUrl: '/digital-twin/builds/lab/Build/lab.data',
      frameworkUrl: '/digital-twin/builds/lab/Build/lab.framework.js',
      codeUrl: '/digital-twin/builds/lab/Build/lab.wasm',
      streamingAssetsUrl: 'StreamingAssets',
      companyName: 'iMatu',
      productName: 'Digital Twin Lab',
      productVersion: '1.0',
      showBanner: false,
    };

    // 创建 Unity 实例
    const win = window as WindowWithUnity;
    if (win.createUnityInstance) {
      win
        .createUnityInstance(
          this.unityContainer.nativeElement as HTMLCanvasElement,
          unityConfig,
          (_progress: number) => {
            // 开发环境下记录 Unity 加载进度
            if (typeof ngDevMode === 'undefined' || ngDevMode) {
              // 开发模式日志已禁用
            }
          }
        )
        .then((instance: UnityInstanceType) => {
          this.unityInstance = instance;
          this.isUnityLoaded = true;
          this.setupUnityCommunication();
          this.snackBar.open('Unity 实验室已就绪', '关闭', { duration: 2000 });
        })
        .catch((_error: unknown) => {
          this.snackBar.open('Unity 启动失败', '关闭', { duration: 3000 });
        });
    }
  }

  private setupUnityCommunication(): void {
    // 设置与 Unity 的双向通信
    const win = window as WindowWithUnity;

    win.sendToUnity = (objectName: string, methodName: string, value: string) => {
      this.unityInstance?.SendMessage(objectName, methodName, value);
    };

    // 接收来自 Unity 的消息
    win.receiveFromUnity = (message: string) => {
      this.handleUnityMessage(message);
    };
  }

  private handleUnityMessage(message: string): void {
    try {
      const data = JSON.parse(message) as {
        type: string;
        state?: CircuitState | DeviceState;
        action?: string;
      };

      switch (data.type) {
        case 'circuit_state_update':
          if (data.state) {
            this.sendCircuitStateToBackend(data.state as CircuitState);
          }
          break;

        case 'device_state_update':
          if (data.state) {
            this.sendDeviceStateToBackend(data.state as DeviceState);
          }
          break;

        case 'simulation_control':
          if (data.action) {
            this.handleSimulationControl(data.action);
          }
          break;

        default:
      }
    } catch (_error) {
      // 错误已静默处理
    }
  }

  private handleSimulationControl(action: string): void {
    switch (action) {
      case 'start':
        this.isSimulationRunning = true;
        break;
      case 'stop':
        this.isSimulationRunning = false;
        break;
      case 'reset':
        this.resetCircuit();
        break;
      default:
    }
  }

  private initializeWebSocket(): void {
    const wsUrl = `ws://${window.location.host}/api/v1/digital-twin/ws/session/${this.sessionId}?user_id=user_${Math.random()}`;

    try {
      this.webSocket = new WebSocket(wsUrl);

      this.webSocket.onopen = () => {
        this.isConnected = true;

        this.snackBar.open('实时连接已建立', '关闭', { duration: 2000 });
      };

      this.webSocket.onmessage = (event: MessageEvent<string>) => {
        this.handleWebSocketMessage(event.data);
      };

      this.webSocket.onclose = () => {
        this.isConnected = false;

        // 尝试重连
        setTimeout(() => this.initializeWebSocket(), 5000);
      };

      this.webSocket.onerror = (_error) => {
        this.snackBar.open('连接出现错误', '关闭', { duration: 3000 });
      };
    } catch (_error) {
      this.snackBar.open('无法建立实时连接', '关闭', { duration: 3000 });
    }
  }

  private handleWebSocketMessage(data: string): void {
    try {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const message = JSON.parse(data) as {
        type: string;
        state?: CircuitState | DeviceState;
        device_id?: string;
        message?: string;
      };

      switch (message.type) {
        case 'circuit_state_broadcast':
          if (message.state) {
            this.updateCircuitState(message.state as CircuitState);
          }
          break;

        case 'device_state_broadcast':
          if (message.device_id && message.state) {
            this.updateDeviceState(message.device_id, message.state as DeviceState);
          }
          break;

        case 'sync_response':
          this.handleSyncResponse(message);
          break;

        case 'error':
          if (message.message) {
            this.snackBar.open(`错误：${message.message}`, '关闭', { duration: 3000 });
          }
          break;

        default:
      }
    } catch (_error) {
      // 错误已静默处理
    }
  }

  private updateCircuitState(state: CircuitState): void {
    this.circuitState = state;

    // 同步到 Unity
    if (this.isUnityLoaded) {
      const win = window as WindowWithUnity;
      win.sendToUnity?.('CircuitManager', 'UpdateCircuitState', JSON.stringify(state));
    }

    // 更新UI显示
    this.participantCount = state.elements?.length || 0;
  }

  private updateDeviceState(deviceId: string, state: DeviceState): void {
    this.deviceStates.set(deviceId, state);

    // 同步到 Unity
    if (this.isUnityLoaded) {
      const message = { deviceId, state };
      const win = window as WindowWithUnity;
      win.sendToUnity?.('DeviceManager', 'UpdateDeviceState', JSON.stringify(message));
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private handleSyncResponse(message: any): void {
    const typedMessage = message as { circuit_state?: CircuitState; device_states?: DeviceState[] };

    if (typedMessage.circuit_state) {
      this.updateCircuitState(typedMessage.circuit_state);
    }

    if (typedMessage.device_states) {
      typedMessage.device_states.forEach((deviceState: DeviceState) => {
        this.deviceStates.set(deviceState.device_id, deviceState);
      });
    }

    this.snackBar.open('状态同步完成', '关闭', { duration: 2000 });
  }

  // 发送电路状态到后端
  private sendCircuitStateToBackend(state: CircuitState): void {
    if (!this.isConnected) return;

    const message = {
      type: 'circuit_state_update',
      session_id: this.sessionId,
      state,
      sender: 'frontend',
    };

    this.webSocket.send(JSON.stringify(message));
  }

  // 发送设备状态到后端
  private sendDeviceStateToBackend(state: DeviceState): void {
    if (!this.isConnected) return;

    const message = {
      type: 'device_state_update',
      session_id: this.sessionId,
      state,
    };

    this.webSocket.send(JSON.stringify(message));
  }

  // 仿真控制
  toggleSimulation(): void {
    this.isSimulationRunning = !this.isSimulationRunning;

    if (this.isUnityLoaded) {
      const win = window as WindowWithUnity;
      win.sendToUnity?.(
        'SimulationController',
        'ToggleSimulation',
        this.isSimulationRunning.toString()
      );
    }

    const action = this.isSimulationRunning ? '开始' : '停止';
    this.snackBar.open(`仿真已${action}`, '关闭', { duration: 2000 });
  }

  // 设备同步控制
  toggleDeviceSync(): void {
    this.isDeviceSyncEnabled = !this.isDeviceSyncEnabled;

    if (this.isUnityLoaded) {
      const win = window as WindowWithUnity;
      win.sendToUnity?.('IoTManager', 'ToggleDeviceSync', this.isDeviceSyncEnabled.toString());
    }

    const status = this.isDeviceSyncEnabled ? '启用' : '禁用';
    this.snackBar.open(`设备同步已${status}`, '关闭', { duration: 2000 });
  }

  // 重置电路
  resetCircuit(): void {
    if (this.isUnityLoaded) {
      const win = window as WindowWithUnity;
      win.sendToUnity?.('CircuitManager', 'ResetCircuit', '');
      this.snackBar.open('电路已重置', '关闭', { duration: 2000 });
    }
  }

  // 添加元件
  addElement(elementType: string): void {
    if (this.isUnityLoaded) {
      const win = window as WindowWithUnity;
      win.sendToUnity?.('CircuitManager', 'AddElement', elementType);
      this.snackBar.open(`已添加${elementType}元件`, '关闭', { duration: 2000 });
    }
  }

  // 获取会话信息
  getSessionDetails(): void {
    this.http
      .get<{
        participant_count: number;
      }>(`${this.baseUrl}/digital-twin/sessions/${this.sessionId}/participants`)
      .subscribe({
        next: (data) => {
          this.participantCount = data.participant_count;
          // 显示详细信息对话框
          this.showSessionDialog(data);
        },
        error: (_error) => {
          // 静默处理错误
        },
      });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private showSessionDialog(_data: any): void {
    // 这里可以创建一个 Material Dialog 组件显示会话详情
  }

  // 返回主页
  goBack(): void {
    void this.router.navigate(['/dashboard']);
  }

  // 全屏切换
  toggleFullscreen(): void {
    if (!document.fullscreenElement) {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
      this.unityContainer.nativeElement.requestFullscreen();
    } else {
      void document.exitFullscreen();
    }
  }

  // 弹出独立实验窗口（PRD F-09 桌面端适配：多窗口模式）
  openInNewWindow(): void {
    if (!this.electronService.isElectron) {
      // 浏览器端降级：新标签页打开
      window.open(`/digital-twin-lab/${this.sessionId}`, '_blank');
      return;
    }

    // Electron 端：通过 IPC 请求主进程创建新窗口
    this.electronService.sendAppEvent({
      type: 'open-new-window' as never,
      url: `/digital-twin-lab/${this.sessionId}`,
      title: `数字孪生实验 - ${this.sessionId}`,
      width: 1280,
      height: 800,
    } as never);

    this.snackBar.open('实验窗口已弹出', '关闭', { duration: 2000 });
  }

  // 获取平均电压
  getAverageVoltage(): number {
    if (this.deviceStates.size === 0) return 0;

    let sum = 0;
    let count = 0;
    this.deviceStates.forEach((state) => {
      if (state.is_connected) {
        sum += state.voltage;
        count++;
      }
    });

    return count > 0 ? sum / count : 0;
  }

  // 获取前N个元件
  getTopElements(count: number): CircuitElement[] {
    if (!this.circuitState?.elements) return [];

    // 按功率排序，返回前count个
    return [...this.circuitState.elements]
      .sort((a, b) => Math.abs(b.power) - Math.abs(a.power))
      .slice(0, count);
  }

  /** 设置键盘快捷键 */
  private setupKeyboardShortcuts(): void {
    // 延时注册，确保 DOM 渲染完成
    setTimeout(() => {
      const element = document.querySelector('.digital-twin-lab') as HTMLElement;
      if (!element) return;

      // 设置 tabindex 以接收键盘事件
      element.tabIndex = -1;
      element.focus();

      this.shortcutRegistrar.register(element, (action) => {
        this.handleShortcutAction(action);
      });
    }, 500);
  }

  /** 处理快捷键动作 */
  private handleShortcutAction(action: string): void {
    switch (action) {
      case 'rotate':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'RotateSelected', '');
          this.snackBar.open('旋转选中元件', '关闭', { duration: 1000 });
        }
        break;

      case 'delete':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'DeleteSelected', '');
          this.snackBar.open('删除选中元件', '关闭', { duration: 1000 });
        }
        break;

      case 'undo':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'Undo', '');
          this.snackBar.open('撤销', '关闭', { duration: 1000 });
        }
        break;

      case 'redo':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'Redo', '');
          this.snackBar.open('重做', '关闭', { duration: 1000 });
        }
        break;

      case 'cancel':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'CancelSelection', '');
        }
        break;

      case 'selectAll':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'SelectAll', '');
          this.snackBar.open('已全选', '关闭', { duration: 1000 });
        }
        break;

      case 'copy':
      case 'paste':
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('ClipboardManager', action === 'copy' ? 'Copy' : 'Paste', '');
        }
        break;

      case 'save':
        this.snackBar.open('电路已保存', '关闭', { duration: 2000 });
        if (this.isUnityLoaded) {
          const win = window as WindowWithUnity;
          win.sendToUnity?.('CircuitManager', 'SaveCircuit', '');
        }
        break;

      case 'new':
        this.resetCircuit();
        this.snackBar.open('已新建电路', '关闭', { duration: 2000 });
        break;

      case 'zoomIn':
        this.adjustZoom(1.2);
        break;

      case 'zoomOut':
        this.adjustZoom(0.8);
        break;

      case 'resetZoom':
        this.adjustZoom(1);
        break;

      case 'help':
        this.showShortcutHelp();
        break;
    }
  }

  /** 调整 Unity 视图缩放 */
  private adjustZoom(factor: number): void {
    if (this.isUnityLoaded) {
      const win = window as WindowWithUnity;
      win.sendToUnity?.('CameraController', 'AdjustZoom', factor.toString());
    }
  }

  /** 显示快捷键帮助面板 */
  private showShortcutHelp(): void {
    const groups = this.shortcutRegistrar.getGroupedShortcuts();
    this.dialog.open(CircuitShortcutHelpDialogComponent, {
      data: groups,
      width: '480px',
      autoFocus: false,
    });
  }

  private cleanupConnections(): void {
    if (this.webSocket) {
      this.webSocket.close();
    }

    if (this.unityInstance) {
      this.unityInstance.Quit();
    }
  }
}
