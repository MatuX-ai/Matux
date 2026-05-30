const PptxGenJS = require('pptxgenjs');

// 创建演示文稿
const pptx = new PptxGenJS();

// 设置演示文稿属性
pptx.title = 'iMato多来源学习系统 - 项目规划';
pptx.author = 'iMato Team';
pptx.subject = 'K12教育机构开源管理系统规划';
pptx.company = 'iMato';

// 定义配色方案
const colors = {
  primary: '065A82',
  secondary: '1C7293',
  accent: '21295C',
  light: 'E8F4F8',
  white: 'FFFFFF',
  text: '21295C',
  gray: '6C757D',
  success: '28A745',
  warning: 'FFC107',
  danger: 'DC3545'
};

// ==================== 幻灯片 1: 封面 ====================
let slide = pptx.addSlide();
slide.background = { color: colors.primary };

slide.addText('iMato多来源学习系统', {
  x: 0.5, y: 1.5, w: 9, h: 1,
  fontSize: 48, fontFace: 'Arial Black', color: colors.white, align: 'center'
});

slide.addText('K12教育机构开源管理系统 - 项目规划', {
  x: 0.5, y: 2.3, w: 9, h: 0.6,
  fontSize: 20, fontFace: 'Arial', color: colors.light, align: 'center'
});

slide.addShape(pptx.ShapeType.line, {
  x: 2, y: 3, w: 6, h: 0,
  line: { color: colors.light, width: 2 }
});

slide.addText([
  { text: '✓ K12开源管理系统', options: { fontSize: 18, color: colors.white, bold: true } },
  { text: '\n✓ 职校创客教育与市场对接', options: { fontSize: 18, color: colors.white, bold: true } },
  { text: '\n✓ 智能收费模型（免费+订阅+Token）', options: { fontSize: 18, color: colors.white, bold: true } }
], { x: 1, y: 3.5, w: 8, h: 1.5, align: 'center' });

slide.addText('2026年3月', {
  x: 0.5, y: 6.5, w: 9, h: 0.4,
  fontSize: 12, color: colors.light, align: 'center'
});

// ==================== 幻灯片 2: 项目概览 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('项目概览', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

slide.addText('核心目标', {
  x: 0.5, y: 1, w: 4, h: 0.4,
  fontSize: 18, color: colors.secondary, bold: true
});

slide.addText([
  { text: '🎯 为教育机构、校园AI教学、机器人培训机构（面向K12）提供开源免费管理系统', options: { fontSize: 11, breakLine: true } },
  { text: '🤖 带AI教师功能、基础入门课件', options: { fontSize: 11, breakLine: true } },
  { text: '🔗 打通学生、家长、机构、学校，建立统一课程体系', options: { fontSize: 11, breakLine: true } },
  { text: '💼 职校创客教育与市场需求对接', options: { fontSize: 11, breakLine: true } },
  { text: '💰 免费课程体系 + AI课程（订阅费+Token消耗）', options: { fontSize: 11, breakLine: true } }
], {
  x: 0.5, y: 1.5, w: 4, h: 2,
  fontSize: 11, color: colors.text
});

slide.addText('目标用户群体', {
  x: 5, y: 1, w: 4, h: 0.4,
  fontSize: 18, color: colors.secondary, bold: true
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
    x: 5, y: 1.5 + i * 0.5, w: 1.5, h: 0.4,
    fontSize: 12, color: colors.primary, bold: true
  });
  slide.addText(user.desc, {
    x: 6.6, y: 1.5 + i * 0.5, w: 2.4, h: 0.4,
    fontSize: 10, color: colors.gray
  });
});

slide.addText('技术栈', {
  x: 0.5, y: 5, w: 9, h: 0.4,
  fontSize: 18, color: colors.secondary, bold: true
});

slide.addText('前端: Angular 16 + TypeScript + Angular Material | 后端: Python FastAPI | 数据库: PostgreSQL | 部署: Docker + 云托管', {
  x: 0.5, y: 5.5, w: 9, h: 0.4,
  fontSize: 12, align: 'center', color: colors.text
});

// ==================== 幻灯片 3: K12核心系统架构 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('K12核心系统架构', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 统一课程体系
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 2.8, h: 2.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('统一课程体系', {
  x: 0.5, y: 1.1, w: 2.8, h: 0.4,
  fontSize: 16, color: colors.primary, bold: true, align: 'center'
});
slide.addText('4大分类：机器人、编程、AI基础、项目制\n6级难度：Level 1-6对应K12各年级\n多版本：基础版、进阶版、竞赛版\nAI辅助推荐与个性化学习路径', {
  x: 0.7, y: 1.6, w: 2.4, h: 1.7,
  fontSize: 10, color: colors.text
});

// AI教师系统
slide.addShape(pptx.ShapeType.rect, {
  x: 3.4, y: 1, w: 2.8, h: 2.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('AI教师系统', {
  x: 3.4, y: 1.1, w: 2.8, h: 0.4,
  fontSize: 16, color: colors.primary, bold: true, align: 'center'
});
slide.addText('智能问答：基于课程内容答疑\n代码批改：自动分析和反馈\n项目指导：分步骤指导实践\n学习推荐：个性化路径规划', {
  x: 3.6, y: 1.6, w: 2.4, h: 1.7,
  fontSize: 10, color: colors.text
});

// 四角色Dashboard
slide.addShape(pptx.ShapeType.rect, {
  x: 6.3, y: 1, w: 2.8, h: 2.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('四角色Dashboard', {
  x: 6.3, y: 1.1, w: 2.8, h: 0.4,
  fontSize: 16, color: colors.primary, bold: true, align: 'center'
});
slide.addText('教师Dashboard：教学进度、学情分析\n机构管理：运营数据、课程监控\n学校管理：校本课程、跨机构协作\n教育局：区域数据、质量监控', {
  x: 6.5, y: 1.6, w: 2.4, h: 1.7,
  fontSize: 10, color: colors.text
});

// 多端协同
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 3.8, w: 4.3, h: 1.5,
  fill: { color: colors.primary }
});
slide.addText('多端协同', {
  x: 0.5, y: 3.9, w: 4.3, h: 0.4,
  fontSize: 16, color: colors.white, bold: true, align: 'center'
});
slide.addText('Web端 + 移动端 + 管理端，数据实时同步', {
  x: 0.7, y: 4.4, w: 3.9, h: 0.4,
  fontSize: 12, color: colors.light
});

// 开源策略
slide.addShape(pptx.ShapeType.rect, {
  x: 4.9, y: 3.8, w: 4.2, h: 1.5,
  fill: { color: colors.secondary }
});
slide.addText('开源策略', {
  x: 4.9, y: 3.9, w: 4.2, h: 0.4,
  fontSize: 16, color: colors.white, bold: true, align: 'center'
});
slide.addText('AGPL-3.0协议 | 基础版完全免费', {
  x: 5.1, y: 4.4, w: 3.8, h: 0.4,
  fontSize: 12, color: colors.light
});

// ==================== 幻灯片 4: AI教师功能详解 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('AI教师系统功能详解', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 智能问答
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 4.3, h: 2,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('💬 智能问答', {
  x: 0.7, y: 1.1, w: 3.9, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true
});
slide.addText('基于课程内容回答学生问题\n根据学生理解程度调整讲解方式\n提供个性化的学习建议', {
  x: 0.7, y: 1.5, w: 3.9, h: 1.3,
  fontSize: 11, color: colors.text
});

// 代码批改
slide.addShape(pptx.ShapeType.rect, {
  x: 4.9, y: 1, w: 4.2, h: 2,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('✅ 代码批改', {
  x: 5.1, y: 1.1, w: 3.8, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true
});
slide.addText('智能分析学生代码并给出反馈\n自动识别代码错误和优化建议\n提供详细的修改说明', {
  x: 5.1, y: 1.5, w: 3.8, h: 1.3,
  fontSize: 11, color: colors.text
});

// 项目指导
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 3.2, w: 4.3, h: 2,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('🎯 项目指导', {
  x: 0.7, y: 3.3, w: 3.9, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true
});
slide.addText('分步骤指导学生完成实践项目\n提供技术方案和代码示例\n帮助学生解决开发中遇到的问题', {
  x: 0.7, y: 3.7, w: 3.9, h: 1.3,
  fontSize: 11, color: colors.text
});

// 学习推荐
slide.addShape(pptx.ShapeType.rect, {
  x: 4.9, y: 3.2, w: 4.2, h: 2,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 1 }
});
slide.addText('📊 学习推荐', {
  x: 5.1, y: 3.3, w: 3.8, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true
});
slide.addText('基于学习历史和兴趣推荐下一课程\n个性化学习路径规划\n智能适配学生能力水平', {
  x: 5.1, y: 3.7, w: 3.8, h: 1.3,
  fontSize: 11, color: colors.text
});

// Token消耗
slide.addText('Token消耗参考: 智能问答(300-1500) | 代码批改(800-3500) | 学习路径推荐(700-2500) | 项目指导(800-3000)', {
  x: 0.5, y: 5.5, w: 9, h: 0.4,
  fontSize: 11, color: colors.secondary, bold: true, align: 'center'
});

// ==================== 幻灯片 5: 职校创客教育系统 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('职校创客教育与市场对接系统', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 核心价值
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 9, h: 1.2,
  fill: { color: colors.secondary }
});
slide.addText('核心价值', {
  x: 0.7, y: 1.1, w: 8.6, h: 0.35,
  fontSize: 14, color: colors.white, bold: true
});
slide.addText('• 激发学生创新能力和实践能力  • 提供真实企业项目和市场需求对接  • 支持学生参加各类创客赛事  • 帮助学生对接就业机会', {
  x: 0.7, y: 1.5, w: 8.6, h: 0.6,
  fontSize: 11, color: colors.light
});

// 五大功能模块
const makerModules = [
  { name: '创客项目孵化', icon: '🚀', desc: '机器人、物联网、软件、混合项目' },
  { name: '企业需求对接', icon: '🏢', desc: '技术开发、产品设计、创新研究' },
  { name: '市场需求推荐', icon: '🤖', desc: 'AI智能匹配算法，精准推荐' },
  { name: '创客赛事管理', icon: '🏆', desc: '校内、区域、全国、国际赛事' },
  { name: '成果展示就业', icon: '💼', desc: '个人成果库、就业推荐对接' }
];

makerModules.forEach((module, i) => {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.5 + (i % 3) * 3.1,
    y: 2.5 + Math.floor(i / 3) * 1.5,
    w: 2.9, h: 1.3,
    fill: { color: colors.light },
    line: { color: colors.primary, width: 1 }
  });
  slide.addText(`${module.icon} ${module.name}`, {
    x: 0.5 + (i % 3) * 3.1 + 0.2,
    y: 2.5 + Math.floor(i / 3) * 1.5 + 0.2,
    w: 2.5, h: 0.35,
    fontSize: 12, color: colors.primary, bold: true
  });
  slide.addText(module.desc, {
    x: 0.5 + (i % 3) * 3.1 + 0.2,
    y: 2.5 + Math.floor(i / 3) * 1.5 + 0.6,
    w: 2.5, h: 0.5,
    fontSize: 10, color: colors.text
  });
});

// 实施计划
slide.addText('实施计划（预计7-11个月）', {
  x: 0.5, y: 5.8, w: 9, h: 0.3,
  fontSize: 14, color: colors.secondary, bold: true
});

slide.addText('阶段1: 基础功能(2-3月) | 阶段2: 需求对接(1-2月) | 阶段3: 赛事管理(1-2月) | 阶段4: 智能推荐(1-2月) | 阶段5: 运营优化(持续)', {
  x: 0.5, y: 6.2, w: 9, h: 0.4,
  fontSize: 10, align: 'center', color: colors.text
});

// ==================== 幻灯片 6: 收费模型设计 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('收费模型设计', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 免费版
slide.addShape(pptx.ShapeType.rect, {
  x: 0.3, y: 1, w: 3, h: 5,
  fill: { color: 'FFFFFF' },
  line: { color: colors.gray, width: 1 }
});
slide.addText('免费版', {
  x: 0.3 + 0.1, y: 1.1, w: 2.8, h: 0.35,
  fontSize: 16, color: colors.gray, bold: true, align: 'center'
});
slide.addText('¥0', {
  x: 0.3 + 0.1, y: 1.5, w: 2.8, h: 0.4,
  fontSize: 24, color: colors.gray, bold: true, align: 'center'
});
slide.addText('<50学生', {
  x: 0.3 + 0.1, y: 1.95, w: 2.8, h: 0.3,
  fontSize: 10, color: colors.gray, align: 'center'
});
slide.addText('✓ 开源管理系统\n✓ 基础课程(L1-2)\n✓ 学生/家长/教师功能\n✓ 基础Dashboard\n✓ 创客项目管理', {
  x: 0.3 + 0.2, y: 2.5, w: 2.6, h: 2.2,
  fontSize: 9, color: colors.text
});
slide.addText('✗ AI教师功能\n✗ 智能推荐\n✗ 高级数据分析', {
  x: 0.3 + 0.2, y: 4.8, w: 2.6, h: 0.8,
  fontSize: 8, color: colors.danger
});

// 专业版
slide.addShape(pptx.ShapeType.rect, {
  x: 3.5, y: 1, w: 3, h: 5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 3 }
});
slide.addText('专业版', {
  x: 3.5 + 0.1, y: 1.1, w: 2.8, h: 0.35,
  fontSize: 16, color: colors.primary, bold: true, align: 'center'
});
slide.addText('¥99/月', {
  x: 3.5 + 0.1, y: 1.5, w: 2.8, h: 0.4,
  fontSize: 24, color: colors.primary, bold: true, align: 'center'
});
slide.addText('50-500学生', {
  x: 3.5 + 0.1, y: 1.95, w: 2.8, h: 0.3,
  fontSize: 10, color: colors.gray, align: 'center'
});
slide.addShape(pptx.ShapeType.rect, {
  x: 3.5 + 0.3, y: 2.35, w: 2.4, h: 0.4,
  fill: { color: colors.primary }
});
slide.addText('10,000 tokens', {
  x: 3.5 + 0.3, y: 2.45, w: 2.4, h: 0.4,
  fontSize: 11, color: colors.white, bold: true, align: 'center'
});
slide.addText('✓ 免费版所有功能\n✓ AI教师功能\n✓ 智能课程推荐\n✓ 学习路径AI规划\n✓ 代码批改(500次/月)\n✓ 企业需求推荐\n✓ 赛事智能匹配\n✓ 高级Dashboard', {
  x: 3.5 + 0.2, y: 2.9, w: 2.6, h: 2.2,
  fontSize: 9, color: colors.text
});
slide.addText('✗ 专属技术支持\n✗ 定制化开发', {
  x: 3.5 + 0.2, y: 5.2, w: 2.6, h: 0.5,
  fontSize: 8, color: colors.danger
});

// 企业版
slide.addShape(pptx.ShapeType.rect, {
  x: 6.7, y: 1, w: 3, h: 5,
  fill: { color: colors.light },
  line: { color: colors.secondary, width: 1 }
});
slide.addText('企业版', {
  x: 6.7 + 0.1, y: 1.1, w: 2.8, h: 0.35,
  fontSize: 16, color: colors.secondary, bold: true, align: 'center'
});
slide.addText('¥2999/月', {
  x: 6.7 + 0.1, y: 1.5, w: 2.8, h: 0.4,
  fontSize: 24, color: colors.secondary, bold: true, align: 'center'
});
slide.addText('>500学生', {
  x: 6.7 + 0.1, y: 1.95, w: 2.8, h: 0.3,
  fontSize: 10, color: colors.gray, align: 'center'
});
slide.addShape(pptx.ShapeType.rect, {
  x: 6.7 + 0.3, y: 2.35, w: 2.4, h: 0.4,
  fill: { color: colors.secondary }
});
slide.addText('100,000 tokens', {
  x: 6.7 + 0.3, y: 2.45, w: 2.4, h: 0.4,
  fontSize: 11, color: colors.white, bold: true, align: 'center'
});
slide.addText('✓ 专业版所有功能\n✓ AI教师功能\n✓ 专属技术支持(7×24)\n✓ 定制化开发\n✓ 数据导入/导出\n✓ 专属服务器部署\n✓ SLA保障99.9%\n✓ 培训服务', {
  x: 6.7 + 0.2, y: 2.9, w: 2.6, h: 2.2,
  fontSize: 9, color: colors.text
});

// ==================== 幻灯片 7: Token计费规则 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('Token计费规则', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

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
  ],
  [
    { text: '课程内容生成', options: { fontSize: 10 } },
    { text: '500-1000', options: { fontSize: 10 } },
    { text: '1000-5000', options: { fontSize: 10 } },
    { text: '1500-6000', options: { fontSize: 10, color: colors.primary, bold: true } }
  ]
];

slide.addTable(tokenTable, {
  x: 0.5, y: 1, w: 9, h: 2.5,
  border: { pt: 1, color: 'CCCCCC' },
  fill: { color: colors.primary }
});

// 计费规则
slide.addText('计费规则', {
  x: 0.5, y: 3.7, w: 9, h: 0.3,
  fontSize: 14, color: colors.secondary, bold: true
});

slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 4.1, w: 2.9, h: 1.3,
  fill: { color: colors.light }
});
slide.addText('免费版', {
  x: 0.6, y: 4.2, w: 2.7, h: 0.35,
  fontSize: 12, color: colors.gray, bold: true
});
slide.addText('无Token配额\n¥0.1/1000 tokens', {
  x: 0.6, y: 4.6, w: 2.7, h: 0.7,
  fontSize: 11, color: colors.text
});

slide.addShape(pptx.ShapeType.rect, {
  x: 3.5, y: 4.1, w: 2.9, h: 1.3,
  fill: { color: colors.light }
});
slide.addText('专业版', {
  x: 3.6, y: 4.2, w: 2.7, h: 0.35,
  fontSize: 12, color: colors.primary, bold: true
});
slide.addText('10,000 tokens/月\n超出 ¥0.08/1000', {
  x: 3.6, y: 4.6, w: 2.7, h: 0.7,
  fontSize: 11, color: colors.text
});

slide.addShape(pptx.ShapeType.rect, {
  x: 6.5, y: 4.1, w: 2.9, h: 1.3,
  fill: { color: colors.light }
});
slide.addText('企业版', {
  x: 6.6, y: 4.2, w: 2.7, h: 0.35,
  fontSize: 12, color: colors.secondary, bold: true
});
slide.addText('100,000 tokens/月\n超出 ¥0.06/1000', {
  x: 6.6, y: 4.6, w: 2.7, h: 0.7,
  fontSize: 11, color: colors.text
});

slide.addText('提醒策略: ⚠️配额预警(80%) | 🚫配额耗尽(暂停AI) | 📅到期提醒(前7天/3天/1天) | ⬇️功能降级(未续费)', {
  x: 0.5, y: 5.7, w: 9, h: 0.4,
  fontSize: 10, color: colors.text
});

// ==================== 幻灯片 8: 实施优先级 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('实施优先级', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

const priorities = [
  {
    level: 'P0 - 第一优先级',
    color: colors.primary,
    tasks: '1. 统一课程体系管理  2. 四角色Dashboard基础版  3. 开源代码整理与发布'
  },
  {
    level: 'P1 - 第二优先级',
    color: colors.secondary,
    tasks: '4. AI教师问答功能  5. AI代码批改功能  6. Token消耗监控与计费'
  },
  {
    level: 'P2 - 第三优先级',
    color: colors.success,
    tasks: '7. 创客项目管理  8. 企业需求对接  9. 基础赛事管理'
  },
  {
    level: 'P3 - 第四优先级',
    color: colors.warning,
    tasks: '10. AI智能推荐系统  11. 创客赛事完整功能  12. 就业对接系统  13. 数据分析与报表'
  },
  {
    level: 'P4 - 第五优先级',
    color: colors.gray,
    tasks: '14. 性能优化与监控  15. 用户反馈系统  16. 国际化支持'
  }
];

priorities.forEach((priority, i) => {
  const yPos = 1 + i * 1;

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.5, y: yPos, w: 9, h: 0.9,
    fill: { color: priority.color === colors.gray ? 'E8E8E8' : colors.light },
    line: { color: priority.color, width: 2 }
  });

  slide.addText(priority.level, {
    x: 0.6, y: yPos + 0.05, w: 8.8, h: 0.3,
    fontSize: 12, color: priority.color, bold: true
  });

  slide.addText(priority.tasks, {
    x: 0.6, y: yPos + 0.35, w: 8.8, h: 0.5,
    fontSize: 10, color: colors.text
  });
});

// ==================== 幻灯片 9: 开源与商业化 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('开源与商业化策略', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 开源策略
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1, w: 4.3, h: 4.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('开源策略', {
  x: 0.5, y: 1.1, w: 4.3, h: 0.4,
  fontSize: 18, color: colors.primary, bold: true, align: 'center'
});
slide.addText('开源范围:\n• 前端完整代码（Angular 16）\n• 后端核心功能（FastAPI）\n• 数据库Schema和API文档\n• 基础课程内容（L1-2）\n• 部署文档和运维指南\n\n开源协议:\n• 代码：AGPL-3.0\n• 课程：CC BY-NC-SA 4.0\n• AI模型：不开源（API服务）', {
  x: 0.7, y: 1.6, w: 3.9, h: 3.7,
  fontSize: 11, color: colors.text
});

// 商业化模式
slide.addShape(pptx.ShapeType.rect, {
  x: 4.9, y: 1, w: 4.2, h: 4.5,
  fill: { color: colors.light },
  line: { color: colors.primary, width: 2 }
});
slide.addText('商业化模式', {
  x: 4.9, y: 1.1, w: 4.2, h: 0.4,
  fontSize: 18, color: colors.primary, bold: true, align: 'center'
});
slide.addText('基础版（免费）\n完全免费，包含开源代码和基础课程\n适合个人教师和小型机构\n\n专业版（¥99/月）\n包含AI教师功能和智能推荐\n10,000 tokens/月配额\n适合中型机构和学校\n\n企业版（¥2999/月）\n包含定制化部署和技术支持\n100,000 tokens/月配额\n适合大型机构和教育局', {
  x: 5.1, y: 1.6, w: 3.8, h: 3.7,
  fontSize: 11, color: colors.text
});

// ==================== 幻灯片 10: 数据安全与合规 ====================
slide = pptx.addSlide();
slide.background = { color: colors.white };

slide.addText('数据安全与合规保障', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 24, fontFace: 'Arial', color: colors.primary, bold: true
});

// 四个模块
const securityModules = [
  {
    title: '🔒 数据隔离',
    content: '• 不同租户数据严格隔离（基于organization_id）\n• AI教师对话记录加密存储\n• 支付信息使用第三方平台，不直接存储敏感数据'
  },
  {
    title: '✓ 合规要求',
    content: '• 符合《个人信息保护法》\n• 学生数据脱敏处理\n• 支持数据导出和删除\n• 符合GDPR风格要求'
  },
  {
    title: '🛡️ 技术保障',
    content: '• JWT Token认证\n• 中间件权限验证\n• 租户隔离中间件\n• 完善的错误处理和日志'
  },
  {
    title: '📊 运维保障',
    content: '• 健康检查和优雅关闭\n• 容器化部署（Docker）\n• 环境变量管理配置\n• 企业版SLA 99.9%保障'
  }
];

securityModules.forEach((module, i) => {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.5 + (i % 2) * 4.6,
    y: 1 + Math.floor(i / 2) * 2.1,
    w: 4.4, h: 2,
    fill: { color: colors.light },
    line: { color: colors.primary, width: 2 }
  });
  slide.addText(module.title, {
    x: 0.5 + (i % 2) * 4.6 + 0.2,
    y: 1 + Math.floor(i / 2) * 2.1 + 0.1,
    w: 4, h: 0.35,
    fontSize: 14, color: colors.primary, bold: true
  });
  slide.addText(module.content, {
    x: 0.5 + (i % 2) * 4.6 + 0.2,
    y: 1 + Math.floor(i / 2) * 2.1 + 0.5,
    w: 4, h: 1.4,
    fontSize: 10, color: colors.text
  });
});

// 数据导出
slide.addText('数据导出与隐私: ✓ Excel报表导出  ✓ PDF报告生成  ✓ 可视化图表  ✓ 数据删除请求  ✓ GDPR风格数据导出', {
  x: 0.5, y: 5.5, w: 9, h: 0.4,
  fontSize: 11, color: colors.text
});

// ==================== 幻灯片 11: 总结与展望 ====================
slide = pptx.addSlide();
slide.background = { color: colors.primary };

slide.addText('总结与展望', {
  x: 0.5, y: 0.5, w: 9, h: 0.6,
  fontSize: 44, fontFace: 'Arial Black', color: colors.white, align: 'center'
});

slide.addText('核心价值', {
  x: 0.5, y: 1.5, w: 9, h: 0.3,
  fontSize: 18, color: colors.light, align: 'center'
});

const coreValues = [
  '开源免费，降低教育机构门槛',
  'AI赋能，提升教学效率',
  '统一体系，打通多方协作',
  '创客教育，对接市场需求',
  '灵活付费，满足不同规模需求'
];

coreValues.forEach((value, i) => {
  slide.addText(`✓ ${value}`, {
    x: 0.5, y: 1.9 + i * 0.35, w: 9, h: 0.3,
    fontSize: 14, color: colors.white, align: 'center'
  });
});

slide.addShape(pptx.ShapeType.line, {
  x: 2, y: 3.7, w: 6, h: 0,
  line: { color: colors.light, width: 2 }
});

slide.addText('下一步计划', {
  x: 0.5, y: 4, w: 9, h: 0.3,
  fontSize: 18, color: colors.light, align: 'center'
});

const nextSteps = [
  'Phase 1: 本地环境功能测试',
  'Phase 2: 云托管部署准备',
  'Phase 3: 用户入口优化',
  'Phase 4: 生产环境验证'
];

nextSteps.forEach((step, i) => {
  slide.addText(`${i + 1}. ${step}`, {
    x: 0.5, y: 4.4 + i * 0.35, w: 9, h: 0.3,
    fontSize: 14, color: colors.light, align: 'center'
  });
});

slide.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 6, w: 9, h: 0.8,
  fill: { color: colors.secondary }
});
slide.addText('📧 联系我们: info@imatuproject.com  |  🌐 官网: www.imatuproject.com', {
  x: 0.5, y: 6.2, w: 9, h: 0.4,
  fontSize: 14, color: colors.light, align: 'center'
});

// ==================== 保存PPT ====================
const outputPath = 'g:/iMato/iMato_Project_Plan_Presentation.pptx';
pptx.writeFile({ fileName: outputPath })
  .then(() => {
    console.log('PPT生成成功！');
    console.log(`保存路径: ${outputPath}`);
  })
  .catch(err => {
    console.error('PPT生成失败:', err);
  });
