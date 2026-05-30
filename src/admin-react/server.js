/**
 * React Admin管理后台启动脚本
 * @description 快速启动和测试React Admin应用
 * @author iMatuProject Team
 * @version 1.0.0
 */

const express = require('express');
const path = require('path');
const app = express();
const PORT = 3001;

// 静态文件服务
app.use(express.static(path.join(__dirname)));

// API路由（Mock数据服务）
app.get('/api/licenses', (req, res) => {
  // 返回Mock许可证数据
  const mockLicenses = Array.from({ length: 20 }, (_, i) => ({
    id: i + 1,
    licenseKey: `LICENSE-${String(i + 1).padStart(6, '0')}-ABC123`,
    orgName: `测试组织${i + 1}`,
    contactEmail: `contact${i + 1}@test.com`,
    licenseType: ['COMMERCIAL', 'ENTERPRISE', 'TRIAL'][Math.floor(Math.random() * 3)],
    status: ['ACTIVE', 'INACTIVE', 'EXPIRED'][Math.floor(Math.random() * 3)],
    createdAt: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
    expiryDate: new Date(Date.now() + Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
    maxUsers: Math.floor(Math.random() * 1000) + 10,
    maxDevices: Math.floor(Math.random() * 500) + 5,
    features: ['core_features', 'advanced_analytics'].slice(0, Math.floor(Math.random() * 2) + 1),
    notes: `这是第${i + 1}个测试许可证`
  }));
  
  res.json({
    data: mockLicenses,
    total: mockLicenses.length
  });
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`🚀 React Admin管理后台服务器启动成功！`);
  console.log(`📡 服务地址: http://localhost:${PORT}`);
  console.log(`📁 静态文件目录: ${__dirname}`);
  console.log(`💡 按 Ctrl+C 停止服务器`);
});