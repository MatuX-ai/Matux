#!/usr/bin/env node
/**
 * 确保 Unity WebGL 构建占位目录存在。
 * 在 CI / fresh clone 后调用，生成 src/assets/ar-lab/build/README.md 占位说明。
 *
 * 使用：
 *   node scripts/ensure-unity-build-placeholder.mjs
 *   npm run ensure:unity-build
 *
 * 退出码：
 *   0 = 占位已就绪（已存在或刚刚创建）
 *   1 = 创建失败
 */
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '..');
const PLACEHOLDER_DIR = join(PROJECT_ROOT, 'src', 'assets', 'ar-lab', 'build');
const PLACEHOLDER_FILE = join(PLACEHOLDER_DIR, 'README.md');

const README_CONTENT = `# AR Lab Unity WebGL Build Output Placeholder

此目录是 \`iMato/src/app/ar-lab/ar-lab.component.ts\` 期望加载 Unity WebGL 构建产物的位置。

\`\`\`
http(s)://<host>/ar-lab/build/ARLabMain.json
\`\`\`

## 为什么这个目录是空的？

仓库根的 \`unity/ImatuARLab/\` 是 Unity Editor 工程源码，但 Unity 构建产物（数十 MB 的 \`Build/\`、\`TemplateData/\`、\`StreamingAssets/\`）不会提交到 Git。

桌面端启动后访问 \`/ar-lab\` 时会先用 \`HTTP HEAD\` 探测 \`ARLabMain.json\`，缺失时进入占位 UI（CSS 3D 立方体 + 构建步骤说明），不会让用户看到一个白屏或 UnityLoader undefined 报错。

## 构建步骤

### 1. Unity Editor 构建

- 用 **Unity 2021.3 LTS** 打开 \`unity/ImatuARLab\`
- \`File → Build Settings…\`
- Platform 切到 **WebGL**
- 点 **Build**，输出目录选择 \`unity/ImatuARLab/Builds/WebGL/\`

### 2. 拷贝到 Angular assets

把整个 \`Builds/WebGL/\` 目录下的内容拷贝到：

\`\`\`
src/assets/ar-lab/build/
\`\`\`

### 3. 重新构建 Angular

\`\`\`bash
npm run build
\`\`\`

## 占位符行为

构建缺失时 AR Lab 页面会展示：

1. CSS 3D 旋转立方体（不依赖 Three.js）
2. 缺失构建路径提示
3. Unity Editor 构建步骤文档
4. "重新检测"和"强制尝试加载"按钮
5. 硬件控制 / 传感器数据 / 模拟实验功能继续可用
`;

function main() {
  if (!existsSync(PLACEHOLDER_DIR)) {
    try {
      mkdirSync(PLACEHOLDER_DIR, { recursive: true });
      console.log(`[ensure-unity-build] created ${PLACEHOLDER_DIR}`);
    } catch (err) {
      console.error(`[ensure-unity-build] failed to create ${PLACEHOLDER_DIR}: ${err?.message ?? err}`);
      process.exit(1);
    }
  }

  if (!existsSync(PLACEHOLDER_FILE)) {
    try {
      writeFileSync(PLACEHOLDER_FILE, README_CONTENT, 'utf8');
      console.log(`[ensure-unity-build] wrote ${PLACEHOLDER_FILE}`);
    } catch (err) {
      console.error(`[ensure-unity-build] failed to write ${PLACEHOLDER_FILE}: ${err?.message ?? err}`);
      process.exit(1);
    }
  } else {
    console.log(`[ensure-unity-build] placeholder already exists at ${PLACEHOLDER_FILE}`);
  }

  process.exit(0);
}

main();
