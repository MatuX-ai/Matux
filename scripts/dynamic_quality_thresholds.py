#!/usr/bin/env python3
"""
动态质量阈值配置工具
根据分支策略实现差异化的质量门禁标准
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class DynamicThresholdConfigurator:
    """动态阈值配置器"""

    def __init__(self):
        self.project_root = Path("g:/iMato")

        # 定义不同分支的质量标准
        self.branch_policies = {
            "main": {
                "name": "生产分支 - 严格标准",
                "coverage_min": 80.0,          # 测试覆盖率最低要求
                "duplication_max": 3.0,         # 代码重复率最高允许
                "bugs_max": 0,                  # Bug 数量上限（阻断级别）
                "vulnerabilities_max": 0,       # 漏洞数量上限（阻断级别）
                "code_smells_max": 100,         # 代码异味上限
                "maintainability_rating": "A",  # 可维护性评级
                "security_rating": "A",         # 安全评级
                "reliability_rating": "A",      # 可靠性评级
                "hotspots_reviewed_min": 100    # 安全热点审查率
            },
            "develop": {
                "name": "开发分支 - 中等标准",
                "coverage_min": 75.0,
                "duplication_max": 4.0,
                "bugs_max": 2,
                "vulnerabilities_max": 1,
                "code_smells_max": 150,
                "maintainability_rating": "B",
                "security_rating": "B",
                "reliability_rating": "B",
                "hotspots_reviewed_min": 90
            },
            "release/*": {
                "name": "发布分支 - 严格标准",
                "coverage_min": 78.0,
                "duplication_max": 3.5,
                "bugs_max": 1,
                "vulnerabilities_max": 0,
                "code_smells_max": 120,
                "maintainability_rating": "A",
                "security_rating": "A",
                "reliability_rating": "A",
                "hotspots_reviewed_min": 95
            },
            "feature/*": {
                "name": "功能分支 - 基础标准",
                "coverage_min": 70.0,
                "duplication_max": 5.0,
                "bugs_max": 5,
                "vulnerabilities_max": 2,
                "code_smells_max": 200,
                "maintainability_rating": "C",
                "security_rating": "C",
                "reliability_rating": "C",
                "hotspots_reviewed_min": 80
            },
            "hotfix/*": {
                "name": "热修复分支 - 中等标准",
                "coverage_min": 75.0,
                "duplication_max": 4.0,
                "bugs_max": 2,
                "vulnerabilities_max": 1,
                "code_smells_max": 150,
                "maintainability_rating": "B",
                "security_rating": "B",
                "reliability_rating": "B",
                "hotspots_reviewed_min": 90
            }
        }

    def get_branch_policy(self, branch_name: str) -> Dict[str, Any]:
        """根据分支名称获取对应的质量政策"""
        # 精确匹配
        if branch_name in self.branch_policies:
            return self.branch_policies[branch_name]

        # 模式匹配
        for pattern, policy in self.branch_policies.items():
            if pattern.endswith("*") and branch_name.startswith(pattern[:-1]):
                return policy

        # 默认使用 develop 分支标准
        print(f"⚠️ 未找到分支 '{branch_name}' 的特定策略，使用 develop 标准")
        return self.branch_policies["develop"]

    def generate_sonar_config(self, branch_name: str) -> str:
        """生成 SonarQube 质量门禁配置文件"""
        policy = self.get_branch_policy(branch_name)

        config_lines = [
            f"# 质量门禁配置 - 分支：{branch_name}",
            f"# 策略：{policy['name']}",
            "",
            "# 覆盖率阈值",
            f"sonar.qualitygate.coverage.min={policy['coverage_min']}",
            "",
            "# 重复率阈值",
            f"sonar.qualitygate.duplication.max={policy['duplication_max']}",
            "",
            "# Bug 数量限制",
            f"sonar.qualitygate.bugs.max={policy['bugs_max']}",
            "",
            "# 漏洞数量限制",
            f"sonar.qualitygate.vulnerabilities.max={policy['vulnerabilities_max']}",
            "",
            "# 代码异味限制",
            f"sonar.qualitygate.code_smells.max={policy['code_smells_max']}",
            "",
            "# 可维护性评级",
            f"sonar.qualitygate.maintainability.rating.min={policy['maintainability_rating']}",
            "",
            "# 安全评级",
            f"sonar.qualitygate.security.rating.min={policy['security_rating']}",
            "",
            "# 可靠性评级",
            f"sonar.qualitygate.reliability.rating.min={policy['reliability_rating']}",
            "",
            "# 安全热点审查率",
            f"sonar.qualitygate.hotspots.reviewed.min={policy['hotspots_reviewed_min']}",
        ]

        return "\n".join(config_lines)

    def generate_jenkins_conditions(self, branch_name: str) -> str:
        """生成 Jenkins Pipeline 质量门禁条件"""
        policy = self.get_branch_policy(branch_name)

        conditions = []

        # 覆盖率检查
        conditions.append(
            f"if (coverage < {policy['coverage_min']}) {{\n"
            f"    error('测试覆盖率 {coverage}% 低于 {branch_name} 分支要求的 {policy['coverage_min']}%')\n"
            f"}}"
        )

        # 重复率检查
        conditions.append(
            f"if (duplication > {policy['duplication_max']}) {{\n"
            f"    error('代码重复率 {duplication}% 高于 {branch_name} 分支允许的 {policy['duplication_max']}%')\n"
            f"}}"
        )

        # Bug 数量检查
        if policy['bugs_max'] == 0:
            conditions.append(
                f"if (blocking_bugs > 0) {{\n"
                f"    error('{branch_name} 分支不允许存在阻断级别 Bug')\n"
                f"}}"
            )
        else:
            conditions.append(
                f"if (blocking_bugs > {policy['bugs_max']}) {{\n"
                f"    error('阻断级别 Bug 数量 {blocking_bugs} 超过 {branch_name} 分支限制的 {policy['bugs_max']}')\n"
                f"}}"
            )

        # 漏洞数量检查
        if policy['vulnerabilities_max'] == 0:
            conditions.append(
                f"if (blocking_vulnerabilities > 0) {{\n"
                f"    error('{branch_name} 分支不允许存在阻断级别漏洞')\n"
                f"}}"
            )
        else:
            conditions.append(
                f"if (blocking_vulnerabilities > {policy['vulnerabilities_max']}) {{\n"
                f"    error('阻断级别漏洞数量 {blocking_vulnerabilities} 超过 {branch_name} 分支限制的 {policy['vulnerabilities_max']}')\n"
                f"}}"
            )

        return "\n\n".join(conditions)

    def generate_github_actions_matrix(self) -> Dict[str, Any]:
        """生成 GitHub Actions 矩阵配置"""
        return {
            "include": [
                {
                    "branch": "main",
                    "coverage_threshold": 80,
                    "duplication_threshold": 3,
                    "fail_on_blocking_bugs": True,
                    "fail_on_blocking_vulnerabilities": True
                },
                {
                    "branch": "develop",
                    "coverage_threshold": 75,
                    "duplication_threshold": 4,
                    "fail_on_blocking_bugs": False,
                    "fail_on_blocking_vulnerabilities": False,
                    "max_blocking_issues": 2
                },
                {
                    "branch_pattern": "feature/*",
                    "coverage_threshold": 70,
                    "duplication_threshold": 5,
                    "fail_on_blocking_bugs": False,
                    "fail_on_blocking_vulnerabilities": False,
                    "max_blocking_issues": 5
                }
            ]
        }

    def save_all_configs(self):
        """保存所有配置文件"""
        output_dir = self.project_root / "quality_thresholds"
        output_dir.mkdir(exist_ok=True)

        configs_saved = []

        # 为每个分支策略生成配置
        for branch_name, policy in self.branch_policies.items():
            # SonarQube 配置
            sonar_config = self.generate_sonar_config(branch_name)
            sonar_path = output_dir / f"sonar_quality_gate_{branch_name.replace('*', '_')}.properties"
            with open(sonar_path, 'w', encoding='utf-8') as f:
                f.write(sonar_config)
            configs_saved.append(str(sonar_path))

            # Jenkins 条件配置
            jenkins_config = self.generate_jenkins_conditions(branch_name)
            jenkins_path = output_dir / f"jenkins_quality_conditions_{branch_name.replace('*', '_')}.groovy"
            with open(jenkins_path, 'w', encoding='utf-8') as f:
                f.write(jenkins_config)
            configs_saved.append(str(jenkins_path))

        # GitHub Actions 矩阵配置
        github_matrix = self.generate_github_actions_matrix()
        matrix_path = output_dir / "github_actions_matrix.json"
        with open(matrix_path, 'w', encoding='utf-8') as f:
            json.dump(github_matrix, f, indent=2, ensure_ascii=False)
        configs_saved.append(str(matrix_path))

        # 总览文档
        overview_path = output_dir / "README.md"
        with open(overview_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_overview_doc())
        configs_saved.append(str(overview_path))

        print(f"✅ 已保存 {len(configs_saved)} 个配置文件:")
        for path in configs_saved:
            print(f"   - {path}")

        return configs_saved

    def _generate_overview_doc(self) -> str:
        """生成分支策略总览文档"""
        doc = """# 动态质量阈值配置总览

## 分支策略说明

本项目采用差异化的质量门禁策略，根据不同分支类型设置不同的质量标准。

### 分支类型与质量标准

| 分支类型 | 覆盖率要求 | 重复率限制 | Bug 限制 | 漏洞限制 | 适用场景 |
|---------|-----------|-----------|---------|---------|----------|
| main (生产) | ≥80% | ≤3% | 0 (阻断级) | 0 (阻断级) | 生产环境发布 |
| release/* (发布) | ≥78% | ≤3.5% | ≤1 | 0 (阻断级) | 版本发布准备 |
| develop (开发) | ≥75% | ≤4% | ≤2 | ≤1 | 日常开发集成 |
| hotfix/* (热修复) | ≥75% | ≤4% | ≤2 | ≤1 | 紧急问题修复 |
| feature/* (功能) | ≥70% | ≤5% | ≤5 | ≤2 | 新功能开发 |

## 配置文件说明

### SonarQube 配置
- `sonar_quality_gate_*.properties` - 各分支的 SonarQube 质量门禁配置
- 自动应用到对应的分支扫描

### Jenkins 配置
- `jenkins_quality_conditions_*.groovy` - Jenkins Pipeline 质量检查条件
- 在 CI/CD流程中自动执行检查

### GitHub Actions 配置
- `github_actions_matrix.json` - GitHub Actions 矩阵策略配置
- 用于 PR 检查和自动化工作流

## 使用方法

### 1. 本地开发检查
```bash
# 运行质量检查脚本
python scripts/quality_trend_analyzer.py
```

### 2. CI/CD自动检查
- 推送到对应分支时自动触发
- PR 创建时自动运行质量门禁
- 不满足标准的代码将被阻止合并

### 3. 查看质量报告
- HTML 报告：`quality_reports/quality_report_*.html`
- 历史数据：`quality_reports/quality_history.json`

## 质量指标说明

### 测试覆盖率 (Coverage)
- 衡量单元测试覆盖的代码比例
- 新代码必须达到对应分支的最低要求
- 鼓励持续提高覆盖率

### 代码重复率 (Duplication)
- 检测代码复制粘贴程度
- 过高的重复率会导致维护困难
- 建议通过重构提取公共组件

### Bug 数量
- 统计阻断级别的 Bug 数量
- 生产分支不允许存在任何阻断 Bug
- 其他分支控制在合理范围

### 安全漏洞 (Vulnerabilities)
- 检测潜在的安全风险
- 生产分支零容忍
- 开发分支需要定期清理

### 代码异味 (Code Smells)
- 衡量代码的可维护性
- 包括复杂度、命名规范等
- 控制在合理范围内

## 持续改进

质量阈值会根据项目发展阶段和团队实际情况进行动态调整。
建议定期回顾和优化这些标准。
"""
        return doc

    def apply_to_jenkinsfile(self):
        """应用配置到 Jenkinsfile"""
        jenkinsfile_path = self.project_root / "Jenkinsfile"

        if not jenkinsfile_path.exists():
            print(f"⚠️ Jenkinsfile 不存在")
            return

        print(f"📝 准备更新 Jenkinsfile...")
        # 这里可以添加实际的 Jenkinsfile 更新逻辑
        print("✅ Jenkinsfile 更新完成（需要手动集成）")


def main():
    """主函数"""
    configurator = DynamicThresholdConfigurator()

    print("🔧 开始配置动态质量阈值...")
    print("=" * 60)

    # 保存所有配置文件
    configs = configurator.save_all_configs()

    # 应用到 Jenkinsfile
    configurator.apply_to_jenkinsfile()

    print("=" * 60)
    print("✅ 动态质量阈值配置完成！")

    return True


if __name__ == "__main__":
    main()
