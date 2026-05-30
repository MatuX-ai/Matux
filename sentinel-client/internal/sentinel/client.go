package sentinel

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"strings"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/go-redis/redis/v8"
	"github.com/sirupsen/logrus"
	
	"github.com/imatu/sentinel-client/config"
)

// Client Sentinel客户端
type Client struct {
	config *config.SentinelConfig
	redis  *redis.Client
	logger *logrus.Logger
}

// LicenseClaims 许可证声明
type LicenseClaims struct {
	jwt.StandardClaims
	OrgID    string   `json:"org_id"`
	Features []string `json:"features"`
	Status   string   `json:"status"`
}

// LicenseToken 许可证令牌结构
type LicenseToken struct {
	Token     string    `json:"token"`
	OrgID     string    `json:"org_id"`
	Features  []string  `json:"features"`
	IssuedAt  time.Time `json:"issued_at"`
	ExpiresAt time.Time `json:"expires_at"`
	Status    string    `json:"status"`
}

// NewClient 创建新的Sentinel客户端
func NewClient(cfg *config.SentinelConfig) (*Client, error) {
	client := &Client{
		config: cfg,
		logger: logrus.New(),
	}

	// 初始化Redis连接
	if err := client.initRedis(); err != nil {
		return nil, fmt.Errorf("failed to initialize Redis: %w", err)
	}

	return client, nil
}

// initRedis 初始化Redis连接
func (c *Client) initRedis() error {
	c.redis = redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", c.config.Storage.Host, c.config.Storage.Port),
		Password: c.config.Storage.Password,
		DB:       c.config.Storage.DB,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := c.redis.Ping(ctx).Result()
	if err != nil {
		return fmt.Errorf("failed to connect to Redis: %w", err)
	}

	c.logger.Info("Successfully connected to Redis")
	return nil
}

// GenerateToken 生成许可证令牌
func (c *Client) GenerateToken(orgID string, features []string, daysValid int) (string, error) {
	// 生成唯一的许可证ID
	licenseID, err := c.generateLicenseID()
	if err != nil {
		return "", fmt.Errorf("failed to generate license ID: %w", err)
	}

	// 设置过期时间
	expirationTime := time.Now().Add(time.Duration(daysValid) * 24 * time.Hour)

	// 创建JWT声明
	claims := LicenseClaims{
		StandardClaims: jwt.StandardClaims{
			Id:        licenseID,
			Issuer:    c.config.License.Issuer,
			Audience:  c.config.License.Audience,
			ExpiresAt: expirationTime.Unix(),
			IssuedAt:  time.Now().Unix(),
			Subject:   orgID,
		},
		OrgID:    orgID,
		Features: features,
		Status:   "active",
	}

	// 创建token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)

	// 签名token
	tokenString, err := token.SignedString([]byte(c.config.License.SecretKey))
	if err != nil {
		return "", fmt.Errorf("failed to sign token: %w", err)
	}

	// 存储到Redis
	if err := c.storeTokenInRedis(licenseID, tokenString, expirationTime); err != nil {
		c.logger.WithError(err).Warn("Failed to store token in Redis")
	}

	// 记录日志
	c.logger.WithFields(logrus.Fields{
		"org_id":      orgID,
		"license_id":  licenseID,
		"expires_at":  expirationTime,
		"features":    features,
	}).Info("Generated new license token")

	return tokenString, nil
}

// ValidateToken 验证许可证令牌
func (c *Client) ValidateToken(tokenString string) (*LicenseToken, error) {
	// 解析token
	token, err := jwt.ParseWithClaims(tokenString, &LicenseClaims{}, func(token *jwt.Token) (interface{}, error) {
		return []byte(c.config.License.SecretKey), nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to parse token: %w", err)
	}

	// 验证token
	claims, ok := token.Claims.(*LicenseClaims)
	if !ok || !token.Valid {
		return nil, fmt.Errorf("invalid token")
	}

	// 检查Redis中的状态
	storedToken, err := c.getTokenFromRedis(claims.Id)
	if err != nil {
		c.logger.WithField("license_id", claims.Id).Warn("Token not found in Redis")
		// 即使Redis中找不到，也允许通过JWT验证的有效令牌
	}

	// 如果Redis中有存储且状态不是active，则拒绝
	if storedToken != "" && !strings.Contains(storedToken, `"status":"active"`) {
		return nil, fmt.Errorf("license is not active")
	}

	licenseToken := &LicenseToken{
		Token:     tokenString,
		OrgID:     claims.OrgID,
		Features:  claims.Features,
		IssuedAt:  time.Unix(claims.IssuedAt, 0),
		ExpiresAt: time.Unix(claims.ExpiresAt, 0),
		Status:    claims.Status,
	}

	return licenseToken, nil
}

// RevokeToken 吊销许可证令牌
func (c *Client) RevokeToken(tokenString string) error {
	// 解析token获取ID
	token, _, err := new(jwt.Parser).ParseUnverified(tokenString, &LicenseClaims{})
	if err != nil {
		return fmt.Errorf("failed to parse token: %w", err)
	}

	claims, ok := token.Claims.(*LicenseClaims)
	if !ok {
		return fmt.Errorf("invalid token claims")
	}

	// 从Redis删除
	err = c.deleteTokenFromRedis(claims.Id)
	if err != nil {
		c.logger.WithError(err).Warn("Failed to delete token from Redis")
	}

	// 更新状态为revoked
	revokedClaims := *claims
	revokedClaims.Status = "revoked"
	
	newToken := jwt.NewWithClaims(jwt.SigningMethodHS256, revokedClaims)
	revokedToken, err := newToken.SignedString([]byte(c.config.License.SecretKey))
	if err != nil {
		return fmt.Errorf("failed to create revoked token: %w", err)
	}

	// 存储吊销状态到Redis
	expirationTime := time.Now().Add(24 * time.Hour) // 保留24小时用于审计
	if err := c.storeRevokedToken(claims.Id, revokedToken, expirationTime); err != nil {
		c.logger.WithError(err).Warn("Failed to store revoked token")
	}

	c.logger.WithFields(logrus.Fields{
		"license_id": claims.Id,
		"org_id":     claims.OrgID,
	}).Info("License token revoked")

	return nil
}

// GetToken 查询许可证令牌信息
func (c *Client) GetToken(tokenString string) (*LicenseToken, error) {
	return c.ValidateToken(tokenString)
}

// generateLicenseID 生成唯一的许可证ID
func (c *Client) generateLicenseID() (string, error) {
	bytes := make([]byte, c.config.License.KeyLength)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	
	// 使用Base64编码并添加前缀
	encoded := base64.URLEncoding.EncodeToString(bytes)
	return fmt.Sprintf("%s-%s", c.config.License.Prefix, encoded[:16]), nil
}

// Redis存储相关方法
func (c *Client) storeTokenInRedis(licenseID, token string, expiration time.Time) error {
	ctx := context.Background()
	key := fmt.Sprintf("license:%s", licenseID)
	
	return c.redis.Set(ctx, key, token, time.Until(expiration)).Err()
}

func (c *Client) getTokenFromRedis(licenseID string) (string, error) {
	ctx := context.Background()
	key := fmt.Sprintf("license:%s", licenseID)
	
	return c.redis.Get(ctx, key).Result()
}

func (c *Client) deleteTokenFromRedis(licenseID string) error {
	ctx := context.Background()
	key := fmt.Sprintf("license:%s", licenseID)
	
	return c.redis.Del(ctx, key).Err()
}

func (c *Client) storeRevokedToken(licenseID, token string, expiration time.Time) error {
	ctx := context.Background()
	key := fmt.Sprintf("license:revoked:%s", licenseID)
	
	return c.redis.Set(ctx, key, token, time.Until(expiration)).Err()
}

// Close 关闭客户端连接
func (c *Client) Close() error {
	if c.redis != nil {
		return c.redis.Close()
	}
	return nil
}