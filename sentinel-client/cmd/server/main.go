package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/rs/cors"

	"github.com/imatu/sentinel-client/api/handlers"
	"github.com/imatu/sentinel-client/api/middleware"
	"github.com/imatu/sentinel-client/config"
	"github.com/imatu/sentinel-client/internal/sentinel"
)

func main() {
	// 加载配置
	cfg := config.LoadConfig()
	
	// 创建Sentinel客户端
	client, err := sentinel.NewClient(cfg)
	if err != nil {
		log.Fatalf("Failed to create Sentinel client: %v", err)
	}
	defer client.Close()

	// 创建处理器
	licenseHandler := handlers.NewLicenseHandler(client)
	authMiddleware := middleware.NewAuthMiddleware()

	// 创建路由器
	router := mux.NewRouter()

	// API路由组
	api := router.PathPrefix("/api").Subrouter()

	// 许可证相关路由
	licenses := api.PathPrefix("/licenses").Subrouter()

	// 应用中间件链
	middlewareChain := func(h http.HandlerFunc) http.HandlerFunc {
		return authMiddleware.Recovery(
			authMiddleware.Logging(
				authMiddleware.CORS(h),
			),
		)
	}

	// 注册路由
	licenses.HandleFunc("", middlewareChain(licenseHandler.GenerateLicense)).Methods("POST")     // 生成许可证
	licenses.HandleFunc("/{token}", middlewareChain(licenseHandler.GetLicense)).Methods("GET")   // 查询许可证
	licenses.HandleFunc("/{token}", middlewareChain(licenseHandler.RevokeLicense)).Methods("DELETE") // 吊销许可证
	licenses.HandleFunc("", middlewareChain(licenseHandler.ListLicenses)).Methods("GET")         // 列出许可证
	licenses.HandleFunc("/validate", middlewareChain(licenseHandler.ValidateLicense)).Methods("POST") // 验证许可证

	// 健康检查端点
	router.HandleFunc("/health", middlewareChain(licenseHandler.HealthCheck)).Methods("GET")
	router.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("pong"))
	}).Methods("GET")

	// 配置CORS
	corsHandler := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"*"},
	})

	// 创建HTTP服务器
	port := getEnv("PORT", "8080")
	addr := fmt.Sprintf(":%s", port)
	
	server := &http.Server{
		Addr:         addr,
		Handler:      corsHandler.Handler(router),
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// 启动服务器
	fmt.Printf("🚀 Starting Sentinel License Service on port %s\n", port)
	fmt.Printf("📋 API Documentation available at http://localhost:%s/api/docs\n", port)
	fmt.Printf("🏥 Health check endpoint: http://localhost:%s/health\n", port)

	// 在goroutine中启动服务器
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	fmt.Println("\n🛑 Shutting down server...")

	// 创建优雅关闭的上下文
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 关闭服务器
	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	fmt.Println("✅ Server exited gracefully")
}

// getEnv 获取环境变量，带默认值
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}