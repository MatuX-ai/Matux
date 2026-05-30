/**
 * 学员档案数据模型
 */

export type StudentStatus = '在读' | '休学' | '毕业' | '退学' | '转校';
export type Gender = 'male' | 'female' | 'other';

export interface StudentProfile {
  id: string;
  name: string;
  gender: Gender;
  birthDate?: string; // YYYY-MM-DD
  grade?: string; // 年级 (如：初三)
  school?: string; // 就读学校

  // 联系方式
  phone?: string;
  email?: string;
  address?: string;

  // 身份证信息
  idCardNumber?: string;
  idCardAddress?: string;

  // 头像
  avatarUrl?: string;

  // 学籍状态
  status: StudentStatus;
  enrollmentDate: string; // 入学日期
  graduationDate?: string; // 预计毕业日期
  actualGraduationDate?: string; // 实际毕业日期

  // 分班信息
  currentClassId?: string;
  currentClassName?: string;

  // 课时信息
  totalPurchasedHours: number;
  totalConsumedHours: number;
  remainingHours: number;

  // 家长信息
  parents: ParentInfo[];

  // 紧急联系人
  emergencyContact?: string;
  emergencyPhone?: string;

  // 扩展字段
  customFields?: Record<string, unknown>;

  // 备注
  notes?: string;

  // 元数据
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
}

export interface ParentInfo {
  id: string;
  studentId: string;
  name: string;
  relationshipType: RelationshipType;
  phone: string;
  email?: string;
  wechat?: string;
  qq?: string;
  address?: string;
  isPrimary: boolean;
  notes?: string;
}

export type RelationshipType = '父亲' | '母亲' | '其他监护人';

// ==================== 查询和筛选模型 ====================

export interface StudentQuery {
  page: number;
  pageSize: number;
  keyword?: string;
  grade?: string;
  school?: string;
  status?: StudentStatus;
  classId?: string;
  hasLowBalance?: boolean; // 课时不足预警
}

export interface StudentListResponse {
  total: number;
  list: StudentProfile[];
  page: number;
  pageSize: number;
}

export interface StudentFilters {
  grade?: string;
  school?: string;
  status?: StudentStatus;
  classId?: string;
  gender?: Gender;
  hasLowBalance?: boolean;
}

// ==================== 导入导出模型 ====================

export interface StudentImportResult {
  success: number;
  failed: number;
  errors: ImportError[];
}

export interface ImportError {
  row: number;
  message: string;
  data?: Record<string, unknown>;
}

// ==================== 统计模型 ====================

export interface StudentStats {
  totalStudents: number;
  activeStudents: number;
  newStudentsThisMonth: number;
  graduatedStudents: number;
  lowBalanceWarningCount: number;
}
