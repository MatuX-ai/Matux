/**
 * 应用路由常量 - 集中管理所有路由路径
 * 避免硬编码，一处修改，全局生效
 *
 * 使用方式：
 * import { ROUTES } from './routes.const';
 * router.navigate([ROUTES.USER.DASHBOARD]);
 */

export const ROUTES = {
  // 首页重定向
  HOME: '/',

  // 认证模块
  AUTH: {
    BASE: '/auth',
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    CALLBACK: '/auth/callback',
  },

  // 用户中心模块
  USER: {
    BASE: '/user',
    DASHBOARD: '/user/dashboard',
    PROFILE: '/user/profile',
    TOKEN: '/user/token',
    COURSES: '/user/courses',
    LEARNING_PROFILE: '/user/learning-profile',
    GROWTH_TRAJECTORY: '/user/growth-trajectory',
    REPORTS: '/user/reports',
    TEACHING_SUGGESTIONS: '/user/teaching-suggestions',
    ACHIEVEMENTS: '/user/achievements',
    EMOTIONAL_COMPANION: '/user/emotional-companion',
    AI_TEACHER_SETTINGS: '/user/ai-teacher-settings',
  },

  // AI 编程教育
  AI_EDU: {
    BASE: '/ai-edu',
    DASHBOARD: '/ai-edu/dashboard',
  },

  // 学习实验室
  LAB: {
    AR_LAB: '/ar-lab',
    ARVR_COURSE: '/arvr-course',
    DIGITAL_TWIN: '/digital-twin-lab',
    CREATIVITY: '/creativity-engine',
    VIRCADIA: '/vircadia',
  },

  // 其他功能模块
  EXAM: '/exam',
  OFFLINE_MODE: '/offline-mode',
  CONTENT_STORE: '/content-store',

  // OpenSciEDU 公共课程
  OPENSCIEDU: {
    BASE: '/opensciedu',
    CATALOG: '/opensciedu/catalog',
    KNOWLEDGE_GRAPH: '/opensciedu/knowledge-graph',
  },

  // 产品相关（保留原有）
  PRODUCT: {
    DOWNLOAD: '/download',
    DOWNLOAD_DESKTOP: '/download#desktop',
    DOWNLOAD_APP: '/download#app',
    HARDWARE: '/hardware',
  },
} as const;

// 路由参数类型
export type RoutePath = string;
