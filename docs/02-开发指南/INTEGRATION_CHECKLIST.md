# OpenMTSciEd 前端集成检查清单

## ✅ 集成前准备

- [ ] 后端服务运行中 (`http://localhost:3000`)
- [ ] Neo4j连接正常
- [ ] API测试通过 (运行 `test-openmtscied-apis.ps1`)

---

## 📝 集成步骤清单

### 1. 环境配置

- [ ] 编辑 `g:\iMato\src\environments\environment.ts`
- [ ] 添加 `openMtSciEdApiUrl: 'http://localhost:3000/api/v1'`
- [ ] 编辑 `g:\iMato\src\environments\environment.prod.ts`
- [ ] 添加生产环境API地址

**验证**:
```typescript
// 在任意组件中测试
console.log(environment.openMtSciEdApiUrl);
// 应输出: http://localhost:3000/api/v1
```

---

### 2. 导入HttpClient

- [ ] 检查 `app.module.ts` 是否导入 `HttpClientModule`
- [ ] 或确保使用 `provideHttpClient()` (Angular 15+)

**代码**:
```typescript
// app.module.ts
import { HttpClientModule } from '@angular/common/http';

@NgModule({
  imports: [
    HttpClientModule,
    // ...
  ]
})
export class AppModule {}
```

---

### 3. 复制服务文件

- [ ] 复制 `G:\OpenMTSciEd\openmt-scied.service.ts` 
- [ ] 到 `g:\iMato\src\app\services\openmt-scied.service.ts`

**验证**:
```bash
# 检查文件是否存在
ls g:\iMato\src\app\services\openmt-scied.service.ts
```

---

### 4. 创建演示组件 (可选)

- [ ] 创建目录 `g:\iMato\src\app\components\openmt-demo`
- [ ] 从集成指南复制组件代码
- [ ] 或使用现有组件测试

---

### 5. 添加路由 (可选)

- [ ] 编辑 `app.routes.ts` 或路由配置
- [ ] 添加 `/openmt-demo` 路由

**代码**:
```typescript
{
  path: 'openmt-demo',
  loadComponent: () => import('./components/openmt-demo/openmt-demo.component')
    .then(m => m.OpenMtDemoComponent)
}
```

---

### 6. 测试集成

#### 基础测试
- [ ] 启动前端: `ng serve`
- [ ] 访问: `http://localhost:4200`
- [ ] 打开浏览器控制台 (F12)

#### API调用测试
在组件中使用服务:

```typescript
constructor(private openMtService: OpenMtSciEdService) {}

ngOnInit() {
  // 测试1: 获取教程列表
  this.openMtService.getTutorials(1, 5).subscribe({
    next: (data) => console.log('教程列表:', data),
    error: (err) => console.error('错误:', err)
  });
  
  // 测试2: 获取硬件项目
  this.openMtService.getHardwareProjects(1, 5).subscribe({
    next: (data) => console.log('硬件项目:', data),
    error: (err) => console.error('错误:', err)
  });
}
```

**预期结果**:
- ✅ 控制台输出教程数据
- ✅ 控制台输出硬件项目数据
- ✅ 无CORS错误
- ✅ 无404错误

---

## 🐛 常见问题排查

### 问题1: Cannot find module 'openmt-scied.service'

**原因**: 文件路径错误或未保存  
**解决**: 
```bash
# 确认文件存在
ls g:\iMato\src\app\services\openmt-scied.service.ts

# 检查导入路径
import { OpenMtSciEdService } from './services/openmt-scied.service';
```

---

### 问题2: No provider for HttpClient

**原因**: 未导入HttpClientModule  
**解决**: 在 `app.module.ts` 中添加 `HttpClientModule`

---

### 问题3: CORS Error

**症状**: `Access to XMLHttpRequest has been blocked by CORS policy`  
**解决**: Next.js默认允许跨域,检查后端是否正常启动

**验证**:
```bash
# 测试后端是否响应
curl http://localhost:3000/api/health
```

---

### 问题4: 404 Not Found

**原因**: API地址配置错误  
**检查**:
```typescript
// environment.ts
openMtSciEdApiUrl: 'http://localhost:3000/api/v1'  // 确保包含 /api/v1
```

---

### 问题5: TypeScript类型错误

**症状**: `Property 'openMtSciEdApiUrl' does not exist on type...`  
**解决**: 
1. 重启IDE/编辑器
2. 清除缓存: `rm -rf .angular/cache`
3. 重新编译: `ng build`

---

## 📊 集成验证清单

完成以下测试即表示集成成功:

- [ ] ✅ 能导入 `OpenMtSciEdService`
- [ ] ✅ 能注入服务到组件
- [ ] ✅ `getTutorials()` 返回数据
- [ ] ✅ `getHardwareProjects()` 返回数据
- [ ] ✅ `generateLearningPath()` 返回路径
- [ ] ✅ `getRecommendations()` 返回推荐
- [ ] ✅ 无控制台错误
- [ ] ✅ 无网络请求失败

---

## 🎯 下一步

集成成功后可以:

1. **创建实际功能页面**
   - 教程浏览页面
   - 学习路径可视化
   - 资源推荐卡片

2. **优化用户体验**
   - 添加加载状态
   - 添加错误提示
   - 添加缓存机制

3. **集成到现有流程**
   - 在用户学习中调用推荐API
   - 根据学习进度生成路径
   - 展示相关硬件项目

---

## 📚 参考文档

- **完整集成指南**: `FRONTEND_INTEGRATION_GUIDE.md`
- **API文档**: `backend-next/API_DOCUMENTATION.md`
- **快速参考**: `backend-next/API_QUICK_REFERENCE.md`

---

**集成时间估计**: 30-60分钟  
**难度**: ⭐⭐ (简单)
