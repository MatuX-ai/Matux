import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

/**
 * 创意想法接口
 */
export interface CreativityIdea {
  id?: number;
  title: string;
  description: string;
  category?: string;
  tags?: string[];
  userId?: number;
  createdAt?: string;
  updatedAt?: string;
  score?: number;
  status?: string;
}

/**
 * Prompt 模板接口
 */
export interface PromptTemplate {
  id?: number;
  name: string;
  content: string;
  category?: string;
  tags?: string[];
  usageCount?: number;
  isPopular?: boolean;
}

/**
 * 创意生成请求接口
 */
export interface GenerateIdeaRequest {
  topic?: string;
  category?: string;
  keywords?: string[];
  templateId?: number;
}

/**
 * 创意评分请求接口
 */
export interface ScoreIdeaRequest {
  ideaId?: number;
  ideaText: string;
  criteria?: string[];
}

/**
 * 图像生成请求接口
 */
export interface GenerateImageRequest {
  prompt: string;
  style?: string;
  size?: string;
  negativePrompt?: string;
}

/**
 * 图像生成元数据接口
 */
export interface ImageMetadata {
  width?: number;
  height?: number;
  format?: string;
  seed?: number;
  steps?: number;
  guidanceScale?: number;
}

/**
 * 商业评估请求接口
 */
export interface BusinessEvaluationRequest {
  ideaText: string;
  marketSize?: string;
  targetAudience?: string;
  businessModel?: string;
}

/**
 * 统计数据接口
 */
export interface CreativityStatistics {
  totalIdeas: number;
  averageScore: number;
  topCategories: Array<{ name: string; count: number }>;
  recentActivity: number;
}

/**
 * 用户仪表板数据接口
 */
export interface UserDashboard {
  totalIdeas: number;
  pendingReview: number;
  averageScore: number;
  recentIdeas: CreativityIdea[];
  statistics: CreativityStatistics;
}

@Injectable({
  providedIn: 'root',
})
export class CreativityService {
  private apiUrl = `${environment.apiUrl}/api/v1/creativity`;

  constructor(private http: HttpClient) {}

  // 创意想法相关 API
  generateIdea(request: GenerateIdeaRequest): Observable<CreativityIdea> {
    return this.http.post<CreativityIdea>(`${this.apiUrl}/generate-idea`, request);
  }

  getUserIdeas(params?: HttpParams): Observable<CreativityIdea[]> {
    return this.http.get<CreativityIdea[]>(`${this.apiUrl}/my-ideas`, { params });
  }

  getIdeaById(id: number): Observable<CreativityIdea> {
    return this.http.get<CreativityIdea>(`${this.apiUrl}/ideas/${id}`);
  }

  createIdea(ideaData: CreativityIdea): Observable<CreativityIdea> {
    return this.http.post<CreativityIdea>(`${this.apiUrl}/ideas`, ideaData);
  }

  updateIdea(id: number, ideaData: CreativityIdea): Observable<CreativityIdea> {
    return this.http.put<CreativityIdea>(`${this.apiUrl}/ideas/${id}`, ideaData);
  }

  deleteIdea(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/ideas/${id}`);
  }

  // Prompt 模板相关 API
  getTemplates(params?: HttpParams): Observable<PromptTemplate[]> {
    return this.http.get<PromptTemplate[]>(`${this.apiUrl}/templates`, { params });
  }

  getTemplateById(id: number): Observable<PromptTemplate> {
    return this.http.get<PromptTemplate>(`${this.apiUrl}/templates/${id}`);
  }

  searchTemplates(query: string): Observable<PromptTemplate[]> {
    return this.http.get<PromptTemplate[]>(`${this.apiUrl}/templates/search/${query}`);
  }

  getPopularTemplates(): Observable<PromptTemplate[]> {
    return this.http.get<PromptTemplate[]>(`${this.apiUrl}/templates/popular`);
  }

  // 创意评分相关 API
  scoreIdea(request: ScoreIdeaRequest): Observable<{ score: number; feedback: string }> {
    return this.http.post<{ score: number; feedback: string }>(
      `${this.apiUrl}/score-idea`,
      request
    );
  }

  // 图像生成相关 API
  generateImage(
    request: GenerateImageRequest
  ): Observable<{ imageUrl: string; metadata: ImageMetadata }> {
    return this.http.post<{ imageUrl: string; metadata: ImageMetadata }>(
      `${this.apiUrl}/generate-image`,
      request
    );
  }

  // 商业价值评估 API
  evaluateBusiness(
    request: BusinessEvaluationRequest
  ): Observable<{ score: number; analysis: string; suggestions: string[] }> {
    return this.http.post<{ score: number; analysis: string; suggestions: string[] }>(
      `${this.apiUrl}/evaluate-business`,
      request
    );
  }

  // 统计数据 API
  getStatistics(): Observable<CreativityStatistics> {
    return this.http.get<CreativityStatistics>(`${this.apiUrl}/statistics`);
  }

  // 批量操作
  batchScoreIdeas(ideas: string[]): Observable<Array<{ idea: string; score: number }>> {
    return this.http.post<Array<{ idea: string; score: number }>>(`${this.apiUrl}/batch-score`, {
      ideas,
    });
  }

  // 获取用户仪表板数据
  getUserDashboard(): Observable<UserDashboard> {
    return this.http.get<UserDashboard>(`${this.apiUrl}/dashboard`);
  }
}
