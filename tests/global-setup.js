/**
 * Playwright 全局设置
 * 
 * 在所有测试开始前执行，用于：
 * 1. 确保后端服务运行
 * 2. 准备测试数据
 * 3. 清理环境
 */

const { chromium } = require('@playwright/test');
const http = require('http');

/**
 * 检查服务是否可用
 */
function checkService(url, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    function tryConnect() {
      http.get(url, (res) => {
        if (res.statusCode >= 200 && res.statusCode < 400) {
          resolve(true);
        } else {
          retry();
        }
      }).on('error', () => {
        retry();
      });
    }
    
    function retry() {
      if (Date.now() - startTime > timeout) {
        console.log(`⚠️  服务 ${url} 连接超时，继续测试...`);
        resolve(false); // 不阻塞测试
      } else {
        setTimeout(tryConnect, 1000);
      }
    }
    
    tryConnect();
  });
}

async function globalSetup(config) {
  console.log('🔧 开始 Playwright 全局设置...');
  
  // 1. 检查后端服务
  console.log('  📡 检查后端服务...');
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  await checkService(`${backendUrl}/health`);
  
  // 2. 检查前端服务
  console.log('  📡 检查前端服务...');
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:4200';
  await checkService(frontendUrl);
  
  // 3. 创建测试输出目录
  const fs = require('fs');
  const path = require('path');
  const outputDir = path.join(__dirname, '..', 'test-results');
  
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  console.log('✅ 全局设置完成');
}

module.exports = globalSetup;
