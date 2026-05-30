# 前端开发规范

## 1. 概述

本文档定义了 iMatuProject 前端开发的编码规范、最佳实践和技术标准，旨在提高代码质量、增强团队协作效率并确保项目的长期可维护性。

## 2. 代码风格规范

### 2.1 CSS/SCSS 规范

#### 2.1.1 属性顺序规范

严格按照以下顺序组织CSS属性：

```scss
// 1. CSS自定义属性
--custom-property: value;

// 2. 定位属性
position: relative;
top: 0;
right: 0;
bottom: 0;
left: 0;
z-index: 1;

// 3. 显示和布局
display: flex;
visibility: visible;
float: left;
clear: both;
overflow: hidden;

// 4. Flexbox/Grid属性
flex-direction: row;
justify-content: center;
align-items: center;
grid-template-columns: 1fr 1fr;

// 5. 盒模型
box-sizing: border-box;
width: 100px;
height: 50px;
margin: 10px;
padding: 5px;
border: 1px solid #ccc;

// 6. 背景和装饰
background-color: #fff;
box-shadow: 0 2px 4px rgba(0,0,0,0.1);
border-radius: 4px;

// 7. 字体和文本
color: #333;
font-family: Arial, sans-serif;
font-size: 14px;
font-weight: normal;
line-height: 1.5;
text-align: left;

// 8. 交互属性
cursor: pointer;
user-select: none;
pointer-events: auto;

// 9. 过渡和动画
transition: all 0.3s ease;
transform: translateX(0);
animation: slideIn 0.5s ease;
```

#### 2.1.2 选择器命名规范

- 使用BEM命名法：`.block__element--modifier`
- 组件类名使用前缀：`.c-component-name`
- 工具类使用前缀：`.u-utility-name`
- 状态类使用前缀：`.is-state-name`

```scss
// 正确示例
.c-button { }
.c-button__icon { }
.c-button--primary { }
.is-disabled { }
.u-text-center { }

// 错误示例
.button { }           // 缺少组件前缀
.btn_primary { }      // 命名不一致
.active-item { }      // 缺少状态前缀
```

#### 2.1.3 SCSS结构规范

```scss
// 组件样式结构示例
.c-component-name {
  // 1. CSS自定义属性
  --component-property: value;
  
  // 2. 基础样式（按属性顺序）
  position: relative;
  display: block;
  // ... 其他属性
  
  // 3. 伪类和伪元素
  &:hover {
    // 按属性顺序
  }
  
  &::before {
    // 按属性顺序
  }
  
  // 4. 子元素
  &__element {
    // 按属性顺序
  }
  
  // 5. 修饰符
  &--modifier {
    // 按属性顺序
  }
  
  // 6. 响应式变体
  @media (min-width: 768px) {
    // 按属性顺序
  }
}
```

### 2.2 JavaScript/TypeScript 规范

#### 2.2.1 命名规范

```javascript
// 变量命名 - 使用camelCase
const userName = 'John';
const isActive = true;
const userList = [];

// 常量命名 - 使用UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3;
const API_BASE_URL = 'https://api.example.com';

// 函数命名 - 使用camelCase，动词开头
function getUserInfo() { }
function calculateTotal() { }
function isValidEmail() { }

// 类命名 - 使用PascalCase
class UserService { }
class DataProcessor { }

// 接口命名 - 使用PascalCase，I前缀
interface IUser { }
interface IApiResponse { }
```

#### 2.2.2 文件命名规范

```
// 组件文件
user-profile.component.ts
user-profile.component.html
user-profile.component.scss

// 服务文件
user.service.ts
data-processing.service.ts

// 模块文件
user.module.ts
shared.module.ts

// 工具函数文件
string-utils.ts
date-helpers.ts
```

### 2.3 HTML 规范

#### 2.3.1 语义化标签

```html
<!-- 正确使用语义化标签 -->
<header>
  <nav>
    <ul>
      <li><a href="#">首页</a></li>
    </ul>
  </nav>
</header>

<main>
  <article>
    <h1>文章标题</h1>
    <p>文章内容...</p>
  </article>
</main>

<footer>
  <p>&copy; 2026 iMatuProject</p>
</footer>
```

#### 2.3.2 属性顺序

```html
<!-- HTML属性推荐顺序 -->
<input
  id="username"
  class="form-input"
  type="text"
  name="username"
  placeholder="请输入用户名"
  required
  autocomplete="off"
  aria-label="用户名输入框">
```

## 3. 设计系统规范

### 3.1 Design Tokens 使用

强制使用设计系统提供的Design Tokens：

```scss
// ✅ 正确 - 使用Design Tokens
.c-button {
  background-color: $primary-color;
  border-radius: $border-radius-button;
  font-size: $font-size-body-medium;
  padding: $spacing-sm $spacing-lg;
}

// ❌ 错误 - 使用硬编码值
.c-button {
  background-color: #007bff;
  border-radius: 4px;
  font-size: 14px;
  padding: 8px 16px;
}
```

### 3.2 组件设计原则

1. **单一职责原则** - 每个组件只负责一个功能
2. **可复用性** - 组件应该可以在不同场景下复用
3. **可配置性** - 通过props或CSS变量提供配置选项
4. **无障碍性** - 遵循WCAG标准，支持键盘导航

## 4. 性能优化规范

### 4.1 CSS性能

```scss
// ✅ 使用高效的CSS选择器
.c-button { }           // 优秀
.header .nav-item { }   // 良好
#header .nav-item { }   // 避免使用ID选择器

// ❌ 避免低效的选择器
div:nth-child(2n+1) span:first-child { }  // 复杂且低效
* { }                                     // 通用选择器影响性能
```

### 4.2 图片优化

```html
<!-- 使用适当的图片格式和懒加载 -->
<img 
  src="image.webp" 
  alt="描述文字"
  loading="lazy"
  width="300"
  height="200">

<!-- 响应式图片 -->
<picture>
  <source media="(min-width: 768px)" srcset="large.webp">
  <source media="(min-width: 480px)" srcset="medium.webp">
  <img src="small.webp" alt="响应式图片">
</picture>
```

## 5. 测试规范

### 5.1 单元测试

```typescript
// 组件测试示例
describe('UserProfileComponent', () => {
  let component: UserProfileComponent;
  let fixture: ComponentFixture<UserProfileComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [UserProfileComponent]
    });
    fixture = TestBed.createComponent(UserProfileComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should display user name', () => {
    component.user = { name: 'John Doe' };
    fixture.detectChanges();
    const nameElement = fixture.nativeElement.querySelector('.user-name');
    expect(nameElement.textContent).toContain('John Doe');
  });
});
```

### 5.2 E2E测试

```typescript
// E2E测试示例
describe('Login Flow', () => {
  it('should login successfully with valid credentials', () => {
    cy.visit('/login');
    cy.get('[data-cy=username]').type('user@example.com');
    cy.get('[data-cy=password]').type('password123');
    cy.get('[data-cy=submit]').click();
    cy.url().should('include', '/dashboard');
    cy.get('[data-cy=user-menu]').should('be.visible');
  });
});
```

## 6. 安全规范

### 6.1 XSS防护

```typescript
// ✅ 正确 - 使用Angular内置的安全机制
@Component({
  template: `<div [innerHTML]="safeContent"></div>`
})
export class SafeComponent {
  safeContent = this.sanitizer.bypassSecurityTrustHtml(userInput);
  
  constructor(private sanitizer: DomSanitizer) {}
}

// ❌ 锗误 - 直接绑定用户输入
@Component({
  template: `<div [innerHTML]="userInput"></div>`  // 危险！
})
export class UnsafeComponent {
  userInput = '<script>alert("XSS")</script>';
}
```

### 6.2 CSRF保护

```typescript
// 使用Angular HttpClient的CSRF保护
@Injectable()
export class ApiService {
  constructor(private http: HttpClient) {}

  postData(data: any): Observable<any> {
    return this.http.post('/api/data', data, {
      withCredentials: true  // 包含认证cookie
    });
  }
}
```

## 7. 工具链配置

### 7.1 ESLint配置

```javascript
// .eslintrc.js
module.exports = {
  extends: [
    '@angular-eslint/recommended',
    'plugin:@typescript-eslint/recommended'
  ],
  rules: {
    '@angular-eslint/component-selector': [
      'error',
      {
        type: 'element',
        prefix: 'app',
        style: 'kebab-case'
      }
    ],
    '@typescript-eslint/no-unused-vars': 'error',
    'prefer-const': 'error'
  }
};
```

### 7.2 Stylelint配置

```javascript
// .stylelintrc.js
module.exports = {
  extends: [
    'stylelint-config-standard-scss',
    'stylelint-config-recommended'
  ],
  plugins: [
    'stylelint-scss',
    'stylelint-order'
  ],
  rules: {
    'order/properties-order': [
      [
        // 按照前面定义的属性顺序
        'position',
        'top',
        'right',
        // ... 其他属性
      ],
      {
        unspecified: 'bottomAlphabetical',
        severity: 'error'
      }
    ]
  }
};
```

## 8. CI/CD集成

### 8.1 预提交检查

```json
// package.json scripts
{
  "scripts": {
    "pre-commit": "lint-staged",
    "lint:css": "stylelint \"src/**/*.scss\"",
    "lint:ts": "eslint \"src/**/*.ts\"",
    "test": "ng test",
    "build": "ng build --prod"
  }
}
```

### 8.2 GitHub Actions配置

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '16'
        
    - name: Install dependencies
      run: npm ci
      
    - name: Run linters
      run: |
        npm run lint:css
        npm run lint:ts
        
    - name: Run tests
      run: npm test -- --no-watch --no-progress --browsers=ChromeHeadless
      
    - name: Build application
      run: npm run build
```

## 9. 团队协作规范

### 9.1 Git提交规范

使用约定式提交格式：

```
feat: 添加用户登录功能
fix: 修复登录页面样式问题
docs: 更新API文档
style: 调整按钮组件样式顺序
refactor: 重构用户服务
test: 添加登录功能测试用例
chore: 更新依赖包版本
```

### 9.2 代码审查清单

审查时检查以下要点：
- [ ] 是否遵循编码规范
- [ ] 属性顺序是否正确
- [ ] 是否使用Design Tokens
- [ ] 是否有适当的测试覆盖
- [ ] 是否考虑了无障碍性
- [ ] 性能影响是否合理
- [ ] 安全性是否得到保障

## 10. 持续改进

### 10.1 定期回顾

- 每月进行一次规范执行情况回顾
- 收集团队反馈，持续优化规范
- 跟踪新技术趋势，及时更新规范

### 10.2 培训计划

- 新成员入职时进行规范培训
- 定期组织技术分享会
- 建立规范知识库和FAQ

---
*最后更新: 2026年2月27日*
*版本: 1.0.0*