/**
 * 课件图谱闭包表 - 前端数据模型
 *
 * 与后端闭包表结构对齐，用于课件展示、导航及层级查询
 */

// ==================== 节点模型 ====================

/** 节点类型 */
export type CoursewareNodeType = 'course' | 'chapter' | 'section' | 'lesson' | 'quiz';

/** 内容类型 */
export type CoursewareContentType = 'video' | 'text' | 'quiz' | 'exercise' | 'interactive';

/** 节点状态 */
export type CoursewareNodeStatus = 'draft' | 'published' | 'archived';

/** 课件节点基础信息 */
export interface CoursewareNodeBase {
  title: string;
  description?: string;
  node_type: CoursewareNodeType;
  content_type?: CoursewareContentType;
  content_url?: string;
  duration_minutes: number;
  cover_image_url?: string;
  order_index: number;
  difficulty: string;
  tags: string[];
  extra_data: Record<string, unknown>;
  course_id?: number;
  material_id?: number;
  org_id?: number;
}

/** 创建课件节点 */
export interface CoursewareNodeCreate extends CoursewareNodeBase {
  parent_id?: number | null;
  created_by?: number;
}

/** 更新课件节点 */
export interface CoursewareNodeUpdate {
  title?: string;
  description?: string;
  node_type?: CoursewareNodeType;
  content_type?: CoursewareContentType;
  content_url?: string;
  duration_minutes?: number;
  cover_image_url?: string;
  order_index?: number;
  difficulty?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  course_id?: number;
  material_id?: number;
  is_active?: boolean;
  is_published?: boolean;
  status?: CoursewareNodeStatus;
  updated_by?: number;
}

/** 移动节点 */
export interface CoursewareNodeMove {
  new_parent_id?: number | null;
  new_order_index?: number;
}

/** 课件节点响应 */
export interface CoursewareNodeResponse {
  id: number;
  title: string;
  description?: string;
  node_type: CoursewareNodeType;
  content_type?: CoursewareContentType;
  content_url?: string;
  duration_minutes: number;
  cover_image_url?: string;
  order_index: number;
  difficulty: string;
  tags: string[];
  extra_data: Record<string, unknown>;
  course_id?: number;
  material_id?: number;
  org_id?: number;
  is_active: boolean;
  is_published: boolean;
  status: CoursewareNodeStatus;
  created_by?: number;
  updated_by?: number;
  created_at: string;
  updated_at: string;

  /** 层级信息 */
  parent_id?: number | null;
  depth: number;
  children_count: number;
}

/** 树形节点 */
export interface CoursewareTreeNode {
  node: CoursewareNodeResponse;
  children: CoursewareTreeNode[];
}

/** 节点列表响应 */
export interface CoursewareNodeListResponse {
  total: number;
  items: CoursewareNodeResponse[];
}


// ==================== 层级查询模型 ====================

/** 祖先节点 */
export interface AncestorNode {
  id: number;
  title: string;
  node_type: CoursewareNodeType;
  depth: number; // 与查询节点的层级距离
}

/** 后代节点 */
export interface DescendantNode {
  id: number;
  title: string;
  node_type: CoursewareNodeType;
  depth: number;
  is_active: boolean;
  order_index: number;
}

/** 层级查询响应 */
export interface HierarchyResponse {
  node: CoursewareNodeResponse;
  ancestors: AncestorNode[];
  descendants: DescendantNode[];
  children: CoursewareNodeResponse[];
  total_descendants: number;
}

/** 特定层级节点响应 */
export interface LevelNodesResponse {
  level: number;
  nodes: CoursewareNodeResponse[];
}

/** 节点路径 */
export interface NodePath {
  path: CoursewareNodeResponse[];
  depth: number;
}

/** 子树响应 */
export interface CoursewareSubtreeResponse {
  root: CoursewareNodeResponse;
  tree: CoursewareTreeNode;
  total_nodes: number;
}


// ==================== 批量操作模型 ====================

/** 批量创建 */
export interface BatchNodeCreate {
  nodes: CoursewareNodeCreate[];
}

/** 批量创建响应 */
export interface BatchNodeCreateResponse {
  created: number;
  errors: Array<{ index: number; error: string }>;
  nodes: CoursewareNodeResponse[];
}

/** 批量删除响应 */
export interface BatchDeleteResponse {
  deleted: number;
  errors: Array<{ node_id: number; error: string }>;
}


// ==================== 一致性验证 ====================

/** 一致性验证结果 */
export interface ClosureValidationResult {
  is_valid: boolean;
  total_nodes: number;
  total_closure_entries: number;
  orphan_nodes: number[];
  dangling_closure_entries: number[];
  missing_self_references: number[];
  depth_inconsistencies: Array<Record<string, unknown>>;
  cycle_detected: boolean;
  details: string;
}


// ==================== 迁移模型 ====================

/** 迁移结果 */
export interface MigrationResult {
  success: boolean;
  source_type: string;
  total_processed: number;
  total_created: number;
  total_errors: number;
  errors: Array<Record<string, unknown>>;
  duration_seconds: number;
}

/** 回滚结果 */
export interface RollbackResult {
  success: boolean;
  nodes_deleted: number;
  closure_entries_deleted: number;
  errors: string[];
  duration_seconds: number;
}


// ==================== 工具函数 ====================

/** 节点类型标签 */
export const CoursewareNodeTypeLabels: Record<CoursewareNodeType, string> = {
  course: '课程',
  chapter: '章节',
  section: '节',
  lesson: '课时',
  quiz: '测验',
};

/** 内容类型标签 */
export const CoursewareContentTypeLabels: Record<CoursewareContentType, string> = {
  video: '视频',
  text: '文本',
  quiz: '测验',
  exercise: '练习',
  interactive: '互动',
};

/** 节点状态标签 */
export const CoursewareNodeStatusLabels: Record<CoursewareNodeStatus, string> = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
};

/** 获取节点类型图标 */
export function getNodeTypeIcon(nodeType: CoursewareNodeType): string {
  const icons: Record<CoursewareNodeType, string> = {
    course: 'school',
    chapter: 'bookmark',
    section: 'label',
    lesson: 'play_circle',
    quiz: 'quiz',
  };
  return icons[nodeType] || 'circle';
}

/** 获取内容类型图标 */
export function getContentTypeIcon(contentType: CoursewareContentType): string {
  const icons: Record<CoursewareContentType, string> = {
    video: 'videocam',
    text: 'article',
    quiz: 'quiz',
    exercise: 'edit_note',
    interactive: 'touch_app',
  };
  return icons[contentType] || 'description';
}