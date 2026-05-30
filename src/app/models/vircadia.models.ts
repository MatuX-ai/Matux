/**
 * Vircadia Web SDK 类型定义文件
 *
 * 定义了与 Vircadia 元宇宙平台交互所需的所有 TypeScript 接口和类型
 *
 * @packageDocumentation
 */

// ==================== 基础配置类型 ====================

/**
 * Vircadia SDK配置选项
 */
export interface VircadiaSDKConfig {
  /** Vircadia 服务器 URL */
  serverUrl: string;
  /** API 密钥 (可选) */
  apiKey?: string;
  /** 访问令牌 (用于认证) */
  accessToken?: string;
  /** 请求超时时间 (毫秒) */
  timeout?: number;
  /** 是否启用调试模式 */
  debug?: boolean;
  /** WebSocket 配置 */
  websocket?: WebSocketConfig;
}

/**
 * WebSocket 配置
 */
export interface WebSocketConfig {
  /** WebSocket 服务器 URL */
  url?: string;
  /** 自动重连 */
  autoReconnect?: boolean;
  /** 重连间隔 (毫秒) */
  reconnectInterval?: number;
  /** 最大重连次数 */
  maxReconnectAttempts?: number;
}

// ==================== 用户认证类型 ====================

/**
 * 用户登录请求
 */
export interface LoginRequest {
  /** 用户名或邮箱 */
  username: string;
  /** 密码 */
  password: string;
  /** 是否记住登录状态 */
  rememberMe?: boolean;
}

/**
 * 用户登录响应
 */
export interface LoginResponse {
  /** 访问令牌 */
  access_token: string;
  /** 刷新令牌 */
  refresh_token?: string;
  /** 令牌类型 */
  token_type: string;
  /** 过期时间 (秒) */
  expires_in: number;
  /** 用户信息 */
  user: UserInfo;
}

/**
 * 用户信息
 */
export interface UserInfo {
  /** 用户 ID */
  id: string;
  /** 用户名 */
  username: string;
  /** 显示名称 */
  displayName?: string;
  /** 邮箱 */
  email?: string;
  /** 头像 URL */
  avatarUrl?: string;
  /** 账号创建时间 */
  createdAt?: string;
  /** 最后登录时间 */
  lastLoginAt?: string;
  /** 用户角色 */
  roles?: string[];
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * Token 刷新响应
 */
export interface RefreshTokenResponse {
  /** 新的访问令牌 */
  access_token: string;
  /** 新的刷新令牌 */
  refresh_token?: string;
  /** 令牌类型 */
  token_type: string;
  /** 过期时间 (秒) */
  expires_in: number;
}

// ==================== 场景管理类型 ====================

/**
 * 场景信息
 */
export interface SceneInfo {
  /** 场景 ID */
  id: string;
  /** 场景名称 */
  name: string;
  /** 场景描述 */
  description?: string;
  /** 场景缩略图 URL */
  thumbnailUrl?: string;
  /** 场景文件 URL */
  sceneUrl: string;
  /** 创建者 ID */
  creatorId?: string;
  /** 创建时间 */
  createdAt?: string;
  /** 更新时间 */
  updatedAt?: string;
  /** 是否公开 */
  isPublic?: boolean;
  /** 最大并发用户数 */
  maxUsers?: number;
  /** 当前用户数 */
  currentUserCount?: number;
  /** 场景标签 */
  tags?: string[];
  /** 场景元数据 */
  metadata?: Record<string, any>;
}

/**
 * 加载场景请求
 */
export interface LoadSceneRequest {
  /** 场景 ID */
  sceneId: string;
  /** 起始位置 (可选) */
  startPosition?: Vector3;
  /** 起始朝向 (可选) */
  startRotation?: Quaternion;
}

/**
 * 场景列表查询参数
 */
export interface SceneQueryParams {
  /** 搜索关键词 */
  search?: string;
  /** 标签过滤 */
  tags?: string[];
  /** 是否只显示公开场景 */
  publicOnly?: boolean;
  /** 分页 - 页码 */
  page?: number;
  /** 分页 - 每页数量 */
  limit?: number;
  /** 排序字段 */
  sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'userCount';
  /** 排序方向 */
  sortOrder?: 'asc' | 'desc';
}

/**
 * 场景列表响应
 */
export interface SceneListResponse {
  /** 场景列表 */
  data: SceneInfo[];
  /** 总数 */
  total: number;
  /** 当前页码 */
  page: number;
  /** 每页数量 */
  limit: number;
  /** 总页数 */
  totalPages: number;
}

// ==================== 3D 对象类型 ====================

/**
 * 3D 向量
 */
export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

/**
 * 四元数
 */
export interface Quaternion {
  x: number;
  y: number;
  z: number;
  w: number;
}

/**
 * 3D 对象信息
 */
export interface GameObject {
  /** 对象 ID */
  id: string;
  /** 对象名称 */
  name: string;
  /** 对象类型 */
  type: 'mesh' | 'light' | 'camera' | 'empty' | 'ui' | 'audio';
  /** 位置 */
  position: Vector3;
  /** 旋转 */
  rotation: Quaternion;
  /** 缩放 */
  scale: Vector3;
  /** 父对象 ID */
  parentId?: string;
  /** 子对象 ID 列表 */
  childrenIds?: string[];
  /** 是否可见 */
  visible?: boolean;
  /** 是否可交互 */
  interactable?: boolean;
  /** 碰撞体信息 */
  collider?: ColliderInfo;
  /** 渲染组件信息 */
  renderer?: RendererInfo;
  /** 脚本组件 */
  scripts?: ScriptComponent[];
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * 碰撞体信息
 */
export interface ColliderInfo {
  /** 碰撞体类型 */
  type: 'box' | 'sphere' | 'capsule' | 'mesh' | 'plane';
  /** 尺寸 */
  size?: Vector3;
  /** 半径 */
  radius?: number;
  /** 高度 */
  height?: number;
  /** 是否触发器 */
  isTrigger?: boolean;
}

/**
 * 渲染组件信息
 */
export interface RendererInfo {
  /** 渲染类型 */
  type: 'mesh' | 'skinned_mesh' | 'particle' | 'trail';
  /** 材质 URL */
  materialUrl?: string;
  /** 几何体 URL */
  geometryUrl?: string;
  /** 是否接收阴影 */
  receiveShadow?: boolean;
  /** 是否投射阴影 */
  castShadow?: boolean;
}

/**
 * 脚本组件
 */
export interface ScriptComponent {
  /** 脚本名称 */
  name: string;
  /** 脚本类型 */
  type: string;
  /** 脚本参数 */
  parameters?: Record<string, any>;
}

/**
 * 对象交互请求
 */
export interface InteractRequest {
  /** 对象 ID */
  objectId: string;
  /** 交互类型 */
  interactionType: 'click' | 'hover' | 'grab' | 'release' | 'use' | 'activate';
  /** 交互数据 */
  data?: Record<string, any>;
}

/**
 * 对象交互响应
 */
export interface InteractResponse {
  /** 是否成功 */
  success: boolean;
  /** 响应消息 */
  message?: string;
  /** 响应数据 */
  data?: Record<string, any>;
}

// ==================== Avatar 类型 ====================

/**
 * Avatar 信息
 */
export interface AvatarInfo {
  /** Avatar ID */
  id: string;
  /** Avatar 名称 */
  name: string;
  /** Avatar 描述 */
  description?: string;
  /** Avatar 模型 URL */
  modelUrl: string;
  /** 缩略图 URL */
  thumbnailUrl?: string;
  /** 创建者 ID */
  creatorId?: string;
  /** 是否公开 */
  isPublic?: boolean;
  /** 标签 */
  tags?: string[];
  /** 元数据 */
  metadata?: Record<string, any>;
}

/**
 * Avatar 动画状态
 */
export interface AvatarAnimationState {
  /** 当前动画名称 */
  currentAnimation?: string;
  /** 是否正在播放 */
  isPlaying: boolean;
  /** 播放进度 (0-1) */
  progress?: number;
  /** 可用动画列表 */
  availableAnimations?: string[];
}

/**
 * 设置 Avatar 请求
 */
export interface SetAvatarRequest {
  /** Avatar ID */
  avatarId: string;
  /** 自定义颜色 (可选) */
  customColors?: Record<string, string>;
  /** 自定义配饰 (可选) */
  accessories?: string[];
}

// ==================== 事件类型 ====================

/**
 * 虚拟世界事件基类
 */
export interface VirtualWorldEvent {
  /** 事件 ID */
  eventId: string;
  /** 事件类型 */
  type: string;
  /** 事件发生时间 */
  timestamp: string;
  /** 发起者用户 ID */
  userId?: string;
  /** 事件数据 */
  data?: Record<string, unknown>;
}

/**
 * 用户加入事件
 */
export interface UserJoinedEvent extends VirtualWorldEvent {
  type: 'user.joined';
  data: {
    userInfo: UserInfo;
    joinTime: string;
  };
}

/**
 * 用户离开事件
 */
export interface UserLeftEvent extends VirtualWorldEvent {
  type: 'user.left';
  data: {
    userId: string;
    leaveTime: string;
    reason?: string;
  };
}

/**
 * 对象状态变更事件
 */
export interface ObjectStateChangedEvent extends VirtualWorldEvent {
  type: 'object.stateChanged';
  data: {
    objectId: string;
    previousState: Record<string, any>;
    newState: Record<string, any>;
  };
}

/**
 * 聊天消息事件
 */
export interface ChatMessageEvent extends VirtualWorldEvent {
  type: 'chat.message';
  data: {
    messageId: string;
    senderId: string;
    content: string;
    messageType: 'text' | 'voice' | 'emoji';
  };
}

// ==================== 错误类型 ====================

/**
 * SDK 错误类型
 */
export type VircadiaErrorType =
  | 'AUTHENTICATION_ERROR'
  | 'NETWORK_ERROR'
  | 'TIMEOUT_ERROR'
  | 'SCENE_NOT_FOUND'
  | 'OBJECT_NOT_FOUND'
  | 'PERMISSION_DENIED'
  | 'INVALID_PARAMETER'
  | 'SERVER_ERROR'
  | 'UNKNOWN_ERROR';

/**
 * SDK 错误对象
 */
export interface VircadiaError {
  /** 错误类型 */
  type: VircadiaErrorType;
  /** 错误消息 */
  message: string;
  /** HTTP 状态码 (如果有) */
  statusCode?: number;
  /** 原始错误 (如果有) */
  originalError?: any;
  /** 错误发生的时间 */
  timestamp: string;
  /** 错误堆栈 (调试模式) */
  stack?: string;
}

// ==================== 回调函数类型 ====================

/**
 * 事件监听器回调
 */
export type EventListenerCallback = (event: VirtualWorldEvent) => void;

/**
 * 连接状态变化回调
 */
export type ConnectionStatusCallback = (
  status: 'connected' | 'disconnected' | 'connecting' | 'error'
) => void;

/**
 * 场景加载进度回调
 */
export type SceneLoadProgressCallback = (progress: number, status: string) => void;

// ==================== 性能统计类型 ====================

/**
 * 性能统计数据
 */
export interface PerformanceStats {
  /** 帧率 (FPS) */
  fps: number;
  /** 平均帧率 */
  averageFps: number;
  /** 最低帧率 */
  minFps: number;
  /** 最高帧率 */
  maxFps: number;
  /** 渲染耗时 (毫秒) */
  renderTime: number;
  /** 网络延迟 (毫秒) */
  networkLatency: number;
  /** 内存使用 (MB) */
  memoryUsage: number;
  /** 绘制调用次数 */
  drawCalls: number;
  /** 三角形数量 */
  triangleCount: number;
  /** 顶点数量 */
  vertexCount: number;
}

/**
 * 网络统计信息
 */
export interface NetworkStats {
  /** 下载速度 (KB/s) */
  downloadSpeed: number;
  /** 上传速度 (KB/s) */
  uploadSpeed: number;
  /** 总下载量 (KB) */
  totalDownloaded: number;
  /** 总上传量 (KB) */
  totalUploaded: number;
  /** 丢包率 (%) */
  packetLoss: number;
  /** 抖动 (毫秒) */
  jitter: number;
}

// ==================== 物理引擎类型 ====================

/**
 * 物理属性配置
 */
export interface PhysicsProperties {
  /** 质量 (千克) */
  mass: number;
  /** 碰撞体类型 */
  colliderType: 'box' | 'sphere' | 'capsule' | 'cylinder' | 'mesh';
  /** 碰撞体尺寸 */
  colliderSize?: Vector3;
  /** 半径 (用于球体/圆柱体) */
  radius?: number;
  /** 高度 (用于圆柱体/胶囊体) */
  height?: number;
  /** 摩擦系数 */
  friction: number;
  /** 弹性系数 */
  bounciness: number;
  /** 是否为触发器 */
  isTrigger: boolean;
  /** 是否受重力影响 */
  affectedByGravity: boolean;
}

/**
 * 刚体约束配置
 */
export interface RigidBodyConstraints {
  /** 冻结旋转 */
  freezeRotation?: boolean;
  /** 冻结位置 */
  freezePosition?: boolean;
  /** 轴向锁定 */
  axisLock?: 'x' | 'y' | 'z' | 'xy' | 'xz' | 'yz';
}

/**
 * 刚体配置
 */
export interface RigidBodyConfig {
  /** 刚体类型 */
  type: 'static' | 'dynamic' | 'kinematic';
  /** 物理属性 */
  properties: PhysicsProperties;
  /** 约束配置 */
  constraints?: RigidBodyConstraints;
}
