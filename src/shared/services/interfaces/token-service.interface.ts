/**
 * Token 服务接口定义
 * 框架无关的 Token 管理抽象
 */

export interface ITokenService {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;
  isTokenExpired(token?: string): boolean;
  decodeToken(token: string): Record<string, unknown> | null;
  onTokenRefresh(callback: (token: string) => void): void;
}
