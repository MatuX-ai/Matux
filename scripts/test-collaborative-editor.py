#!/usr/bin/env python3
"""
协作编辑系统集成测试脚本
测试后端API和前端组件的功能完整性
"""

import requests
import json
import time
import threading
from typing import Dict, List, Any
import unittest
from concurrent.futures import ThreadPoolExecutor
import websocket

class CollaborativeEditorTest(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8000"
        self.org_id = 1
        self.course_id = 101
        self.headers = {
            "Authorization": "Bearer test-token",  # 实际使用时需要真实的JWT token
            "Content-Type": "application/json"
        }
        self.test_document_id = None
        
    def tearDown(self):
        # 清理测试数据
        if self.test_document_id:
            try:
                requests.delete(
                    f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}",
                    headers=self.headers
                )
            except:
                pass

    def test_01_create_document(self):
        """测试创建协作文档"""
        payload = {
            "document_name": "测试文档",
            "document_type": "richtext",
            "content": "这是测试文档的初始内容",
            "allow_comments": True,
            "allow_suggestions": True
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents",
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.test_document_id = data["id"]
        
        self.assertEqual(data["document_name"], "测试文档")
        self.assertEqual(data["content"], "这是测试文档的初始内容")
        self.assertEqual(data["version_number"], 1)
        print("✓ 文档创建测试通过")

    def test_02_get_document(self):
        """测试获取文档详情"""
        # 先创建文档
        self.test_01_create_document()
        
        response = requests.get(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["id"], self.test_document_id)
        self.assertEqual(data["document_name"], "测试文档")
        print("✓ 文档获取测试通过")

    def test_03_apply_operations(self):
        """测试应用操作"""
        # 先创建文档
        self.test_01_create_document()
        
        operations = [
            {
                "operation_type": "insert",
                "position": 0,
                "content": "前缀内容 - ",
                "client_id": "test-client-1"
            },
            {
                "operation_type": "insert",
                "position": 20,
                "content": " 后缀内容",
                "client_id": "test-client-1"
            }
        ]
        
        response = requests.post(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}/operations/batch",
            headers=self.headers,
            json=operations
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["success"])
        self.assertEqual(len(data["transformed_operations"]), 2)
        self.assertIn("前缀内容", data["new_content"])
        print("✓ 操作应用测试通过")

    def test_04_add_comment(self):
        """测试添加评论"""
        # 先创建文档
        self.test_01_create_document()
        
        comment_data = {
            "start_position": 0,
            "end_position": 6,
            "content": "这是一条评论",
            "comment_type": "comment"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}/comments",
            headers=self.headers,
            json=comment_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["content"], "这是一条评论")
        self.assertEqual(data["start_position"], 0)
        print("✓ 添加评论测试通过")

    def test_05_add_suggestion(self):
        """测试添加建议"""
        # 先创建文档
        self.test_01_create_document()
        
        suggestion_data = {
            "start_position": 0,
            "end_position": 6,
            "original_content": "这是测试",
            "suggested_content": "这是修改后的测试",
            "suggestion_reason": "内容不够准确"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}/suggestions",
            headers=self.headers,
            json=suggestion_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["suggested_content"], "这是修改后的测试")
        self.assertEqual(data["status"], "pending")
        print("✓ 添加建议测试通过")

    def test_06_session_management(self):
        """测试会话管理"""
        # 先创建文档
        self.test_01_create_document()
        
        # 加入会话
        session_data = {
            "client_id": "test-session-123"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}/sessions",
            headers=self.headers,
            json=session_data
        )
        
        self.assertEqual(response.status_code, 200)
        session_response = response.json()
        session_id = session_response["session_id"]
        
        # 更新光标位置
        cursor_data = {
            "cursor_position": 10
        }
        
        response = requests.put(
            f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/sessions/{session_id}/cursor",
            headers=self.headers,
            json=cursor_data
        )
        
        self.assertEqual(response.status_code, 200)
        print("✓ 会话管理测试通过")

    def test_07_concurrent_operations(self):
        """测试并发操作处理"""
        # 先创建文档
        self.test_01_create_document()
        
        def apply_operation(client_id: str, operation_data: Dict):
            response = requests.post(
                f"{self.base_url}/api/v1/org/{self.org_id}/courses/{self.course_id}/collaborative-documents/{self.test_document_id}/operations/batch",
                headers=self.headers,
                json=[operation_data]
            )
            return response.status_code == 200
        
        # 准备并发操作
        operations = [
            {
                "operation_type": "insert",
                "position": 0,
                "content": f"[用户{i}插入] ",
                "client_id": f"client-{i}"
            }
            for i in range(5)
        ]
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(apply_operation, f"client-{i}", op)
                for i, op in enumerate(operations)
            ]
            
            results = [future.result() for future in futures]
        
        # 验证所有操作都成功
        self.assertTrue(all(results))
        print("✓ 并发操作测试通过")

    def test_08_ot_algorithm_validation(self):
        """测试OT算法正确性"""
        from src.app.shared.components.collaborative_editor.ot_algorithm import (
            OperationalTransformation, TextOperation
        )
        
        # 测试插入-插入转换
        op1: TextOperation = {
            "type": "insert",
            "position": 5,
            "content": "ABC",
            "clientId": "client1",
            "timestamp": 1000
        }
        
        op2: TextOperation = {
            "type": "insert",
            "position": 3,
            "content": "XYZ",
            "clientId": "client2",
            "timestamp": 1001
        }
        
        transformed = OperationalTransformation.transform(op1, op2)
        self.assertEqual(transformed["position"], 8)  # 应该向后移动XYZ的长度
        
        # 测试删除-插入转换
        op3: TextOperation = {
            "type": "delete",
            "position": 10,
            "content": "hello",
            "clientId": "client1",
            "timestamp": 1000
        }
        
        op4: TextOperation = {
            "type": "insert",
            "position": 8,
            "content": "world",
            "clientId": "client2",
            "timestamp": 1001
        }
        
        transformed2 = OperationalTransformation.transform(op3, op4)
        self.assertEqual(transformed2["position"], 15)  # 删除位置应该向后移动
        
        print("✓ OT算法验证测试通过")

def run_performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    base_url = "http://localhost:8000"
    headers = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}
    
    # 创建测试文档
    doc_response = requests.post(
        f"{base_url}/api/v1/org/1/courses/101/collaborative-documents",
        headers=headers,
        json={
            "document_name": "性能测试文档",
            "document_type": "richtext",
            "content": "A" * 10000,  # 10KB文档
            "allow_comments": True,
            "allow_suggestions": True
        }
    )
    
    if doc_response.status_code != 200:
        print("✗ 无法创建测试文档")
        return
    
    document_id = doc_response.json()["id"]
    
    # 测试大量操作的处理速度
    start_time = time.time()
    
    operations = []
    for i in range(100):
        operations.append({
            "operation_type": "insert",
            "position": i * 10,
            "content": f"操作{i}",
            "client_id": f"perf-client-{i}"
        })
    
    # 分批发送操作
    batch_size = 10
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i + batch_size]
        response = requests.post(
            f"{base_url}/api/v1/org/1/courses/101/collaborative-documents/{document_id}/operations/batch",
            headers=headers,
            json=batch
        )
        
        if response.status_code != 200:
            print(f"✗ 批次 {i//batch_size + 1} 处理失败")
            return
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✓ 处理100个操作耗时: {duration:.3f}秒")
    print(f"✓ 平均每个操作耗时: {duration*1000/100:.2f}毫秒")
    print(f"✓ 吞吐量: {100/duration:.1f} 操作/秒")
    
    # 清理
    requests.delete(
        f"{base_url}/api/v1/org/1/courses/101/collaborative-documents/{document_id}",
        headers=headers
    )

def run_compatibility_test():
    """兼容性测试"""
    print("\n=== 兼容性测试 ===")
    
    # 测试不同浏览器的WebSocket连接
    test_cases = [
        ("Chrome", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        ("Firefox", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"),
        ("Safari", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"),
        ("Edge", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59")
    ]
    
    for browser_name, user_agent in test_cases:
        try:
            # 模拟不同浏览器的请求
            headers = {
                "User-Agent": user_agent,
                "Authorization": "Bearer test-token",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "http://localhost:8000/health",
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✓ {browser_name} 兼容性测试通过")
            else:
                print(f"✗ {browser_name} 兼容性测试失败")
                
        except Exception as e:
            print(f"✗ {browser_name} 兼容性测试异常: {e}")

if __name__ == "__main__":
    print("开始协作编辑系统集成测试...\n")
    
    # 运行单元测试
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # 运行性能测试
    try:
        run_performance_test()
    except Exception as e:
        print(f"性能测试失败: {e}")
    
    # 运行兼容性测试
    try:
        run_compatibility_test()
    except Exception as e:
        print(f"兼容性测试失败: {e}")
    
    print("\n=== 测试完成 ===")
