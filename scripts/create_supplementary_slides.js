const PptxGenJS = require('pptxgenjs');

// 创建演示文稿
const pptx = new PptxGenJS();

// 设置演示文稿属性
pptx.title = 'MatuX商业计划书 - 补充幻灯片';
pptx.author = 'iMato Team';

// 定义配色方案
const colors = {
  primary: '065A82',
  secondary: '1C7293',
  light: 'E8F4F8',
  white: 'FFFFFF',
  text: '21295C',
  gray: '6C757D',
  danger: 'DC3545'
};

// ==================== 幻灯片 1: K12开源管理系统 ====================
let slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('K12开源管理系统', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 产品定位
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 9, h: 1.2,
  fill: { color: colors.primary }
});
slide.addText('产品定位', {
  x: 0.7, y: 1.1, w: 8.6, h: 0.3,
  fontSize: 16, color: colors.white, bold: true
});
slide.addText('为教育机构、校园AI教学、机器人培训机构（面向K12）提供开源免费管理系统，带AI教师功能、基础入门课件，打通学生、家长、机构、学校，建立统一的课程体系', {
  x: 0.7, y: 1.5, w: 8.6, h: 0.6,
  fontSize: 12, color: colors.light
});

// 目标用户
slide.addText('目标用户群体', {
  x: 0.5, y: 2.5, w: 9, h: 0.3,
  fontSize: 16, color: colors.secondary, bold: true
});

const users = [
  { icon: '🏫', name: '教育机构', desc: '机器人、编程、AI培训机构' },
  { icon: '📚', name: '学校', desc: '中小学、职业学校' },
  { icon: '👨‍🏫', name: '教师', desc: '授课教师、助教、教务管理员' },
  { icon: '👦', name: '学生', desc: 'K12学生（小学至高中）' },
  { icon: '👨‍👩‍👧', name: '家长', desc: '查看学习进度和成果' },
  { icon: '🏛️', name: '教育局', desc: '数据汇总和监管' }
];

users.forEach((user, i) => {
  slide.addText(`${user.icon} ${user.name}`, {
    x: 0.5 + (i % 3) * 3.1,
    y: 2.9 + Math.floor(i / 3) * 0.6,
    w: 1.5, h: 0.3,
    fontSize: 12, color: colors.primary, bold: true
  });
  slide.addText(user.desc, {
    x: 2.1 + (i % 3) * 3.1,
    y: 2.9 + Math.floor(i / 3) * 0.6,
    w: 1.4, h: 0.3,
    fontSize: 10, color: colors.gray
  });
});

// 核心功能
slide.addText('核心功能模块', {
  x: 0.5, y: 4.3, w: 9, h: 0.3,
  fontSize: 16, color: colors.secondary, bold: true
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 0.5, y: 4.7, w: 2.9, h: 1.3,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('📚 统一课程体系\n4大分类·6级难度\n多版本课程\nAI辅助推荐', {
  x: 0.7, y: 4.9, w: 2.5, h: 0.9,
  fontSize: 11, color: colors.text
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 3.4, y: 4.7, w: 2.9, h: 1.3,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('🤖 AI教师系统\n智能问答·代码批改\n项目指导·学习推荐', {
  x: 3.6, y: 4.9, w: 2.5, h: 0.9,
  fontSize: 11, color: colors.text
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 6.3, y: 4.7, w: 2.9, h: 1.3,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('📊 四角色Dashboard\n教师·机构管理\n学校·教育局\n多端协同', {
  x: 6.5, y: 4.9, w: 2.5, h: 0.9,
  fontSize: 11, color: colors.text
});

// ==================== 幻灯片 2: AI教师系统 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('AI教师系统', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 四大核心功能
const aiFeatures = [
  {
    icon: '💬',
    title: '智能问答',
    desc: '基于课程内容回答学生问题\n根据学生理解程度调整讲解方式\n提供个性化的学习建议'
  },
  {
    icon: '✅',
    title: '代码批改',
    desc: '智能分析学生代码并给出反馈\n自动识别代码错误和优化建议\n提供详细的修改说明'
  },
  {
    icon: '🎯',
    title: '项目指导',
    desc: '分步骤指导学生完成实践项目\n提供技术方案和代码示例\n帮助学生解决开发中遇到的问题'
  },
  {
    icon: '📊',
    title: '学习推荐',
    desc: '基于学习历史和兴趣推荐下一课程\n个性化学习路径规划\n智能适配学生能力水平'
  }
];

aiFeatures.forEach((feature, i) => {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.5 + (i % 2) * 4.6,
    y: 1 + Math.floor(i / 2) * 2,
    w: 4.4, h: 1.9,
    fill: { color: colors.light },
    line: { color: colors.primary, width: 1 }
  });
  slide.addText(`${feature.icon} ${feature.title}`, {
    x: 0.5 + (i % 2) * 4.6 + 0.2,
    y: 1 + Math.floor(i / 2) * 2 + 0.1,
    w: 4, h: 0.35,
    fontSize: 14, color: colors.primary, bold: true
  });
  slide.addText(feature.desc, {
    x: 0.5 + (i % 2) * 4.6 + 0.2,
    y: 1 + Math.floor(i / 2) * 2 + 0.5,
    w: 4, h: 1.3,
    fontSize: 10, color: colors.text
  });
});

// Token消耗说明
slide.addText('Token消耗参考: 智能问答(300-1500) | 代码批改(800-3500) | 学习路径推荐(700-2500) | 项目指导(800-3000)', {
  x: 0.5, y: 5.2, w: 9, h: 0.4,
  fontSize: 11, color: colors.secondary, bold: true, align: 'center'
});

// ==================== 幻灯片 3: 职校创客教育系统1 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('职校创客教育与市场对接系统 (1/3)', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 业务背景
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 9, h: 1.2,
  fill: { color: colors.secondary }
});
slide.addText('业务背景', {
  x: 0.7, y: 1.1, w: 8.6, h: 0.3,
  fontSize: 14, color: colors.white, bold: true
});
slide.addText('职校学生创客教育是连接学校教育与企业实际需求的重要桥梁。本模块旨在：激发学生创新能力和实践能力、提供真实企业项目和市场需求对接、支持学生参加各类创客赛事、帮助学生对接就业机会', {
  x: 0.7, y: 1.5, w: 8.6, h: 0.6,
  fontSize: 11, color: colors.light
});

// 创客项目孵化
slide.addText('🚀 创客项目孵化', {
  x: 0.5, y: 2.5, w: 9, h: 0.3,
  fontSize: 16, color: colors.secondary, bold: true
});

slide.addText('项目类型：', {
  x: 0.5, y: 2.9, w: 1.5, h: 0.3,
  fontSize: 12, color: colors.primary, bold: true
});
slide.addText('机器人项目（智能小车、机械臂、无人机）\n物联网项目（智能家居、环境监测、农业自动化）\n软件项目（移动应用、Web应用、游戏开发）\n混合项目（软硬件结合的创新应用）', {
  x: 2.1, y: 2.9, w: 7.4, h: 0.8,
  fontSize: 10, color: colors.text
});

slide.addText('项目流程：', {
  x: 0.5, y: 3.8, w: 1.5, h: 0.3,
  fontSize: 12, color: colors.primary, bold: true
});
slide.addText('创意提交 → 导师审核 → 项目立项 → 资源分配 → 开发实施 → 阶段评审 → 成果展示', {
  x: 2.1, y: 3.8, w: 7.4, h: 0.3,
  fontSize: 11, color: colors.text
});

// 企业需求对接
slide.addText('🏢 企业需求对接', {
  x: 0.5, y: 4.3, w: 9, h: 0.3,
  fontSize: 16, color: colors.secondary, bold: true
});

slide.addText('需求分类：技术开发需求 | 产品设计需求 | 创新研究需求 | 校企合作项目', {
  x: 0.5, y: 4.7, w: 9, h: 0.3,
  fontSize: 11, color: colors.text
});

slide.addText('对接流程：企业发布需求 → 学校审核 → 学生组队竞标 → 企业选择 → 签订协议 → 项目实施 → 验收交付', {
  x: 0.5, y: 5.1, w: 9, h: 0.3,
  fontSize: 11, color: colors.text
});

// ==================== 幻灯片 4: 职校创客教育系统2 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('职校创客教育与市场对接系统 (2/3)', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 市场需求推荐系统
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 4.4, h: 2.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('🤖 市场需求推荐系统', {
  x: 0.5, y: 1.1, w: 4.4, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true, align: 'center'
});
slide.addText('基于学生的技能、兴趣和历史项目，AI系统推荐匹配的企业需求和创客赛事', {
  x: 0.7, y: 1.5, w: 4, h: 0.5,
  fontSize: 11, color: colors.text
});
slide.addText('推荐算法因素：\n• 学生技能匹配度（技能标签、技术栈）40%\n• 历史项目相似度 30%\n• 学习兴趣偏好 20%\n• 同类学生参与记录（协同过滤）10%', {
  x: 0.7, y: 2.1, w: 4, h: 1.3,
  fontSize: 10, color: colors.text
});

// 创客赛事管理
slide.addShape(pptx.ShapeType.rect, {
  x: 4.9, y: 1, w: 4.4, h: 2.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('🏆 创客赛事管理', {
  x: 4.9, y: 1.1, w: 4.4, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true, align: 'center'
});
slide.addText('赛事分类：校内赛事、区域赛事、全国赛事、国际赛事', {
  x: 5.1, y: 1.5, w: 4, h: 0.3,
  fontSize: 11, color: colors.text
});
slide.addText('功能模块：\n• 赛事发布与报名\n• 赛事推荐与智能匹配\n• 项目提交与评审\n• 成果展示与排名', {
  x: 5.1, y: 1.9, w: 4, h: 1.2,
  fontSize: 10, color: colors.text
});

// 成果展示与就业对接
slide.addText('💼 成果展示与就业对接', {
  x: 0.5, y: 3.7, w: 9, h: 0.3,
  fontSize: 16, color: colors.secondary, bold: true
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 0.5, y: 4.1, w: 2.9, h: 1.3,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('📁 个人成果库\n• 项目作品集\n• 竞赛成果\n• 技能认证\n• 能力评估', {
  x: 0.7, y: 4.3, w: 2.5, h: 0.9,
  fontSize: 10, color: colors.text
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 3.4, y: 4.1, w: 2.9, h: 1.3,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('🎖️ 竞赛成就\n• 获奖记录\n• 证书展示\n• 排名统计\n• 评委推荐', {
  x: 3.6, y: 4.3, w: 2.5, h: 0.9,
  fontSize: 10, color: colors.text
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 6.3, y: 4.1, w: 2.9, h: 1.3,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('💼 就业推荐\n• 岗位匹配\n• 企业对接\n• 面试准备\n• 薪资参考', {
  x: 6.5, y: 4.3, w: 2.5, h: 0.9,
  fontSize: 10, color: colors.text
});

// ==================== 幻灯片 5: 职校创客教育系统3 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('职校创客教育与市场对接系统 (3/3)', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

slide.addText('实施计划（预计7-11个月）', {
  x: 0.5, y: 1, w: 9, h: 0.3,
  fontSize: 16, color: colors.secondary, bold: true
});

const phases = [
  {
    name: '阶段1: 基础功能',
    time: '2-3个月',
    items: '• 创客项目创建与管理\n• 基础项目展示和进度跟踪\n• 团队组建和协作功能'
  },
  {
    name: '阶段2: 需求对接',
    time: '1-2个月',
    items: '• 企业需求发布模块\n• 投标和竞标系统\n• 项目合同管理'
  },
  {
    name: '阶段3: 赛事管理',
    time: '1-2个月',
    items: '• 赛事发布和报名系统\n• 成果提交和评审功能\n• 赛事推荐算法'
  },
  {
    name: '阶段4: 智能推荐',
    time: '1-2个月',
    items: '• AI需求推荐系统\n• 学生成果库建设\n• 就业推荐对接'
  },
  {
    name: '阶段5: 运营优化',
    time: '持续',
    items: '• 数据分析和监控\n• 用户反馈收集\n• 功能迭代优化'
  }
];

phases.forEach((phase, i) => {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.5 + (i % 3) * 3.1,
    y: 1.5 + Math.floor(i / 3) * 2,
    w: 2.9, h: 1.8,
    fill: { color: colors.light },
    line: { color: colors.primary, width: 1 }
  });
  slide.addText(phase.name, {
    x: 0.5 + (i % 3) * 3.1 + 0.2,
    y: 1.5 + Math.floor(i / 3) * 2 + 0.1,
    w: 2.5, h: 0.3,
    fontSize: 11, color: colors.primary, bold: true
  });
  slide.addText(phase.time, {
    x: 0.5 + (i % 3) * 3.1 + 0.2,
    y: 1.5 + Math.floor(i / 3) * 2 + 0.4,
    w: 2.5, h: 0.25,
    fontSize: 9, color: colors.secondary
  });
  slide.addText(phase.items, {
    x: 0.5 + (i % 3) * 3.1 + 0.2,
    y: 1.5 + Math.floor(i / 3) * 2 + 0.7,
    w: 2.5, h: 1,
    fontSize: 9, color: colors.text
  });
});

// 系统架构
slide.addText('技术架构', {
  x: 0.5, y: 5, w: 9, h: 0.3,
  fontSize: 14, color: colors.secondary, bold: true
});

slide.addText('前端: Angular组件化 | 后端: FastAPI + PostgreSQL | AI: 智能推荐算法 | 部署: Docker容器化', {
  x: 0.5, y: 5.4, w: 9, h: 0.4,
  fontSize: 11, color: colors.text, align: 'center'
});

// ==================== 幻灯片 6: 收费模型 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('收费模型设计', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

slide.addText('免费课程体系 + AI课程（订阅费+Token消耗）', {
  x: 0.5, y: 0.9, w: 9, h: 0.4,
  fontSize: 14, color: colors.secondary, bold: true, align: 'center'
});

// 三档套餐
const plans = [
  {
    name: '免费版',
    price: '¥0',
    users: '<50学生',
    tokens: '无',
    color: colors.gray,
    features: '✓ 完整开源管理系统\n✓ 基础课程(L1-2)\n✓ 学生/家长/教师功能\n✓ 基础Dashboard\n✓ 创客项目管理',
    notFeatures: '✗ AI教师功能\n✗ 智能推荐'
  },
  {
    name: '专业版',
    price: '¥99/月',
    users: '50-500学生',
    tokens: '10,000/月',
    color: colors.primary,
    features: '✓ 免费版所有功能\n✓ AI教师功能\n✓ 智能课程推荐\n✓ 学习路径AI规划\n✓ 代码批改(500次/月)\n✓ 企业需求推荐\n✓ 赛事智能匹配',
    notFeatures: '✗ 专属技术支持'
  },
  {
    name: '企业版',
    price: '¥2999/月',
    users: '>500学生',
    tokens: '100,000/月',
    color: colors.secondary,
    features: '✓ 专业版所有功能\n✓ AI教师功能\n✓ 专属技术支持(7×24)\n✓ 定制化开发\n✓ 数据导入/导出\n✓ SLA保障99.9%',
    notFeatures: ''
  }
];

plans.forEach((plan, i) => {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.3 + i * 3.2, y: 1.5, w: 3, h: 4,
    fill: { color: i === 1 ? colors.light : 'FFFFFF' },
    line: { color: plan.color, width: i === 1 ? 3 : 1 }
  });
  slide.addText(plan.name, {
    x: 0.3 + i * 3.2 + 0.1, y: 1.6, w: 2.8, h: 0.35,
    fontSize: 16, color: plan.color, bold: true, align: 'center'
  });
  slide.addText(plan.price, {
    x: 0.3 + i * 3.2 + 0.1, y: 2, w: 2.8, h: 0.4,
    fontSize: 24, color: plan.color, bold: true, align: 'center'
  });
  slide.addText(plan.users, {
    x: 0.3 + i * 3.2 + 0.1, y: 2.45, w: 2.8, h: 0.3,
    fontSize: 10, color: colors.gray, align: 'center'
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.3 + i * 3.2 + 0.3, y: 2.85, w: 2.4, h: 0.4,
    fill: { color: plan.color }
  });
  slide.addText(`${plan.tokens} tokens`, {
    x: 0.3 + i * 3.2 + 0.3, y: 2.95, w: 2.4, h: 0.4,
    fontSize: 11, color: colors.white, bold: true, align: 'center'
  });
  slide.addText(plan.features, {
    x: 0.3 + i * 3.2 + 0.2, y: 3.4, w: 2.6, h: 1.8,
    fontSize: 9, color: colors.text
  });
  if (plan.notFeatures) {
    slide.addText(plan.notFeatures, {
      x: 0.3 + i * 3.2 + 0.2, y: 5.2, w: 2.6, h: 0.4,
      fontSize: 8, color: colors.danger
    });
  }
});

// ==================== 幻灯片 7: Token计费规则 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('Token计费规则', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// Token消耗表
const tokenTable = [
  [
    { text: '功能', options: { fontSize: 12, bold: true, color: 'FFFFFF' } },
    { text: '输入', options: { fontSize: 12, bold: true, color: 'FFFFFF' } },
    { text: '输出', options: { fontSize: 12, bold: true, color: 'FFFFFF' } },
    { text: '单次消耗', options: { fontSize: 12, bold: true, color: 'FFFFFF' } }
  ],
  [
    { text: '智能问答', options: { fontSize: 10 } },
    { text: '100-500', options: { fontSize: 10 } },
    { text: '200-1000', options: { fontSize: 10 } },
    { text: '300-1500', options: { fontSize: 10, color: colors.primary, bold: true } }
  ],
  [
    { text: '代码批改', options: { fontSize: 10 } },
    { text: '500-2000', options: { fontSize: 10 } },
    { text: '300-1500', options: { fontSize: 10 } },
    { text: '800-3500', options: { fontSize: 10, color: colors.primary, bold: true } }
  ],
  [
    { text: '学习路径推荐', options: { fontSize: 10 } },
    { text: '200-500', options: { fontSize: 10 } },
    { text: '500-2000', options: { fontSize: 10 } },
    { text: '700-2500', options: { fontSize: 10, color: colors.primary, bold: true } }
  ],
  [
    { text: '项目指导', options: { fontSize: 10 } },
    { text: '300-1000', options: { fontSize: 10 } },
    { text: '500-2000', options: { fontSize: 10 } },
    { text: '800-3000', options: { fontSize: 10, color: colors.primary, bold: true } }
  ]
];

slide.addTable(tokenTable, {
  x: 0.5, y: 1, w: 9, h: 2.2,
  border: { pt: 1, color: 'CCCCCC' },
  fill: { color: colors.primary }
});

// 计费规则
slide.addText('计费规则', {
  x: 0.5, y: 3.5, w: 9, h: 0.3,
  fontSize: 14, color: colors.secondary, bold: true
});

slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 3.9, w: 2.9, h: 1.2,
  fill: { color: colors.light }
});
slide.addText('免费版\n无Token配额\n¥0.1/1000 tokens', {
  x: 0.6, y: 4, w: 2.7, h: 1,
  fontSize: 11, color: colors.text
});

slide.addShape(pptx.ShapeType.rect, {
  x: 3.5, y: 3.9, w: 2.9, h: 1.2,
  fill: { color: colors.light }
});
slide.addText('专业版\n10,000 tokens/月\n超出 ¥0.08/1000', {
  x: 3.6, y: 4, w: 2.7, h: 1,
  fontSize: 11, color: colors.text
});

slide.addShape(pptx.ShapeType.rect, {
  x: 6.5, y: 3.9, w: 2.9, h: 1.2,
  fill: { color: colors.light }
});
slide.addText('企业版\n100,000 tokens/月\n超出 ¥0.06/1000', {
  x: 6.6, y: 4, w: 2.7, h: 1,
  fontSize: 11, color: colors.text
});

// 提醒策略
slide.addText('提醒策略', {
  x: 0.5, y: 5.4, w: 9, h: 0.3,
  fontSize: 14, color: colors.secondary, bold: true
});

slide.addText('⚠️ 配额预警(80%) | 🚫 配额耗尽(暂停AI) | 📅 到期提醒(前7天/3天/1天) | ⬇️ 功能降级(未续费)', {
  x: 0.5, y: 5.8, w: 9, h: 0.4,
  fontSize: 10, color: colors.text
});

// 保存PPT
const outputPath = 'g:/iMato/scripts/MatuX_商业计划书_补充幻灯片.pptx';
pptx.writeFile({ fileName: outputPath })
  .then(() => {
    console.log('补充幻灯片生成成功！');
    console.log(`共生成 ${pptx.slides.length} 页补充幻灯片`);
    console.log(`保存路径: ${outputPath}`);
    console.log('\n请将此PPT中的幻灯片复制并插入到原PPT文件中：');
    console.log('g:/iMato/scripts/MatuX_创业大赛商业计划书_完整版.pptx');
  })
  .catch(err => {
    console.error('生成失败:', err);
  });
