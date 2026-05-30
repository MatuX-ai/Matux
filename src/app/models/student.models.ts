/**
 * 学员管理模块类型定义
 */

/**
 * 学员状态枚举
 */
export type StudentStatus = 'active' | 'inactive' | 'graduated' | 'suspended';

/**
 * 家长信息接口
 */
export interface ParentInfo {
  /** 家长姓名 */
  name: string;
  /** 联系电话 */
  phone: string;
  /** 与学员关系 (父子/母女等) */
  relationship: string;
  /** 邮箱 (可选) */
  email?: string;
}

/**
 * 学员基本信息
 */
export interface Student {
  /** 学员 ID */
  id: number;
  /** 姓名 */
  name: string;
  /** 邮箱 */
  email: string;
  /** 电话 (可选) */
  phone?: string;
  /** 年级 */
  grade: string;
  /** 已报名课程数 */
  enrolledCourses: number;
  /** 学习进度 (0-100) */
  progress: number;
  /** 出勤率 (可选) */
  attendanceRate?: number;
  /** 状态 */
  status: StudentStatus;
  /** 家长信息 (可选) */
  parentInfo?: ParentInfo;
  /** 报名日期 (可选) */
  enrollmentDate?: string;
  /** 毕业日期 (可选) */
  graduationDate?: string;
  /** 头像 URL (可选) */
  avatar?: string;
  /** 总缴费金额 (可选) */
  totalPayment?: number;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

/**
 * 学员创建请求
 */
export interface StudentCreate {
  name: string;
  email: string;
  phone?: string;
  grade: string;
  parentInfo?: ParentInfo;
  enrollmentDate?: string;
  avatar?: string;
}

/**
 * 学员更新请求
 */
export interface StudentUpdate {
  name?: string;
  email?: string;
  phone?: string;
  grade?: string;
  parentInfo?: ParentInfo;
  avatar?: string;
  status?: StudentStatus;
}

/**
 * 学员统计信息
 */
export interface StudentStats {
  /** 总学员数 */
  totalCount: number;
  /** 在读学员数 */
  activeCount: number;
  /** 已毕业学员数 */
  graduatedCount: number;
  /** 休学学员数 */
  suspendedCount: number;
  /** 平均出勤率 */
  averageAttendance?: number;
  /** 平均满意度 */
  averageSatisfaction?: number;
  /** 总报名课程数 */
  totalEnrolledCourses: number;
}

/**
 * 学员详情 (扩展信息)
 */
export interface StudentDetail extends Student {
  /** 报名的课程列表 */
  courseEnrollments?: CourseEnrollment[];
  /** 成绩记录 */
  grades?: GradeRecord[];
  /** 学习轨迹 */
  learningPath?: LearningPathItem[];
  /** 缴费记录 */
  paymentRecords?: PaymentRecord[];
}

/**
 * 课程报名记录
 */
export interface CourseEnrollment {
  courseId: number;
  courseName: string;
  enrollDate: string;
  status: 'ongoing' | 'completed' | 'dropped';
  progress: number;
  finalGrade?: number;
}

/**
 * 成绩记录
 */
export interface GradeRecord {
  courseId: number;
  courseName: string;
  score: number;
  comment?: string;
  date: string;
}

/**
 * 学习轨迹项
 */
export interface LearningPathItem {
  type: 'course' | 'exam' | 'assignment' | 'certificate';
  title: string;
  description: string;
  completedAt: string;
  score?: number;
}

/**
 * 缴费记录
 */
export interface PaymentRecord {
  id: number;
  amount: number;
  type: string;
  description: string;
  paymentDate: string;
  status: 'paid' | 'pending' | 'refunded';
}
