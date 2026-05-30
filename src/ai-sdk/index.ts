/**
 * iMato AI Service SDK 入口文件
 *
 * 使用示例:
 *
 * // 基础使用
 * import { AIServiceClient, ModelProvider } from './ai-sdk';
 *
 * const client = new AIServiceClient({
 *   baseUrl: 'http://localhost:8000',
 *   accessToken: 'your-access-token'
 * });
 *
 * const response = await client.generateCode({
 *   prompt: '创建一个计算斐波那契数列的函数',
 *   provider: ModelProvider.OPENAI,
 *   language: ProgrammingLanguage.PYTHON
 * });
 *
 * console.log(response.code);
 */

// 核心客户端
export { AIServiceClient, createAIClient } from './ai-client';

// HTTP客户端工具
export { HttpClient, HttpErrorImpl, HttpMethod } from './http-client';

// 类型定义
export * from './types';

// Angular包装器（可选）
export { AngularAIService } from './angular-wrapper';

// 版本信息
export const VERSION = '1.0.0';

// 默认导出
export { AIServiceClient as default } from './ai-client';
