
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
