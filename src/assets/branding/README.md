# 添加机器人吉祥物图片到首页

## 任务说明
将可爱的 3D 机器人图片添加到首页首焦图的右侧位置。

## 已完成的工作
1. ✅ 修改了 `marketing-home.component.ts` - 添加了左右布局结构和图片标签
2. ✅ 修改了 `marketing-home.component.scss` - 添加了响应式样式
3. ✅ 创建了 `src/assets/branding/` 目录

## 需要您手动完成的步骤

### 步骤 1: 准备图片文件
将您提供的机器人图片保存到项目目录：
```
g:\iMato\src\assets\branding\robot-mascot.png
```

**图片要求：**
- 格式：PNG（支持透明背景）
- 建议尺寸：宽度 500-800px
- 背景：透明背景最佳（如果原图是白色背景，可以使用在线工具去除）

### 步骤 2: 使用在线工具去除背景（可选）
如果图片需要去除白色背景：
1. 访问 https://www.remove.bg/zh
2. 上传您的机器人图片
3. 下载去背后的 PNG 图片
4. 保存为 `robot-mascot.png`

### 步骤 3: 查看效果
刷新浏览器访问首页，应该能看到：
- 左侧：标题、副标题、按钮
- 右侧：可爱的 3D 机器人图片

## 技术细节

### 布局结构
```html
<div class="hero-content-wrapper">
  <div class="hero-content">
    <!-- 左侧内容 -->
  </div>
  <div class="hero-image">
    <img src="assets/branding/robot-mascot.png" />
    <!-- 右侧机器人图片 -->
  </div>
</div>
```

### 响应式设计
- **桌面端（>768px）**：左右布局，图片在右侧
- **移动端（≤768px）**：上下布局，图片在下方

### 样式特性
- 图片最大高度 500px（桌面端）/ 300px（移动端）
- 添加阴影效果增强立体感
- Hover 时有轻微放大和旋转动画

## 注意事项
1. 如果图片不显示，请检查：
   - 图片路径是否正确
   - 浏览器控制台是否有 404 错误
   - 图片文件是否已保存

2. 如果图片太大或太小：
   - 修改 SCSS 中的 `max-height` 值
   - 或调整图片本身的分辨率

3. 如果想要调整左右比例：
   - 修改 `.hero-content-wrapper` 的 `gap` 值
   - 或调整 `.hero-content` 和 `.hero-image` 的 `flex` 值
