/**
 * 全局 API 设置组件
 *
 * 提供统一的界面用于管理所有外部服务的 API 配置
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';

import {
  AiServiceConfig,
  DatabaseConnectionConfig,
  GlobalApiSettings,
  JupyterHubConfig,
  MqttConfig,
  OpenHydraConfig,
} from '../../models/api-settings.models';
import { ApiSettingsService } from '../../services/api-settings.service';

import { HelpDialogComponent, HelpDialogData } from './help-dialog.component';

@Component({
  selector: 'app-api-settings',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatToolbarModule,
    MatTabsModule,
    MatCheckboxModule,
    MatSnackBarModule,
    MatDialogModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './api-settings.component.html',
  styleUrls: ['./api-settings.component.scss'],
})
export class ApiSettingsComponent implements OnInit {
  /** 全局设置表单 */
  settingsForm!: FormGroup;

  /** 加载中 */
  loading = false;

  /** 保存中 */
  saving = false;

  /** 当前选中的 Tab */
  selectedTabIndex = 0;

  /** 全局 API 设置数据 */
  settings: GlobalApiSettings = {};

  constructor(
    private fb: FormBuilder,
    private settingsService: ApiSettingsService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.initForm();
    // 延迟加载数据，先显示页面
    setTimeout(() => {
      this.loadSettings();
    }, 100);
  }

  /**
   * 显示使用指南对话框
   */
  showHelp(serviceType: string): void {
    const data: HelpDialogData = { serviceType };
    this.dialog.open(HelpDialogComponent, {
      width: '90vw',
      maxWidth: '800px',
      maxHeight: '90vh',
      data,
    });
  }

  /**
   * 获取数据库连接列表控制器
   */
  get databasesControls(): AbstractControl[] {
    const databasesArray = this.settingsForm.get('databases') as FormArray;
    return databasesArray?.controls || [];
  }

  /**
   * 安全获取数据库表单控件
   */
  getDatabaseControl(index: number, controlName: string): FormControl | null {
    const databasesArray = this.settingsForm.get('databases') as FormArray;
    const control = databasesArray?.at(index)?.get(controlName);
    return control as FormControl | null;
  }

  /**
   * 获取 AI 服务列表控制器
   */
  get aiServicesControls(): AbstractControl[] {
    const aiServicesArray = this.settingsForm.get('aiServices') as FormArray;
    return aiServicesArray?.controls || [];
  }

  /**
   * 根据端点识别 AI 服务提供商
   */
  getAiProvider(endpoint: string | null | undefined): string {
    if (!endpoint) return '未配置';

    // 国内 AI 服务映射表
    const domesticProviders: Record<string, string> = {
      'deepseek.com': 'DeepSeek', // DeepSeek 深度求索
      'moonshot.cn': '月之暗面 (Kimi)', // Kimi 智能助手
      'aliyuncs.com': '通义千问', // 阿里云通义千问
    };

    // 优先检查国内服务商
    const domesticResult = this.findProviderByDomain(endpoint, domesticProviders);
    if (domesticResult) return domesticResult;

    // 国际 AI 服务映射表
    const internationalProviders: Record<string, string> = {
      'openai.com': 'OpenAI', // OpenAI GPT 系列
      'anthropic.com': 'Anthropic', // Claude 系列
      'azure.com': 'Azure OpenAI', // 微软 Azure OpenAI
      'google.com': 'Google AI', // Google Gemini/PaLM
      'cohere.com': 'Cohere', // Cohere NLP
      'together.ai': 'Together AI', // Together AI
      'replicate.com': 'Replicate', // Replicate ML
      'huggingface.co': 'Hugging Face', // Hugging Face Transformers
    };

    return this.findProviderByDomain(endpoint, internationalProviders) ?? '自定义';
  }

  /**
   * 根据域名映射查找服务提供商
   * @param endpoint API 端点 URL
   * @param providers 域名到名称的映射表
   * @returns 找到的提供商名称，未找到返回空字符串
   */
  private findProviderByDomain(endpoint: string, providers: Record<string, string>): string | null {
    for (const [domain, name] of Object.entries(providers)) {
      if (endpoint.includes(domain)) return name;
    }
    return null; // 未找到匹配的提供商
  }

  /**
   * 安全获取 AI 服务表单控件
   */
  getAiServiceControl(index: number, controlName: string): FormControl | null {
    const aiServicesArray = this.settingsForm.get('aiServices') as FormArray;
    const control = aiServicesArray?.at(index)?.get(controlName);
    return control as FormControl | null;
  }

  /**
   * 初始化表单
   */
  private initForm(): void {
    this.settingsForm = this.fb.group({
      openHydra: this.createOpenHydraGroup(), // OpenHydra 集成配置
      jupyterHub: this.createJupyterHubGroup(), // JupyterHub 教学环境配置
      databases: this.fb.array([]), // 数据库连接列表
      mqtt: this.createMqttGroup(), // MQTT 消息队列配置
      prometheus: this.createPrometheusGroup(), // Prometheus 监控配置
      celery: this.createCeleryGroup(), // Celery 任务队列配置
      objectStorage: this.createObjectStorageGroup(), // 对象存储配置
      aiServices: this.fb.array([]), // AI 服务集成列表
    });

    // 添加默认配置项
    this.addDefaultDatabaseConfig();
    this.addDefaultAiServices();
  }

  /**
   * 创建 OpenHydra 表单组
   */
  private createOpenHydraGroup(): FormGroup {
    /* eslint-disable @typescript-eslint/unbound-method */
    return this.fb.group({
      apiUrl: ['', [Validators.required]],
      apiKey: [''],
      enabled: [false],
      timeout: [5000],
      notes: [''],
    });
    /* eslint-enable @typescript-eslint/unbound-method */
  }

  /**
   * 创建 JupyterHub 表单组
   */
  private createJupyterHubGroup(): FormGroup {
    /* eslint-disable @typescript-eslint/unbound-method */
    return this.fb.group({
      url: ['', [Validators.required]],
      apiToken: [''],
      enabled: [false],
      defaultRole: ['user'],
    });
    /* eslint-enable @typescript-eslint/unbound-method */
  }

  /**
   * 创建 MQTT 表单组
   */
  private createMqttGroup(): FormGroup {
    return this.fb.group({
      brokerUrl: [''],
      port: [1883],
      username: [''],
      password: [''],
      tlsEnabled: [false],
      qos: [1],
      enabled: [false],
    });
  }

  /**
   * 创建 Prometheus 表单组
   */
  private createPrometheusGroup(): FormGroup {
    return this.fb.group({
      serverUrl: [''],
      metricsEndpoint: ['/metrics'],
      scrapeInterval: [15],
      enabled: [false],
    });
  }

  /**
   * 创建 Celery 表单组
   */
  private createCeleryGroup(): FormGroup {
    return this.fb.group({
      brokerUrl: [''],
      resultBackendUrl: [''],
      defaultQueue: ['default'],
      workerCount: [4],
      enabled: [false],
    });
  }

  /**
   * 创建对象存储表单组
   */
  private createObjectStorageGroup(): FormGroup {
    return this.fb.group({
      provider: ['minio'],
      accessKey: [''],
      secretKey: [''],
      bucket: [''],
      region: [''],
      endpoint: [''],
      enabled: [false],
    });
  }

  /**
   * 添加默认数据库配置
   */
  private addDefaultDatabaseConfig(): void {
    const databasesArray = this.settingsForm.get('databases') as FormArray;
    databasesArray.push(
      this.fb.group({
        name: ['本地数据库'],
        host: ['localhost'],
        port: [5432],
        database: ['imato_main'],
        username: ['postgres'],
        password: [''],
        ssl: [false],
        poolSize: [10],
        enabled: [false],
      })
    );
  }

  /**
   * 添加默认 AI 服务配置
   */
  private addDefaultAiServices(): void {
    const aiServicesArray = this.settingsForm.get('aiServices') as FormArray;

    aiServicesArray.push(
      this.fb.group({
        serviceName: ['DeepSeek'],
        endpoint: ['https://api.deepseek.com/v1'],
        apiKey: [''],
        model: ['deepseek-chat'],
        maxTokens: [4096],
        temperature: [0.7],
        enabled: [false],
      })
    );
    aiServicesArray.push(
      this.fb.group({
        serviceName: ['Kimi 2.5'],
        endpoint: ['https://api.moonshot.cn/v1'],
        apiKey: [''],
        model: ['moonshot-v1-8k'],
        maxTokens: [8192],
        temperature: [0.7],
        enabled: [false],
      })
    );
    aiServicesArray.push(
      this.fb.group({
        serviceName: ['通义千问'],
        endpoint: ['https://dashscope.aliyuncs.com/api/v1'],
        apiKey: [''],
        model: ['qwen-turbo'],
        maxTokens: [8192],
        temperature: [0.7],
        enabled: [false],
      })
    );
  }

  /**
   * 加载设置数据
   */
  loadSettings(): void {
    this.loading = true;
    this.settingsService.getGlobalSettings().subscribe({
      next: (settings) => {
        this.settings = settings;

        // 先填充简单配置
        this.patchSimpleConfig('openHydra', settings.openHydra);
        this.patchSimpleConfig('jupyterHub', settings.jupyterHub);
        this.patchSimpleConfig('mqtt', settings.mqtt);
        this.patchSimpleConfig('prometheus', settings.prometheus);
        this.patchSimpleConfig('celery', settings.celery);
        this.patchSimpleConfig('objectStorage', settings.objectStorage);

        const aiServicesArray = this.settingsForm.get('aiServices') as FormArray;

        // 如果后端有 AI 服务数据，追加到默认配置后面
        if (settings.aiServices && settings.aiServices.length > 0) {
          settings.aiServices.forEach((item) => {
            aiServicesArray.push(this.fb.group(item));
          });
        }

        // 数据库同理
        if (settings.databases && settings.databases.length > 0) {
          const databasesArray = this.settingsForm.get('databases') as FormArray;
          settings.databases.forEach((item) => {
            databasesArray.push(this.fb.group(item));
          });
        }

        this.loading = false;
      },
      error: (error) => {
        console.error('加载设置失败:', error);
        this.snackBar.open('加载设置失败，将使用默认配置', '关闭', { duration: 3000 });
        this.loading = false;
        this.settings = this.getDefaultSettings();
      },
    });
  }

  /**
   * 获取默认设置（本地方法）
   */
  private getDefaultSettings(): GlobalApiSettings {
    return {
      openHydra: {
        apiUrl: '',
        apiKey: '',
        enabled: false,
      },
      jupyterHub: {
        url: '',
        apiToken: '',
        enabled: false,
      },
      databases: [],
      mqtt: undefined,
      prometheus: undefined,
      celery: undefined,
      objectStorage: undefined,
      aiServices: [],
    };
  }

  /**
   * 填充表单数据
   */
  private patchForm(settings: GlobalApiSettings): void {
    // 填充简单配置
    this.patchSimpleConfig('openHydra', settings.openHydra);
    this.patchSimpleConfig('jupyterHub', settings.jupyterHub);
    this.patchSimpleConfig('mqtt', settings.mqtt);
    this.patchSimpleConfig('prometheus', settings.prometheus);
    this.patchSimpleConfig('celery', settings.celery);
    this.patchSimpleConfig('objectStorage', settings.objectStorage);

    // 处理数据库连接 FormArray
    if (settings.databases && Array.isArray(settings.databases) && settings.databases.length > 0) {
      this.updateFormArray('databases', settings.databases);
    }

    // 处理 AI 服务 FormArray
    if (
      settings.aiServices &&
      Array.isArray(settings.aiServices) &&
      settings.aiServices.length > 0
    ) {
      this.updateFormArray('aiServices', settings.aiServices);
    }
  }

  /**
   * 填充简单配置项
   * @param key 配置项键名
   * @param value 配置值
   */
  private patchSimpleConfig(key: string, value: unknown): void {
    if (value && typeof value === 'object') {
      this.settingsForm.patchValue({ [key]: value });
    }
  }

  /**
   * 更新 FormArray 数据
   * @param key FormArray 的键名
   * @param items 要更新的数据项数组
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private updateFormArray(key: string, items: any[]): void {
    const formArray = this.settingsForm.get(key) as FormArray;
    formArray.clear(); // 清空现有项
    items.forEach((item) => {
      formArray.push(this.fb.group(item)); // 重建新项
    });
  }

  /**
   * 保存设置
   */
  saveSettings(): void {
    if (this.settingsForm.invalid) {
      this.snackBar.open('请填写必填项', '关闭', { duration: 3000 });
      this.settingsForm.markAllAsTouched(); // 标记所有字段为已触碰，显示验证错误
      return;
    }

    this.saving = true;
    const formValue = this.settingsForm.getRawValue() as GlobalApiSettings;

    // 过滤空值，只保存有数据的配置项
    const settings: GlobalApiSettings = this.filterEmptyConfigs(formValue);

    this.settingsService.saveGlobalSettings(settings).subscribe({
      next: (response) => {
        if (response.success) {
          this.snackBar.open('设置已保存', '关闭', { duration: 3000 });
          this.loadSettings(); // 重新加载最新配置
        } else {
          this.snackBar.open(response.error ?? '保存失败', '关闭', { duration: 3000 });
        }
        this.saving = false;
      },
      error: (error) => {
        console.error('保存设置失败:', error);
        this.snackBar.open('保存失败，请稍后重试', '关闭', { duration: 3000 });
        this.saving = false;
      },
    });
  }

  /**
   * 过滤空配置项
   * @param formValue 表单原始值
   * @returns 过滤后的配置对象
   */
  private filterEmptyConfigs(formValue: GlobalApiSettings): GlobalApiSettings {
    const settings: Partial<GlobalApiSettings> = {};
    for (const [key, value] of Object.entries(formValue) as Array<[string, unknown]>) {
      if (
        value &&
        typeof value === 'object' &&
        !Array.isArray(value) &&
        Object.keys(value).length > 0
      ) {
        (settings as Record<string, unknown>)[key] = value;
      }
    }
    return settings as GlobalApiSettings;
  }

  /**
   * 测试连接
   */
  testConnection(serviceType: string): void {
    const formGroup = this.settingsForm.get(serviceType);
    if (!formGroup) {
      this.snackBar.open('请先配置服务信息', '关闭', { duration: 3000 });
      return;
    }

    const config = formGroup.getRawValue() as
      | OpenHydraConfig
      | JupyterHubConfig
      | DatabaseConnectionConfig
      | MqttConfig;

    if (!config) {
      this.snackBar.open('请先配置服务信息', '关闭', { duration: 3000 });
      return;
    }

    this.snackBar.open(`正在测试 ${serviceType} 连接...`, '关闭', { duration: 2000 });

    this.settingsService.testApiConnection(serviceType, config).subscribe({
      next: (result) => {
        const message = result.message ?? (result.success ? '连接成功' : '连接失败');
        const duration = result.success ? 3000 : 5000;
        this.snackBar.open(message, '关闭', { duration });

        if (result.responseTime) {
          this.snackBar.open(`响应时间:${result.responseTime}ms`, '关闭', { duration: 3000 });
        }
      },
      error: (error) => {
        console.error('测试连接失败:', error);
        this.snackBar.open('测试连接失败，请检查网络或服务状态', '关闭', { duration: 5000 });
      },
    });
  }

  /**
   * 添加 AI 服务
   */
  addAiService(): void {
    const newService: AiServiceConfig = {
      serviceName: `AI Service ${Date.now()}`,
      endpoint: '',
      apiKey: '',
      model: '',
      maxTokens: 2048,
      temperature: 0.7,
      enabled: false,
    };

    const aiServicesArray = this.settingsForm.get('aiServices') as FormArray;
    aiServicesArray.push(this.fb.group(newService));

    this.snackBar.open('已添加新的 AI 服务配置', '关闭', { duration: 3000 });
  }

  /**
   * 移除 AI 服务
   */
  removeAiService(index: number): void {
    const aiServicesArray = this.settingsForm.get('aiServices') as FormArray;
    aiServicesArray.removeAt(index);
    this.snackBar.open('已移除 AI 服务配置', '关闭', { duration: 3000 });
  }

  /**
   * 添加数据库连接
   */
  addDatabaseConnection(): void {
    const newConnection: DatabaseConnectionConfig = {
      name: `Database ${Date.now()}`,
      host: 'localhost',
      port: 5432,
      database: '',
      username: '',
      password: '',
      ssl: false,
      poolSize: 10,
      enabled: false,
    };

    const databasesArray = this.settingsForm.get('databases') as FormArray;
    databasesArray.push(this.fb.group(newConnection));

    this.snackBar.open('已添加新的数据库连接', '关闭', { duration: 3000 });
  }

  /**
   * 移除数据库连接
   */
  removeDatabaseConnection(index: number): void {
    const databasesArray = this.settingsForm.get('databases') as FormArray;
    databasesArray.removeAt(index);
    this.snackBar.open('已移除数据库连接', '关闭', { duration: 3000 });
  }

  /**
   * 测试数据库连接
   */
  testDatabaseConnection(index: number): void {
    const control = this.databasesControls[index];
    if (!control) {
      this.snackBar.open('请先填写数据库配置', '关闭', { duration: 3000 });
      return;
    }

    const dbConfig = control.value as DatabaseConnectionConfig;
    const dbName = dbConfig?.name ?? '未命名数据库';
    this.snackBar.open(`正在测试连接：${dbName}...`, '关闭', { duration: 2000 });

    // TODO: 调用后端 API 测试数据库连接
    // 这里模拟测试过程
    setTimeout(() => {
      const success = Math.random() > 0.3; // 70% 成功率模拟
      if (success) {
        const responseTime = Math.floor(Math.random() * 100);
        this.snackBar.open(`✅ 连接成功！响应时间：${responseTime}ms`, '关闭', {
          duration: 3000,
        });
      } else {
        this.snackBar.open('❌ 连接失败，请检查主机地址、端口、用户名和密码', '关闭', {
          duration: 5000,
        });
      }
    }, 1500);
  }

  /**
   * 测试 AI 服务连接
   */
  testAiService(index: number): void {
    const control = this.aiServicesControls[index];
    if (!control) {
      this.snackBar.open('请先填写 AI 服务配置', '关闭', { duration: 3000 });
      return;
    }

    const serviceConfig = control.value as AiServiceConfig;
    const serviceName = serviceConfig?.serviceName ?? '未命名 AI 服务';
    const endpoint = serviceConfig?.endpoint ?? '';
    this.snackBar.open(
      `正在测试连接：${serviceName} (${this.getAiProvider(endpoint)})...`,
      '关闭',
      { duration: 2000 }
    );

    // TODO: 调用后端 API 测试 AI 服务连接
    // 这里模拟测试过程
    setTimeout(() => {
      const success = Math.random() > 0.25; // 75% 成功率模拟
      if (success) {
        const responseTime = Math.floor(Math.random() * 200) + 50;
        this.snackBar.open(`✅ 连接成功！模型可用，响应时间：${responseTime}ms`, '关闭', {
          duration: 3000,
        });
      } else {
        this.snackBar.open('❌ 连接失败，请检查 API 端点和密钥是否正确', '关闭', {
          duration: 5000,
        });
      }
    }, 2000);
  }

  /**
   * 获取 OpenHydra 配置
   */
  get openHydraConfig(): FormGroup {
    return this.settingsForm.get('openHydra') as FormGroup;
  }

  /**
   * 获取 JupyterHub 配置
   */
  get jupyterHubConfig(): FormGroup {
    return this.settingsForm.get('jupyterHub') as FormGroup;
  }

  /**
   * 获取 MQTT 配置
   */
  get mqttConfig(): FormGroup {
    return this.settingsForm.get('mqtt') as FormGroup;
  }

  /**
   * 获取对象存储配置
   */
  get objectStorageConfig(): FormGroup {
    return this.settingsForm.get('objectStorage') as FormGroup;
  }
}
