/**
 * 健康检查模块
 * @module backend/health
 */

const http = require('http');

// 【P3-4修复】统一魔法数字为具名常量
const HTTP_REQUEST_TIMEOUT = 5000;  // 通用 HTTP 请求超时 5 秒

// 【启动优化 P0-4】健康检查专用超时：1.5s
// 原因：后端 uvicorn listen 后，FastAPI 路由通常 < 200ms 就绪
// - 命中：< 200ms 返回成功
// - 未命中：1.5s 内必失败（连接拒绝 / 404），不会拖启动
// 原 5s 超时在 backoff 场景下最坏会被拖 15s（3 路径串行扫描）
const HEALTH_CHECK_TIMEOUT_MS = 1500;

/**
 * 使用 Node.js http 模块进行 HTTP 请求
 * @param {string} url 请求URL
 * @param {number} timeout 超时时间（毫秒）
 * @returns {Promise<{success: boolean, statusCode?: number, body?: string, error?: string}>}
 */
function httpGet(url, timeout = HTTP_REQUEST_TIMEOUT) {
  return new Promise((resolve) => {
    try {
      const urlObj = new URL(url);
      // 强制使用 IPv4 地址，避免 localhost 解析到 IPv6 (::1)
      let hostname = urlObj.hostname;
      if (hostname === 'localhost') {
        hostname = '127.0.0.1';
      }
      const options = {
        hostname: hostname,
        port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
        path: urlObj.pathname + urlObj.search,
        method: 'GET',
        timeout: timeout,
      };

      const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => {
          body += chunk;
        });
        res.on('end', () => {
          resolve({
            success: true,
            statusCode: res.statusCode,
            body: body,
          });
        });
      });

      req.on('error', (err) => {
        resolve({
          success: false,
          error: err.message,
        });
      });

      req.on('timeout', () => {
        req.destroy();
        resolve({
          success: false,
          error: '请求超时',
        });
      });

      req.end();
    } catch (err) {
      resolve({
        success: false,
        error: err.message,
      });
    }
  });
}

/**
 * 健康检查 - 使用 Node.js http 模块
 * 支持多种检查方式和更好的错误处理
 * 【启动优化 P0-4】单次超时 5s → 1.5s，减少失败路径扫描时间
 * @param {string} backendHost 后端主机
 * @param {number} backendPort 后端端口
 * @param {string[]} checkPaths 要检查的路径列表
 * @returns {Promise<{success: boolean, status?: string, version?: string, uptime?: number, error?: string}>}
 */
async function healthCheck(backendHost = 'localhost', backendPort = 8000, checkPaths = null) {
  const paths = checkPaths || ['/health', '/', '/docs'];

  for (const path of paths) {
    // 【启动优化 P0-4】使用专用短超时 HEALTH_CHECK_TIMEOUT_MS
    const url = `http://${backendHost}:${backendPort}${path}`;
    const result = await httpGet(url, HEALTH_CHECK_TIMEOUT_MS);

    if (result.success) {
      // 检查响应状态码（包括重定向）
      if (result.statusCode) {
        // 2xx 成功 或 3xx 重定向（后端可能返回重定向到健康端点）
        const isSuccessStatus = (result.statusCode >= 200 && result.statusCode < 400);
        if (isSuccessStatus) {
          // 尝试解析响应体
          try {
            if (result.body) {
              try {
                const body = JSON.parse(result.body);
                if (body && (body.status === 'ok' || body.status === 'healthy' || body.status === 'running')) {
                  return {
                    success: true,
                    status: 'ok',
                    version: body.python_version || body.version || '3.11',
                    uptime: body.uptime,
                  };
                }
                // 即使没有标准status字段，只要能连接就认为成功
                return { success: true, status: 'ok' };
              } catch {
                // 不是JSON响应，但能连接上就是成功
                return { success: true, status: 'ok' };
              }
            } else {
              // 没有响应体，但能连接上就是成功
              return { success: true, status: 'ok' };
            }
          } catch (err) {
            // 解析错误，但能连接上就是成功
            return { success: true, status: 'ok' };
          }
        }
      }
    }
    // 记录失败但继续尝试下一个URL
    console.log(`[HEALTH] 健康检查 ${url} 失败: ${result.error || 'HTTP ' + result.statusCode}`);
  }

  // 所有URL都失败
  return { success: false, error: '所有健康检查端点都无法访问' };
}

module.exports = {
  httpGet,
  healthCheck,
};
