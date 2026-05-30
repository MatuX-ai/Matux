/**
 * AI创意引擎相关的类型定义
 */

// 创意分类枚举
export enum IdeaCategory {
  TECHNOLOGY = 'technology',
  BUSINESS = 'business',
  DESIGN = 'design',
  EDUCATION = 'education',
  HEALTHCARE = 'healthcare',
  ENTERTAINMENT = 'entertainment',
  ENVIRONMENT = 'environment',
  OTHER = 'other',
}

// 图像风格枚举
export enum ImageStyle {
  REALISTIC = 'realistic',
  ARTISTIC = 'artistic',
  CARTOON = 'cartoon',
  PHOTOGRAPHIC = 'photographic',
  DIGITAL_ART = 'digital_art',
  THREE_D_RENDER = '3d_render',
}

// 评分者类型枚举
export enum ScorerType {
  AI = 'ai',
  HUMAN = 'human',
  HYBRID = 'hybrid',
}

// 创意想法创建请求
export interface CreativeIdeaCreate {
  title: string;
  description?: string;
  category?: IdeaCategory;
  prompt_template_id?: number;
  tags?: string[];
  is_public?: boolean;
}

// 创意想法更新请求
export interface CreativeIdeaUpdate {
  title?: string;
  description?: string;
  category?: IdeaCategory;
  tags?: string[];
  is_public?: boolean;
}

// 创意想法响应
export interface CreativeIdeaResponse {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  category?: string;
  prompt_template_id?: number;
  ai_generated_content?: any;
  images?: any[];
  scores?: any;
  tags?: string[];
  is_public: boolean;
  view_count: number;
  like_count: number;
  created_at: string;
  updated_at: string;
}

// Prompt模板创建请求
export interface PromptTemplateCreate {
  name: string;
  category?: string;
  template: string;
  variables?: Record<string, any>;
  description?: string;
  is_public?: boolean;
}

// Prompt模板响应
export interface PromptTemplateResponse {
  id: number;
  name: string;
  category?: string;
  template: string;
  variables?: Record<string, any>;
  description?: string;
  usage_count: number;
  is_public: boolean;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

// 创意生成请求
export interface IdeaGenerationRequest {
  prompt_template_id?: number;
  custom_prompt?: string;
  category?: IdeaCategory;
  variables?: Record<string, any>;
  temperature?: number;
  max_tokens?: number;
}

// 创意生成响应
export interface IdeaGenerationResponse {
  idea_id: number;
  title: string;
  content: string;
  category?: string;
  processing_time: number;
  tokens_used: number;
}

// 图像生成请求
export interface ImageGenerationRequest {
  prompt: string;
  style?: ImageStyle;
  size?: string;
  quality?: string;
  n?: number;
}

// 图像生成响应
export interface ImageGenerationResponse {
  images: Array<{
    url: string;
    revised_prompt: string;
    style?: string;
  }>;
  processing_time: number;
  total_cost: number;
}

// 创意评分请求
export interface IdeaScoreRequest {
  idea_content: string;
  technical_requirements?: string;
  business_model?: string;
  market_context?: string;
  scoring_criteria?: Record<string, number>;
}

// 创意评分响应
export interface IdeaScoreResponse {
  total_score: number;
  creativity: number;
  feasibility: number;
  commercial_value: number;
  detailed_analysis: {
    analysis_text: string;
    strengths: string[];
    risks: string[];
    improvement_areas: string[];
  };
  recommendations: string[];
}

// 商业价值评估请求
export interface BusinessEvaluationRequest {
  idea_description: string;
  target_market: string;
  estimated_costs: Record<string, number>;
  revenue_projections: Record<string, number>;
  competition_analysis: string;
}

// 商业价值评估响应
export interface BusinessEvaluationResponse {
  cost_benefit_ratio: number;
  market_potential: number;
  risk_assessment: {
    overall_risk: string;
    market_risk: string;
    technical_risk: string;
    financial_risk: string;
    operational_risk: string;
    risk_factors: string[];
  };
  investment_recommendation: string;
  timeline_estimate: string;
  resource_requirements: string[];
}

// 统计数据响应
export interface CreativityStatisticsResponse {
  user_statistics: {
    total_ideas: number;
    public_ideas: number;
    average_score: number;
  };
  template_statistics: {
    total_templates: number;
    public_templates: number;
    private_templates: number;
    category_distribution: Record<string, number>;
    total_usages: number;
    average_usage_per_template: number;
  };
}

// 批量评分请求
export interface BatchScoreRequest {
  ideas: string[];
  scoring_criteria?: Record<string, number>;
}

// 批量评分响应
export interface BatchScoreResponse {
  results: Array<{
    index: number;
    success: boolean;
    total_score?: number;
    creativity?: number;
    feasibility?: number;
    commercial_value?: number;
    recommendations?: string[];
    error?: string;
  }>;
}

// 综合分析请求
export interface ComprehensiveAnalysisRequest {
  idea_content: string;
  business_context?: {
    target_market: string;
    estimated_costs: Record<string, number>;
    revenue_projections: Record<string, number>;
    competition_analysis: string;
  };
}

// 综合分析响应
export interface ComprehensiveAnalysisResponse {
  scoring: {
    total_score: number;
    creativity: number;
    feasibility: number;
    commercial_value: number;
    recommendations: string[];
  };
  business_evaluation?: BusinessEvaluationResponse;
  overall_assessment: {
    strengths: string[];
    weaknesses: string[];
    recommendations: string[];
    investment_outlook: string;
  };
}

// 用户仪表板数据
export interface UserDashboardResponse {
  statistics: {
    total_ideas: number;
    public_ideas: number;
    tech_ideas: number;
    business_ideas: number;
    average_score: number;
    total_views: number;
    total_likes: number;
  };
  recent_ideas: Array<{
    id: number;
    title: string;
    category: string;
    created_at: string;
    view_count: number;
    like_count: number;
  }>;
  template_usage: Array<{
    template_name: string;
    category: string;
    usage_count: number;
  }>;
}
