#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class SimpleSDKGenerator {
  constructor() {
    this.sdkDir = path.join(__dirname, '..', 'sdk', 'imatu-sdk-ts');
    this.openapiPath = path.join(this.sdkDir, 'openapi.json');
  }

  async run() {
    try {
      console.log('🚀 开始生成TypeScript SDK...');
      
      // 读取OpenAPI规范
      const openapiSpec = this.readOpenAPISpec();
      
      // 生成基础文件
      this.generateBaseFiles();
      
      // 生成API客户端
      this.generateAPIClients(openapiSpec);
      
      // 生成索引文件
      this.generateIndexFile();
      
      console.log('✅ TypeScript SDK生成完成！');
      console.log(`📁 输出目录: ${this.sdkDir}`);
      
    } catch (error) {
      console.error('❌ SDK生成失败:', error.message);
      process.exit(1);
    }
  }

  readOpenAPISpec() {
    console.log('📄 读取OpenAPI规范...');
    
    if (!fs.existsSync(this.openapiPath)) {
      throw new Error(`找不到OpenAPI规范文件: ${this.openapiPath}`);
    }
    
    const content = fs.readFileSync(this.openapiPath, 'utf8');
    const spec = JSON.parse(content);
    
    console.log(`✅ 成功读取OpenAPI规范，包含 ${Object.keys(spec.paths || {}).length} 个API路径`);
    return spec;
  }

  generateBaseFiles() {
    console.log('🏗️ 生成基础SDK文件...');
    
    const srcDir = path.join(this.sdkDir, 'src');
    
    // 确保src目录存在
    if (!fs.existsSync(srcDir)) {
      fs.mkdirSync(srcDir, { recursive: true });
    }
    
    // 生成客户端文件
    const clientContent = this.generateClientFile();
    fs.writeFileSync(path.join(srcDir, 'client.ts'), clientContent);
    console.log('   📝 client.ts');
    
    // 生成类型定义文件
    const typesContent = this.generateTypesFile();
    fs.writeFileSync(path.join(srcDir, 'types.ts'), typesContent);
    console.log('   📝 types.ts');
    
    // 生成配置文件
    const configContent = this.generateConfigFile();
    fs.writeFileSync(path.join(srcDir, 'config.ts'), configContent);
    console.log('   📝 config.ts');
  }

  generateClientFile() {
    return `import axios from 'axios';
import { SDKConfig } from './types';

export class APIClient {
  private config;
  private client;

  constructor(config) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 10000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers
      }
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        if (this.config.accessToken) {
          config.headers.Authorization = \`Bearer \${this.config.accessToken}\`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.handleUnauthorized();
        }
        return Promise.reject(error);
      }
    );
  }

  handleUnauthorized() {
    this.config.accessToken = undefined;
    if (this.config.onUnauthorized) {
      this.config.onUnauthorized();
    }
  }

  setAccessToken(token) {
    this.config.accessToken = token;
  }

  get(url, config) {
    return this.client.get(url, config);
  }

  post(url, data, config) {
    return this.client.post(url, data, config);
  }

  put(url, data, config) {
    return this.client.put(url, data, config);
  }

  delete(url, config) {
    return this.client.delete(url, config);
  }
}`;
  }

  generateTypesFile() {
    return `export class SDKConfig {
  constructor() {
    this.baseURL = 'http://localhost:8000';
    this.timeout = 10000;
    this.headers = {
      'X-API-Version': '1.0.0'
    };
  }
}

export class APIError {
  constructor(code, message, details) {
    this.code = code;
    this.message = message;
    this.details = details;
  }
}

export class PaginatedResponse {
  constructor(data, total, page, pageSize, totalPages) {
    this.data = data;
    this.total = total;
    this.page = page;
    this.pageSize = pageSize;
    this.totalPages = totalPages;
  }
}

// 基础响应类型
export class BaseResponse {
  constructor(success, data, error, timestamp) {
    this.success = success;
    this.data = data;
    this.error = error;
    this.timestamp = timestamp;
  }
}`;
  }

  generateConfigFile() {
    return `import { SDKConfig } from './types';

export const defaultConfig = new SDKConfig();

export function createConfig(overrides) {
  const config = new SDKConfig();
  if (overrides) {
    Object.assign(config, overrides);
  }
  return config;
}`;
  }

  generateAPIClients(openapiSpec) {
    console.log('🤖 生成API客户端...');
    
    const generatedDir = path.join(this.sdkDir, 'src', 'generated');
    
    // 确保generated目录存在
    if (!fs.existsSync(generatedDir)) {
      fs.mkdirSync(generatedDir, { recursive: true });
    }
    
    // 从OpenAPI规范提取模块
    const modules = this.extractModules(openapiSpec);
    
    modules.forEach(module => {
      const clientCode = this.generateModuleClient(module);
      const filePath = path.join(generatedDir, module.name + '.ts');
      fs.writeFileSync(filePath, clientCode);
      console.log('   📦 ' + module.name + '.ts');
    });
  }

  extractModules(openapiSpec) {
    const paths = openapiSpec.paths || {};
    const modules = new Map();
    
    Object.keys(paths).forEach(path => {
      // 根据路径提取模块名
      const moduleMatch = path.match(/^\/api\/v1\/([^\/]+)/);
      if (moduleMatch) {
        const moduleName = moduleMatch[1];
        if (!modules.has(moduleName)) {
          modules.set(moduleName, {
            name: moduleName,
            paths: []
          });
        }
        modules.get(moduleName).paths.push({ path, methods: paths[path] });
      }
    });
    
    return Array.from(modules.values());
  }

  generateModuleClient(module) {
    const className = this.capitalize(module.name) + 'API';
    
    let methods = '';
    
    module.paths.forEach(({ path, methods: pathMethods }) => {
      Object.keys(pathMethods).forEach(method => {
        const operation = pathMethods[method];
        const methodName = this.generateMethodName(path, method);
        const responseType = operation.responses && operation.responses['200'] ? 
          'any' : 'void';
          
        methods += \`
  // \${operation.summary || operation.description || \`\${method.toUpperCase()} \${path}\`}
  async \${methodName}(params) {
    const url = '\${path}';
    const config = { params };
    
    try {
      const response = await this.client.\${method}(url, params, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
\`;
      });
    });
    
    return \`// Auto-generated \${module.name} API Client

import { APIClient } from '../client';

export class \${className} {
  constructor(client) {
    this.client = client;
  }
\${methods}
}

// 导出实例创建函数
export function create\${className}(client) {
  return new \${className}(client);
}
\`;
  }

  generateMethodName(path, method) {
    // 简单的命名转换
    const cleanPath = path.replace(/^\\/api\\/v1\\//, '').replace(/\\//g, '_');
    return \`\${method}\${this.capitalize(cleanPath)}\`;
  }

  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  generateIndexFile() {
    console.log('🔗 生成索引文件...');
    
    const indexPath = path.join(this.sdkDir, 'src', 'index.ts');
    const indexContent = `// iMatuProject TypeScript SDK Entry Point
export * from './client';
export * from './types';
export * from './config';

// Generated API clients
export * from './generated/auth';
export * from './generated/users';
export * from './generated/ai';
export * from './generated/courses';
`;
    
    fs.writeFileSync(indexPath, indexContent);
    console.log('   📝 index.ts');
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  const generator = new SimpleSDKGenerator();
  generator.run();
}

module.exports = SimpleSDKGenerator;