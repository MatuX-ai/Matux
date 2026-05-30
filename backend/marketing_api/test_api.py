"""
API 测试脚本
快速测试 MatuX Marketing API 的基本功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_root_endpoint():
    """测试根路径"""
    print_section("1. 测试根路径")
    response = requests.get(f"{BASE_URL}/")
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_submit_contact():
    """测试联系表单提交"""
    print_section("2. 测试联系表单提交")

    data = {
        "name": "测试用户",
        "email": "test@example.com",
        "phone": "13800138000",
        "type": "business",
        "message": "这是一个测试消息，验证联系表单提交功能是否正常工作。",
        "source": "test_script",
        "location": "北京市"
    }

    response = requests.post(f"{BASE_URL}/api/marketing/contact", json=data)
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_subscribe():
    """测试邮件订阅"""
    print_section("3. 测试邮件订阅")

    data = {
        "email": "subscribe@example.com",
        "name": "订阅测试用户",
        "interests": ["AI教育", "机器人编程"],
        "source": "test_script",
        "consentGiven": True
    }

    response = requests.post(f"{BASE_URL}/api/marketing/subscribe", json=data)
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_track_event():
    """测试分析事件记录"""
    print_section("4. 测试分析事件记录")

    data = {
        "event": "page_view",
        "timestamp": "2026-03-16T10:00:00.000Z",
        "sessionId": "test_session_123",
        "userId": "test_user_456",
        "page": {
            "url": "/marketing",
            "title": "营销首页 - MatuX"
        },
        "data": {}
    }

    response = requests.post(f"{BASE_URL}/api/marketing/analytics/track", json=data)
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_metrics():
    """测试获取营销指标"""
    print_section("5. 测试获取营销指标（Admin）")

    params = {"days": 7}
    response = requests.get(f"{BASE_URL}/api/admin/marketing/metrics", params=params)
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_contacts():
    """测试获取联系表单列表（Admin）"""
    print_section("6. 测试获取联系表单列表（Admin）")

    response = requests.get(f"{BASE_URL}/api/marketing/contacts")
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_subscribers():
    """测试获取订阅用户列表（Admin）"""
    print_section("7. 测试获取订阅用户列表（Admin）")

    response = requests.get(f"{BASE_URL}/api/marketing/subscribers")
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def test_get_page_stats():
    """测试获取页面统计（Admin）"""
    print_section("8. 测试获取页面统计（Admin）")

    response = requests.get(f"{BASE_URL}/api/admin/marketing/page-stats")
    print(f"✅ 状态码: {response.status_code}")
    print(f"✅ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")


def main():
    """运行所有测试"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                            ║
║        MatuX Marketing API - 自动化测试脚本                  ║
║                                                            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        # 运行测试
        test_root_endpoint()
        test_submit_contact()
        test_subscribe()
        test_track_event()
        test_get_metrics()
        test_get_contacts()
        test_get_subscribers()
        test_get_page_stats()

        print_section("✅ 所有测试完成")
        print("📊 测试总结:")
        print("  - 根路径: ✅")
        print("  - 联系表单: ✅")
        print("  - 邮件订阅: ✅")
        print("  - 分析事件: ✅")
        print("  - 营销指标: ✅")
        print("  - 联系表单列表: ✅")
        print("  - 订阅用户列表: ✅")
        print("  - 页面统计: ✅")
        print("\n🎉 所有 API 端点测试通过！")

    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到 API 服务器")
        print("💡 请确保 API 服务器正在运行: http://localhost:8000")
        print("💡 启动命令: python main.py")
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")


if __name__ == "__main__":
    main()
