package handlers

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/sirupsen/logrus"

	"github.com/imatu/sentinel-client/internal/sentinel"
)

// LicenseHandler 许可证处理器
type LicenseHandler struct {
	client *sentinel.Client
	logger *logrus.Logger
}

// GenerateLicenseRequest 生成许可证请求
type GenerateLicenseRequest struct {
	OrgID    string   `json:"org_id" validate:"required"`
	Features []string `json:"features"`
	Days     int      `json:"days" validate:"min=1,max=3650"`
}

// LicenseResponse 许可证响应
type LicenseResponse struct {
	Token     string    `json:"token"`
	OrgID     string    `json:"org_id"`
	Features  []string  `json:"features"`
	IssuedAt  time.Time `json:"issued_at"`
	ExpiresAt time.Time `json:"expires_at"`
	Status    string    `json:"status"`
	Message   string    `json:"message,omitempty"`
}

// ValidationError 验证错误响应
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// ErrorResponse 错误响应
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
	Code    int    `json:"code"`
}

// NewLicenseHandler 创建新的许可证处理器
func NewLicenseHandler(client *sentinel.Client) *LicenseHandler {
	return &LicenseHandler{
		client: client,
		logger: logrus.New(),
	}
}

// GenerateLicense 生成许可证 - POST /api/licenses
func (h *LicenseHandler) GenerateLicense(w http.ResponseWriter, r *http.Request) {
	// 从Header获取组织ID（兼容原有代码要求）
	orgID := r.Header.Get("X-Org-ID")
	
	var req GenerateLicenseRequest
	
	// 如果Header中没有组织ID，则从请求体获取
	if orgID == "" {
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			h.sendError(w, "Invalid request body", http.StatusBadRequest)
			return
		}
		
		// 验证请求参数
		if err := h.validateGenerateRequest(&req); err != nil {
			h.sendValidationError(w, err)
			return
		}
		
		orgID = req.OrgID
	} else {
		// 从Header获取时，解析其他参数
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			// 如果解析失败，使用默认值
			req.Features = []string{"bulk_users", "custom_courses"}
			req.Days = 30
		} else {
			// 验证Features参数
			if len(req.Features) == 0 {
				req.Features = []string{"bulk_users", "custom_courses"}
			}
			if req.Days <= 0 {
				req.Days = 30
			}
		}
	}

	// 生成许可证令牌
	token, err := h.client.GenerateToken(orgID, req.Features, req.Days)
	if err != nil {
		h.logger.WithError(err).Error("Failed to generate license")
		h.sendError(w, "Failed to generate license: "+err.Error(), http.StatusInternalServerError)
		return
	}

	response := LicenseResponse{
		Token:     token,
		OrgID:     orgID,
		Features:  req.Features,
		IssuedAt:  time.Now(),
		ExpiresAt: time.Now().Add(time.Duration(req.Days) * 24 * time.Hour),
		Status:    "active",
		Message:   "License generated successfully",
	}

	h.sendJSON(w, response, http.StatusCreated)
	h.logger.WithFields(logrus.Fields{
		"org_id": orgID,
		"days":   req.Days,
		"token":  token[:20] + "...", // 只记录部分token用于追踪
	}).Info("License generated successfully")
}

// GetLicense 查询许可证 - GET /api/licenses/{token}
func (h *LicenseHandler) GetLicense(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	tokenString := vars["token"]
	
	if tokenString == "" {
		h.sendError(w, "Token parameter is required", http.StatusBadRequest)
		return
	}

	// 验证许可证
	license, err := h.client.GetToken(tokenString)
	if err != nil {
		h.logger.WithError(err).WithField("token", tokenString[:20]+"...").Warn("License validation failed")
		h.sendError(w, "Invalid or expired license: "+err.Error(), http.StatusUnauthorized)
		return
	}

	response := LicenseResponse{
		Token:     license.Token,
		OrgID:     license.OrgID,
		Features:  license.Features,
		IssuedAt:  license.IssuedAt,
		ExpiresAt: license.ExpiresAt,
		Status:    license.Status,
	}

	h.sendJSON(w, response, http.StatusOK)
	h.logger.WithFields(logrus.Fields{
		"org_id": license.OrgID,
		"status": license.Status,
	}).Info("License queried successfully")
}

// RevokeLicense 吊销许可证 - DELETE /api/licenses/{token}
func (h *LicenseHandler) RevokeLicense(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	tokenString := vars["token"]
	
	if tokenString == "" {
		h.sendError(w, "Token parameter is required", http.StatusBadRequest)
		return
	}

	// 吊销许可证
	if err := h.client.RevokeToken(tokenString); err != nil {
		h.logger.WithError(err).WithField("token", tokenString[:20]+"...").Error("Failed to revoke license")
		h.sendError(w, "Failed to revoke license: "+err.Error(), http.StatusInternalServerError)
		return
	}

	response := map[string]interface{}{
		"message": "License revoked successfully",
		"token":   tokenString[:20] + "...",
	}

	h.sendJSON(w, response, http.StatusOK)
	h.logger.WithField("token", tokenString[:20]+"...").Info("License revoked successfully")
}

// ListLicenses 列出许可证 - GET /api/licenses (可选实现)
func (h *LicenseHandler) ListLicenses(w http.ResponseWriter, r *http.Request) {
	// 这里可以实现列出所有许可证的功能
	// 当前版本简化处理
	response := map[string]interface{}{
		"message": "License listing not implemented in this version",
		"data":    []interface{}{},
	}

	h.sendJSON(w, response, http.StatusOK)
}

// ValidateLicense 验证许可证 - POST /api/licenses/validate (可选端点)
func (h *LicenseHandler) ValidateLicense(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Token string `json:"token" validate:"required"`
	}
	
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.sendError(w, "Invalid request body", http.StatusBadRequest)
		return
	}
	
	if req.Token == "" {
		h.sendError(w, "Token is required", http.StatusBadRequest)
		return
	}

	license, err := h.client.ValidateToken(req.Token)
	if err != nil {
		h.sendError(w, "Invalid license: "+err.Error(), http.StatusUnauthorized)
		return
	}

	response := map[string]interface{}{
		"valid":       true,
		"license":     license,
		"message":     "License is valid",
	}

	h.sendJSON(w, response, http.StatusOK)
}

// 辅助方法
func (h *LicenseHandler) sendJSON(w http.ResponseWriter, data interface{}, statusCode int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(data)
}

func (h *LicenseHandler) sendError(w http.ResponseWriter, message string, statusCode int) {
	response := ErrorResponse{
		Error:   http.StatusText(statusCode),
		Message: message,
		Code:    statusCode,
	}
	h.sendJSON(w, response, statusCode)
}

func (h *LicenseHandler) sendValidationError(w http.ResponseWriter, errors []ValidationError) {
	response := map[string]interface{}{
		"error":   "Validation failed",
		"message": "Request validation failed",
		"errors":  errors,
		"code":    http.StatusBadRequest,
	}
	h.sendJSON(w, response, http.StatusBadRequest)
}

func (h *LicenseHandler) validateGenerateRequest(req *GenerateLicenseRequest) []ValidationError {
	var errors []ValidationError
	
	if req.OrgID == "" {
		errors = append(errors, ValidationError{
			Field:   "org_id",
			Message: "Organization ID is required",
		})
	}
	
	if req.Days < 1 || req.Days > 3650 {
		errors = append(errors, ValidationError{
			Field:   "days",
			Message: "Days must be between 1 and 3650",
		})
	}
	
	return errors
}

// HealthCheck 健康检查端点
func (h *LicenseHandler) HealthCheck(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":    "healthy",
		"timestamp": time.Now().UTC(),
		"service":   "sentinel-license-service",
		"version":   "1.0.0",
	}
	
	h.sendJSON(w, response, http.StatusOK)
}