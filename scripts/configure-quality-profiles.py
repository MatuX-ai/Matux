#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonarQube Quality Profiles 配置脚本
用于自动化配置项目的质量规则集和门禁标准
"""

import json
import requests
import time
from typing import Dict, List, Any

class SonarQubeConfigurator:
    def __init__(self, base_url: str = "http://localhost:9000/sonarqube", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}' if token else '',
            'Content-Type': 'application/json'
        }

    def create_quality_profile(self, name: str, language: str, parent_key: str = None) -> str:
        """创建质量配置文件"""
        url = f"{self.base_url}/api/qualityprofiles/create"
        data = {
            'name': name,
            'language': language
        }
        if parent_key:
            data['parentKey'] = parent_key

        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code == 200:
            profile_key = response.json()['profile']['key']
            print(f"✓ 创建质量配置文件: {name} ({language}) - Key: {profile_key}")
            return profile_key
        else:
            print(f"✗ 创建质量配置文件失败: {response.text}")
            return None

    def activate_rules(self, profile_key: str, rule_keys: List[str]) -> None:
        """激活规则到配置文件"""
        url = f"{self.base_url}/api/qualityprofiles/activate_rule"

        for rule_key in rule_keys:
            data = {
                'key': profile_key,
                'rule': rule_key,
                'severity': 'MAJOR'  # 默认严重程度
            }

            response = requests.post(url, data=data, headers=self.headers)
            if response.status_code == 200:
                print(f"✓ 激活规则: {rule_key}")
            else:
                print(f"✗ 激活规则失败 {rule_key}: {response.text}")

    def set_rule_severity(self, profile_key: str, rule_key: str, severity: str) -> None:
        """设置规则严重程度"""
        url = f"{self.base_url}/api/qualityprofiles/change_parent"
        data = {
            'profileKey': profile_key,
            'ruleKey': rule_key,
            'severity': severity
        }

        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code != 200:
            print(f"✗ 设置规则严重程度失败 {rule_key}: {response.text}")

    def create_quality_gate(self, name: str) -> str:
        """创建质量门禁"""
        url = f"{self.base_url}/api/qualitygates/create"
        data = {'name': name}

        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code == 200:
            gate_id = response.json()['id']
            print(f"✓ 创建质量门禁: {name} - ID: {gate_id}")
            return gate_id
        else:
            print(f"✗ 创建质量门禁失败: {response.text}")
            return None

    def set_quality_gate_condition(self, gate_id: str, metric: str, op: str, error_threshold: str) -> None:
        """设置质量门禁条件"""
        url = f"{self.base_url}/api/qualitygates/create_condition"
        data = {
            'gateId': gate_id,
            'metric': metric,
            'op': op,
            'error': error_threshold
        }

        response = requests.post(url, data=data, headers=self.headers)
        if response.status_code == 200:
            print(f"✓ 设置门禁条件: {metric} {op} {error_threshold}")
        else:
            print(f"✗ 设置门禁条件失败: {response.text}")

def configure_imatu_quality_profiles():
    """配置iMatu项目的质量配置文件"""

    # 初始化配置器
    configurator = SonarQubeConfigurator()

    # 创建各语言的质量配置文件
    profiles = {}

    # Python配置文件
    python_profile = configurator.create_quality_profile(
        "iMatu Python Rules", "py", "Sonar way"
    )
    profiles['python'] = python_profile

    # TypeScript配置文件
    ts_profile = configurator.create_quality_profile(
        "iMatu TypeScript Rules", "ts", "Sonar way"
    )
    profiles['typescript'] = ts_profile

    # JavaScript配置文件
    js_profile = configurator.create_quality_profile(
        "iMatu JavaScript Rules", "js", "Sonar way"
    )
    profiles['javascript'] = js_profile

    # CSS/SCSS配置文件
    css_profile = configurator.create_quality_profile(
        "iMatu CSS Rules", "css", "Sonar way"
    )
    profiles['css'] = css_profile

    # 激活关键规则
    critical_rules = {
        'python': [
            'python:S1481',  # Unused local variables
            'python:S1134',  # Fixme tags
            'python:S1135',  # Todo tags
            'python:S2068',  # Hard-coded credentials
            'python:S5542',  # Encryption algorithms
            'python:S4792',  # Logging configuration
        ],
        'typescript': [
            'typescript:S1854',  # Unused assignments
            'typescript:S1134',  # Fixme tags
            'typescript:S1135',  # Todo tags
            'typescript:S2068',  # Hard-coded credentials
            'typescript:S5691',  # XSS vulnerabilities
            'typescript:S4502',  # CSRF protection
        ]
    }

    # 激活规则
    for lang, rules in critical_rules.items():
        if profiles.get(lang):
            configurator.activate_rules(profiles[lang], rules)

    return profiles

def configure_quality_gates():
    """配置质量门禁标准"""

    configurator = SonarQubeConfigurator()

    # 创建主质量门禁
    main_gate = configurator.create_quality_gate("iMatu Quality Gate")

    if main_gate:
        # 设置门禁条件
        conditions = [
            ('new_coverage', 'LT', '80'),           # 新代码覆盖率 < 80%
            ('new_duplicated_lines_density', 'GT', '3'),  # 重复率 > 3%
            ('new_maintainability_rating', 'GT', '1'),    # 可维护性评级 > A
            ('new_security_rating', 'GT', '1'),           # 安全评级 > A
            ('new_reliability_rating', 'GT', '1'),        # 可靠性评级 > A
            ('new_security_hotspots_reviewed', 'LT', '100'), # 安全热点审查率 < 100%
            ('bugs', 'GT', '0'),                   # Bug数量 > 0
            ('vulnerabilities', 'GT', '0'),        # 漏洞数量 > 0
            ('code_smells', 'GT', '100'),          # 代码异味 > 100
        ]

        for metric, op, threshold in conditions:
            configurator.set_quality_gate_condition(main_gate, metric, op, threshold)

    return main_gate

def main():
    """主配置函数"""
    print("开始配置SonarQube质量配置文件...")
    print("=" * 50)

    try:
        # 配置质量配置文件
        print("\n1. 配置质量配置文件:")
        profiles = configure_imatu_quality_profiles()

        # 配置质量门禁
        print("\n2. 配置质量门禁:")
        gate = configure_quality_gates()

        print("\n" + "=" * 50)
        print("配置完成!")
        print(f"创建的配置文件: {list(profiles.keys())}")
        print(f"质量门禁ID: {gate}")

    except Exception as e:
        print(f"\n配置过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
