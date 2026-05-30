package middleware

import (
	"net/http"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

// AuthMiddleware 认证中间件
type AuthMiddleware struct {
	logger *logrus.Logger
}

// NewAuthMiddleware 创建新的认证中间件
func NewAuthMiddleware() *AuthMiddleware {
	return &AuthMiddleware{
		logger: logrus.New(),
	}
}

// RequireAPIKey 要求API密钥的中间件
func (am *AuthMiddleware) RequireAPIKey(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 从Header获取API密钥
		apiKey := r.Header.Get("X-API-Key")
		authHeader := r.Header.Get("Authorization")
		
		// 如果Authorization header存在，提取Bearer token
		if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
			apiKey = strings.TrimPrefix(authHeader, "Bearer ")
		}
		
		// 验证API密钥（这里应该从配置或数据库获取）
		if apiKey == "" {
			am.logger.Warn("Missing API key")
			http.Error(w, "API key required", http.StatusUnauthorized)
			return
		}
		
		// 在生产环境中，这里应该验证API密钥的有效性
		// 例如查询数据库或调用认证服务
		
		// 继续处理请求
		next.ServeHTTP(w, r)
	}
}

// CORS 中间件
func (am *AuthMiddleware) CORS(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 设置CORS头
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key, X-Org-ID")
		
		// 处理预检请求
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		
		next.ServeHTTP(w, r)
	}
}

// Logging 记录请求日志的中间件
func (am *AuthMiddleware) Logging(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// 包装ResponseWriter以捕获状态码
		lrw := &loggingResponseWriter{ResponseWriter: w}
		
		// 处理请求
		next.ServeHTTP(lrw, r)
		
		// 记录日志
		duration := time.Since(start)
		am.logger.WithFields(logrus.Fields{
			"method":      r.Method,
			"url":         r.URL.Path,
			"status_code": lrw.statusCode,
			"duration_ms": duration.Milliseconds(),
			"user_agent":  r.UserAgent(),
			"remote_addr": r.RemoteAddr,
		}).Info("HTTP request processed")
	}
}

// loggingResponseWriter 包装ResponseWriter以捕获状态码
type loggingResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (lrw *loggingResponseWriter) WriteHeader(code int) {
	lrw.statusCode = code
	lrw.ResponseWriter.WriteHeader(code)
}

// Recovery 恐慌恢复中间件
func (am *AuthMiddleware) Recovery(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				am.logger.WithField("error", err).Error("Panic recovered")
				http.Error(w, "Internal server error", http.StatusInternalServerError)
			}
		}()
		
		next.ServeHTTP(w, r)
	}
}