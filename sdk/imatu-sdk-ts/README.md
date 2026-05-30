# iMatuProject TypeScript SDK

官方的iMatuProject TypeScript SDK，用于与后端API进行交互。

## 功能特性

- 🎯 类型安全的API客户端
- 🔧 自动化的SDK生成
- 📊 完整的测试覆盖
- 📚 详细的API文档
- ⚡ 异步操作支持
- 🔐 内置认证机制

## 安装

```bash
npm install @imatuproject/sdk
```

## 快速开始

```typescript
import { APIClient, createConfig } from '@imatuproject/sdk';

// 创建配置
const config = createConfig({
  baseURL: 'https://api.imatuproject.com',
  accessToken: 'your-access-token'
});

// 创建客户端实例
const client = new APIClient(config);

// 使用API
try {
  const response = await client.get('/api/v1/users');
  console.log(response.data);
} catch (error) {
  console.error('API调用失败:', error);
}
```

## 开发指南

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/imatuproject/sdk.git
cd sdk/imatu-sdk-ts

# 安装依赖
npm install

# 构建SDK
npm run build

# 运行测试
npm run test

# 生成文档
npm run docs
```

### 生成新的SDK版本

```bash
# 从后端导出最新的OpenAPI规范并生成SDK
node ../scripts/generate-sdk.js
```

## 目录结构

```
src/
├── client.ts          # 核心HTTP客户端
├── config.ts          # 配置管理
├── types.ts           # 公共类型定义
├── index.ts           # 入口文件
└── generated/         # 自动生成的API客户端
tests/
├── client.spec.ts     # 客户端测试
├── config.spec.ts     # 配置测试
└── generated/         # 生成代码测试
```

## API参考

详细的API文档请查看 [在线文档](https://imatuproject.github.io/sdk)。

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件