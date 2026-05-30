# iMato Pricing Modes - Shared Modules

**Purpose**: 共享模块和工具类，供三种版本共同使用

---

## 📦 包含的共享模块

### **1. Token 计费系统** (`token-billing/`)

#### 后端服务 (`backend/`)
- `TokenService` - Token 管理核心服务
- `PackageService` - 套餐管理服务
- `BillingService` - 计费逻辑处理

#### 前端服务 (`frontend/`)
- `TokenService` - Angular HTTP 客户端
- `TokenComponent` - 可复用的 UI 组件
- `TokenPipe` - Token 格式化管道

---

### **2. 许可证权限控制** (`license-permission/`)

- `LicensePermissionMiddleware` - 权限验证中间件
- `@require_license_type()` - 装饰器
- `PermissionMatrix` - 权限矩阵配置

---

### **3. 支付集成** (`payment-integration/`)

- `PaymentService` - 统一支付接口
- `WechatPayProvider` - 微信支付
- `AlipayProvider` - 支付宝支付
- `StripeProvider` - 国际支付（可选）

---

## 🔧 使用方法

### **在后端导入共享服务**

```python
# 从共享模块导入
from pricing_modes.shared.token_billing.backend import TokenService
from pricing_modes.shared.license_permission import require_license_type

# 在路由中使用
@router.post("/generate-course")
@require_license_type(["WINDOWS_LOCAL", "CLOUD_HOSTED"])
async def generate_course(
    current_user: User = Depends(get_current_user),
    token_service: TokenService = Depends()
):
    # 业务逻辑
    pass
```

### **在前端导入共享服务**

```typescript
// 从共享模块导入
import { TokenService } from '@pricing-modes/shared/token-billing/frontend';
import { TokenBalanceComponent } from '@pricing-modes/shared/token-billing/frontend';

// 在组件中使用
@Component({
  selector: 'app-pricing-page',
  template: `
    <app-token-balance [userId]="userId"></app-token-balance>
  `
})
export class PricingPageComponent {
  constructor(private tokenService: TokenService) {}
}
```

---

## 📋 开发规范

### **代码风格**
- ✅ 遵循项目统一的代码规范
- ✅ TypeScript 严格模式
- ✅ Python type hints
- ✅ 函数职责单一（< 50 行）

### **测试要求**
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试必须通过
- ✅ 性能测试达标

### **文档要求**
- ✅ 每个公开 API 必须有文档注释
- ✅ 提供使用示例
- ✅ 标注注意事项

---

## 🔄 版本兼容性

| 共享模块版本 | 开源版 | Windows 版 | 云托管版 |
|-------------|--------|-----------|---------|
| v1.0        | ✅     | ✅        | ✅      |

---

## 📞 维护团队

- **负责人**: AI Assistant
- **更新频率**: 按需更新
- **变更日志**: 详见 Git Commit History

---

## ⚠️ 注意事项

1. **避免循环依赖**: 共享模块不应依赖特定版本的代码
2. **向后兼容**: 修改共享 API 时需保持向后兼容
3. **充分测试**: 修改后需测试三种版本的兼容性
4. **文档同步**: API 变更需及时更新文档

---

**最后更新**: 2026-03-14
