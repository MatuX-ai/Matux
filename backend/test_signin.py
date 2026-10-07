"""测试 signin API"""
import requests

BASE_URL = "http://localhost:8002"

# 测试登录
print("=== 测试登录 ===")
response = requests.post(
    f"{BASE_URL}/api/v1/auth/signin",
    data={
        "username": "test_admin",
        "password": "Admin123!"
    }
)
print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")

if response.status_code == 200:
    data = response.json()
    token = data.get("access_token")
    print(f"Token: {token[:30] if token else None}...")

    # 测试 start_exam
    print("\n=== 测试获取测验列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/exams", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        exams = response.json().get("exams", [])
        print(f"测验数量: {len(exams)}")

        if exams:
            exam_id = exams[0]["id"]
            print(f"\n=== 测试开始测验 ID={exam_id} ===")
            response = requests.post(
                f"{BASE_URL}/api/v1/exams/{exam_id}/start",
                headers=headers,
                json={}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
