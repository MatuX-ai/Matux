/**
 * iMato 学习端自动化测试 - 测试配置
 *
 * 集中管理测试账号、页面定义、校验规则和运行参数
 */

const path = require('path');

// ==================== 测试账号 ====================

const TEST_ACCOUNTS = {
  student: {
    username: 'test_student',
    password: 'TestStudent123!',
    role: '学生',
    description: '学习体验权限',
  },
  teacher: {
    username: 'test_teacher',
    password: 'TestTeacher123!',
    role: '教师',
    description: '教学管理权限',
  },
  admin: {
    username: 'test_admin',
    password: 'TestAdmin123!',
    role: '管理员',
    description: '完整管理权限',
  },
};

// 默认使用学生账号
const DEFAULT_ACCOUNT = TEST_ACCOUNTS.student;

// ==================== 环境配置 ====================

const rawFrontend = process.env.FRONTEND_URL || 'app://./index.html';

const ENVIRONMENT = {
  // 前端地址（开发模式 ng serve 或 生产模式 app:// 协议）
  frontendUrl: rawFrontend,
  // 【修复】独立 API 基础地址，autoLogin 直连后端不走前端 url
  apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
  // 【新增】协议模式：'app' | 'http'，引擎据此分支决定是否探测 dev server
  protocolMode: rawFrontend.startsWith('app://') ? 'app' : 'http',
  // 后端健康检查地址
  backendHealthUrl: process.env.BACKEND_HEALTH_URL || 'http://localhost:8000/health',
  // 后端启动等待超时（毫秒）
  backendTimeout: 60000,
  // 页面加载超时
  pageLoadTimeout: 30000,
  // 元素等待超时
  elementTimeout: 10000,
  // 操作间隔（毫秒），避免请求过快
  actionDelay: 800,
  // 截图目录
  screenshotDir: path.join(__dirname, '..', '..', 'test-results', 'auto-test', 'screenshots'),
  // 报告输出目录
  reportDir: path.join(__dirname, '..', '..', 'test-results', 'auto-test'),
  // 日志文件路径
  logFile: path.join(__dirname, '..', '..', 'test-results', 'auto-test', 'test-execution.log'),
};

// ==================== 页面定义 ====================

/**
 * 每个页面的校验规则：
 * - path: 路由路径
 * - name: 页面中文名称
 * - description: 页面描述
 * - requiredElements: 必须存在的元素选择器（CSS）
 * - optionalElements: 建议存在的元素（不阻塞测试）
 * - interactionTests: 交互测试步骤
 * - skipIfModuleInactive: 如果模块未激活则跳过
 * - moduleName: 对应后端模块名（用于检查激活状态）
 */
const PAGES = [
  // ========== 认证页面 ==========
  {
    path: '/auth/login',
    name: '登录页',
    description: '用户登录入口',
    requiredElements: [
      { selector: '.login-card', description: '登录卡片' },
      { selector: 'input[type="email"], input[name="email"]', description: '邮箱输入框' },
      { selector: 'input[name="password"]', description: '密码输入框' },
      { selector: 'button.login-button', description: '登录按钮' },
    ],
    optionalElements: [
      { selector: '.test-login-button', description: '测试账号一键登录按钮' },
      { selector: '.oauth-buttons', description: 'OAuth 第三方登录' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },

  // ========== 用户中心页面 ==========
  {
    path: '/user/dashboard',
    name: '学生仪表板',
    description: '学生学习数据总览',
    requiredElements: [
      { selector: 'app-student-dashboard, app-user-page-layout', description: '仪表板组件' },
    ],
    optionalElements: [
      { selector: '.stats-card, .dashboard-card', description: '统计卡片' },
      { selector: '.learning-source-progress, app-learning-source-progress', description: '学习来源进度组件' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/profile',
    name: '个人资料',
    description: '用户个人信息管理',
    requiredElements: [
      { selector: 'app-user-profile, app-user-page-layout', description: '个人资料组件' },
    ],
    optionalElements: [
      { selector: 'form, .profile-form', description: '资料表单' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/courses',
    name: '我的课程',
    description: '已注册课程列表',
    requiredElements: [
      { selector: 'app-my-courses, app-user-page-layout', description: '课程列表组件' },
    ],
    optionalElements: [
      { selector: '.course-card, .course-list, .course-grid', description: '课程卡片/列表' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/achievements',
    name: '成就系统',
    description: '学习成就与徽章',
    requiredElements: [
      { selector: 'app-achievements, app-user-page-layout', description: '成就组件' },
    ],
    optionalElements: [
      { selector: '.achievement-card, .badge-grid', description: '成就/徽章卡片' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/learning-profile',
    name: '学习画像',
    description: '个人学习数据分析',
    requiredElements: [
      { selector: 'app-learning-profile, app-user-page-layout', description: '学习画像组件' },
    ],
    optionalElements: [],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/growth-trajectory',
    name: '成长轨迹',
    description: '跨学期学习轨迹',
    requiredElements: [
      { selector: 'app-growth-trajectory-page, app-user-page-layout', description: '成长轨迹组件' },
    ],
    optionalElements: [
      { selector: '.trajectory-chart, canvas, svg', description: '轨迹图表' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/reports',
    name: '学习报告',
    description: '学习报告与数据分析',
    requiredElements: [
      { selector: 'app-learning-reports, app-user-page-layout', description: '学习报告组件' },
    ],
    optionalElements: [
      { selector: '.report-card, .chart-container', description: '报告卡片/图表' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },
  {
    path: '/user/emotional-companion',
    name: '情感陪伴',
    description: 'AI 情感陪伴对话',
    requiredElements: [
      { selector: 'app-emotional-companion, app-user-page-layout', description: '情感陪伴组件' },
    ],
    optionalElements: [
      { selector: '.chat-container, .chat-input, textarea', description: '聊天界面' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },

  // ========== AI 教育模块 ==========
  {
    path: '/ai-edu/dashboard',
    name: 'AI 编程教育',
    description: 'AI 辅助编程学习平台',
    requiredElements: [
      { selector: 'app-ai-edu-feature, app-ai-edu-dashboard', description: 'AI 教育组件' },
    ],
    optionalElements: [
      { selector: '.course-card, .lesson-list', description: '课程/课时列表' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },

  // ========== OpenSciEDU ==========
  {
    path: '/opensciedu',
    name: 'OpenSciEDU 公共课程',
    description: '开源科学教育课程',
    requiredElements: [
      { selector: 'app-opensciedu-page', description: 'OpenSciEDU 组件' },
    ],
    optionalElements: [
      { selector: 'mat-tab-group', description: '课程/图谱 Tab' },
      { selector: '.course-card, .course-grid', description: '课程卡片' },
    ],
    interactionTests: [
      {
        name: '切换到知识图谱 Tab',
        action: 'click',
        selector: '.mat-mdc-tab:has-text("知识图谱")',
        expectSelector: 'app-opensciedu-graph',
      },
    ],
    skipIfModuleInactive: false,
  },

  // ========== 离线模式 ==========
  {
    path: '/offline-mode',
    name: '离线模式',
    description: '离线学习与同步',
    requiredElements: [
      { selector: 'app-offline-mode, app-offline-dashboard, .offline-dashboard', description: '离线模式组件' },
    ],
    optionalElements: [
      { selector: '.sync-status, .offline-indicator', description: '同步状态' },
    ],
    interactionTests: [],
    skipIfModuleInactive: false,
  },

  // ========== 以下为模块控制页面（可能未激活） ==========
  {
    path: '/ar-lab',
    name: 'AR 实验室',
    description: '增强现实实验环境',
    requiredElements: [
      { selector: 'app-ar-lab', description: 'AR 实验室组件' },
    ],
    optionalElements: [
      { selector: 'canvas', description: 'AR 渲染画布' },
    ],
    interactionTests: [],
    skipIfModuleInactive: true,
    moduleName: 'ar_lab',
  },
  {
    path: '/exam',
    name: '考试系统',
    description: '在线考试与测评',
    requiredElements: [
      { selector: 'app-exam, app-exam-list, .exam-list, .exam-container', description: '考试系统组件' },
    ],
    optionalElements: [
      { selector: '.exam-list, .exam-card', description: '考试列表' },
    ],
    interactionTests: [],
    skipIfModuleInactive: true,
    moduleName: 'exam',
  },
  {
    path: '/content-store',
    name: '内容商店',
    description: '学习资源商店',
    requiredElements: [
      { selector: 'app-content-store, app-store-home, .store-container', description: '内容商店组件' },
    ],
    optionalElements: [
      { selector: '.store-card, .resource-grid', description: '资源卡片' },
    ],
    interactionTests: [],
    skipIfModuleInactive: true,
    moduleName: 'content_store',
  },
  {
    path: '/creativity-engine',
    name: '创意引擎',
    description: '创意编程与项目制作',
    requiredElements: [
      { selector: 'app-creativity-engine', description: '创意引擎组件' },
    ],
    optionalElements: [],
    interactionTests: [],
    skipIfModuleInactive: true,
    moduleName: 'creativity',
  },
  {
    path: '/digital-twin-lab',
    name: '数字孪生实验室',
    description: '数字孪生仿真实验',
    requiredElements: [
      { selector: 'app-digital-twin-lab', description: '数字孪生组件' },
    ],
    optionalElements: [
      { selector: 'canvas, .scene-container', description: '3D 渲染区域' },
    ],
    interactionTests: [],
    skipIfModuleInactive: true,
    moduleName: 'digital_twin',
  },
  {
    path: '/vircadia',
    name: 'Vircadia 虚拟世界',
    description: '虚拟现实学习空间',
    requiredElements: [
      { selector: 'app-vircadia', description: 'Vircadia 组件' },
    ],
    optionalElements: [],
    interactionTests: [],
    skipIfModuleInactive: true,
    moduleName: 'ar_vr',
  },
];

// ==================== 导出 ====================

module.exports = {
  TEST_ACCOUNTS,
  DEFAULT_ACCOUNT,
  ENVIRONMENT,
  PAGES,
};
