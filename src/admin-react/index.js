/**
 * React Admin管理后台入口文件
 * @description 应用程序的根入口点
 * @author iMatuProject Team
 * @version 1.0.0
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// 引入基础样式
import './admin-react.css';

/**
 * 应用根容器
 * 使用React 18的新API创建根节点
 */
const root = ReactDOM.createRoot(document.getElementById('root'));

/**
 * 渲染React Admin应用
 * 严格模式用于突出潜在问题
 */
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

/**
 * 性能监控和错误处理
 * 生产环境中收集性能指标
 */
if (process.env.NODE_ENV === 'production') {
  // 可以在这里添加性能监控代码
  console.log('React Admin管理后台已启动');
}