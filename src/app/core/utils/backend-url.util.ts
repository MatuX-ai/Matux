/**
 * 后端地址解析工具
 *
 * 背景（【P0-C 修复】）：
 * Electron 桌面端通过自定义协议加载 SPA，`window.location.origin` 是
 * `app://.`（打包版）或 `file://`（直接开 dist）。这意味着：
 *  - HTTP API 可以走相对路径，由 electron/main.js 的 protocol handler
 *    把 `app://./api/...` 代理到 `http://localhost:8000/api/...`；
 *  - WebSocket **不能**走该代理，`new WebSocket('ws://app://./ws/...')`
 *    会被浏览器解析成 host=`app`，直接 ERR_NAME_NOT_RESOLVED。
 *
 * 因此桌面端必须把「页面 origin」替换成真实后端地址（默认 localhost:8000，
 * 与 electron/main.js 的 BACKEND_PORT 默认值一致），并允许宿主注入覆盖。
 */

/** Electron 主进程注入的覆盖入口（可选） */
declare global {
  interface Window {
    __IMATU_BACKEND_URL__?: string;
  }
}

const DEFAULT_BACKEND_HOST = 'localhost';
const DEFAULT_BACKEND_PORT = 8000;

/** origin 是否为桌面端本地协议（app:// / file://） */
export function isDesktopOrigin(origin: string): boolean {
  return origin.startsWith('app://') || origin.startsWith('file://');
}

/**
 * 解析真实后端 HTTP origin。
 * 非桌面端原样返回（开发用 Angular 代理，生产用同源反向代理）。
 */
export function resolveBackendOrigin(origin: string = window.location.origin): string {
  if (!isDesktopOrigin(origin)) {
    return origin;
  }

  const injected = window.__IMATU_BACKEND_URL__;
  if (injected) {
    return injected.replace(/\/+$/, '');
  }

  return `http://${DEFAULT_BACKEND_HOST}:${DEFAULT_BACKEND_PORT}`;
}

/** 解析 WebSocket 基址（http → ws / https → wss） */
export function resolveBackendWsBase(origin: string = window.location.origin): string {
  return resolveBackendOrigin(origin).replace(/^http/, 'ws');
}
