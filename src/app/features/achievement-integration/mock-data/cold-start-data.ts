/**
 * 学员成果模块 - 冷启动数据
 * 用于在没有实际数据时提供示例数据
 */

import {
  Achievement,
  AchievementActivity,
  AchievementProgress,
  AchievementStats,
} from '../models/achievement.model';

/**
 * 示例成果数据
 */
export const MOCK_ACHIEVEMENTS: Achievement[] = [
  {
    id: 1,
    userId: 1001,
    moduleId: 101,
    lessonId: 201,
    type: 'project',
    title: '智能温室监控系统',
    description:
      '使用ESP32和多种传感器构建的温室环境监控系统，能够实时监控温度、湿度、光照等环境参数，并通过MQTT协议上传到云平台。系统支持自动控制通风和浇水，集成Web界面进行远程管理。',
    files: [
      {
        id: 1,
        achievementId: 1,
        fileName: 'greenhouse_system.pdf',
        fileType: 'application/pdf',
        fileSize: 5242880,
        fileUrl: '/mock/greenhouse.pdf',
        thumbnailUrl: '/mock/greenhouse_thumb.jpg',
        uploadedAt: '2026-03-01T10:00:00Z',
      },
      {
        id: 2,
        achievementId: 1,
        fileName: 'source_code.zip',
        fileType: 'application/zip',
        fileSize: 10485760,
        fileUrl: '/mock/greenhouse_code.zip',
        uploadedAt: '2026-03-01T10:05:00Z',
      },
      {
        id: 3,
        achievementId: 1,
        fileName: 'demo_video.mp4',
        fileType: 'video/mp4',
        fileSize: 52428800,
        fileUrl: '/mock/greenhouse_demo.mp4',
        thumbnailUrl: '/mock/greenhouse_video_thumb.jpg',
        uploadedAt: '2026-03-01T10:10:00Z',
      },
    ],
    status: 'approved',
    score: 5,
    feedback:
      '非常优秀的项目！系统设计合理，技术实现完整，文档清晰。特别值得表扬的是云平台集成和远程控制功能，体现了很强的工程能力。',
    reviewedBy: 2001,
    reviewedAt: '2026-03-02T14:30:00Z',
    submittedAt: '2026-03-01T10:00:00Z',
    updatedAt: '2026-03-02T14:30:00Z',
    tags: ['IoT', 'ESP32', 'MQTT', '云平台', '远程控制'],
    isPublic: true,
  },
  {
    id: 2,
    userId: 1002,
    moduleId: 102,
    lessonId: 202,
    type: 'project',
    title: '循迹机器人控制系统',
    description:
      '基于STM32的智能循迹机器人，采用PID控制算法实现精准路径跟踪。系统包含摄像头视觉识别、传感器数据融合、电机控制等模块，支持多种赛道模式。',
    files: [
      {
        id: 4,
        achievementId: 2,
        fileName: 'line_follower_robot.pdf',
        fileType: 'application/pdf',
        fileSize: 4194304,
        fileUrl: '/mock/line_follower.pdf',
        uploadedAt: '2026-03-03T09:00:00Z',
      },
    ],
    status: 'approved',
    score: 4,
    feedback: '项目完成度很高，PID控制算法实现正确。建议进一步优化图像识别的准确性和响应速度。',
    reviewedBy: 2001,
    reviewedAt: '2026-03-04T11:00:00Z',
    submittedAt: '2026-03-03T09:00:00Z',
    updatedAt: '2026-03-04T11:00:00Z',
    tags: ['STM32', 'PID控制', '机器视觉', '机器人'],
    isPublic: true,
  },
  {
    id: 3,
    userId: 1003,
    moduleId: 103,
    lessonId: 203,
    type: 'certificate',
    title: 'Python编程认证证书',
    description:
      '完成Python编程基础课程并通过综合考试，获得认证证书。掌握变量、函数、面向对象编程等核心概念，能够独立开发小型应用程序。',
    files: [
      {
        id: 5,
        achievementId: 3,
        fileName: 'python_certificate.jpg',
        fileType: 'image/jpeg',
        fileSize: 2097152,
        fileUrl: '/mock/python_cert.jpg',
        uploadedAt: '2026-03-05T08:00:00Z',
      },
    ],
    status: 'approved',
    score: 5,
    feedback: '考试表现优秀，编程基础扎实，代码风格规范。',
    reviewedBy: 2002,
    reviewedAt: '2026-03-06T10:00:00Z',
    submittedAt: '2026-03-05T08:00:00Z',
    updatedAt: '2026-03-06T10:00:00Z',
    tags: ['Python', '编程', '认证'],
    isPublic: true,
  },
  {
    id: 4,
    userId: 1004,
    moduleId: 104,
    lessonId: 204,
    type: 'portfolio',
    title: '全栈Web开发作品集',
    description:
      '包含6个完整的Web应用项目，涵盖前端、后端、数据库全栈开发。项目包括电商系统、社交平台、数据可视化仪表板等，采用React、Node.js、MongoDB等技术栈。',
    files: [
      {
        id: 6,
        achievementId: 4,
        fileName: 'portfolio.pdf',
        fileType: 'application/pdf',
        fileSize: 8388608,
        fileUrl: '/mock/portfolio.pdf',
        uploadedAt: '2026-03-07T11:00:00Z',
      },
      {
        id: 7,
        achievementId: 4,
        fileName: 'project_demos.zip',
        fileType: 'application/zip',
        fileSize: 52428800,
        fileUrl: '/mock/portfolio_demos.zip',
        uploadedAt: '2026-03-07T11:05:00Z',
      },
    ],
    status: 'approved',
    score: 5,
    feedback: '作品集质量非常高，项目设计完整，代码规范，用户体验优秀。展现了扎实的全栈开发能力。',
    reviewedBy: 2002,
    reviewedAt: '2026-03-08T14:00:00Z',
    submittedAt: '2026-03-07T11:00:00Z',
    updatedAt: '2026-03-08T14:00:00Z',
    tags: ['全栈开发', 'React', 'Node.js', 'MongoDB', 'Web开发'],
    isPublic: true,
  },
  {
    id: 5,
    userId: 1005,
    moduleId: 105,
    lessonId: 205,
    type: 'project',
    title: '语音控制机器人',
    description:
      '集成了语音识别和自然语言处理的智能机器人，能够通过语音指令执行复杂任务。使用百度语音API和阿里云NLP服务，实现语音到指令的转换和执行。',
    files: [
      {
        id: 8,
        achievementId: 5,
        fileName: 'voice_robot.pdf',
        fileType: 'application/pdf',
        fileSize: 5242880,
        fileUrl: '/mock/voice_robot.pdf',
        uploadedAt: '2026-03-09T10:00:00Z',
      },
    ],
    status: 'approved',
    score: 4,
    feedback: '语音识别集成成功，交互流畅。建议增加更多自然语言理解能力，提升指令识别准确率。',
    reviewedBy: 2001,
    reviewedAt: '2026-03-10T13:00:00Z',
    submittedAt: '2026-03-09T10:00:00Z',
    updatedAt: '2026-03-10T13:00:00Z',
    tags: ['语音识别', 'NLP', 'AI', '机器人', '交互'],
    isPublic: true,
  },
  {
    id: 6,
    userId: 1006,
    moduleId: 106,
    lessonId: 206,
    type: 'case_study',
    title: 'AR增强现实教学系统',
    description:
      '基于ARKit/ARCore开发的增强现实教学应用，通过扫描实物显示3D模型和教学内容。支持多人协作学习，提供沉浸式学习体验。已在中小学进行实地测试，获得师生好评。',
    files: [
      {
        id: 9,
        achievementId: 6,
        fileName: 'ar_education.pdf',
        fileType: 'application/pdf',
        fileSize: 6291456,
        fileUrl: '/mock/ar_education.pdf',
        uploadedAt: '2026-03-11T09:00:00Z',
      },
      {
        id: 10,
        achievementId: 6,
        fileName: 'ar_demo.mp4',
        fileType: 'video/mp4',
        fileSize: 73400320,
        fileUrl: '/mock/ar_demo.mp4',
        thumbnailUrl: '/mock/ar_demo_thumb.jpg',
        uploadedAt: '2026-03-11T09:10:00Z',
      },
    ],
    status: 'approved',
    score: 5,
    feedback: '创新性很强，AR技术应用出色。实地测试数据充分，用户体验设计优秀。极具商业价值！',
    reviewedBy: 2002,
    reviewedAt: '2026-03-12T15:00:00Z',
    submittedAt: '2026-03-11T09:00:00Z',
    updatedAt: '2026-03-12T15:00:00Z',
    tags: ['AR', '增强现实', '教育', 'ARKit', 'ARCore'],
    isPublic: true,
  },
  {
    id: 7,
    userId: 1007,
    moduleId: 107,
    lessonId: 207,
    type: 'project',
    title: '机器学习图像识别系统',
    description:
      '基于TensorFlow和OpenCV开发的图像识别系统，能够识别多种物体和场景。使用CNN卷积神经网络，训练数据集超过10万张图片。系统支持实时识别和批量处理，准确率达到95%以上。',
    files: [
      {
        id: 11,
        achievementId: 7,
        fileName: 'ml_image_recognition.pdf',
        fileType: 'application/pdf',
        fileSize: 7340032,
        fileUrl: '/mock/ml_recognition.pdf',
        uploadedAt: '2026-03-13T10:00:00Z',
      },
      {
        id: 12,
        achievementId: 7,
        fileName: 'model.h5',
        fileType: 'application/octet-stream',
        fileSize: 104857600,
        fileUrl: '/mock/model.h5',
        uploadedAt: '2026-03-13T10:05:00Z',
      },
    ],
    status: 'approved',
    score: 5,
    feedback:
      '深度学习模型设计优秀，准确率出色。项目文档完整，代码质量高，展现了扎实的机器学习功底。',
    reviewedBy: 2001,
    reviewedAt: '2026-03-14T14:00:00Z',
    submittedAt: '2026-03-13T10:00:00Z',
    updatedAt: '2026-03-14T14:00:00Z',
    tags: ['机器学习', 'TensorFlow', 'OpenCV', 'CNN', '图像识别'],
    isPublic: true,
  },
  {
    id: 8,
    userId: 1008,
    moduleId: 108,
    lessonId: 208,
    type: 'assignment',
    title: '电路仿真实验报告',
    description:
      '完成电路设计、仿真分析和实验验证的全流程作业。使用Multisim进行电路仿真，分析电路性能指标，完成实际电路搭建和测试。报告包含详细的设计思路、计算过程和测试数据。',
    files: [
      {
        id: 13,
        achievementId: 8,
        fileName: 'circuit_lab_report.pdf',
        fileType: 'application/pdf',
        fileSize: 3145728,
        fileUrl: '/mock/circuit_report.pdf',
        uploadedAt: '2026-03-15T11:00:00Z',
      },
    ],
    status: 'approved',
    score: 4,
    feedback: '实验报告规范，数据分析详细。建议加强对误差来源的分析和改进建议。',
    reviewedBy: 2002,
    reviewedAt: '2026-03-16T10:00:00Z',
    submittedAt: '2026-03-15T11:00:00Z',
    updatedAt: '2026-03-16T10:00:00Z',
    tags: ['电路设计', '仿真', '实验', 'Multisim'],
    isPublic: true,
  },
];

/**
 * 示例统计数据
 */
export const MOCK_STATS: AchievementStats = {
  totalAchievements: 1234,
  pendingReviews: 45,
  approvedAchievements: 1100,
  rejectedAchievements: 89,
  averageScore: 4.3,
  recentActivity: [
    {
      id: 1,
      achievementId: 8,
      achievementTitle: '电路仿真实验报告',
      type: 'approved',
      userId: 1008,
      userName: '学员1008',
      timestamp: '2026-03-16T10:00:00Z',
    },
    {
      id: 2,
      achievementId: 7,
      achievementTitle: '机器学习图像识别系统',
      type: 'approved',
      userId: 1007,
      userName: '学员1007',
      timestamp: '2026-03-14T14:00:00Z',
    },
    {
      id: 3,
      achievementId: 6,
      achievementTitle: 'AR增强现实教学系统',
      type: 'approved',
      userId: 1006,
      userName: '学员1006',
      timestamp: '2026-03-12T15:00:00Z',
    },
    {
      id: 4,
      achievementId: 5,
      achievementTitle: '语音控制机器人',
      type: 'approved',
      userId: 1005,
      userName: '学员1005',
      timestamp: '2026-03-10T13:00:00Z',
    },
    {
      id: 5,
      achievementId: 4,
      achievementTitle: '全栈Web开发作品集',
      type: 'approved',
      userId: 1004,
      userName: '学员1004',
      timestamp: '2026-03-08T14:00:00Z',
    },
  ],
  byType: {
    project: 450,
    certificate: 280,
    assignment: 320,
    portfolio: 120,
    case_study: 64,
  },
  byStatus: {
    pending: 45,
    approved: 1100,
    rejected: 89,
    revision: 0,
  },
};

/**
 * 示例学习进度数据
 */
export const MOCK_PROGRESS: AchievementProgress = {
  achievementId: 0,
  userId: 1001,
  courseId: 1,
  moduleId: 101,
  lessonId: 201,
  completionPercentage: 85,
  totalAchievements: 20,
  completedAchievements: 17,
  averageScore: 4.6,
  lastUpdated: '2026-03-17T10:00:00Z',
  milestones: [
    {
      id: 1,
      name: '第一阶段：基础入门',
      description: '完成基础课程学习和首个项目',
      achievedAt: '2026-02-01T10:00:00Z',
      achievementIds: [1, 2, 3, 4, 5],
    },
    {
      id: 2,
      name: '第二阶段：进阶提升',
      description: '完成核心模块和多个项目',
      achievedAt: '2026-02-28T10:00:00Z',
      achievementIds: [6, 7, 8, 9, 10, 11, 12],
    },
    {
      id: 3,
      name: '第三阶段：高级应用',
      description: '完成高级课程和综合项目',
      achievedAt: '2026-03-15T10:00:00Z',
      achievementIds: [13, 14, 15, 16, 17],
    },
  ],
};

/**
 * 示例用户进度数据（多用户）
 */
export const MOCK_USER_PROGRESS: Record<number, AchievementProgress> = {
  1001: {
    achievementId: 0,
    userId: 1001,
    courseId: 1,
    completionPercentage: 85,
    totalAchievements: 20,
    completedAchievements: 17,
    averageScore: 4.6,
    lastUpdated: '2026-03-17T10:00:00Z',
    milestones: MOCK_PROGRESS.milestones,
  },
  1002: {
    achievementId: 0,
    userId: 1002,
    courseId: 1,
    completionPercentage: 72,
    totalAchievements: 18,
    completedAchievements: 13,
    averageScore: 4.3,
    lastUpdated: '2026-03-16T10:00:00Z',
    milestones: [
      {
        id: 1,
        name: '第一阶段：基础入门',
        description: '完成基础课程学习和首个项目',
        achievedAt: '2026-02-05T10:00:00Z',
        achievementIds: [20, 21, 22, 23, 24],
      },
      {
        id: 2,
        name: '第二阶段：进阶提升',
        description: '完成核心模块和多个项目',
        achievedAt: '2026-03-10T10:00:00Z',
        achievementIds: [25, 26, 27, 28, 29, 30, 31],
      },
      {
        id: 3,
        name: '第三阶段：高级应用',
        description: '完成高级课程和综合项目',
        achievementIds: [32, 33, 34, 35, 36],
      },
    ],
  },
  1003: {
    achievementId: 0,
    userId: 1003,
    courseId: 2,
    completionPercentage: 90,
    totalAchievements: 10,
    completedAchievements: 9,
    averageScore: 4.8,
    lastUpdated: '2026-03-17T09:00:00Z',
    milestones: [
      {
        id: 1,
        name: 'Python 基础认证',
        description: '完成Python基础课程',
        achievedAt: '2026-03-06T10:00:00Z',
        achievementIds: [40, 41, 42],
      },
      {
        id: 2,
        name: 'Python 进阶认证',
        description: '完成Python进阶课程',
        achievedAt: '2026-03-15T10:00:00Z',
        achievementIds: [43, 44, 45, 46, 47, 48],
      },
    ],
  },
};

/**
 * 示例活动记录
 */
export const MOCK_ACTIVITY: AchievementActivity[] = [
  {
    id: 1,
    achievementId: 8,
    achievementTitle: '电路仿真实验报告',
    type: 'approved',
    userId: 1008,
    userName: '学员1008',
    timestamp: '2026-03-16T10:00:00Z',
  },
  {
    id: 2,
    achievementId: 7,
    achievementTitle: '机器学习图像识别系统',
    type: 'approved',
    userId: 1007,
    userName: '学员1007',
    timestamp: '2026-03-14T14:00:00Z',
  },
  {
    id: 3,
    achievementId: 6,
    achievementTitle: 'AR增强现实教学系统',
    type: 'approved',
    userId: 1006,
    userName: '学员1006',
    timestamp: '2026-03-12T15:00:00Z',
  },
  {
    id: 4,
    achievementId: 5,
    achievementTitle: '语音控制机器人',
    type: 'approved',
    userId: 1005,
    userName: '学员1005',
    timestamp: '2026-03-10T13:00:00Z',
  },
  {
    id: 5,
    achievementId: 4,
    achievementTitle: '全栈Web开发作品集',
    type: 'approved',
    userId: 1004,
    userName: '学员1004',
    timestamp: '2026-03-08T14:00:00Z',
  },
  {
    id: 6,
    achievementId: 1,
    achievementTitle: '智能温室监控系统',
    type: 'submitted',
    userId: 1001,
    userName: '学员1001',
    timestamp: '2026-03-01T10:00:00Z',
  },
  {
    id: 7,
    achievementId: 2,
    achievementTitle: '循迹机器人控制系统',
    type: 'submitted',
    userId: 1002,
    userName: '学员1002',
    timestamp: '2026-03-03T09:00:00Z',
  },
];

/**
 * 用户信息映射
 */
export const MOCK_USERS: Record<number, { name: string; avatar: string }> = {
  1001: { name: '张小明', avatar: 'A' },
  1002: { name: '李小红', avatar: 'B' },
  1003: { name: '王小强', avatar: 'C' },
  1004: { name: '赵小芳', avatar: 'D' },
  1005: { name: '刘小刚', avatar: 'E' },
  1006: { name: '陈小丽', avatar: 'F' },
  1007: { name: '杨小杰', avatar: 'G' },
  1008: { name: '周小梅', avatar: 'H' },
};

/**
 * 冷启动配置
 */
export const COLD_START_CONFIG = {
  enabled: true, // 是否启用冷启动数据
  autoLoad: true, // 自动加载数据
  mockDelay: 500, // 模拟网络延迟（毫秒）
  maxAchievements: 100, // 最大展示成果数
  refreshInterval: 300000, // 数据刷新间隔（5分钟）
};

/**
 * 获取分页的成果数据
 */
export function getMockAchievements(
  page: number = 1,
  pageSize: number = 10,
  filter?: { status?: string[]; type?: string[] }
): { data: Achievement[]; total: number } {
  let filtered = [...MOCK_ACHIEVEMENTS];

  // 应用状态筛选
  if (filter?.status && filter.status.length > 0) {
    filtered = filtered.filter((a) => filter.status!.includes(a.status));
  }

  // 应用类型筛选
  if (filter?.type && filter.type.length > 0) {
    filtered = filtered.filter((a) => filter.type!.includes(a.type));
  }

  const total = filtered.length;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const data = filtered.slice(start, end);

  return { data, total };
}

/**
 * 获取模拟统计数据
 */
export function getMockStats(): AchievementStats {
  return { ...MOCK_STATS };
}

/**
 * 获取用户进度
 */
export function getUserProgress(userId: number): AchievementProgress | null {
  return MOCK_USER_PROGRESS[userId] || null;
}

/**
 * 获取最近活动
 */
export function getRecentActivity(limit: number = 10): AchievementActivity[] {
  return MOCK_ACTIVITY.slice(0, limit);
}

/**
 * 模拟API延迟
 */
export function mockApiDelay<T>(data: T, delay: number = COLD_START_CONFIG.mockDelay): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delay);
  });
}
