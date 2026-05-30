/**
 * AI创意引擎客户端
 * 提供创意生成、评分、图像生成等完整功能的TypeScript SDK
 */

import * as CreativityTypes from './creativity-types';
import { HttpClient } from './http-client';
import { AIServiceConfig } from './types';

export class CreativityClient {
  private httpClient: HttpClient;
  private config: AIServiceConfig;

  constructor(config: AIServiceConfig) {
    this.config = config;
    this.httpClient = new HttpClient(config.baseUrl, config.timeout, config.headers);
  }

  /**
   * 生成创意想法
   */
  async generateIdea(
    request: CreativityTypes.IdeaGenerationRequest
  ): Promise<CreativityTypes.IdeaGenerationResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<CreativityTypes.IdeaGenerationResponse>(
      '/creativity/generate-idea',
      request,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 获取用户的创意想法列表
   */
  async getUserIdeas(_params?: {
    category?: string;
    is_public?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<CreativityTypes.CreativeIdeaResponse[]> {
    this._ensureAccessToken();
    const response = await this.httpClient.get<CreativityTypes.CreativeIdeaResponse[]>(
      '/creativity/my-ideas',
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 获取指定创意想法详情
   */
  async getIdeaById(ideaId: number): Promise<CreativityTypes.CreativeIdeaResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.get<CreativityTypes.CreativeIdeaResponse>(
      `/creativity/ideas/${ideaId}`,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 创建新的创意想法
   */
  async createIdea(
    ideaData: CreativityTypes.CreativeIdeaCreate
  ): Promise<{ message: string; idea_id: number }> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<{ message: string; idea_id: number }>(
      '/creativity/ideas',
      ideaData,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 更新创意想法
   */
  async updateIdea(
    ideaId: number,
    ideaData: CreativityTypes.CreativeIdeaUpdate
  ): Promise<CreativityTypes.CreativeIdeaResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.put<CreativityTypes.CreativeIdeaResponse>(
      `/creativity/ideas/${ideaId}`,
      ideaData,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 删除创意想法
   */
  async deleteIdea(ideaId: number): Promise<{ message: string }> {
    this._ensureAccessToken();
    const response = await this.httpClient.delete<{ message: string }>(
      `/creativity/ideas/${ideaId}`,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 获取Prompt模板列表
   */
  async getTemplates(_params?: {
    category?: string;
    is_public?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<CreativityTypes.PromptTemplateResponse[]> {
    const response =
      await this.httpClient.get<CreativityTypes.PromptTemplateResponse[]>('/creativity/templates');
    return response.data;
  }

  /**
   * 获取指定Prompt模板详情
   */
  async getTemplateById(templateId: number): Promise<CreativityTypes.PromptTemplateResponse> {
    const response = await this.httpClient.get<CreativityTypes.PromptTemplateResponse>(
      `/creativity/templates/${templateId}`
    );
    return response.data;
  }

  /**
   * 搜索Prompt模板
   */
  async searchTemplates(
    query: string,
    limit: number = 20
  ): Promise<CreativityTypes.PromptTemplateResponse[]> {
    const response = await this.httpClient.get<CreativityTypes.PromptTemplateResponse[]>(
      `/creativity/templates/search/${encodeURIComponent(query)}?limit=${limit}`
    );
    return response.data;
  }

  /**
   * 获取热门模板
   */
  async getPopularTemplates(limit: number = 10): Promise<CreativityTypes.PromptTemplateResponse[]> {
    const response = await this.httpClient.get<CreativityTypes.PromptTemplateResponse[]>(
      `/creativity/templates/popular?limit=${limit}`
    );
    return response.data;
  }

  /**
   * 对创意想法进行评分
   */
  async scoreIdea(
    request: CreativityTypes.IdeaScoreRequest
  ): Promise<CreativityTypes.IdeaScoreResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<CreativityTypes.IdeaScoreResponse>(
      '/creativity/score-idea',
      request,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 生成创意图像
   */
  async generateImage(
    request: CreativityTypes.ImageGenerationRequest
  ): Promise<CreativityTypes.ImageGenerationResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<CreativityTypes.ImageGenerationResponse>(
      '/creativity/generate-image',
      request,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 评估创意的商业价值
   */
  async evaluateBusiness(
    request: CreativityTypes.BusinessEvaluationRequest
  ): Promise<CreativityTypes.BusinessEvaluationResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<CreativityTypes.BusinessEvaluationResponse>(
      '/creativity/evaluate-business',
      request,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 获取创意统计数据
   */
  async getStatistics(): Promise<CreativityTypes.CreativityStatisticsResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.get<CreativityTypes.CreativityStatisticsResponse>(
      '/creativity/statistics',
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 批量评分创意想法
   */
  async batchScoreIdeas(
    request: CreativityTypes.BatchScoreRequest
  ): Promise<CreativityTypes.BatchScoreResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<CreativityTypes.BatchScoreResponse>(
      '/creativity/batch-score',
      request,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 综合创意分析（评分+商业评估）
   */
  async comprehensiveAnalysis(
    request: CreativityTypes.ComprehensiveAnalysisRequest
  ): Promise<CreativityTypes.ComprehensiveAnalysisResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.post<CreativityTypes.ComprehensiveAnalysisResponse>(
      '/creativity/comprehensive-analysis',
      request,
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 获取用户创意仪表板数据
   */
  async getUserDashboard(): Promise<CreativityTypes.UserDashboardResponse> {
    this._ensureAccessToken();
    const response = await this.httpClient.get<CreativityTypes.UserDashboardResponse>(
      '/creativity/dashboard',
      { accessToken: this.config.accessToken }
    );
    return response.data;
  }

  /**
   * 生成并保存创意想法（便捷方法）
   */
  async generateAndSaveIdea(request: CreativityTypes.IdeaGenerationRequest): Promise<{
    idea: CreativityTypes.CreativeIdeaResponse;
    processing_time: number;
  }> {
    this._ensureAccessToken();

    // 先生成创意
    const generationResult = await this.generateIdea(request);

    // 保存创意
    const saveResult = await this.createIdea({
      title: generationResult.title,
      description: '',
      category: generationResult.category as CreativityTypes.IdeaCategory,
      is_public: false,
    });

    // 获取保存后的完整创意信息
    const savedIdea = await this.getIdeaById(saveResult.idea_id);

    return {
      idea: savedIdea,
      processing_time: generationResult.processing_time,
    };
  }

  /**
   * 生成创意想法并配套图像（便捷方法）
   */
  async generateIdeaWithImages(
    ideaRequest: CreativityTypes.IdeaGenerationRequest,
    imageRequest: CreativityTypes.ImageGenerationRequest
  ): Promise<{
    idea: CreativityTypes.CreativeIdeaResponse;
    images: CreativityTypes.ImageGenerationResponse;
    total_processing_time: number;
    total_cost: number;
  }> {
    this._ensureAccessToken();

    // 并发执行创意生成和图像生成
    const [ideaResult, imageResult] = await Promise.all([
      this.generateAndSaveIdea(ideaRequest),
      this.generateImage(imageRequest),
    ]);

    // 更新创意想法，添加图像信息
    const updatedIdea = await this.updateIdea(ideaResult.idea.id, {
      title: ideaResult.idea.title,
      description: ideaResult.idea.description,
      tags: ideaResult.idea.tags,
      is_public: ideaResult.idea.is_public,
    });

    return {
      idea: updatedIdea,
      images: imageResult,
      total_processing_time: ideaResult.processing_time + imageResult.processing_time,
      total_cost: imageResult.total_cost,
    };
  }

  /**
   * 导出创意想法为JSON格式
   */
  exportIdeaToJson(idea: CreativityTypes.CreativeIdeaResponse): string {
    const exportData: Record<string, unknown> = {
      title: idea.title,
      content: (idea.ai_generated_content as string) || idea.description,
      category: idea.category,
      scores: idea.scores as unknown,
      images: idea.images,
      tags: idea.tags,
      created_at: idea.created_at,
      exported_at: new Date().toISOString(),
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * 导出创意想法为文本格式
   */
  exportIdeaToText(idea: CreativityTypes.CreativeIdeaResponse): string {
    let text = `# ${idea.title}\n\n`;

    if (idea.category) {
      text += `**分类:** ${idea.category}\n\n`;
    }

    if (idea.description) {
      text += `**描述:**\n${idea.description}\n\n`;
    }

    if (idea.ai_generated_content) {
      text += `**创意内容:**\n${typeof idea.ai_generated_content === 'string' ? idea.ai_generated_content : JSON.stringify(idea.ai_generated_content, null, 2)}\n\n`;
    }

    if (idea.scores) {
      text += `**评分结果:**\n${JSON.stringify(idea.scores, null, 2)}\n\n`;
    }

    if (idea.tags && idea.tags.length > 0) {
      text += `**标签:** ${idea.tags.join(', ')}\n\n`;
    }

    text += `**创建时间:** ${new Date(idea.created_at).toLocaleString()}\n`;
    text += `**导出时间:** ${new Date().toLocaleString()}`;

    return text;
  }

  /**
   * 获取评分的颜色标识
   */
  getScoreColor(score: number): 'success' | 'warning' | 'error' {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    return 'error';
  }

  /**
   * 获取评分的文字描述
   */
  getScoreDescription(score: number): string {
    if (score >= 8) return '优秀';
    if (score >= 6) return '良好';
    if (score >= 4) return '一般';
    return '需要改进';
  }

  /**
   * 验证创意想法数据
   */
  validateIdea(idea: CreativityTypes.CreativeIdeaCreate): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!idea.title || idea.title.trim().length === 0) {
      errors.push('标题不能为空');
    } else if (idea.title.length < 3) {
      errors.push('标题至少需要3个字符');
    } else if (idea.title.length > 255) {
      errors.push('标题不能超过255个字符');
    }

    if (idea.description && idea.description.length > 2000) {
      errors.push('描述不能超过2000个字符');
    }

    if (idea.tags) {
      if (idea.tags.length > 10) {
        errors.push('标签数量不能超过10个');
      }

      const invalidTags = idea.tags.filter((tag) => tag.length > 50);
      if (invalidTags.length > 0) {
        errors.push('单个标签不能超过50个字符');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  /**
   * 验证Prompt模板数据
   */
  validateTemplate(template: CreativityTypes.PromptTemplateCreate): {
    isValid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (!template.name || template.name.trim().length === 0) {
      errors.push('模板名称不能为空');
    } else if (template.name.length > 255) {
      errors.push('模板名称不能超过255个字符');
    }

    if (!template.template || template.template.trim().length === 0) {
      errors.push('模板内容不能为空');
    } else if (template.template.length < 10) {
      errors.push('模板内容至少需要10个字符');
    }

    if (template.description && template.description.length > 1000) {
      errors.push('模板描述不能超过1000个字符');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  private _ensureAccessToken(): void {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for creativity service operations');
    }
  }
}

/**
 * 创建创意客户端的便捷函数
 */
export function createCreativityClient(config: AIServiceConfig): CreativityClient {
  return new CreativityClient(config);
}

// 默认导出
export default CreativityClient;
