# Build Resources Directory

此目录用于存放 Electron Builder 需要的资源文件。

## 📁 必需文件

### icon.ico (必需)
- **尺寸**: 256x256 px (推荐)
- **格式**: ICO 格式，包含多个尺寸（16, 32, 48, 128, 256）
- **用途**: 
  - 应用程序图标
  - 安装包图标
  - 快捷方式图标
  - 卸载程序图标

**获取方式**:
1. 使用在线工具转换：https://convertio.co/png-ico/
2. 使用专业软件：ICOFX, Greenfish Icon Editor
3. 从 PNG 生成：`png2icns icon.ico icon.png`

### icon.png (可选但推荐)
- **尺寸**: 512x512 px
- **用途**: macOS 应用图标

## 🔧 临时解决方案

如果暂时没有图标，可以使用默认图标：

```bash
# 使用 electron-builder 默认图标
npx electron-builder create-dmg
```

## 📝 注意事项

1. **图标版权**: 确保使用的图标有合法授权
2. **尺寸要求**: Windows 至少需要 256x256 尺寸
3. **透明度**: 支持 alpha 通道（透明背景）
4. **多分辨率**: 建议包含多种尺寸以适应不同场景

## 🎨 设计建议

- 使用简洁的图形，避免过多细节
- 在 small size 下也能清晰识别
- 与 iMato 品牌风格一致
- 考虑深色/浅色主题下的显示效果

---

**当前状态**: ⚠️ 需要添加 icon.ico 文件  
**下一步**: 将设计好的图标放入此目录
