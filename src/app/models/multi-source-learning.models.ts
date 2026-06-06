/**
 * 转发层 - 共享模型
 * 从 shared/models/ 重新导出
 */
export type {
  LearningSource,
  LearningSourceCreate,
  LearningSourceListResponse,
  LearningSourceStats,
  LearningSourceUpdate,
} from '../../shared/models/course.models';
export type {
  UnifiedLearningRecord,
  UnifiedLearningRecordCreate,
  UnifiedLearningRecordListResponse,
  UnifiedLearningRecordUpdate,
  UnifiedProgressStats,
} from '../../shared/models/course.models';
export type {
  UserOrganization,
  UserOrganizationCreate,
  UserOrganizationListResponse,
  UserOrganizationStats,
  UserOrganizationUpdate,
} from '../../shared/models/course.models';
export { LearningSourceType, LearningSourceTypeLabels } from '../../shared/models/course.models';
export { UserOrganizationRoleLabels } from '../../shared/models/course.models';
