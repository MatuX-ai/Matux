# iMato 国际化 (i18n) 指南

## 概述

iMato项目使用Angular框架内置的国际化支持，结合自定义的i18n服务来实现多语言功能。翻译文件存储在 `src/assets/i18n/` 目录中。

## 支持的語言

| 语言代码 | 语言名称 | 本地名称 | 状态 |
|----------|----------|----------|------|
| `zh-CN` | 简体中文 | 中文 | ✅ 已实现 |
| `en-US` | 英语(美国) | English | ✅ 已实现 |

## 文件结构

```
src/assets/i18n/
├── en-US.json         # 英文翻译文件
├── zh-CN.json         # 中文翻译文件
├── index.ts          # 语言元数据定义
├── helpers.ts        # 辅助函数
└── README.md         # 本文件
```

## 使用方法

### 1. 在组件中使用翻译服务

```typescript
import { Component } from '@angular/core';
import { I18nService } from '../../core/services/i18n.service';

@Component({
  selector: 'app-example',
  template: `
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
  `
})
export class ExampleComponent {
  constructor(private i18nService: I18nService) {}
  
  get title(): string {
    return this.i18nService.translate('home.title');
  }
  
  get description(): string {
    return this.i18nService.translate('home.subtitle');
  }
}
```

### 2. 使用语言切换器

项目已包含语言切换器组件：

```html
<app-language-switcher></app-language-switcher>
```

### 3. 添加新的翻译键

1. 在 `zh-CN.json` 中添加中文翻译：
```json
{
  "newSection": {
    "title": "新标题",
    "description": "新描述"
  }
}
```

2. 在 `en-US.json` 中添加对应的英文翻译：
```json
{
  "newSection": {
    "title": "New Title",
    "description": "New Description"
  }
}
```

3. 在组件中使用：
```typescript
this.i18nService.translate('newSection.title');
```

### 4. 带参数的翻译

支持带占位符的翻译：

```json
{
  "welcome": "欢迎, {{name}}!"
}
```

使用方式：
```typescript
const name = '张三';
const translation = this.i18nService.translate('welcome');
const formatted = translation.replace('{{name}}', name);
```

## 翻译文件结构

翻译文件使用JSON格式，支持嵌套结构：

```json
{
  "common": {
    "actions": {
      "save": "保存",
      "cancel": "取消",
      "delete": "删除"
    }
  },
  "home": {
    "title": "首页标题",
    "subtitle": "首页副标题"
  }
}
```

访问方式：`this.i18nService.translate('common.actions.save')`

## 添加新语言

1. 创建新的翻译文件，例如 `fr-FR.json`
2. 在 `index.ts` 中添加语言元数据：
```typescript
{
  code: 'fr-FR',
  name: 'French',
  nativeName: 'Français',
  direction: 'ltr',
  flag: '🇫🇷',
  locale: 'fr-FR'
}
```

3. 更新 `I18nService` 中的 `supportedLangs` 数组

## 最佳实践

1. **统一命名规范**：使用小写字母和点号分隔，如 `section.subsection.key`
2. **保持一致性**：确保所有语言文件有相同的结构
3. **及时更新**：添加新功能时，同步更新所有语言文件
4. **使用常量**：为常用翻译键定义常量
5. **测试覆盖**：确保翻译功能在各种语言环境下正常工作

## 故障排除

### 翻译键未找到
- 检查翻译键是否在所有语言文件中都存在
- 检查键路径是否正确
- 确保翻译文件已正确加载

### 语言切换后页面不更新
- 检查是否调用了 `window.location.reload()`
- 确认翻译文件路径是否正确
- 检查浏览器缓存

## 相关文件

- `src/app/core/services/i18n.service.ts` - i18n核心服务
- `src/app/shared/components/language-switcher/` - 语言切换组件
- `angular.json` - Angular i18n配置

---

**最后更新**: 2026-03-17  
**维护者**: iMato开发团队