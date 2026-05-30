/**
 * 教师信息数据模型
 */

export type EmploymentType = 'full_time' | 'part_time';
export type TeacherStatus = 'active' | 'inactive' | 'resigned';

export interface Teacher {
  id: string;
  name: string;
  gender?: 'male' | 'female';
  birthDate?: string;
  phone: string;
  email?: string;

  // 身份证信息
  idCardNumber?: string;

  // 入职信息
  hireDate: string;
  employmentType: EmploymentType;

  // 薪酬配置
  baseSalary: number; // 底薪 (元/月)
  positionAllowance: number; // 岗位津贴 (元/月)

  // 教学资质
  teacherCertificate?: string; // 教师资格证编号
  qualifications?: Qualification[];

  // 教学信息
  teachingSubjects: string[]; // 教授科目
  maxWeeklyHours: number; // 最大周课时量
  preferredTeachingTimes?: TimeSlot[]; // 偏好授课时间段

  // 状态
  isActive: boolean;
  status: TeacherStatus;

  // 头像
  avatarUrl?: string;

  // 备注
  notes?: string;

  // 元数据
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
}

export interface Qualification {
  name: string;
  certificateNumber?: string;
  issueDate?: string;
  expiryDate?: string;
  issuingAuthority?: string;
}

export interface TimeSlot {
  dayOfWeek: number;
  startTime: string;
  endTime: string;
}

// ==================== 授课记录模型 ====================

export interface TeachingRecord {
  id: string;
  teacherId: string;
  scheduleId?: string;
  courseId: string;
  classId?: string;

  teachingDate: string;
  startTime: string;
  endTime: string;
  durationMinutes: number;

  courseType: CourseType;
  classSize: number;

  hourlyRate: number; // 课时费标准 (元/小时)
  teachingIncome: number; // 本次课时费

  month: string; // YYYY-MM
  status: TeachingStatus;
  isConfirmed: boolean;

  notes?: string;

  createdAt: string;
  confirmedAt?: string;
  confirmedBy?: string;
}

export type CourseType = 'one_on_one' | 'small_class' | 'medium_class' | 'large_class';
export type TeachingStatus = 'completed' | 'cancelled' | 'makeup';

// ==================== 教师工资模型 ====================

export interface TeacherSalary {
  id: string;
  teacherId: string;
  month: string; // YYYY-MM

  // 收入部分
  baseSalary: number;
  teachingIncome: number;
  performanceBonus: number;
  attendanceBonus: number;
  renewalBonus: number;
  competitionBonus: number;

  // 扣款项
  lateDeduction: number;
  accidentDeduction: number;
  complaintDeduction: number;
  otherDeductions: number;

  // 应发工资
  grossSalary: number;

  // 扣除项
  socialSecurity: number;
  housingFund: number;
  tax: number;

  // 实发工资
  netSalary: number;

  // 发放状态
  status: SalaryStatus;
  paidDate?: string;
  paidBy?: string;

  notes?: string;

  createdAt: string;
  updatedAt: string;
}

export type SalaryStatus = 'pending' | 'calculated' | 'paid';

// ==================== 查询和统计模型 ====================

export interface TeacherQuery {
  page: number;
  pageSize: number;
  keyword?: string;
  employmentType?: EmploymentType;
  status?: TeacherStatus;
  subject?: string;
}

export interface TeacherListResponse {
  total: number;
  list: Teacher[];
  page: number;
  pageSize: number;
}

export interface TeacherWorkloadStats {
  teacherId: string;
  teacherName: string;
  totalClasses: number;
  totalHours: number;
  totalStudents: number;
  monthlyIncome: number;
  period: string; // YYYY-MM
}

export interface TeacherSalarySummary {
  teacherId: string;
  teacherName: string;
  month: string;
  baseSalary: number;
  teachingIncome: number;
  bonuses: number;
  deductions: number;
  netSalary: number;
  status: SalaryStatus;
}
