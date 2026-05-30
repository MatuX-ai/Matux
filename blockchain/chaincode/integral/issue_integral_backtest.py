#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
积分链码IssueIntegral功能回测脚本
验证权限控制、数据持久化和业务逻辑正确性
"""

import json
import subprocess
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class IssueIntegralBacktest:
    """IssueIntegral功能回测类"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = datetime.now()
        
    def log_result(self, test_name: str, status: str, message: str, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == "PASS":
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
            if details:
                print(f"   详情: {details}")
    
    def run_docker_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """执行Docker命令"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)
    
    def check_fabric_network(self) -> bool:
        """检查Fabric网络状态"""
        test_name = "Fabric网络状态检查"
        try:
            # 检查必要的容器是否运行
            containers = [
                "peer0.education.imatu.com",
                "peer0.school.imatu.com", 
                "peer0.enterprise.imatu.com",
                "orderer.example.com",
                "cli"
            ]
            
            running_containers = []
            returncode, stdout, stderr = self.run_docker_command(["docker", "ps", "--format", "{{.Names}}"])
            
            if returncode == 0:
                running_containers = stdout.split('\n') if stdout else []
            
            missing_containers = [c for c in containers if c not in running_containers]
            
            if missing_containers:
                self.log_result(test_name, "FAIL", 
                              f"缺少必要容器: {missing_containers}")
                return False
            else:
                self.log_result(test_name, "PASS", 
                              f"所有必要容器运行正常: {len(containers)}个")
                return True
                
        except Exception as e:
            self.log_result(test_name, "FAIL", f"网络检查异常: {str(e)}")
            return False
    
    def test_permission_control(self) -> bool:
        """测试权限控制功能"""
        test_name = "权限控制验证"
        
        # 测试教育局权限（应该成功）
        edu_env = [
            "CORE_PEER_TLS_ENABLED=true",
            "CORE_PEER_LOCALMSPID=EducationBureauMSP",
            "CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt",
            "CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp",
            "CORE_PEER_ADDRESS=peer0.education.imatu.com:7051"
        ]
        
        edu_cmd = ["docker", "exec", "cli"] + edu_env + [
            "peer", "chaincode", "invoke",
            "-o", "orderer.example.com:7050",
            "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
            "-C", "imatu-channel",
            "-n", "integral",
            "-c", '{"function":"IssueIntegral","Args":["student_edu_test","100"]}'
        ]
        
        returncode, stdout, stderr = self.run_docker_command(edu_cmd)
        
        if returncode == 0:
            self.log_result(f"{test_name} - 教育局权限", "PASS", "教育局成功发行积分")
        else:
            self.log_result(f"{test_name} - 教育局权限", "FAIL", 
                          "教育局发行积分失败", stderr)
            return False
        
        # 测试学校权限（应该失败）
        school_env = [
            "CORE_PEER_TLS_ENABLED=true",
            "CORE_PEER_LOCALMSPID=SchoolMSP",
            "CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/peers/peer0.school.imatu.com/tls/ca.crt",
            "CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/school.imatu.com/users/Admin@school.imatu.com/msp",
            "CORE_PEER_ADDRESS=peer0.school.imatu.com:9051"
        ]
        
        school_cmd = ["docker", "exec", "cli"] + school_env + [
            "peer", "chaincode", "invoke",
            "-o", "orderer.example.com:7050",
            "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
            "-C", "imatu-channel",
            "-n", "integral",
            "-c", '{"function":"IssueIntegral","Args":["student_school_test","100"]}'
        ]
        
        returncode, stdout, stderr = self.run_docker_command(school_cmd)
        
        if returncode != 0 and "权限不足" in stderr:
            self.log_result(f"{test_name} - 学校权限", "PASS", "学校被正确拒绝权限")
            return True
        else:
            self.log_result(f"{test_name} - 学校权限", "FAIL", 
                          "学校权限控制失效", stderr)
            return False
    
    def test_data_persistence(self) -> bool:
        """测试数据持久化功能"""
        test_name = "数据持久化验证"
        
        # 发行积分
        student_id = f"student_persist_{int(time.time())}"
        amount = "200"
        
        issue_env = [
            "CORE_PEER_TLS_ENABLED=true",
            "CORE_PEER_LOCALMSPID=EducationBureauMSP",
            "CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt",
            "CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp",
            "CORE_PEER_ADDRESS=peer0.education.imatu.com:7051"
        ]
        
        # 发行积分
        issue_cmd = ["docker", "exec", "cli"] + issue_env + [
            "peer", "chaincode", "invoke",
            "-o", "orderer.example.com:7050",
            "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
            "-C", "imatu-channel",
            "-n", "integral",
            "-c", f'{{"function":"IssueIntegral","Args":["{student_id}","{amount}"]}}'
        ]
        
        returncode, stdout, stderr = self.run_docker_command(issue_cmd)
        
        if returncode != 0:
            self.log_result(test_name, "FAIL", "积分发行失败", stderr)
            return False
        
        # 等待区块确认
        time.sleep(2)
        
        # 查询余额验证持久化
        query_cmd = ["docker", "exec", "cli"] + issue_env + [
            "peer", "chaincode", "query",
            "-C", "imatu-channel",
            "-n", "integral",
            "-c", f'{{"function":"GetStudentBalance","Args":["{student_id}"]}}'
        ]
        
        returncode, stdout, stderr = self.run_docker_command(query_cmd)
        
        if returncode == 0 and stdout:
            try:
                balance_data = json.loads(stdout)
                if balance_data.get("total_amount") == int(amount):
                    self.log_result(test_name, "PASS", 
                                  f"数据持久化成功，余额: {balance_data['total_amount']}")
                    return True
                else:
                    self.log_result(test_name, "FAIL", 
                                  f"余额不匹配，期望: {amount}, 实际: {balance_data.get('total_amount')}")
                    return False
            except json.JSONDecodeError:
                self.log_result(test_name, "FAIL", "余额数据格式错误", stdout)
                return False
        else:
            self.log_result(test_name, "FAIL", "查询余额失败", stderr)
            return False
    
    def test_business_logic(self) -> bool:
        """测试业务逻辑正确性"""
        test_name = "业务逻辑验证"
        
        student_id = f"student_logic_{int(time.time())}"
        
        # 多次发行积分
        amounts = [100, 150, 75]
        total_expected = sum(amounts)
        
        issue_env = [
            "CORE_PEER_TLS_ENABLED=true",
            "CORE_PEER_LOCALMSPID=EducationBureauMSP",
            "CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt",
            "CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp",
            "CORE_PEER_ADDRESS=peer0.education.imatu.com:7051"
        ]
        
        # 逐次发行积分
        for i, amount in enumerate(amounts):
            issue_cmd = ["docker", "exec", "cli"] + issue_env + [
                "peer", "chaincode", "invoke",
                "-o", "orderer.example.com:7050",
                "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
                "-C", "imatu-channel",
                "-n", "integral",
                "-c", f'{{"function":"IssueIntegral","Args":["{student_id}","{amount}"]}}'
            ]
            
            returncode, stdout, stderr = self.run_docker_command(issue_cmd)
            if returncode != 0:
                self.log_result(f"{test_name} - 第{i+1}次发行", "FAIL", 
                              f"发行失败: {amount}积分", stderr)
                return False
            
            time.sleep(1)  # 等待区块确认
        
        # 查询最终余额
        query_cmd = ["docker", "exec", "cli"] + issue_env + [
            "peer", "chaincode", "query",
            "-C", "imatu-channel",
            "-n", "integral",
            "-c", f'{{"function":"GetStudentBalance","Args":["{student_id}"]}}'
        ]
        
        returncode, stdout, stderr = self.run_docker_command(query_cmd)
        
        if returncode == 0 and stdout:
            try:
                balance_data = json.loads(stdout)
                actual_balance = balance_data.get("total_amount", 0)
                
                if actual_balance == total_expected:
                    self.log_result(test_name, "PASS", 
                                  f"业务逻辑正确，累计余额: {actual_balance}")
                    return True
                else:
                    self.log_result(test_name, "FAIL", 
                                  f"余额计算错误，期望: {total_expected}, 实际: {actual_balance}")
                    return False
            except json.JSONDecodeError:
                self.log_result(test_name, "FAIL", "余额数据解析失败", stdout)
                return False
        else:
            self.log_result(test_name, "FAIL", "查询余额失败", stderr)
            return False
    
    def test_edge_cases(self) -> bool:
        """测试边界条件"""
        test_name = "边界条件测试"
        
        issue_env = [
            "CORE_PEER_TLS_ENABLED=true",
            "CORE_PEER_LOCALMSPID=EducationBureauMSP",
            "CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/peers/peer0.education.imatu.com/tls/ca.crt",
            "CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/peerOrganizations/education.imatu.com/users/Admin@education.imatu.com/msp",
            "CORE_PEER_ADDRESS=peer0.education.imatu.com:7051"
        ]
        
        edge_cases = [
            {
                "name": "零积分发行",
                "student_id": "student_zero",
                "amount": "0",
                "should_fail": True
            },
            {
                "name": "负积分发行", 
                "student_id": "student_negative",
                "amount": "-50",
                "should_fail": True
            },
            {
                "name": "空学生ID",
                "student_id": "",
                "amount": "100",
                "should_fail": True
            }
        ]
        
        all_passed = True
        
        for case in edge_cases:
            issue_cmd = ["docker", "exec", "cli"] + issue_env + [
                "peer", "chaincode", "invoke",
                "-o", "orderer.example.com:7050",
                "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/crypto/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
                "-C", "imatu-channel",
                "-n", "integral",
                "-c", f'{{"function":"IssueIntegral","Args":["{case["student_id"]}","{case["amount"]}"]}}'
            ]
            
            returncode, stdout, stderr = self.run_docker_command(issue_cmd)
            
            if case["should_fail"]:
                if returncode != 0:
                    self.log_result(f"{test_name} - {case['name']}", "PASS", "正确拒绝无效请求")
                else:
                    self.log_result(f"{test_name} - {case['name']}", "FAIL", 
                                  "未拒绝无效请求", stdout)
                    all_passed = False
            else:
                if returncode == 0:
                    self.log_result(f"{test_name} - {case['name']}", "PASS", "成功处理有效请求")
                else:
                    self.log_result(f"{test_name} - {case['name']}", "FAIL", 
                                  "处理有效请求失败", stderr)
                    all_passed = False
        
        return all_passed
    
    def generate_report(self) -> Dict:
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "test_suite": "IssueIntegral功能回测",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": len(self.test_results),
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": round(self.passed_tests / len(self.test_results) * 100, 2) if self.test_results else 0,
            "results": self.test_results
        }
        
        return report
    
    def run_full_backtest(self) -> Dict:
        """执行完整的回测"""
        print("🚀 开始IssueIntegral功能回测...")
        print("=" * 50)
        
        # 执行各项测试
        tests = [
            ("网络状态检查", self.check_fabric_network),
            ("权限控制验证", self.test_permission_control),
            ("数据持久化验证", self.test_data_persistence),
            ("业务逻辑验证", self.test_business_logic),
            ("边界条件测试", self.test_edge_cases)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 执行测试: {test_name}")
            try:
                result = test_func()
                if not result:
                    print(f"⚠️  测试 {test_name} 未完全通过")
            except Exception as e:
                self.log_result(test_name, "FAIL", f"测试执行异常: {str(e)}")
                print(f"❌ 测试 {test_name} 异常: {str(e)}")
        
        # 生成报告
        report = self.generate_report()
        
        print("\n" + "=" * 50)
        print("📊 回测结果汇总:")
        print(f"   总测试数: {report['total_tests']}")
        print(f"   通过测试: {report['passed_tests']}")
        print(f"   失败测试: {report['failed_tests']}")
        print(f"   通过率: {report['pass_rate']}%")
        print(f"   执行耗时: {report['duration_seconds']:.2f}秒")
        
        if report['failed_tests'] == 0:
            print("🎉 所有测试通过！IssueIntegral功能验证成功！")
        else:
            print("⚠️  部分测试失败，请检查上述错误信息")
        
        return report

def main():
    """主函数"""
    backtester = IssueIntegralBacktest()
    report = backtester.run_full_backtest()
    
    # 保存详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"issue_integral_backtest_{timestamp}.json"
    
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细报告已保存至: {report_filename}")
    except Exception as e:
        print(f"\n⚠️  报告保存失败: {str(e)}")
    
    # 根据测试结果返回退出码
    sys.exit(1 if report['failed_tests'] > 0 else 0)

if __name__ == "__main__":
    main()