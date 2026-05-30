/**
 * 离线数据模型定义
 * 定义离线存储所需的各种数据结构
 */

/**
 * 离线数据存储键名枚举
 */
export enum OfflineStorageKey {
  /** 用户数据 */
  USER_DATA = 'userData',
  /** 课程数据 */
  COURSE_DATA = 'courseData',
  /** 任务数据 */
  TASK_DATA = 'taskData',
  /** 设置数据 */
  SETTINGS = 'settings',
  /** 缓存数据 */
  CACHE = 'cache',
  /** 待同步操作队列 */
  SYNC_QUEUE = 'syncQueue',
}

/**
 * 离线操作类型枚举
 */
export enum OfflineOperationType {
  /** 创建操作 */
  CREATE = 'CREATE',
  /** 更新操作 */
  UPDATE = 'UPDATE',
  /** 删除操作 */
  DELETE = 'DELETE',
}

/**
 * 离线操作状态枚举
 */
export enum OfflineOperationStatus {
  /** 待处理 */
  PENDING = 'PENDING',
  /** 同步中 */
  SYNCING = 'SYNCING',
  /** 已完成 */
  COMPLETED = 'COMPLETED',
  /** 失败 */
  FAILED = 'FAILED',
}

/**
 * 离线操作记录接口
 */
export interface OfflineOperation {
  /** 唯一标识符 */
  id: string;
  /** 操作类型 */
  type: OfflineOperationType;
  /** 操作状态 */
  status: OfflineOperationStatus;
  /** 数据表名 */
  tableName: string;
  /** 数据记录ID */
  recordId: string;
  /** 操作数据 */
  data: any;
  /** 创建时间 */
  createdAt: Date;
  /** 最后更新时间 */
  updatedAt: Date;
  /** 重试次数 */
  retryCount: number;
  /** 错误信息 */
  errorMessage?: string;
}

/**
 * 离线同步配置接口
 */
export interface OfflineSyncConfig {
  /** 是否启用自动同步 */
  autoSync: boolean;
  /** 同步间隔（毫秒） */
  syncInterval: number;
  /** 最大重试次数 */
  maxRetryAttempts: number;
  /** 网络质量要求 */
  minimumNetworkQuality: 'any' | 'fast-3g' | '4g' | 'wifi';
  /** 批量同步大小 */
  batchSize: number;
}

/**
 * 离线存储统计信息接口
 */
export interface OfflineStorageStats {
  /** 总存储大小（字节） */
  totalSize: number;
  /** 各类数据数量 */
  itemCounts: Record<string, number>;
  /** 最后同步时间 */
  lastSyncTime?: Date;
  /** 待同步操作数 */
  pendingOperations: number;
}

/**
 * 离线数据实体基接口
 */
export interface OfflineEntity {
  /** 实体ID */
  id: string;
  /** 创建时间 */
  createdAt: Date;
  /** 更新时间 */
  updatedAt: Date;
  /** 版本号 */
  version: number;
}

/**
 * 离线用户数据接口
 */
export interface OfflineUserData extends OfflineEntity {
  /** 用户名 */
  username: string;
  /** 邮箱 */
  email: string;
  /** 显示名称 */
  displayName: string;
  /** 头像URL */
  avatarUrl?: string;
  /** 角色 */
  roles: string[];
  /** 最后登录时间 */
  lastLoginAt: Date;
  /** 偏好设置 */
  preferences: Record<string, any>;
}

/**
 * 离线课程数据接口
 */
export interface OfflineCourseData extends OfflineEntity {
  /** 课程标题 */
  title: string;
  /** 课程描述 */
  description: string;
  /** 课程封面 */
  coverImage?: string;
  /** 教师ID */
  teacherId: string;
  /** 学生IDs */
  studentIds: string[];
  /** 课程状态 */
  status: 'draft' | 'published' | 'archived';
  /** 课时列表 */
  lessons: OfflineLessonData[];
  /** 分类标签 */
  tags: string[];
  /** 进度信息 */
  progress?: Record<string, any>;
}

/**
 * 离线课时数据接口
 */
export interface OfflineLessonData extends OfflineEntity {
  /** 课时标题 */
  title: string;
  /** 课时内容 */
  content: string;
  /** 排序序号 */
  order: number;
  /** 附件列表 */
  attachments: OfflineAttachment[];
  /** 完成状态 */
  completed: boolean;
}

/**
 * 离线附件接口
 */
export interface OfflineAttachment {
  /** 附件ID */
  id: string;
  /** 文件名 */
  filename: string;
  /** 文件大小 */
  size: number;
  /** MIME类型 */
  mimeType: string;
  /** 下载URL */
  url: string;
  /** 本地缓存路径 */
  localPath?: string;
}

/**
 * 离线任务数据接口
 */
export interface OfflineTaskData extends OfflineEntity {
  /** 任务标题 */
  title: string;
  /** 任务描述 */
  description: string;
  /** 任务类型 */
  type: string;
  /** 分配给用户ID */
  assigneeId: string;
  /** 创建者ID */
  creatorId: string;
  /** 截止日期 */
  dueDate?: Date;
  /** 优先级 */
  priority: 'low' | 'medium' | 'high';
  /** 状态 */
  status: 'todo' | 'in-progress' | 'completed' | 'cancelled';
  /** 相关课程ID */
  courseId?: string;
  /** 标签 */
  tags: string[];
}
