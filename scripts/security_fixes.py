#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全问题修复脚本
Security Issues Fix Script
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityFixer:
    """安全问题修复器"""
    
    def __init__(self):
        self.fixes_applied = []
        self.fixes_failed = []
    
    def apply_all_fixes(self) -> Dict[str, Any]:
        """应用所有安全修复"""
        logger.info("开始应用安全修复...")
        
        # 1. 修复数据库SSL配置
        self.fix_database_ssl()
        
        # 2. 修复调试模式配置
        self.fix_debug_mode()
        
        # 3. 添加HTTPS配置检查
        self.add_https_check()
        
        # 4. 添加安全日志记录
        self.setup_security_logging()
        
        # 5. 添加自定义错误页面
        self.create_error_pages()
        
        return {
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "timestamp": datetime.now().isoformat()
        }
    
    def fix_database_ssl(self):
        """修复数据库SSL配置"""
        try:
            # 检查环境配置文件
            env_files = ['.env', '.env.production', 'backend/.env']
            
            for env_file in env_files:
                if os.path.exists(env_file):
                    with open(env_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 添加SSL配置
                    if 'DATABASE_URL' in content and 'sslmode=' not in content:
                        lines = content.split('\n')
                        new_lines = []
                        
                        for line in lines:
                            if line.startswith('DATABASE_URL='):
                                # 在URL末尾添加SSL模式
                                if '?' in line:
                                    line = line.rstrip() + '&sslmode=require'
                                else:
                                    line = line.rstrip() + '?sslmode=require'
                            new_lines.append(line)
                        
                        with open(env_file, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(new_lines))
                        
                        self.fixes_applied.append({
                            "issue": "数据库SSL配置",
                            "fix": "在数据库URL中添加sslmode=require",
                            "file": env_file
                        })
                        logger.info(f"已修复数据库SSL配置: {env_file}")
                        return
            
            # 如果没找到环境文件，创建示例配置
            self.create_ssl_example_config()
            
        except Exception as e:
            self.fixes_failed.append({
                "issue": "数据库SSL配置",
                "error": str(e)
            })
            logger.error(f"修复数据库SSL配置失败: {e}")
    
    def create_ssl_example_config(self):
        """创建SSL配置示例"""
        example_config = """
# 数据库SSL配置示例
# PostgreSQL with SSL
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require

# MySQL with SSL  
DATABASE_URL=mysql://user:password@host:port/database?ssl-mode=REQUIRED
"""
        
        with open('DATABASE_SSL_CONFIG_EXAMPLE.txt', 'w', encoding='utf-8') as f:
            f.write(example_config)
        
        self.fixes_applied.append({
            "issue": "数据库SSL配置",
            "fix": "创建SSL配置示例文件",
            "file": "DATABASE_SSL_CONFIG_EXAMPLE.txt"
        })
    
    def fix_debug_mode(self):
        """修复调试模式配置"""
        try:
            # 检查后端配置文件
            config_files = [
                'backend/config/settings.py',
                'backend/main.py'
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 修改调试模式设置
                    if 'DEBUG = True' in content:
                        content = content.replace('DEBUG = True', 'DEBUG = False')
                        
                        with open(config_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        self.fixes_applied.append({
                            "issue": "调试模式配置",
                            "fix": "将DEBUG设置为False",
                            "file": config_file
                        })
                        logger.info(f"已修复调试模式配置: {config_file}")
                        return
            
            # 创建生产环境配置示例
            self.create_production_config_example()
            
        except Exception as e:
            self.fixes_failed.append({
                "issue": "调试模式配置",
                "error": str(e)
            })
            logger.error(f"修复调试模式配置失败: {e}")
    
    def create_production_config_example(self):
        """创建生产环境配置示例"""
        prod_config = """
# 生产环境配置示例
import os

# 安全配置
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///production.db'

# 安全头配置
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
"""
        
        with open('PRODUCTION_SECURITY_CONFIG.py', 'w', encoding='utf-8') as f:
            f.write(prod_config)
        
        self.fixes_applied.append({
            "issue": "调试模式配置",
            "fix": "创建生产环境安全配置示例",
            "file": "PRODUCTION_SECURITY_CONFIG.py"
        })
    
    def add_https_check(self):
        """添加HTTPS配置检查"""
        try:
            # 检查Nginx配置
            nginx_conf = 'nginx/nginx.conf'
            if os.path.exists(nginx_conf):
                with open(nginx_conf, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 添加HTTPS重定向
                https_redirect = """
# HTTPS重定向配置
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS配置
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
                
                with open('HTTPS_NGINX_CONFIG_EXAMPLE.conf', 'w', encoding='utf-8') as f:
                    f.write(https_redirect)
                
                self.fixes_applied.append({
                    "issue": "HTTPS配置",
                    "fix": "创建HTTPS Nginx配置示例",
                    "file": "HTTPS_NGINX_CONFIG_EXAMPLE.conf"
                })
                logger.info("已创建HTTPS配置示例")
            
        except Exception as e:
            self.fixes_failed.append({
                "issue": "HTTPS配置",
                "error": str(e)
            })
            logger.error(f"添加HTTPS配置检查失败: {e}")
    
    def setup_security_logging(self):
        """设置安全日志记录"""
        try:
            # 创建安全日志配置
            security_logging_config = """
# 安全日志配置
import logging
import logging.handlers
from datetime import datetime

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # 创建安全日志处理器
        handler = logging.handlers.RotatingFileHandler(
            'logs/security.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_security_event(self, event_type: str, user_id: str = None, 
                          ip_address: str = None, details: dict = None):
        \"\"\"记录安全事件\"\"\"
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        self.logger.info(json.dumps(log_data))

# 常见安全事件类型
SECURITY_EVENTS = {
    'LOGIN_ATTEMPT': '用户登录尝试',
    'LOGIN_SUCCESS': '用户登录成功',
    'LOGIN_FAILED': '用户登录失败',
    'UNAUTHORIZED_ACCESS': '未授权访问尝试',
    'SQL_INJECTION_ATTEMPT': 'SQL注入尝试',
    'XSS_ATTEMPT': 'XSS攻击尝试',
    'CSRF_ATTEMPT': 'CSRF攻击尝试',
    'BRUTE_FORCE_ATTEMPT': '暴力破解尝试',
    'DATA_EXFILTRATION': '数据泄露尝试',
    'PRIVILEGE_ESCALATION': '权限提升尝试'
}
"""
            
            # 确保logs目录存在
            os.makedirs('logs', exist_ok=True)
            
            with open('SECURITY_LOGGING_CONFIG.py', 'w', encoding='utf-8') as f:
                f.write(security_logging_config)
            
            self.fixes_applied.append({
                "issue": "安全日志记录",
                "fix": "创建安全日志配置文件",
                "file": "SECURITY_LOGGING_CONFIG.py"
            })
            logger.info("已创建安全日志配置")
            
        except Exception as e:
            self.fixes_failed.append({
                "issue": "安全日志记录",
                "error": str(e)
            })
            logger.error(f"设置安全日志记录失败: {e}")
    
    def create_error_pages(self):
        """创建自定义错误页面"""
        try:
            # 创建错误页面目录
            error_pages_dir = 'src/assets/error-pages'
            os.makedirs(error_pages_dir, exist_ok=True)
            
            # 404错误页面
            error_404 = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面未找到 - 404</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }
        .error-container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
        }
        .error-code {
            font-size: 72px;
            color: #e74c3c;
            margin: 0;
        }
        .error-message {
            font-size: 24px;
            color: #333;
            margin: 20px 0;
        }
        .error-description {
            color: #666;
            margin: 20px 0;
        }
        .back-button {
            background-color: #3498db;
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1 class="error-code">404</h1>
        <h2 class="error-message">页面未找到</h2>
        <p class="error-description">抱歉，您访问的页面不存在或已被移除。</p>
        <a href="/" class="back-button">返回首页</a>
    </div>
</body>
</html>
"""
            
            # 500错误页面
            error_500 = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>服务器错误 - 500</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background-color: #f5f5f5;
        }
        .error-container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
        }
        .error-code {
            font-size: 72px;
            color: #e74c3c;
            margin: 0;
        }
        .error-message {
            font-size: 24px;
            color: #333;
            margin: 20px 0;
        }
        .error-description {
            color: #666;
            margin: 20px 0;
        }
        .contact-info {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1 class="error-code">500</h1>
        <h2 class="error-message">服务器内部错误</h2>
        <p class="error-description">抱歉，服务器遇到了意外情况，无法完成您的请求。</p>
        <div class="contact-info">
            <strong>技术支持:</strong><br>
            请稍后重试，如果问题持续存在，请联系系统管理员。
        </div>
    </div>
</body>
</html>
"""
            
            # 写入错误页面文件
            with open(os.path.join(error_pages_dir, '404.html'), 'w', encoding='utf-8') as f:
                f.write(error_404)
            
            with open(os.path.join(error_pages_dir, '500.html'), 'w', encoding='utf-8') as f:
                f.write(error_500)
            
            self.fixes_applied.append({
                "issue": "自定义错误页面",
                "fix": "创建404和500错误页面",
                "files": [
                    os.path.join(error_pages_dir, '404.html'),
                    os.path.join(error_pages_dir, '500.html')
                ]
            })
            logger.info("已创建自定义错误页面")
            
        except Exception as e:
            self.fixes_failed.append({
                "issue": "自定义错误页面",
                "error": str(e)
            })
            logger.error(f"创建自定义错误页面失败: {e}")

def main():
    """主函数"""
    fixer = SecurityFixer()
    results = fixer.apply_all_fixes()
    
    # 保存修复结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_filename = f"security_fixes_results_{timestamp}.json"
    
    with open(results_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"安全修复结果已保存到: {results_filename}")
    
    # 打印摘要
    print("\n" + "="*50)
    print("安全修复摘要")
    print("="*50)
    print(f"成功应用的修复: {len(results['fixes_applied'])}")
    print(f"失败的修复: {len(results['fixes_failed'])}")
    
    if results['fixes_applied']:
        print("\n已应用的修复:")
        for fix in results['fixes_applied']:
            print(f"  ✓ {fix['issue']}: {fix.get('fix', '')}")
    
    if results['fixes_failed']:
        print("\n失败的修复:")
        for fix in results['fixes_failed']:
            print(f"  ✗ {fix['issue']}: {fix['error']}")

if __name__ == "__main__":
    main()