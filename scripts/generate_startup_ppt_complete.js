const PptxGenJS = require("pptxgenjs");
const path = require("path");

// 创建PPT实例
const pptx = new PptxGenJS();

// 设置PPT元数据
pptx.title = "iMatuProject - AI普惠教育平台";
pptx.author = "MatuX团队";

// 颜色方案 - 科技蓝主题
const colors = {
  primary: "1E3A8A",      // 深蓝色
  secondary: "3B82F6",    // 亮蓝色
  accent: "10B981",       // 绿色
  dark: "1F2937",         // 深灰
  light: "F3F4F6",        // 浅灰
  white: "FFFFFF",
  orange: "F59E0B",        // 橙色
  purple: "8B5CF6",       // 紫色
  pink: "EC4899"           // 粉色
};

// ==================== 封面页 ====================
const slide1 = pptx.addSlide();
slide1.background = { color: colors.primary };

slide1.addText("iMatuProject", {
  x: 0.5, y: 1.2, w: 9, h: 0.9,
  fontSize: 54, bold: true, color: colors.white,
  align: "center", fontFace: "Microsoft YaHei"
});

slide1.addText("AI驱动的0基础陪伴式教育平台", {
  x: 0.5, y: 2.3, w: 9, h: 0.7,
  fontSize: 32, bold: true, color: colors.secondary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide1.addText("—— 创业大赛商业计划书 ——", {
  x: 0.5, y: 3.2, w: 9, h: 0.5,
  fontSize: 20, color: colors.light,
  align: "center", fontFace: "Microsoft YaHei"
});

const highlights = [
  "AI智能体技术",
  "软硬一体教育",
  "普惠公益生态",
  "下沉市场覆盖",
  "自适应学习引擎"
];

const highlightText = highlights.join("  •  ");
slide1.addText(highlightText, {
  x: 1.2, y: 4.3, w: 7.6, h: 1.2,
  align: "center", valign: "middle", fontFace: "Microsoft YaHei",
  fontSize: 18, color: colors.light
});

slide1.addText(new Date().toLocaleDateString("zh-CN"), {
  x: 4.5, y: 6.8, w: 1.5, h: 0.3,
  fontSize: 12, color: colors.light,
  align: "center", fontFace: "Microsoft YaHei"
});

// ==================== 目录页 ====================
const slide2 = pptx.addSlide();
slide2.background = { color: colors.white };

slide2.addText("目录", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const tocItems = [
  "项目背景与愿景",
  "全球AI教育发展趋势",
  "普惠教育解决方案",
  "六大核心模块详解",
  "商业模式与ROI",
  "实施规划与风险控制"
];

tocItems.forEach((item, index) => {
  slide2.addText(`${index + 1}.  ${item}`, {
    x: 1.2, y: 1.2 + index * 0.75, w: 7.6, h: 0.55,
    fontSize: 18, fontFace: "Microsoft YaHei", bold: true,
    color: colors.primary
  });
});

// ==================== 项目背景页 ====================
const slide3 = pptx.addSlide();
slide3.background = { color: colors.white };

slide3.addText("项目背景：教育资源的巨大鸿沟", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const problems = [
  { title: "下沉市场教育资源匮乏", desc: "中国3-4线城市及县城中小学学生人数占比80%，但机器人教育资源严重不足", icon: "🏫" },
  { title: "专业教师成本高昂", desc: "传统机器人课程需要专业教师，县域学校难以承担每年数千元的师资费用", icon: "👩‍🏫" },
  { title: "硬件设备门槛高", desc: "传统机器人课程套装价格5000元/年，远超普通家庭承受能力", icon: "💰" },
  { title: "网络基础设施不足", desc: "偏远地区网络不稳定，纯在线教育无法有效覆盖", icon: "📶" }
];

problems.forEach((problem, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);
  
  slide3.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.5, y: 1.2 + row * 2.3, w: 4.2, h: 2.1,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 2 }
  });

  slide3.addText(problem.title, {
    x: 0.7 + col * 4.5, y: 1.35 + row * 2.3, w: 3.8, h: 0.45,
    fontSize: 15, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide3.addText(problem.desc, {
    x: 0.7 + col * 4.5, y: 1.85 + row * 2.3, w: 3.8, h: 1.35,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 愿景与使命页 ====================
const slide4 = pptx.addSlide();
slide4.background = { color: colors.white };

slide4.addText("我们的愿景与使命", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide4.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 1.1, w: 8.8, h: 2.8,
  fill: { color: colors.primary }
});

slide4.addText("愿景：让每个孩子都能享受优质的AI教育", {
  x: 0.7, y: 1.8, w: 8.4, h: 1.8,
  fontSize: 28, bold: true, color: colors.white,
  align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

slide4.addText("使命：通过AI智能体技术，为下沉市场提供0基础陪伴式教育服务", {
  x: 0.5, y: 4.2, w: 9, h: 0.8,
  fontSize: 20, bold: true, color: colors.secondary,
  align: "center", fontFace: "Microsoft YaHei"
});

const metrics = [
  { label: "目标覆盖", value: "1.44亿学生" },
  { label: "成本降低", value: "99%" },
  { label: "AI替代", value: "80%常规教学" },
  { label: "硬件成本", value: "≤30元/年" }
];

metrics.forEach((metric, index) => {
  slide4.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 5.3, w: 2, h: 1.3,
    fill: { color: colors.light },
    line: { color: colors.accent, width: 2 }
  });

  slide4.addText(metric.value, {
    x: 0.5 + index * 2.25, y: 5.5, w: 2, h: 0.6,
    fontSize: 24, bold: true, color: colors.accent,
    align: "center", fontFace: "Arial"
  });

  slide4.addText(metric.label, {
    x: 0.5 + index * 2.25, y: 6.1, w: 2, h: 0.4,
    fontSize: 11, color: colors.dark,
    align: "center", fontFace: "Microsoft YaHei"
  });
});

// ==================== 全球AI教育发展趋势页 ====================
const slide5 = pptx.addSlide();
slide5.background = { color: colors.white };

slide5.addText("全球人工智能教育发展趋势", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const trendData = [
  { title: "市场规模爆发式增长", value: "8910亿", year: "2028年中国", cagr: "CAGR 37%", color: colors.primary },
  { title: "AI教育快速渗透", value: "476亿", year: "2027年预计", cagr: "CAGR 20%+", color: colors.secondary },
  { title: "元宇宙教育兴起", value: "93.8亿", year: "2023年中国", cagr: "CAGR 17%", color: colors.accent },
  { title: "STEM教育扩容", value: "200亿美元", year: "2024年中国", cagr: "CAGR 15%+", color: colors.purple }
];

trendData.forEach((trend, index) => {
  slide5.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 1.1, w: 2, h: 2.4,
    fill: { color: trend.color }
  });

  slide5.addText(trend.title, {
    x: 0.5 + index * 2.25, y: 1.2, w: 2, h: 0.6,
    fontSize: 12, bold: true, color: colors.white,
    align: "center", fontFace: "Microsoft YaHei"
  });

  slide5.addText(trend.value, {
    x: 0.5 + index * 2.25, y: 1.8, w: 2, h: 0.5,
    fontSize: 26, bold: true, color: colors.white,
    align: "center", fontFace: "Arial"
  });

  slide5.addText(trend.year, {
    x: 0.5 + index * 2.25, y: 2.3, w: 2, h: 0.3,
    fontSize: 10, color: colors.light,
    align: "center", fontFace: "Microsoft YaHei"
  });

  slide5.addText(trend.cagr, {
    x: 0.5 + index * 2.25, y: 2.95, w: 2, h: 0.4,
    fontSize: 12, bold: true, color: colors.accent,
    align: "center", fontFace: "Arial"
  });
});

// 核心趋势
slide5.addText("核心发展趋势", {
  x: 0.5, y: 3.8, w: 2, h: 0.4,
  fontSize: 18, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const coreTrends = [
  "从辅助教学到核心驱动的转变",
  "个性化、自适应学习成为标配",
  "软硬结合教育模式快速发展",
  "AI降低教育门槛，实现普惠教育",
  "元宇宙和AR/VR技术深度应用",
  "教育公平与社会价值被高度重视"
];

coreTrends.forEach((trendText, index) => {
  const row = Math.floor(index / 2);
  const col = index % 2;
  
  slide5.addShape(pptx.ShapeType.ellipse, {
    x: 0.7 + col * 4.5, y: 4.4 + row * 0.55, w: 0.16, h: 0.14,
    fill: { color: colors.accent }
  });

  slide5.addText(trendText, {
    x: 1 + col * 4.5, y: 4.35 + row * 0.55, w: 3.9, h: 0.4,
    fontSize: 12, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 普惠教育解决方案页 ====================
const slide6 = pptx.addSlide();
slide6.background = { color: colors.white };

slide6.addText("普惠教育解决方案", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

// 核心思路
slide6.addText("核心思路：AI Agent + 低成本硬件 + 手机终端", {
  x: 0.5, y: 1.1, w: 9, h: 0.5,
  fontSize: 18, bold: true, color: colors.secondary, fontFace: "Microsoft YaHei"
});

const solutions = [
  {
    title: "极低成本硬件",
    items: [
      "定制Arduino Nano/ESP32，成本≤20元",
      "集成基础传感器（温湿度、光敏、LED）",
      "Type-C直连手机，无需电脑"
    ],
    color: colors.primary
  },
  {
    title: "手机即终端",
    items: [
      "利用家长旧手机或学生自有手机",
      "蓝牙/OTG连接硬件",
      "手机算力运行AI服务"
    ],
    color: colors.secondary
  },
  {
    title: "AI智能体替代",
    items: [
      "AI虚拟导师：基于MiniCPM等轻量模型",
      "处理80%常规教学问题",
      "复杂问题转接高校志愿者"
    ],
    color: colors.accent
  },
  {
    title: "公益生态运营",
    items: [
      "基础功能完全免费",
      "B端合作分摊成本",
      "C端零付费，增值服务由公益基金赞助"
    ],
    color: colors.purple
  }
];

solutions.forEach((solution, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);
  
  slide6.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.5, y: 1.8 + row * 2, w: 4.2, h: 1.8,
    fill: { color: colors.light },
    line: { color: solution.color, width: 3 }
  });

  slide6.addText(solution.title, {
    x: 0.7 + col * 4.5, y: 1.9 + row * 2, w: 3.8, h: 0.4,
    fontSize: 15, bold: true, color: solution.color, fontFace: "Microsoft YaHei"
  });

  solution.items.forEach((item, itemIndex) => {
    slide6.addText(`• ${item}`, {
      x: 0.7 + col * 4.5, y: 2.35 + row * 2 + itemIndex * 0.4, w: 3.8, h: 0.35,
      fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// ==================== 核心模块总览页 ====================
const slide7 = pptx.addSlide();
slide7.background = { color: colors.white };

slide7.addText("六大核心模块总览", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const modules = [
  { name: "AI智能教育", icon: "🤖", color: colors.primary },
  { name: "AR/VR沉浸式学习", icon: "🥽", color: colors.secondary },
  { name: "边缘AI硬件", icon: "🔌", color: colors.accent },
  { name: "区块链积分认证", icon: "⛓", color: colors.purple },
  { name: "软硬结合实训", icon: "🔬", color: colors.orange },
  { name: "游戏化激励系统", icon: "🎮", color: colors.pink }
];

modules.forEach((module, index) => {
  const col = index % 3;
  const row = Math.floor(index / 3);
  
  slide7.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 3, y: 1.2 + row * 2.2, w: 2.8, h: 2,
    fill: { color: colors.light },
    line: { color: module.color, width: 3 }
  });

  slide7.addText(module.name, {
    x: 0.5 + col * 3, y: 1.3 + row * 2.2, w: 2.8, h: 0.5,
    fontSize: 14, bold: true, color: module.color,
    align: "center", fontFace: "Microsoft YaHei"
  });

  slide7.addText(module.icon, {
    x: 1.5 + col * 3, y: 2.0 + row * 2.2, w: 0.8, h: 0.6,
    fontSize: 40, align: "center"
  });
});

// ==================== 模块1：AI智能教育（第1页）- 核心能力 ====================
const slide8 = pptx.addSlide();
slide8.background = { color: colors.white };

slide8.addText("核心模块一：AI智能教育", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide8.addText("核心能力：基于大语言模型的个性化学习助手", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.secondary, fontFace: "Microsoft YaHei"
});

const aiCapabilities = [
  {
    title: "AI虚拟导师",
    desc: "基于MiniCPM-2B轻量模型，支持中英文，4GB内存可运行，端侧推理保护隐私",
    metrics: [
      { label: "响应时间", value: "0.8秒" },
      { label: "准确率", value: "90%" },
      { label: "支持语言", value: "中英文" }
    ]
  },
  {
    title: "对话式学习",
    desc: "5轮对话窗口，上下文感知，RAG知识库增强，实时问答解惑",
    metrics: [
      { label: "对话轮数", value: "5轮" },
      { label: "知识库", value: "3大类" },
      { label: "RAG检索", value: "实时" }
    ]
  }
];

aiCapabilities.forEach((cap, index) => {
  slide8.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 4.5, y: 1.6, w: 4.2, h: 3.2,
    fill: { color: colors.light },
    line: { color: colors.primary, width: 2 }
  });

  slide8.addText(cap.title, {
    x: 0.7 + index * 4.5, y: 1.75, w: 3.8, h: 0.45,
    fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide8.addText(cap.desc, {
    x: 0.7 + index * 4.5, y: 2.3, w: 3.8, h: 1.3,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  cap.metrics.forEach((metric, metricIndex) => {
    slide8.addText(`${metric.label}:`, {
      x: 0.7 + index * 4.5, y: 3.7 + metricIndex * 0.35, w: 1.5, h: 0.3,
      fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
    });

    slide8.addText(metric.value, {
      x: 2.3 + index * 4.5, y: 3.7 + metricIndex * 0.35, w: 2.2, h: 0.3,
      fontSize: 11, bold: true, color: colors.accent, fontFace: "Arial"
    });
  });
});

// 技术栈
slide8.addText("技术栈", {
  x: 0.5, y: 5.2, w: 1.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const techStack = [
  "MiniCPM-2B（2B参数轻量LLM）",
  "LangChain（对话式AI框架）",
  "RAG（检索增强生成）",
  "MLC-LLM（端侧推理优化）",
  "Vector Database（知识库存储）"
];

techStack.forEach((tech, index) => {
  slide8.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 1.8, y: 5.7, w: 1.6, h: 0.8,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 1 }
  });

  slide8.addText(tech, {
    x: 0.6 + index * 1.8, y: 5.9, w: 1.4, h: 0.6,
    fontSize: 10, color: colors.dark,
    align: "center", valign: "middle", fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块1：AI智能教育（第2页）- 普惠价值 ====================
const slide9 = pptx.addSlide();
slide9.background = { color: colors.white };

slide9.addText("核心模块一：AI智能教育（续）", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide9.addText("普惠价值：AI替代80%常规教学，降低师资成本", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

// 成本对比
slide9.addText("成本对比", {
  x: 0.5, y: 1.7, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const costComparison = [
  { label: "传统模式", teacher: "1200元/月", ai: "无", total: "5000元/年" },
  { label: "AI模式", teacher: "0元", ai: "本地运行", total: "30元/年" },
  { label: "成本降低", teacher: "100%", ai: "端侧计算", total: "99.4%" }
];

costComparison.forEach((cost, index) => {
  const bgColors = [colors.light, colors.accent, colors.primary];
  
  slide9.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 2.2 + index * 0.6, w: 1.5, h: 0.5,
    fill: { color: index === 2 ? colors.accent : colors.light },
    line: { color: colors.primary, width: 1 }
  });

  slide9.addText(cost.label, {
    x: 0.6, y: 2.35 + index * 0.6, w: 1.3, h: 0.4,
    fontSize: 12, bold: true, color: index === 2 ? colors.white : colors.primary,
    align: "center", valign: "middle", fontFace: "Microsoft YaHei"
  });

  slide9.addText(`师资: ${cost.teacher}`, {
    x: 2.1, y: 2.35 + index * 0.6, w: 2.5, h: 0.35,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide9.addText(`AI: ${cost.ai}`, {
    x: 4.7, y: 2.35 + index * 0.6, w: 2, h: 0.35,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide9.addText(`总计: ${cost.total}`, {
    x: 6.8, y: 2.35 + index * 0.6, w: 2.4, h: 0.35,
    fontSize: 11, bold: true, color: index === 2 ? colors.accent : colors.primary, fontFace: "Arial"
  });
});

// 下沉市场覆盖
slide9.addText("下沉市场覆盖", {
  x: 0.5, y: 4.3, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const marketCoverage = [
  { label: "全国中小学生", value: "1.8亿人" },
  { label: "下沉市场占比", value: "80%" },
  { label: "目标覆盖", value: "1.44亿人" },
  { label: "县域学校", value: "10万所+" }
];

marketCoverage.forEach((market, index) => {
  slide9.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 4.8, w: 2, h: 1.3,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 2 }
  });

  slide9.addText(market.value, {
    x: 0.5 + index * 2.25, y: 5, w: 2, h: 0.6,
    fontSize: 26, bold: true, color: colors.accent,
    align: "center", fontFace: "Arial"
  });

  slide9.addText(market.label, {
    x: 0.5 + index * 2.25, y: 5.6, w: 2, h: 0.4,
    fontSize: 11, color: colors.dark,
    align: "center", fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块2：AR/VR沉浸式学习（第1页）- 虚拟实验室 ====================
const slide10 = pptx.addSlide();
slide10.background = { color: colors.white };

slide10.addText("核心模块二：AR/VR沉浸式学习", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.secondary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide10.addText("虚拟实验室：256个3D电子元件模型", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.secondary, fontFace: "Microsoft YaHei"
});

const labFeatures = [
  {
    title: "3D模型库",
    desc: "从KiCad官方库精选256个常用电子元件（电阻、电容、IC、LED等），三级LOD优化",
    metrics: [
      { label: "模型数量", value: "256个" },
      { label: "LOD级别", value: "3级" },
      { label: "单模型大小", value: "1.2MB" }
    ]
  },
  {
    title: "虚拟仿真",
    desc: "LED亮灭模拟、开关控制、电气规则检查，降低实体硬件损耗",
    metrics: [
      { label: "仿真响应", value: "50ms" },
      { label: "吸附精度", value: "2cm" },
      { label: "成功率高", value: "98%" }
    ]
  }
];

labFeatures.forEach((feature, index) => {
  slide10.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 4.5, y: 1.6, w: 4.2, h: 3.2,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 2 }
  });

  slide10.addText(feature.title, {
    x: 0.7 + index * 4.5, y: 1.75, w: 3.8, h: 0.45,
    fontSize: 16, bold: true, color: colors.secondary, fontFace: "Microsoft YaHei"
  });

  slide10.addText(feature.desc, {
    x: 0.7 + index * 4.5, y: 2.3, w: 3.8, h: 1.3,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  feature.metrics.forEach((metric, metricIndex) => {
    slide10.addText(`${metric.label}:`, {
      x: 0.7 + index * 4.5, y: 3.7 + metricIndex * 0.35, w: 1.5, h: 0.3,
      fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
    });

    slide10.addText(metric.value, {
      x: 2.3 + index * 4.5, y: 3.7 + metricIndex * 0.35, w: 2.2, h: 0.3,
      fontSize: 11, bold: true, color: colors.accent, fontFace: "Arial"
    });
  });
});

// 技术栈
slide10.addText("技术栈", {
  x: 0.5, y: 5.2, w: 1.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const arTechStack = [
  "Unity 3D引擎",
  "ARFoundation",
  "Vircadia平台",
  "KiCad模型库",
  "Ammo.js物理引擎"
];

arTechStack.forEach((tech, index) => {
  slide10.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 1.8, y: 5.7, w: 1.6, h: 0.8,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 1 }
  });

  slide10.addText(tech, {
    x: 0.6 + index * 1.8, y: 5.9, w: 1.4, h: 0.6,
    fontSize: 10, color: colors.dark,
    align: "center", valign: "middle", fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块2：AR/VR沉浸式学习（第2页）- AR实时指导 ====================
const slide11 = pptx.addSlide();
slide11.background = { color: colors.white };

slide11.addText("核心模块二：AR/VR沉浸式学习（续）", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.secondary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide11.addText("AR实时指导：降低操作门槛，提升学习效率", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

const arFeatures = [
  {
    title: "硬件识别",
    desc: "手机摄像头识别面包板接线状态，实时检测硬件连接",
    capabilities: [
      "面包板网格识别",
      "杜邦线连接检测",
      "元件位置定位",
      "极性验证"
    ]
  },
  {
    title: "虚拟指引",
    desc: "AR叠加虚拟导线动画，预置5种常见错误场景提示",
    capabilities: [
      "正确接线路径显示",
      "错误实时纠错提示",
      "3D虚拟元件叠加",
      "语音指导配合"
    ]
  },
  {
    title: "MediaPipe手势",
    desc: "18种手势支持，复杂序列检测与隐藏任务触发",
    capabilities: [
      "点击/双击识别",
      "缩放/旋转操作",
      "自定义手势序列",
      "多模态交互联动"
    ]
  }
];

arFeatures.forEach((feature, index) => {
  slide11.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.7, w: 2.8, h: 3.4,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 2 }
  });

  slide11.addText(feature.title, {
    x: 0.7 + index * 3, y: 1.85, w: 2.4, h: 0.45,
    fontSize: 14, bold: true, color: colors.secondary, fontFace: "Microsoft YaHei"
  });

  slide11.addText(feature.desc, {
    x: 0.7 + index * 3, y: 2.35, w: 2.4, h: 1.0,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  feature.capabilities.forEach((cap, capIndex) => {
    slide11.addText(`• ${cap}`, {
      x: 0.7 + index * 3, y: 3.4 + capIndex * 0.35, w: 2.4, h: 0.3,
      fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// 普惠价值
slide11.addText("普惠价值", {
  x: 0.5, y: 5.5, w: 1.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const arValue = [
  { label: "虚拟仿真", desc: "降低硬件损耗率80%" },
  { label: "AR指导", desc: "减少教师指导需求" },
  { label: "离线运行", desc: "适配网络不稳定地区" },
  { label: "降低门槛", desc: "0基础学生独立完成" }
];

arValue.forEach((val, index) => {
  slide11.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 6, w: 2, h: 0.7,
    fill: { color: colors.light },
    line: { color: colors.accent, width: 1 }
  });

  slide11.addText(val.label, {
    x: 0.6 + index * 2.25, y: 6.1, w: 1.8, h: 0.25,
    fontSize: 11, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide11.addText(val.desc, {
    x: 0.6 + index * 2.25, y: 6.4, w: 1.8, h: 0.25,
    fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块3：边缘AI硬件（第1页）- 核心技术 ====================
const slide12 = pptx.addSlide();
slide12.background = { color: colors.white };

slide12.addText("核心模块三：边缘AI硬件", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.accent,
  align: "center", fontFace: "Microsoft YaHei"
});

slide12.addText("ESP32 TinyML语音识别系统：95%准确率，640ms响应", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

const hardwareMetrics = [
  { label: "识别准确率", value: "95%", target: "≥85%" },
  { label: "响应延迟", value: "640ms", target: "≤1000ms" },
  { label: "内存使用", value: "335KB", target: "62.9% of 520KB" },
  { label: "电池续航", value: "22.7h", target: "≥8小时" },
  { label: "离线运行", value: "完全", target: "无需网络" },
  { label: "BLE热更新", value: "支持", target: "无线推送" }
];

hardwareMetrics.forEach((metric, index) => {
  const col = index % 3;
  const row = Math.floor(index / 3);
  
  slide12.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 3, y: 1.7 + row * 1.4, w: 2.8, h: 1.2,
    fill: { color: colors.light },
    line: { color: colors.accent, width: 2 }
  });

  slide12.addText(metric.value, {
    x: 0.5 + col * 3, y: 2 + row * 1.4, w: 2.8, h: 0.5,
    fontSize: 26, bold: true, color: colors.accent,
    align: "center", fontFace: "Arial"
  });

  slide12.addText(metric.label, {
    x: 0.5 + col * 3, y: 2.55 + row * 1.4, w: 2.8, h: 0.3,
    fontSize: 11, color: colors.dark,
    align: "center", fontFace: "Microsoft YaHei"
  });
});

// 核心功能
slide12.addText("核心功能", {
  x: 0.5, y: 4.3, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const coreFeatures = [
  "本地AI模型推理（TensorFlow Lite Micro）",
  "离线语音指令识别（开灯/关灯等）",
  "BLE模型热更新（无线推送新模型）",
  "完全离线运行（无需网络连接）",
  "边缘计算（隐私保护）",
  "低功耗设计（22.7小时续航）"
];

coreFeatures.forEach((feature, index) => {
  slide12.addShape(pptx.ShapeType.ellipse, {
    x: 0.7 + (index % 3) * 3, y: 4.85 + Math.floor(index / 3) * 0.55, w: 0.16, h: 0.14,
    fill: { color: colors.accent }
  });

  slide12.addText(feature, {
    x: 1 + (index % 3) * 3, y: 4.8 + Math.floor(index / 3) * 0.55, w: 2.4, h: 0.4,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块3：边缘AI硬件（第2页）- 普惠价值 ====================
const slide13 = pptx.addSlide();
slide13.background = { color: colors.white };

slide13.addText("核心模块三：边缘AI硬件（续）", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.accent,
  align: "center", fontFace: "Microsoft YaHei"
});

slide13.addText("普惠价值：极低成本硬件，适配下沉市场", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

// 硬件成本对比
slide13.addText("硬件成本对比", {
  x: 0.5, y: 1.7, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const hardwareCostComparison = [
  { item: "定制Arduino板", our: "12元", traditional: "80元", save: "85%" },
  { item: "传感器包", our: "8元", traditional: "50元", save: "84%" },
  { item: "包装物流", our: "5元", traditional: "20元", save: "75%" },
  { item: "单套总计", our: "25元", traditional: "5000元/年", save: "99.5%" }
];

hardwareCostComparison.forEach((cost, index) => {
  slide13.addText(cost.item, {
    x: 0.5, y: 2.2 + index * 0.6, w: 2, h: 0.4,
    fontSize: 12, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide13.addText(`我们: ${cost.our}`, {
    x: 2.6, y: 2.2 + index * 0.6, w: 2, h: 0.35,
    fontSize: 12, bold: true, color: colors.accent, fontFace: "Arial"
  });

  slide13.addText(`传统: ${cost.traditional}`, {
    x: 4.7, y: 2.2 + index * 0.6, w: 2.5, h: 0.35,
    fontSize: 12, color: colors.dark, fontFace: "Arial"
  });

  slide13.addText(`节省: ${cost.save}`, {
    x: 7.3, y: 2.2 + index * 0.6, w: 1.8, h: 0.35,
    fontSize: 12, bold: true, color: colors.accent, fontFace: "Arial"
  });
});

// 下沉市场适配
slide13.addText("下沉市场适配", {
  x: 0.5, y: 4.8, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const marketFit = [
  { label: "手机直连", desc: "无需电脑，利用家长旧手机" },
  { label: "Type-C接口", desc: "通用充电接口，降低学习门槛" },
  { label: "离线运行", desc: "适配网络不稳定地区" },
  { label: "即插即用", desc: "无需驱动，无需安装" }
];

marketFit.forEach((fit, index) => {
  slide13.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 5.3, w: 2, h: 1,
    fill: { color: colors.light },
    line: { color: colors.accent, width: 1 }
  });

  slide13.addText(fit.label, {
    x: 0.6 + index * 2.25, y: 5.45, w: 1.8, h: 0.35,
    fontSize: 12, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide13.addText(fit.desc, {
    x: 0.6 + index * 2.25, y: 5.85, w: 1.8, h: 0.35,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块4：区块链积分认证（第1页）- 技术架构 ====================
const slide14 = pptx.addSlide();
slide14.background = { color: colors.white };

slide14.addText("核心模块四：区块链积分认证", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.purple,
  align: "center", fontFace: "Microsoft YaHei"
});

slide14.addText("Hyperledger Fabric企业级区块链网络", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.purple, fontFace: "Microsoft YaHei"
});

const blockchainFeatures = [
  {
    title: "企业级网络架构",
    desc: "三组织Raft共识集群，Hyperledger Fabric 2.x，企业级安全认证",
    capabilities: ["三组织架构", "Raft共识", "企业级安全", "TLS加密通信"]
  },
  {
    title: "智能合约系统",
    desc: "Go语言链码实现积分管理系统，完整的权限控制体系",
    capabilities: ["Go语言链码", "积分管理", "MSP身份认证", "访问控制"]
  }
];

blockchainFeatures.forEach((feature, index) => {
  slide14.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 4.5, y: 1.6, w: 4.2, h: 2.8,
    fill: { color: colors.light },
    line: { color: colors.purple, width: 2 }
  });

  slide14.addText(feature.title, {
    x: 0.7 + index * 4.5, y: 1.75, w: 3.8, h: 0.45,
    fontSize: 16, bold: true, color: colors.purple, fontFace: "Microsoft YaHei"
  });

  slide14.addText(feature.desc, {
    x: 0.7 + index * 4.5, y: 2.3, w: 3.8, h: 0.9,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  feature.capabilities.forEach((cap, capIndex) => {
    slide14.addText(`• ${cap}`, {
      x: 0.7 + index * 4.5, y: 3.25 + capIndex * 0.35, w: 3.8, h: 0.3,
      fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// 技术栈
slide14.addText("技术栈", {
  x: 0.5, y: 4.8, w: 1.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const blockchainTechStack = [
  "Hyperledger Fabric",
  "Raft共识算法",
  "Go智能合约",
  "MSP身份认证",
  "TLS加密通信",
  "Docker容器化"
];

blockchainTechStack.forEach((tech, index) => {
  slide14.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 1.5, y: 5.3, w: 1.3, h: 0.8,
    fill: { color: colors.light },
    line: { color: colors.purple, width: 1 }
  });

  slide14.addText(tech, {
    x: 0.6 + index * 1.5, y: 5.5, w: 1.1, h: 0.6,
    fontSize: 9, color: colors.dark,
    align: "center", valign: "middle", fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块4：区块链积分认证（第2页）- 普惠价值 ====================
const slide15 = pptx.addSlide();
slide15.background = { color: colors.white };

slide15.addText("核心模块四：区块链积分认证（续）", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.purple,
  align: "center", fontFace: "Microsoft YaHei"
});

slide15.addText("普惠价值：积分不可篡改，学习成果可信认证", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

// 积分系统特性
slide15.addText("积分系统特性", {
  x: 0.5, y: 1.7, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const pointFeatures = [
  { title: "不可篡改", desc: "区块链存证，积分永久保存" },
  { title: "跨机构认可", desc: "积分可兑换课程、硬件、服务" },
  { title: "智能衰减", desc: "指数/线性/阶梯式衰减算法" },
  { title: "多模态奖励", desc: "语音/AR/手势联动积分系统" }
];

pointFeatures.forEach((feature, index) => {
  slide15.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 2.2, w: 2, h: 1.2,
    fill: { color: colors.light },
    line: { color: colors.purple, width: 2 }
  });

  slide15.addText(feature.title, {
    x: 0.6 + index * 2.25, y: 2.35, w: 1.8, h: 0.4,
    fontSize: 13, bold: true, color: colors.purple, fontFace: "Microsoft YaHei"
  });

  slide15.addText(feature.desc, {
    x: 0.6 + index * 2.25, y: 2.8, w: 1.8, h: 0.5,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// 积分获取方式
slide15.addText("积分获取方式", {
  x: 0.5, y: 3.8, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const pointMethods = [
  { method: "完成课程", points: "50积分/课时" },
  { method: "项目创作", points: "100积分/优质" },
  { method: "社区贡献", points: "100积分/贡献" },
  { method: "邀请新用户", points: "200积分/人" }
];

pointMethods.forEach((pm, index) => {
  slide15.addText(pm.method, {
    x: 0.5 + index * 2.25, y: 4.3, w: 2, h: 0.35,
    fontSize: 12, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide15.addText(pm.points, {
    x: 0.5 + index * 2.25, y: 4.65, w: 2, h: 0.35,
    fontSize: 12, bold: true, color: colors.accent, fontFace: "Arial"
  });
});

// 积分兑换
slide15.addText("积分兑换", {
  x: 0.5, y: 5.4, w: 1.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const pointExchange = [
  { item: "基础套件", cost: "2000积分", value: "成本20元" },
  { item: "专家答疑", cost: "500积分", value: "成本15元/次" },
  { item: "限定课程", cost: "1000积分", value: "解锁权限" }
];

pointExchange.forEach((ex, index) => {
  slide15.addText(ex.item, {
    x: 2.2 + index * 2.3, y: 5.5, w: 2.2, h: 0.35,
    fontSize: 12, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide15.addText(ex.cost, {
    x: 2.2 + index * 2.3, y: 5.85, w: 2.2, h: 0.35,
    fontSize: 12, bold: true, color: colors.accent, fontFace: "Arial"
  });
});

// ==================== 模块5：软硬结合实训（第1页）- OpenHydra集成 ====================
const slide16 = pptx.addSlide();
slide16.background = { color: colors.white };

slide16.addText("核心模块五：软硬结合实训", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.orange,
  align: "center", fontFace: "Microsoft YaHei"
});

slide16.addText("OpenHydra + XEdu深度融合：软硬结合完整学习闭环", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.orange, fontFace: "Microsoft YaHei"
});

const integrationFeatures = [
  {
    title: "OpenHydra K8s实训环境",
    desc: "Kubernetes容器化实训环境，支持真实项目部署",
    capabilities: ["K8s集群管理", "容器化部署", "真实环境模拟", "团队协作实训"]
  },
  {
    title: "XEdu AI工具链",
    desc: "中小学AI教育工具链，MMEdu框架深度集成",
    capabilities: ["AI模型训练", "ResNet-18分类", "92%准确率", "24小时加速"]
  },
  {
    title: "跨平台任务编排",
    desc: "OpenHydra ↔ MatuX双向通信，自动评分系统",
    capabilities: ["双向通信", "自动评分", "排行榜系统", "实时追踪"]
  }
];

integrationFeatures.forEach((feature, index) => {
  slide16.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.6, w: 2.8, h: 2.8,
    fill: { color: colors.light },
    line: { color: colors.orange, width: 2 }
  });

  slide16.addText(feature.title, {
    x: 0.7 + index * 3, y: 1.75, w: 2.4, h: 0.45,
    fontSize: 14, bold: true, color: colors.orange, fontFace: "Microsoft YaHei"
  });

  slide16.addText(feature.desc, {
    x: 0.7 + index * 3, y: 2.25, w: 2.4, h: 0.7,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  feature.capabilities.forEach((cap, capIndex) => {
    slide16.addText(`• ${cap}`, {
      x: 0.7 + index * 3, y: 3.0 + capIndex * 0.35, w: 2.4, h: 0.3,
      fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// 示范项目
slide16.addText("示范项目：智能温室监控系统", {
  x: 0.5, y: 4.7, w: 5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const greenhouse = [
  { phase: "阶段1", task: "AI模型训练", detail: "ResNet-18植物健康分类，准确率92%" },
  { phase: "阶段2", task: "硬件模拟集成", detail: "虚拟传感器网络，24小时加速模拟" },
  { phase: "阶段3", task: "成果展示竞赛", detail: "自动评审系统，金/银/铜奖" }
];

greenhouse.forEach((gh, index) => {
  slide16.addText(`${gh.phase}: ${gh.task}`, {
    x: 0.5 + index * 3, y: 5.2, w: 2.8, h: 0.35,
    fontSize: 11, bold: true, color: colors.orange, fontFace: "Microsoft YaHei"
  });

  slide16.addText(gh.detail, {
    x: 0.5 + index * 3, y: 5.55, w: 2.8, h: 0.5,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块5：软硬结合实训（第2页）- 普惠价值 ====================
const slide17 = pptx.addSlide();
slide17.background = { color: colors.white };

slide17.addText("核心模块五：软硬结合实训（续）", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.orange,
  align: "center", fontFace: "Microsoft YaHei"
});

slide17.addText("普惠价值：培养基层AI+硬件技能，对接新职业", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

// 职业对接
slide17.addText("职业对接：赋能新职业技能", {
  x: 0.5, y: 1.7, w: 4, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const careerMapping = [
  { skill: "智能家居安装", jobs: ["智能家居", "家庭自动化"], salary: "6000-8000元/月" },
  { skill: "物联网设备运维", jobs: ["IoT工程师", "设备维护"], salary: "8000-12000元/月" },
  { skill: "边缘AI开发", jobs: ["边缘计算", "AI部署"], salary: "10000-15000元/月" }
];

careerMapping.forEach((cm, index) => {
  slide17.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 2.2, w: 2.8, h: 1.8,
    fill: { color: colors.light },
    line: { color: colors.orange, width: 2 }
  });

  slide17.addText(cm.skill, {
    x: 0.7 + index * 3, y: 2.35, w: 2.4, h: 0.4,
    fontSize: 13, bold: true, color: colors.orange, fontFace: "Microsoft YaHei"
  });

  slide17.addText(`就业方向: ${cm.jobs.join(" / ")}`, {
    x: 0.7 + index * 3, y: 2.8, w: 2.4, h: 0.5,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide17.addText(`薪资: ${cm.salary}`, {
    x: 0.7 + index * 3, y: 3.35, w: 2.4, h: 0.4,
    fontSize: 11, bold: true, color: colors.accent, fontFace: "Arial"
  });
});

// 地方产业对接
slide17.addText("地方产业对接", {
  x: 0.5, y: 4.3, w: 2.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const industry = [
  { type: "农业", course: "水质监测传感器", target: "水产养殖" },
  { type: "制造业", course: "工业自动化模拟", target: "工厂产线" },
  { type: "服务业", course: "智能家居项目", target: "家庭服务" },
  { type: "环境", course: "空气质量监测", target: "环保监测" }
];

industry.forEach((ind, index) => {
  slide17.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 4.8, w: 2, h: 1.3,
    fill: { color: colors.light },
    line: { color: colors.accent, width: 1 }
  });

  slide17.addText(`${ind.type}行业`, {
    x: 0.6 + index * 2.25, y: 4.95, w: 1.8, h: 0.3,
    fontSize: 11, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide17.addText(`课程: ${ind.course}`, {
    x: 0.6 + index * 2.25, y: 5.3, w: 1.8, h: 0.35,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide17.addText(`对接: ${ind.target}`, {
    x: 0.6 + index * 2.25, y: 5.65, w: 1.8, h: 0.35,
    fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块6：游戏化激励系统（第1页）- 核心机制 ====================
const slide18 = pptx.addSlide();
slide18.background = { color: colors.white };

slide18.addText("核心模块六：游戏化激励系统", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.pink,
  align: "center", fontFace: "Microsoft YaHei"
});

slide18.addText("成就系统 + 积分排行榜：提升85%参与度", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.pink, fontFace: "Microsoft YaHei"
});

const gamificationFeatures = [
  {
    title: "成就系统",
    desc: "6种成就类型，4大分类，自动解锁检测",
    achievements: ["累计成就", "单次成就", "序列成就", "隐藏成就"],
    stats: "API端点: 10+ | 测试覆盖: 85% | 代码行数: 1,261行"
  },
  {
    title: "积分排行榜",
    desc: "6维度排行榜，4时间周期，积分管理系统",
    rankings: ["总积分榜", "学习时长榜", "课程数榜", "测验分榜"],
    stats: "API端点: 8+ | 测试覆盖: 82% | 代码行数: 1,159行"
  }
];

gamificationFeatures.forEach((feature, index) => {
  slide18.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 4.5, y: 1.6, w: 4.2, h: 3.2,
    fill: { color: colors.light },
    line: { color: colors.pink, width: 2 }
  });

  slide18.addText(feature.title, {
    x: 0.7 + index * 4.5, y: 1.75, w: 3.8, h: 0.45,
    fontSize: 16, bold: true, color: colors.pink, fontFace: "Microsoft YaHei"
  });

  slide18.addText(feature.desc, {
    x: 0.7 + index * 4.5, y: 2.3, w: 3.8, h: 0.7,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  if (feature.achievements) {
    feature.achievements.forEach((ach, achIndex) => {
      slide18.addText(`• ${ach}`, {
        x: 0.7 + index * 4.5, y: 3.05 + achIndex * 0.28, w: 3.8, h: 0.25,
        fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
      });
    });
  }

  if (feature.rankings) {
    feature.rankings.forEach((ranking, rankingIndex) => {
      slide18.addText(`• ${ranking}`, {
        x: 0.7 + index * 4.5, y: 3.05 + rankingIndex * 0.28, w: 3.8, h: 0.25,
        fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
      });
    });
  }

  slide18.addText(feature.stats, {
    x: 0.7 + index * 4.5, y: 4.3, w: 3.8, h: 0.4,
    fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 模块6：游戏化激励系统（第2页）- 普惠价值 ====================
const slide19 = pptx.addSlide();
slide19.background = { color: colors.white };

slide19.addText("核心模块六：游戏化激励系统（续）", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.pink,
  align: "center", fontFace: "Microsoft YaHei"
});

slide19.addText("普惠价值：游戏化激励，提升学习参与度85%", {
  x: 0.5, y: 1.1, w: 9, h: 0.4,
  fontSize: 18, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
});

// 参与度提升
slide19.addText("参与度提升对比", {
  x: 0.5, y: 1.7, w: 3, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const engagement = [
  { metric: "课程完成率", before: "45%", after: "85%", improvement: "+89%" },
  { metric: "学习时长", before: "2.5h/周", after: "4.6h/周", improvement: "+84%" },
  { metric: "项目创作", before: "0.8个/月", after: "1.5个/月", improvement: "+88%" },
  { metric: "社区活跃", before: "15%", after: "50%", improvement: "+233%" }
];

engagement.forEach((eng, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);
  
  slide19.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.5, y: 2.2 + row * 1.3, w: 4.2, h: 1.1,
    fill: { color: colors.light },
    line: { color: colors.pink, width: 1 }
  });

  slide19.addText(eng.metric, {
    x: 0.7 + col * 4.5, y: 2.35 + row * 1.3, w: 1.5, h: 0.35,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide19.addText(`${eng.before} → ${eng.after}`, {
    x: 2.3 + col * 4.5, y: 2.35 + row * 1.3, w: 2.2, h: 0.35,
    fontSize: 11, bold: true, color: colors.accent, fontFace: "Arial"
  });

  slide19.addText(`提升${eng.improvement}`, {
    x: 0.7 + col * 4.5, y: 2.75 + row * 1.3, w: 3.8, h: 0.4,
    fontSize: 12, bold: true, color: colors.accent, fontFace: "Arial"
  });
});

// 激励机制
slide19.addText("激励机制", {
  x: 0.5, y: 5.2, w: 1.5, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const mechanisms = [
  { type: "即时反馈", desc: "完成任务立即获得积分和动画庆祝" },
  { type: "成就解锁", desc: "达成目标解锁新徽章和权限" },
  { type: "排行榜竞争", desc: "与同学比拼，激发学习动力" },
  { type: "连击加成", desc: "连续完成获得额外积分奖励" }
];

mechanisms.forEach((mech, index) => {
  slide19.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 5.7, w: 2, h: 0.7,
    fill: { color: colors.light },
    line: { color: colors.accent, width: 1 }
  });

  slide19.addText(mech.type, {
    x: 0.6 + index * 2.25, y: 5.8, w: 1.8, h: 0.3,
    fontSize: 11, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide19.addText(mech.desc, {
    x: 0.6 + index * 2.25, y: 6.1, w: 1.8, h: 0.25,
    fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 商业模式页 ====================
const slide20 = pptx.addSlide();
slide20.background = { color: colors.white };

slide20.addText("商业模式：分层普惠 + 可持续运营", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

// 分层产品体系
const revenueStreams = [
  {
    name: "高端创客盒子",
    type: "俱乐部会员年费",
    price: "3000-5000元/年",
    users: "5000用户",
    features: ["高级AI摄像头", "1v1专家指导", "国际竞赛名额"]
  },
  {
    name: "普惠创客产品",
    type: "学分积分体系",
    price: "0现金支付",
    users: "10万用户",
    features: ["积分兑换硬件", "硬件租赁", "专属学习报告"]
  },
  {
    name: "学校/政府采购",
    type: "区域批量采购",
    price: "50-200元/学生",
    users: "50万学生",
    features: ["教师管理后台", "班级进度追踪", "区域学业分析"]
  }
];

revenueStreams.forEach((stream, index) => {
  slide20.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 1.2 + index * 1.7, w: 8.8, h: 1.5,
    fill: { color: index % 2 === 0 ? colors.light : colors.white },
    line: { color: colors.secondary, width: 1 }
  });

  slide20.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 1.2 + index * 1.7, w: 2.2, h: 1.5,
    fill: { color: colors.primary }
  });

  slide20.addText(stream.name, {
    x: 0.6, y: 1.35 + index * 1.7, w: 2, h: 0.5,
    fontSize: 14, bold: true, color: colors.white, fontFace: "Microsoft YaHei"
  });

  slide20.addText(stream.type, {
    x: 0.6, y: 1.9 + index * 1.7, w: 2, h: 0.4,
    fontSize: 11, color: colors.light, fontFace: "Microsoft YaHei"
  });

  slide20.addText(stream.price, {
    x: 2.8, y: 1.35 + index * 1.7, w: 2, h: 0.4,
    fontSize: 18, bold: true, color: colors.accent, fontFace: "Arial"
  });

  slide20.addText(stream.users, {
    x: 5, y: 1.35 + index * 1.7, w: 2, h: 0.4,
    fontSize: 12, color: colors.dark, fontFace: "Arial"
  });

  stream.features.forEach((feature, featureIndex) => {
    slide20.addText(`• ${feature}`, {
      x: 7.2, y: 1.35 + index * 1.7 + featureIndex * 0.35, w: 2, h: 0.3,
      fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// ==================== 收入预测与ROI分析页 ====================
const slide21 = pptx.addSlide();
slide21.background = { color: colors.white };

slide21.addText("收入预测与ROI分析", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

// 收入预测
slide21.addText("收入预测（三年）", {
  x: 0.5, y: 1.1, w: 4, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const revenuePrediction = [
  { year: "第一年", users: "10.5万用户", revenue: "150万元", break_even: "否" },
  { year: "第二年", users: "30万用户", revenue: "500万元", break_even: "是" },
  { year: "第三年", users: "80万用户", revenue: "1500万元", break_even: "快速增长" }
];

revenuePrediction.forEach((rev, index) => {
  const bgColors = [colors.light, colors.accent, colors.primary];
  
  slide21.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.6, w: 2.8, h: 1.7,
    fill: { color: bgColors[index] },
    line: { color: colors.secondary, width: 1 }
  });

  slide21.addText(rev.year, {
    x: 0.5 + index * 3, y: 1.75, w: 2.8, h: 0.4,
    fontSize: 14, bold: true, color: index === 0 ? colors.dark : colors.white, fontFace: "Microsoft YaHei"
  });

  slide21.addText(rev.users, {
    x: 0.5 + index * 3, y: 2.2, w: 2.8, h: 0.35,
    fontSize: 11, color: index === 0 ? colors.dark : colors.white, fontFace: "Microsoft YaHei"
  });

  slide21.addText(rev.revenue, {
    x: 0.5 + index * 3, y: 2.6, w: 2.8, h: 0.45,
    fontSize: 22, bold: true, color: index === 0 ? colors.accent : colors.white, fontFace: "Arial"
  });

  slide21.addText(rev.break_even, {
    x: 0.5 + index * 3, y: 3.1, w: 2.8, h: 0.3,
    fontSize: 10, color: index === 0 ? colors.dark : colors.light, fontFace: "Microsoft YaHei"
  });
});

// 投资与ROI
slide21.addText("投资与ROI", {
  x: 0.5, y: 3.7, w: 2, h: 0.4,
  fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const roiAnalysis = [
  { metric: "首年投资", value: "300万元", desc: "含研发、市场、硬件" },
  { metric: "第一年ROI", value: "-50%", desc: "市场推广期" },
  { metric: "第二年ROI", value: "67%", desc: "盈亏平衡点" },
  { metric: "第三年ROI", value: "400%", desc: "快速增长期" }
];

roiAnalysis.forEach((roi, index) => {
  slide21.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 4.2, w: 2, h: 1.2,
    fill: { color: colors.light },
    line: { color: index === 1 ? colors.orange : (index === 3 ? colors.accent : colors.secondary), width: 2 }
  });

  slide21.addText(roi.value, {
    x: 0.5 + index * 2.25, y: 4.35, w: 2, h: 0.6,
    fontSize: 28, bold: true, color: index === 1 ? colors.orange : (index === 3 ? colors.accent : colors.secondary), fontFace: "Arial"
  });

  slide21.addText(roi.metric, {
    x: 0.5 + index * 2.25, y: 5.05, w: 2, h: 0.3,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide21.addText(roi.desc, {
    x: 0.5 + index * 2.25, y: 5.35, w: 2, h: 0.25,
    fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 实施路线图页 ====================
const slide22 = pptx.addSlide();
slide22.background = { color: colors.white };

slide22.addText("实施路线图", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const milestones = [
  {
    phase: "Phase 1",
    title: "MVP验证（3个月）",
    tasks: ["硬件原型开发", "基础APP开发", "2个县域学校试点", "数据收集与分析"],
    kpis: ["50名学生", "收集基础数据", "验证核心功能"],
    color: colors.secondary
  },
  {
    phase: "Phase 2",
    title: "市场拓展（6个月）",
    tasks: ["AR纠错功能", "社区模块", "100个班级扩展", "运营商合作"],
    kpis: ["100个班级", "流量补贴合作", "用户留存>60%"],
    color: colors.accent
  },
  {
    phase: "Phase 3",
    title: "生态构建（12个月）",
    tasks: ["AI自适应课程", "高校志愿者平台", "教育信息化补贴", "全国复制"],
    kpis: ["10万+用户", "盈亏平衡", "进入3个省份"],
    color: colors.primary
  }
];

milestones.forEach((milestone, index) => {
  slide22.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.2, w: 2.8, h: 5.3,
    fill: { color: colors.light },
    line: { color: milestone.color, width: 3 }
  });

  slide22.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.2, w: 2.8, h: 0.6,
    fill: { color: milestone.color }
  });

  slide22.addText(milestone.phase, {
    x: 0.5 + index * 3, y: 1.35, w: 2.8, h: 0.4,
    fontSize: 14, bold: true, color: colors.white,
    align: "center", fontFace: "Arial"
  });

  slide22.addText(milestone.title, {
    x: 0.5 + index * 3, y: 2.0, w: 2.6, h: 0.5,
    fontSize: 14, bold: true, color: colors.primary,
    align: "center", fontFace: "Microsoft YaHei"
  });

  milestone.tasks.forEach((task, taskIndex) => {
    slide22.addShape(pptx.ShapeType.ellipse, {
      x: 0.8 + index * 3, y: 2.7 + taskIndex * 0.45, w: 0.16, h: 0.14,
      fill: { color: milestone.color }
    });

    slide22.addText(task, {
      x: 1.1 + index * 3, y: 2.62 + taskIndex * 0.45, w: 2.1, h: 0.35,
      fontSize: 10, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });

  slide22.addText("关键指标", {
    x: 0.7 + index * 3, y: 5.0, w: 2.4, h: 0.35,
    fontSize: 10, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  milestone.kpis.forEach((kpi, kpiIndex) => {
    slide22.addText(`• ${kpi}`, {
      x: 0.7 + index * 3, y: 5.35 + kpiIndex * 0.25, w: 2.4, h: 0.22,
      fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// ==================== 风险控制页 ====================
const slide23 = pptx.addSlide();
slide23.background = { color: colors.white };

slide23.addText("风险控制与应对策略", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const risks = [
  {
    type: "技术风险",
    risks: ["AR识别精度不足", "手机性能差异", "模型轻量化"],
    solutions: ["二维码标签辅助定位", "分级策略（低端机关闭AR）", "模型蒸馏技术"]
  },
  {
    type: "运营风险",
    risks: ["县域学校接受度低", "硬件损耗率高", "志愿者流失"],
    solutions: ["与地方科协合作", "模块化替换件（1元/个）", "学分激励+公益认证"]
  },
  {
    type: "市场风险",
    risks: ["竞品快速跟进", "政策变动", "用户留存挑战"],
    solutions: ["专利保护+技术壁垒", "多区域布局", "社区运营+数据驱动迭代"]
  },
  {
    type: "资金风险",
    risks: ["前期投入大", "现金流压力", "盈亏周期长"],
    solutions: ["B端合作分摊成本", "政府补贴+公益基金", "分层产品快速回血"]
  }
];

risks.forEach((risk, index) => {
  slide23.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 1.2, w: 2, h: 2.8,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 2 }
  });

  slide23.addText(risk.type, {
    x: 0.6, y: 1.35 + index * 2.25, w: 1.8, h: 0.4,
    fontSize: 13, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  risk.risks.forEach((r, rIndex) => {
    slide23.addShape(pptx.ShapeType.ellipse, {
      x: 0.7 + index * 2.25, y: 1.85 + rIndex * 0.4, w: 0.12, h: 0.12,
      fill: { color: colors.orange }
    });

    slide23.addText(r, {
      x: 0.9 + index * 2.25, y: 1.8 + rIndex * 0.4, w: 1.5, h: 0.3,
      fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });

  risk.solutions.forEach((s, sIndex) => {
    slide23.addShape(pptx.ShapeType.ellipse, {
      x: 0.7 + index * 2.25, y: 2.95 + sIndex * 0.4, w: 0.12, h: 0.12,
      fill: { color: colors.accent }
    });

    slide23.addText(s, {
      x: 0.9 + index * 2.25, y: 2.9 + sIndex * 0.4, w: 1.5, h: 0.3,
      fontSize: 9, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// ==================== 社会价值页 ====================
const slide24 = pptx.addSlide();
slide24.background = { color: colors.primary };

slide24.addText("社会价值：教育公平 + 就业拉动", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.white,
  align: "center", fontFace: "Microsoft YaHei"
});

const socialValues = [
  { title: "教育公平", desc: "县域学生成本降至30元/年，相比传统降低99%", impact: "1.44亿学生受益" },
  { title: "就业拉动", desc: "培养基层AI+硬件技能，对接新职业", impact: "创造就业岗位100万+" },
  { title: "技术普及", desc: "AI、AR、区块链技术下沉到县域", impact: "推动数字化转型" },
  { title: "产业振兴", desc: "结合地方产业开发课程", impact: "赋能乡村振兴" }
];

socialValues.forEach((value, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);
  
  slide24.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.5, y: 1.2 + row * 2.2, w: 4.2, h: 2,
    fill: { color: "rgba(255,255,255,0.1)" },
    line: { color: colors.white, width: 2 }
  });

  slide24.addText(value.title, {
    x: 0.7 + col * 4.5, y: 1.35 + row * 2.2, w: 3.8, h: 0.45,
    fontSize: 16, bold: true, color: colors.white, fontFace: "Microsoft YaHei"
  });

  slide24.addText(value.desc, {
    x: 0.7 + col * 4.5, y: 1.85 + row * 2.2, w: 3.8, h: 0.7,
    fontSize: 11, color: colors.light, fontFace: "Microsoft YaHei"
  });

  slide24.addText(value.impact, {
    x: 0.7 + col * 4.5, y: 2.6 + row * 2.2, w: 3.8, h: 0.4,
    fontSize: 11, bold: true, color: colors.accent, fontFace: "Microsoft YaHei"
  });
});

// ==================== 结束页 ====================
const slide25 = pptx.addSlide();
slide25.background = { color: colors.primary };

slide25.addText("携手共创AI教育新未来", {
  x: 0.5, y: 2.5, w: 9, h: 0.8,
  fontSize: 48, bold: true, color: colors.white,
  align: "center", fontFace: "Microsoft YaHei"
});

slide25.addText("让每个孩子都能享受优质的AI教育", {
  x: 0.5, y: 3.6, w: 9, h: 0.6,
  fontSize: 24, color: colors.light,
  align: "center", fontFace: "Microsoft YaHei"
});

slide25.addText("iMatuProject团队", {
  x: 3.5, y: 5.2, w: 3, h: 0.5,
  align: "center", fontFace: "Microsoft YaHei",
  fontSize: 18, bold: true, color: colors.white
});

slide25.addText(new Date().toLocaleDateString("zh-CN"), {
  x: 4.2, y: 6.2, w: 1.6, h: 0.3,
  align: "center", fontFace: "Microsoft YaHei",
  fontSize: 12, color: colors.light
});

// 保存PPT
const outputPath = path.join(__dirname, "MatuX_创业大赛商业计划书_完整版.pptx");
pptx.writeFile({ fileName: outputPath })
  .then(fileName => {
    console.log("PPT生成成功:", fileName);
  })
  .catch(err => {
    console.error("PPT生成失败:", err);
  });
