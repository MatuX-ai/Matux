#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SDKGenerator {
  constructor() {
    this.sdkDir = path.join(__dirname, 'sdk', 'imatu-sdk-ts');
    this.backendDir = path.join(__dirname, 'backend');
    this.openapiSpec = null;
  }

  async initialize() {
    console.log('🚀 初始化SDK生成环境...');
    
    // 检查必要目录
    if (!fs.existsSync(this.sdkDir)) {
      throw new Error(`SDK目录不存在: ${this.sdkDir}`);
    }

    if (!fs.existsSync(this.backendDir)) {
      throw new Error(`后端目录不存在: ${this.backendDir}`);
    }

    // 安装依赖
    this.installDependencies();
    
    console.log('✅ SDK环境初始化完成');
  }

  installDependencies() {
    console.log('📦 安装项目依赖...');
    try {
      process.chdir(this.sdkDir);
      execSync('npm install', { stdio: 'inherit' });
      console.log('✅ 依赖安装完成');
    } catch (error) {
      console.error('❌ 依赖安装失败:', error.message);
      throw error;
    }
  }

  async exportOpenAPISpec() {
    console.log('📄 导出OpenAPI规范...');
    
    try {
      // 启动后端服务临时导出API文档
      process.chdir(this.backendDir);
      
      // 使用Python脚本导出OpenAPI JSON
      const exportScript = `
import json
import sys
sys.path.append('.')
from main import app
from fastapi.openapi.utils import get_openapi

openapi_schema = get_openapi(
    title=app.title,
    version=app.version,
    description=app.description,
    routes=app.routes,
)

print(json.dumps(openapi_schema, indent=2, ensure_ascii=False))
`;
      
      const openapiJson = execSync(`python -c "${exportScript}"`, {
        encoding: 'utf8'
      });
      
      this.openapiSpec = JSON.parse(openapiJson);
      
      // 保存到文件
      const outputPath = path.join(this.sdkDir, 'openapi.json');
      fs.writeFileSync(outputPath, openapiJson, 'utf8');
      
      console.log(`✅ OpenAPI规范已导出到: ${outputPath}`);
      return outputPath;
      
    } catch (error) {
      console.error('❌ OpenAPI导出失败:', error.message);
      throw error;
    }
  }

  async generateSDK(openapiPath) {
    console.log('🔧 生成TypeScript SDK...');
    
    try {
      process.chdir(this.sdkDir);
      
      // 使用swagger-codegen-cli生成SDK
      const templateDir = path.join(__dirname, 'templates', 'typescript-fetch');
      const outputDir = path.join(this.sdkDir, 'src', 'generated');
      
      // 确保输出目录存在
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      // 生成基础SDK结构
      this.generateBaseSDK();
      
      // 生成API客户端
      this.generateAPIClients();
      
      console.log('✅ TypeScript SDK生成完成');
      
    } catch (error) {
      console.error('❌ SDK生成失败:', error.message);
      throw error;
    }
  }

  generateBaseSDK() {
    console.log('🏗️ 生成基础SDK结构...');
    
    const baseFiles = {
      'index.ts': this.generateIndexFile(),
      'client.ts': this.generateClientFile(),
      'types.ts': this.generateTypesFile(),
      'config.ts': this.generateConfigFile()
    };
    
    const srcDir = path.join(this.sdkDir, 'src');
    
    Object.entries(baseFiles).forEach(([filename, content]) => {
      const filePath = path.join(srcDir, filename);
      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`   📝 ${filename}`);
    });
  }

  generateIndexFile() {
    return `// iMatuProject TypeScript SDK Entry Point
export * from './client';
export * from './types';
export * from './config';

// Auto-generated API clients
export * from './generated';
`;
  }

  generateClientFile() {
    return `import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { SDKConfig } from './config';

export class APIClient {
  private client: AxiosInstance;
  private config: SDKConfig;

  constructor(config: SDKConfig) {
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
        // 添加认证token
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
        // 统一错误处理
        if (error.response?.status === 401) {
          // 处理未授权错误
          this.handleUnauthorized();
        }
        return Promise.reject(error);
      }
    );
  }

  private handleUnauthorized() {
    // 清除token并触发重新登录
    this.config.accessToken = undefined;
    if (this.config.onUnauthorized) {
      this.config.onUnauthorized();
    }
  }

  public setAccessToken(token: string) {
    this.config.accessToken = token;
  }

  public get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get(url, config);
  }

  public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post(url, data, config);
  }

  public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put(url, data, config);
  }

  public delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete(url, config);
  }
}
`;
  }

  generateTypesFile() {
    return `// Generated API Types

export interface SDKConfig {
  baseURL: string;
  accessToken?: string;
  timeout?: number;
  headers?: Record<string, string>;
  onUnauthorized?: () => void;
}

export interface APIError {
  code: string;
  message: string;
  details?: any;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 基础响应类型
export interface BaseResponse<T = any> {
  success: boolean;
  data?: T;
  error?: APIError;
  timestamp: string;
}
`;
  }

  generateConfigFile() {
    return `import { SDKConfig } from './types';

export const defaultConfig: SDKConfig = {
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'X-API-Version': '1.0.0'
  }
};

export function createConfig(overrides?: Partial<SDKConfig>): SDKConfig {
  return {
    ...defaultConfig,
    ...overrides
  };
}
`;
  }

  generateAPIClients() {
    console.log('🤖 生成API客户端...');
    
    // 基于OpenAPI规范生成各个模块的客户端
    const modules = this.extractModules();
    const generatedDir = path.join(this.sdkDir, 'src', 'generated');
    
    modules.forEach(module => {
      const clientCode = this.generateModuleClient(module);
      const filePath = path.join(generatedDir, `${module.name}.ts`);
      fs.writeFileSync(filePath, clientCode, 'utf8');
      console.log(`   📦 ${module.name} API Client`);
    });
  }

  extractModules() {
    // 从OpenAPI规范中提取API模块
    if (!this.openapiSpec) return [];
    
    const paths = this.openapiSpec.paths || {};
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
        modules.get(moduleName).paths.push(path);
      }
    });
    
    return Array.from(modules.values());
  }

  generateModuleClient(module) {
    return `// Auto-generated ${module.name} API Client

import { APIClient } from '../client';
import { BaseResponse } from '../types';

export class ${this.capitalize(module.name)}API {
  constructor(private client: APIClient) {}

  // 在这里添加具体的API方法
  // 示例方法：
  /*
  async getList(params?: any): Promise<BaseResponse<any[]>> {
    const response = await this.client.get('/api/v1/${module.name}', { params });
    return response.data;
  }

  async getById(id: string): Promise<BaseResponse<any>> {
    const response = await this.client.get(`/api/v1/${module.name}/${id}`);
    return response.data;
  }

  async create(data: any): Promise<BaseResponse<any>> {
    const response = await this.client.post('/api/v1/${module.name}', data);
    return response.data;
  }

  async update(id: string, data: any): Promise<BaseResponse<any>> {
    const response = await this.client.put(`/api/v1/${module.name}/${id}`, data);
    return response.data;
  }

  async delete(id: string): Promise<BaseResponse<void>> {
    const response = await this.client.delete(`/api/v1/${module.name}/${id}`);
    return response.data;
  }
  */

  private capitalize(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}
`;
  }

  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  async build() {
    console.log('🔨 构建SDK...');
    
    try {
      process.chdir(this.sdkDir);
      execSync('npm run build', { stdio: 'inherit' });
      console.log('✅ SDK构建完成');
    } catch (error) {
      console.error('❌ SDK构建失败:', error.message);
      throw error;
    }
  }

  async runTests() {
    console.log('🧪 运行测试...');
    
    try {
      process.chdir(this.sdkDir);
      execSync('npm run test:coverage', { stdio: 'inherit' });
      console.log('✅ 测试完成');
    } catch (error) {
      console.error('❌ 测试失败:', error.message);
      throw error;
    }
  }

  async generateDocs() {
    console.log('📚 生成文档...');
    
    try {
      process.chdir(this.sdkDir);
      execSync('npm run docs', { stdio: 'inherit' });
      console.log('✅ 文档生成完成');
    } catch (error) {
      console.error('❌ 文档生成失败:', error.message);
      throw error;
    }
  }

  async run() {
    try {
      await this.initialize();
      const openapiPath = await this.exportOpenAPISpec();
      await this.generateSDK(openapiPath);
      await this.build();
      await this.runTests();
      await this.generateDocs();
      
      console.log('\\n🎉 SDK生成全流程完成！');
      console.log('📁 输出目录:', this.sdkDir);
      
    } catch (error) {
      console.error('\\n❌ SDK生成过程出现错误:', error.message);
      process.exit(1);
    }
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  const generator = new SDKGenerator();
  generator.run();
}

module.exports = SDKGenerator;
`;
  }

  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  const generator = new SDKGenerator();
  generator.run();
}

module.exports = SDKGenerator;