import time
import requests
import json

BASE = "http://localhost:8002/api/v1/auth"

# Test 1: /signin endpoint
print("=== Test 1: POST /signin ===")
r = requests.post(
    f"{BASE}/signin",
    json={"email": "nonexistent@test.com", "password": "wrong"},
    timeout=5
)
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:200]}")
print()

# Test 2: /signup endpoint
print("=== Test 2: POST /signup ===")
test_email = f"test_{int(time.time())}@test.com"
r = requests.post(
    f"{BASE}/signup",
    json={"email": test_email, "password": "Test123456", "username": "testuser"},
    timeout=5
)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response keys: {list(data.keys())}")
    print(f"accessToken: {'present' if 'accessToken' in data else 'MISSING'}")
    print(
        f"refreshToken: {'present' if 'refreshToken' in data else 'MISSING'}")
    print(f"user: {'present' if 'user' in data else 'MISSING'}")
    if 'user' in data:
        print(f"  user.email: {data['user'].get('email', 'N/A')}")
    # Save token for refresh test
    refresh_token = data.get('refreshToken', '')
    access_token = data.get('accessToken', '')
else:
    print(f"Body: {r.text[:300]}")
    access_token = ""
    refresh_token = ""
print()

# Test 3: /refresh endpoint
if refresh_token:
    print("=== Test 3: POST /refresh ===")
    r = requests.post(
        f"{BASE}/refresh",
        json={"refreshToken": refresh_token},
        timeout=5
    )
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:200]}")
else:
    print("=== Test 3: SKIPPED (no refresh token) ===")
print()

print("=== All tests completed ===")
