"""
测试 AI-Edu API 端点

这个脚本独立测试 AI-Edu 相关的 API，避免其他模块的问题
"""

import requests
import json
from pathlib import Path

# API 基础地址
API_BASE = "http://localhost:8000"

print("=" * 80)
print("AI-Edu API 测试")
print("=" * 80)

# 测试用例
test_cases = [
    {
        'name': '获取课程模块列表',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/modules',
        'expected_status': 200
    },
    {
        'name': '获取学习进度列表',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/progress',
        'expected_status': 200
    },
    {
        'name': '获取学习统计',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/progress/statistics',
        'expected_status': 200
    }
]

results = []

for test in test_cases:
    print(f"\n测试：{test['name']}")
    print(f"  方法：{test['method']}")
    print(f"  端点：{test['endpoint']}")
    
    try:
        url = f"{API_BASE}{test['endpoint']}"
        
        if test['method'] == 'GET':
            response = requests.get(url, timeout=5)
        
        status_ok = response.status_code == test['expected_status']
        status_icon = "✅" if status_ok else "❌"
        
        print(f"  {status_icon} 状态码：{response.status_code} (期望：{test['expected_status']})")
        
        if status_ok:
            try:
                data = response.json()
                print(f"  ✅ 响应格式：JSON")
                
                # 简单展示数据结构
                if isinstance(data, dict):
                    if 'data' in data:
                        if isinstance(data['data'], list):
                            print(f"  📊 数据条数：{len(data['data'])}")
                        elif isinstance(data['data'], dict):
                            print(f"  📊 数据字段：{list(data['data'].keys())[:5]}...")
                
            except json.JSONDecodeError:
                print(f"  ⚠️  响应不是 JSON 格式")
        else:
            print(f"  ❌ 响应内容：{response.text[:200]}")
        
        results.append({
            'name': test['name'],
            'success': status_ok,
            'status_code': response.status_code
        })
        
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 连接失败 - 无法连接到 {url}")
        print(f"  💡 提示：请确保后端服务已启动 (python main.py)")
        results.append({
            'name': test['name'],
            'success': False,
            'error': 'Connection failed'
        })
    except Exception as e:
        print(f"  ❌ 测试出错：{e}")
        results.append({
            'name': test['name'],
            'success': False,
            'error': str(e)
        })

# 打印摘要
print("\n" + "=" * 80)
print("测试摘要")
print("=" * 80)

passed = sum(1 for r in results if r['success'])
total = len(results)

print(f"通过：{passed}/{total}")

if passed == total:
    print("\n🎉 所有测试通过!")
else:
    print(f"\n⚠️  {total - passed} 个测试失败")

print("\n" + "=" * 80)
