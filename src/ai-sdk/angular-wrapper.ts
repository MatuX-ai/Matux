/**
 * Angular 服务包装器
 * 用于在 Angular 应用中更容易地使用 AI 服务
 *
 * @deprecated 请直接使用 AIServiceClient 或通过 Angular DI 注入 AIServiceClient。
 * 此类仅保留以保持 ai-code-generator 等现有组件的向后兼容。
 */

// 注意：此文件需要 Angular 和 RxJS 依赖
// 如果不在 Angular 环境中，请使用 ai-client.ts 中的 AIServiceClient

import { AIServiceClient } from './ai-client';
import type {
  AIRequestRecord,
  AIServiceConfig,
  AvailableModelsResponse,
  CodeGenerationRequest,
  CodeGenerationResponse,
  UsageStats,
} from './types';

// 模拟 Angular Injectable 装饰器（如果在非 Angular 环境中）
const Injectable = (_options: any) => (target: any) => target;

@Injectable({
  providedIn: 'root',
})
/**
 * @deprecated 请直接使用 AIServiceClient。此类仅用于向后兼容。
 */
export class AngularAIService {
  private aiClient!: AIServiceClient;

  constructor() {
    // 默认配置 - 实际使用时应该从环境变量或配置服务获取
    const defaultConfig: AIServiceConfig = {
      baseUrl: 'http://localhost:8000',
      timeout: 30000,
    };

    this.aiClient = new AIServiceClient(defaultConfig);
  }

  /**
   * 设置访问令牌
   */
  setAccessToken(token: string): void {
    this.aiClient.setAccessToken(token);
  }

  /**
   * 清除访问令牌
   */
  clearAccessToken(): void {
    this.aiClient.clearAccessToken();
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<AIServiceConfig>): void {
    this.aiClient.updateConfig(config);
  }

  /**
   * 生成代码
   */
  generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResponse> {
    return this.aiClient.generateCode(request);
  }

  /**
   * 获取可用模型列表
   */
  getAvailableModels(): Promise<AvailableModelsResponse> {
    return this.aiClient.getAvailableModels();
  }

  /**
   * 获取使用统计
   */
  getUsageStats(): Promise<UsageStats> {
    return this.aiClient.getUsageStats();
  }

  /**
   * 获取最近的请求记录
   */
  getRecentRequests(limit: number = 10): Promise<AIRequestRecord[]> {
    return this.aiClient.getRecentRequests(limit);
  }

  /**
   * 使用预设模板生成代码
   */
  generateWithTemplate(
    template: keyof typeof AIServiceClient.templates,
    ...args: any[]
  ): Promise<CodeGenerationResponse> {
    return this.aiClient.generateWithTemplate(template, ...args);
  }

  /**
   * 批量生成代码
   */
  generateCodeBatch(requests: CodeGenerationRequest[]): Promise<CodeGenerationResponse[]> {
    return this.aiClient.generateCodeBatch(requests);
  }

  /**
   * 带重试的代码生成
   */
  generateCodeWithRetry(
    request: CodeGenerationRequest,
    maxRetries: number = 3,
    retryDelay: number = 1000
  ): Promise<CodeGenerationResponse> {
    return this.aiClient.generateCodeWithRetry(request, maxRetries, retryDelay);
  }

  /**
   * 预设模板的快捷方法
   */
  generateReactComponent(
    componentName: string,
    propsInterface?: string
  ): Promise<CodeGenerationResponse> {
    return this.generateWithTemplate('reactComponent', componentName, propsInterface);
  }

  generateApiService(serviceName: string, endpoints: string[]): Promise<CodeGenerationResponse> {
    return this.generateWithTemplate('apiService', serviceName, endpoints);
  }

  generateDataModel(modelName: string, fields: string[]): Promise<CodeGenerationResponse> {
    return this.generateWithTemplate('dataModel', modelName, fields);
  }

  generateUtilityFunction(functionName: string, purpose: string): Promise<CodeGenerationResponse> {
    return this.generateWithTemplate('utilityFunction', functionName, purpose);
  }

  generateUnitTest(functionName: string, testCases: string[]): Promise<CodeGenerationResponse> {
    return this.generateWithTemplate('unitTest', functionName, testCases);
  }
}
