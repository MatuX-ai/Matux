"""
防重复开发检测机制
确保新功能开发不会与现有实现冲突
提供代码、功能和架构层面的重复检测
"""

import ast
from collections import defaultdict
import hashlib
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DuplicateDevelopmentDetector:
    """防重复开发检测器"""

    def __init__(self, project_root: str = "."):
        """
        初始化检测器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root)
        self.detection_results = {}
        self.function_signatures = {}
        self.file_hashes = {}
        self.keyword_patterns = {}

        # 定义关键领域和关键词
        self.domain_keywords = {
            "model_compression": ["compress", "quantiz", "prun", "optimize", "reduce"],
            "edge_impulse": ["edge", "impulse", "ei-", "studio"],
            "tinyml": ["tiny", "micro", "tflite", "embedded"],
            "model_training": ["train", "fit", "learn", "epoch"],
            "deployment": ["deploy", "export", "package", "bundle"],
        }

    def scan_project_for_duplicates(self) -> Dict[str, Any]:
        """
        扫描整个项目寻找潜在的重复开发

        Returns:
            检测结果报告
        """
        logger.info("开始项目重复开发扫描...")

        # 1. 文件级重复检测
        file_duplicates = self._detect_file_duplicates()

        # 2. 函数级重复检测
        function_duplicates = self._detect_function_duplicates()

        # 3. 功能领域重叠检测
        domain_overlaps = self._detect_domain_overlaps()

        # 4. 代码模式重复检测
        pattern_duplicates = self._detect_pattern_duplicates()

        # 5. 配置和依赖重复检测
        config_duplicates = self._detect_config_duplicates()

        # 综合结果
        self.detection_results = {
            "scan_timestamp": self._get_current_timestamp(),
            "project_root": str(self.project_root),
            "file_duplicates": file_duplicates,
            "function_duplicates": function_duplicates,
            "domain_overlaps": domain_overlaps,
            "pattern_duplicates": pattern_duplicates,
            "config_duplicates": config_duplicates,
            "risk_assessment": self._assess_duplicate_risks(
                file_duplicates, function_duplicates, domain_overlaps
            ),
        }

        logger.info("重复开发扫描完成")
        return self.detection_results

    def _detect_file_duplicates(self) -> Dict[str, Any]:
        """检测文件级别的重复"""
        logger.info("检测文件重复...")

        file_info = {}
        name_similarities = []
        content_similarities = []

        # 收集所有Python文件信息
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            try:
                rel_path = str(file_path.relative_to(self.project_root))

                # 计算文件哈希
                with open(file_path, "rb") as f:
                    content = f.read()
                    file_hash = hashlib.md5(content).hexdigest()

                # 提取文件基本信息
                file_info[rel_path] = {
                    "size": len(content),
                    "hash": file_hash,
                    "modified_time": os.path.getmtime(file_path),
                    "name": file_path.name,
                    "directory": str(file_path.parent.relative_to(self.project_root)),
                }

                self.file_hashes[rel_path] = file_hash

            except Exception as e:
                logger.warning(f"处理文件失败 {file_path}: {e}")

        # 检测名称相似性
        file_names = list(file_info.keys())
        for i in range(len(file_names)):
            for j in range(i + 1, len(file_names)):
                name1, name2 = file_names[i], file_names[j]
                similarity = self._calculate_name_similarity(name1, name2)
                if similarity > 0.7:  # 高相似度阈值
                    name_similarities.append(
                        {
                            "files": [name1, name2],
                            "similarity": similarity,
                            "type": "name_similarity",
                        }
                    )

        # 检测内容重复
        hash_groups = defaultdict(list)
        for file_path, file_hash in self.file_hashes.items():
            hash_groups[file_hash].append(file_path)

        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                content_similarities.append(
                    {"files": files, "hash": file_hash, "type": "identical_content"}
                )

        return {
            "total_files": len(file_info),
            "name_similarities": name_similarities,
            "content_duplicates": content_similarities,
            "file_info": file_info,
        }

    def _detect_function_duplicates(self) -> Dict[str, Any]:
        """检测函数级别的重复"""
        logger.info("检测函数重复...")

        function_signatures = {}
        duplicate_candidates = []

        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                rel_path = str(file_path.relative_to(self.project_root))
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        signature = self._extract_function_signature(node, rel_path)
                        func_key = f"{rel_path}:{node.name}"

                        function_signatures[func_key] = signature

                        # 检查是否存在相似函数
                        similar_funcs = self._find_similar_functions(
                            signature, function_signatures, func_key
                        )

                        if similar_funcs:
                            duplicate_candidates.append(
                                {
                                    "function": func_key,
                                    "similar_functions": similar_funcs,
                                    "signature": signature,
                                }
                            )

            except Exception as e:
                logger.warning(f"解析文件失败 {file_path}: {e}")

        self.function_signatures = function_signatures

        return {
            "total_functions": len(function_signatures),
            "duplicate_candidates": duplicate_candidates,
            "function_signatures": function_signatures,
        }

    def _detect_domain_overlaps(self) -> Dict[str, Any]:
        """检测功能领域的重叠"""
        logger.info("检测领域重叠...")

        domain_files = defaultdict(list)
        overlap_analysis = {}

        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            try:
                rel_path = str(file_path.relative_to(self.project_root))
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().lower()

                # 分析文件属于哪些领域
                file_domains = []
                for domain, keywords in self.domain_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        file_domains.append(domain)
                        domain_files[domain].append(rel_path)

                if file_domains:
                    overlap_analysis[rel_path] = {
                        "domains": file_domains,
                        "domain_count": len(file_domains),
                    }

            except Exception as e:
                logger.warning(f"分析文件领域失败 {file_path}: {e}")

        # 分析领域重叠
        domain_overlaps = {}
        domains = list(domain_files.keys())

        for i in range(len(domains)):
            for j in range(i + 1, len(domains)):
                domain1, domain2 = domains[i], domains[j]
                common_files = set(domain_files[domain1]) & set(domain_files[domain2])

                if common_files:
                    overlap_key = f"{domain1}_vs_{domain2}"
                    domain_overlaps[overlap_key] = {
                        "domains": [domain1, domain2],
                        "common_files": list(common_files),
                        "overlap_count": len(common_files),
                    }

        return {
            "domain_distribution": {
                domain: len(files) for domain, files in domain_files.items()
            },
            "file_domain_mapping": overlap_analysis,
            "domain_overlaps": domain_overlaps,
        }

    def _detect_pattern_duplicates(self) -> Dict[str, Any]:
        """检测代码模式重复"""
        logger.info("检测代码模式重复...")

        patterns = {
            "model_loading": [r"tf\.keras\.models\.load_model", r"tflite\.Interpreter"],
            "compression_patterns": [r"quantiz", r"prun", r"compress"],
            "api_endpoints": [r"@.*route", r"def.*api", r"class.*API"],
            "configuration_loading": [
                r"config.*load",
                r"settings.*get",
                r"environment.*variable",
            ],
        }

        pattern_matches = defaultdict(list)

        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            try:
                rel_path = str(file_path.relative_to(self.project_root))
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                for pattern_name, regex_patterns in patterns.items():
                    for regex_pattern in regex_patterns:
                        matches = re.findall(regex_pattern, content, re.IGNORECASE)
                        if matches:
                            pattern_matches[pattern_name].append(
                                {
                                    "file": rel_path,
                                    "matches": matches,
                                    "count": len(matches),
                                }
                            )

            except Exception as e:
                logger.warning(f"模式匹配失败 {file_path}: {e}")

        return {"patterns": patterns, "pattern_matches": dict(pattern_matches)}

    def _detect_config_duplicates(self) -> Dict[str, Any]:
        """检测配置和依赖重复"""
        logger.info("检测配置重复...")

        config_files = (
            list(self.project_root.rglob("*.yaml"))
            + list(self.project_root.rglob("*.yml"))
            + list(self.project_root.rglob("*.json"))
            + list(self.project_root.rglob("*.ini"))
        )

        config_analysis = {
            "config_files": [],
            "dependency_conflicts": [],
            "environment_duplicates": [],
        }

        # 分析配置文件
        for config_file in config_files:
            try:
                rel_path = str(config_file.relative_to(self.project_root))
                config_analysis["config_files"].append(
                    {
                        "path": rel_path,
                        "extension": config_file.suffix,
                        "size": config_file.stat().st_size,
                    }
                )
            except Exception as e:
                logger.warning(f"配置文件分析失败 {config_file}: {e}")

        # 检测依赖冲突 (requirements文件)
        requirements_files = list(self.project_root.rglob("*requirements*.txt"))
        dependencies = defaultdict(list)

        for req_file in requirements_files:
            try:
                with open(req_file, "r") as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # 提取包名
                            package_name = re.split("[>=<~]", line)[0].strip()
                            if package_name:
                                dependencies[package_name].append(
                                    {
                                        "file": str(
                                            req_file.relative_to(self.project_root)
                                        ),
                                        "line": line_num,
                                        "version_spec": line,
                                    }
                                )
            except Exception as e:
                logger.warning(f"依赖文件分析失败 {req_file}: {e}")

        # 找出冲突的依赖
        for package, locations in dependencies.items():
            if len(locations) > 1:
                versions = [loc["version_spec"] for loc in locations]
                if len(set(versions)) > 1:  # 不同版本
                    config_analysis["dependency_conflicts"].append(
                        {
                            "package": package,
                            "locations": locations,
                            "versions": versions,
                        }
                    )

        return config_analysis

    def _extract_function_signature(
        self, node: ast.FunctionDef, file_path: str
    ) -> Dict[str, Any]:
        """提取函数签名信息"""
        signature = {
            "name": node.name,
            "file": file_path,
            "args": [],
            "returns": None,
            "decorators": [],
            "complexity": 0,
        }

        # 提取参数信息
        for arg in node.args.args:
            signature["args"].append(
                {
                    "name": arg.arg,
                    "annotation": (
                        ast.unparse(arg.annotation) if arg.annotation else None
                    ),
                }
            )

        # 提取返回类型
        if node.returns:
            signature["returns"] = ast.unparse(node.returns)

        # 提取装饰器
        for decorator in node.decorator_list:
            signature["decorators"].append(ast.unparse(decorator))

        # 计算复杂度 (简化版)
        signature["complexity"] = len(
            [n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While))]
        )

        return signature

    def _find_similar_functions(
        self,
        signature: Dict[str, Any],
        all_signatures: Dict[str, Any],
        exclude_key: str,
    ) -> List[Dict[str, Any]]:
        """查找相似函数"""
        similar_funcs = []

        for func_key, other_signature in all_signatures.items():
            if func_key == exclude_key:
                continue

            similarity_score = self._calculate_function_similarity(
                signature, other_signature
            )
            if similarity_score > 0.8:  # 高相似度阈值
                similar_funcs.append(
                    {
                        "function": func_key,
                        "similarity": similarity_score,
                        "differences": self._get_function_differences(
                            signature, other_signature
                        ),
                    }
                )

        return similar_funcs

    def _calculate_function_similarity(
        self, sig1: Dict[str, Any], sig2: Dict[str, Any]
    ) -> float:
        """计算函数相似度"""
        if sig1["name"] != sig2["name"]:
            return 0.0

        # 参数相似度
        args1 = set(arg["name"] for arg in sig1["args"])
        args2 = set(arg["name"] for arg in sig2["args"])
        args_similarity = len(args1 & args2) / max(len(args1 | args2), 1)

        # 返回类型相似度
        returns_similar = sig1["returns"] == sig2["returns"]
        returns_similarity = 1.0 if returns_similar else 0.0

        # 装饰器相似度
        dec1 = set(sig1["decorators"])
        dec2 = set(sig2["decorators"])
        dec_similarity = len(dec1 & dec2) / max(len(dec1 | dec2), 1)

        # 综合相似度
        return 0.4 * args_similarity + 0.3 * returns_similarity + 0.3 * dec_similarity

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算文件名相似度"""
        # 简化的字符串相似度计算
        name1_lower = name1.lower().replace("/", "_").replace("\\", "_")
        name2_lower = name2.lower().replace("/", "_").replace("\\", "_")

        if name1_lower == name2_lower:
            return 1.0

        # 计算编辑距离相似度
        def edit_distance(s1, s2):
            if len(s1) < len(s2):
                return edit_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)

            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row

            return previous_row[-1]

        distance = edit_distance(name1_lower, name2_lower)
        max_len = max(len(name1_lower), len(name2_lower))
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0

    def _get_function_differences(
        self, sig1: Dict[str, Any], sig2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取函数差异"""
        return {
            "args_diff": set(a["name"] for a in sig1["args"])
            ^ set(a["name"] for a in sig2["args"]),
            "returns_diff": sig1["returns"] != sig2["returns"],
            "decorators_diff": set(sig1["decorators"]) ^ set(sig2["decorators"]),
        }

    def _assess_duplicate_risks(
        self,
        file_dups: Dict[str, Any],
        func_dups: Dict[str, Any],
        domain_overlaps: Dict[str, Any],
    ) -> Dict[str, Any]:
        """评估重复开发风险"""

        risk_factors = {
            "file_name_conflicts": len(file_dups.get("name_similarities", [])),
            "identical_files": len(file_dups.get("content_duplicates", [])),
            "function_similarities": len(func_dups.get("duplicate_candidates", [])),
            "domain_overlaps": len(domain_overlaps.get("domain_overlaps", [])),
        }

        # 计算总体风险分数 (0-100)
        risk_score = (
            risk_factors["file_name_conflicts"] * 10
            + risk_factors["identical_files"] * 25
            + risk_factors["function_similarities"] * 20
            + risk_factors["domain_overlaps"] * 15
        )

        risk_level = "LOW"
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"

        return {
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": self._generate_recommendations(risk_factors),
        }

    def _generate_recommendations(self, risk_factors: Dict[str, int]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if risk_factors["file_name_conflicts"] > 0:
            recommendations.append("统一文件命名规范，避免功能描述重叠")

        if risk_factors["identical_files"] > 0:
            recommendations.append("合并相同功能的文件，消除代码冗余")

        if risk_factors["function_similarities"] > 5:
            recommendations.append("重构相似函数，提取公共逻辑")

        if risk_factors["domain_overlaps"] > 2:
            recommendations.append("明确定义各功能模块边界，避免职责重叠")

        if not recommendations:
            recommendations.append("当前代码结构良好，无明显重复开发风险")

        return recommendations

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()

    def save_detection_report(self, output_path: str = None) -> str:
        """保存检测报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"duplicate_detection_report_{timestamp}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.detection_results, f, indent=2, ensure_ascii=False)

        logger.info(f"检测报告已保存到: {output_path}")
        return output_path

    def get_high_risk_items(self, max_items: int = 10) -> List[Dict[str, Any]]:
        """获取高风险项目"""
        high_risk = []

        # 文件重复风险
        file_dups = self.detection_results.get("file_duplicates", {})
        for dup in file_dups.get("name_similarities", []):
            high_risk.append(
                {
                    "type": "file_name_similarity",
                    "risk_level": "MEDIUM",
                    "items": dup["files"],
                    "details": f"相似度: {dup['similarity']:.2f}",
                }
            )

        # 函数重复风险
        func_dups = self.detection_results.get("function_duplicates", {})
        for dup in func_dups.get("duplicate_candidates", []):
            high_risk.append(
                {
                    "type": "function_similarity",
                    "risk_level": "HIGH",
                    "items": [dup["function"]]
                    + [sf["function"] for sf in dup["similar_functions"]],
                    "details": f"相似函数数量: {len(dup['similar_functions'])}",
                }
            )

        # 按风险等级排序
        high_risk.sort(
            key=lambda x: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[x["risk_level"]],
            reverse=True,
        )

        return high_risk[:max_items]


# 使用示例
def demo_duplicate_detector():
    """演示重复开发检测功能"""
    print("=== 防重复开发检测演示 ===")

    detector = DuplicateDevelopmentDetector(".")

    # 执行检测
    print("1. 执行项目扫描...")
    results = detector.scan_project_for_duplicates()

    # 显示风险评估
    risk_assessment = results.get("risk_assessment", {})
    print(f"\n2. 风险评估:")
    print(f"   风险分数: {risk_assessment.get('risk_score', 0)}")
    print(f"   风险等级: {risk_assessment.get('risk_level', 'UNKNOWN')}")

    # 显示主要风险因素
    risk_factors = risk_assessment.get("risk_factors", {})
    print(f"\n3. 风险因素:")
    for factor, count in risk_factors.items():
        print(f"   {factor}: {count}")

    # 显示建议
    recommendations = risk_assessment.get("recommendations", [])
    print(f"\n4. 改进建议:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")

    # 保存报告
    print(f"\n5. 保存检测报告...")
    report_path = detector.save_detection_report()
    print(f"   报告位置: {report_path}")

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    from datetime import datetime

    demo_duplicate_detector()
