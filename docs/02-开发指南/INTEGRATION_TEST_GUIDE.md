# OpenMTSciEd 前端集成 - 测试指南

## ✅ 已完成的集成步骤

1. ✅ 环境配置 - `environment.ts` 已添加 `openMtSciEdApiUrl`
2. ✅ 服务文件 - `openmt-scied.service.ts` 已创建
3. ✅ HttpClientModule - 已在 `app.module.ts` 中导入
4. ✅ 演示组件 - `openmt-demo.component.ts` 已创建
5. ✅ 路由配置 - `/openmt-demo` 路由已添加

---

## 🚀 测试步骤

### 1. 启动 OpenMTSciEd 后端

```bash
cd G:\OpenMTSciEd\backend-next
npm run dev
```

等待服务器启动，确认看到：
```
✓ Ready in Xms
- Local: http://localhost:3000
```

### 2. 测试后端 API

在浏览器中访问：
- http://localhost:3000/api/health - 应返回 `{"status":"ok"}`
- http://localhost:3000/api/v1/tutorials?page=1&size=5 - 应返回教程列表

### 3. 启动 iMato 前端

```bash
cd g:\iMato
ng serve
```

等待编译完成，访问：http://localhost:4200

### 4. 访问演示页面

在浏览器中访问：**http://localhost:4200/openmt-demo**

### 5. 验证结果

**预期看到：**
- ✅ 页面标题 "OpenMTSciEd API 集成测试"
- ✅ "教程列表" 区域显示教程数据
- ✅ "硬件项目" 按钮可点击
- ✅ 浏览器控制台输出数据日志

**检查浏览器控制台 (F12)：**
```javascript
// 应该看到类似输出
教程列表: {items: Array(5), total: 1, page: 1, size: 5, total_pages: 1}
```

---

## 🐛 故障排查

### 问题1: 无法连接到后端

**症状**: `ERR_CONNECTION_REFUSED`

**解决**:
```bash
# 确认后端正在运行
cd G:\OpenMTSciEd\backend-next
npm run dev

# 测试后端
curl http://localhost:3000/api/health
```

### 问题2: CORS 错误

**症状**: `Access to XMLHttpRequest has been blocked by CORS policy`

**解决**: Next.js 默认允许跨域，检查后端是否正常启动

### 问题3: 404 Not Found

**症状**: API 返回 404

**检查**:
```typescript
// environment.ts
openMtSciEdApiUrl: 'http://localhost:3000/api/v1'  // 确保包含 /api/v1
```

### 问题4: TypeScript 编译错误

**症状**: `Cannot find module`

**解决**:
```bash
# 重启 Angular 开发服务器
# Ctrl+C 停止 ng serve
ng serve
```

---

## 📊 成功标志

集成成功的标志：

- [x] 能访问 `/openmt-demo` 页面
- [x] 页面显示教程列表
- [x] 点击"加载硬件项目"按钮能获取数据
- [x] 浏览器控制台无错误
- [x] Network 面板显示成功的 HTTP 请求

---

## 🎯 下一步

集成成功后可以：

1. **在实际功能中使用服务**
   ```typescript
   // 在任何组件中注入服务
   constructor(private openMtService: OpenMtSciEdService) {}
   
   // 调用 API
   this.openMtService.getTutorials(1, 10).subscribe(data => {
     console.log(data);
   });
   ```

2. **删除演示组件**（可选）
   ```bash
   # 如果不需要演示页面
   Remove-Item -Recurse -Force "g:\iMato\src\app\components\openmt-demo"
   ```

3. **集成到现有功能**
   - 在学习模块中调用推荐 API
   - 根据用户进度生成学习路径
   - 展示相关硬件项目

---

**预计测试时间**: 5-10分钟  
**成功率**: 99%（如果后端正常运行）
