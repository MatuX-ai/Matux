/**
 * 创意想法相关类型定义
 */

/**
 * 创意想法类别枚举
 */
export enum IdeaCategory {
  TECHNOLOGY = 'technology',
  BUSINESS = 'business',
  DESIGN = 'design',
  EDUCATION = 'education',
  ENTERTAINMENT = 'entertainment',
  OTHER = 'other',
}

/**
 * 创意想法基础接口
 */
export interface CreativeIdeaBase {
  /** 标题 */
  title: string;
  /** 描述 */
  description?: string;
  /** 类别 */
  category?: IdeaCategory;
  /** 是否公开 */
  is_public?: boolean;
  /** 标签列表 */
  tags?: string[];
  /** AI生成的内容 */
  ai_generated_content?: string | Record<string, any>;
  /** 评分结果（JSON字符串） */
  scores?: string;
  /** 图像数据（JSON字符串） */
  images?: string;
  /** 创建时间 */
  created_at?: string;
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 创意想法完整接口
 */
export interface CreativeIdea extends CreativeIdeaBase {
  /** 创意ID */
  id: number;
  /** 用户ID */
  user_id: number;
  /** 点赞数 */
  likes_count?: number;
  /** 查看数 */
  views_count?: number;
  /** 状态 */
  status?: 'draft' | 'published' | 'archived';
}

/**
 * 创建创意想法请求接口
 */
export interface CreativeIdeaCreate extends CreativeIdeaBase {
  // 继承基础属性，无需额外字段
}

/**
 * 更新创意想法请求接口
 */
export interface CreativeIdeaUpdate extends Partial<CreativeIdeaBase> {
  // 允许部分更新
}

/**
 * 创意想法响应接口
 */
export interface CreativeIdeaResponse extends CreativeIdea {
  // 可以添加额外的响应字段
  author?: {
    id: number;
    username: string;
    avatar?: string;
  };
}

/**
 * 评分结果接口
 */
export interface IdeaScores {
  /** 创新性评分 (1-10) */
  innovation: number;
  /** 实用性评分 (1-10) */
  practicality: number;
  /** 商业价值评分 (1-10) */
  business_value: number;
  /** 技术可行性评分 (1-10) */
  technical_feasibility: number;
  /** 总体评分 (1-10) */
  overall_score: number;
  /** 详细评语 */
  detailed_feedback?: string;
  /** 详细分析（可选） */
  detailed_analysis?: {
    analysis_text: string;
    strengths: string[];
    weaknesses: string[];
  };
  /** 推荐建议列表（可选） */
  recommendations?: string[];
}

/**
 * 图像生成结果接口
 */
export interface GeneratedImage {
  /** 图像URL */
  url: string;
  /** 图像描述 */
  description?: string;
  /** 生成时间 */
  generated_at: string;
  /** 图像尺寸 */
  dimensions?: {
    width: number;
    height: number;
  };
}

/**
 * Prompt模板接口
 */
export interface PromptTemplate {
  /** 模板ID */
  id: number;
  /** 模板名称 */
  name: string;
  /** 模板内容 */
  template: string;
  /** 描述 */
  description?: string;
  /** 类别 */
  category?: string;
  /** 是否公开 */
  is_public: boolean;
  /** 使用次数 */
  usage_count: number;
  /** 创建者ID */
  creator_id: number;
  /** 创建时间 */
  created_at: string;
  /** 更新时间 */
  updated_at: string;
}

/**
 * Prompt模板创建接口
 */
export interface PromptTemplateCreate {
  /** 模板名称 */
  name: string;
  /** 模板内容 */
  template: string;
  /** 描述 */
  description?: string;
  /** 类别 */
  category?: string;
  /** 是否公开 */
  is_public?: boolean;
}

/**
 * Prompt模板响应接口
 */
export interface PromptTemplateResponse extends PromptTemplate {
  // 可以扩展响应字段
}

/**
 * 用户仪表板数据接口
 */
export interface UserDashboardData {
  /** 总创意数 */
  total_ideas: number;
  /** 已发布创意数 */
  published_ideas: number;
  /** 平均评分 */
  average_score: number;
  /** 最受欢迎的创意 */
  top_ideas: CreativeIdeaResponse[];
  /** 最近活动 */
  recent_activity: {
    type: 'created' | 'updated' | 'liked';
    idea_id: number;
    timestamp: string;
  }[];
}
