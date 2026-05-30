import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-minimal-dashboard',
  template: `
    <div style="padding: 2rem; font-family: Arial, sans-serif;">
      <h1 style="color: #333; text-align: center;">🎓 iMatuProject 教育平台</h1>
      <div
        style="max-width: 800px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);"
      >
        <h2 style="color: #2196F3; border-bottom: 2px solid #2196F3; padding-bottom: 0.5rem;">
          欢迎使用 iMatuProject 平台
        </h2>

        <div
          style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin: 2rem 0;"
        >
          <div
            style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; text-align: center;"
          >
            <h3 style="margin: 0 0 1rem 0; color: #1976D2;">📊 仪表盘</h3>
            <p style="margin: 0; color: #555;">查看学习进度和统计数据</p>
          </div>

          <div
            style="background: #e8f5e8; padding: 1.5rem; border-radius: 8px; text-align: center;"
          >
            <h3 style="margin: 0 0 1rem 0; color: #388E3C;">📚 课程中心</h3>
            <p style="margin: 0; color: #555;">访问丰富的教育资源</p>
          </div>

          <div
            style="background: #fff3e0; padding: 1.5rem; border-radius: 8px; text-align: center;"
          >
            <h3 style="margin: 0 0 1rem 0; color: #EF6C00;">👥 社区互动</h3>
            <p style="margin: 0; color: #555;">与其他学习者交流分享</p>
          </div>

          <div
            style="background: #f3e5f5; padding: 1.5rem; border-radius: 8px; text-align: center;"
          >
            <h3 style="margin: 0 0 1rem 0; color: #7B1FA2;">⚙️ 设置管理</h3>
            <p style="margin: 0; color: #555;">个性化您的学习体验</p>
          </div>
        </div>

        <div style="background: #fafafa; padding: 1.5rem; border-radius: 8px; margin-top: 2rem;">
          <h3 style="margin-top: 0; color: #666;">平台特色功能</h3>
          <ul style="color: #555; line-height: 1.6;">
            <li>✨ AI智能推荐学习路径</li>
            <li>🎮 AR/VR沉浸式学习体验</li>
            <li>🤝 协作式项目开发</li>
            <li>📱 移动端无缝同步</li>
            <li>🔒 区块链证书认证</li>
          </ul>
        </div>

        <div style="text-align: center; margin-top: 2rem;">
          <button
            style="background: #2196F3; color: white; border: none; padding: 0.8rem 2rem; border-radius: 4px; cursor: pointer; font-size: 1rem;"
          >
            开始学习之旅
          </button>
        </div>
      </div>

      <footer
        style="text-align: center; color: #888; margin-top: 2rem; padding: 1rem; border-top: 1px solid #eee;"
      >
        <p>© 2026 iMatuProject 教育科技平台 | 版本 1.0.0</p>
      </footer>
    </div>
  `,
  standalone: true,
  imports: [CommonModule],
})
export class MinimalDashboardComponent {
  constructor() {}
}
