/**
 * Admin Layout 配置文件
 * 定义路由路径和页面标题映射
 */

/** 路由路径常量 */
export const ROUTE_PATHS = {
  DASHBOARD: '/admin/dashboard',
  LOGIN: '/admin/login',
  // LICENSES: '/admin/licenses', // // 已解耦至 OpenMTEduInst 项目
  MATERIALS: '/admin/materials',
  COURSES: '/admin/courses',
  USERS: '/admin/users',
  PAYMENTS: '/admin/payments',
  DATABASE_REGISTRY: '/admin/database-registry',
  MARKETING: '/admin/marketing',
  API_SETTINGS: '/admin/api-settings',
  API_DOCS: '/admin/api-docs',
} as const;

/** 页面标题映射表 */
export const PAGE_TITLE_MAP: Record<string, string> = {
  '/admin/dashboard': '仪表板',
  // '/admin/licenses': '许可证管理', // 已解耦至 OpenMTEduInst 项目
  '/admin/materials': '课件库管理',
  '/admin/courses': '课程库管理',
  '/admin/users': '用户管理',
  '/admin/payments': '支付管理',
  '/admin/database-registry': '数据中心管理',
  '/admin/marketing': '营销数据',
  '/admin/api-settings': 'API 设置',
  '/admin/api-docs': 'API 文档',
} as const;

/** 路由到标题的映射（用于 ActivatedRoute） */
export const ROUTE_TITLE_MAP: Record<string, string> = {
  dashboard: '仪表板',
  users: '用户管理',
  // licenses: '许可证管理', // 已解耦至 OpenMTEduInst 项目
  payments: '支付管理',
  sponsorship: '赞助管理',
  'database-registry': '数据中心管理',
  'api-docs': 'API 文档',
};
