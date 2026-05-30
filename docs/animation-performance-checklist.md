# 动效性能优化检查清单

## 🎯 优化目标验证

### 1. 总时长控制（≤1s）✅
- [ ] Hero 区渐显总时长：**0.6s** (原 1.6s) ⬇️ 62.5%
- [ ] 单个动画最长：**0.5s**
- [ ] 滚动渐入：**0.4s**
- [ ] 按钮响应：**0.15s**

### 2. 移除过度动效 ✅
- [x] ~~CTA 区脉冲背景动画~~ **已移除**
- [x] ~~过长的渐显延迟~~ **从 0.8s 降至 0.5s**
- [x] ~~过度的位移/旋转~~ **位移从 20px→15px，旋转从 5°→3°**

### 3. 核心区块保留 ✅
- [ ] Hero 区逐行渐显 **保留**（首屏视觉引导）
- [ ] 卡片 hover 反馈 **保留并优化**（交互确认）
- [ ] 按钮 hover/active **保留并优化**（操作反馈）
- [ ] 滚动渐入 **保留并优化**（内容揭示）

---

## 📊 性能指标检查

### 桌面端标准
- [ ] FPS ≥ 60fps（Chrome/Firefox/Safari）
- [ ] LCP < 2.5s
- [ ] CLS < 0.1
- [ ] 动画总时长 ≤ 1s

### 移动端标准（低性能设备）
- [ ] FPS ≥ 30fps（Redmi Note、Galaxy A 系列）
- [ ] FCP < 1.8s
- [ ] 无明显卡顿或延迟

---

## 🔍 手动测试步骤

### 1. Hero 区渐显测试
```
1. 打开首页 http://localhost:4200
2. 观察首屏标题、副标题、按钮的渐显顺序
3. 使用手机计时器测量总时长
4. 预期结果：总时长 ≤ 0.6s，流畅无卡顿
```

### 2. 卡片 Hover 测试
```
1. 将鼠标悬停在任意卡片上
2. 观察卡片上移、阴影加深、图标旋转
3. 预期结果：
   - 位移距离：2px（轻微）
   - 过渡时间：0.2s
   - 图标旋转：3°（ subtle）
   - FPS ≥ 60
```

### 3. 按钮响应测试
```
1. 悬停和点击主按钮
2. 观察缩放和阴影变化
3. 预期结果：
   - Hover 响应：0.15s
   - Active 缩放：scale(0.98)
   - 即时反馈，无延迟感
```

### 4. 滚动渐入测试
```
1. 向下滚动页面
2. 观察内容区块依次渐入
3. 预期结果：
   - 动画时长：0.4s
   - 位移距离：15px
   - 流畅衔接，无闪烁
```

### 5. 移动端禁用测试
```
1. 打开 Chrome DevTools > Device Toolbar
2. 选择移动设备（如 iPhone SE）
3. 刷新页面
4. 预期结果：
   - 背景粒子动画已禁用
   - CTA 脉冲动画已移除
   - 仅保留必要交互反馈
```

---

## 🛠️ 自动化测试工具

### 1. Chrome DevTools Performance
```javascript
// 打开 DevTools > Performance
// 录制页面加载和交互
// 查看关键指标：
// - FPS 曲线（不应低于 30）
// - Layout/Paint 耗时
// - Composite Layers
```

### 2. Lighthouse 测试
```bash
# 运行 Lighthouse
npx lighthouse http://localhost:4200 --view

# 关键指标：
# - Performance: 90+
# - Accessibility: 90+
# - Best Practices: 90+
```

### 3. Puppeteer 自动化脚本
```bash
# 安装依赖
npm install --save-dev puppeteer

# 运行测试
node tests/performance/test-animation-performance.js

# 查看报告
dist/performance-reports/animation-performance-*.json
```

### 4. WebPageTest 在线测试
```
访问：https://www.webpagetest.org
输入 URL: http://localhost:4200（需内网穿透）
选择测试地点和浏览器
查看 Waterfall 和 Video 回放
```

---

## 📱 真机测试设备清单

### 低端 Android 设备
- [ ] Redmi Note 系列
- [ ] Samsung Galaxy A 系列
- [ ] Huawei Y 系列

### 老旧 iOS 设备
- [ ] iPhone 6s / 7 / 8
- [ ] iPhone SE (第一代)

### 低端笔记本
- [ ] Intel Celeron / Pentium 处理器
- [ ] 4GB RAM 或更低
- [ ] 集成显卡

---

## ♿ 可访问性检查

### prefers-reduced-motion
```scss
// 测试代码
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition: none !important;
  }
}
```

**测试步骤:**
1. macOS: 系统偏好设置 > 辅助功能 > 显示 > 减弱动态效果
2. Windows: 设置 > 轻松使用 > 显示 > 关闭动画
3. 刷新页面，所有动画应被禁用

---

## 🔥 常见问题排查

### Q1: 动画在低端设备上卡顿
**解决方案:**
```scss
// 1. 减少位移距离
transform: translateY(-2px); // 而非 -10px

// 2. 缩短动画时长
transition: all 0.15s ease; // 而非 0.5s

// 3. 禁用装饰性动画
@media (max-width: 768px) {
  .hero-section::before {
    animation: none !important;
  }
}
```

### Q2: Hover 效果不流畅
**解决方案:**
```scss
// 1. 使用 transform 代替 margin/padding
transform: translateY(-2px); // ✓
margin-top: -2px;            // ✗

// 2. 添加 will-change（谨慎使用）
.feature-card:hover {
  will-change: transform;
}

// 3. 确保 GPU 加速
.feature-card {
  backface-visibility: hidden;
  perspective: 1000px;
}
```

### Q3: 滚动渐入触发不及时
**解决方案:**
```javascript
// 调整 Intersection Observer 阈值
const observer = new IntersectionObserver(
  (entries) => { /* ... */ },
  { 
    threshold: 0.1,        // 10% 可见即触发
    rootMargin: '0px 0px -50px 0px' // 提前 50px 触发
  }
);
```

---

## 📈 性能监控指标

### 关键指标定义
| 指标 | 含义 | 目标值 |
|------|------|--------|
| FPS | 每秒帧数 | ≥30（移动），≥60（桌面） |
| FCP | 首次内容绘制 | <1.8s |
| LCP | 最大内容绘制 | <2.5s |
| CLS | 累计布局偏移 | <0.1 |
| TBT | 阻塞总时间 | <200ms |

### 监控工具
- Chrome User Experience Report (CrUX)
- Google Analytics + Custom Events
- Sentry Performance Monitoring
- Custom Performance API

---

## ✅ 最终验收标准

### 必须满足（P0）
- [ ] 所有动画总时长 ≤ 1s
- [ ] 低端设备 FPS ≥ 30
- [ ] 无无限循环装饰动画
- [ ] 支持 prefers-reduced-motion

### 建议满足（P1）
- [ ] 桌面端 FPS ≥ 60
- [ ] LCP < 2.5s
- [ ] Lighthouse Performance ≥ 90
- [ ] 滚动渐入流畅无闪烁

### 可选优化（P2）
- [ ] Web Animations API 精确控制
- [ ] 动态导入动画库
- [ ] 自定义性能监控面板

---

## 📝 测试报告模板

```markdown
## 测试报告

**测试日期**: YYYY-MM-DD  
**测试人员**: [姓名]  
**测试环境**: 
- 设备：[MacBook Pro 2023 / iPhone 12 / Redmi Note 10]
- 浏览器：[Chrome 120 / Safari 17 / Firefox 121]
- 网络：[WiFi / 4G / 5G]

### 测试结果

#### Hero 区渐显
- [ ] 通过 / [ ] 失败
- 实测时长：___ ms
- 备注：_________

#### 卡片 Hover
- [ ] 通过 / [ ] 失败
- 平均 FPS: ___
- 备注：_________

#### 按钮响应
- [ ] 通过 / [ ] 失败
- 响应时间：___ ms
- 备注：_________

#### 滚动渐入
- [ ] 通过 / [ ] 失败
- 动画时长：___ ms
- 备注：_________

### 问题记录
1. [问题描述]
2. [复现步骤]
3. [截图/录屏]

### 改进建议
- [建议 1]
- [建议 2]
```

---

## 🔄 持续优化计划

### 短期（1 个月内）
- [ ] 每周运行一次自动化测试
- [ ] 收集用户反馈
- [ ] 优化移动端表现

### 中期（3 个月内）
- [ ] 引入 Web Animations API
- [ ] 建立性能基线
- [ ] 监控真实用户数据

### 长期（6 个月内）
- [ ] 动画性能回归测试
- [ ] 适配更多设备
- [ ] 探索新技术（如 FLIP 动画）

---

**最后更新**: 2026-03-13  
**维护团队**: iMato Frontend Team
