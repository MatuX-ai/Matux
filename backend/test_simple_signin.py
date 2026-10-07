"""直接测试 signin 端点"""
import requests
import traceback

BASE_URL = "http://localhost:8002"

print("=== 测试 signin ===")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/signin",
        data={"username": "test_admin", "password": "Admin123!"},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
    traceback.print_exc()
