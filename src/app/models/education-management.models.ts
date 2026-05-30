/**
 * 教育管理系统数据模型
 * 为教师、学生、课程、组织等提供强类型接口定义
 */

// ==================== 组织相关接口 ====================

/** 组织基本信息 */
export interface Organization {
  id: number;
  name: string;
  type: 'school' | 'training_institution' | 'online_platform' | 'competition_center';
  logo_url?: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  status: 'active' | 'inactive' | 'pending_review';
  created_at: string;
  updated_at: string;
}

/** 组织成员（用户关联） */
export interface OrganizationMember {
  id: number;
  org_id: number;
  user_id: number;
  role: 'admin' | 'teacher' | 'student' | 'parent' | 'staff';
  department?: string;
  position?: string;
  join_date: string;
  leave_date?: string;
  status: 'active' | 'inactive' | 'pending';
  permissions: Record<string, boolean>;
  created_at: string;
  updated_at: string;
}

/** 组织统计数据 */
export interface OrganizationStats {
  teacher_count: number;
  student_count: number;
  course_count: number;
  classroom_count: number;
  active_lessons_today: number;
  pending_assignments: number;
  average_attendance_rate: number;
  average_progress_rate: number;
}

// ==================== 教师相关接口 ====================

/** 教师档案 */
export interface TeacherProfile {
  id: number;
  user_id: number;
  org_id: number;
  employee_id?: string;
  title?: 'professor' | 'associate_professor' | 'lecturer' | 'assistant' | 'teaching_assistant';
  department?: string;
  specialization?: string;
  years_of_experience?: number;
  highest_degree?: 'bachelor' | 'master' | 'phd' | 'postdoc';
  biography?: string;
  office_hours?: string;
  office_location?: string;
  status: 'active' | 'on_leave' | 'retired' | 'inactive';
  hire_date: string;
  created_at: string;
  updated_at: string;
}

/** 教师课程关联 */
export interface TeacherCourseAssignment {
  id: number;
  teacher_id: number;
  course_id: number;
  org_id: number;
  role: 'main_teacher' | 'assistant_teacher' | 'substitute_teacher';
  start_date: string;
  end_date?: string;
  workload_hours: number;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

// ==================== 学生相关接口 ====================

/** 学生档案 */
export interface StudentProfile {
  id: number;
  user_id: number;
  org_id: number;
  student_id?: string;
  grade?: number;
  class_name?: string;
  enrollment_date: string;
  expected_graduation_date?: string;
  guardian_name?: string;
  guardian_phone?: string;
  guardian_email?: string;
  emergency_contact?: string;
  medical_notes?: string;
  status: 'active' | 'graduated' | 'transferred' | 'suspended' | 'inactive';
  created_at: string;
  updated_at: string;
}

/** 学生课程关联 */
export interface StudentCourseEnrollment {
  id: number;
  student_id: number;
  course_id: number;
  org_id: number;
  enrollment_date: string;
  completion_date?: string;
  grade?: number;
  attendance_rate: number;
  progress_rate: number;
  status: 'enrolled' | 'completed' | 'dropped' | 'suspended';
  created_at: string;
  updated_at: string;
}

// ==================== 课程相关接口 ====================

/** 课程基本信息 */
export interface Course {
  id: number;
  org_id: number;
  title: string;
  name?: string; // 别名，兼容不同 API
  code?: string;
  description?: string;
  subject?: string;
  instructor_name?: string;
  institution?: string;
  source_type?: 'school_curriculum' | 'school_interest' | 'institution';
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  level?: 'beginner' | 'intermediate' | 'advanced';
  credit_hours?: number;
  total_lessons?: number;
  schedule_pattern?: 'weekly' | 'biweekly' | 'monthly' | 'custom';
  start_date?: string;
  end_date?: string;
  max_students?: number;
  enrolled_students?: number;
  current_students?: number;
  rating?: number;
  thumbnail_url?: string;
  tags?: string[];
  status: 'draft' | 'published' | 'ongoing' | 'completed' | 'archived';
  requirements?: string;
  learning_objectives?: string[];
  is_enrolled?: boolean;
  student_progress?: number;
  created_at: string;
  updated_at: string;
}

/** 课程库列表响应 */
export interface CourseLibraryResponse {
  courses: Course[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** 课程章节/课时 */
export interface Lesson {
  id: number;
  course_id: number;
  order_number: number;
  title: string;
  description?: string;
  content_type: 'lecture' | 'lab' | 'workshop' | 'discussion' | 'exam' | 'assignment';
  duration_minutes: number;
  materials?: string[];
  learning_outcomes?: string[];
  is_required: boolean;
  scheduled_date?: string;
  completed_date?: string;
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

/** 课程章节（包含多个课时） */
export interface CourseChapter {
  id: number;
  course_id: number;
  title: string;
  description?: string;
  order_number: number;
  lessons: Lesson[];
  created_at: string;
  updated_at: string;
}

// ==================== 作业与评估接口 ====================

/** 作业/任务 */
export interface Assignment {
  id: number;
  lesson_id: number;
  course_id: number;
  title: string;
  description?: string;
  instructions: string;
  due_date: string;
  max_score: number;
  weight: number;
  type: 'homework' | 'quiz' | 'project' | 'essay' | 'presentation' | 'lab_report';
  attachments?: string[];
  submission_format?: 'text' | 'file' | 'code' | 'presentation' | 'multiple';
  created_at: string;
  updated_at: string;
}

/** 学生作业提交 */
export interface StudentAssignmentSubmission {
  id: number;
  assignment_id: number;
  student_id: number;
  content?: string;
  attachments?: string[];
  submitted_at: string;
  grade?: number;
  feedback?: string;
  graded_by?: number;
  graded_at?: string;
  status: 'pending' | 'submitted' | 'graded' | 'overdue' | 'missed';
  late_submission: boolean;
  created_at: string;
  updated_at: string;
}

// ==================== 学习进度与考勤接口 ====================

/** 学习进度记录 */
export interface LearningProgress {
  id: number;
  student_id: number;
  course_id: number;
  lesson_id?: number;
  progress_percentage: number;
  time_spent_minutes: number;
  last_activity_type:
    | 'lesson_completed'
    | 'assignment_submitted'
    | 'quiz_taken'
    | 'material_viewed';
  last_activity_at: string;
  overall_understanding?: 'poor' | 'fair' | 'good' | 'excellent';
  notes?: string;
  created_at: string;
  updated_at: string;
}

/** 出勤记录 */
export interface AttendanceRecord {
  id: number;
  student_id: number;
  course_id: number;
  lesson_id?: number;
  date: string;
  status: 'present' | 'absent' | 'late' | 'excused' | 'half_day';
  check_in_time?: string;
  check_out_time?: string;
  notes?: string;
  recorded_by: number;
  recorded_at: string;
  created_at: string;
  updated_at: string;
}

// ==================== Dashboard数据接口 ====================

/** 教师Dashboard概览 */
export interface TeacherDashboardOverview {
  teacher_id: number;
  org_id: number;
  stats: {
    total_courses: number;
    active_courses: number;
    total_students: number;
    pending_assignments: number;
    completed_lessons_this_week: number;
    average_student_progress: number;
    attendance_rate: number;
  };
  upcoming_lessons: {
    id: number;
    course_id: number;
    course_name: string;
    lesson_title: string;
    scheduled_date: string;
    start_time: string;
    classroom?: string;
  }[];
  recent_activities: {
    id: number;
    type: 'assignment_submitted' | 'grade_updated' | 'lesson_completed' | 'attendance_recorded';
    title: string;
    description: string;
    student_name?: string;
    course_name?: string;
    timestamp: string;
  }[];
  pending_actions: {
    type: 'grade_assignment' | 'review_submission' | 'update_attendance' | 'provide_feedback';
    count: number;
    priority: 'high' | 'medium' | 'low';
  }[];
  last_updated: string;
}

/** 多源学习整合的教师数据 */
export interface MultiSourceTeacherData {
  teacher_id: number;
  organizations: {
    org_id: number;
    org_name: string;
    role: string;
    stats: OrganizationStats;
  }[];
  unified_progress: {
    total_students: number;
    average_progress_across_orgs: number;
    active_courses_count: number;
    pending_assignments_count: number;
  };
  learning_sources: {
    source_id: number;
    source_name: string;
    source_type: 'school_curriculum' | 'institution' | 'online_platform';
    org_id: number;
    student_count: number;
    progress_rate: number;
  }[];
}

// ==================== API响应接口 ====================

/** 通用API响应包装 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error_code?: string;
  pagination?: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

/** 分页列表响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ==================== 类型守卫和工具类型 ====================

/** 检查对象是否为 Organization */
export function isOrganization(obj: unknown): obj is Organization {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    typeof (obj as Record<string, unknown>)['id'] === 'number' &&
    typeof (obj as Record<string, unknown>)['name'] === 'string'
  );
}

/** 检查对象是否为 TeacherProfile */
export function isTeacherProfile(obj: unknown): obj is TeacherProfile {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'user_id' in obj &&
    'org_id' in obj &&
    typeof (obj as Record<string, unknown>)['user_id'] === 'number' &&
    typeof (obj as Record<string, unknown>)['org_id'] === 'number'
  );
}

/** 提取多源学习中的组织信息 */
export function extractOrganizationInfo(sourceDetail: Record<string, unknown>): {
  organization_name?: string;
  organization_id?: number;
  class_name?: string;
  grade?: number;
} {
  return {
    organization_name:
      (sourceDetail['organization_name'] as string | undefined) ??
      (sourceDetail['org_name'] as string | undefined),
    organization_id:
      (sourceDetail['organization_id'] as number | undefined) ??
      (sourceDetail['org_id'] as number | undefined),
    class_name: sourceDetail['class_name'] as string | undefined,
    grade: sourceDetail['grade'] as number | undefined,
  };
}
