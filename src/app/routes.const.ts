/**
 * 应用路由常量 - 集中管理所有路由路径
 * 避免硬编码，一处修改，全局生效
 */

export const ROUTES = {
  // 首页
  HOME: '/',

  // 产品相关
  PRODUCT: {
    DOWNLOAD: '/download',
    DOWNLOAD_DESKTOP: '/download#desktop',
    DOWNLOAD_APP: '/download#app',
    HARDWARE: '/hardware',
  },

  // 学习相关
  LEARNING: {
    COURSES: '/courses',
    AR_LAB: '/ar-lab',
  },

  // 技术相关
  TECH: {
    BLOCKCHAIN: '/blockchain',
    GITHUB: '/github',
  },

  // 用户相关
  USER: {
    SIGNUP: '/signup',
    CONTACT: '/contact',
    DEMO: '/demo',
  },

  // 功能模块
  MODULE: {
    DASHBOARD: '/dashboard',
    AR_LAB: '/ar-lab',
    OFFLINE_MODE: '/offline-mode',
    AI_EDU: '/ai-edu',
    ARVR_COURSE: '/arvr-course',
    DIGITAL_TWIN_LAB: '/digital-twin-lab',
    LICENSE_MANAGEMENT: '/license-management',
    CONTENT_STORE: '/content-store',
    CREATIVITY_ENGINE: '/creativity-engine',
  },

  // 后台管理
  ADMIN: {
    LOGIN: '/admin/login',
    DASHBOARD: '/admin',
    LICENSES: '/admin/licenses',
    // ORGANIZATIONS: '/admin/institutions', // ✅ 已解耦到 OpenMTEduInst 项目
    USERS: '/admin/users',
    PAYMENTS: '/admin/payments',
    SPONSORSHIP: '/admin/sponsorship',
    DATABASE_REGISTRY: '/admin/database-registry',
    MARKETING: '/admin/marketing',
  },
} as const;

// 路由参数类型
export type RoutePath = string;

// Tab类型
export enum TabType {
  B = 'B', // B端 - 教培机构
  G = 'G', // G端 - 校园服务
}
