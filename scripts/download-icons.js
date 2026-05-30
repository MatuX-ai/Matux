#!/usr/bin/env node

/**
 * 图标下载工具
 * 从 Google Material Icons 下载 SVG 图标到本地
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

// 常用图标列表（可以根据需要扩展）
const ICONS_TO_DOWNLOAD = [
  // 教育相关
  'school', 'menu_book', 'psychology', 'auto_stories', 'workspace_premium',
  'emoji_events', 'cast_for_education', 'language', 'view_in_ar',

  // 技术相关
  'code', 'memory', 'dns', 'cloud', 'security', 'fingerprint',
  'data_usage', 'api', 'storage', 'computer', 'smartphone',

  // 媒体相关
  'play_circle', 'pause_circle', 'volume_up', 'videocam', 'headphones',
  'radio', 'photo_camera', 'image', 'music_note', 'mic',

  // 社交相关
  'people', 'person', 'group', 'forum', 'chat', 'email',
  'phone', 'location_on', 'share', 'notifications',

  // 导航相关
  'home', 'menu', 'close', 'arrow_forward', 'arrow_back',
  'expand_more', 'expand_less', 'more_vert', 'search', 'refresh',

  // 状态相关
  'check_circle', 'error', 'warning', 'info', 'hourglass_empty',
  'schedule', 'favorite', 'star', 'bookmark', 'thumb_up',

  // 动作相关
  'add', 'edit', 'delete', 'save', 'download', 'upload',
  'print', 'file_download', 'file_upload', 'content_copy',

  // 营销相关
  'rocket', 'trending_up', 'analytics', 'touch_app', 'devices',
  'brush', 'lightbulb', 'shopping_cart', 'payment', 'local_offer',
];

const OUTPUT_DIR = path.join(__dirname, '..', 'src', 'assets', 'icons');
const MATERIAL_ICONS_BASE_URL = 'https://raw.githubusercontent.com/google/material-design-icons/master/';

/**
 * 确保目录存在
 */
function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`创建目录：${dir}`);
  }
}

/**
 * 下载文件
 */
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);

    https.get(url, (response) => {
      if (response.statusCode === 200) {
        response.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve(dest);
        });
      } else {
        file.close();
        reject(new Error(`下载失败：${url} - ${response.statusCode}`));
      }
    }).on('error', (err) => {
      fs.unlinkSync(dest);
      reject(err);
    });
  });
}

/**
 * 下载单个图标
 */
async function downloadIcon(iconName) {
  const styles = ['outlined', 'round', 'sharp', 'twotone'];
  const downloaded = [];

  for (const style of styles) {
    const url = `${MATERIAL_ICONS_BASE_URL}src/${style}/svg/production/ic_${iconName}_24px.svg`;
    const dest = path.join(OUTPUT_DIR, style, `${iconName}.svg`);

    try {
      ensureDir(path.dirname(dest));
      await downloadFile(url, dest);
      downloaded.push(`${iconName} (${style})`);
      console.log(`✓ 已下载：${iconName} - ${style}`);
    } catch (error) {
      console.log(`✗ 跳过：${iconName} - ${style}`);
    }
  }

  return downloaded;
}

/**
 * 生成图标索引文件
 */
function generateIconIndex() {
  const indexContent = `/**
 * 图标索引文件
 * 自动生成 - 请勿手动修改
 */

export const ICONS = ${JSON.stringify(ICONS_TO_DOWNLOAD, null, 2)};

export const ICON_PATHS = {
${ICONS_TO_DOWNLOAD.map(name => `  '${name}': 'assets/icons/outlined/${name}.svg'`).join(',\n')}
};

export function getIconPath(name: string, style: 'outlined' | 'round' | 'sharp' | 'twotone' = 'outlined'): string {
  return \`assets/icons/\${style}/\${name}.svg\`;
}
`;

  const indexPath = path.join(OUTPUT_DIR, 'icon-index.ts');
  fs.writeFileSync(indexPath, indexContent);
  console.log(`✓ 已生成图标索引：${indexPath}`);
}

/**
 * 生成 Angular Module
 */
function generateAngularModule() {
  const moduleContent = `import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * 图标模块
 * 提供本地 SVG 图标支持
 */
@NgModule({
  declarations: [],
  imports: [
    CommonModule,
  ],
  exports: [],
})
export class IconModule { }
`;

  const modulePath = path.join(OUTPUT_DIR, 'icon.module.ts');
  fs.writeFileSync(modulePath, moduleContent);
  console.log(`✓ 已生成 Angular 模块：${modulePath}`);
}

/**
 * 主函数
 */
async function main() {
  console.log('🚀 开始下载 Material Icons...\n');

  ensureDir(OUTPUT_DIR);

  let totalDownloaded = 0;

  for (const iconName of ICONS_TO_DOWNLOAD) {
    const downloaded = await downloadIcon(iconName);
    totalDownloaded += downloaded.length;

    // 添加小延迟，避免请求过快
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log(`\n✅ 完成！共下载 ${totalDownloaded} 个图标`);
  console.log(`📁 保存位置：${OUTPUT_DIR}`);

  // 生成索引文件
  generateIconIndex();
  generateAngularModule();

  console.log('\n💡 使用示例:');
  console.log('  <mat-icon svgIcon="school"></mat-icon>');
  console.log('  或者在组件中:');
  console.log('  import { ICON_PATHS } from \'./assets/icons/icon-index\';');
}

// 运行主函数
main().catch(console.error);
