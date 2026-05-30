/**
 * 学员成果数据接口
 */
export interface Achievement {
  id: number;
  userId: number;
  moduleId?: number;
  lessonId?: number;
  type: AchievementType;
  title: string;
  description: string;
  files: AchievementFile[];
  status: AchievementStatus;
  score?: number;
  feedback?: string;
  reviewedBy?: number;
  reviewedAt?: string;
  submittedAt: string;
  updatedAt: string;
  tags: string[];
  isPublic: boolean;
}

/**
 * 成果类型
 */
export type AchievementType =
  | 'project' // 项目案例
  | 'certificate' // 证书
  | 'assignment' // 作业
  | 'portfolio' // 作品集
  | 'case_study' // 案例研究
  | 'other'; // 其他

/**
 * 成果状态
 */
export type AchievementStatus =
  | 'pending' // 待审核
  | 'approved' // 已通过
  | 'rejected' // 已拒绝
  | 'revision'; // 需要修改

/**
 * 成果文件接口
 */
export interface AchievementFile {
  id: number;
  achievementId: number;
  fileName: string;
  fileType: string;
  fileSize: number;
  fileUrl: string;
  thumbnailUrl?: string;
  uploadedAt: string;
}

/**
 * 成果审核记录接口
 */
export interface AchievementReview {
  id: number;
  achievementId: number;
  reviewerId: number;
  reviewerName: string;
  status: AchievementStatus;
  score: number;
  feedback: string;
  reviewedAt: string;
  comment?: string;
}

/**
 * 成果展示模板接口
 */
export interface AchievementTemplate {
  id: number;
  name: string;
  type: AchievementType;
  layout: 'card' | 'grid' | 'timeline' | 'masonry';
  styles: TemplateStyle;
  fields: TemplateField[];
}

/**
 * 模板样式接口
 */
export interface TemplateStyle {
  backgroundColor: string;
  textColor: string;
  accentColor: string;
  cardStyle: 'flat' | 'elevated' | 'outlined';
  borderRadius: number;
  showProgress: boolean;
  showTags: boolean;
  showDate: boolean;
}

/**
 * 模板字段配置接口
 */
export interface TemplateField {
  key: string;
  label: string;
  type: 'text' | 'image' | 'file' | 'rating' | 'date' | 'tags';
  required: boolean;
  displayInCard: boolean;
  displayInDetail: boolean;
}

/**
 * 学习进度关联接口
 */
export interface AchievementProgress {
  achievementId: number;
  userId: number;
  courseId?: number;
  moduleId?: number;
  lessonId?: number;
  completionPercentage: number;
  totalAchievements: number;
  completedAchievements: number;
  averageScore: number;
  lastUpdated: string;
  milestones: ProgressMilestone[];
}

/**
 * 进度里程碑接口
 */
export interface ProgressMilestone {
  id: number;
  name: string;
  description: string;
  achievedAt?: string;
  achievementIds: number[];
}

/**
 * 成果统计数据接口
 */
export interface AchievementStats {
  totalAchievements: number;
  pendingReviews: number;
  approvedAchievements: number;
  rejectedAchievements: number;
  averageScore: number;
  recentActivity: AchievementActivity[];
  byType: Record<string, number>;
  byStatus: Record<AchievementStatus, number>;
}

/**
 * 成果活动记录接口
 */
export interface AchievementActivity {
  id: number;
  achievementId: number;
  achievementTitle: string;
  type: 'submitted' | 'approved' | 'rejected' | 'commented';
  userId: number;
  userName: string;
  timestamp: string;
}

/**
 * 成果筛选接口
 */
export interface AchievementFilter {
  status?: AchievementStatus[];
  type?: AchievementType[];
  moduleId?: number[];
  lessonId?: number[];
  userId?: number[];
  dateFrom?: string;
  dateTo?: string;
  tags?: string[];
  searchQuery?: string;
}

/**
 * 成果排序接口
 */
export type AchievementSortBy = 'submittedAt' | 'updatedAt' | 'score' | 'title' | 'reviewedAt';

export interface AchievementSort {
  field: AchievementSortBy;
  direction: 'asc' | 'desc';
}
