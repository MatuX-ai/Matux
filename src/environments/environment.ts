export const environment = {
  production: false,
  // 【P3-4 修复】使用相对路径，走 SPA server (8080) 的代理，避免浏览器 CORS 预检
  //   - 此前 apiUrl: 'http://localhost:8000' 会让 SPA 在 localhost:8080
  //     请求 8000 时产生 CORS 预检，有时被超时 / 拦截导致状态栏一直
  //     显示“后端未启动”。
  //   - 相对路径让请求落到同源 8080，由 spa-server.py 透明转发到 8000。
  apiUrl: '',
  // 【P3-4 修复】WebSocket 也使用相对路径，同理走 SPA server 代理（若需）
  wsUrl: '',
  openMtSciEdApiUrl: '/api/v1', // OpenMTSciEd API

  /** HTTP 请求超时时间（毫秒）- 开发环境下较短，便于 Mock 降级快速生效 */
  httpTimeout: 5000,

  /**
   * 【P4-A】选课记录相关 API 配置。
   *   - enrollmentsApiUrl: 后端 endpoint；当前后端尚未提供 student/enrollments
   *     端点，这里暂时指向 /api/v1/micro-course/ 作为实验通道。
   *   - useRealEnrollmentsApi: 是否走真实 HTTP（默认 false，保持以前 mock 体验）。
   *     调试 P3-1 重试卡片时可临时设为 true。
   */
  enrollmentsApiUrl: '/api/v1/student/enrollments',
  useRealEnrollmentsApi: false,

  /** OAuth 应用凭证 */
  oauth: {
    github: {
      clientId: 'your_github_client_id',
    },
    google: {
      clientId: 'your_google_client_id',
    },
    wechat: {
      appId: 'your_wechat_app_id',
    },
    qq: {
      appId: 'your_qq_app_id',
    },
  } as const,
};
