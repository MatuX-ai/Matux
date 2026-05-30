const PptxGenJS = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// 创建PPT实例
const pptx = new PptxGenJS();

// 设置PPT元数据
pptx.title = "MatuX AI教育平台 - 创业大赛商业计划书";
pptx.author = "MatuX团队";

// 颜色方案 - 科技蓝主题
const colors = {
  primary: "1E3A8A",      // 深蓝色
  secondary: "3B82F6",    // 亮蓝色
  accent: "10B981",       // 绿色
  dark: "1F2937",         // 深灰
  light: "F3F4F6",        // 浅灰
  white: "FFFFFF",
  orange: "F59E0B"        // 橙色
};

// ==================== 封面页 ====================
const slide1 = pptx.addSlide();
slide1.background = { color: colors.primary };

slide1.addText("MatuX AI教育平台", {
  x: 0.5, y: 1.5, w: 9, h: 1,
  fontSize: 48, bold: true, color: colors.white,
  align: "center", fontFace: "Microsoft YaHei"
});

slide1.addText("智能化多模态教育生态系统", {
  x: 0.5, y: 2.8, w: 9, h: 0.7,
  fontSize: 28, bold: true, color: colors.secondary,
  align: "center", fontFace: "Microsoft YaHei"
});

slide1.addText("—— 创业大赛商业计划书 ——", {
  x: 0.5, y: 3.8, w: 9, h: 0.6,
  fontSize: 20, color: colors.light,
  align: "center", fontFace: "Microsoft YaHei"
});

const featureText = "✓ AI智能推荐  ✓ AR/VR沉浸式学习  ✓ 区块链积分认证  ✓ 边缘AI硬件  ✓ 软硬结合实训";
slide1.addText(featureText, {
  x: 1.5, y: 4.8, w: 7, h: 1.5,
  align: "center", valign: "middle", fontFace: "Microsoft YaHei",
  fontSize: 16, color: colors.light
});

slide1.addText(new Date().toLocaleDateString("zh-CN"), {
  x: 4.5, y: 6.8, w: 1.5, h: 0.4,
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
  "项目概况与愿景",
  "市场前景分析",
  "核心竞争力",
  "商业模式与ROI",
  "实施规划与路线图",
  "团队与资源"
];

tocItems.forEach((item, index) => {
  slide2.addText(`${index + 1}.  ${item}`, {
    x: 1.5, y: 1.3 + index * 0.8, w: 7, h: 0.6,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true,
    color: colors.primary
  });
});

// ==================== 项目概况页 ====================
const slide3 = pptx.addSlide();
slide3.background = { color: colors.white };

slide3.addText("项目概况", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const features = [
  { title: "AI智能教育", desc: "基于LangChain的对话式学习助手，0.8秒响应，准确率90%" },
  { title: "AR/VR沉浸式学习", desc: "256个3D电子元件模型，虚拟实验室，MediaPipe手势识别" },
  { title: "区块链积分认证", desc: "Hyperledger Fabric企业级网络，积分不可篡改" },
  { title: "边缘AI硬件", desc: "ESP32 TinyML语音识别，95%准确率，离线运行" },
  { title: "软硬结合实训", desc: "OpenHydra+XEdu深度融合，跨平台任务编排" },
  { title: "游戏化激励", desc: "成就系统、排行榜、积分衰减机制" }
];

features.forEach((feature, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);
  slide3.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.5, y: 1.2 + row * 1.8, w: 4.2, h: 1.6,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 2 }
  });

  slide3.addText(feature.title, {
    x: 0.7 + col * 4.5, y: 1.3 + row * 1.8, w: 3.8, h: 0.4,
    fontSize: 16, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide3.addText(feature.desc, {
    x: 0.7 + col * 4.5, y: 1.75 + row * 1.8, w: 3.8, h: 0.9,
    fontSize: 12, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 市场规模页 ====================
const slide4 = pptx.addSlide();
slide4.background = { color: colors.white };

slide4.addText("市场前景分析", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

// 市场数据卡片
const marketData = [
  { title: "AI教育市场", value: "476亿", sub: "2027年预计，年复合增长20%+" },
  { title: "STEM教育", value: "200亿美元", sub: "中国2024年预测，年复合增长15%+" },
  { title: "元宇宙教育", value: "93.8亿", sub: "中国2023年，年复合增长17%" },
  { title: "在线教育", value: "8910亿", sub: "中国2028年预测，年复合增长37%" }
];

marketData.forEach((data, index) => {
  slide4.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 2.25, y: 1.2, w: 2, h: 2.2,
    fill: { color: index % 2 === 0 ? colors.secondary : colors.primary },
    line: { color: colors.white, width: 0 }
  });

  slide4.addText(data.title, {
    x: 0.5 + index * 2.25, y: 1.3, w: 2, h: 0.4,
    fontSize: 12, bold: true, color: colors.white,
    align: "center", fontFace: "Microsoft YaHei"
  });

  slide4.addText(data.value, {
    x: 0.5 + index * 2.25, y: 1.8, w: 2, h: 0.5,
    fontSize: 24, bold: true, color: colors.white,
    align: "center", fontFace: "Arial"
  });

  slide4.addText(data.sub, {
    x: 0.5 + index * 2.25, y: 2.35, w: 2, h: 0.9,
    fontSize: 10, color: colors.white,
    align: "center", valign: "top", fontFace: "Microsoft YaHei"
  });
});

// 市场趋势
slide4.addText("核心市场趋势", {
  x: 0.5, y: 4, w: 2, h: 0.5,
  fontSize: 18, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const trends = [
  "教育数字化转型加速，政策强力支持",
  "AI技术成熟，从辅助到核心驱动",
  "软硬结合成为新趋势",
  "元宇宙教育应用场景不断丰富",
  "个性化、智能化需求日益增长",
  "区块链认证提升学习可信度"
];

trends.forEach((trendText, index) => {
  const row = Math.floor(index / 2);
  const col = index % 2;
  slide4.addShape(pptx.ShapeType.ellipse, {
    x: 0.5 + col * 4 + 0.08, y: 4.6 + row * 0.5, w: 0.24, h: 0.2,
    fill: { color: colors.accent }
  });

  slide4.addText(trendText, {
    x: 0.9 + col * 4, y: 4.5 + row * 0.5, w: 4, h: 0.4,
    fontSize: 13, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 竞争优势页 ====================
const slide5 = pptx.addSlide();
slide5.background = { color: colors.white };

slide5.addText("核心竞争力", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const advantages = [
  {
    title: "技术壁垒",
    items: [
      "ESP32 TinyML边缘AI：95%准确率，640ms响应",
      "256个3D电子元件模型库，LOD优化技术",
      "Hyperledger Fabric企业级区块链",
      "AI学习助手0.8秒响应，准确率90%"
    ]
  },
  {
    title: "生态整合",
    items: [
      "OpenHydra K8s实训环境深度集成",
      "XEdu中小学AI工具链无缝对接",
      "Vircadia元宇宙教育场景",
      "软硬结合完整学习闭环"
    ]
  },
  {
    title: "产品矩阵",
    items: [
      "开源版：社区驱动，技术验证",
      "Windows本地版：离线运行，企业部署",
      "云托管版：SaaS模式，多租户支持",
      "ToB定制：学校授权，课程开发"
    ]
  },
  {
    title: "用户体验",
    items: [
      "游戏化激励系统，提升85%参与度",
      "多模态交互（语音/AR/手势）",
      "智能推荐算法，i+1难度匹配",
      "实时进度同步，多设备无缝切换"
    ]
  }
];

advantages.forEach((adv, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);

  slide5.addShape(pptx.ShapeType.rect, {
    x: 0.5 + col * 4.5, y: 1.2 + row * 2.4, w: 4.2, h: 2.2,
    fill: { color: colors.light },
    line: { color: colors.secondary, width: 3 }
  });

  slide5.addText(adv.title, {
    x: 0.7 + col * 4.5, y: 1.3 + row * 2.4, w: 3.8, h: 0.5,
    fontSize: 18, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  adv.items.forEach((item, itemIndex) => {
    slide5.addText(`• ${item}`, {
      x: 0.7 + col * 4.5, y: 1.85 + row * 2.4 + itemIndex * 0.45, w: 3.8, h: 0.4,
      fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// ==================== 商业模式页 ====================
const slide6 = pptx.addSlide();
slide6.background = { color: colors.white };

slide6.addText("商业模式", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const revenueStreams = [
  { name: "开源版", type: "免费", desc: "社区驱动，技术验证，吸引开发者" },
  { name: "Windows本地版", type: "$999/年", desc: "离线运行，企业部署，含AI功能" },
  { name: "云托管版", type: "$299/年", desc: "SaaS模式，云端同步，多租户" },
  { name: "ToB定制", type: "$500+起", desc: "学校授权，课程定制，按需收费" },
  { name: "Token增值", type: "按量计费", desc: "AI功能调用，课程生成，智能推荐" }
];

revenueStreams.forEach((stream, index) => {
  slide6.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 1.2 + index * 1.2, w: 8.8, h: 1,
    fill: { color: index % 2 === 0 ? colors.light : colors.white },
    line: { color: colors.secondary, width: 1 }
  });

  slide6.addShape(pptx.ShapeType.rect, {
    x: 0.5, y: 1.2 + index * 1.2, w: 1.5, h: 1,
    fill: { color: colors.primary },
    line: { color: colors.secondary, width: 1 }
  });

  slide6.addText(stream.name, {
    x: 0.6, y: 1.4 + index * 1.2, w: 1.3, h: 0.6,
    fontSize: 16, bold: true, color: colors.white,
    align: "center", fontFace: "Microsoft YaHei"
  });

  slide6.addText(stream.type, {
    x: 2.2, y: 1.4 + index * 1.2, w: 1.5, h: 0.4,
    fontSize: 18, bold: true, color: colors.accent, fontFace: "Arial"
  });

  slide6.addText(stream.desc, {
    x: 4, y: 1.35 + index * 1.2, w: 5.2, h: 0.7,
    fontSize: 13, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== ROI分析页 ====================
const slide7 = pptx.addSlide();
slide7.background = { color: colors.white };

slide7.addText("投资回报分析", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

// 投资估算
slide7.addText("投资估算（首年）", {
  x: 0.5, y: 1, w: 4, h: 0.4,
  fontSize: 18, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const investments = [
  { item: "研发团队（10人）", amount: "120万元" },
  { item: "云服务与基础设施", amount: "30万元" },
  { item: "市场推广与运营", amount: "50万元" },
  { item: "硬件采购（ESP32等）", amount: "20万元" },
  { item: "其他运营成本", amount: "30万元" }
];

investments.forEach((inv, index) => {
  slide7.addText(inv.item, {
    x: 0.5, y: 1.5 + index * 0.5, w: 2.5, h: 0.4,
    fontSize: 13, color: colors.dark, fontFace: "Microsoft YaHei"
  });

  slide7.addText(inv.amount, {
    x: 3.1, y: 1.5 + index * 0.5, w: 1.2, h: 0.4,
    fontSize: 13, bold: true, color: colors.primary, fontFace: "Arial"
  });
});

slide7.addShape(pptx.ShapeType.rect, {
  x: 0.5, y: 4, w: 3.8, h: 0.5,
  fill: { color: colors.accent }
});

slide7.addText("总投资：250万元", {
  x: 0.5, y: 4, w: 3.8, h: 0.5,
  fontSize: 16, bold: true, color: colors.white,
  align: "center", valign: "middle", fontFace: "Microsoft YaHei"
});

// 收入预测
slide7.addText("收入预测（三年）", {
  x: 5, y: 1, w: 4, h: 0.4,
  fontSize: 18, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const revenuePrediction = [
  { year: "第一年", amount: "80万元", user: "5,000用户" },
  { year: "第二年", amount: "300万元", user: "20,000用户" },
  { year: "第三年", amount: "800万元", user: "50,000用户" }
];

revenuePrediction.forEach((rev, index) => {
  slide7.addShape(pptx.ShapeType.rect, {
    x: 5, y: 1.5 + index * 0.7, w: 4.2, h: 0.6,
    fill: { color: index === 0 ? colors.light : index === 1 ? colors.secondary : colors.primary },
    line: { color: colors.white, width: 1 }
  });

  slide7.addText(rev.year, {
    x: 5.1, y: 1.6 + index * 0.7, w: 1, h: 0.4,
    fontSize: 14, bold: true, color: index === 0 ? colors.dark : colors.white, fontFace: "Microsoft YaHei"
  });

  slide7.addText(rev.amount, {
    x: 6.2, y: 1.6 + index * 0.7, w: 1.5, h: 0.4,
    fontSize: 18, bold: true, color: index === 0 ? colors.accent : colors.white, fontFace: "Arial"
  });

  slide7.addText(rev.user, {
    x: 5.1, y: 1.9 + index * 0.7, w: 4, h: 0.3,
    fontSize: 11, color: index === 0 ? colors.dark : colors.light, fontFace: "Microsoft YaHei"
  });
});

// ROI计算
slide7.addText("ROI分析", {
  x: 0.5, y: 5, w: 2, h: 0.4,
  fontSize: 18, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
});

const roiData = [
  { label: "第一年ROI", value: "-68%", desc: "市场推广期" },
  { label: "第二年ROI", value: "20%", desc: "盈亏平衡点" },
  { label: "第三年ROI", value: "220%", desc: "快速增长期" }
];

roiData.forEach((roi, index) => {
  slide7.addText(roi.label, {
    x: 0.5 + index * 3, y: 5.5, w: 2.8, h: 0.4,
    fontSize: 14, bold: true, color: colors.primary, fontFace: "Microsoft YaHei"
  });

  slide7.addText(roi.value, {
    x: 0.5 + index * 3, y: 5.9, w: 2.8, h: 0.5,
    fontSize: 28, bold: true, color: index === 0 ? colors.orange : colors.accent, fontFace: "Arial"
  });

  slide7.addText(roi.desc, {
    x: 0.5 + index * 3, y: 6.4, w: 2.8, h: 0.3,
    fontSize: 11, color: colors.dark, fontFace: "Microsoft YaHei"
  });
});

// ==================== 实施路线图页 ====================
const slide8 = pptx.addSlide();
slide8.background = { color: colors.white };

slide8.addText("实施路线图", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 36, bold: true, color: colors.primary,
  align: "center", fontFace: "Microsoft YaHei"
});

const milestones = [
  {
    phase: "Phase 1",
    title: "基础建设（3个月）",
    items: ["Token计费系统", "Windows安装包", "核心功能完善"],
    color: colors.secondary
  },
  {
    phase: "Phase 2",
    title: "市场拓展（6个月）",
    items: ["云托管部署", "ToB客户开拓", "课程内容扩充"],
    color: colors.accent
  },
  {
    phase: "Phase 3",
    title: "生态构建（12个月）",
    items: ["社区运营", "合作伙伴", "技术迭代"],
    color: colors.primary
  }
];

milestones.forEach((milestone, index) => {
  slide8.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.2, w: 2.8, h: 5,
    fill: { color: colors.light },
    line: { color: milestone.color, width: 3 }
  });

  slide8.addShape(pptx.ShapeType.rect, {
    x: 0.5 + index * 3, y: 1.2, w: 2.8, h: 0.7,
    fill: { color: milestone.color }
  });

  slide8.addText(milestone.phase, {
    x: 0.5 + index * 3, y: 1.35, w: 2.8, h: 0.4,
    fontSize: 14, bold: true, color: colors.white,
    align: "center", fontFace: "Arial"
  });

  slide8.addText(milestone.title, {
    x: 0.5 + index * 3, y: 2.1, w: 2.6, h: 0.5,
    fontSize: 15, bold: true, color: colors.primary,
    align: "center", fontFace: "Microsoft YaHei"
  });

  milestone.items.forEach((item, itemIndex) => {
    slide8.addShape(pptx.ShapeType.ellipse, {
      x: 0.8 + index * 3, y: 2.8 + itemIndex * 0.7, w: 0.16, h: 0.16,
      fill: { color: milestone.color }
    });

    slide8.addText(item, {
      x: 1.1 + index * 3, y: 2.72 + itemIndex * 0.7, w: 2.1, h: 0.4,
      fontSize: 12, color: colors.dark, fontFace: "Microsoft YaHei"
    });
  });
});

// ==================== 结束页 ====================
const slide9 = pptx.addSlide();
slide9.background = { color: colors.primary };

slide9.addText("感谢聆听", {
  x: 0.5, y: 2.5, w: 9, h: 0.8,
  fontSize: 48, bold: true, color: colors.white,
  align: "center", fontFace: "Microsoft YaHei"
});

slide9.addText("携手共创AI教育新未来", {
  x: 0.5, y: 3.6, w: 9, h: 0.6,
  fontSize: 28, color: colors.light,
  align: "center", fontFace: "Microsoft YaHei"
});

slide9.addText("联系方式： MatuX团队", {
  x: 2, y: 4.8, w: 6, h: 0.5,
  align: "center", fontFace: "Microsoft YaHei",
  fontSize: 18, bold: true, color: colors.white
});

// 保存PPT
const outputPath = path.join(__dirname, "MatuX_创业大赛商业计划书.pptx");
pptx.writeFile({ fileName: outputPath })
  .then(fileName => {
    console.log("PPT生成成功:", fileName);
  })
  .catch(err => {
    console.error("PPT生成失败:", err);
  });
