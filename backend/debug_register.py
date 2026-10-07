"""调试注册端点"""
import requests
import traceback

BASE_URL = "http://localhost:8002"

print("=== 调试注册 ===")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "username": "test_debug_user",
            "email": "debug@test.com",
            "password": "Test123!"
        },
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code >= 400:
        print(f"\n详细错误:")
        try:
            error_data = response.json()
            print(error_data)
        except:
            print(response.text)
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
