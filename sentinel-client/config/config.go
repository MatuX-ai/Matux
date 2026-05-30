package config

import (
	"os"
	"strconv"
)

// RedisConfig Redis配置
type RedisConfig struct {
	Host     string `yaml:"host"`
	Port     int    `yaml:"port"`
	DB       int    `yaml:"db"`
	Password string `yaml:"password"`
	SSL      bool   `yaml:"ssl"`
}

// LicenseConfig 许可证配置
type LicenseConfig struct {
	Issuer           string `yaml:"issuer"`
	Audience         string `yaml:"audience"`
	Algorithm        string `yaml:"algorithm"`
	ExpirationHours  int    `yaml:"expiration_hours"`
	KeyLength        int    `yaml:"key_length"`
	Prefix           string `yaml:"prefix"`
	SecretKey        string `yaml:"secret_key"`
}

// CacheConfig 缓存配置
type CacheConfig struct {
	TTLSeconds       int `yaml:"ttl_seconds"`
	CleanupInterval  int `yaml:"cleanup_interval"`
}

// SentinelConfig Sentinel主配置
type SentinelConfig struct {
	Storage RedisConfig   `yaml:"storage"`
	License LicenseConfig `yaml:"license"`
	Cache   CacheConfig   `yaml:"cache"`
}

// LoadConfig 从环境变量加载配置
func LoadConfig() *SentinelConfig {
	config := &SentinelConfig{
		Storage: RedisConfig{
			Host:     getEnv("REDIS_HOST", "localhost"),
			Port:     getIntEnv("REDIS_PORT", 6379),
			DB:       getIntEnv("REDIS_DB", 1),
			Password: os.Getenv("REDIS_PASSWORD"),
			SSL:      getBoolEnv("REDIS_SSL", false),
		},
		License: LicenseConfig{
			Issuer:          getEnv("LICENSE_ISSUER", "iMatuProject"),
			Audience:        getEnv("LICENSE_AUDIENCE", "enterprise"),
			Algorithm:       getEnv("LICENSE_ALGORITHM", "HS256"),
			ExpirationHours: getIntEnv("LICENSE_EXPIRATION_HOURS", 24),
			KeyLength:       getIntEnv("LICENSE_KEY_LENGTH", 32),
			Prefix:          getEnv("LICENSE_PREFIX", "LICENSE"),
			SecretKey:       getEnv("SECRET_KEY", "your-secret-key-here"),
		},
		Cache: CacheConfig{
			TTLSeconds:      getIntEnv("CACHE_TTL_SECONDS", 3600),
			CleanupInterval: getIntEnv("CACHE_CLEANUP_INTERVAL", 300),
		},
	}
	
	return config
}

// 辅助函数
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getIntEnv(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getBoolEnv(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}