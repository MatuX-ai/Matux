
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
        """记录安全事件"""
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
