package middleware

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/sirupsen/logrus"

	"github.com/imatu/sentinel-client/internal/sentinel"
)

// LicenseValidator 许可证验证中间件
type LicenseValidator struct {
	client *sentinel.Client
	logger *logrus.Logger
}

// LicenseInfo 许可证信息上下文键
type LicenseInfo struct {
	OrgID     string
	Token     string
	Features  []string
	ExpiresAt time.Time
	Status    string
}

// Context keys
type contextKey string
const LicenseInfoKey contextKey = "license_info"

// NewLicenseValidator 创建新的许可证验证器
func NewLicenseValidator(client *sentinel.Client) *LicenseValidator {
	return &LicenseValidator{
		client: client,
		logger: logrus.New(),
	}
}

// RequireLicense 要求有效的许可证
func (lv *LicenseValidator) RequireLicense(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 尝试从不同位置获取许可证
		licenseToken := lv.extractLicenseToken(r)
		
		if licenseToken == "" {
			lv.logger.Warn("Missing license token")
			http.Error(w, "License token required", http.StatusUnauthorized)
			return
		}

		// 验证许可证
		license, err := lv.client.ValidateToken(licenseToken)
		if err != nil {
			lv.logger.WithError(err).WithField("token", maskToken(licenseToken)).Warn("Invalid license token")
			http.Error(w, fmt.Sprintf("Invalid license: %v", err), http.StatusUnauthorized)
			return
		}

		// 检查许可证状态
		if license.Status != "active" {
			lv.logger.WithFields(logrus.Fields{
				"org_id": license.OrgID,
				"status": license.Status,
			}).Warn("License not active")
			http.Error(w, "License is not active", http.StatusForbidden)
			return
		}

		// 检查是否过期
		if time.Now().After(license.ExpiresAt) {
			lv.logger.WithFields(logrus.Fields{
				"org_id":     license.OrgID,
				"expires_at": license.ExpiresAt,
			}).Warn("License expired")
			http.Error(w, "License has expired", http.StatusForbidden)
			return
		}

		// 将许可证信息添加到请求上下文
		ctx := context.WithValue(r.Context(), LicenseInfoKey, LicenseInfo{
			OrgID:     license.OrgID,
			Token:     license.Token,
			Features:  license.Features,
			ExpiresAt: license.ExpiresAt,
			Status:    license.Status,
		})
		
		// 记录验证成功的日志
		lv.logger.WithFields(logrus.Fields{
			"org_id":   license.OrgID,
			"features": license.Features,
		}).Debug("License validation successful")

		// 继续处理请求
		next.ServeHTTP(w, r.WithContext(ctx))
	}
}

// RequireFeature 要求特定功能的许可证
func (lv *LicenseValidator) RequireFeature(feature string) func(http.HandlerFunc) http.HandlerFunc {
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			// 先进行基本许可证验证
			licenseInfo, ok := r.Context().Value(LicenseInfoKey).(LicenseInfo)
			if !ok {
				http.Error(w, "License validation required first", http.StatusInternalServerError)
				return
			}

			// 检查是否具有所需功能
			if !hasFeature(licenseInfo.Features, feature) {
				lv.logger.WithFields(logrus.Fields{
					"org_id":        licenseInfo.OrgID,
					"required_feat": feature,
					"available_feats": licenseInfo.Features,
				}).Warn("License missing required feature")
				http.Error(w, fmt.Sprintf("License does not include required feature: %s", feature), http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		}
	}
}

// RateLimit 基于许可证的速率限制
func (lv *LicenseValidator) RateLimit(maxRequests int, window time.Duration) func(http.HandlerFunc) http.HandlerFunc {
	// 简单的内存存储用于演示（生产环境应使用Redis）
	requestCounts := make(map[string][]time.Time)
	
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			licenseInfo, ok := r.Context().Value(LicenseInfoKey).(LicenseInfo)
			if !ok {
				next.ServeHTTP(w, r)
				return
			}

			orgKey := licenseInfo.OrgID
			now := time.Now()
			
			// 清理过期的请求记录
			validRequests := make([]time.Time, 0)
			for _, reqTime := range requestCounts[orgKey] {
				if now.Sub(reqTime) < window {
					validRequests = append(validRequests, reqTime)
				}
			}
			requestCounts[orgKey] = validRequests

			// 检查是否超出限制
			if len(requestCounts[orgKey]) >= maxRequests {
				lv.logger.WithFields(logrus.Fields{
					"org_id":       orgKey,
					"requests":     len(requestCounts[orgKey]),
					"max_requests": maxRequests,
				}).Warn("Rate limit exceeded")
				
				w.Header().Set("Retry-After", fmt.Sprintf("%.0f", window.Seconds()))
				http.Error(w, fmt.Sprintf("Rate limit exceeded. Maximum %d requests per %v", maxRequests, window), http.StatusTooManyRequests)
				return
			}

			// 记录本次请求
			requestCounts[orgKey] = append(requestCounts[orgKey], now)

			// 添加速率限制头信息
			remaining := maxRequests - len(requestCounts[orgKey])
			w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%d", maxRequests))
			w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%d", remaining))
			w.Header().Set("X-RateLimit-Reset", fmt.Sprintf("%d", now.Add(window).Unix()))

			next.ServeHTTP(w, r)
		}
	}
}

// AuditLogging 审计日志中间件
func (lv *LicenseValidator) AuditLogging(action string) func(http.HandlerFunc) http.HandlerFunc {
	return func(next http.HandlerFunc) http.HandlerFunc {
		return func(w http.ResponseWriter, r *http.Request) {
			licenseInfo, ok := r.Context().Value(LicenseInfoKey).(LicenseInfo)
			if !ok {
				next.ServeHTTP(w, r)
				return
			}

			// 记录审计日志
			lv.logger.WithFields(logrus.Fields{
				"action":     action,
				"org_id":     licenseInfo.OrgID,
				"ip":         getClientIP(r),
				"user_agent": r.UserAgent(),
				"path":       r.URL.Path,
				"method":     r.Method,
			}).Info("Audit log entry")

			next.ServeHTTP(w, r)
		}
	}
}

// extractLicenseToken 从请求中提取许可证令牌
func (lv *LicenseValidator) extractLicenseToken(r *http.Request) string {
	// 1. 从Authorization header (Bearer token)
	authHeader := r.Header.Get("Authorization")
	if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
		return strings.TrimPrefix(authHeader, "Bearer ")
	}

	// 2. 从自定义header
	if token := r.Header.Get("X-License-Token"); token != "" {
		return token
	}

	// 3. 从查询参数
	if token := r.URL.Query().Get("license_token"); token != "" {
		return token
	}

	// 4. 从表单数据
	if token := r.FormValue("license_token"); token != "" {
		return token
	}

	return ""
}

// 辅助函数
func hasFeature(features []string, requiredFeature string) bool {
	for _, feature := range features {
		if feature == requiredFeature {
			return true
		}
	}
	return false
}

func maskToken(token string) string {
	if len(token) <= 20 {
		return "***"
	}
	return token[:10] + "..." + token[len(token)-10:]
}

func getClientIP(r *http.Request) string {
	// 检查常见的代理头
	forwarded := r.Header.Get("X-Forwarded-For")
	if forwarded != "" {
		// X-Forwarded-For可能包含多个IP，取第一个
		ips := strings.Split(forwarded, ",")
		return strings.TrimSpace(ips[0])
	}
	
	// 检查其他代理头
	if realIP := r.Header.Get("X-Real-IP"); realIP != "" {
		return realIP
	}
	
	// 直接使用RemoteAddr
	return r.RemoteAddr
}