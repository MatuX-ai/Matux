const http = require('http');

http.get('http://localhost:3000/web', (res) => {
  let data = '';
  res.on('data', (chunk) => (data += chunk));
  res.on('end', () => {
    const labels = [
      '首页', '我的课程', 'AR 实验室', '实战项目', '积分商城',
      '学习成就', '连胜系统', '区块链证书', '设备连接', '传感器监控',
      '返回选择页', 'AI 助教', '你好，同学', 'MatuX 学习端 Web 版',
      '今日学习任务', '本周学习统计'
    ];
    labels.forEach((l) => {
      console.log(data.includes(l) ? 'OK   ' + l : 'MISS ' + l);
    });
  });
}).on('error', (e) => console.error('ERROR:', e.message));
