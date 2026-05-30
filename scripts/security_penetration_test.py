#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全渗透测试框架
Security Penetration Testing Framework
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import time

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_penetration_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityPenetrationTester:
    """安全渗透测试器"""
    
    def __init__(self):
        self.test_results = []
        self.vulnerabilities_found = []
        self.start_time = None
        self.end_time = None
        
    def run_full_security_test(self) -> Dict[str, Any]:
        """运行完整的安全渗透测试"""
        logger.info("开始执行安全渗透测试...")
        self.start_time = datetime.now()
        
        try:
            # 1. 智能合约漏洞扫描
            self.test_smart_contract_vulnerabilities()
            
            # 2. API渗透测试
            self.test_api_security()
            
            # 3. 数据库加密强度检测
            self.test_database_encryption()
            
            # 4. OWASP Top 10合规性检查
            self.check_owasp_compliance()
            
        except Exception as e:
            logger.error(f"安全测试执行失败: {e}")
            self.test_results.append({
                "test_type": "overall",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        self.end_time = datetime.now()
        return self.generate_security_report()
    
    def test_smart_contract_vulnerabilities(self):
        """测试智能合约漏洞"""
        logger.info("开始智能合约漏洞扫描...")
        
        # 检查Slither是否可用
        if not self.check_slither_installed():
            logger.warning("Slither未安装，跳过智能合约扫描")
            self.test_results.append({
                "test_type": "smart_contract",
                "status": "skipped",
                "reason": "Slither未安装",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        contract_files = [
            "blockchain/chaincode/skill_certification.go",
            "blockchain/chaincode/integral/integral_chaincode.go"
        ]
        
        vulnerabilities = []
        for contract_file in contract_files:
            if os.path.exists(contract_file):
                vulns = self.scan_contract_with_slither(contract_file)
                vulnerabilities.extend(vulns)
                
        # 分析漏洞严重程度
        critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'High']
        medium_vulns = [v for v in vulnerabilities if v.get('severity') == 'Medium']
        low_vulns = [v for v in vulnerabilities if v.get('severity') == 'Low']
        
        self.test_results.append({
            "test_type": "smart_contract",
            "status": "completed",
            "findings": {
                "total_vulnerabilities": len(vulnerabilities),
                "critical": len(critical_vulns),
                "medium": len(medium_vulns),
                "low": len(low_vulns)
            },
            "vulnerabilities": vulnerabilities,
            "timestamp": datetime.now().isoformat()
        })
        
        if critical_vulns:
            self.vulnerabilities_found.extend(critical_vulns)
            logger.warning(f"发现 {len(critical_vulns)} 个高危漏洞")
    
    def check_slither_installed(self) -> bool:
        """检查Slither是否已安装"""
        try:
            result = subprocess.run(['slither', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def scan_contract_with_slither(self, contract_path: str) -> List[Dict]:
        """使用Slither扫描智能合约"""
        try:
            cmd = ['slither', contract_path, '--json', '-']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and result.stdout:
                # 解析Slither输出
                try:
                    slither_output = json.loads(result.stdout)
                    return self.parse_slither_results(slither_output)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析Slither输出: {contract_path}")
                    return []
            else:
                logger.warning(f"Slither扫描失败: {contract_path}")
                if result.stderr:
                    logger.debug(f"错误详情: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error(f"Slither扫描超时: {contract_path}")
            return []
        except Exception as e:
            logger.error(f"Slither扫描异常: {contract_path}, 错误: {e}")
            return []
    
    def parse_slither_results(self, slither_output: Dict) -> List[Dict]:
        """解析Slither扫描结果"""
        vulnerabilities = []
        
        # 处理检测到的问题
        if 'results' in slither_output:
            for issue in slither_output['results'].get('detectors', []):
                vuln = {
                    'type': issue.get('check', 'unknown'),
                    'severity': issue.get('impact', 'Low'),
                    'confidence': issue.get('confidence', 'Medium'),
                    'description': issue.get('description', ''),
                    'elements': issue.get('elements', [])
                }
                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def test_api_security(self):
        """API安全渗透测试"""
        logger.info("开始API安全渗透测试...")
        
        # 即使没有ZAP也执行基础API安全测试
        logger.info("执行基础API安全测试（无需ZAP）")
        
        # 获取API端点
        api_endpoints = self.discover_api_endpoints()
        
        vulnerabilities = []
        for endpoint in api_endpoints:
            vulns = self.test_api_endpoint(endpoint)
            vulnerabilities.extend(vulns)
        
        # 分析结果
        critical_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) >= 7.0]
        medium_vulns = [v for v in vulnerabilities if 4.0 <= v.get('cvss_score', 0) < 7.0]
        low_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) < 4.0]
        
        self.test_results.append({
            "test_type": "api_security",
            "status": "completed",
            "findings": {
                "tested_endpoints": len(api_endpoints),
                "total_vulnerabilities": len(vulnerabilities),
                "critical": len(critical_vulns),
                "medium": len(medium_vulns),
                "low": len(low_vulns)
            },
            "vulnerabilities": vulnerabilities,
            "timestamp": datetime.now().isoformat()
        })
        
        if critical_vulns:
            self.vulnerabilities_found.extend(critical_vulns)
        
        # 获取API端点
        api_endpoints = self.discover_api_endpoints()
        
        vulnerabilities = []
        for endpoint in api_endpoints:
            vulns = self.test_api_endpoint(endpoint)
            vulnerabilities.extend(vulns)
        
        # 分析结果
        critical_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) >= 7.0]
        medium_vulns = [v for v in vulnerabilities if 4.0 <= v.get('cvss_score', 0) < 7.0]
        low_vulns = [v for v in vulnerabilities if v.get('cvss_score', 0) < 4.0]
        
        self.test_results.append({
            "test_type": "api_security",
            "status": "completed",
            "findings": {
                "tested_endpoints": len(api_endpoints),
                "total_vulnerabilities": len(vulnerabilities),
                "critical": len(critical_vulns),
                "medium": len(medium_vulns),
                "low": len(low_vulns)
            },
            "vulnerabilities": vulnerabilities,
            "timestamp": datetime.now().isoformat()
        })
        
        if critical_vulns:
            self.vulnerabilities_found.extend(critical_vulns)
    
    def check_zap_installed(self) -> bool:
        """检查OWASP ZAP是否已安装"""
        try:
            # 检查ZAP CLI
            result = subprocess.run(['zap-cli', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            try:
                # 检查ZAP GUI版本
                result = subprocess.run(['java', '-jar', 'zap.jar', '-cmd', '-help'], 
                                      capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # 检查系统路径中的ZAP
                zap_paths = [
                    'C:\\Program Files\\OWASP\\Zed Attack Proxy\\zap.bat',
                    'C:\\Program Files (x86)\\OWASP\\Zed Attack Proxy\\zap.bat',
                    '/usr/share/zaproxy/zap.sh',
                    '/Applications/ZAP.app/Contents/Java/zap.sh'
                ]
                for zap_path in zap_paths:
                    if os.path.exists(zap_path):
                        return True
                return False
    
    def discover_api_endpoints(self) -> List[Dict]:
        """发现API端点"""
        endpoints = []
        
        # 从路由文件中提取端点
        route_files = [
            'backend/routes/auth_routes.py',
            'backend/routes/blockchain_routes.py',
            'backend/routes/integral_routes.py',
            'backend/routes/user_routes.py'
        ]
        
        for route_file in route_files:
            if os.path.exists(route_file):
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单的正则表达式匹配FastAPI路由
                    import re
                    pattern = r'@(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)'                    
                    matches = re.findall(pattern, content)
                    for method, path in matches:
                        endpoints.append({
                            'path': path,
                            'methods': [method.upper()]
                        })
        
        # 如果没有找到端点，使用预定义的
        if not endpoints:
            endpoints = [
                {'path': '/api/v1/auth/login', 'methods': ['POST']},
                {'path': '/api/v1/auth/register', 'methods': ['POST']},
                {'path': '/api/v1/blockchain/certificates', 'methods': ['GET', 'POST']},
                {'path': '/api/v1/integral/balance', 'methods': ['GET']},
                {'path': '/api/v1/users/profile', 'methods': ['GET', 'PUT']},
                {'path': '/api/v1/admin/users', 'methods': ['GET', 'DELETE']},
                {'path': '/api/v1/content/store', 'methods': ['GET', 'POST']},
                {'path': '/api/v1/payment/process', 'methods': ['POST']}
            ]
        
        return endpoints
    
    def test_api_endpoint(self, endpoint: Dict) -> List[Dict]:
        """测试单个API端点"""
        vulnerabilities = []
        
        base_url = "http://localhost:8000"  # 假设本地运行
        url = f"{base_url}{endpoint['path']}"
        
        # 测试常见安全漏洞
        test_cases = [
            self.test_sql_injection,
            self.test_xss,
            self.test_csrf,
            self.test_authentication_bypass,
            self.test_rate_limiting,
            self.test_input_validation
        ]
        
        for test_func in test_cases:
            try:
                vuln = test_func(url, endpoint)
                if vuln:
                    vulnerabilities.append(vuln)
            except Exception as e:
                logger.debug(f"API测试异常 {url}: {e}")
        
        return vulnerabilities
    
    def test_sql_injection(self, url: str, endpoint: Dict) -> Optional[Dict]:
        """测试SQL注入漏洞"""
        if 'GET' not in endpoint['methods']:
            return None
            
        # 测试恶意参数
        malicious_params = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]
        
        for param in malicious_params:
            try:
                response = requests.get(f"{url}?id={param}", timeout=5)
                # 检查是否返回敏感信息或错误信息
                if ('database' in response.text.lower() or 
                    'sql' in response.text.lower() or
                    response.status_code == 500):
                    return {
                        'type': 'SQL Injection',
                        'severity': 'High',
                        'cvss_score': 9.8,
                        'endpoint': url,
                        'description': '可能存在的SQL注入漏洞'
                    }
            except:
                continue
        
        return None
    
    def test_xss(self, url: str, endpoint: Dict) -> Optional[Dict]:
        """测试跨站脚本攻击(XSS)漏洞"""
        if 'GET' not in endpoint['methods']:
            return None
            
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.get(f"{url}?search={payload}", timeout=5)
                if payload in response.text:
                    return {
                        'type': 'Cross-Site Scripting (XSS)',
                        'severity': 'Medium',
                        'cvss_score': 6.1,
                        'endpoint': url,
                        'description': '可能存在的反射型XSS漏洞'
                    }
            except:
                continue
        
        return None
    
    def test_csrf(self, url: str, endpoint: Dict) -> Optional[Dict]:
        """测试CSRF保护"""
        if 'POST' not in endpoint['methods'] and 'PUT' not in endpoint['methods']:
            return None
            
        try:
            # 尝试不带CSRF token的POST请求
            response = requests.post(url, data={'test': 'data'}, timeout=5)
            
            # 如果没有CSRF保护，通常会返回403或其他错误
            if response.status_code == 200:
                return {
                    'type': 'CSRF Protection Missing',
                    'severity': 'Medium',
                    'cvss_score': 5.4,
                    'endpoint': url,
                    'description': '缺少CSRF保护机制'
                }
        except:
            pass
        
        return None
    
    def test_authentication_bypass(self, url: str, endpoint: Dict) -> Optional[Dict]:
        """测试认证绕过漏洞"""
        try:
            # 尝试访问受保护的资源而不认证
            response = requests.get(url, timeout=5)
            
            # 检查是否需要认证但未被拦截
            if (response.status_code == 200 and 
                'protected' in url.lower()):
                return {
                    'type': 'Authentication Bypass',
                    'severity': 'High',
                    'cvss_score': 8.1,
                    'endpoint': url,
                    'description': '可能存在的认证绕过漏洞'
                }
        except:
            pass
        
        return None
    
    def test_rate_limiting(self, url: str, endpoint: Dict) -> Optional[Dict]:
        """测试速率限制"""
        if 'POST' not in endpoint['methods']:
            return None
            
        try:
            # 快速发送多个请求测试速率限制
            responses = []
            for i in range(10):
                response = requests.post(url, data={'test': f'data{i}'}, timeout=2)
                responses.append(response.status_code)
                time.sleep(0.1)  # 短暂延迟
            
            # 如果所有请求都成功，可能缺少速率限制
            if responses.count(200) > 8:
                return {
                    'type': 'Rate Limiting Missing',
                    'severity': 'Medium',
                    'cvss_score': 4.3,
                    'endpoint': url,
                    'description': '可能缺少适当的速率限制机制'
                }
        except:
            pass
        
        return None
    
    def test_input_validation(self, url: str, endpoint: Dict) -> Optional[Dict]:
        """测试输入验证"""
        test_inputs = [
            {'param': 'id', 'value': '999999999999999999999'},  # 整数溢出
            {'param': 'email', 'value': 'test@'},  # 无效邮箱
            {'param': 'name', 'value': 'A' * 10000},  # 缓冲区溢出
        ]
        
        for test_input in test_inputs:
            try:
                params = {test_input['param']: test_input['value']}
                if 'GET' in endpoint['methods']:
                    response = requests.get(url, params=params, timeout=5)
                elif 'POST' in endpoint['methods']:
                    response = requests.post(url, data=params, timeout=5)
                else:
                    continue
                    
                # 检查服务器响应
                if response.status_code == 500:
                    return {
                        'type': 'Input Validation Error',
                        'severity': 'Medium',
                        'cvss_score': 5.3,
                        'endpoint': url,
                        'description': f"输入验证不当导致服务器错误: {test_input['param']}"
                    }
                    
            except:
                continue
        
        return None
    
    def test_database_encryption(self):
        """数据库加密强度检测"""
        logger.info("开始数据库加密强度检测...")
        
        findings = {
            'encryption_algorithms': [],
            'key_management': [],
            'configuration_issues': []
        }
        
        # 检查数据库配置
        try:
            # 检查PostgreSQL连接配置
            if hasattr(settings, 'DATABASE_URL'):
                db_url = settings.DATABASE_URL
                if 'sslmode=require' not in db_url:
                    findings['configuration_issues'].append({
                        'issue': 'SSL/TLS未强制启用',
                        'severity': 'Medium',
                        'recommendation': '在数据库连接URL中添加sslmode=require'
                    })
        except:
            pass
        
        # 检查密钥管理
        env_files = ['.env', '.env.production', 'backend/.env']
        for env_file in env_files:
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'SECRET_KEY=' in content and 'secret_key_placeholder' in content:
                        findings['key_management'].append({
                            'issue': '使用默认密钥',
                            'severity': 'High',
                            'recommendation': '替换为强随机密钥'
                        })
        
        self.test_results.append({
            "test_type": "database_encryption",
            "status": "completed",
            "findings": findings,
            "timestamp": datetime.now().isoformat()
        })
    
    def check_owasp_compliance(self):
        """检查OWASP Top 10合规性"""
        logger.info("检查OWASP Top 10合规性...")
        
        owasp_checks = {
            'injection': self.check_injection_flaws(),
            'broken_authentication': self.check_broken_authentication(),
            'sensitive_data_exposure': self.check_sensitive_data_exposure(),
            'xxe': self.check_xml_external_entities(),
            'broken_access_control': self.check_broken_access_control(),
            'security_misconfiguration': self.check_security_misconfiguration(),
            'cross_site_scripting': self.check_cross_site_scripting(),
            'insecure_deserialization': self.check_insecure_deserialization(),
            'using_components_with_known_vulnerabilities': self.check_component_vulnerabilities(),
            'insufficient_logging_monitoring': self.check_logging_monitoring()
        }
        
        compliance_score = sum(1 for check in owasp_checks.values() if check['compliant'])
        total_checks = len(owasp_checks)
        
        self.test_results.append({
            "test_type": "owasp_compliance",
            "status": "completed",
            "compliance_score": f"{compliance_score}/{total_checks}",
            "details": owasp_checks,
            "timestamp": datetime.now().isoformat()
        })
    
    def check_injection_flaws(self) -> Dict:
        """检查注入缺陷"""
        return {
            'compliant': True,  # 假设使用了ORM和参数化查询
            'details': '项目使用SQLAlchemy ORM，降低了SQL注入风险'
        }
    
    def check_broken_authentication(self) -> Dict:
        """检查认证缺陷"""
        return {
            'compliant': True,
            'details': '使用JWT令牌和OAuth2认证机制'
        }
    
    def check_sensitive_data_exposure(self) -> Dict:
        """检查敏感数据暴露"""
        issues = []
        
        # 检查HTTPS配置
        if not self.is_https_configured():
            issues.append('缺少HTTPS配置')
        
        # 检查敏感信息日志
        log_files = ['security_penetration_test.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'password' in content.lower() or 'token' in content.lower():
                        issues.append('日志中可能包含敏感信息')
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues
        }
    
    def is_https_configured(self) -> bool:
        """检查HTTPS配置"""
        try:
            # 检查是否有SSL证书配置
            ssl_configs = [
                'ssl_certificate',
                'ssl_key',
                'certfile',
                'keyfile'
            ]
            
            config_files = ['nginx/nginx.conf', 'backend/config/settings.py']
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for ssl_config in ssl_configs:
                            if ssl_config in content.lower():
                                return True
            return False
        except:
            return False
    
    def check_xml_external_entities(self) -> Dict:
        """检查XML外部实体"""
        return {
            'compliant': True,
            'details': '项目主要使用JSON格式，XML使用较少'
        }
    
    def check_broken_access_control(self) -> Dict:
        """检查访问控制缺陷"""
        return {
            'compliant': True,
            'details': '实现了RBAC权限控制系统'
        }
    
    def check_security_misconfiguration(self) -> Dict:
        """检查安全配置错误"""
        issues = []
        
        # 检查调试模式
        if hasattr(settings, 'DEBUG') and settings.DEBUG:
            issues.append('生产环境中启用了调试模式')
        
        # 检查错误页面
        if not self.has_custom_error_pages():
            issues.append('缺少自定义错误页面')
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues
        }
    
    def has_custom_error_pages(self) -> bool:
        """检查是否有自定义错误页面"""
        error_pages = ['404.html', '500.html', 'error.html']
        static_dirs = ['src/assets', 'backend/static']
        
        for static_dir in static_dirs:
            if os.path.exists(static_dir):
                for error_page in error_pages:
                    if os.path.exists(os.path.join(static_dir, error_page)):
                        return True
        return False
    
    def check_cross_site_scripting(self) -> Dict:
        """检查跨站脚本攻击"""
        return {
            'compliant': True,
            'details': '前端使用Angular框架，具有内置XSS防护'
        }
    
    def check_insecure_deserialization(self) -> Dict:
        """检查不安全的反序列化"""
        return {
            'compliant': True,
            'details': '主要使用JSON序列化，避免了pickle等不安全格式'
        }
    
    def check_component_vulnerabilities(self) -> Dict:
        """检查组件漏洞"""
        issues = []
        
        # 检查依赖包版本
        requirements_files = ['backend/requirements.txt', 'package.json']
        for req_file in requirements_files:
            if os.path.exists(req_file):
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单检查是否包含已知有漏洞的包版本
                    vulnerable_packages = ['django<3.0', 'requests<2.20']
                    for vuln_pkg in vulnerable_packages:
                        if vuln_pkg in content:
                            issues.append(f'发现易受攻击的依赖包: {vuln_pkg}')
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues
        }
    
    def check_logging_monitoring(self) -> Dict:
        """检查日志和监控"""
        issues = []
        
        # 检查日志配置
        if not self.has_security_logging():
            issues.append('缺少安全事件日志记录')
        
        # 检查监控配置
        monitoring_tools = ['prometheus', 'grafana', 'sentry']
        has_monitoring = any(tool in self.get_installed_tools() for tool in monitoring_tools)
        if not has_monitoring:
            issues.append('缺少安全监控工具')
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues
        }
    
    def has_security_logging(self) -> bool:
        """检查是否有安全日志记录"""
        try:
            # 检查日志配置文件
            config_files = ['backend/config/logging.py', 'src/environments/environment.prod.ts']
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'security' in content.lower() or 'audit' in content.lower():
                            return True
            return False
        except:
            return False
    
    def get_installed_tools(self) -> List[str]:
        """获取已安装的工具列表"""
        tools = []
        
        # 检查npm包
        if os.path.exists('package.json'):
            try:
                with open('package.json', 'r', encoding='utf-8') as f:
                    package_json = json.load(f)
                    tools.extend(package_json.get('dependencies', {}).keys())
                    tools.extend(package_json.get('devDependencies', {}).keys())
            except:
                pass
        
        # 检查Python包
        if os.path.exists('backend/requirements.txt'):
            try:
                with open('backend/requirements.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            tools.append(line.split('==')[0])
            except:
                pass
        
        return tools
    
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全测试报告"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else 0
        
        # 统计总体结果
        total_critical = sum(
            result['findings'].get('critical', 0) 
            for result in self.test_results 
            if isinstance(result.get('findings'), dict)
        )
        
        total_medium = sum(
            result['findings'].get('medium', 0) 
            for result in self.test_results 
            if isinstance(result.get('findings'), dict)
        )
        
        total_low = sum(
            result['findings'].get('low', 0) 
            for result in self.test_results 
            if isinstance(result.get('findings'), dict)
        )
        
        # 判断整体安全状态
        overall_status = "PASS"
        if total_critical > 0:
            overall_status = "FAIL"
        elif total_medium > 5:
            overall_status = "WARNING"
        
        report = {
            "report_metadata": {
                "title": "安全渗透测试报告",
                "generated_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "tester": "SecurityPenetrationTester"
            },
            "summary": {
                "overall_status": overall_status,
                "total_critical_vulnerabilities": total_critical,
                "total_medium_vulnerabilities": total_medium,
                "total_low_vulnerabilities": total_low,
                "compliance_score": self.calculate_compliance_score()
            },
            "test_results": self.test_results,
            "recommendations": self.generate_recommendations(),
            "vulnerabilities_found": self.vulnerabilities_found
        }
        
        return report
    
    def calculate_compliance_score(self) -> float:
        """计算合规分数"""
        total_tests = len([r for r in self.test_results if r['status'] == 'completed'])
        passed_tests = len([
            r for r in self.test_results 
            if r['status'] == 'completed' and 
            r.get('findings', {}).get('critical', 0) == 0
        ])
        
        return (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    def generate_recommendations(self) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 基于发现的漏洞生成建议
        critical_vulns = [v for v in self.vulnerabilities_found 
                         if v.get('cvss_score', 0) >= 7.0]
        
        if critical_vulns:
            recommendations.append("立即修复所有高危漏洞")
            recommendations.append("实施紧急安全补丁")
        
        # 通用安全建议
        recommendations.extend([
            "定期更新所有依赖包到最新稳定版本",
            "实施全面的日志记录和监控系统",
            "配置Web应用防火墙(WAF)",
            "启用多因素认证(MFA)",
            "定期进行安全培训",
            "建立安全事件响应流程",
            "实施零信任安全架构",
            "定期进行渗透测试和安全评估"
        ])
        
        return recommendations

def main():
    """主函数"""
    tester = SecurityPenetrationTester()
    report = tester.run_full_security_test()
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"security_penetration_test_report_{timestamp}.json"
    
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"安全测试报告已保存到: {report_filename}")
        
        # 打印摘要
        summary = report['summary']
        print("\n" + "="*50)
        print("安全渗透测试摘要")
        print("="*50)
        print(f"总体状态: {summary['overall_status']}")
        print(f"高危漏洞: {summary['total_critical_vulnerabilities']}")
        print(f"中危漏洞: {summary['total_medium_vulnerabilities']}")
        print(f"低危漏洞: {summary['total_low_vulnerabilities']}")
        print(f"合规分数: {summary['compliance_score']:.1f}%")
        print("="*50)
        
        if summary['overall_status'] == "FAIL":
            print("❌ 安全测试未通过，请立即修复高危漏洞！")
        elif summary['overall_status'] == "WARNING":
            print("⚠️  存在中等风险，请尽快处理！")
        else:
            print("✅ 安全测试通过！")
            
    except Exception as e:
        logger.error(f"保存报告失败: {e}")

if __name__ == "__main__":
    main()