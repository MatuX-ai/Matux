/* eslint-disable max-lines-per-function */
/**
 * 学生仪表板 Mock 数据
 * 用于开发/测试环境
 */

import type {
  LearningSource,
  LearningSourceType,
  UnifiedProgressStats,
} from '../../models/multi-source-learning.models';
import type { CourseEnrollment, UnifiedCourse } from '../../models/unified-course.models';

/**
 * Mock 学习进度统计
 */
export function getMockProgressStats(): UnifiedProgressStats {
  return {
    total_courses: 5,
    completed_courses: 2,
    in_progress_courses: 3,
    total_time_minutes: 1250,
    average_score: 85.5,
    source_breakdown: [
      {
        source_type: 'school_curriculum' as LearningSourceType,
        source_name: '校本部',
        courses: 2,
        completed: 1,
        avg_score: 88,
        total_time: 600,
      },
      {
        source_type: 'school_interest' as LearningSourceType,
        source_name: '校内兴趣班',
        courses: 1,
        completed: 0,
        avg_score: null,
        total_time: 150,
      },
      {
        source_type: 'institution' as LearningSourceType,
        source_name: '创新机器人培训中心',
        courses: 2,
        completed: 1,
        avg_score: 83,
        total_time: 500,
      },
    ],
  };
}

/**
 * Mock 学习来源数据
 */
export function getMockLearningSources(): LearningSource[] {
  // const now = new Date().toISOString(); // 预留时间戳
  return [
    createMockLearningSource(1, 1, '校本部', 'school_curriculum', true, '2025-09-01', '2026-07-31'),
    createMockLearningSource(
      2,
      2,
      '创新机器人培训中心',
      'institution',
      false,
      '2025-10-15',
      '2026-06-30'
    ),
    createMockLearningSource(
      3,
      1,
      '校内兴趣班',
      'school_interest',
      false,
      '2025-11-01',
      '2026-05-31'
    ),
  ];
}

/**
 * 创建单个 Mock 学习来源
 */
export function createMockLearningSource(
  id: number,
  userId: number,
  name: string,
  sourceType: LearningSourceType,
  isPrimary: boolean,
  startDate: string,
  endDate: string
): LearningSource {
  const now = new Date().toISOString();
  return {
    id,
    user_id: userId,
    org_id: id === 2 ? 2 : 1,
    name,
    source_type: sourceType,
    status: 'active',
    is_primary: isPrimary,
    is_active: true,
    role: 'student',
    source_detail: {},
    start_date: startDate,
    end_date: endDate,
    notes: null,
    created_at: now,
    updated_at: now,
  };
}

/**
 * Mock 已报名课程
 */
export function getMockEnrolledCourses(): Array<{
  course: UnifiedCourse;
  progress: number;
  enrollment: CourseEnrollment;
}> {
  return [
    {
      course: {
        id: 1,
        org_id: 1,
        title: '机器人基础入门',
        description: '学习机器人基础知识',
        cover_image_url: null,
        category: 'robotics',
        difficulty: 'beginner',
        duration_minutes: 1200,
        status: 'published',
        source_type: 'school_curriculum',
        teacher_name: '李老师',
        tags: ['机器人', '入门'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      progress: 75,
      enrollment: {
        id: 1,
        user_id: 1,
        course_id: 1,
        org_id: 1,
        progress_percentage: 75,
        score: null,
        status: 'active',
        enrolled_at: new Date().toISOString(),
        completed_at: null,
      },
    },
  ];
}

/**
 * Mock 推荐课程
 */
export function getMockRecommendedCourses(): UnifiedCourse[] {
  return [
    {
      id: 10,
      org_id: 1,
      title: 'ROS机器人操作系统',
      description: '学习 ROS 机器人操作系统的核心概念',
      cover_image_url: null,
      category: 'robotics',
      difficulty: 'advanced',
      duration_minutes: 2400,
      status: 'published',
      source_type: 'online_platform',
      teacher_name: '张博士',
      tags: ['ROS', '机器人', '高级'],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 11,
      org_id: 1,
      title: '深度学习与计算机视觉',
      description: '掌握深度学习算法在计算机视觉中的应用',
      cover_image_url: null,
      category: 'ai',
      difficulty: 'intermediate',
      duration_minutes: 2100,
      status: 'published',
      source_type: 'online_platform',
      teacher_name: '王教授',
      tags: ['深度学习', '计算机视觉', 'AI'],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];
}

/**
 * Mock 成就徽章
 */
export interface MockAchievementBadge {
  id: string;
  name: string;
  icon: string;
  description: string;
  unlocked: boolean;
  unlockedDate?: string;
  streak_days?: number;
}

// eslint-disable-next-line max-lines-per-function

export function getMockAchievementBadges(): MockAchievementBadge[] {
  return [
    {
      id: 'first-lesson',
      name: '初入编程',
      icon: '🎓',
      description: '完成第一个课程',
      unlocked: true,
      unlockedDate: '2026-01-15',
    },
    {
      id: 'first-code',
      name: '代码新手',
      icon: '💻',
      description: '编写第一行代码',
      unlocked: true,
      unlockedDate: '2026-01-20',
    },
    {
      id: 'python-start',
      name: 'Python入门',
      icon: '🐍',
      description: '完成 Python 基础课程',
      unlocked: true,
      unlockedDate: '2026-02-20',
    },
    {
      id: 'streak-7',
      name: '坚持7天',
      icon: '🔥',
      description: '连续学习7天',
      unlocked: true,
      unlockedDate: '2026-03-01',
    },
    {
      id: 'quiz-master',
      name: '测验达人',
      icon: '📝',
      description: '5次测验获得满分',
      unlocked: true,
      unlockedDate: '2026-03-15',
    },
    {
      id: 'blockly-pro',
      name: '积木高手',
      icon: '🧩',
      description: '完成10个Blockly关卡',
      unlocked: true,
      unlockedDate: '2026-04-01',
    },
    {
      id: 'first-debug',
      name: 'Bug猎手',
      icon: '🔧',
      description: '独立修复3个错误',
      unlocked: true,
      unlockedDate: '2026-04-05',
    },
    {
      id: 'streak-30',
      name: '30天坚持',
      icon: '🏆',
      description: '连续学习30天',
      unlocked: true,
      unlockedDate: '2026-04-28',
    },
    {
      id: 'circuit-master',
      name: '电路大师',
      icon: '⚡',
      description: '完成所有电路实验',
      unlocked: false,
    },
    {
      id: 'ai-pioneer',
      name: 'AI先锋',
      icon: '🤖',
      description: '完成AI编程课程',
      unlocked: false,
    },
    {
      id: 'project-10',
      name: '项目达人',
      icon: '🚀',
      description: '完成10个项目',
      unlocked: false,
    },
    {
      id: 'streak-100',
      name: '百日传说',
      icon: '💎',
      description: '连续学习100天',
      unlocked: false,
    },
  ];
}

/* ============================================================================
 * 游戏化扩展 Mock 数据（PRD 学生仪表板重构）
 * ========================================================================== */

/**
 * 成就稀有度等级
 */
export type BadgeRarity = 'common' | 'rare' | 'epic' | 'legendary';

/**
 * 扩展成就徽章（含稀有度、积分值）
 */
export interface ExtendedAchievementBadge extends MockAchievementBadge {
  rarity: BadgeRarity;
  pointValue: number;
}

/**
 * 用户等级
 */
export interface MockUserLevel {
  current: number;
  title: string;
  exp: number;
  expToNext: number;
  totalExp: number;
  expProgressPercent: number;
}

/**
 * 本周学习统计
 */
export interface MockWeeklyStats {
  hoursThisWeek: number;
  tasksCount: number;
  pointsEarned: number;
  streakDays: number;
  weekComparison: {
    hoursChange: number;
    tasksChange: number;
    pointsChange: number;
  };
}

/**
 * 每日任务
 */
export interface MockDailyTask {
  id: string;
  title: string;
  description: string;
  icon: string;
  rewardExp: number;
  rarity: BadgeRarity;
  completed: boolean;
  progress?: { current: number; total: number };
  category: 'course' | 'ai' | 'quiz' | 'project' | 'streak';
  actionRoute?: string;
}

/**
 * 排行榜条目
 */
export interface MockLeaderboardEntry {
  rank: number;
  userId: number;
  username: string;
  avatar?: string;
  totalExp: number;
  weeklyChange: number;
  rankChange: number;
  isCurrentUser: boolean;
}

/**
 * Mock 用户等级（Lv.5 探索者）
 */
export function getMockLevel(): MockUserLevel {
  return {
    current: 5,
    title: '探索者',
    exp: 1200,
    expToNext: 2000,
    totalExp: 6200,
    expProgressPercent: 60,
  };
}

/**
 * Mock 本周学习统计
 */
export function getMockWeeklyStats(): MockWeeklyStats {
  return {
    hoursThisWeek: 12.5,
    tasksCount: 8,
    pointsEarned: 85,
    streakDays: 12,
    weekComparison: {
      hoursChange: 2.3,
      tasksChange: 2,
      pointsChange: 15,
    },
  };
}

/**
 * Mock 每日任务（5 个，含稀有度、完成态、奖励）
 */
export function getMockDailyTasks(): MockDailyTask[] {
  return [
    {
      id: 'task-complete-lesson',
      title: '完成 1 节课程',
      description: '任意课程学习 1 章节',
      icon: 'school',
      rewardExp: 20,
      rarity: 'common',
      completed: true,
      progress: { current: 1, total: 1 },
      category: 'course',
      actionRoute: '/user/courses',
    },
    {
      id: 'task-ai-chat',
      title: 'AI 对话 3 次',
      description: '与 AI 老师互动 3 次',
      icon: 'chat',
      rewardExp: 30,
      rarity: 'common',
      completed: true,
      progress: { current: 3, total: 3 },
      category: 'ai',
      actionRoute: '/ai-edu/coding',
    },
    {
      id: 'task-quiz',
      title: '完成 1 个测试',
      description: '任意课程小测',
      icon: 'quiz',
      rewardExp: 50,
      rarity: 'rare',
      completed: false,
      category: 'quiz',
      actionRoute: '/user/courses',
    },
    {
      id: 'task-submit-project',
      title: '提交 1 个项目',
      description: '上传作品到课件库',
      icon: 'upload_file',
      rewardExp: 100,
      rarity: 'epic',
      completed: false,
      category: 'project',
      actionRoute: '/user/materials',
    },
    {
      id: 'task-streak-week',
      title: '连续学习 7 天',
      description: '距离目标还差 2 天',
      icon: 'local_fire_department',
      rewardExp: 200,
      rarity: 'legendary',
      completed: false,
      progress: { current: 5, total: 7 },
      category: 'streak',
    },
  ];
}

/**
 * Mock 同班排行榜（top 5）
 */
export function getMockLeaderboard(): MockLeaderboardEntry[] {
  return [
    {
      rank: 1,
      userId: 1,
      username: '小明（我）',
      totalExp: 1250,
      weeklyChange: 85,
      rankChange: 1,
      isCurrentUser: true,
    },
    {
      rank: 2,
      userId: 2,
      username: '小红',
      totalExp: 1180,
      weeklyChange: 60,
      rankChange: 0,
      isCurrentUser: false,
    },
    {
      rank: 3,
      userId: 3,
      username: '小华',
      totalExp: 1050,
      weeklyChange: 45,
      rankChange: 2,
      isCurrentUser: false,
    },
    {
      rank: 4,
      userId: 4,
      username: '小丽',
      totalExp: 980,
      weeklyChange: 30,
      rankChange: -1,
      isCurrentUser: false,
    },
    {
      rank: 5,
      userId: 5,
      username: '小龙',
      totalExp: 920,
      weeklyChange: 25,
      rankChange: 0,
      isCurrentUser: false,
    },
  ];
}

/**
 * 获取扩展成就徽章（带稀有度、积分值）
 */
export function getExtendedAchievementBadges(): ExtendedAchievementBadge[] {
  return getMockAchievementBadges().map((badge) => {
    // 根据徽章语义分配稀有度
    const legendaryIds = ['streak-100'];
    const epicIds = ['circuit-master', 'ai-pioneer', 'project-10'];
    const rareIds = ['streak-30', 'blockly-pro', 'quiz-master'];

    let rarity: BadgeRarity = 'common';
    if (legendaryIds.includes(badge.id)) rarity = 'legendary';
    else if (epicIds.includes(badge.id)) rarity = 'epic';
    else if (rareIds.includes(badge.id)) rarity = 'rare';

    return {
      ...badge,
      rarity,
      pointValue: rarity === 'legendary' ? 200 : rarity === 'epic' ? 100 : rarity === 'rare' ? 50 : 20,
    };
  });
}
