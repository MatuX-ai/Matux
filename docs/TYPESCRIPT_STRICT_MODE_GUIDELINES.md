# TypeScript严格类型检查开发规范

## 📋 规范概述

本文档规定了iMatuProject前端项目中TypeScript严格类型检查的开发标准和最佳实践。

## 🎯 核心原则

### 1. 严格模式必须启用
所有TypeScript项目必须启用严格类型检查：
```json
{
  "strict": true,
  "noImplicitAny": true,
  "strictNullChecks": true,
  "strictFunctionTypes": true,
  "noImplicitThis": true,
  "noImplicitReturns": true,
  "noFallthroughCasesInSwitch": true
}
```

### 2. 禁止使用 `any` 类型
除非在极少数情况下且有充分理由，否则禁止使用 `any` 类型。

**❌ 错误示例**:
```typescript
function processData(data: any) {
  return data.value;
}
```

**✅ 正确示例**:
```typescript
interface DataStructure {
  value: string;
  timestamp: number;
}

function processData(data: DataStructure) {
  return data.value;
}
```

### 3. 明确定义接口和类型
所有复杂数据结构必须有明确的接口定义。

**推荐做法**:
```typescript
// 在 shared/models/ 目录下定义
export interface User {
  id: number;
  username: string;
  email: string;
  roles: UserRole[];
  createdAt: string;
}

export type UserRole = 'admin' | 'user' | 'guest';
```

## 🔧 类型安全工具函数

项目提供了一系列类型安全的工具函数：

### JSON处理
```typescript
import { safeJsonParse, safeJsonParseArray, safeJsonStringify } from '../shared/utils/type-safe-json.utils';

// 安全解析JSON对象
const userData = safeJsonParse<User>(localStorage.getItem('user'), defaultUser);

// 安全解析JSON数组
const tags = safeJsonParseArray<string>(idea.tags, []);

// 安全序列化
const jsonStr = safeJsonStringify(complexObject);
```

### 对象操作
```typescript
import { getObjectKeys, getObjectValues, getObjectEntries } from '../shared/utils/type-safe-json.utils';

const keys = getObjectKeys(user); // 类型安全的键数组
const values = getObjectValues(user); // 类型安全的值数组
```

## 🛡️ 运行时类型验证

### 输入验证
```typescript
import { validateRequiredProperties } from '../shared/utils/type-safe-json.utils';

const validation = validateRequiredProperties(userData, ['id', 'username', 'email']);
if (!validation.isValid) {
  throw new Error(`缺少必要属性: ${validation.missingKeys.join(', ')}`);
}
```

### 错误边界处理
```typescript
// 对于可能失败的操作，始终提供错误处理
try {
  const parsedData = safeJsonParse<ApiResponse>(response, fallbackData);
  // 处理解析后的数据
} catch (error) {
  console.error('数据处理失败:', error);
  // 使用默认值或显示错误信息
}
```

## 📁 项目结构规范

### 类型定义文件组织
```
src/
├── shared/
│   ├── models/                 # 数据模型接口
│   │   ├── user.interface.ts
│   │   ├── creative-idea.interface.ts
│   │   └── index.ts
│   ├── utils/
│   │   ├── type-safe-json.utils.ts
│   │   └── index.ts
│   └── types/                  # 全局类型定义
│       └── global.d.ts
```

### 命名约定
- 接口文件: `*.interface.ts`
- 工具函数文件: `*.utils.ts`
- 枚举类型: 使用 PascalCase
- 接口名称: 使用 PascalCase，通常以 `I` 开头（可选）

## 🔍 代码审查检查清单

在代码审查时，检查以下项目：

### ✅ 必须检查项
- [ ] 是否启用了严格类型检查
- [ ] 是否避免使用 `any` 类型
- [ ] 复杂数据结构是否有明确定义的接口
- [ ] JSON解析是否使用了类型安全的方法
- [ ] 是否有适当的错误处理机制
- [ ] 函数参数和返回值是否有明确类型

### ⚠️ 建议检查项
- [ ] 是否遵循命名约定
- [ ] 类型定义是否放在合适的目录中
- [ ] 是否重复造轮子（应该使用现有工具函数）
- [ ] 是否有足够的类型注释

## 🚫 常见反模式

### 1. 隐式any
```typescript
// ❌ 避免
function calculate(data) {
  return data.value * 2;
}

// ✅ 推荐
interface CalculationData {
  value: number;
}

function calculate(data: CalculationData): number {
  return data.value * 2;
}
```

### 2. 不安全的类型断言
```typescript
// ❌ 避免
const result = someData as MyType; // 可能导致运行时错误

// ✅ 推荐
const result = safeJsonParse<MyType>(someData, defaultValue);
```

### 3. 忽略null检查
```typescript
// ❌ 避免
function getUserName(user: User | null) {
  return user.name; // 可能导致运行时错误
}

// ✅ 推荐
function getUserName(user: User | null) {
  return user?.name ?? 'Unknown User';
}
```

## 📊 性能考虑

虽然严格类型检查会增加编译时间，但它带来的好处远大于成本：

1. **编译时错误检测**: 减少运行时错误
2. **更好的IDE支持**: 更准确的自动补全和重构
3. **代码可维护性**: 更清晰的代码意图
4. **团队协作**: 统一的编码标准

## 🔄 持续改进

定期回顾和更新此规范：
- 每季度审查一次类型使用情况
- 根据项目发展调整规范要求
- 收集团队反馈持续优化

---

**最后更新**: 2026年3月1日  
**版本**: 1.0  
**负责人**: 前端架构组