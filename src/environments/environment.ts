export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000',
  openMtSciEdApiUrl: 'http://localhost:3000/api/v1', // OpenMTSciEd API

  /** HTTP 请求超时时间（毫秒）- 开发环境下较短，便于 Mock 降级快速生效 */
  httpTimeout: 5000,

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
