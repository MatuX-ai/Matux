/**
 * Admin 管理后台菜单配置
 *
 * 定义所有可用的菜单项，用于统一导航和权限控制
 */

export interface MenuItem {
  /** 菜单唯一标识，用于权限匹配 */
  id: string;
  /** 菜单显示文本 */
  title: string;
  /** Material Icon 图标名称 */
  icon: string;
  /** 路由路径 */
  route: string;
  /** 可选：子菜单项 */
  children?: MenuItem[];
  /** 可选：权限标识，为空则所有人可见 */
  permission?: string;
}

/**
 * 主菜单配置
 * 按功能模块分组排列
 */
export const ADMIN_MENU_ITEMS: MenuItem[] = [
  // 核心功能
  {
    id: 'dashboard',
    title: '仪表板',
    icon: 'dashboard',
    route: '/admin/dashboard',
  },
  {
    id: 'users',
    title: '用户管理',
    icon: 'people',
    route: '/admin/users',
  },

  // 资源管理
  {
    id: 'licenses',
    title: '许可证管理',
    icon: 'vpn_key',
    route: '/admin/licenses',
  },
  // {
  //   id: 'organizations',
  //   title: '机构管理',
  //   icon: 'business',
  //   route: '/admin/organizations',
  // },  // 已解耦到 OpenMTEduInst 项目
  {
    id: 'materials',
    title: '课件库管理',
    icon: 'folder',
    route: '/admin/materials',
  },
  {
    id: 'courses',
    title: '课程库管理',
    icon: 'school',
    route: '/admin/courses',
  },

  // 财务管理
  {
    id: 'payments',
    title: '支付管理',
    icon: 'payment',
    route: '/admin/payments',
  },
  {
    id: 'sponsorship',
    title: '赞助管理',
    icon: 'handshake',
    route: '/admin/sponsorship',
  },

  // 数据中心
  {
    id: 'database-registry',
    title: '数据中心',
    icon: 'storage',
    route: '/admin/database-registry',
  },
  {
    id: 'marketing',
    title: '营销数据',
    icon: 'analytics',
    route: '/admin/marketing',
  },
  {
    id: 'api-settings',
    title: 'API 设置',
    icon: 'settings_ethernet',
    route: '/admin/api-settings',
  },
  {
    id: 'api-docs',
    title: 'API 文档',
    icon: 'description',
    route: '/admin/api-docs',
  },
];

/**
 * 菜单分组配置 (可选)
 * 用于在侧边栏中按组显示菜单项
 */
export const MENU_GROUPS: {
  title: string;
  items: string[]; // 菜单项 ID 列表
}[] = [
  {
    title: '核心功能',
    items: ['dashboard', 'users'],
  },
  {
    title: '资源管理',
    items: ['licenses', 'materials', 'courses'], // organizations 已解耦到 OpenMTEduInst 项目
  },
  {
    title: '财务管理',
    items: ['payments', 'sponsorship'],
  },
  {
    title: '数据中心',
    items: ['database-registry', 'marketing', 'api-settings', 'api-docs'],
  },
];
