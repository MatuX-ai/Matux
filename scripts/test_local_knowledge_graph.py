#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地知识图谱API测试
验证本地知识图谱服务的功能
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_local_knowledge_graph():
    """测试本地知识图谱API"""
    
    print("=== 本地知识图谱API测试 ===\n")
    
    # 1. 健康检查
    print("1. 健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/local-knowledge-graph/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✓ 服务状态: {health_data['status']}")
            print(f"   ✓ 功能特性: {', '.join(health_data['features'])}")
        else:
            print(f"   ✗ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ 连接失败: {e}")
        return False
    
    # 2. 添加知识节点
    print("\n2. 添加知识节点...")
    knowledge_nodes = [
        {
            "node_id": "python_basics_1",
            "title": "Python基础语法",
            "content": "Python是一种高级编程语言，具有简洁易读的语法。包括变量、数据类型、运算符等基础概念。",
            "knowledge_type": "concept",
            "difficulty": 0.3,
            "metadata": {"language": "python", "level": "beginner"}
        },
        {
            "node_id": "python_functions",
            "title": "Python函数",
            "content": "函数是可重用的代码块，可以接受参数并返回结果。Python使用def关键字定义函数。",
            "knowledge_type": "skill",
            "difficulty": 0.5,
            "metadata": {"language": "python", "level": "intermediate"}
        },
        {
            "node_id": "python_classes",
            "title": "Python类和对象",
            "content": "面向对象编程是Python的重要特性。类是对象的模板，对象是类的实例。",
            "knowledge_type": "concept",
            "difficulty": 0.7,
            "metadata": {"language": "python", "level": "advanced"}
        },
        {
            "node_id": "javascript_basics",
            "title": "JavaScript基础",
            "content": "JavaScript是Web开发的核心语言，用于创建交互式网页效果。",
            "knowledge_type": "concept",
            "difficulty": 0.4,
            "metadata": {"language": "javascript", "level": "beginner"}
        }
    ]
    
    for node in knowledge_nodes:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/local-knowledge-graph/nodes",
                json=node
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ 添加节点: {node['title']}")
            else:
                print(f"   ✗ 添加节点失败: {node['title']} - {response.status_code}")
        except Exception as e:
            print(f"   ✗ 添加节点异常: {node['title']} - {e}")
    
    # 3. 添加知识关系
    print("\n3. 添加知识关系...")
    knowledge_edges = [
        {
            "source_id": "python_basics_1",
            "target_id": "python_functions",
            "edge_type": "prerequisite",
            "weight": 0.9,
            "metadata": {"reason": "需要先掌握基础语法才能学习函数"}
        },
        {
            "source_id": "python_functions",
            "target_id": "python_classes",
            "edge_type": "prerequisite",
            "weight": 0.8,
            "metadata": {"reason": "函数是面向对象编程的基础"}
        }
    ]
    
    for edge in knowledge_edges:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/local-knowledge-graph/edges",
                json=edge
            )
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ 添加关系: {edge['source_id']} -> {edge['target_id']}")
            else:
                print(f"   ✗ 添加关系失败: {edge['source_id']} -> {edge['target_id']} - {response.status_code}")
        except Exception as e:
            print(f"   ✗ 添加关系异常: {e}")
    
    # 4. 获取学习路径
    print("\n4. 获取学习路径...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/local-knowledge-graph/learning-path",
            json={
                "start_node": "python_basics_1",
                "end_node": "python_classes",
                "max_difficulty": 0.8
            }
        )
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"   ✓ 学习路径长度: {result['path_length']}")
                print(f"   ✓ 路径: {' -> '.join(result['path'])}")
            else:
                print(f"   ✗ 未找到学习路径: {result['message']}")
        else:
            print(f"   ✗ 获取学习路径失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 获取学习路径异常: {e}")
    
    # 5. 语义搜索
    print("\n5. 语义搜索...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/local-knowledge-graph/search",
            json={
                "query": "Python编程基础",
                "top_k": 3
            }
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ 搜索结果数量: {len(result['results'])}")
            for i, item in enumerate(result['results'], 1):
                print(f"     {i}. {item.get('title', 'Unknown')} (相似度: {item.get('distance', 'N/A')})")
        else:
            print(f"   ✗ 搜索失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 搜索异常: {e}")
    
    # 6. 获取统计信息
    print("\n6. 获取统计信息...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/local-knowledge-graph/statistics")
        if response.status_code == 200:
            result = response.json()
            stats = result['statistics']
            print(f"   ✓ 节点总数: {stats.get('total_nodes', 0)}")
            print(f"   ✓ 边总数: {stats.get('total_edges', 0)}")
            print(f"   ✓ 知识类型: {stats.get('knowledge_types', {})}")
        else:
            print(f"   ✗ 获取统计信息失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 获取统计信息异常: {e}")
    
    # 7. 学生学习记录
    print("\n7. 记录学生学习行为...")
    student_id = "test_student_001"
    learning_records = [
        {
            "node_id": "python_basics_1",
            "performance": 0.85,
            "time_spent": 1200,
            "metadata": {"attempts": 3}
        },
        {
            "node_id": "python_functions",
            "performance": 0.72,
            "time_spent": 1800,
            "metadata": {"attempts": 5}
        }
    ]
    
    for record in learning_records:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/local-knowledge-graph/students/{student_id}/learning-record",
                json=record
            )
            if response.status_code == 200:
                print(f"   ✓ 记录学习: {record['node_id']} (表现: {record['performance']})")
            else:
                print(f"   ✗ 记录学习失败: {record['node_id']} - {response.status_code}")
        except Exception as e:
            print(f"   ✗ 记录学习异常: {e}")
    
    # 8. 获取学习进度
    print("\n8. 获取学生学习进度...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/local-knowledge-graph/students/{student_id}/progress"
        )
        if response.status_code == 200:
            result = response.json()
            progress = result['progress']
            print(f"   ✓ 已掌握节点: {len(progress.get('mastered_nodes', []))}")
            print(f"   ✓ 学习记录数: {len(progress.get('learning_history', []))}")
            print(f"   ✓ 平均表现: {progress.get('average_performance', 0):.2f}")
        else:
            print(f"   ✗ 获取学习进度失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 获取学习进度异常: {e}")
    
    # 9. 获取个性化推荐
    print("\n9. 获取个性化推荐...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/local-knowledge-graph/students/{student_id}/recommendations?top_k=3"
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ 推荐数量: {len(result['recommendations'])}")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"     {i}. {rec.get('title', 'Unknown')} (优先级: {rec.get('priority', 'N/A')})")
        else:
            print(f"   ✗ 获取推荐失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 获取推荐异常: {e}")
    
    # 10. 知识缺口分析
    print("\n10. 知识缺口分析...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/local-knowledge-graph/knowledge-gaps",
            json={
                "mastered_nodes": ["python_basics_1"],
                "target_nodes": ["python_classes"]
            }
        )
        if response.status_code == 200:
            result = response.json()
            gaps = result['gaps']
            print(f"   ✓ 知识缺口数量: {result['gap_count']}")
            if gaps:
                print(f"   ✓ 缺口节点: {', '.join(gaps)}")
            else:
                print(f"   ✓ 无知识缺口")
        else:
            print(f"   ✗ 知识缺口分析失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 知识缺口分析异常: {e}")
    
    print("\n=== 本地知识图谱API测试完成 ===")
    return True

if __name__ == "__main__":
    try:
        success = test_local_knowledge_graph()
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        exit(1)