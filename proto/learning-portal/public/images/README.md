# MatuX 原型站图片资源清单

## 已复制的资源
- ✅ `/images/logo.png` - MatuX Logo (PNG格式)
- ✅ `/images/logo.jpg` - MatuX Logo (JPG格式)
- ✅ `/images/robot-mascot.png` - 机器人吉祥物

## 需要准备的图片资源

### 1. 团队头像 (3张)
**位置**: `/public/images/team/`

| 文件名 | 尺寸建议 | 说明 |
|--------|---------|------|
| `ceo.jpg` | 400x400px | 陈伟博士（创始人 & CEO）头像 |
| `cto.jpg` | 400x400px | 林晓梅（CTO）头像 |
| `hardware-director.jpg` | 400x400px | 张伟（硬件研发总监）头像 |

**要求**: 
- 正方形或接近正方形比例
- 专业商务照风格
- JPG或PNG格式，文件大小 < 200KB

---

### 2. 首页图片 (2张)
**位置**: `/public/images/`

| 文件名 | 尺寸建议 | 说明 |
|--------|---------|------|
| `hero-bg.jpg` | 1920x1080px | 首页Hero区域背景图（AI/STEM教育主题） |
| `tech-stack.jpg` | 800x600px | 技术架构展示图（代码、硬件、区块链等元素） |

**要求**:
- Hero背景图需要科技感强，适合做半透明遮罩
- 技术栈图片可以包含代码编辑器、ESP32开发板、区块链图标等元素

---

### 3. 功能页图片 (1张)
**位置**: `/public/images/`

| 文件名 | 尺寸建议 | 说明 |
|--------|---------|------|
| `stem-collaboration.jpg` | 800x600px | STEM协作场景图（学生在实验室协作） |

**要求**:
- 展示学生团队协作进行STEM实验的场景
- 明亮、积极向上的氛围

---

### 4. 产品展示图（可选，建议准备）
**位置**: `/public/images/products/`

| 文件名 | 尺寸建议 | 说明 |
|--------|---------|------|
| `esp32-board.jpg` | 600x400px | ESP32开发板实物图 |
| `metaverse-lab.jpg` | 800x600px | 元宇宙虚拟实验室截图 |
| `ai-code-gen.jpg` | 800x600px | AI代码生成界面截图 |
| `mobile-app.jpg` | 400x800px | 移动端应用界面截图 |
| `blockchain-cert.jpg` | 600x400px | 区块链证书示例 |

---

## 图片优化建议

1. **格式选择**:
   - 照片类使用 JPG（质量80-85%）
   - 图标/Logo使用 PNG
   - 简单图形考虑使用 SVG

2. **尺寸优化**:
   - 所有图片宽度不超过 2000px
   - 单张图片文件大小控制在 500KB 以内
   - 使用工具压缩：TinyPNG、Squoosh.app

3. **命名规范**:
   - 使用小写字母和连字符
   - 避免中文和特殊字符
   - 示例：`hero-bg.jpg`, `team-photo-01.jpg`

---

## 快速占位方案

如果暂时没有真实图片，可以使用以下方法生成占位图：

1. **在线工具**:
   - https://placeholder.com/ - 生成纯色占位图
   - https://picsum.photos/ - 随机高质量图片

2. **本地生成** (PowerShell):
```powershell
# 创建纯色占位图脚本（需要安装 ImageMagick）
magick convert -size 400x400 xc:#3b82f6 -fill white -pointsize 40 -gravity center -annotate 0 "Team Photo" team-placeholder.jpg
```

3. **设计工具**:
   - Figma / Canva 制作简单的品牌占位图
   - 使用 MatuX 品牌色：主色 #0f172a，强调色 #3b82f6

---

## 下一步操作

1. 准备上述图片资源
2. 将图片放入对应的 `/public/images/` 子目录
3. 重新构建项目：`npm run build`
4. 检查图片加载是否正常

**注意**: 当前代码已更新为本地路径引用，添加图片后即可正常显示。
