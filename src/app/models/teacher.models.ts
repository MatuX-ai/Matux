/**
 * 教师管理模块类型定义
 */

/**
 * 教师状态枚举
 */
export type TeacherStatus = 'active' | 'inactive' | 'on_leave';

/**
 * 教师基本信息
 */
export interface Teacher {
  /** 教师 ID */
  id: number;
  /** 姓名 */
  name: string;
  /** 邮箱 */
  email: string;
  /** 电话 (可选) */
  phone?: string;
  /** 所属部门 */
  department: string;
  /** 职位 (可选) */
  position?: string;
  /** 授课数量 */
  courseCount: number;
  /** 带学生数 (可选) */
  studentCount?: number;
  /** 状态 */
  status: TeacherStatus;
  /** 入职日期 (可选) */
  hireDate?: string;
  /** 个人简介 (可选) */
  bio?: string;
  /** 头像 URL (可选) */
  avatar?: string;
  /** 评分 (1-5, 可选) */
  rating?: number;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
}

/**
 * 教师创建请求
 */
export interface TeacherCreate {
  name: string;
  email: string;
  phone?: string;
  department: string;
  position?: string;
  hireDate?: string;
  bio?: string;
  avatar?: string;
}

/**
 * 教师更新请求
 */
export interface TeacherUpdate {
  name?: string;
  email?: string;
  phone?: string;
  department?: string;
  position?: string;
  bio?: string;
  avatar?: string;
  status?: TeacherStatus;
}

/**
 * 教师统计信息
 */
export interface TeacherStats {
  /** 总教师数 */
  totalCount: number;
  /** 在职教师数 */
  activeCount: number;
  /** 请假教师数 */
  onLeaveCount: number;
  /** 离职教师数 */
  inactiveCount: number;
  /** 平均评分 */
  averageRating?: number;
  /** 总授课数 */
  totalCourseCount: number;
}

/**
 * 教师详情 (扩展信息)
 */
export interface TeacherDetail extends Teacher {
  /** 学员评价列表 */
  reviews?: TeacherReview[];
  /** 授课记录 */
  courseRecords?: CourseRecord[];
  /** 工作统计 */
  workStats?: TeacherWorkStats;
}

/**
 * 学员评价
 */
export interface TeacherReview {
  id: number;
  studentId: number;
  studentName: string;
  rating: number;
  comment: string;
  createdAt: string;
}

/**
 * 授课记录
 */
export interface CourseRecord {
  courseId: number;
  courseName: string;
  studentCount: number;
  startDate: string;
  endDate?: string;
  status: 'ongoing' | 'completed' | 'cancelled';
}

/**
 * 教师工作统计
 */
export interface TeacherWorkStats {
  /** 总课时数 */
  totalHours: number;
  /** 本月课时数 */
  monthHours: number;
  /** 学员总数 */
  totalStudents: number;
  /** 好评率 */
  positiveRate: number;
  /** 出勤率 */
  attendanceRate: number;
}
