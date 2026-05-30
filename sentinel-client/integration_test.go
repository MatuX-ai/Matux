package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/mux"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"github.com/imatu/sentinel-client/api/handlers"
	"github.com/imatu/sentinel-client/api/middleware"
	"github.com/imatu/sentinel-client/config"
	"github.com/imatu/sentinel-client/internal/sentinel"
)

// MockSentinelClient 模拟Sentinel客户端用于测试
type MockSentinelClient struct {
	mock.Mock
}

func (m *MockSentinelClient) GenerateToken(orgID string, features []string, days int) (string, error) {
	args := m.Called(orgID, features, days)
	return args.String(0), args.Error(1)
}

func (m *MockSentinelClient) ValidateToken(token string) (*sentinel.LicenseToken, error) {
	args := m.Called(token)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*sentinel.LicenseToken), args.Error(1)
}

func (m *MockSentinelClient) RevokeToken(token string) error {
	args := m.Called(token)
	return args.Error(0)
}

func (m *MockSentinelClient) GetToken(token string) (*sentinel.LicenseToken, error) {
	args := m.Called(token)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*sentinel.LicenseToken), args.Error(1)
}

func (m *MockSentinelClient) Close() error {
	args := m.Called()
	return args.Error(0)
}

// TestGenerateLicense 测试生成许可证功能
func TestGenerateLicense(t *testing.T) {
	// 创建模拟客户端
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	// 设置期望调用
	expectedToken := "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJvcmctMTIzIiwib3JnX2lkIjoib3JnLTEyMyIsImZlYXR1cmVzIjpbImJ1bGtfdXNlcnMiLCJjdXN0b21fY291cnNlcyJdLCJleHAiOjE3NDU2Nzg5MDAsImlhdCI6MTY3MjU5ODkwMCwiaXNzIjoiaU1hdHVQcm9qZWN0IiwiYXVkIjoiZW50ZXJwcmlzZSJ9.signature"
	mockClient.On("GenerateToken", "org-123", []string{"bulk_users", "custom_courses"}, 30).Return(expectedToken, nil)

	// 创建请求
	reqBody := `{
		"org_id": "org-123",
		"features": ["bulk_users", "custom_courses"],
		"days": 30
	}`
	req, err := http.NewRequest("POST", "/api/licenses", bytes.NewBufferString(reqBody))
	assert.NoError(t, err)
	req.Header.Set("Content-Type", "application/json")

	// 创建响应记录器
	rr := httptest.NewRecorder()

	// 执行请求
	handler.GenerateLicense(rr, req)

	// 验证结果
	assert.Equal(t, http.StatusCreated, rr.Code)

	var response handlers.LicenseResponse
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedToken, response.Token)
	assert.Equal(t, "org-123", response.OrgID)
	assert.Equal(t, []string{"bulk_users", "custom_courses"}, response.Features)

	// 验证mock被正确调用
	mockClient.AssertExpectations(t)
}

// TestGenerateLicenseWithHeader 测试使用Header传递组织ID的情况
func TestGenerateLicenseWithHeader(t *testing.T) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	expectedToken := "test-token-123"
	mockClient.On("GenerateToken", "org-header", []string{"bulk_users", "custom_courses"}, 30).Return(expectedToken, nil)

	// 创建请求，使用Header传递org_id
	reqBody := `{
		"features": ["bulk_users", "custom_courses"],
		"days": 30
	}`
	req, err := http.NewRequest("POST", "/api/licenses", bytes.NewBufferString(reqBody))
	assert.NoError(t, err)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Org-ID", "org-header")

	rr := httptest.NewRecorder()
	handler.GenerateLicense(rr, req)

	assert.Equal(t, http.StatusCreated, rr.Code)
	
	var response handlers.LicenseResponse
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, expectedToken, response.Token)

	mockClient.AssertExpectations(t)
}

// TestGetLicense 测试查询许可证功能
func TestGetLicense(t *testing.T) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	// 设置期望
	token := "test-license-token"
	expectedLicense := &sentinel.LicenseToken{
		Token:     token,
		OrgID:     "org-123",
		Features:  []string{"feature1", "feature2"},
		IssuedAt:  time.Now(),
		ExpiresAt: time.Now().Add(24 * time.Hour),
		Status:    "active",
	}
	mockClient.On("GetToken", token).Return(expectedLicense, nil)

	// 创建请求
	req, err := http.NewRequest("GET", fmt.Sprintf("/api/licenses/%s", token), nil)
	assert.NoError(t, err)

	// 创建响应记录器
	rr := httptest.NewRecorder()

	// 使用mux设置路由变量
	r := mux.NewRouter()
	r.HandleFunc("/api/licenses/{token}", handler.GetLicense)
	r.ServeHTTP(rr, req.WithContext(req.Context()))

	// 验证结果
	assert.Equal(t, http.StatusOK, rr.Code)

	var response handlers.LicenseResponse
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, token, response.Token)
	assert.Equal(t, "org-123", response.OrgID)
	assert.Equal(t, "active", response.Status)

	mockClient.AssertExpectations(t)
}

// TestRevokeLicense 测试吊销许可证功能
func TestRevokeLicense(t *testing.T) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	token := "test-token-to-revoke"
	mockClient.On("RevokeToken", token).Return(nil)

	req, err := http.NewRequest("DELETE", fmt.Sprintf("/api/licenses/%s", token), nil)
	assert.NoError(t, err)

	rr := httptest.NewRecorder()
	handler.RevokeLicense(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)

	var response map[string]interface{}
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "License revoked successfully", response["message"])

	mockClient.AssertExpectations(t)
}

// TestValidateLicense 测试验证许可证功能
func TestValidateLicense(t *testing.T) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	token := "valid-license-token"
	expectedLicense := &sentinel.LicenseToken{
		Token:     token,
		OrgID:     "org-456",
		Features:  []string{"premium_feature"},
		IssuedAt:  time.Now(),
		ExpiresAt: time.Now().Add(24 * time.Hour),
		Status:    "active",
	}
	mockClient.On("ValidateToken", token).Return(expectedLicense, nil)

	reqBody := fmt.Sprintf(`{"token": "%s"}`, token)
	req, err := http.NewRequest("POST", "/api/licenses/validate", bytes.NewBufferString(reqBody))
	assert.NoError(t, err)
	req.Header.Set("Content-Type", "application/json")

	rr := httptest.NewRecorder()
	handler.ValidateLicense(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)

	var response map[string]interface{}
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.True(t, response["valid"].(bool))
	assert.Equal(t, "License is valid", response["message"])

	mockClient.AssertExpectations(t)
}

// TestHealthCheck 测试健康检查
func TestHealthCheck(t *testing.T) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	req, err := http.NewRequest("GET", "/health", nil)
	assert.NoError(t, err)

	rr := httptest.NewRecorder()
	handler.HealthCheck(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)

	var response map[string]interface{}
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "healthy", response["status"])
	assert.Equal(t, "sentinel-license-service", response["service"])
}

// TestErrorHandling 测试错误处理
func TestErrorHandling(t *testing.T) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)

	// 测试生成许可证错误
	mockClient.On("GenerateToken", "org-error", mock.Anything, mock.Anything).Return("", fmt.Errorf("database error"))

	reqBody := `{"org_id": "org-error", "features": ["test"], "days": 30}`
	req, err := http.NewRequest("POST", "/api/licenses", bytes.NewBufferString(reqBody))
	assert.NoError(t, err)
	req.Header.Set("Content-Type", "application/json")

	rr := httptest.NewRecorder()
	handler.GenerateLicense(rr, req)

	assert.Equal(t, http.StatusInternalServerError, rr.Code)

	var response handlers.ErrorResponse
	err = json.Unmarshal(rr.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "Failed to generate license: database error", response.Message)

	mockClient.AssertExpectations(t)
}

// TestMiddlewareIntegration 测试中间件集成
func TestMiddlewareIntegration(t *testing.T) {
	// 创建真实配置和客户端用于集成测试
	cfg := &config.SentinelConfig{
		License: config.LicenseConfig{
			Issuer:    "TestIssuer",
			Audience:  "TestAudience",
			SecretKey: "test-secret-key",
		},
	}
	
	client, err := sentinel.NewClient(cfg)
	if err != nil {
		t.Skip("Skipping integration test: Redis not available")
		return
	}
	defer client.Close()

	handler := handlers.NewLicenseHandler(client)
	authMiddleware := middleware.NewAuthMiddleware()

	// 测试CORS中间件
	testHandler := authMiddleware.CORS(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test"))
	})

	req, err := http.NewRequest("OPTIONS", "/test", nil)
	assert.NoError(t, err)

	rr := httptest.NewRecorder()
	testHandler(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
	assert.Equal(t, "*", rr.Header().Get("Access-Control-Allow-Origin"))

	// 测试日志中间件
	logHandler := authMiddleware.Logging(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	req, err = http.NewRequest("GET", "/test", nil)
	assert.NoError(t, err)

	rr = httptest.NewRecorder()
	logHandler(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
}

// BenchmarkGenerateLicense 基准测试许可证生成
func BenchmarkGenerateLicense(b *testing.B) {
	mockClient := new(MockSentinelClient)
	handler := handlers.NewLicenseHandler(mockClient)
	
	mockClient.On("GenerateToken", mock.Anything, mock.Anything, mock.Anything).Return("benchmark-token", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		reqBody := `{"org_id": "bench-org", "features": ["feature1"], "days": 30}`
		req, _ := http.NewRequest("POST", "/api/licenses", bytes.NewBufferString(reqBody))
		req.Header.Set("Content-Type", "application/json")
		
		rr := httptest.NewRecorder()
		handler.GenerateLicense(rr, req)
	}
}

// TestCompatibilityWithPythonSystem 测试与Python系统的兼容性
func TestCompatibilityWithPythonSystem(t *testing.T) {
	// 这个测试验证生成的JWT格式是否与Python系统兼容
	
	cfg := &config.SentinelConfig{
		License: config.LicenseConfig{
			Issuer:    "iMatuProject",  // 与Python配置保持一致
			Audience:  "enterprise",    // 与Python配置保持一致
			SecretKey: "test-secret-key-for-compatibility",
		},
	}
	
	client, err := sentinel.NewClient(cfg)
	assert.NoError(t, err)
	defer client.Close()

	// 生成许可证
	token, err := client.GenerateToken("compat-test-org", []string{"bulk_users"}, 30)
	assert.NoError(t, err)
	assert.NotEmpty(t, token)

	// 验证许可证
	license, err := client.ValidateToken(token)
	assert.NoError(t, err)
	assert.Equal(t, "compat-test-org", license.OrgID)
	assert.Equal(t, []string{"bulk_users"}, license.Features)
	assert.Equal(t, "active", license.Status)
}