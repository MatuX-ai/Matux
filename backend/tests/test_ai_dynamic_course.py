"""
动态课程生成服务单元测试
测试AI驱动的个性化课程生成功能
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from ai_service.dynamic_course import (
    DynamicCourseGenerator,
    DynamicCourseRequest,
    StudentProfile,
)
from main import app

client = TestClient(app)


@pytest.fixture
def mock_user_token():
    """模拟用户认证令牌"""
    return "mock_jwt_token"


@pytest.fixture
def mock_course_request():
    """模拟课程生成请求"""
    return {
        "student_profile": {
            "grade": 8,
            "age": 14,
            "learning_style": "动手型",
            "prior_knowledge": ["基础电路知识", "简单编程"],
            "interests": ["机器人", "电子制作"],
            "learning_goals": ["理解传感器原理", "掌握基本编程"],
        },
        "subject_area": "信息技术",
        "learning_objectives": ["掌握Arduino编程", "理解传感器应用"],
        "difficulty_level": "中级",
        "project_type": "实践项目",
        "time_constraint": 10,
    }


@pytest.fixture
def mock_openai_response():
    """模拟OpenAI响应"""
    return {
        "content": """# 光敏传感器智能浇水系统

这是一个为初中生设计的基于光敏传感器的自动浇水项目。

## 学习成果
- 理解光敏传感器的工作原理
- 掌握Arduino基础编程
- 学会设计简单的自动控制系统

## 项目组件

### 组件1：项目介绍与准备
- 时长：30分钟
- 材料：电脑、Arduino开发板、光敏传感器模块
- 步骤：了解项目背景、准备硬件设备、安装开发环境

### 组件2：电路连接与测试
- 时长：45分钟
- 材料：面包板、杜邦线、LED指示灯
- 步骤：连接光敏传感器、测试传感器读数、调试电路

### 组件3：程序编写与上传
- 时长：60分钟
- 材料：Arduino IDE软件
- 步骤：编写控制程序、上传到开发板、测试功能

## 所需材料
- Arduino Uno开发板 x1
- 光敏传感器模块 x1
- 面包板 x1
- 杜邦线若干
- 小水泵或LED指示灯 x1
- USB数据线 x1

## 总时长
预计完成时间：135分钟（约2.25小时）

## 难度评估
适中 - 适合有一定电子和编程基础的初中生

## 先修知识
- 基础电路连接知识
- 简单的C语言编程概念

## 评估方法
- 项目功能演示
- 代码质量检查
- 学习过程记录""",
        "tokens_used": 847,
        "model": "gpt-3.5-turbo",
    }


class TestDynamicCourseGenerator:
    """动态课程生成器测试"""

    def test_init_success(self):
        """测试初始化成功"""
        with patch("backend.ai_service.dynamic_course.AsyncOpenAI") as mock_openai:
            generator = DynamicCourseGenerator()
            assert generator.client is not None
            assert len(generator.course_templates) > 0
            assert generator.model == "gpt-3.5-turbo"

    def test_load_course_templates(self):
        """测试课程模板加载"""
        generator = DynamicCourseGenerator()
        templates = generator.course_templates

        assert len(templates) >= 4
        template_ids = [t.template_id for t in templates]
        assert "light_sensor_project" in template_ids
        assert "arduino_basics" in template_ids
        assert "python_programming" in template_ids
        assert "stem_innovation" in template_ids

    def test_select_template_success(self):
        """测试模板选择成功"""
        generator = DynamicCourseGenerator()

        request = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=8,
                age=14,
                learning_style="动手型",
                prior_knowledge=[],
                interests=[],
                learning_goals=[],
            ),
            subject_area="信息技术",
            learning_objectives=["测试目标"],
            difficulty_level="中级",
            project_type="实践项目",
            time_constraint=10,
        )

        template = generator._select_template(request)
        assert template is not None
        assert template.template_id == "light_sensor_project"

    def test_select_template_no_match(self):
        """测试无匹配模板时的处理"""
        generator = DynamicCourseGenerator()

        request = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=1,
                age=7,
                learning_style="视觉型",
                prior_knowledge=[],
                interests=[],
                learning_goals=[],
            ),
            subject_area="艺术",
            learning_objectives=["测试目标"],
            difficulty_level="专家级",
            project_type="理论研究",
            time_constraint=100,
        )

        template = generator._select_template(request)
        # 应该返回默认模板而不是None
        assert template is not None

    def test_build_prompt(self):
        """测试提示词构建"""
        generator = DynamicCourseGenerator()
        template = generator.course_templates[0]

        request = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=8,
                age=14,
                learning_style="动手型",
                prior_knowledge=["基础电路"],
                interests=["机器人"],
                learning_goals=["掌握编程"],
            ),
            subject_area="信息技术",
            learning_objectives=["学习Arduino", "理解传感器"],
            difficulty_level="中级",
            project_type="实践项目",
            time_constraint=10,
        )

        prompt = generator._build_prompt(request, template)

        # 验证关键信息是否包含在提示词中
        assert "8年级" in prompt
        assert "动手型" in prompt
        assert "基础电路" in prompt
        assert "机器人" in prompt
        assert "学习Arduino" in prompt
        assert "10小时" in prompt

    @pytest.mark.asyncio
    async def test_call_openai_success(self, mock_openai_response):
        """测试调用OpenAI API成功"""
        with patch(
            "backend.ai_service.dynamic_course.AsyncOpenAI"
        ) as mock_openai_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_choice = AsyncMock()
            mock_message = AsyncMock()

            mock_message.content = mock_openai_response["content"]
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_response.usage.total_tokens = mock_openai_response["tokens_used"]

            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            generator = DynamicCourseGenerator()
            generator.client = mock_client

            result = await generator._call_openai("测试提示词")

            assert result["content"] == mock_openai_response["content"]
            assert result["tokens_used"] == mock_openai_response["tokens_used"]
            assert result["model"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_call_openai_failure(self):
        """测试调用OpenAI API失败"""
        with patch(
            "backend.ai_service.dynamic_course.AsyncOpenAI"
        ) as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create.side_effect = Exception("API调用失败")
            mock_openai_class.return_value = mock_client

            generator = DynamicCourseGenerator()
            generator.client = mock_client

            with pytest.raises(Exception) as exc_info:
                await generator._call_openai("测试提示词")

            assert "API调用失败" in str(exc_info.value)

    def test_parse_openai_response(self, mock_openai_response):
        """测试解析OpenAI响应"""
        generator = DynamicCourseGenerator()
        response = generator._parse_openai_response(mock_openai_response["content"])

        assert response.course_title is not None
        assert response.course_description is not None
        assert isinstance(response.learning_outcomes, list)
        assert isinstance(response.project_components, list)
        assert isinstance(response.required_materials, list)
        assert response.estimated_duration > 0
        assert response.generated_at is not None

    def test_validate_request_valid(self):
        """测试有效请求验证"""
        generator = DynamicCourseGenerator()

        request = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=8,
                age=14,
                learning_style="动手型",
                prior_knowledge=[],
                interests=[],
                learning_goals=[],
            ),
            subject_area="信息技术",
            learning_objectives=["学习目标"],
            difficulty_level="中级",
            project_type="实践项目",
            time_constraint=10,
        )

        assert generator.validate_request(request) is True

    def test_validate_request_invalid(self):
        """测试无效请求验证"""
        generator = DynamicCourseGenerator()

        # 无效年级
        request1 = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=0,
                age=14,
                learning_style="动手型",
                prior_knowledge=[],
                interests=[],
                learning_goals=[],
            ),
            subject_area="信息技术",
            learning_objectives=["学习目标"],
            difficulty_level="中级",
            project_type="实践项目",
            time_constraint=10,
        )

        # 缺少学科领域
        request2 = DynamicCourseRequest(
            student_profile=StudentProfile(
                grade=8,
                age=14,
                learning_style="动手型",
                prior_knowledge=[],
                interests=[],
                learning_goals=[],
            ),
            subject_area="",
            learning_objectives=["学习目标"],
            difficulty_level="中级",
            project_type="实践项目",
            time_constraint=10,
        )

        assert generator.validate_request(request1) is False
        assert generator.validate_request(request2) is False


class TestDynamicCourseAPI:
    """动态课程API测试"""

    def test_generate_course_success(
        self, mock_course_request, mock_user_token, mock_openai_response
    ):
        """测试课程生成API成功"""
        with patch(
            "backend.routes.dynamic_course_routes.dynamic_course_generator"
        ) as mock_generator:
            # 模拟生成器行为
            mock_response = MagicMock()
            mock_response.course_title = "测试课程"
            mock_response.course_description = "测试描述"
            mock_response.learning_outcomes = ["成果1", "成果2"]
            mock_response.project_components = []
            mock_response.required_materials = ["材料1", "材料2"]
            mock_response.estimated_duration = 120
            mock_response.difficulty_assessment = "适中"
            mock_response.prerequisites = ["预备知识"]
            mock_response.assessment_methods = ["评估方法"]
            mock_response.generated_at = datetime.now()
            mock_response.tokens_used = 100

            mock_generator.generate_course.return_value = mock_response
            mock_generator.validate_request.return_value = True

            # 模拟数据库会话
            with patch("backend.utils.database.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_db

                # 模拟用户认证
                with patch(
                    "backend.routes.auth_routes.get_current_user"
                ) as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.id = 1
                    mock_user.org_id = 1
                    mock_user.has_permission.return_value = True
                    mock_get_user.return_value = mock_user

                    response = client.post(
                        "/api/v1/ai/dynamic-course",
                        json=mock_course_request,
                        headers={"Authorization": f"Bearer {mock_user_token}"},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "course_id" in data
                    assert data["course_title"] == "测试课程"

    def test_generate_course_unauthorized(self, mock_course_request):
        """测试未授权访问"""
        response = client.post("/api/v1/ai/dynamic-course", json=mock_course_request)

        assert response.status_code == 401

    def test_generate_course_insufficient_permissions(
        self, mock_course_request, mock_user_token
    ):
        """测试权限不足"""
        with patch("backend.routes.auth_routes.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.has_permission.return_value = False
            mock_get_user.return_value = mock_user

            response = client.post(
                "/api/v1/ai/dynamic-course",
                json=mock_course_request,
                headers={"Authorization": f"Bearer {mock_user_token}"},
            )

            assert response.status_code == 403

    def test_generate_course_invalid_request(self, mock_user_token):
        """测试无效请求"""
        invalid_request = {
            "student_profile": {
                "grade": 0,  # 无效年级
                "age": 14,
                "learning_style": "动手型",
            },
            "subject_area": "",  # 空学科领域
            "learning_objectives": [],
            "difficulty_level": "中级",
            "project_type": "实践项目",
            "time_constraint": 10,
        }

        with patch("backend.routes.auth_routes.get_current_user") as mock_get_user:
            mock_user = MagicMock()
            mock_user.has_permission.return_value = True
            mock_get_user.return_value = mock_user

            response = client.post(
                "/api/v1/ai/dynamic-course",
                json=invalid_request,
                headers={"Authorization": f"Bearer {mock_user_token}"},
            )

            assert response.status_code == 422  # 验证错误

    def test_get_course_history_success(self, mock_user_token):
        """测试获取课程历史成功"""
        with patch("backend.utils.database.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db

            with patch("backend.routes.auth_routes.get_current_user") as mock_get_user:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.has_permission.return_value = True
                mock_get_user.return_value = mock_user

                response = client.get(
                    "/api/v1/ai/dynamic-course/history",
                    headers={"Authorization": f"Bearer {mock_user_token}"},
                )

                assert response.status_code == 200

    def test_get_course_stats_success(self, mock_user_token):
        """测试获取统计信息成功"""
        with patch("backend.utils.database.get_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db

            with patch("backend.routes.auth_routes.get_current_user") as mock_get_user:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.has_permission.return_value = True
                mock_get_user.return_value = mock_user

                response = client.get(
                    "/api/v1/ai/dynamic-course/stats",
                    headers={"Authorization": f"Bearer {mock_user_token}"},
                )

                assert response.status_code == 200


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_course_request, mock_openai_response):
        """测试完整工作流程"""
        # 1. 用户认证
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "test_student",
                "email": "student@test.com",
                "password": "testpassword123",
            },
        )
        assert register_response.status_code == 200

        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "test_student", "password": "testpassword123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. 生成动态课程
        with patch(
            "backend.ai_service.dynamic_course.DynamicCourseGenerator._call_openai"
        ) as mock_call:
            mock_call.return_value = mock_openai_response

            generate_response = client.post(
                "/api/v1/ai/dynamic-course", json=mock_course_request, headers=headers
            )

            assert generate_response.status_code == 200
            course_data = generate_response.json()
            assert "course_id" in course_data
            assert "course_title" in course_data
            assert course_data["course_title"] is not None

            course_data["course_id"]

            # 3. 获取课程历史
            history_response = client.get(
                "/api/v1/ai/dynamic-course/history", headers=headers
            )
            assert history_response.status_code == 200

            # 4. 获取统计信息
            stats_response = client.get(
                "/api/v1/ai/dynamic-course/stats", headers=headers
            )
            assert stats_response.status_code == 200

            # 5. 获取模板评估（需要管理权限）
            # 这里跳过，因为普通用户没有管理权限


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
