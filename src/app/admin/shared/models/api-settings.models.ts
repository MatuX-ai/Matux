/**
 * 全局 API 设置模型定义
 *
 * 用于管理所有外部服务和第三方集成的 API 配置
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

/**
 * OpenHydra 服务配置
 */
export interface OpenHydraConfig {
  /** API 基础 URL */
  apiUrl: string;
  /** API 密钥 */
  apiKey: string;
  /** 是否启用 */
  enabled: boolean;
  /** 超时时间 (毫秒) */
  timeout?: number;
  /** 备注说明 */
  notes?: string;
}

/**
 * JupyterHub 服务配置
 */
export interface JupyterHubConfig {
  /** JupyterHub URL */
  url: string;
  /** API Token */
  apiToken?: string;
  /** 是否启用 */
  enabled: boolean;
  /** 默认用户角色 */
  defaultRole?: 'user' | 'admin' | 'instructor';
}

/**
 * 数据库连接配置
 */
export interface DatabaseConnectionConfig {
  /** 连接名称 */
  name: string;
  /** 主机地址 */
  host: string;
  /** 端口 */
  port: number;
  /** 数据库名称 */
  database: string;
  /** 用户名 */
  username: string;
  /** 密码 (加密存储) */
  password?: string;
  /** SSL 连接 */
  ssl?: boolean;
  /** 连接池大小 */
  poolSize?: number;
  /** 是否启用 */
  enabled: boolean;
}

/**
 * MQTT 消息服务配置
 */
export interface MqttConfig {
  /** Broker 地址 */
  brokerUrl: string;
  /** 端口 */
  port: number;
  /** 用户名 */
  username?: string;
  /** 密码 */
  password?: string;
  /** 是否启用 TLS */
  tlsEnabled?: boolean;
  /** QoS 级别 */
  qos?: number;
  /** 是否启用 */
  enabled: boolean;
}

/**
 * Prometheus 监控配置
 */
export interface PrometheusConfig {
  /** Prometheus Server URL */
  serverUrl: string;
  /** Metrics 端点 */
  metricsEndpoint: string;
  /** 采集间隔 (秒) */
  scrapeInterval?: number;
  /** 是否启用 */
  enabled: boolean;
}

/**
 * Celery 任务队列配置
 */
export interface CeleryConfig {
  /** Broker URL (Redis/RabbitMQ) */
  brokerUrl: string;
  /** Result Backend URL */
  resultBackendUrl?: string;
  /** 默认队列名称 */
  defaultQueue?: string;
  /** Worker 数量 */
  workerCount?: number;
  /** 是否启用 */
  enabled: boolean;
}

/**
 * 对象存储配置 (S3 兼容)
 */
export interface ObjectStorageConfig {
  /** 服务提供商 */
  provider: 'aws-s3' | 'aliyun-oss' | 'tencent-cos' | 'minio';
  /** Access Key */
  accessKey: string;
  /** Secret Key */
  secretKey: string;
  /** Bucket 名称 */
  bucket: string;
  /** 区域 */
  region?: string;
  /** 端点 URL */
  endpoint?: string;
  /** 是否启用 */
  enabled: boolean;
}

/**
 * AI 服务配置 (通用)
 */
export interface AiServiceConfig {
  /** 服务名称 */
  serviceName: string;
  /** API 端点 */
  endpoint: string;
  /** API 密钥 */
  apiKey: string;
  /** 模型名称 */
  model?: string;
  /** 最大 Token 数 */
  maxTokens?: number;
  /** 温度参数 */
  temperature?: number;
  /** 是否启用 */
  enabled: boolean;
}

/**
 * 全局 API 设置汇总
 */
export interface GlobalApiSettings {
  /** OpenHydra 集成配置 */
  openHydra?: OpenHydraConfig;
  /** JupyterHub 配置 */
  jupyterHub?: JupyterHubConfig;
  /** 数据库连接列表 */
  databases?: DatabaseConnectionConfig[];
  /** MQTT 配置 */
  mqtt?: MqttConfig;
  /** Prometheus 监控配置 */
  prometheus?: PrometheusConfig;
  /** Celery 任务队列配置 */
  celery?: CeleryConfig;
  /** 对象存储配置 */
  objectStorage?: ObjectStorageConfig;
  /** AI 服务配置列表 */
  aiServices?: AiServiceConfig[];
  /** 最后更新时间 */
  lastUpdated?: string;
  /** 更新者 */
  updatedBy?: string;
}

/**
 * API 设置保存响应
 */
export interface ApiSettingsResponse {
  /** 是否成功 */
  success: boolean;
  /** 消息 */
  message?: string;
  /** 设置数据 */
  data?: GlobalApiSettings;
  /** 错误信息 */
  error?: string;
}
