/**
 * API 设置管理服务
 *
 * 提供全局 API 配置的增删改查功能
 * 支持本地存储和后端 API 同步
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';

import {
  AiServiceConfig,
  ApiSettingsResponse,
  CeleryConfig,
  DatabaseConnectionConfig,
  GlobalApiSettings,
  JupyterHubConfig,
  MqttConfig,
  ObjectStorageConfig,
  OpenHydraConfig,
  PrometheusConfig,
} from '../models/api-settings.models';

@Injectable({
  providedIn: 'root',
})
export class ApiSettingsService {
  private readonly API_BASE = '/api/v1/admin/settings';
  private readonly STORAGE_KEY = 'admin_api_settings_cache';

  constructor(private http: HttpClient) {}

  /**
   * 获取所有 API 设置
   */
  getGlobalSettings(): Observable<GlobalApiSettings> {
    return this.http.get<ApiSettingsResponse>(this.API_BASE).pipe(
      map((response) => {
        if (response.success && response.data) {
          return response.data;
        }
        // 如果 API 失败，返回默认配置
        return this.getDefaultSettings();
      }),
      catchError((error) => {
        console.error('获取全局 API 设置失败:', error);
        // 返回模拟数据用于开发
        return of(this.getMockSettings());
      })
    );
  }

  /**
   * 保存全局 API 设置
   */
  saveGlobalSettings(settings: GlobalApiSettings): Observable<ApiSettingsResponse> {
    const settingsWithMeta = {
      ...settings,
      lastUpdated: new Date().toISOString(),
      updatedBy: 'admin', // TODO: 从当前登录用户获取
    };

    return this.http.post<ApiSettingsResponse>(this.API_BASE, settingsWithMeta).pipe(
      tap(() => {
        // 保存到本地缓存
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(settingsWithMeta));
      }),
      catchError((error) => {
        console.error('保存全局 API 设置失败:', error);
        return throwError(() => new Error('保存失败，请检查网络连接'));
      })
    );
  }

  /**
   * 测试 API 连接
   */
  testApiConnection(
    serviceType: string,
    config: OpenHydraConfig | JupyterHubConfig | DatabaseConnectionConfig | MqttConfig
  ): Observable<{ success: boolean; message: string; responseTime?: number }> {
    const startTime = Date.now();

    // 根据服务类型执行不同的测试
    switch (serviceType.toLowerCase()) {
      case 'openhydra':
        return this.testOpenHydraConnection(config as OpenHydraConfig).pipe(
          map((result) => ({
            ...result,
            responseTime: Date.now() - startTime,
          }))
        );

      case 'jupyterhub':
        return this.testJupyterHubConnection(config as JupyterHubConfig).pipe(
          map((result) => ({
            ...result,
            responseTime: Date.now() - startTime,
          }))
        );

      case 'database':
        return this.testDatabaseConnection(config as DatabaseConnectionConfig).pipe(
          map((result) => ({
            ...result,
            responseTime: Date.now() - startTime,
          }))
        );

      case 'mqtt':
        return this.testMqttConnection(config as MqttConfig).pipe(
          map((result) => ({
            ...result,
            responseTime: Date.now() - startTime,
          }))
        );

      default:
        return of({
          success: false,
          message: `不支持的服务类型：${serviceType}`,
        });
    }
  }

  /**
   * 测试 OpenHydra 连接
   */
  private testOpenHydraConnection(
    config: OpenHydraConfig
  ): Observable<{ success: boolean; message: string }> {
    if (!config.enabled) {
      return of({ success: false, message: 'OpenHydra 服务未启用' });
    }

    // 发送测试请求到 OpenHydra API
    return this.http
      .get(`${config.apiUrl}/health`, {
        headers: {
          Authorization: `Bearer ${config.apiKey}`,
        },
        observe: 'response',
      })
      .pipe(
        map((response) => {
          if (response.status === 200) {
            return { success: true, message: 'OpenHydra 连接成功' };
          }
          return { success: false, message: 'OpenHydra 连接失败' };
        }),
        catchError((error) => {
          return of({
            success: false,
            message: `OpenHydra 连接失败:${(error as Error).message || '未知错误'}`,
          });
        })
      );
  }

  /**
   * 测试 JupyterHub 连接
   */
  private testJupyterHubConnection(
    config: JupyterHubConfig
  ): Observable<{ success: boolean; message: string }> {
    if (!config.enabled) {
      return of({ success: false, message: 'JupyterHub 服务未启用' });
    }

    return this.http
      .get(`${config.url}/hub/api`, {
        headers: config.apiToken
          ? {
              Authorization: `token ${config.apiToken}`,
            }
          : {},
        observe: 'response',
      })
      .pipe(
        map((response) => {
          if (response.status === 200) {
            return { success: true, message: 'JupyterHub 连接成功' };
          }
          return { success: false, message: 'JupyterHub 连接失败' };
        }),
        catchError((error) => {
          return of({
            success: false,
            message: `JupyterHub 连接失败:${(error as Error).message || '未知错误'}`,
          });
        })
      );
  }

  /**
   * 测试数据库连接
   */
  private testDatabaseConnection(
    config: DatabaseConnectionConfig
  ): Observable<{ success: boolean; message: string }> {
    if (!config.enabled) {
      return of({ success: false, message: '数据库连接未启用' });
    }

    // 调用后端 API 测试数据库连接
    return this.http
      .post<{ success: boolean; message: string }>(`${this.API_BASE}/test-database`, config)
      .pipe(
        catchError((error) => {
          return of({
            success: false,
            message: `数据库连接测试失败:${(error as Error).message || '未知错误'}`,
          });
        })
      );
  }

  /**
   * 测试 MQTT 连接
   */
  private testMqttConnection(
    config: MqttConfig
  ): Observable<{ success: boolean; message: string }> {
    if (!config.enabled) {
      return of({ success: false, message: 'MQTT 服务未启用' });
    }

    // 调用后端 API 测试 MQTT 连接
    return this.http
      .post<{ success: boolean; message: string }>(`${this.API_BASE}/test-mqtt`, config)
      .pipe(
        catchError((error) => {
          return of({
            success: false,
            message: `MQTT 连接测试失败:${(error as Error).message || '未知错误'}`,
          });
        })
      );
  }

  /**
   * 添加 AI 服务配置
   */
  addAiService(service: AiServiceConfig): Observable<boolean> {
    return this.getGlobalSettings().pipe(
      map((settings) => {
        if (!settings.aiServices) {
          settings.aiServices = [];
        }
        settings.aiServices.push(service);
        return settings;
      }),
      map((updatedSettings) => {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedSettings));
        return true;
      })
    );
  }

  /**
   * 删除 AI 服务配置
   */
  removeAiService(serviceName: string): Observable<boolean> {
    return this.getGlobalSettings().pipe(
      map((settings) => {
        if (settings.aiServices) {
          settings.aiServices = settings.aiServices.filter((s) => s.serviceName !== serviceName);
        }
        return settings;
      }),
      map((updatedSettings) => {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedSettings));
        return true;
      })
    );
  }

  /**
   * 添加数据库连接配置
   */
  addDatabaseConnection(connection: DatabaseConnectionConfig): Observable<boolean> {
    return this.getGlobalSettings().pipe(
      map((settings) => {
        if (!settings.databases) {
          settings.databases = [];
        }
        settings.databases.push(connection);
        return settings;
      }),
      map((updatedSettings) => {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedSettings));
        return true;
      })
    );
  }

  /**
   * 删除数据库连接配置
   */
  removeDatabaseConnection(connectionName: string): Observable<boolean> {
    return this.getGlobalSettings().pipe(
      map((settings) => {
        if (settings.databases) {
          settings.databases = settings.databases.filter((db) => db.name !== connectionName);
        }
        return settings;
      }),
      map((updatedSettings) => {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedSettings));
        return true;
      })
    );
  }

  /**
   * 获取默认设置
   */
  private getDefaultSettings(): GlobalApiSettings {
    return {
      openHydra: {
        apiUrl: '', // OpenHydra API 基础地址
        apiKey: '', // OpenHydra API 认证密钥
        enabled: false,
      },
      jupyterHub: {
        url: '', // JupyterHub 服务地址
        apiToken: '', // JupyterHub API 认证令牌
        enabled: false,
      },
      databases: [], // 数据库连接列表
      mqtt: undefined, // MQTT 消息服务配置
      prometheus: undefined, // Prometheus 监控配置
      celery: undefined, // Celery 任务队列配置
      objectStorage: undefined, // 对象存储配置
      aiServices: [], // AI 服务配置列表
    };
  }

  /**
   * 获取模拟设置 (用于开发环境)
   */
  private getMockSettings(): GlobalApiSettings {
    return {
      openHydra: this.getMockOpenHydraConfig(),
      jupyterHub: this.getMockJupyterHubConfig(),
      databases: this.getMockDatabaseConfigs(),
      mqtt: this.getMockMqttConfig(),
      prometheus: this.getMockPrometheusConfig(),
      celery: this.getMockCeleryConfig(),
      objectStorage: this.getMockObjectStorageConfig(),
      aiServices: this.getMockAiServiceConfigs(),
      lastUpdated: new Date().toISOString(),
      updatedBy: 'system',
    };
  }

  /**
   * 获取模拟的 OpenHydra 配置 (开发环境)
   */
  private getMockOpenHydraConfig(): OpenHydraConfig {
    return {
      apiUrl: 'http://localhost:8080', // 本地开发环境地址
      apiKey: 'openhydra-test-key', // 测试用 API 密钥
      enabled: true,
      timeout: 5000, // 超时时间 5 秒
      notes: 'OpenHydra 开发环境',
    };
  }

  /**
   * 获取模拟的 JupyterHub 配置 (开发环境)
   */
  private getMockJupyterHubConfig(): JupyterHubConfig {
    return {
      url: 'http://localhost:8000', // 本地开发环境地址
      apiToken: 'jupyter-test-token', // 测试用 API 令牌
      enabled: true,
      defaultRole: 'user', // 默认用户角色
    };
  }

  /**
   * 获取模拟的数据库配置列表 (开发环境)
   */
  private getMockDatabaseConfigs(): DatabaseConnectionConfig[] {
    return [
      {
        name: '主数据库', // 主业务数据库
        host: 'localhost',
        port: 5432, // PostgreSQL 默认端口
        database: 'imato_main',
        username: 'postgres',
        password: '***', // 密码已脱敏
        ssl: false,
        poolSize: 10, // 连接池大小
        enabled: true,
      },
    ];
  }

  /**
   * 获取模拟的 MQTT 配置 (开发环境)
   */
  private getMockMqttConfig(): MqttConfig {
    return {
      brokerUrl: 'tcp://localhost', // 本地 MQTT Broker
      port: 1883, // MQTT 默认端口
      username: 'mqtt_user',
      password: '***', // 密码已脱敏
      tlsEnabled: false,
      qos: 1, // QoS 级别：至少送达一次
      enabled: false,
    };
  }

  /**
   * 获取模拟的 Prometheus 配置 (开发环境)
   */
  private getMockPrometheusConfig(): PrometheusConfig {
    return {
      serverUrl: 'http://localhost:9090', // 本地 Prometheus 服务
      metricsEndpoint: '/metrics', // 指标采集端点
      scrapeInterval: 15, // 采集间隔 15 秒
      enabled: false,
    };
  }

  /**
   * 获取模拟的 Celery 配置 (开发环境)
   */
  private getMockCeleryConfig(): CeleryConfig {
    return {
      brokerUrl: 'redis://localhost:6379/0', // Redis Broker
      resultBackendUrl: 'redis://localhost:6379/0', // 结果后端存储
      defaultQueue: 'default', // 默认队列名称
      workerCount: 4, // Worker 进程数
      enabled: true,
    };
  }

  /**
   * 获取模拟的对象存储配置 (开发环境)
   */
  private getMockObjectStorageConfig(): ObjectStorageConfig {
    return {
      provider: 'minio', // MinIO 对象存储
      accessKey: 'minioadmin', // 访问密钥
      secretKey: '***', // 密钥已脱敏
      bucket: 'imato-storage', // 存储桶名称
      region: 'us-east-1', // 区域
      endpoint: 'http://localhost:9000', // MinIO 服务地址
      enabled: false,
    };
  }

  /**
   * 获取模拟的 AI 服务配置列表 (开发环境)
   */
  private getMockAiServiceConfigs(): AiServiceConfig[] {
    return [
      {
        serviceName: 'OpenAI GPT', // OpenAI GPT 服务
        endpoint: 'https://api.openai.com/v1', // OpenAI API 端点
        apiKey: 'sk-***', // API 密钥已脱敏
        model: 'gpt-4', // 使用 GPT-4 模型
        maxTokens: 2048, // 最大 Token 数
        temperature: 0.7, // 温度参数：创造性平衡
        enabled: false,
      },
    ];
  }
}
