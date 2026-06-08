/**
 * OpenSciEDU 模拟数据服务
 *
 * 【临时方案】当 Neo4j 不可用时，提供内置模拟数据用于开发测试
 * - 确保 OpenSciEDU 页面可以正常展示和交互
 *
 * 【Neo4j 问题说明】
 *  当前 OpenMTSciEd 后端使用 Neo4j Aura 云服务，存在 DNS 解析不稳定问题:
 *  - 错误: ENOTFOUND 4abd5ef9.databases.neo4j.io
 *  - 根因: Neo4j Aura 云数据库 DNS 解析失败
 *
 * 【解决方案】部署到自有 Neo4j 服务器后:
 *  1. 在 OpenMTSciEd 后端设置环境变量:
 *     NEO4J_URI=bolt://your-neo4j-server:7687
 *     NEO4J_USERNAME=neo4j
 *     NEO4J_PASSWORD=your-secure-password
 *  2. 参考: g:\OpenMTSciEd\backend-next\lib\neo4j.ts
 *  3. 移除本模拟服务的降级逻辑
 */

import { Injectable } from '@angular/core';
import { Observable, of, delay } from 'rxjs';
import {
  CourseCategory,
  CourseInstructor,
  CourseChapter,
  CourseLesson,
  PublicCourse,
  CourseListResponse,
  CourseDetail,
  KnowledgeNode,
  KnowledgeEdge,
  KnowledgeGraphData,
  SearchResult,
} from './opensciedu.service';


/**
 * 内置模拟课程数据
 */
const MOCK_CATEGORIES: CourseCategory[] = [
  { id: 'programming', name: '编程入门', icon: 'code', description: '零基础学习编程' },
  { id: 'algorithm', name: '算法与数据结构', icon: 'psychology', description: '算法思维训练' },
  { id: 'web', name: 'Web 开发', icon: 'web', description: '前端与后端技术' },
  { id: 'ai', name: '人工智能', icon: 'smart_toy', description: 'AI 与机器学习' },
  { id: 'science', name: '科学实验', icon: 'science', description: '跨学科科学探索' },
];

const MOCK_INSTRUCTORS: CourseInstructor[] = [
  { id: 't1', name: '李老师', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=t1', title: '资深编程讲师' },
  { id: 't2', name: '王博士', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=t2', title: 'AI 算法专家' },
  { id: 't3', name: '张工程师', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=t3', title: '全栈开发工程师' },
];

const MOCK_COURSES: PublicCourse[] = [
  {
    id: 'c001',
    title: 'Python 编程入门',
    description: '从零开始学习 Python 编程，掌握基本语法和编程思维。通过趣味实例激发学习兴趣。',
    coverImage: 'https://picsum.photos/seed/python/400/225',
    category: MOCK_CATEGORIES[0],
    instructor: MOCK_INSTRUCTORS[0],
    difficulty: 'beginner',
    durationMinutes: 480,
    lessonCount: 24,
    studentCount: 12580,
    rating: 4.8,
    tags: ['Python', '编程入门', '青少年'],
    createdAt: '2024-01-15T08:00:00Z',
    updatedAt: '2024-06-01T10:30:00Z',
    isFree: true,
    certificateAvailable: true,
  },
  {
    id: 'c002',
    title: 'JavaScript 互动编程',
    description: '学习 JavaScript 实现网页互动效果，从按钮点击到动画制作。',
    coverImage: 'https://picsum.photos/seed/javascript/400/225',
    category: MOCK_CATEGORIES[2],
    instructor: MOCK_INSTRUCTORS[2],
    difficulty: 'beginner',
    durationMinutes: 360,
    lessonCount: 18,
    studentCount: 8960,
    rating: 4.6,
    tags: ['JavaScript', 'Web', '互动'],
    createdAt: '2024-02-01T09:00:00Z',
    updatedAt: '2024-06-05T14:20:00Z',
    isFree: true,
    certificateAvailable: false,
  },
  {
    id: 'c003',
    title: 'Scratch 游戏制作',
    description: '使用 Scratch 可视化编程工具，制作自己的小游戏，培养逻辑思维。',
    coverImage: 'https://picsum.photos/seed/scratch/400/225',
    category: MOCK_CATEGORIES[0],
    instructor: MOCK_INSTRUCTORS[0],
    difficulty: 'beginner',
    durationMinutes: 240,
    lessonCount: 12,
    studentCount: 15800,
    rating: 4.9,
    tags: ['Scratch', '游戏', '可视化编程'],
    createdAt: '2023-11-20T08:00:00Z',
    updatedAt: '2024-05-28T16:45:00Z',
    isFree: true,
    certificateAvailable: false,
  },
  {
    id: 'c004',
    title: '算法入门：排序与搜索',
    description: '学习基础算法，理解排序和搜索的原理，培养问题解决能力。',
    coverImage: 'https://picsum.photos/seed/algorithm/400/225',
    category: MOCK_CATEGORIES[1],
    instructor: MOCK_INSTRUCTORS[1],
    difficulty: 'intermediate',
    durationMinutes: 420,
    lessonCount: 21,
    studentCount: 5630,
    rating: 4.7,
    tags: ['算法', '排序', '搜索'],
    createdAt: '2024-03-10T10:00:00Z',
    updatedAt: '2024-06-02T11:15:00Z',
    isFree: true,
    certificateAvailable: true,
  },
  {
    id: 'c005',
    title: 'HTML/CSS 网页设计',
    description: '学习网页结构与样式设计，从零开始构建精美网页。',
    coverImage: 'https://picsum.photos/seed/htmlcss/400/225',
    category: MOCK_CATEGORIES[2],
    instructor: MOCK_INSTRUCTORS[2],
    difficulty: 'beginner',
    durationMinutes: 300,
    lessonCount: 15,
    studentCount: 11200,
    rating: 4.5,
    tags: ['HTML', 'CSS', '网页设计'],
    createdAt: '2024-01-25T08:30:00Z',
    updatedAt: '2024-05-30T09:00:00Z',
    isFree: true,
    certificateAvailable: false,
  },
  {
    id: 'c006',
    title: 'AI 探索：机器学习基础',
    description: '了解人工智能和机器学习的基本概念，体验 AI 的魅力。',
    coverImage: 'https://picsum.photos/seed/machinelearning/400/225',
    category: MOCK_CATEGORIES[3],
    instructor: MOCK_INSTRUCTORS[1],
    difficulty: 'intermediate',
    durationMinutes: 540,
    lessonCount: 27,
    studentCount: 4280,
    rating: 4.8,
    tags: ['AI', '机器学习', 'Python'],
    createdAt: '2024-04-05T11:00:00Z',
    updatedAt: '2024-06-03T15:30:00Z',
    isFree: false,
    certificateAvailable: true,
  },
  {
    id: 'c007',
    title: 'Arduino 电子制作',
    description: '通过 Arduino 开发板学习电子电路和编程控制。',
    coverImage: 'https://picsum.photos/seed/arduino/400/225',
    category: MOCK_CATEGORIES[4],
    instructor: MOCK_INSTRUCTORS[2],
    difficulty: 'intermediate',
    durationMinutes: 480,
    lessonCount: 24,
    studentCount: 3450,
    rating: 4.6,
    tags: ['Arduino', '电子', '物联网'],
    createdAt: '2024-02-15T09:30:00Z',
    updatedAt: '2024-05-25T10:45:00Z',
    isFree: true,
    certificateAvailable: true,
  },
  {
    id: 'c008',
    title: '数据结构：树与图',
    description: '深入学习树和图结构，掌握高级数据结构。',
    coverImage: 'https://picsum.photos/seed/datastructure/400/225',
    category: MOCK_CATEGORIES[1],
    instructor: MOCK_INSTRUCTORS[1],
    difficulty: 'advanced',
    durationMinutes: 600,
    lessonCount: 30,
    studentCount: 2890,
    rating: 4.7,
    tags: ['数据结构', '树', '图'],
    createdAt: '2024-05-01T10:00:00Z',
    updatedAt: '2024-06-04T12:00:00Z',
    isFree: false,
    certificateAvailable: true,
  },
];

const MOCK_KNOWLEDGE_GRAPH: KnowledgeGraphData = {
  nodes: [
    { id: 'k001', name: '编程基础', category: 'programming', level: 0, description: '编程入门知识', courseCount: 5, positionX: 400, positionY: 100 },
    { id: 'k002', name: '变量与数据类型', category: 'programming', level: 1, description: '基本数据概念', courseCount: 4, positionX: 250, positionY: 200 },
    { id: 'k003', name: '控制流程', category: 'programming', level: 1, description: '条件与循环', courseCount: 4, positionX: 400, positionY: 200 },
    { id: 'k004', name: '函数', category: 'programming', level: 1, description: '代码复用', courseCount: 3, positionX: 550, positionY: 200 },
    { id: 'k005', name: '算法思维', category: 'algorithm', level: 1, description: '问题解决能力', courseCount: 3, positionX: 400, positionY: 300 },
    { id: 'k006', name: '排序算法', category: 'algorithm', level: 2, description: '经典排序', courseCount: 2, positionX: 250, positionY: 380 },
    { id: 'k007', name: '搜索算法', category: 'algorithm', level: 2, description: '查找技术', courseCount: 2, positionX: 400, positionY: 380 },
    { id: 'k008', name: '数据结构', category: 'algorithm', level: 2, description: '数据组织', courseCount: 2, positionX: 550, positionY: 380 },
    { id: 'k009', name: 'Web 开发', category: 'web', level: 1, description: '网页技术', courseCount: 3, positionX: 700, positionY: 300 },
    { id: 'k010', name: '人工智能', category: 'ai', level: 2, description: 'AI 与 ML', courseCount: 2, positionX: 700, positionY: 200 },
  ],
  edges: [
    { source: 'k001', target: 'k002', relationType: 'prerequisite' },
    { source: 'k001', target: 'k003', relationType: 'prerequisite' },
    { source: 'k001', target: 'k004', relationType: 'prerequisite' },
    { source: 'k002', target: 'k005', relationType: 'prerequisite' },
    { source: 'k003', target: 'k005', relationType: 'prerequisite' },
    { source: 'k005', target: 'k006', relationType: 'prerequisite' },
    { source: 'k005', target: 'k007', relationType: 'prerequisite' },
    { source: 'k005', target: 'k008', relationType: 'prerequisite' },
    { source: 'k004', target: 'k009', relationType: 'prerequisite' },
    { source: 'k005', target: 'k010', relationType: 'prerequisite' },
  ],
  categories: ['programming', 'algorithm', 'web', 'ai', 'science'],
};


/**
 * OpenSciEDU 模拟数据服务
 *
 * 提供与真实 API 相同接口的模拟数据
 * 用于 Neo4j 不可用时的开发测试
 */
@Injectable({
  providedIn: 'root'
})
export class OpenSciEDUMockService {
  /**
   * 模拟网络延迟（200-500ms）
   */
  private getDelay(): number {
    return 200 + Math.random() * 300;
  }

  /**
   * 获取公共课程列表
   */
  getPublicCourses(
    page: number = 1,
    pageSize: number = 20,
    category?: string,
    difficulty?: string
  ): Observable<CourseListResponse> {
    let filtered = [...MOCK_COURSES];

    // 按分类筛选
    if (category) {
      filtered = filtered.filter(c => c.category?.id === category);
    }

    // 按难度筛选
    if (difficulty) {
      filtered = filtered.filter(c => c.difficulty === difficulty);
    }

    // 分页
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    const courses = filtered.slice(start, end);

    const response: CourseListResponse = {
      courses,
      total: filtered.length,
      page,
      pageSize,
      hasNext: end < filtered.length,
    };

    console.log('[OpenSciEDU Mock] 获取课程列表:', { page, pageSize, total: filtered.length });
    return of(response).pipe(delay(this.getDelay()));
  }

  /**
   * 获取课程详情
   */
  getCourseDetail(courseId: string): Observable<CourseDetail | null> {
    const course = MOCK_COURSES.find(c => c.id === courseId);

    if (!course) {
      return of(null).pipe(delay(this.getDelay()));
    }

    const detail: CourseDetail = {
      ...course,
      chapters: this.generateMockChapters(course),
      learningOutcomes: [
        '掌握基本编程概念',
        '能够独立编写简单程序',
        '培养逻辑思维能力',
      ],
      prerequisites: [
        '会使用电脑',
        '对编程有好奇心',
      ],
    };

    console.log('[OpenSciEDU Mock] 获取课程详情:', courseId);
    return of(detail).pipe(delay(this.getDelay()));
  }

  /**
   * 生成模拟章节
   */
  private generateMockChapters(course: PublicCourse): CourseChapter[] {
    const chapterCount = Math.min(4, Math.ceil(course.lessonCount / 5));
    const chapters: CourseChapter[] = [];

    for (let i = 0; i < chapterCount; i++) {
      const lessonCount = Math.ceil(course.lessonCount / chapterCount);
      const lessons: CourseLesson[] = [];

      for (let j = 0; j < lessonCount; j++) {
        const lessonIndex = i * lessonCount + j + 1;
        if (lessonIndex <= course.lessonCount) {
          lessons.push({
            id: `l${course.id}-${i}-${j}`,
            title: `课时 ${lessonIndex}`,
            durationMinutes: 15 + Math.floor(Math.random() * 10),
            type: Math.random() > 0.7 ? 'video' : 'text',
          });
        }
      }

      chapters.push({
        id: `ch${course.id}-${i}`,
        title: `第 ${i + 1} 章`,
        order: i + 1,
        lessons,
        durationMinutes: lessons.length * 20,
      });
    }

    return chapters;
  }

  /**
   * 获取知识图谱
   */
  getKnowledgeGraph(): Observable<KnowledgeGraphData> {
    console.log('[OpenSciEDU Mock] 获取知识图谱');
    return of(MOCK_KNOWLEDGE_GRAPH).pipe(delay(this.getDelay()));
  }

  /**
   * 搜索课程
   */
  searchCourses(keyword: string, page: number = 1, pageSize: number = 20): Observable<SearchResult> {
    const lowerKeyword = keyword.toLowerCase();
    const results = MOCK_COURSES.filter(c =>
      c.title.toLowerCase().includes(lowerKeyword) ||
      c.description.toLowerCase().includes(lowerKeyword) ||
      c.tags.some(t => t.toLowerCase().includes(lowerKeyword))
    );

    const start = (page - 1) * pageSize;
    const courses = results.slice(start, start + pageSize);

    console.log('[OpenSciEDU Mock] 搜索课程:', { keyword, total: results.length });

    return of({
      courses,
      total: results.length,
      query: keyword,
      suggestions: [keyword + ' 入门', keyword + ' 基础', keyword + ' 实践'],
    }).pipe(delay(this.getDelay()));
  }

  /**
   * 获取分类列表
   */
  getCategories(): Observable<CourseCategory[]> {
    console.log('[OpenSciEDU Mock] 获取分类列表');
    return of(MOCK_CATEGORIES).pipe(delay(this.getDelay()));
  }
}
