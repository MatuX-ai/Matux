module.exports = {
  '/api': {
    target: 'http://localhost:3000',
    secure: false,
    changeOrigin: true,
    logLevel: 'debug',
    bypass: function(req, res, proxyOptions) {
      // 离线模式下直接返回模拟数据
      if (req.headers['x-offline-mode'] === 'true') {
        console.log('[Offline Proxy] 拦截API请求:', req.url);
        
        // 根据不同API路径返回相应的模拟数据
        if (req.url.startsWith('/api/v1/users')) {
          return mockUserData(req, res);
        } else if (req.url.startsWith('/api/v1/tasks')) {
          return mockTaskData(req, res);
        } else if (req.url.startsWith('/api/v1/courses')) {
          return mockCourseData(req, res);
        } else {
          return mockGenericData(req, res);
        }
      }
      
      // 正常代理请求
      return null;
    }
  },
  '/assets': {
    target: 'http://localhost:4200',
    secure: false,
    changeOrigin: true
  }
};

/**
 * 模拟用户数据
 */
function mockUserData(req, res) {
  const userData = {
    id: 'user-1',
    username: 'demo-user',
    email: 'demo@example.com',
    displayName: '演示用户',
    roles: ['student'],
    lastLoginAt: new Date().toISOString(),
    preferences: {
      theme: 'light',
      language: 'zh-CN'
    }
  };

  res.setHeader('Content-Type', 'application/json');
  res.statusCode = 200;
  res.end(JSON.stringify(userData));
  return true;
}

/**
 * 模拟任务数据
 */
function mockTaskData(req, res) {
  const tasks = [
    {
      id: 'task-1',
      title: '完成数学第一章练习',
      description: '完成微积分基础概念的相关习题',
      type: 'exercise',
      assigneeId: 'user-1',
      creatorId: 'teacher-1',
      dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
      priority: 'high',
      status: 'todo',
      courseId: 'course-1',
      tags: ['数学', '微积分', '基础'],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    },
    {
      id: 'task-2',
      title: '阅读英语语法资料',
      description: '阅读并理解被动语态的使用规则',
      type: 'reading',
      assigneeId: 'user-1',
      creatorId: 'teacher-2',
      dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      priority: 'medium',
      status: 'in-progress',
      courseId: 'course-2',
      tags: ['英语', '语法', '被动语态'],
      createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date().toISOString()
    }
  ];

  res.setHeader('Content-Type', 'application/json');
  res.statusCode = 200;
  res.end(JSON.stringify(tasks));
  return true;
}

/**
 * 模拟课程数据
 */
function mockCourseData(req, res) {
  const courses = [
    {
      id: 'course-1',
      title: '高等数学基础',
      description: '深入学习微积分和线性代数的基础知识',
      teacherId: 'teacher-1',
      studentIds: ['user-1'],
      status: 'published',
      tags: ['数学', '微积分', '线性代数'],
      lessons: [
        {
          id: 'lesson-1',
          title: '函数与极限',
          content: '本节课介绍函数的基本概念和极限理论...',
          order: 1,
          completed: false
        }
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
  ];

  res.setHeader('Content-Type', 'application/json');
  res.statusCode = 200;
  res.end(JSON.stringify(courses));
  return true;
}

/**
 * 通用模拟数据
 */
function mockGenericData(req, res) {
  const responseData = {
    message: '离线模式 - 模拟数据响应',
    timestamp: new Date().toISOString(),
    path: req.url,
    method: req.method
  };

  res.setHeader('Content-Type', 'application/json');
  res.statusCode = 200;
  res.end(JSON.stringify(responseData));
  return true;
}