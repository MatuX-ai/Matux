#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
链码生命周期配置回测验证脚本
验证链码安装、批准和提交的完整流程
"""

import json
import subprocess
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

class ChaincodeLifecycleBacktest:
    def __init__(self, network_path: str = r"g:\iMato\blockchain\fabric-network"):
        self.network_path = network_path
        self.channel_name = "imatu-channel"
        self.chaincode_name = "integral_cc"
        self.chaincode_version = "1.0"
        self.package_name = f"{self.chaincode_name}.tar.gz"
        self.test_results = []
        self.start_time = datetime.now()

    def log_result(self, test_name: str, status: str, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   详情: {details}")

    def run_docker_command(self, command: List[str]) -> tuple[int, str, str]:
        """执行Docker命令"""
        try:
            result = subprocess.run(
                command,
                cwd=self.network_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    def test_docker_status(self) -> bool:
        """测试Docker状态"""
        test_name = "Docker服务状态检查"
        try:
            returncode, stdout, stderr = self.run_docker_command(["docker", "info"])
            if returncode == 0:
                self.log_result(test_name, "PASS", "Docker服务正常运行")
                return True
            else:
                self.log_result(test_name, "FAIL", f"Docker服务异常: {stderr}")
                return False
        except Exception as e:
            self.log_result(test_name, "FAIL", f"Docker连接失败: {str(e)}")
            return False

    def test_network_containers(self) -> bool:
        """测试网络容器状态"""
        test_name = "Fabric网络容器状态"
        try:
            # 检查Peer容器
            returncode, stdout, stderr = self.run_docker_command([
                "docker", "ps", "--filter", "name=peer0", "--format", "{{.Names}}"
            ])

            if returncode == 0:
                containers = [c for c in stdout.split('\n') if c.strip()]
                if len(containers) >= 3:
                    self.log_result(test_name, "PASS", f"检测到 {len(containers)} 个Peer节点: {', '.join(containers)}")
                    return True
                else:
                    self.log_result(test_name, "FAIL", f"Peer节点数量不足: 期望≥3, 实际{len(containers)}")
                    return False
            else:
                self.log_result(test_name, "FAIL", f"无法获取容器列表: {stderr}")
                return False
        except Exception as e:
            self.log_result(test_name, "FAIL", f"容器状态检查失败: {str(e)}")
            return False

    def test_chaincode_package_creation(self) -> bool:
        """测试链码包创建"""
        test_name = "链码包创建"
        try:
            # 先清理旧包
            cleanup_cmd = ["docker", "exec", "cli", "rm", "-f", self.package_name]
            self.run_docker_command(cleanup_cmd)

            # 创建新包
            package_cmd = [
                "docker", "exec", "cli",
                "peer", "lifecycle", "chaincode", "package",
                self.package_name,
                "--path", "/opt/gopath/src/github.com/chaincode",
                "--lang", "golang",
                "--label", f"{self.chaincode_name}_{self.chaincode_version}"
            ]

            returncode, stdout, stderr = self.run_docker_command(package_cmd)

            if returncode == 0:
                # 验证包是否存在
                check_cmd = ["docker", "exec", "cli", "ls", "-la", self.package_name]
                check_returncode, check_stdout, check_stderr = self.run_docker_command(check_cmd)

                if check_returncode == 0:
                    self.log_result(test_name, "PASS", f"链码包创建成功: {self.package_name}")
                    return True
                else:
                    self.log_result(test_name, "FAIL", f"链码包创建但验证失败: {check_stderr}")
                    return False
            else:
                self.log_result(test_name, "FAIL", f"链码包创建失败: {stderr}")
                return False
        except Exception as e:
            self.log_result(test_name, "FAIL", f"链码包创建异常: {str(e)}")
            return False

    def test_chaincode_installation(self) -> bool:
        """测试链码安装到Peer节点"""
        test_name = "链码安装到Peer节点"
        organizations = [
            {
                "name": "Education Bureau",
                "msp_id": "EducationBureauMSP",
                "peer_address": "peer0.education.imatu.com:7051",
                "tls_cert": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt",
                "msp_path": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp"
            },
            {
                "name": "School",
                "msp_id": "SchoolMSP",
                "peer_address": "peer0.school.imatu.com:9051",
                "tls_cert": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt",
                "msp_path": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp"
            },
            {
                "name": "Enterprise",
                "msp_id": "EnterpriseMSP",
                "peer_address": "peer0.enterprise.imatu.com:11051",
                "tls_cert": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt",
                "msp_path": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp"
            }
        ]

        success_count = 0
        for org in organizations:
            try:
                env_vars = [
                    f"CORE_PEER_TLS_ENABLED=true",
                    f"CORE_PEER_LOCALMSPID={org['msp_id']}",
                    f"CORE_PEER_TLS_ROOTCERT_FILE={org['tls_cert']}",
                    f"CORE_PEER_MSPCONFIGPATH={org['msp_path']}",
                    f"CORE_PEER_ADDRESS={org['peer_address']}"
                ]

                install_cmd = [
                    "docker", "exec", "cli"
                ] + env_vars + [
                    "peer", "lifecycle", "chaincode", "install", self.package_name
                ]

                returncode, stdout, stderr = self.run_docker_command(install_cmd)

                if returncode == 0:
                    success_count += 1
                    self.log_result(f"{test_name} - {org['name']}", "PASS", "链码安装成功")
                else:
                    self.log_result(f"{test_name} - {org['name']}", "FAIL", f"链码安装失败: {stderr}")

            except Exception as e:
                self.log_result(f"{test_name} - {org['name']}", "FAIL", f"链码安装异常: {str(e)}")

        if success_count == len(organizations):
            self.log_result(test_name, "PASS", f"所有 {success_count} 个组织链码安装成功")
            return True
        else:
            self.log_result(test_name, "FAIL", f"部分组织链码安装失败: {success_count}/{len(organizations)} 成功")
            return False

    def test_package_id_query(self) -> Optional[str]:
        """测试查询Package ID"""
        test_name = "Package ID查询"
        try:
            query_cmd = ["docker", "exec", "cli", "peer", "lifecycle", "chaincode", "queryinstalled"]
            returncode, stdout, stderr = self.run_docker_command(query_cmd)

            if returncode == 0 and stdout:
                # 解析Package ID
                import re
                package_id_match = re.search(r'Package ID: ([^,\s]+)', stdout)
                if package_id_match:
                    package_id = package_id_match.group(1)
                    self.log_result(test_name, "PASS", f"Package ID: {package_id}")
                    return package_id
                else:
                    self.log_result(test_name, "FAIL", "无法从输出中解析Package ID")
                    return None
            else:
                self.log_result(test_name, "FAIL", f"查询失败: {stderr}")
                return None
        except Exception as e:
            self.log_result(test_name, "FAIL", f"查询异常: {str(e)}")
            return None

    def test_chaincode_approval(self, package_id: str) -> bool:
        """测试链码批准"""
        test_name = "链码定义批准"
        organizations = [
            {
                "name": "Education Bureau",
                "msp_id": "EducationBureauMSP",
                "peer_address": "peer0.education.imatu.com:7051",
                "tls_cert": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt",
                "msp_path": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp"
            },
            {
                "name": "School",
                "msp_id": "SchoolMSP",
                "peer_address": "peer0.school.imatu.com:9051",
                "tls_cert": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt",
                "msp_path": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp"
            },
            {
                "name": "Enterprise",
                "msp_id": "EnterpriseMSP",
                "peer_address": "peer0.enterprise.imatu.com:11051",
                "tls_cert": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/peers/peer0.enterprise.imatu.com/tls/ca.crt",
                "msp_path": "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/enterprise.imatu.com/users/Admin@enterprise.imatu.com/msp"
            }
        ]

        success_count = 0
        for org in organizations:
            try:
                env_vars = [
                    f"CORE_PEER_TLS_ENABLED=true",
                    f"CORE_PEER_LOCALMSPID={org['msp_id']}",
                    f"CORE_PEER_TLS_ROOTCERT_FILE={org['tls_cert']}",
                    f"CORE_PEER_MSPCONFIGPATH={org['msp_path']}",
                    f"CORE_PEER_ADDRESS={org['peer_address']}"
                ]

                approve_cmd = [
                    "docker", "exec", "cli"
                ] + env_vars + [
                    "peer", "lifecycle", "chaincode", "approveformyorg",
                    "--channelID", self.channel_name,
                    "--name", self.chaincode_name,
                    "--version", self.chaincode_version,
                    "--package-id", package_id,
                    "--sequence", "1",
                    "--tls",
                    "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
                ]

                returncode, stdout, stderr = self.run_docker_command(approve_cmd)

                if returncode == 0:
                    success_count += 1
                    self.log_result(f"{test_name} - {org['name']}", "PASS", "链码批准成功")
                else:
                    self.log_result(f"{test_name} - {org['name']}", "FAIL", f"链码批准失败: {stderr}")

            except Exception as e:
                self.log_result(f"{test_name} - {org['name']}", "FAIL", f"链码批准异常: {str(e)}")

        if success_count == len(organizations):
            self.log_result(test_name, "PASS", f"所有 {success_count} 个组织链码批准成功")
            return True
        else:
            self.log_result(test_name, "FAIL", f"部分组织链码批准失败: {success_count}/{len(organizations)} 成功")
            return False

    def test_commit_readiness(self) -> bool:
        """测试提交准备状态"""
        test_name = "提交准备状态检查"
        try:
            check_cmd = [
                "docker", "exec", "cli",
                "peer", "lifecycle", "chaincode", "checkcommitreadiness",
                "--channelID", self.channel_name,
                "--name", self.chaincode_name,
                "--version", self.chaincode_version,
                "--sequence", "1",
                "--output", "json"
            ]

            returncode, stdout, stderr = self.run_docker_command(check_cmd)

            if returncode == 0 and stdout:
                try:
                    readiness_data = json.loads(stdout)
                    approvals = sum(1 for approved in readiness_data.values() if approved)
                    if approvals >= 2:  # 至少需要2个组织批准
                        self.log_result(test_name, "PASS", f"提交准备就绪: {approvals}/3 组织批准")
                        return True
                    else:
                        self.log_result(test_name, "FAIL", f"提交准备不足: {approvals}/3 组织批准")
                        return False
                except json.JSONDecodeError:
                    self.log_result(test_name, "FAIL", "无法解析JSON输出")
                    return False
            else:
                self.log_result(test_name, "FAIL", f"检查失败: {stderr}")
                return False
        except Exception as e:
            self.log_result(test_name, "FAIL", f"检查异常: {str(e)}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.test_results if result["status"] == "FAIL")
        total_tests = len(self.test_results)

        report = {
            "test_suite": "链码生命周期配置回测",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0
            },
            "test_results": self.test_results,
            "configuration": {
                "network_path": self.network_path,
                "channel_name": self.channel_name,
                "chaincode_name": self.chaincode_name,
                "chaincode_version": self.chaincode_version
            }
        }

        return report

    def run_full_backtest(self) -> Dict[str, Any]:
        """运行完整的回测"""
        print("=" * 60)
        print("链码生命周期配置回测开始")
        print("=" * 60)

        # 按顺序执行测试
        tests = [
            self.test_docker_status,
            self.test_network_containers,
            self.test_chaincode_package_creation,
            self.test_chaincode_installation,
            self.test_package_id_query,
            self.test_chaincode_approval,
            self.test_commit_readiness
        ]

        package_id = None

        for i, test_func in enumerate(tests):
            print(f"\n--- 测试 {i+1}/{len(tests)} ---")

            if test_func.__name__ == "test_package_id_query":
                package_id = test_func()
                if not package_id:
                    # 如果无法获取Package ID，跳过后续需要它的测试
                    self.log_result("链码批准", "SKIP", "由于Package ID获取失败，跳过批准测试")
                    self.log_result("提交准备状态检查", "SKIP", "由于Package ID获取失败，跳过提交准备检查")
                    break
            elif test_func.__name__ == "test_chaincode_approval":
                if package_id:
                    test_func(package_id)
                else:
                    self.log_result("链码批准", "SKIP", "Package ID不可用")
            elif test_func.__name__ == "test_commit_readiness":
                # 这个测试依赖于批准测试的成功
                # 在实际环境中应该检查批准状态
                test_func()
            else:
                test_func()

        # 生成报告
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("回测完成")
        print("=" * 60)
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过测试: {report['summary']['passed_tests']}")
        print(f"失败测试: {report['summary']['failed_tests']}")
        print(f"通过率: {report['summary']['pass_rate']}%")
        print(f"执行时间: {report['duration_seconds']:.2f}秒")

        return report

def main():
    """主函数"""
    backtester = ChaincodeLifecycleBacktest()
    report = backtester.run_full_backtest()

    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"chaincode_lifecycle_backtest_{timestamp}.json"

    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n详细报告已保存到: {report_filename}")
    except Exception as e:
        print(f"保存报告失败: {e}")

if __name__ == "__main__":
    main()
