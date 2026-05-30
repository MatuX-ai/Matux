"""
测试用户认证和学习进度API
"""
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000"

def test_auth_api():
    """测试认证API"""
    print("=== 测试认证API ===")

    # 1. 测试用户注册
    print("\n1. 测试用户注册...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        print(f"注册响应状态码: {response.status_code}")
        print(f"注册响应内容: {response.json()}")

        if response.status_code == 200:
            print("✅ 用户注册成功")
        else:
            print(f"❌ 用户注册失败: {response.json()}")
    except Exception as e:
        print(f"❌ 注册请求异常: {e}")

    # 2. 测试用户登录
    print("\n2. 测试用户登录...")
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", data=login_data)
        print(f"登录响应状态码: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"✅ 用户登录成功，获取到令牌")

            # 3. 测试获取当前用户信息
            print("\n3. 测试获取当前用户信息...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
            print(f"获取用户信息响应状态码: {response.status_code}")

            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ 获取用户信息成功: {user_info}")
            else:
                print(f"❌ 获取用户信息失败: {response.json()}")

            # 4. 测试登出
            print("\n4. 测试用户登出...")
            response = requests.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)
            print(f"登出响应状态码: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ 用户登出成功: {response.json()}")
            else:
                print(f"❌ 用户登出失败: {response.json()}")
        else:
            print(f"❌ 用户登录失败: {response.json()}")
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")


def test_progress_api():
    """测试学习进度API"""
    print("\n\n=== 测试学习进度API ===")

    # 首先登录获取令牌
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/token", data=login_data)
        if response.status_code != 200:
            print("❌ 无法获取访问令牌，跳过进度API测试")
            return

        token_data = response.json()
        access_token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. 测试更新学习进度
        print("\n1. 测试更新学习进度...")
        progress_data = {
            "lesson_id": 1,
            "progress_percentage": 50,
            "time_spent_seconds": 300,
            "quiz_score": 85.5,
            "code_quality_score": 90.0,
            "status": "in_progress"
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/org/1/ai-edu/progress",
            json=progress_data,
            headers=headers
        )
        print(f"更新进度响应状态码: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ 更新学习进度成功: {response.json()}")
        else:
            print(f"❌ 更新学习进度失败: {response.json()}")

        # 2. 测试获取学习进度
        print("\n2. 测试获取学习进度...")
        response = requests.get(
            f"{BASE_URL}/api/v1/org/1/ai-edu/progress",
            headers=headers
        )
        print(f"获取进度响应状态码: {response.status_code}")

        if response.status_code == 200:
            progress_list = response.json()
            print(f"✅ 获取学习进度成功，共{progress_list.get('count', 0)}条记录")
        else:
            print(f"❌ 获取学习进度失败: {response.json()}")

        # 3. 测试获取进度统计
        print("\n3. 测试获取进度统计...")
        response = requests.get(
            f"{BASE_URL}/api/v1/org/1/ai-edu/progress/statistics",
            headers=headers
        )
        print(f"获取统计响应状态码: {response.status_code}")

        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 获取进度统计成功: {stats}")
        else:
            print(f"❌ 获取进度统计失败: {response.json()}")

    except Exception as e:
        print(f"❌ 进度API测试异常: {e}")


if __name__ == "__main__":
    print("开始测试用户认证和学习进度API...")

    # 测试认证API
    test_auth_api()

    # 测试学习进度API
    test_progress_api()

    print("\n测试完成!")
