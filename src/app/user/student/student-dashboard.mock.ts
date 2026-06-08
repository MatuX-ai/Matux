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
  const now = new Date().toISOString();
  return [
    createMockLearningSource(
      1,
      1,
      '校本部',
      'school_curriculum',
      true,
      '2025-09-01',
      '2026-07-31'
    ),
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
}

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
