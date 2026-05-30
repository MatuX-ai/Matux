#!/usr/bin/env python3
"""
代码质量验证和覆盖率分析脚本
集成ESLint、单元测试覆盖率和代码复杂度分析
"""

import json
import subprocess
import sys
import os
from pathlib import Path
import time
from typing import Dict, List, Any

class CodeQualityAnalyzer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent / "sdk" / "imatu-sdk-ts"
        self.results = {}
        
    def run_eslint_analysis(self) -> Dict[str, Any]:
        """运行ESLint代码质量检查"""
        print("🔍 运行ESLint代码质量检查...")
        
        try:
            # 运行ESLint
            result = subprocess.run([
                'npx', 'eslint', 'src/**/*.ts', '--format', 'json'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ ESLint检查通过")
                return {
                    "status": "pass",
                    "errors": 0,
                    "warnings": 0,
                    "issues": []
                }
            else:
                # 解析ESLint输出
                try:
                    eslint_output = json.loads(result.stdout)
                    errors = sum(1 for issue in eslint_output if issue.get('severity') == 2)
                    warnings = sum(1 for issue in eslint_output if issue.get('severity') == 1)
                    
                    print(f"⚠️  ESLint发现问题: {errors}个错误, {warnings}个警告")
                    
                    return {
                        "status": "fail" if errors > 0 else "warning",
                        "errors": errors,
                        "warnings": warnings,
                        "issues": eslint_output[:10]  # 只保留前10个问题
                    }
                except json.JSONDecodeError:
                    print("❌ ESLint输出解析失败")
                    return {
                        "status": "error",
                        "errors": 0,
                        "warnings": 0,
                        "issues": [{"message": "ESLint执行失败", "severity": 2}]
                    }
                    
        except Exception as e:
            print(f"❌ ESLint执行异常: {e}")
            return {
                "status": "error",
                "errors": 0,
                "warnings": 0,
                "issues": [{"message": f"执行异常: {str(e)}", "severity": 2}]
            }
    
    def run_test_coverage(self) -> Dict[str, Any]:
        """运行测试并生成覆盖率报告"""
        print("🧪 运行测试并分析覆盖率...")
        
        try:
            # 运行带覆盖率的测试
            result = subprocess.run([
                'npm', 'run', 'test:coverage'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 测试执行成功")
                # 解析覆盖率报告
                return self.parse_coverage_report()
            else:
                print("❌ 测试执行失败")
                return {
                    "status": "fail",
                    "coverage": 0,
                    "lines_covered": 0,
                    "lines_total": 0,
                    "functions_covered": 0,
                    "functions_total": 0
                }
                
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            return {
                "status": "error",
                "coverage": 0,
                "error": str(e)
            }
    
    def parse_coverage_report(self) -> Dict[str, Any]:
        """解析测试覆盖率报告"""
        try:
            coverage_dir = self.project_root / "coverage"
            lcov_file = coverage_dir / "lcov.info"
            
            if not lcov_file.exists():
                print("❌ 未找到覆盖率报告文件")
                return {
                    "status": "error",
                    "coverage": 0,
                    "message": "覆盖率报告文件不存在"
                }
            
            # 读取lcov文件
            with open(lcov_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单解析lcov格式
            lines_found = 0
            lines_hit = 0
            functions_found = 0
            functions_hit = 0
            
            for line in content.split('\n'):
                if line.startswith('LF:'):  # Lines found
                    lines_found = int(line.split(':')[1])
                elif line.startswith('LH:'):  # Lines hit
                    lines_hit = int(line.split(':')[1])
                elif line.startswith('FN:'):  # Functions found
                    functions_found = int(line.split(':')[1])
                elif line.startswith('FH:'):  # Functions hit
                    functions_hit = int(line.split(':')[1])
            
            # 计算覆盖率百分比
            line_coverage = (lines_hit / lines_found * 100) if lines_found > 0 else 0
            function_coverage = (functions_hit / functions_found * 100) if functions_found > 0 else 0
            
            print(f"📊 行覆盖率: {line_coverage:.1f}% ({lines_hit}/{lines_found})")
            print(f"📊 函数覆盖率: {function_coverage:.1f}% ({functions_hit}/{functions_found})")
            
            return {
                "status": "pass",
                "line_coverage": line_coverage,
                "function_coverage": function_coverage,
                "lines_covered": lines_hit,
                "lines_total": lines_found,
                "functions_covered": functions_hit,
                "functions_total": functions_found
            }
            
        except Exception as e:
            print(f"❌ 覆盖率报告解析失败: {e}")
            return {
                "status": "error",
                "coverage": 0,
                "error": str(e)
            }
    
    def analyze_code_complexity(self) -> Dict[str, Any]:
        """分析代码复杂度"""
        print("🧮 分析代码复杂度...")
        
        try:
            # 统计代码行数和文件数量
            src_files = list(self.project_root.glob('src/**/*.ts'))
            total_lines = 0
            total_files = len(src_files)
            
            for file_path in src_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 过滤空行和注释行
                        code_lines = [line for line in lines 
                                    if line.strip() and not line.strip().startswith('//')]
                        total_lines += len(code_lines)
                except Exception:
                    continue
            
            # 计算平均每文件行数
            avg_lines_per_file = total_lines / total_files if total_files > 0 else 0
            
            print(f"📁 源文件数量: {total_files}")
            print(f"📝 有效代码行数: {total_lines}")
            print(f"📊 平均每文件行数: {avg_lines_per_file:.1f}")
            
            # 复杂度评估
            if avg_lines_per_file < 100:
                complexity_level = "low"
                recommendation = "代码结构良好，易于维护"
            elif avg_lines_per_file < 300:
                complexity_level = "medium"
                recommendation = "建议适当拆分大型文件"
            else:
                complexity_level = "high"
                recommendation = "强烈建议重构，拆分复杂模块"
            
            return {
                "status": "analyzed",
                "total_files": total_files,
                "total_lines": total_lines,
                "avg_lines_per_file": avg_lines_per_file,
                "complexity_level": complexity_level,
                "recommendation": recommendation
            }
            
        except Exception as e:
            print(f"❌ 复杂度分析失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """生成综合质量报告"""
        print("=" * 60)
        print("代码质量验证和覆盖率分析")
        print("=" * 60)
        
        # 执行各项检查
        eslint_result = self.run_eslint_analysis()
        coverage_result = self.run_test_coverage()
        complexity_result = self.analyze_code_complexity()
        
        # 综合评分
        quality_score = self.calculate_quality_score(
            eslint_result, coverage_result, complexity_result
        )
        
        # 生成报告
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "eslint_analysis": eslint_result,
            "coverage_analysis": coverage_result,
            "complexity_analysis": complexity_result,
            "quality_score": quality_score,
            "overall_status": self.determine_overall_status(
                eslint_result, coverage_result, complexity_result
            ),
            "recommendations": self.generate_recommendations(
                eslint_result, coverage_result, complexity_result
            )
        }
        
        return report
    
    def calculate_quality_score(self, eslint_result: Dict, coverage_result: Dict, 
                              complexity_result: Dict) -> float:
        """计算综合质量得分"""
        score_components = []
        
        # ESLint得分 (40%权重)
        if eslint_result["status"] == "pass":
            eslint_score = 1.0
        elif eslint_result["status"] == "warning":
            eslint_score = 0.7
        else:
            eslint_score = 0.3
        score_components.append(eslint_score * 0.4)
        
        # 覆盖率得分 (40%权重)
        if "line_coverage" in coverage_result:
            coverage_percentage = coverage_result["line_coverage"] / 100
            coverage_score = min(1.0, coverage_percentage)
            score_components.append(coverage_score * 0.4)
        else:
            score_components.append(0.2)  # 默认得分
        
        # 复杂度得分 (20%权重)
        if "complexity_level" in complexity_result:
            if complexity_result["complexity_level"] == "low":
                complexity_score = 1.0
            elif complexity_result["complexity_level"] == "medium":
                complexity_score = 0.7
            else:
                complexity_score = 0.4
            score_components.append(complexity_score * 0.2)
        else:
            score_components.append(0.1)  # 默认得分
        
        return sum(score_components)
    
    def determine_overall_status(self, eslint_result: Dict, coverage_result: Dict, 
                               complexity_result: Dict) -> str:
        """确定整体状态"""
        scores = []
        
        # ESLint状态
        if eslint_result["status"] == "pass":
            scores.append(3)
        elif eslint_result["status"] == "warning":
            scores.append(2)
        else:
            scores.append(1)
        
        # 覆盖率状态
        if "line_coverage" in coverage_result:
            if coverage_result["line_coverage"] >= 80:
                scores.append(3)
            elif coverage_result["line_coverage"] >= 60:
                scores.append(2)
            else:
                scores.append(1)
        else:
            scores.append(1)
        
        # 复杂度状态
        if "complexity_level" in complexity_result:
            if complexity_result["complexity_level"] == "low":
                scores.append(3)
            elif complexity_result["complexity_level"] == "medium":
                scores.append(2)
            else:
                scores.append(1)
        else:
            scores.append(1)
        
        average_score = sum(scores) / len(scores)
        
        if average_score >= 2.5:
            return "excellent"
        elif average_score >= 2.0:
            return "good"
        elif average_score >= 1.5:
            return "fair"
        else:
            return "poor"
    
    def generate_recommendations(self, eslint_result: Dict, coverage_result: Dict, 
                               complexity_result: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # ESLint相关建议
        if eslint_result["status"] != "pass":
            if eslint_result["errors"] > 0:
                recommendations.append(f"修复{eslint_result['errors']}个代码错误")
            if eslint_result["warnings"] > 0:
                recommendations.append(f"处理{eslint_result['warnings']}个代码警告")
        
        # 覆盖率相关建议
        if "line_coverage" in coverage_result:
            current_coverage = coverage_result["line_coverage"]
            if current_coverage < 80:
                needed_coverage = 80 - current_coverage
                recommendations.append(f"提高测试覆盖率{needed_coverage:.1f}个百分点至80%")
        
        # 复杂度相关建议
        if "complexity_level" in complexity_result:
            if complexity_result["complexity_level"] == "high":
                recommendations.append("重构复杂模块，降低代码复杂度")
                recommendations.append(complexity_result["recommendation"])
        
        if not recommendations:
            recommendations.append("代码质量良好，继续保持")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any]):
        """保存质量报告"""
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"code_quality_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 详细质量报告已保存到: {report_file}")
        
        # 也保存为Markdown格式便于阅读
        md_file = reports_dir / f"code_quality_report_{timestamp}.md"
        self.save_markdown_report(report, md_file)
    
    def save_markdown_report(self, report: Dict[str, Any], filepath: Path):
        """保存Markdown格式报告"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 代码质量分析报告\n\n")
            f.write(f"**生成时间**: {report['timestamp']}\n\n")
            
            f.write("## 综合评分\n")
            f.write(f"- **质量得分**: {report['quality_score']:.2f}/1.00\n")
            f.write(f"- **整体状态**: {report['overall_status'].upper()}\n\n")
            
            f.write("## ESLint分析\n")
            eslint = report['eslint_analysis']
            f.write(f"- 状态: {eslint['status']}\n")
            f.write(f"- 错误数: {eslint.get('errors', 0)}\n")
            f.write(f"- 警告数: {eslint.get('warnings', 0)}\n\n")
            
            f.write("## 测试覆盖率\n")
            coverage = report['coverage_analysis']
            if 'line_coverage' in coverage:
                f.write(f"- 行覆盖率: {coverage['line_coverage']:.1f}%\n")
                f.write(f"- 函数覆盖率: {coverage['function_coverage']:.1f}%\n")
            f.write("\n")
            
            f.write("## 代码复杂度\n")
            complexity = report['complexity_analysis']
            f.write(f"- 文件数量: {complexity.get('total_files', 0)}\n")
            f.write(f"- 代码行数: {complexity.get('total_lines', 0)}\n")
            f.write(f"- 复杂度等级: {complexity.get('complexity_level', 'unknown')}\n\n")
            
            f.write("## 改进建议\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")

def main():
    """主函数"""
    analyzer = CodeQualityAnalyzer()
    report = analyzer.generate_quality_report()
    
    # 显示摘要
    print("\n" + "=" * 60)
    print("📊 质量分析摘要")
    print("=" * 60)
    print(f"综合质量得分: {report['quality_score']:.2f}/1.00")
    print(f"整体状态: {report['overall_status'].upper()}")
    
    eslint = report['eslint_analysis']
    print(f"ESLint检查: {eslint['errors']}错误, {eslint['warnings']}警告")
    
    coverage = report['coverage_analysis']
    if 'line_coverage' in coverage:
        print(f"测试覆盖率: {coverage['line_coverage']:.1f}%")
    
    complexity = report['complexity_analysis']
    print(f"代码复杂度: {complexity.get('complexity_level', 'unknown')}")
    
    print("\n💡 改进建议:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # 保存报告
    analyzer.save_report(report)
    
    # 根据质量得分给出最终评价
    score = report['quality_score']
    if score >= 0.8:
        print("\n🎉 代码质量优秀，可以投入生产使用！")
    elif score >= 0.6:
        print("\n✅ 代码质量良好，建议根据建议进行优化")
    else:
        print("\n⚠️ 代码质量需要改进，建议重点关注问题区域")

if __name__ == "__main__":
    main()