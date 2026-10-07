export const environment = {
  production: true,
  apiUrl: 'https://api.imatuproject.com',
  wsUrl: 'wss://api.imatuproject.com',

  /** 【P4-A】选课记录相关 API 配置 */
  enrollmentsApiUrl: '/api/v1/student/enrollments',
  useRealEnrollmentsApi: true,

  /** OAuth 应用凭证 — CI/CD 注入实际值 */
  oauth: {
    github: {
      clientId: process.env['OAUTH_GITHUB_CLIENT_ID'] ?? '',
    },
    google: {
      clientId: process.env['OAUTH_GOOGLE_CLIENT_ID'] ?? '',
    },
    wechat: {
      appId: process.env['OAUTH_WECHAT_APP_ID'] ?? '',
    },
    qq: {
      appId: process.env['OAUTH_QQ_APP_ID'] ?? '',
    },
  } as const,
};
