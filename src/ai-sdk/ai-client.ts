/**
 * AI服务客户端主类
 */

import { HttpClient, HttpErrorImpl } from './http-client';
import type {
  AIRequestRecord,
  AIServiceConfig,
  AvailableModelsResponse,
  CodeGenerationRequest,
  CodeGenerationResponse,
  CourseRecommendationsResponse,
  FeedbackType,
  ModelRefreshResponse,
  RecommendationFeedbackResponse,
  RecommendationStats,
  UsageStats,
  UserLearningProfile,
} from './types';
import { ModelProvider } from './types';

/**
 * AI服务客户端类
 */
export class AIServiceClient {
  private httpClient: HttpClient;
  private config: AIServiceConfig & { timeout: number; headers: Record<string, string> };

  constructor(config: AIServiceConfig) {
    this.config = {
      timeout: 30000,
      headers: {},
      ...config,
    } as AIServiceConfig & { timeout: number; headers: Record<string, string> };

    this.httpClient = new HttpClient(this.config.baseUrl, this.config.timeout, this.config.headers);

    // 如果提供了访问令牌，设置到HTTP客户端
    if (this.config.accessToken) {
      this.httpClient.setAccessToken(this.config.accessToken);
    }
  }

  /**
   * 设置访问令牌
   */
  setAccessToken(token: string): void {
    this.config.accessToken = token;
    this.httpClient.setAccessToken(token);
  }

  /**
   * 清除访问令牌
   */
  clearAccessToken(): void {
    this.config.accessToken = undefined;
    this.httpClient.clearAccessToken();
  }

  /**
   * 更新配置
   */
  updateConfig(newConfig: Partial<AIServiceConfig>): void {
    this.config = { ...this.config, ...newConfig };

    if (newConfig.baseUrl) {
      this.httpClient.setBaseUrl(newConfig.baseUrl);
    }

    if (newConfig.timeout !== undefined) {
      // 注意：HttpClient的timeout是每个请求的，这里只是更新默认值
    }

    if (newConfig.headers) {
      // 更新默认头需要重新创建 HttpClient
      this.httpClient = new HttpClient(this.config.baseUrl, this.config.timeout, {
        ...this.config.headers,
        ...newConfig.headers,
      });

      if (this.config.accessToken) {
        this.httpClient.setAccessToken(this.config.accessToken);
      }
    }
  }

  /**
   * 生成代码
   */
  async generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResponse> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for AI service');
    }

    try {
      const response = await this.httpClient.post<CodeGenerationResponse>(
        '/api/v1/generate-code',
        {
          prompt: request.prompt,
          provider: request.provider ?? ModelProvider.OPENAI,
          model: request.model,
          language: request.language,
          temperature: request.temperature,
          max_tokens: request.maxTokens,
          system_prompt: request.systemPrompt,
        },
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to generate code: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 获取可用模型列表
   */
  async getAvailableModels(): Promise<AvailableModelsResponse> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for AI service');
    }

    try {
      const response = await this.httpClient.get<AvailableModelsResponse>('/api/v1/models', {
        accessToken: this.config.accessToken,
      });

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to get available models: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 获取使用统计
   */
  async getUsageStats(): Promise<UsageStats> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for AI service');
    }

    try {
      const response = await this.httpClient.get<UsageStats>('/api/v1/usage-stats', {
        accessToken: this.config.accessToken,
      });

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to get usage stats: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 获取最近的请求记录
   */
  async getRecentRequests(limit: number = 10): Promise<AIRequestRecord[]> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for AI service');
    }

    try {
      const response = await this.httpClient.get<AIRequestRecord[]>(
        `/api/v1/recent-requests?limit=${limit}`,
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to get recent requests: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 预设的代码生成模板
   */
  static templates = {
    /**
     * 生成React组件
     */
    reactComponent: (componentName: string, propsInterface?: string): string => {
      return `创建一个名为${componentName}的React组件${propsInterface ? `，接受以下props: ${propsInterface}` : ''}`;
    },

    /**
     * 生成API服务类
     */
    apiService: (serviceName: string, endpoints: string[]): string => {
      return `创建一个名为${serviceName}的API服务类，包含以下端点: ${endpoints.join(', ')}`;
    },

    /**
     * 生成数据模型
     */
    dataModel: (modelName: string, fields: string[]): string => {
      return `创建一个名为${modelName}的数据模型，包含以下字段: ${fields.join(', ')}`;
    },

    /**
     * 生成工具函数
     */
    utilityFunction: (functionName: string, purpose: string): string => {
      return `创建一个名为${functionName}的工具函数，用于${purpose}`;
    },

    /**
     * 生成单元测试
     */
    unitTest: (functionName: string, testCases: string[]): string => {
      return `为${functionName}函数编写单元测试，测试以下场景：${testCases.join(', ')}`;
    },
  };

  /**
   * 快捷方法：使用预设模板生成代码
   */
  async generateWithTemplate(
    template: keyof typeof AIServiceClient.templates,
    ...args: unknown[]
  ): Promise<CodeGenerationResponse> {
    const templateFn = AIServiceClient.templates[template] as (...args: unknown[]) => string;
    const prompt = templateFn(...args);
    return this.generateCode({ prompt });
  }

  /**
   * 批量生成代码
   */
  async generateCodeBatch(requests: CodeGenerationRequest[]): Promise<CodeGenerationResponse[]> {
    const promises = requests.map((request) => this.generateCode(request));
    return Promise.all(promises);
  }

  /**
   * 带重试的代码生成
   */
  async generateCodeWithRetry(
    request: CodeGenerationRequest,
    maxRetries: number = 3,
    retryDelay: number = 1000
  ): Promise<CodeGenerationResponse> {
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.generateCode(request);
      } catch (error) {
        lastError = error as Error;

        if (attempt < maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, retryDelay * attempt));
        }
      }
    }

    throw lastError ?? new Error('Failed to generate code after retries');
  }

  // ====================
  // 推荐系统相关方法
  // ====================

  /**
   * 获取课程推荐
   */
  async getCourseRecommendations(
    numRecommendations: number = 5
  ): Promise<CourseRecommendationsResponse> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.get<CourseRecommendationsResponse>(
        `/api/v1/recommendations/courses?num_recommendations=${numRecommendations}`,
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to get course recommendations: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 提交推荐反馈
   */
  async submitRecommendationFeedback(
    courseId: string,
    feedbackType: FeedbackType,
    context?: Record<string, unknown>
  ): Promise<RecommendationFeedbackResponse> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.post<RecommendationFeedbackResponse>(
        '/api/v1/recommendations/feedback',
        {
          course_id: courseId,
          feedback_type: feedbackType,
          context,
        },
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to submit recommendation feedback: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 记录学习活动
   */
  async recordLearningActivity(
    courseId: string,
    lessonId: string,
    progress: number = 0,
    timeSpent: number = 0,
    completionStatus: 'in_progress' | 'completed' | 'skipped' = 'in_progress',
    difficultyRating?: number,
    interestRating?: number
  ): Promise<{ message: string; recordId: number; updatedProfile: boolean }> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.post<{
        message: string;
        recordId: number;
        updatedProfile: boolean;
      }>(
        '/api/v1/recommendations/learning-record',
        {
          course_id: courseId,
          lesson_id: lessonId,
          progress,
          time_spent: timeSpent,
          completion_status: completionStatus,
          difficulty_rating: difficultyRating,
          interest_rating: interestRating,
        },
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to record learning activity: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 获取用户学习画像
   */
  async getUserLearningProfile(): Promise<UserLearningProfile> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.get<UserLearningProfile>(
        '/api/v1/recommendations/user-profile',
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to get user learning profile: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 更新学习偏好
   */
  async updateLearningPreferences(
    preferences: Record<string, unknown>
  ): Promise<UserLearningProfile> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.put<UserLearningProfile>(
        '/api/v1/recommendations/user-profile/preferences',
        preferences,
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to update learning preferences: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 获取推荐统计信息
   */
  async getRecommendationStats(): Promise<RecommendationStats> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.get<RecommendationStats>(
        '/api/v1/recommendations/stats',
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to get recommendation stats: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * 刷新推荐模型（需要管理员权限）
   */
  async refreshRecommendationModel(): Promise<ModelRefreshResponse> {
    if (!this.config.accessToken) {
      throw new Error('Access token is required for recommendation service');
    }

    try {
      const response = await this.httpClient.post<ModelRefreshResponse>(
        '/api/v1/recommendations/refresh-model',
        {},
        {
          accessToken: this.config.accessToken,
        }
      );

      return response.data;
    } catch (error) {
      if (error instanceof HttpErrorImpl) {
        throw error;
      }
      throw new Error(
        `Failed to refresh recommendation model: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }
}

/**
 * 创建AI服务客户端实例的工厂函数
 */
export function createAIClient(config: AIServiceConfig): AIServiceClient {
  return new AIServiceClient(config);
}

/**
 * 默认导出
 */
export default AIServiceClient;
