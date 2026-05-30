/**
 * iMato 教育培训管理系统 - 排课模块数据模型
 */

// ==================== 核心排课模型 ====================

export interface CourseSchedule {
  id: string;
  courseId: string;
  courseName?: string;
  teacherId: string;
  teacherName?: string;
  classroomId?: string;
  classroomName?: string;
  classId?: string;
  className?: string;
  dayOfWeek: number; // 0-6, 0 表示周日
  startTime: string; // HH:mm
  endTime: string; // HH:mm
  startDate: string; // YYYY-MM-DD
  endDate: string; // YYYY-MM-DD
  recurrencePattern: 'weekly' | 'biweekly' | 'once' | 'custom';
  isConfirmed: boolean;
  isActive: boolean;
  hasConflict?: boolean;
  conflicts?: ScheduleConflict[];
}

export interface ScheduleConflict {
  id: string;
  scheduleId: string;
  conflictType: ConflictType;
  description: string;
  relatedScheduleIds: string[];
  status: 'pending' | 'resolved' | 'ignored';
  createdAt: string;
  resolvedAt?: string;
}

export type ConflictType =
  | 'teacher_conflict' // 教师冲突
  | 'classroom_conflict' // 教室冲突
  | 'student_conflict' // 学生冲突
  | 'capacity_conflict'; // 容量冲突

// ==================== 约束条件模型 ====================

export interface SchedulingConstraints {
  hardConstraints: Constraint[]; // 硬约束 (不可违反)
  softConstraints: SoftConstraint[]; // 软约束 (尽量满足)
}

export interface Constraint {
  id: string;
  type: ConstraintType;
  description: string;
  enabled: boolean;
}

export interface SoftConstraint {
  id: string;
  type: ConstraintType;
  description: string;
  weight: number; // 权重 (0-1)
  enabled: boolean;
}

export type ConstraintType =
  | 'teacher_time_conflict' // 教师同一时间只能在一个教室
  | 'classroom_capacity' // 教室容量必须 >= 班级人数
  | 'student_double_booking' // 学生不能同时上两门课
  | 'teacher_unavailable' // 教师不可排课时间
  | 'teacher_preference' // 教师偏好时间段
  | 'classroom_equipment' // 教室设备匹配度
  | 'continuous_classes' // 避免连续上课超过 N 节
  | 'daily_class_limit'; // 同一天同一班级不超过 N 次课

// ==================== 排课请求和响应模型 ====================

export interface ScheduleGenerationRequest {
  courses: CourseInfo[];
  teachers: TeacherInfo[];
  classrooms: ClassroomInfo[];
  classes: ClassInfo[];
  constraints: SchedulingConstraints;
  options?: ScheduleGenerationOptions;
}

export interface ScheduleGenerationOptions {
  populationSize?: number; // 种群大小 (默认 100)
  generations?: number; // 迭代代数 (默认 1000)
  mutationRate?: number; // 变异率 (默认 0.1)
}

export interface ScheduleGenerationResponse {
  success: boolean;
  schedule: CourseSchedule[];
  conflicts: ScheduleConflict[];
  score: number; // 优化得分 (0-100)
  message?: string;
}

// ==================== 辅助接口 ====================

export interface CourseInfo {
  id: string;
  name: string;
  totalHours: number;
  courseType: 'one_on_one' | 'small_class' | 'medium_class' | 'large_class';
}

export interface TeacherInfo {
  id: string;
  name: string;
  availableTimeSlots: TimeSlot[];
  maxWeeklyHours: number;
  teachingSubjects: string[];
}

export interface ClassroomInfo {
  id: string;
  name: string;
  capacity: number;
  equipment: string[];
}

export interface ClassInfo {
  id: string;
  name: string;
  studentCount: number;
  students: string[]; // 学生 ID 列表
}

export interface TimeSlot {
  dayOfWeek: number;
  startTime: string;
  endTime: string;
}

// ==================== 课表视图相关模型 ====================

export interface ScheduleView {
  viewMode: 'day' | 'week' | 'month';
  currentDate: Date;
  schedules: CourseSchedule[];
  filters?: ScheduleFilters;
}

export interface ScheduleFilters {
  teacherId?: string;
  classroomId?: string;
  classId?: string;
  courseType?: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  allDay?: boolean;
  backgroundColor?: string;
  borderColor?: string;
  textColor?: string;
  extendedProps: {
    schedule: CourseSchedule;
    hasConflict?: boolean;
  };
}
