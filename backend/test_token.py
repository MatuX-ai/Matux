"""测试使用 token 端点登录"""
import requests

BASE_URL = "http://localhost:8002"

# 使用 /api/v1/auth/token 获取 token
print("=== 测试 /api/v1/auth/token ===")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/token",
    data={
        "username": "test_admin",
        "password": "Admin123!"
    }
)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text[:500]}")

if response.status_code == 200:
    data = response.json()
    token = data.get("access_token")
    print(f"\nToken: {token[:30] if token else None}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 测试获取测验列表
    print("\n=== 获取测验列表 ===")
    response = requests.get(f"{BASE_URL}/api/v1/exams", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        exams = response.json().get("exams", [])
        print(f"测验数量: {len(exams)}")
        for exam in exams[:3]:
            print(f"  - {exam['id']}: {exam['title']}")

        if exams:
            exam_id = exams[0]["id"]
            print(f"\n=== 测试开始测验 ID={exam_id} ===")
            response = requests.post(
                f"{BASE_URL}/api/v1/exams/{exam_id}/start",
                headers=headers,
                json={}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:500]}")
    else:
        print(f"获取测验列表失败: {response.text}")
else:
    print(f"登录失败")
