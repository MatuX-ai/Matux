#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonarQube扫描结果验证脚本
用于验证扫描是否成功完成并分析基本质量指标
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class SonarScanValidator:
    def __init__(self, base_url: str = "http://localhost:9000/sonarqube", username: str = "admin", password: str = "admin"):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def get_project_status(self, project_key: str) -> Dict[str, Any]:
        """获取项目状态信息"""
        url = f"{self.base_url}/api/measures/component"
        params = {
            'component': project_key,
            'metricKeys': 'bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc,sqale_index,reliability_rating,security_rating,sqale_rating'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ 获取项目 {project_key} 状态失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"✗ 请求项目 {project_key} 状态时出错: {str(e)}")
            return None

    def get_issues_summary(self, project_key: str) -> Dict[str, int]:
        """获取问题摘要统计"""
        url = f"{self.base_url}/api/issues/search"
        params = {
            'componentKeys': project_key,
            'statuses': 'OPEN,CONFIRMED,REOPENED',
            'ps': 1  # 只需要总数
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                return {
                    'total': data.get('total', 0),
                    'facets': data.get('facets', [])
                }
            else:
                return {'total': 0}
        except Exception as e:
            print(f"✗ 获取问题统计时出错: {str(e)}")
            return {'total': 0}

    def get_quality_gate_status(self, project_key: str) -> Dict[str, Any]:
        """获取质量门禁状态"""
        url = f"{self.base_url}/api/qualitygates/project_status"
        params = {'projectKey': project_key}

        try:
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json().get('projectStatus', {})
            else:
                return {}
        except Exception as e:
            print(f"✗ 获取质量门禁状态时出错: {str(e)}")
            return {}

    def analyze_project_metrics(self, project_key: str, project_name: str) -> Dict[str, Any]:
        """分析项目指标"""
        print(f"\n分析项目: {project_name} ({project_key})")
        print("-" * 50)

        # 获取测量数据
        measures_data = self.get_project_status(project_key)
        if not measures_data:
            return None

        # 解析测量值
        metrics = {}
        component = measures_data.get('component', {})
        for measure in component.get('measures', []):
            metric_key = measure['metric']
            metric_value = measure['value']
            metrics[metric_key] = metric_value

        # 获取问题统计
        issues_summary = self.get_issues_summary(project_key)

        # 获取质量门禁状态
        quality_gate = self.get_quality_gate_status(project_key)

        # 构建分析结果
        analysis_result = {
            'project_key': project_key,
            'project_name': project_name,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'issues_count': issues_summary.get('total', 0),
            'quality_gate_status': quality_gate.get('status', 'UNKNOWN'),
            'analysis_complete': True
        }

        # 打印关键指标
        print(f"代码行数: {metrics.get('ncloc', 'N/A')}")
        print(f"覆盖率: {metrics.get('coverage', 'N/A')}%")
        print(f"重复率: {metrics.get('duplicated_lines_density', 'N/A')}%")
        print(f"Bug数量: {metrics.get('bugs', 'N/A')}")
        print(f"漏洞数量: {metrics.get('vulnerabilities', 'N/A')}")
        print(f"代码异味: {metrics.get('code_smells', 'N/A')}")
        print(f"技术债(天): {int(metrics.get('sqale_index', 0))/480:.1f}" if metrics.get('sqale_index') else "技术债: N/A")
        print(f"问题总数: {issues_summary.get('total', 'N/A')}")
        print(f"质量门禁: {quality_gate.get('status', 'UNKNOWN')}")

        # 质量评级
        reliability = self.get_rating_description(metrics.get('reliability_rating', '5'))
        security = self.get_rating_description(metrics.get('security_rating', '5'))
        maintainability = self.get_rating_description(metrics.get('sqale_rating', '5'))

        print(f"可靠性评级: {reliability}")
        print(f"安全性评级: {security}")
        print(f"可维护性评级: {maintainability}")

        return analysis_result

    def get_rating_description(self, rating_value: str) -> str:
        """转换评级数值为描述"""
        ratings = {
            '1.0': 'A (优秀)',
            '2.0': 'B (良好)',
            '3.0': 'C (一般)',
            '4.0': 'D (较差)',
            '5.0': 'E (很差)'
        }
        return ratings.get(rating_value, f"未知({rating_value})")

    def generate_validation_report(self, projects_analysis: List[Dict[str, Any]]) -> str:
        """生成验证报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sonar-validation-report-{timestamp}.json"

        report = {
            'report_title': 'SonarQube扫描结果验证报告',
            'generated_at': datetime.now().isoformat(),
            'projects_analyzed': len(projects_analysis),
            'projects': projects_analysis,
            'summary': self.generate_summary_stats(projects_analysis)
        }

        # 保存报告
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return filename

    def generate_summary_stats(self, projects_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成汇总统计"""
        summary = {
            'total_projects': len(projects_analysis),
            'successful_analyses': sum(1 for p in projects_analysis if p.get('analysis_complete')),
            'failed_analyses': sum(1 for p in projects_analysis if not p.get('analysis_complete')),
            'total_issues': sum(p.get('issues_count', 0) for p in projects_analysis),
            'average_coverage': self.calculate_average(projects_analysis, 'coverage'),
            'average_duplication': self.calculate_average(projects_analysis, 'duplicated_lines_density')
        }
        return summary

    def calculate_average(self, projects: List[Dict[str, Any]], metric_key: str) -> float:
        """计算平均值"""
        values = []
        for project in projects:
            metrics = project.get('metrics', {})
            if metric_key in metrics:
                try:
                    values.append(float(metrics[metric_key]))
                except ValueError:
                    pass

        return sum(values) / len(values) if values else 0.0

def main():
    """主验证函数"""
    print("SonarQube扫描结果验证")
    print("=" * 60)

    # 初始化验证器
    validator = SonarScanValidator()

    # 要验证的项目列表
    projects = [
        ('imatuproject-full', 'iMatu主项目'),
        ('imatuproject-backend', 'iMatu后端服务'),
        ('imatuproject-frontend', 'iMatu前端应用')
    ]

    # 分析各个项目
    projects_analysis = []
    for project_key, project_name in projects:
        analysis = validator.analyze_project_metrics(project_key, project_name)
        if analysis:
            projects_analysis.append(analysis)
        time.sleep(1)  # 避免请求过于频繁

    # 生成验证报告
    if projects_analysis:
        report_file = validator.generate_validation_report(projects_analysis)
        print(f"\n{'='*60}")
        print(f"✓ 验证完成！详细报告已保存至: {report_file}")

        # 打印汇总信息
        summary = validator.generate_summary_stats(projects_analysis)
        print(f"\n汇总统计:")
        print(f"- 成功分析项目: {summary['successful_analyses']}/{summary['total_projects']}")
        print(f"- 总问题数: {summary['total_issues']}")
        print(f"- 平均覆盖率: {summary['average_coverage']:.1f}%")
        print(f"- 平均重复率: {summary['average_duplication']:.1f}%")
    else:
        print("\n✗ 未能获取任何项目的分析数据")

if __name__ == "__main__":
    main()
