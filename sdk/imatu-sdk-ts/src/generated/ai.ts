// Auto-generated AI API Client

import { APIClient } from '../client';
import { BaseResponse, CodeGenerationRequest, CodeGenerationResponse, TextGenerationRequest, ImageGenerationRequest, AIModel } from '../types';

export class AIAPI {
  constructor(private client: APIClient) {}

  // AI代码生成
  async generateCode(request: CodeGenerationRequest): Promise<BaseResponse<CodeGenerationResponse>> {
    const response = await this.client.post<CodeGenerationResponse>('/api/v1/ai/generate-code', request);
    return response.data;
  }

  // AI文本生成
  async generateText(request: TextGenerationRequest): Promise<BaseResponse<any>> {
    const response = await this.client.post<any>('/api/v1/ai/generate-text', request);
    return response.data;
  }

  // AI图像生成
  async generateImage(request: ImageGenerationRequest): Promise<BaseResponse<any>> {
    const response = await this.client.post<any>('/api/v1/ai/generate-image', request);
    return response.data;
  }

  // 获取可用模型列表
  async getAvailableModels(): Promise<BaseResponse<AIModel[]>> {
    const response = await this.client.get<AIModel[]>('/api/v1/ai/models');
    return response.data;
  }

  // 获取AI使用统计
  async getUsageStats(): Promise<BaseResponse<any>> {
    const response = await this.client.get<any>('/api/v1/ai/usage');
    return response.data;
  }

  // 获取AI模型详情
  async getModelDetails(modelId: string): Promise<BaseResponse<AIModel>> {
    const response = await this.client.get<AIModel>(`/api/v1/ai/models/${modelId}`);
    return response.data;
  }
}

// 导出实例创建函数
export function createAIAPI(client: APIClient) {
  return new AIAPI(client);
}