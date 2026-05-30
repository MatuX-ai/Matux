# OpenMTSciEd 前端集成 - 快速开始

## 🎯 目标
将OpenMTSciEd API集成到iMato Angular前端应用

---

## 📦 已准备的文件

### 1. 服务文件 (可直接使用)
**位置**: `G:\OpenMTSciEd\openmt-scied.service.ts`

**功能**: 
- ✅ 教程管理 (CRUD)
- ✅ 课件管理
- ✅ 学习路径生成
- ✅ 资源推荐
- ✅ 硬件项目管理

**包含**:
- 完整的TypeScript接口定义
- 所有API端点方法
- 错误处理支持
- RxJS Observable返回类型

---

### 2. 集成指南
**位置**: `G:\OpenMTSciEd\FRONTEND_INTEGRATION_GUIDE.md`

**内容**:
- 详细集成步骤
- 代码示例
- 演示组件完整代码
- 路由配置说明

---

### 3. 检查清单
**位置**: `G:\OpenMTSciEd\INTEGRATION_CHECKLIST.md`

**用途**:
- 逐步验证集成进度
- 常见问题排查
- 测试验证清单

---

## 🚀 5分钟快速集成

### 步骤1: 复制服务文件
```bash
# 从
G:\OpenMTSciEd\openmt-scied.service.ts

# 复制到
g:\iMato\src\app\services\openmt-scied.service.ts
```

### 步骤2: 配置环境
编辑 `g:\iMato\src\environments\environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000',
  openMtSciEdApiUrl: 'http://localhost:3000/api/v1',  // ← 添加这行
};
```

### 步骤3: 确保HttpClientModule已导入
在 `app.module.ts`:
```typescript
import { HttpClientModule } from '@angular/common/http';

@NgModule({
  imports: [HttpClientModule, /* ... */]
})
export class AppModule {}
```

### 步骤4: 在组件中使用
```typescript
import { Component, OnInit } from '@angular/core';
import { OpenMtSciEdService } from '../services/openmt-scied.service';

@Component({
  selector: 'app-home',
  template: `<div>{{ tutorials | json }}</div>`
})
export class HomeComponent implements OnInit {
  tutorials: any[] = [];

  constructor(private openMtService: OpenMtSciEdService) {}

  ngOnInit() {
    this.openMtService.getTutorials(1, 5).subscribe({
      next: (data) => this.tutorials = data.items,
      error: (err) => console.error(err)
    });
  }
}
```

### 步骤5: 测试
```bash
cd g:\iMato
ng serve
```

访问 `http://localhost:4200`,打开控制台查看数据。

---

## ✅ 验证成功

看到以下输出表示集成成功:

```javascript
// 浏览器控制台
{
  items: [...],
  total: 1,
  page: 1,
  size: 5,
  total_pages: 1
}
```

---

## 📋 完整API方法列表

```typescript
// 教程
getTutorials(page, size, subject?, gradeLevel?)
getTutorialById(id)
createTutorial(tutorial)
updateTutorial(id, tutorial)
deleteTutorial(id)

// 课件
getCoursewares(page, size, subject?, gradeLevel?, type?)
createCourseware(courseware)

// 学习路径
generateLearningPath(userId, currentGrade, subjects, learningGoals?)
getUserProgress(userId)

// 推荐
getRecommendations(userId, limit, subjects?)
getCoursewareRecommendations(userId, subject?, limit)

// 硬件项目
getHardwareProjects(page, size, difficulty?, category?, subject?)
createHardwareProject(project)
```

---

## 🔧 常用示例

### 示例1: 按科目筛选教程
```typescript
this.openMtService.getTutorials(1, 10, 'physics', '9-12')
  .subscribe(response => {
    console.log(`找到 ${response.total} 个物理教程`);
  });
```

### 示例2: 生成学习路径
```typescript
this.openMtService.generateLearningPath(
  userId,
  '9-12',
  ['physics', 'mathematics'],
  ['mechanics']
).subscribe(path => {
  console.log(`学习路径包含 ${path.nodes.length} 个节点`);
  console.log(`预计需要 ${path.estimated_duration_hours} 小时`);
});
```

### 示例3: 获取推荐
```typescript
this.openMtService.getRecommendations(userId, 5, ['physics'])
  .subscribe(response => {
    response.recommendations.forEach(rec => {
      console.log(`${rec.title} - 评分: ${rec.score}`);
    });
  });
```

### 示例4: 获取硬件项目
```typescript
this.openMtService.getHardwareProjects(1, 10, 'beginner', 'electronics')
  .subscribe(response => {
    response.items.forEach(project => {
      console.log(`${project.title} - 难度: ${project.difficulty_level}`);
    });
  });
```

---

## ⚠️ 注意事项

1. **后端必须运行**: 确保 `npm run dev` 在 `G:\OpenMTSciEd\backend-next` 中运行
2. **端口3000**: API服务在3000端口,不是8000
3. **CORS**: Next.js默认允许跨域,无需额外配置
4. **错误处理**: 始终订阅时提供error回调
5. **取消订阅**: 组件销毁时取消订阅避免内存泄漏

---

## 🐛 故障排查速查

| 问题 | 可能原因 | 解决 |
|------|---------|------|
| Cannot find module | 文件路径错误 | 检查导入路径 |
| No provider for HttpClient | 未导入模块 | 添加HttpClientModule |
| CORS Error | 后端未启动 | 启动后端服务 |
| 404 Not Found | URL错误 | 检查environment配置 |
| TypeScript错误 | IDE缓存 | 重启IDE |

---

## 📚 相关文档

- **详细指南**: `FRONTEND_INTEGRATION_GUIDE.md` (579行)
- **检查清单**: `INTEGRATION_CHECKLIST.md` (226行)
- **API文档**: `backend-next/API_DOCUMENTATION.md`
- **快速参考**: `backend-next/API_QUICK_REFERENCE.md`
- **测试报告**: `backend-next/API_FINAL_TEST_REPORT.md`

---

## 💡 提示

- 使用演示组件快速测试所有API
- 查看浏览器Network面板调试请求
- 参考 `openmt-scied.service.ts` 中的接口定义
- 遇到任何问题先查看 `INTEGRATION_CHECKLIST.md`

---

**准备好了吗?开始集成吧!** 🚀

预计时间: 30-60分钟  
难度: ⭐⭐ (简单)  
成功率: 99% (如果按照步骤)
