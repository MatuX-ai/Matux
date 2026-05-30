/**
 * 统一课程与学习数据模型
 */

// ==================== 多来源学习类型 ====================

export type LearningSourceType =
  | 'school_curriculum'
  | 'school_interest'
  | 'institution'
  | 'self_study'
  | 'online_platform'
  | 'competition';

export const LearningSourceTypeLabels: Record<string, string> = {
  school_curriculum: '校本课程',
  school_interest: '校内兴趣班',
  institution: '培训机构',
  self_study: '自学',
  online_platform: '在线平台',
  competition: '竞赛',
};

/** 学习来源 */
export interface LearningSource {
  id: number;
  user_id: number;
  org_id: number;
  name: string;
  source_type: LearningSourceType;
  status: 'active' | 'inactive' | 'completed' | 'suspended';
  is_primary: boolean;
  is_active: boolean;
  role: string;
  source_detail: Record<string, unknown>;
  start_date: string | null;
  end_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface LearningSourceCreate {
  name: string;
  source_type: LearningSourceType;
  org_id: number;
  user_id?: number;
  role?: string;
  start_date?: string;
  end_date?: string;
  notes?: string;
  is_primary?: boolean;
  source_detail?: Record<string, unknown>;
}

export interface LearningSourceUpdate {
  name?: string;
  status?: string;
  is_primary?: boolean;
}

export interface LearningSourceStats {
  total_courses: number;
  completed_courses: number;
  in_progress_courses: number;
  total_time_minutes: number;
  average_score: number | null;
  total?: number;
  active?: number;
  primary?: { name?: string } | null;
}

export interface LearningSourceListResponse {
  total: number;
  items: LearningSource[];
}

// ==================== 统一课程 ====================

export type CourseStatus = 'draft' | 'published' | 'archived';

export interface CourseEnrollment {
  id: number;
  user_id: number;
  course_id: number;
  org_id: number;
  progress_percentage: number;
  score: number | null;
  status: 'active' | 'completed' | 'dropped';
  enrolled_at: string;
  completed_at: string | null;
}

export interface UnifiedCourse {
  id: number;
  org_id: number;
  title: string;
  description: string;
  cover_image_url: string | null;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration_minutes: number;
  status: CourseStatus;
  source_type: LearningSourceType;
  teacher_name: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

// ==================== 统一学习记录 ====================

/** 统一学习记录 */
export interface UnifiedLearningRecord {
  id: number;
  user_id: number;
  course_id: number;
  source_type: LearningSourceType;
  module_id: number;
  lesson_id: number;
  progress_percentage: number;
  score: number | null;
  time_spent_minutes: number;
  status: 'active' | 'completed' | 'paused';
  last_access_time: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UnifiedLearningRecordCreate {
  user_id: number;
  course_id: number;
  source_type: LearningSourceType;
  module_id: number;
  lesson_id: number;
  progress_percentage: number;
}

export interface UnifiedLearningRecordUpdate {
  progress_percentage?: number;
  score?: number;
  time_spent_minutes?: number;
  status?: string;
}

export interface UnifiedLearningRecordListResponse {
  total: number;
  page: number;
  page_size: number;
  items: UnifiedLearningRecord[];
}

/** 统一学习进度统计 */
export interface UnifiedProgressStats {
  total_courses: number;
  completed_courses: number;
  in_progress_courses: number;
  total_time_minutes: number;
  average_score: number | null;
  source_breakdown: Array<{
    source_type: LearningSourceType;
    source_name: string;
    courses: number;
    completed: number;
    avg_score: number | null;
    total_time: number;
  }>;
}

// ==================== 用户组织关联 ====================

/** 用户组织关联 */
export interface UserOrganization {
  id: number;
  user_id: number;
  org_id: number;
  role: string;
  status: string;
  is_primary: boolean;
  class_name?: string;
  learning_source_type?: LearningSourceType;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export const UserOrganizationRoleLabels: Record<string, string> = {
  student: '学生',
  teacher: '教师',
  admin: '管理员',
  parent: '家长',
};

export interface UserOrganizationCreate {
  user_id: number;
  org_id: number;
  role: string;
  is_primary?: boolean;
}

export interface UserOrganizationUpdate {
  role?: string;
  status?: string;
  is_primary?: boolean;
}

export interface UserOrganizationListResponse {
  total: number;
  items: UserOrganization[];
}

export interface UserOrganizationStats {
  total: number;
  by_source_type: Record<string, number>;
  by_role?: Record<string, number>;
}
