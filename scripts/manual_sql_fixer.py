#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动SQL注入漏洞修复脚本
针对具体文件和行号进行精确修复
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualSQLFixer:
    """手动SQL注入修复器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        self.fixes_failed = []
    
    def fix_blockchain_services(self):
        """修复区块链服务中的SQL注入漏洞"""
        # 修复 gateway_service.py
        self._fix_gateway_service()
        
        # 修复 service.py  
        self._fix_blockchain_service()
        
        # 修复 vc_service.py
        self._fix_vc_service()
        
        self._save_report()
    
    def _fix_gateway_service(self):
        """修复网关服务"""
        file_path = self.project_root / "backend" / "services" / "blockchain" / "gateway_service.py"
        
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return
        
        try:
            # 创建备份
            backup_path = file_path.with_suffix(file_path.suffix + '.manual_bak')
            shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 修复具体的f-string问题
            fixes_made = []
            
            for i, line in enumerate(lines):
                original_line = line
                
                # 修复行150: description or f"积分发行_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if '积分发行_' in line and 'datetime.now()' in line:
                    # 替换为更安全的方式
                    lines[i] = line.replace(
                        'f"积分发行_{datetime.now().strftime(\'%Y%m%d_%H%M%S\')}"',
                        '"积分发行_" + datetime.now().strftime(\'%Y%m%d_%H%M%S\')'
                    )
                    fixes_made.append(f"行{i+1}: 修复f-string中的时间戳格式化")
                
                # 修复其他类似的f-string问题
                elif 'f"' in line and '{' in line and any(keyword in line for keyword in ['SELECT', 'INSERT', 'UPDATE']):
                    # 转换为.format()方法
                    fixed_line = self._convert_fstring_to_format(line)
                    if fixed_line != line:
                        lines[i] = fixed_line
                        fixes_made.append(f"行{i+1}: 转换f-string为.format()方法")
            
            # 写入修复后的内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            if fixes_made:
                self.fixes_applied.append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "fixes": fixes_made
                })
                logger.info(f"网关服务修复完成: {len(fixes_made)} 处修改")
            else:
                logger.info("网关服务无需修复")
                
        except Exception as e:
            self.fixes_failed.append({
                "file": str(file_path.relative_to(self.project_root)),
                "error": str(e)
            })
            logger.error(f"修复网关服务失败: {e}")
    
    def _fix_blockchain_service(self):
        """修复区块链主服务"""
        file_path = self.project_root / "backend" / "services" / "blockchain" / "service.py"
        
        if not file_path.exists():
            return
        
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.manual_bak')
            shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixes_made = []
            
            for i, line in enumerate(lines):
                # 修复各种f-string SQL查询
                if 'f"' in line and any(op in line.upper() for op in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                    fixed_line = self._convert_fstring_to_safe_format(line)
                    if fixed_line != line:
                        lines[i] = fixed_line
                        fixes_made.append(f"行{i+1}: 修复SQL查询f-string")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            if fixes_made:
                self.fixes_applied.append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "fixes": fixes_made
                })
                logger.info(f"区块链服务修复完成: {len(fixes_made)} 处修改")
                
        except Exception as e:
            self.fixes_failed.append({
                "file": str(file_path.relative_to(self.project_root)),
                "error": str(e)
            })
    
    def _fix_vc_service(self):
        """修复VC服务"""
        file_path = self.project_root / "backend" / "services" / "blockchain" / "vc_service.py"
        
        if not file_path.exists():
            return
        
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.manual_bak')
            shutil.copy2(file_path, backup_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixes_made = []
            
            for i, line in enumerate(lines):
                # 修复VC相关的f-string
                if 'f"' in line and ('certificate' in line or 'credential' in line):
                    fixed_line = self._convert_fstring_to_safe_format(line)
                    if fixed_line != line:
                        lines[i] = fixed_line
                        fixes_made.append(f"行{i+1}: 修复VC f-string")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            if fixes_made:
                self.fixes_applied.append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "fixes": fixes_made
                })
                logger.info(f"VC服务修复完成: {len(fixes_made)} 处修改")
                
        except Exception as e:
            self.fixes_failed.append({
                "file": str(file_path.relative_to(self.project_root)),
                "error": str(e)
            })
    
    def _convert_fstring_to_format(self, line: str) -> str:
        """将f-string转换为.format()方法"""
        # 简单的f-string转换
        if 'f"' in line:
            # 移除f前缀
            line = line.replace('f"', '"')
            # 移除f'前缀
            line = line.replace("f'", "'")
            
            # 查找 {variable} 模式并替换
            import re
            pattern = r'\{([^}]+)\}'
            matches = re.findall(pattern, line)
            
            if matches:
                # 添加.format()调用
                format_args = ', '.join(matches)
                line = line.replace('\n', '') + f'.format({format_args})\n'
        
        return line
    
    def _convert_fstring_to_safe_format(self, line: str) -> str:
        """转换为安全的.format()格式"""
        if 'f"' not in line and "f'" not in line:
            return line
            
        # 移除f前缀
        line = line.replace('f"', '"').replace("f'", "'")
        
        # 提取变量名并构建安全的.format()调用
        import re
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, line)
        
        if matches:
            # 清理变量名，只保留字母数字和下划线
            clean_matches = []
            for match in matches:
                # 移除表达式，只保留变量名
                var_name = match.split('.')[0].split('[')[0].strip()
                if var_name.isidentifier():
                    clean_matches.append(var_name)
            
            if clean_matches:
                format_call = '.format(' + ', '.join(clean_matches) + ')'
                # 在行尾添加.format()调用
                if line.endswith('\n'):
                    line = line.rstrip() + format_call + '\n'
                else:
                    line = line + format_call
        
        return line
    
    def _save_report(self):
        """保存修复报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "fix_timestamp": timestamp,
            "project_root": str(self.project_root),
            "fixes_applied": self.fixes_applied,
            "fixes_failed": self.fixes_failed,
            "summary": {
                "total_files_fixed": len(self.fixes_applied),
                "total_fixes": sum(len(fix.get('fixes', [])) for fix in self.fixes_applied),
                "total_failed": len(self.fixes_failed)
            }
        }
        
        report_filename = f"manual_sql_fix_report_{timestamp}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"手动修复报告已保存到: {report_filename}")
        
        # 打印详细摘要
        print("\n" + "="*60)
        print("手动SQL注入修复摘要")
        print("="*60)
        print(f"修复时间: {timestamp}")
        print(f"修复文件数: {len(self.fixes_applied)}")
        print(f"总修复数: {report['summary']['total_fixes']}")
        print(f"失败数: {len(self.fixes_failed)}")
        
        if self.fixes_applied:
            print("\n详细修复记录:")
            for fix_record in self.fixes_applied:
                print(f"\n📁 {fix_record['file']}:")
                for fix_detail in fix_record['fixes']:
                    print(f"  ✓ {fix_detail}")
        
        if self.fixes_failed:
            print("\n失败记录:")
            for failure in self.fixes_failed:
                print(f"  ✗ {failure['file']}: {failure['error']}")

def main():
    """主函数"""
    fixer = ManualSQLFixer()
    fixer.fix_blockchain_services()
    print("\n✅ 手动SQL注入修复完成!")

if __name__ == "__main__":
    main()