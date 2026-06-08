/**
 * Playwright 全局清理
 * 
 * 在所有测试结束后执行，用于：
 * 1. 清理测试数据
 * 2. 关闭浏览器
 * 3. 生成测试报告
 */

async function globalTeardown(config) {
  console.log('🧹 开始 Playwright 全局清理...');
  
  // 清理可以在此处添加
  // 目前由 Playwright 自动处理
  
  console.log('✅ 全局清理完成');
}

module.exports = globalTeardown;
