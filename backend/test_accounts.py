"""测试不同账号"""
import requests

BASE_URL = "http://localhost:8002"

# 测试不同账号
accounts = [
    ("test_admin", "Admin123!", "Admin"),
    ("testuser", "Test123!", "testuser"),
    ("test_student", "Test123!", "test_student"),
    ("admin@testorg.com", "Admin123!", "admin email"),
]

for username, password, desc in accounts:
    print(f"\n=== 测试 {desc} ===")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/token",
        data={"username": username, "password": password}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"Token: {token[:30]}...")
        print(f"登录成功!")

        # 测试 start_exam
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/exams", headers=headers)
        if response.status_code == 200:
            exams = response.json().get("exams", [])
            print(f"测验数量: {len(exams)}")
            if exams:
                exam_id = exams[0]["id"]
                print(f"测试开始测验 ID={exam_id}...")
                response = requests.post(
                    f"{BASE_URL}/api/v1/exams/{exam_id}/start",
                    headers=headers, json={}
                )
                print(f"start_exam Status: {response.status_code}")
                print(f"start_exam Response: {response.text[:300]}")
        break
    else:
        print(f"失败: {response.text[:100]}")
