"""测试 start_exam API 端点"""
import requests
import json

BASE_URL = "http://localhost:8002"

def get_token():
    """获取认证 token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/signin",
        data={
            "username": "test_admin",
            "password": "Admin123!"
        }
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    print(f"登录失败: {response.status_code} - {response.text}")
    return None

def test_start_exam(token):
    """测试 start_exam API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 先获取测验列表
    print("=== 获取测验列表 ===")
    response = requests.get(f"{BASE_URL}/api/v1/exams", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        exams = data.get("exams", [])
        print(f"测验数量: {len(exams)}")
        for exam in exams:
            print(f"  - ID={exam['id']}, title={exam['title']}, status={exam['status']}")
        
        if exams:
            # 测试开始第一个已发布的测验
            exam_id = exams[0]["id"]
            print(f"\n=== 开始测验 ID={exam_id} ===")
            response = requests.post(
                f"{BASE_URL}/api/v1/exams/{exam_id}/start",
                headers=headers,
                json={}
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"成功! attempt_id={data.get('attempt_id')}")
                print(f"题目数量: {len(data.get('questions', []))}")
            else:
                print(f"失败!")
                try:
                    error = response.json()
                    print(f"错误详情: {error}")
                except:
                    print(f"响应内容: {response.text}")
    else:
        print(f"获取测验列表失败: {response.text}")

def main():
    print("获取认证 token...")
    token = get_token()
    if token:
        print(f"Token 获取成功: {token[:20]}...")
        test_start_exam(token)
    else:
        print("无法获取 token")

if __name__ == "__main__":
    main()
