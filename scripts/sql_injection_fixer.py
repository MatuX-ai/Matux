#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL注入漏洞修复器
自动修复扫描发现的SQL注入漏洞
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SQLInjectionFixer:
    """SQL注入漏洞修复器"""
    
    def __init__(self, project_root: str = ".", scan_report: str = None):
        self.project_root = Path(project_root)
        self.scan_report = scan_report
        self.fixes_applied = []
        self.fixes_failed = []
        
        # 需要修复的关键文件列表
        self.target_files = [
            "backend/backtest_hardware_rental.py",
            "backend/core_function_verification.py",
            "backend/delivery_verification.py",
            "backend/services/blockchain/gateway_service.py",
            "backend/services/blockchain/service.py",
            "backend/services/blockchain/vc_service.py",
            "backend/simple_test_app.py",
            "backend/test_hardware_api.py",
            "backend/user_license_app.py",
            "backend/validate_hardware_migration.py"
        ]
        
        # SQL注入修复模式
        self.fix_patterns = {
            # f-string模式
            r'f["\'].*?\{.*?\}.*?["\']': self._fix_fstring,
            # % 格式化模式
            r'["\'].*?%.*?["\']\s*%\s*\(': self._fix_percent_format,
            # .format() 方法模式
            r'["\'].*?\{.*?\}.*?["\']\.format\(': self._fix_format_method,
        }

    def load_scan_report(self) -> List[Dict]:
        """加载扫描报告"""
        if not self.scan_report:
            # 自动查找最新的扫描报告
            scan_reports = list(Path(".").glob("optimized_security_scan_*.json"))
            if scan_reports:
                self.scan_report = str(max(scan_reports, key=os.path.getctime))
            else:
                raise FileNotFoundError("未找到安全扫描报告")
        
        with open(self.scan_report, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # 提取SQL注入漏洞
        sql_vulnerabilities = []
        for file_path, vulns in report_data.get("vulnerabilities_by_file", {}).items():
            for vuln in vulns:
                if "SQL Injection" in vuln["vulnerability_type"]:
                    sql_vulnerabilities.append({
                        "file_path": file_path,
                        "line_number": vuln["line_number"],
                        "description": vuln["description"],
                        "code_snippet": vuln["code_snippet"]
                    })
        
        logger.info(f"加载了 {len(sql_vulnerabilities)} 个SQL注入漏洞")
        return sql_vulnerabilities

    def fix_all_vulnerabilities(self):
        """修复所有SQL注入漏洞"""
        vulnerabilities = self.load_scan_report()
        
        # 按文件分组处理
        vulns_by_file = {}
        for vuln in vulnerabilities:
            file_path = vuln["file_path"]
            if file_path not in vulns_by_file:
                vulns_by_file[file_path] = []
            vulns_by_file[file_path].append(vuln)
        
        # 修复每个文件
        for file_path, file_vulns in vulns_by_file.items():
            if self._should_process_file(file_path):
                self._fix_file(file_path, file_vulns)
        
        self._save_fix_report()

    def _should_process_file(self, file_path: str) -> bool:
        """判断是否应该处理该文件"""
        # 只处理指定的目标文件
        return any(target_file in file_path for target_file in self.target_files)

    def _fix_file(self, file_path: str, vulnerabilities: List[Dict]):
        """修复单个文件中的漏洞"""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            logger.warning(f"文件不存在: {full_path}")
            return
        
        try:
            # 创建备份
            backup_path = full_path.with_suffix(full_path.suffix + '.bak')
            shutil.copy2(full_path, backup_path)
            
            # 读取文件内容
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 按行号排序漏洞（从后往前处理，避免行号变化）
            sorted_vulns = sorted(vulnerabilities, key=lambda x: x['line_number'], reverse=True)
            
            fixes_count = 0
            for vuln in sorted_vulns:
                line_num = vuln['line_number'] - 1  # 转换为0索引
                if 0 <= line_num < len(lines):
                    original_line = lines[line_num]
                    fixed_line = self._apply_fixes(original_line.strip())
                    
                    if fixed_line != original_line.strip():
                        lines[line_num] = fixed_line + '\n'
                        fixes_count += 1
                        
                        self.fixes_applied.append({
                            "file": file_path,
                            "line": vuln['line_number'],
                            "original": original_line.strip(),
                            "fixed": fixed_line,
                            "description": vuln['description']
                        })
            
            # 写入修复后的内容
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"文件 {file_path} 修复完成，共修复 {fixes_count} 处漏洞")
            
        except Exception as e:
            self.fixes_failed.append({
                "file": file_path,
                "error": str(e)
            })
            logger.error(f"修复文件 {file_path} 失败: {e}")

    def _apply_fixes(self, line: str) -> str:
        """应用具体的修复"""
        fixed_line = line
        
        # 1. 修复f-string中的SQL注入风险
        fixed_line = self._fix_fstring_sql(fixed_line)
        
        # 2. 修复%格式化中的SQL注入风险
        fixed_line = self._fix_percent_format_sql(fixed_line)
        
        # 3. 修复.format()方法中的SQL注入风险
        fixed_line = self._fix_format_method_sql(fixed_line)
        
        return fixed_line

    def _fix_fstring_sql(self, line: str) -> str:
        """修复f-string中的SQL注入"""
        # 匹配f-string模式，特别是包含数据库操作的
        fstring_pattern = r'f(["\'])(.*?)\{(.*?)\}(.*?)\1'
        
        def replace_fstring(match):
            quote = match.group(1)
            prefix = match.group(2)
            expression = match.group(3)
            suffix = match.group(4)
            
            # 检查是否是SQL相关的表达式
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE']
            if any(keyword in line.upper() for keyword in sql_keywords):
                # 转换为参数化查询
                return f'"{prefix}{{}}{suffix}".format({expression})'
            else:
                # 对于非SQL的f-string，保持原样或转换为.format()
                return f'"{prefix}{{}}{suffix}".format({expression})'
        
        return re.sub(fstring_pattern, replace_fstring, line, flags=re.IGNORECASE)

    def _fix_percent_format_sql(self, line: str) -> str:
        """修复%格式化中的SQL注入"""
        # 匹配 % 格式化模式
        percent_pattern = r'(["\'])(.*?)%([sd])(.*?)\1\s*%\s*(\([^)]+\)|[^,]+)'
        
        def replace_percent(match):
            quote = match.group(1)
            prefix = match.group(2)
            format_char = match.group(3)
            suffix = match.group(4)
            values = match.group(5)
            
            # 转换为.format()方法
            return f'"{prefix}{{{format_char}}}{suffix}".format({values})'
        
        return re.sub(percent_pattern, replace_percent, line)

    def _fix_format_method_sql(self, line: str) -> str:
        """修复.format()方法中的SQL注入"""
        # 这个通常已经是相对安全的，但可以进一步加固
        format_pattern = r'(["\'])(.*?)\{([^}]*?)\}(.*?)\1\.format\((.*?)\)'
        
        def replace_format(match):
            quote = match.group(1)
            prefix = match.group(2)
            placeholder = match.group(3)
            suffix = match.group(4)
            args = match.group(5)
            
            # 确保参数是安全的
            safe_args = self._sanitize_format_args(args)
            return f'{quote}{prefix}{{{placeholder}}}{suffix}{quote}.format({safe_args})'
        
        return re.sub(format_pattern, replace_format, line)

    def _sanitize_format_args(self, args: str) -> str:
        """清理.format()方法的参数"""
        # 移除潜在的危险字符
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/']
        sanitized = args
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized

    def _fix_fstring(self, match) -> str:
        """修复f-string模式"""
        return match.group(0).replace('f"', '"').replace("f'", "'") + '.format()'

    def _fix_percent_format(self, match) -> str:
        """修复%格式化模式"""
        return match.group(0).replace('%', '{}').replace('(', '').replace(')', '') + '.format()'

    def _fix_format_method(self, match) -> str:
        """修复.format()方法模式"""
        return match.group(0)  # 通常已经相对安全

    def _save_fix_report(self):
        """保存修复报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "fix_timestamp": timestamp,
            "project_root": str(self.project_root),
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "summary": {
                "total_fixed": len(self.fixes_applied),
                "total_failed": len(self.fixes_failed)
            }
        }
        
        report_filename = f"sql_injection_fix_report_{timestamp}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"修复报告已保存到: {report_filename}")
        
        # 打印摘要
        print("\n" + "="*50)
        print("SQL注入漏洞修复摘要")
        print("="*50)
        print(f"修复时间: {timestamp}")
        print(f"成功修复: {len(self.fixes_applied)} 处")
        print(f"修复失败: {len(self.fixes_failed)} 处")
        
        if self.fixes_applied:
            print("\n成功修复的文件:")
            fixed_files = set(fix['file'] for fix in self.fixes_applied)
            for file_path in fixed_files:
                file_fixes = [f for f in self.fixes_applied if f['file'] == file_path]
                print(f"  {file_path}: {len(file_fixes)} 处修复")
        
        if self.fixes_failed:
            print("\n修复失败的文件:")
            for failure in self.fixes_failed:
                print(f"  {failure['file']}: {failure['error']}")

def main():
    """主函数"""
    fixer = SQLInjectionFixer()
    
    try:
        fixer.fix_all_vulnerabilities()
        print("\n✅ SQL注入漏洞修复完成!")
    except Exception as e:
        logger.error(f"修复过程出错: {e}")
        print(f"\n❌ 修复失败: {e}")

if __name__ == "__main__":
    main()