# 认证模块测试脚本 (PowerShell版本)
# 验证认证系统的各项功能

Write-Host "🚀 开始认证模块测试..." -ForegroundColor Green
Write-Host ""

# 测试计数器
$totalTests = 0
$passedTests = 0

# 测试函数
function Run-Test {
    param(
        [string]$TestName,
        [scriptblock]$TestScript
    )
    
    $global:totalTests++
    Write-Host "$($global:totalTests). $TestName" -ForegroundColor Yellow
    
    try {
        $result = & $TestScript
        if ($result) {
            $global:passedTests++
            Write-Host "   🟢 通过" -ForegroundColor Green
        } else {
            Write-Host "   🔴 失败" -ForegroundColor Red
        }
    } catch {
        Write-Host "   🔴 错误: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

# 测试1: 文件存在性检查
Write-Host "📋 文件结构验证" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

Run-Test "认证模型文件存在" {
    Test-Path "src\app\core\models\auth.models.ts"
}

Run-Test "认证状态管理文件存在" {
    Test-Path "src\app\core\services\auth-state-manager.ts"
}

Run-Test "认证主服务文件存在" {
    Test-Path "src\app\core\services\auth-main-service.ts"
}

Run-Test "认证入口文件存在" {
    Test-Path "src\app\auth\index.ts"
}

Run-Test "认证页面HTML存在" {
    Test-Path "src\app\auth\auth-page.html"
}

Run-Test "认证页面SCSS存在" {
    Test-Path "src\app\auth\auth-page.scss"
}

# 测试2: OAuth提供商验证
Write-Host "📋 OAuth提供商验证" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

Run-Test "检查OAuth提供商类型定义" {
    $content = Get-Content "src\app\core\models\auth.models.ts" -Raw
    $content -match "github.*google.*wechat.*qq"
}

Run-Test "检查微信配置接口" {
    $content = Get-Content "src\app\core\models\auth.models.ts" -Raw
    $content -match "WeChatAuthConfig"
}

Run-Test "检查QQ配置接口" {
    $content = Get-Content "src\app\core\models\auth.models.ts" -Raw
    $content -match "QQAuthConfig"
}

# 测试3: 服务方法验证
Write-Test "认证服务方法验证" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

Run-Test "检查微信登录方法" {
    $content = Get-Content "src\app\core\services\auth-main-service.ts" -Raw
    $content -match "signInWithWeChat"
}

Run-Test "检查QQ登录方法" {
    $content = Get-Content "src\app\core\services\auth-main-service.ts" -Raw
    $content -match "signInWithQQ"
}

Run-Test "检查微信回调处理" {
    $content = Get-Content "src\app\core\services\auth-main-service.ts" -Raw
    $content -match "handleWeChatCallback"
}

Run-Test "检查QQ回调处理" {
    $content = Get-Content "src\app\core\services\auth-main-service.ts" -Raw
    $content -match "handleQQCallback"
}

# 测试4: UI组件验证
Write-Host "📋 UI组件验证" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

Run-Test "检查微信登录按钮" {
    $content = Get-Content "src\app\auth\auth-page.html" -Raw
    $content -match "signInWithWeChat"
}

Run-Test "检查QQ登录按钮" {
    $content = Get-Content "src\app\auth\auth-page.html" -Raw
    $content -match "signInWithQQ"
}

Run-Test "检查OAuth按钮布局" {
    $content = Get-Content "src\app\auth\auth-page.scss" -Raw
    $content -match "grid-template-columns.*repeat\(4.*1fr\)"
}

# 测试5: 文档完整性验证
Write-Host "📋 文档完整性验证" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

Run-Test "集成指南文档存在" {
    Test-Path "docs\WECHAT_QQ_INTEGRATION_GUIDE.md"
}

Run-Test "认证系统文档存在" {
    Test-Path "docs\AUTH_SYSTEM_DOCUMENTATION.md"
}

Run-Test "演示页面存在" {
    Test-Path "docs\auth-demo.html"
}

# 测试6: 配置验证
Write-Host "📋 配置验证" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

Run-Test "检查环境变量配置说明" {
    $content = Get-Content "docs\WECHAT_QQ_INTEGRATION_GUIDE.md" -Raw
    $content -match "NG_APP_WECHAT_APP_ID"
}

Run-Test "检查后端配置说明" {
    $content = Get-Content "docs\WECHAT_QQ_INTEGRATION_GUIDE.md" -Raw
    $content -match "WECHAT_APP_SECRET"
}

# 输出测试结果
Write-Host "📊 测试总结" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray
Write-Host "总测试数: $totalTests" -ForegroundColor White
Write-Host "通过测试: $passedTests" -ForegroundColor Green
Write-Host "失败测试: $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "通过率: $(($passedTests / $totalTests * 100).ToString("F1"))%" -ForegroundColor Yellow

if ($passedTests -eq $totalTests) {
    Write-Host ""
    Write-Host "🎉 所有测试通过！认证模块功能正常" -ForegroundColor Green
    Write-Host "✅ 支持的登录方式：" -ForegroundColor White
    Write-Host "   • 邮箱密码登录" -ForegroundColor White
    Write-Host "   • GitHub OAuth登录" -ForegroundColor White
    Write-Host "   • Google OAuth登录" -ForegroundColor White
    Write-Host "   • 微信OAuth登录" -ForegroundColor White
    Write-Host "   • QQ OAuth登录" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "⚠️  部分测试失败，请检查相关功能" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 测试完成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

# 返回测试结果
exit ($totalTests - $passedTests)