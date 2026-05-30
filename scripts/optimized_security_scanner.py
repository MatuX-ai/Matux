#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的安全漏洞扫描器
专注于项目核心代码的安全问题检测
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Vulnerability:
    """漏洞信息"""
    vulnerability_type: str
    severity: str  # HIGH, MEDIUM, LOW
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    fix_recommendation: str
    cvss_score: float

class OptimizedSecurityScanner:
    """优化的安全扫描器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.vulnerabilities: List[Vulnerability] = []
        
        # 需要排除的目录
        self.exclude_dirs = {
            'node_modules', 'venv', '__pycache__', '.git', 
            'build', 'dist', 'flutter', 'sdk', 'models',
            'docs', 'reports', 'scripts', 'shared-styles'
        }
        
        # 需要扫描的核心目录
        self.include_dirs = {
            'backend', 'src', 'config', 'middleware', 'routes',
            'services', 'models', 'utils', 'security'
        }
        
        # SQL注入检测模式
        self.sql_injection_patterns = [
            (r"(?i)(select|insert|update|delete|drop|create|alter)\s+.*['\"].*\+.*['\"]", "字符串拼接SQL查询"),
            (r"(?i)execute\s*\(\s*['\"].*\+.*['\"]\s*\)", "动态SQL执行"),
            (r"(?i)query\s*\(\s*['\"].*\+.*['\"]\s*\)", "动态查询执行"),
            (r"(?i)%s|%d|%f", "格式化字符串占位符"),
            (r"(?i)\{.*\}\.format\(.*\)", "format方法"),
            (r"(?i)f['\"].*\{.*\}.*['\"]", "f-string"),
        ]
        
        # XSS检测模式
        self.xss_patterns = [
            (r"(?i)<script[^>]*>.*?</script>", "内联脚本标签"),
            (r"(?i)on\w+\s*=\s*[\"'][^\"']*['\"]", "事件处理器"),
            (r"(?i)javascript:", "JavaScript协议"),
            (r"(?i)vbscript:", "VBScript协议"),
            (r"(?i)data:text/html", "数据URI"),
            (r"(?i)eval\s*\(", "eval函数"),
            (r"(?i)innerHTML\s*=", "innerHTML赋值"),
            (r"(?i)document\.write", "document.write"),
        ]

    def scan_project(self) -> List[Vulnerability]:
        """扫描项目核心代码"""
        logger.info("开始扫描项目核心代码安全漏洞...")
        
        # 扫描Python文件
        python_files = self._get_core_python_files()
        logger.info(f"发现 {len(python_files)} 个核心Python文件")
        
        for py_file in python_files:
            self._scan_python_file(py_file)
        
        # 扫描前端核心文件
        frontend_files = self._get_core_frontend_files()
        logger.info(f"发现 {len(frontend_files)} 个核心前端文件")
        
        for file_path in frontend_files:
            self._scan_frontend_file(file_path)
        
        logger.info(f"扫描完成，发现 {len(self.vulnerabilities)} 个安全漏洞")
        return self.vulnerabilities
    
    def _get_core_python_files(self) -> List[Path]:
        """获取核心Python文件"""
        core_files = []
        for include_dir in self.include_dirs:
            dir_path = self.project_root / include_dir
            if dir_path.exists():
                # 递归查找Python文件
                for py_file in dir_path.rglob("*.py"):
                    # 检查是否在排除目录中
                    if not any(exclude_dir in py_file.parts for exclude_dir in self.exclude_dirs):
                        core_files.append(py_file)
        return core_files
    
    def _get_core_frontend_files(self) -> List[Path]:
        """获取核心前端文件"""
        core_files = []
        frontend_dirs = ['src', 'frontend']
        
        for frontend_dir in frontend_dirs:
            dir_path = self.project_root / frontend_dir
            if dir_path.exists():
                # 查找主要的前端文件
                extensions = ['*.js', '*.ts', '*.jsx', '*.tsx', '*.html', '*.vue']
                for ext in extensions:
                    for file_path in dir_path.rglob(ext):
                        if not any(exclude_dir in file_path.parts for exclude_dir in self.exclude_dirs):
                            core_files.append(file_path)
        return core_files
    
    def _scan_python_file(self, file_path: Path):
        """扫描Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 检查SQL注入漏洞
            self._check_sql_injection(file_path, lines, content)
            
            # 检查XSS漏洞
            self._check_backend_xss(file_path, lines, content)
            
        except Exception as e:
            logger.warning(f"扫描文件 {file_path} 时出错: {e}")
    
    def _scan_frontend_file(self, file_path: Path):
        """扫描前端文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 检查前端XSS漏洞
            self._check_frontend_xss(file_path, lines, content)
            
        except Exception as e:
            logger.warning(f"扫描前端文件 {file_path} 时出错: {e}")
    
    def _check_sql_injection(self, file_path: Path, lines: List[str], content: str):
        """检查SQL注入漏洞"""
        for line_num, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            # 跳过注释和空行
            if not line_clean or line_clean.startswith('#'):
                continue
            
            # 检查各种SQL注入模式
            for pattern, description in self.sql_injection_patterns:
                if re.search(pattern, line_clean):
                    # 排除安全的参数化查询
                    if not self._is_safe_query(line_clean):
                        vulnerability = Vulnerability(
                            vulnerability_type="SQL Injection",
                            severity="HIGH",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            code_snippet=line_clean[:100],  # 截取前100字符
                            description=f"发现潜在的SQL注入漏洞 - {description}",
                            fix_recommendation="使用参数化查询、ORM框架或预编译语句替代字符串拼接",
                            cvss_score=9.8
                        )
                        self.vulnerabilities.append(vulnerability)
                        logger.warning(f"SQL注入风险 [{description}]: {file_path}:{line_num}")
                        break  # 每行只报告一次
    
    def _check_backend_xss(self, file_path: Path, lines: List[str], content: str):
        """检查后端XSS漏洞"""
        for line_num, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            if not line_clean:
                continue
            
            # 检查模板渲染和响应输出
            if any(keyword in line_clean.lower() for keyword in ['render_template', 'jsonify', 'Response']):
                # 检查是否直接输出用户输入
                if any(source in line_clean for source in ['request.args', 'request.form', 'request.json']):
                    if not self._has_output_encoding(line_clean):
                        vulnerability = Vulnerability(
                            vulnerability_type="Backend XSS",
                            severity="MEDIUM",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            code_snippet=line_clean[:100],
                            description="发现潜在的反射型XSS漏洞 - 用户输入未经适当编码直接输出",
                            fix_recommendation="对用户输入进行HTML编码后再输出，或使用安全的模板引擎",
                            cvss_score=6.1
                        )
                        self.vulnerabilities.append(vulnerability)
                        logger.warning(f"后端XSS风险: {file_path}:{line_num}")
    
    def _check_frontend_xss(self, file_path: Path, lines: List[str], content: str):
        """检查前端XSS漏洞"""
        for line_num, line in enumerate(lines, 1):
            line_clean = line.strip()
            
            if not line_clean or line_clean.startswith('//'):
                continue
            
            # 检查危险的DOM操作
            for pattern, description in self.xss_patterns:
                if re.search(pattern, line_clean):
                    # 检查是否是安全使用
                    if not self._is_safe_frontend_usage(line_clean):
                        vulnerability = Vulnerability(
                            vulnerability_type="Frontend XSS",
                            severity="MEDIUM",
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            code_snippet=line_clean[:100],
                            description=f"发现前端XSS漏洞 - {description}",
                            fix_recommendation="使用安全的DOM操作方法，避免innerHTML和危险事件处理器",
                            cvss_score=6.1
                        )
                        self.vulnerabilities.append(vulnerability)
                        logger.warning(f"前端XSS风险 [{description}]: {file_path}:{line_num}")
                        break
    
    def _is_safe_query(self, line: str) -> bool:
        """判断SQL查询是否安全"""
        # 检查是否使用了安全的ORM或参数化查询
        safe_patterns = [
            r'\.execute\([^)]*(?:params|values|data)[^)]*\)',  # 参数化执行
            r'\.query\([^)]*\)',  # SQLAlchemy查询
            r'\.filter\([^)]*\)',  # SQLAlchemy过滤
            r'\.where\([^)]*\)',   # SQLAlchemy条件
            r'SELECT\s+\*\s+FROM\s+\w+\s+WHERE\s+\w+\s*=\s*\?',  # 预编译语句
            r'cursor\.execute\(.*,.*\)',  # 带参数的执行
        ]
        
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in safe_patterns)
    
    def _has_output_encoding(self, line: str) -> bool:
        """检查输出是否经过编码"""
        safe_functions = [
            'escape(', 'html.escape(', 'Markup.escape(',
            'json.dumps(', 'jsonify(', 'render_template('
        ]
        return any(func in line for func in safe_functions)
    
    def _is_safe_frontend_usage(self, line: str) -> bool:
        """判断前端代码是否安全使用"""
        # 检查是否在注释中或使用安全方法
        if line.strip().startswith('//') or '//' in line:
            return True
        
        # 检查是否使用安全的框架方法
        safe_frameworks = ['angular.', 'react.', 'vue.', '$sce.trustAsHtml']
        return any(framework in line.lower() for framework in safe_frameworks)
    
    def generate_report(self) -> Dict:
        """生成扫描报告"""
        # 按严重程度分类
        critical_vulns = [v for v in self.vulnerabilities if v.severity == "HIGH"]
        medium_vulns = [v for v in self.vulnerabilities if v.severity == "MEDIUM"]
        low_vulns = [v for v in self.vulnerabilities if v.severity == "LOW"]
        
        # 按文件统计
        vulns_by_file = {}
        for vuln in self.vulnerabilities:
            file_key = vuln.file_path
            if file_key not in vulns_by_file:
                vulns_by_file[file_key] = []
            vulns_by_file[file_key].append(vars(vuln))
        
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "total_vulnerabilities": len(self.vulnerabilities),
            "critical_vulnerabilities": len(critical_vulns),
            "medium_vulnerabilities": len(medium_vulns),
            "low_vulnerabilities": len(low_vulns),
            "vulnerabilities_by_type": {},
            "vulnerabilities_by_severity": {
                "HIGH": len(critical_vulns),
                "MEDIUM": len(medium_vulns),
                "LOW": len(low_vulns)
            },
            "vulnerabilities_by_file": vulns_by_file,
            "summary": {
                "sql_injection_count": len([v for v in self.vulnerabilities if "SQL Injection" in v.vulnerability_type]),
                "xss_count": len([v for v in self.vulnerabilities if "XSS" in v.vulnerability_type]),
                "other_vulnerabilities": len([v for v in self.vulnerabilities if "SQL Injection" not in v.vulnerability_type and "XSS" not in v.vulnerability_type])
            }
        }
        
        # 按漏洞类型统计
        type_count = {}
        for vuln in self.vulnerabilities:
            vuln_type = vuln.vulnerability_type
            type_count[vuln_type] = type_count.get(vuln_type, 0) + 1
        report["vulnerabilities_by_type"] = type_count
        
        return report
    
    def save_report(self, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimized_security_scan_{timestamp}.json"
        
        report = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"安全扫描报告已保存到: {filename}")
        return filename

def main():
    """主函数"""
    scanner = OptimizedSecurityScanner()
    vulnerabilities = scanner.scan_project()
    
    # 生成并保存报告
    report_file = scanner.save_report()
    
    # 打印摘要
    report = scanner.generate_report()
    print("\n" + "="*60)
    print("优化安全扫描摘要")
    print("="*60)
    print(f"扫描时间: {report['scan_timestamp']}")
    print(f"总漏洞数: {report['total_vulnerabilities']}")
    print(f"高危漏洞: {report['critical_vulnerabilities']}")
    print(f"中危漏洞: {report['medium_vulnerabilities']}")
    print(f"低危漏洞: {report['low_vulnerabilities']}")
    print("-"*60)
    print(f"SQL注入漏洞: {report['summary']['sql_injection_count']}")
    print(f"XSS漏洞: {report['summary']['xss_count']}")
    print(f"其他漏洞: {report['summary']['other_vulnerabilities']}")
    print("="*60)
    
    if vulnerabilities:
        print("\n发现的主要漏洞:")
        # 按文件分组显示
        vulns_by_file = {}
        for vuln in vulnerabilities[:20]:  # 显示前20个漏洞
            file_key = vuln.file_path
            if file_key not in vulns_by_file:
                vulns_by_file[file_key] = []
            vulns_by_file[file_key].append(vuln)
        
        for file_path, file_vulns in list(vulns_by_file.items())[:5]:  # 显示前5个文件
            print(f"\n📁 {file_path}:")
            for vuln in file_vulns:
                print(f"  [{vuln.severity}] {vuln.vulnerability_type} (行 {vuln.line_number})")
                print(f"    描述: {vuln.description}")
        
        if len(vulnerabilities) > 20:
            print(f"\n... 还有 {len(vulnerabilities) - 20} 个漏洞")
    else:
        print("✅ 未发现明显安全漏洞")

if __name__ == "__main__":
    main()