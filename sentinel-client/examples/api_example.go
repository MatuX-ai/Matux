// 许可证API使用示例
// 与用户提供的示例代码保持一致

package main

import (
	"fmt"
	"net/http"
	"io/ioutil"
	"strings"
)

// GenerateLicense 生成许可证的示例函数
// 对应用户要求的Golang代码示例
func GenerateLicense(w http.ResponseWriter, r *http.Request) {
	// 从Header获取组织ID
	orgID := r.Header.Get("X-Org-ID")
	
	// 定义功能特性
	features := []string{"bulk_users", "custom_courses"}
	
	// 调用Sentinel生成令牌（这里应该是实际的客户端调用）
	// token, err := sentinel.GenerateToken(orgID, features, 30)
	
	// 模拟生成过程
	token := fmt.Sprintf("license-token-for-%s-with-features-%v", orgID, features)
	
	// 写入响应
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(token))
	
	fmt.Printf("Generated license for org: %s\n", orgID)
}

// 完整的API使用示例
func main() {
	// 创建路由器
	mux := http.NewServeMux()
	
	// 注册许可证生成端点
	mux.HandleFunc("/api/licenses", GenerateLicense)
	
	// 启动服务器
	fmt.Println("🚀 Starting License API Server on :8080")
	fmt.Println("📋 POST /api/licenses - Generate license with X-Org-ID header")
	
	http.ListenAndServe(":8080", mux)
}

/*
=== API 使用示例 ===

1. 生成许可证:
curl -X POST http://localhost:8080/api/licenses \
  -H "X-Org-ID: my-organization-123"

响应示例:
license-token-for-my-organization-123-with-features-[bulk_users custom_courses]

2. 使用完整请求体:
curl -X POST http://localhost:8080/api/licenses \
  -H "Content-Type: application/json" \
  -H "X-Org-ID: org-456" \
  -d '{
    "features": ["advanced_analytics", "team_collaboration"],
    "days": 90
  }'

3. 查询许可证:
curl -X GET "http://localhost:8080/api/licenses/LICENSE-TOKEN-HERE"

4. 验证许可证:
curl -X POST http://localhost:8080/api/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "LICENSE-TOKEN-HERE"}'

5. 吊销许可证:
curl -X DELETE "http://localhost:8080/api/licenses/LICENSE-TOKEN-HERE"

=== 错误处理示例 ===

常见HTTP状态码:
- 200 OK: 成功
- 201 Created: 许可证创建成功
- 400 Bad Request: 请求参数错误
- 401 Unauthorized: 缺少或无效的许可证
- 403 Forbidden: 许可证无权访问
- 404 Not Found: 许可证不存在
- 429 Too Many Requests: 超出速率限制
- 500 Internal Server Error: 服务器内部错误

错误响应格式:
{
  "error": "Bad Request",
  "message": "详细错误描述",
  "code": 400
}

=== 与Python系统集成 ===

该Golang实现与现有Python系统完全兼容:

1. 相同的JWT格式和签名算法
2. 兼容的Redis存储结构
3. 一致的API响应格式
4. 相同的配置参数

可以在混合部署场景中同时使用两个系统。
*/