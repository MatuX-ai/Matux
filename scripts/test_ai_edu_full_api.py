#!/usr/bin/env python3
"""
测试完整版 AI-Edu API

测试所有新增的 API 端点，包括数据库查询功能
"""

import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 80)
print("AI-Edu 完整版 API 测试")
print("=" * 80)

# 测试用例
test_cases = [
    {
        'name': '获取课程模块列表 (真实数据库)',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/modules',
        'expected_status': 200
    },
    {
        'name': '获取模块的课时列表',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/modules/2/lessons',
        'expected_status': 200
    },
    {
        'name': '获取用户学习进度',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/progress?user_id=1',
        'expected_status': 200
    },
    {
        'name': '获取学习统计数据',
        'method': 'GET',
        'endpoint': '/api/v1/org/1/ai-edu/progress/statistics?user_id=1',
        'expected_status': 200
    },
    {
        'name': '更新学习进度 (POST)',
        'method': 'POST',
        'endpoint': '/api/v1/org/1/ai-edu/progress?user_id=1',
        'data': {
            'lesson_id': 1,
            'progress_percentage': 50,
            'time_spent_seconds': 600,
            'status': 'in_progress'
        },
        'expected_status': 200
    },
    {
        'name': '完成课程并获得积分',
        'method': 'POST',
        'endpoint': '/api/v1/org/1/ai-edu/progress/complete?user_id=1',
        'data': {
            'lesson_id': 1,
            'quiz_score': 85,
            'time_spent_seconds': 900
        },
        'expected_status': 200
    }
]

results = []

for i, test in enumerate(test_cases, 1):
    print(f"\n测试 {i}/{len(test_cases)}: {test['name']}")
    print(f"  方法：{test['method']}")
    print(f"  端点：{test['endpoint']}")
    
    try:
        url = f"{API_BASE}{test['endpoint']}"
        
        if test['method'] == 'GET':
            response = requests.get(url, timeout=5)
        elif test['method'] == 'POST':
            response = requests.post(url, json=test.get('data', {}), timeout=5)
        
        status_ok = response.status_code == test['expected_status']
        status_icon = "✅" if status_ok else "❌"
        
        print(f"  {status_icon} 状态码：{response.status_code} (期望：{test['expected_status']})")
        
        if status_ok:
            try:
                data = response.json()
                print(f"  ✅ 响应格式：JSON")
                
                # 智能展示响应数据
                if isinstance(data, dict):
                    if 'success' in data:
                        print(f"  📊 业务状态：{'成功' if data['success'] else '失败'}")
                    
                    if 'data' in data:
                        if isinstance(data['data'], list):
                            print(f"  📊 数据条数：{len(data['data'])}")
                            if len(data['data']) > 0:
                                print(f"  📄 首条数据：{json.dumps(data['data'][0], ensure_ascii=False)[:100]}...")
                        elif isinstance(data['data'], dict):
                            print(f"  📊 统计字段：{list(data['data'].keys())[:5]}...")
                            
                            # 特殊处理统计数据
                            if 'total_courses' in data['data']:
                                stats = data['data']
                                print(f"     - 总课程：{stats.get('total_courses', 0)}")
                                print(f"     - 已完成：{stats.get('completed_courses', 0)}")
                                print(f"     - 进行中：{stats.get('in_progress_courses', 0)}")
                                print(f"     - 总积分：{stats.get('total_points', 0)}")
                    
                    if 'points_earned' in data:
                        print(f"  🎁 获得积分：{data['points_earned']}")
                    
                    if 'breakdown' in data:
                        breakdown = data['breakdown']
                        print(f"  📊 积分明细:")
                        print(f"     - 基础积分：{breakdown.get('base_points', 0)}")
                        print(f"     - 质量奖励：{breakdown.get('quality_bonus', 0)}")
                        print(f"     - 时间奖励：{breakdown.get('time_bonus', 0)}")
                        print(f"     - 总计：{breakdown.get('total', 0)}")
                
            except json.JSONDecodeError:
                print(f"  ⚠️  响应不是 JSON 格式")
                print(f"  响应内容：{response.text[:200]}")
        else:
            print(f"  ❌ 响应内容：{response.text[:200]}")
        
        results.append({
            'name': test['name'],
            'success': status_ok,
            'status_code': response.status_code,
            'response_preview': str(response.json())[:100] if status_ok else response.text[:100]
        })
        
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 连接失败 - 无法连接到 {url}")
        print(f"  💡 提示：请确保后端服务已启动 (python main_ai_edu_full.py)")
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
print(f"通过率：{(passed/total*100):.1f}%\n")

if passed == total:
    print("🎉 所有测试通过!")
else:
    print(f"⚠️  {total - passed} 个测试失败")
    print("\n失败详情:")
    for i, r in enumerate(results, 1):
        if not r['success']:
            print(f"  {i}. {r['name']}")
            if 'error' in r:
                print(f"     错误：{r['error']}")

print("\n" + "=" * 80)
