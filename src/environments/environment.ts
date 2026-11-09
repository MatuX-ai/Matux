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
   * 【Phase1 修复】选课记录相关 API 配置。
   *   - enrollmentsApiUrl: 后端 /api/v1/courses/enrollments
   *     （course_catalog_routes 提供 GET 列表 + POST 报名）。
   *   - useRealEnrollmentsApi: 走真实 HTTP；请求失败时组件进入 error 分支，
   *     由 RetryCardComponent 兜底重试。
   */
  enrollmentsApiUrl: '/api/v1/courses/enrollments',
  useRealEnrollmentsApi: true,

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
