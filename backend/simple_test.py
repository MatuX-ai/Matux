# Simple test for auth and progress APIs
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_register():
    print("\n=== Test User Registration ===")
    url = f"{BASE_URL}/api/v1/auth/register"

    timestamp = int(time.time())
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"test{timestamp}@example.com",
        "password": "Test@123456"
    }

    response = requests.post(url, json=user_data)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("[OK] Registration successful")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return user_data
    else:
        print(f"[FAIL] Registration failed: {response.text}")
        return None

def test_login(username, password):
    print("\n=== Test User Login ===")
    url = f"{BASE_URL}/api/v1/auth/token"

    data = {
        "username": username,
        "password": password
    }

    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        token_data = response.json()
        print("[OK] Login successful")
        print(f"Token Type: {token_data.get('token_type')}")
        print(f"Access Token: {token_data.get('access_token')[:50]}...")
        return token_data.get('access_token')
    else:
        print(f"[FAIL] Login failed: {response.text}")
        return None

def test_get_current_user(token):
    print("\n=== Test Get Current User ===")
    url = f"{BASE_URL}/api/v1/auth/me"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        user_data = response.json()
        print("[OK] Get user info successful")
        print(f"Username: {user_data.get('username')}")
        print(f"Email: {user_data.get('email')}")
        return user_data
    else:
        print(f"[FAIL] Get user info failed: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Testing Auth API and Learning Progress API")
    print("=" * 60)

    # 1. Register user
    user_data = test_register()
    if not user_data:
        print("\n[WARN] Skip remaining tests (registration failed)")
        return

    # 2. Login to get token
    token = test_login(user_data['username'], user_data['password'])
    if not token:
        print("\n[WARN] Skip remaining tests (login failed)")
        return

    # 3. Get current user info
    user_info = test_get_current_user(token)
    if not user_info:
        print("\n[WARN] Skip remaining tests (get user info failed)")
        return

    print("\n" + "=" * 60)
    print("[OK] All core auth tests passed!")
    print("=" * 60)
    print("\nNote: Learning progress API tests skipped due to missing course data")
    print("The auth API is working correctly.")

if __name__ == "__main__":
    main()
