/**
 * 使用指南对话框组件
 *
 * 显示各个 API 配置的详细帮助信息
 */

import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

export interface HelpDialogData {
  serviceType: string;
}

@Component({
  selector: 'app-help-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatIconModule, MatButtonModule],
  template: `
    <div class="help-dialog">
      <div class="dialog-header">
        <h2 mat-dialog-title>
          <mat-icon>help_outline</mat-icon>
          {{ data.serviceType | titlecase }} - 使用指南
        </h2>
        <button mat-icon-button mat-dialog-close>
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div mat-dialog-content class="dialog-content">
        <section class="help-section">
          <h3><mat-icon>menu_book</mat-icon> 功能概述</h3>
          <p>{{ getOverview() }}</p>
        </section>

        <section class="help-section">
          <h3><mat-icon>rocket_launch</mat-icon> 快速开始</h3>
          <ol>
            <li *ngFor="let step of getQuickStartSteps()">{{ step }}</li>
          </ol>
        </section>

        <section class="help-section">
          <h3><mat-icon>settings</mat-icon> 配置项说明</h3>
          <div class="config-items">
            <div class="config-item" *ngFor="let item of getConfigItems()">
              <div class="config-name">
                <strong>{{ item.name }}</strong>
                <span class="required" *ngIf="item.required">*</span>
              </div>
              <div class="config-description">{{ item.description }}</div>
              <div class="config-example" *ngIf="item.example">
                <code>示例：{{ item.example }}</code>
              </div>
            </div>
          </div>
        </section>

        <section class="help-section">
          <h3><mat-icon>wifi_find</mat-icon> 测试连接</h3>
          <p>点击底部的"测试连接"按钮，系统将验证您的配置是否正确。</p>
          <ul>
            <li>✅ 绿色提示：连接成功</li>
            <li>❌ 红色提示：连接失败，请检查配置</li>
          </ul>
        </section>

        <section class="help-section">
          <h3><mat-icon>save</mat-icon> 保存设置</h3>
          <p>配置完成后，点击"保存"按钮即可保存设置。系统会自动验证必填项。</p>
        </section>

        <section class="help-section" *ngIf="getBackendApiRequirements().length > 0">
          <h3><mat-icon>api</mat-icon> 后端 API 接口要求</h3>
          <ul>
            <li *ngFor="let req of getBackendApiRequirements()">{{ req }}</li>
          </ul>
        </section>

        <section class="help-section">
          <h3><mat-icon>bug_report</mat-icon> 故障排查</h3>
          <div *ngFor="let tip of getTroubleshootingTips()">
            <p>
              <strong>{{ tip.issue }}:</strong> {{ tip.solution }}
            </p>
          </div>
        </section>

        <section class="help-section" *ngIf="getExamples().length > 0">
          <h3><mat-icon>lightbulb</mat-icon> 使用示例</h3>
          <ul>
            <li *ngFor="let example of getExamples()">{{ example }}</li>
          </ul>
        </section>
      </div>

      <div mat-dialog-actions class="dialog-actions">
        <button mat-button mat-dialog-close>关闭</button>
      </div>
    </div>
  `,
  styles: [
    `
      .help-dialog {
        max-width: 800px;
      }

      .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 16px;
        border-bottom: 1px solid #e0e0e0;

        h2 {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 0;
          font-size: 20px;
          color: #1976d2;

          mat-icon {
            color: #1976d2;
          }
        }
      }

      .dialog-content {
        max-height: 60vh;
        overflow-y: auto;
        padding: 8px 0;

        .help-section {
          margin-bottom: 24px;

          h3 {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #333;
            font-size: 16px;
            margin-bottom: 12px;

            mat-icon {
              color: #4caf50;
              font-size: 20px;
            }
          }

          p {
            color: #666;
            line-height: 1.6;
            margin: 8px 0;
          }

          ol,
          ul {
            padding-left: 24px;
            color: #666;
            line-height: 1.8;

            li {
              margin-bottom: 8px;
            }
          }
        }

        .config-items {
          .config-item {
            background-color: #f5f5f5;
            padding: 12px 16px;
            margin-bottom: 12px;
            border-radius: 4px;
            border-left: 3px solid #4caf50;

            .config-name {
              margin-bottom: 4px;

              strong {
                color: #333;
                font-size: 14px;
              }

              .required {
                color: #f44336;
                margin-left: 4px;
              }
            }

            .config-description {
              color: #666;
              font-size: 13px;
              margin-bottom: 6px;
            }

            .config-example {
              code {
                background-color: #e8e8e8;
                padding: 4px 8px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #d81b60;
              }
            }
          }
        }
      }

      .dialog-actions {
        justify-content: flex-end;
        padding-top: 16px;
        border-top: 1px solid #e0e0e0;
      }
    `,
  ],
})
export class HelpDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<HelpDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: HelpDialogData
  ) {}

  getOverview(): string {
    const overviews: { [key: string]: string } = {
      openhydra:
        'OpenHydra 是一个强大的第三方服务集成平台，用于统一管理外部 API 连接。通过配置 API URL 和密钥，您可以轻松实现与外部系统的数据交换和功能集成。',
      jupyterhub:
        'JupyterHub 是一个多用户交互式计算环境，支持数据科学和机器学习教学。通过配置 JupyterHub，您可以为用户提供统一的 Notebook 开发环境和计算资源。',
      databases:
        '数据库连接管理允许您配置系统需要连接的数据库实例。支持 PostgreSQL、MySQL 等多种数据库类型，可配置主从库、读写分离等高级功能。',
      mqtt: 'MQTT 是轻量级的消息推送协议，适用于物联网和实时通信场景。配置 MQTT 服务后，系统可以实时推送通知和更新到客户端。',
      prometheus:
        'Prometheus 是开源的监控和告警系统，用于采集和存储系统指标。通过配置 Prometheus，您可以实时监控应用性能、资源使用率等关键指标。',
      celery:
        'Celery 是分布式任务队列系统，用于处理异步任务和定时任务。配置 Celery 可以提高系统的响应速度和可扩展性，适合处理耗时操作。',
      objectstorage:
        '对象存储提供可扩展的文件存储服务，兼容 AWS S3 API。支持 AWS S3、阿里云 OSS、腾讯云 COS、MinIO 等多种服务商，用于存储用户上传的文件、图片、视频等资源。',
      aiservices:
        'AI 服务配置允许您集成第三方 AI 能力，如 OpenAI GPT、Claude 等大语言模型。通过配置 AI 服务，您可以在应用中实现智能对话、内容生成、数据分析等功能。',
    };
    return overviews[this.data.serviceType.toLowerCase()] || '暂无详细说明。';
  }

  getQuickStartSteps(): string[] {
    const steps: { [key: string]: string[] } = {};
    steps['openhydra'] = this.getOpenHydraSteps();
    steps['jupyterhub'] = this.getJupyterHubSteps();
    steps['databases'] = this.getDatabasesSteps();
    steps['mqtt'] = this.getMqttSteps();
    steps['prometheus'] = this.getPrometheusSteps();
    steps['celery'] = this.getCelerySteps();
    steps['objectstorage'] = this.getObjectStorageSteps();
    steps['aiservices'] = this.getAiServicesSteps();
    return steps[this.data.serviceType.toLowerCase()] || ['暂无快速开始步骤。'];
  }

  private getOpenHydraSteps(): string[] {
    return [
      '填写 API URL（必填），例如：http://localhost:8080',
      '输入 API Key（如有）',
      '可选：调整超时时间和添加备注说明',
      '勾选"启用 OpenHydra 服务"',
      '点击"测试连接"验证配置',
      '点击"保存"按钮保存设置',
    ];
  }

  private getJupyterHubSteps(): string[] {
    return [
      '填写 JupyterHub URL（必填），例如：http://localhost:8000',
      '输入 API Token 进行身份验证',
      '选择默认角色（user/admin/instructor）',
      '勾选"启用 JupyterHub 服务"',
      '点击"测试连接"验证配置',
      '点击"保存"按钮',
    ];
  }

  private getDatabasesSteps(): string[] {
    return [
      '点击右上角"+"按钮添加新连接',
      '填写数据库主机地址、端口、数据库名',
      '输入用户名和密码',
      '可选：启用 SSL 加密连接',
      '设置连接池大小',
      '点击"测试连接"验证数据库连接',
      '保存配置',
    ];
  }

  private getMqttSteps(): string[] {
    return [
      '填写 Broker URL，例如：tcp://localhost',
      '输入端口号（默认 1883）',
      '填写用户名和密码（如有）',
      '可选：启用 TLS 加密',
      '选择 QoS 级别（0/1/2）',
      '勾选"启用 MQTT 服务"',
      '测试连接并保存',
    ];
  }

  private getPrometheusSteps(): string[] {
    return [
      '填写 Prometheus Server URL',
      '输入 Metrics Endpoint（默认/metrics）',
      '设置采集间隔（秒）',
      '勾选"启用 Prometheus 监控"',
      '测试连接并保存',
    ];
  }

  private getCelerySteps(): string[] {
    return [
      '填写 Broker URL，例如：redis://localhost:6379/0',
      '填写 Result Backend URL',
      '输入默认队列名称',
      '设置 Worker 数量',
      '勾选"启用 Celery 任务队列"',
      '保存配置',
    ];
  }

  private getObjectStorageSteps(): string[] {
    return [
      '选择服务提供商（AWS S3/阿里云 OSS/腾讯云 COS/MinIO）',
      '填写 Access Key 和 Secret Key',
      '输入 Bucket 名称',
      '填写区域（Region）',
      '可选：填写自定义 Endpoint',
      '勾选"启用对象存储服务"',
      '保存配置',
    ];
  }

  private getAiServicesSteps(): string[] {
    return [
      '点击右上角"+"按钮添加 AI 服务',
      '选择服务提供商（如 OpenAI）',
      '填写 API 端点和 API Key',
      '选择默认模型',
      '调整最大 Token 数和温度参数',
      '测试连接并保存',
    ];
  }

  getConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    const configs: {
      [key: string]: Array<{
        name: string;
        required: boolean;
        description: string;
        example?: string;
      }>;
    } = {};
    configs['openhydra'] = this.getOpenHydraConfigItems();
    configs['jupyterhub'] = this.getJupyterHubConfigItems();
    configs['mqtt'] = this.getMqttConfigItems();
    configs['prometheus'] = this.getPrometheusConfigItems();
    configs['celery'] = this.getCeleryConfigItems();
    configs['objectstorage'] = this.getObjectStorageConfigItems();
    return configs[this.data.serviceType.toLowerCase()] || [];
  }

  private getOpenHydraConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    return [
      {
        name: 'API URL',
        required: true,
        description: 'OpenHydra 服务的访问地址',
        example: 'http://localhost:8080',
      },
      { name: 'API Key', required: false, description: '用于身份验证的 API 密钥' },
      {
        name: '超时时间',
        required: false,
        description: '请求超时时间（毫秒），默认 5000ms',
      },
      {
        name: '备注说明',
        required: false,
        description: '可选的描述信息，用于记录配置用途',
      },
      {
        name: '启用服务',
        required: false,
        description: '勾选后启用 OpenHydra 集成',
      },
    ];
  }

  private getJupyterHubConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    return [
      {
        name: 'URL',
        required: true,
        description: 'JupyterHub 服务的访问地址',
        example: 'http://localhost:8000',
      },
      {
        name: 'API Token',
        required: false,
        description: '用于 API 调用的身份验证令牌',
      },
      {
        name: '默认角色',
        required: false,
        description: '用户的默认角色：user/admin/instructor',
      },
      {
        name: '启用服务',
        required: false,
        description: '勾选后启用 JupyterHub 集成',
      },
    ];
  }

  private getMqttConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    return [
      {
        name: 'Broker URL',
        required: false,
        description: 'MQTT 代理服务器地址',
        example: 'tcp://localhost',
      },
      { name: '端口', required: false, description: 'MQTT 服务端口，默认 1883' },
      { name: '用户名', required: false, description: '连接 MQTT 的用户名' },
      { name: '密码', required: false, description: '连接 MQTT 的密码' },
      { name: 'TLS', required: false, description: '是否启用 TLS 加密连接' },
      { name: 'QoS', required: false, description: '消息质量级别（0/1/2）' },
    ];
  }

  private getPrometheusConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    return [
      {
        name: 'Server URL',
        required: false,
        description: 'Prometheus 服务器地址',
        example: 'http://localhost:9090',
      },
      {
        name: 'Metrics Endpoint',
        required: false,
        description: '指标采集端点，默认/metrics',
      },
      {
        name: '采集间隔',
        required: false,
        description: '数据采集间隔（秒），默认 15 秒',
      },
    ];
  }

  private getCeleryConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    return [
      {
        name: 'Broker URL',
        required: false,
        description: '消息代理地址',
        example: 'redis://localhost:6379/0',
      },
      {
        name: 'Result Backend',
        required: false,
        description: '任务结果存储地址',
      },
      { name: '默认队列', required: false, description: '默认任务队列名称' },
      {
        name: 'Worker 数量',
        required: false,
        description: '并发 Worker 数量，默认 4',
      },
    ];
  }

  private getObjectStorageConfigItems(): Array<{
    name: string;
    required: boolean;
    description: string;
    example?: string;
  }> {
    return [
      {
        name: '服务提供商',
        required: false,
        description: '选择存储服务商',
      },
      { name: 'Access Key', required: false, description: '访问密钥 ID' },
      { name: 'Secret Key', required: false, description: '访问密钥密码' },
      { name: 'Bucket 名称', required: false, description: '存储桶名称' },
      { name: '区域', required: false, description: '数据中心区域' },
      { name: 'Endpoint', required: false, description: '自定义访问端点' },
    ];
  }

  getBackendApiRequirements(): string[] {
    const requirements: { [key: string]: string[] } = {
      openhydra: [
        '后端需提供 GET /api/v1/settings/openhydra 接口获取配置',
        '后端需提供 POST /api/v1/settings/openhydra 接口保存配置',
        '后端需实现 OpenHydra API 连接测试功能',
      ],
      jupyterhub: [
        '后端需提供 GET /api/v1/settings/jupyterhub 接口',
        '后端需提供 POST /api/v1/settings/jupyterhub 接口',
        '后端需实现 JupyterHub API 连接验证',
      ],
      mqtt: [
        '后端需提供 MQTT 连接测试接口',
        '后端需实现 MQTT 客户端连接逻辑',
        '后端需支持 TLS 加密连接',
      ],
      prometheus: ['后端需提供 Prometheus 连接测试接口', '后端需实现指标采集配置'],
      celery: [
        '后端需配置 Celery Broker 连接',
        '后端需配置 Result Backend',
        '后端需启动 Celery Worker',
      ],
      objectstorage: [
        '后端需集成 AWS S3 SDK 或兼容 SDK',
        '后端需提供文件上传/下载接口',
        '后端需实现预签名 URL 生成功能',
      ],
      aiservices: [
        '后端需实现 AI 服务代理转发',
        '后端需处理 API Key 的安全存储',
        '后端需实现请求限流和配额管理',
      ],
    };
    return requirements[this.data.serviceType.toLowerCase()] || [];
  }

  getTroubleshootingTips(): Array<{ issue: string; solution: string }> {
    const tips: { [key: string]: Array<{ issue: string; solution: string }> } = {
      openhydra: [
        { issue: '连接超时', solution: '检查 API URL 是否正确，确认服务已启动且网络可达' },
        { issue: '认证失败', solution: '验证 API Key 是否正确，检查密钥是否过期' },
        { issue: '跨域错误', solution: '确认服务端已配置 CORS 允许跨域请求' },
      ],
      jupyterhub: [
        { issue: '404 Not Found', solution: '检查 URL 地址是否正确，确认 JupyterHub 服务运行正常' },
        { issue: '403 Forbidden', solution: '验证 API Token 是否有效，检查权限配置' },
        { issue: '无法创建用户环境', solution: '检查 JupyterHub 的 spawner 配置和资源限制' },
      ],
      mqtt: [
        { issue: '连接被拒绝', solution: '检查 Broker URL 和端口，确认防火墙允许连接' },
        { issue: '认证失败', solution: '验证用户名和密码，检查 MQTT 服务器的认证配置' },
        { issue: '消息推送失败', solution: '检查 Topic 订阅状态，确认 QoS 级别设置正确' },
      ],
      prometheus: [
        {
          issue: '无法采集指标',
          solution: '检查 Metrics Endpoint 是否正确，确认应用已暴露指标端点',
        },
        { issue: '数据不更新', solution: '验证采集间隔设置，检查 Prometheus 服务器状态' },
      ],
      celery: [
        { issue: '任务不执行', solution: '确认 Celery Worker 已启动，检查 Broker 连接' },
        { issue: '任务卡住', solution: '检查任务超时设置，查看 Worker 日志' },
        { issue: '连接 Redis 失败', solution: '验证 Redis 服务状态，检查连接 URL 格式' },
      ],
      objectstorage: [
        {
          issue: '权限错误',
          solution: '检查 Access Key 和 Secret Key 是否正确，验证 Bucket 权限策略',
        },
        { issue: '上传失败', solution: '确认 Bucket 存在且有写入权限，检查文件大小限制' },
        { issue: '下载速度慢', solution: '检查网络带宽，考虑使用 CDN 加速' },
      ],
    };
    return tips[this.data.serviceType.toLowerCase()] || [];
  }

  getExamples(): string[] {
    const examples: { [key: string]: string[] } = {
      openhydra: [
        '场景：集成第三方 CRM 系统 - 配置 OpenHydra 连接到 CRM API，实现客户数据同步',
        '场景：对接支付网关 - 通过 OpenHydra 统一管理支付接口配置',
      ],
      jupyterhub: [
        '场景：数据科学课程 - 为每个学生分配独立的 Jupyter 环境，支持团队协作',
        '场景：机器学习实验 - 提供 GPU 资源，支持大规模模型训练',
      ],
      mqtt: [
        '场景：实时通知推送 - 当订单状态变化时，通过 MQTT 推送给客户端',
        '场景：物联网设备监控 - 设备传感器数据通过 MQTT 实时上报',
      ],
      prometheus: [
        '场景：应用性能监控 - 监控 API 响应时间、错误率、QPS 等关键指标',
        '场景：资源使用监控 - 监控 CPU、内存、磁盘使用率，设置告警阈值',
      ],
      celery: [
        '场景：异步邮件发送 - 用户注册后，通过 Celery 异步发送验证邮件',
        '场景：定时数据备份 - 每天凌晨 2 点自动备份数据库到对象存储',
      ],
      objectstorage: [
        '场景：用户头像存储 - 用户上传的头像文件存储到 S3，返回 CDN 链接',
        '场景：课程视频托管 - 将教学视频上传到对象存储，通过 CDN 加速播放',
      ],
      aiservices: [
        '场景：智能客服 - 集成 OpenAI GPT，自动回答用户常见问题',
        '场景：内容生成 - 使用 AI 生成产品描述、营销文案等内容',
      ],
    };
    return examples[this.data.serviceType.toLowerCase()] || [];
  }
}
