"""
动态课程生成引擎
基于GPT-3.5 Turbo模型生成个性化课程描述和项目设计
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException

from config.settings import settings

logger = logging.getLogger(__name__)


class StudentProfile(BaseModel):
    """学生档案模型"""

    grade: int = Field(..., ge=1, le=12, description="年级 (1-12)")
    age: int = Field(..., ge=6, le=18, description="年龄")
    learning_style: str = Field(..., description="学习风格")
    prior_knowledge: List[str] = Field(default=[], description="已有知识背景")
    interests: List[str] = Field(default=[], description="兴趣爱好")
    learning_goals: List[str] = Field(default=[], description="学习目标")


class CourseTemplate(BaseModel):
    """课程模板模型"""

    template_id: str
    name: str
    description: str
    subject_areas: List[str]
    difficulty_levels: List[str]
    target_grades: List[int]
    prompt_template: str


class DynamicCourseRequest(BaseModel):
    """动态课程生成请求模型"""

    student_profile: StudentProfile
    subject_area: str = Field(..., description="学科领域")
    learning_objectives: List[str] = Field(..., description="学习目标")
    difficulty_level: str = Field(..., description="难度等级")
    project_type: str = Field(..., description="项目类型")
    time_constraint: int = Field(..., ge=1, le=100, description="时间约束(小时)")
    language: str = Field(default="zh-CN", description="语言")


class CourseComponent(BaseModel):
    """课程组件模型"""

    title: str
    description: str
    duration: int  # 分钟
    materials: List[str]
    steps: List[str]


class DynamicCourseResponse(BaseModel):
    """动态课程生成响应模型"""

    course_title: str
    course_description: str
    learning_outcomes: List[str]
    project_components: List[CourseComponent]
    required_materials: List[str]
    estimated_duration: int  # 总时长(分钟)
    difficulty_assessment: str
    prerequisites: List[str]
    assessment_methods: List[str]
    generated_at: datetime


class DynamicCourseGenerator:
    """动态课程生成器"""

    def __init__(self, db_session: Session = None):
        """初始化课程生成器"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.7
        self.max_tokens = 1500

        # 初始化 Token 计费
        self.db = db_session
        if db_session:
            from services.token_service import TokenService
            from utils.decorators import TokenBillingDecorator
            token_service = TokenService(db_session)
            self.billing = TokenBillingDecorator(token_service)
        else:
            self.billing = None

        # 预定义课程模板
        self.course_templates = self._load_course_templates()

        logger.info("动态课程生成器初始化完成")

    def _load_course_templates(self) -> List[CourseTemplate]:
        """加载预定义课程模板"""
        templates = [
            CourseTemplate(
                template_id="light_sensor_project",
                name="光敏传感器自动浇水系统",
                description="基于光敏传感器的智能植物养护项目",
                subject_areas=["物理", "信息技术", "生物"],
                difficulty_levels=["初级", "中级"],
                target_grades=[6, 7, 8, 9],
                prompt_template="""为{grade}年级学生设计一个基于光敏传感器的自动浇水系统项目。
学生背景：{learning_style}学习风格，已有知识：{prior_knowledge}，兴趣：{interests}
学习目标：{learning_objectives}
项目要求：{project_type}，时间限制：{time_constraint}小时
请生成详细的课程设计方案，包括：
1. 项目标题和整体描述
2. 具体的学习成果
3. 项目组件分解（每个组件包含标题、描述、时长、所需材料、实施步骤）
4. 总体所需材料清单
5. 总估计时长
6. 难度评估
7. 先修知识要求
8. 评估方法""",
            ),
            CourseTemplate(
                template_id="arduino_basics",
                name="Arduino基础电子项目",
                description="Arduino平台入门级电子制作项目",
                subject_areas=["信息技术", "物理", "工程"],
                difficulty_levels=["初级"],
                target_grades=[7, 8, 9, 10],
                prompt_template="""为{grade}年级学生设计一个Arduino基础电子项目。
学生背景：{learning_style}学习风格，已有知识：{prior_knowledge}，兴趣：{interests}
学习目标：{learning_objectives}
项目要求：{project_type}，时间限制：{time_constraint}小时
请生成适合初学者的Arduino项目课程设计。""",
            ),
            CourseTemplate(
                template_id="python_programming",
                name="Python趣味编程项目",
                description="面向青少年的Python编程入门项目",
                subject_areas=["信息技术", "数学"],
                difficulty_levels=["初级", "中级"],
                target_grades=[6, 7, 8, 9, 10],
                prompt_template="""为{grade}年级学生设计一个Python编程项目。
学生背景：{learning_style}学习风格，已有知识：{prior_knowledge}，兴趣：{interests}
学习目标：{learning_objectives}
项目要求：{project_type}，时间限制：{time_constraint}小时
请设计有趣的Python编程课程。""",
            ),
            CourseTemplate(
                template_id="stem_innovation",
                name="STEM创新实践项目",
                description="跨学科STEM综合实践项目",
                subject_areas=["科学", "技术", "工程", "数学"],
                difficulty_levels=["中级", "高级"],
                target_grades=[8, 9, 10, 11, 12],
                prompt_template="""为{grade}年级学生设计一个STEM创新实践项目。
学生背景：{learning_style}学习风格，已有知识：{prior_knowledge}，兴趣：{interests}
学习目标：{learning_objectives}
项目要求：{project_type}，时间限制：{time_constraint}小时
请设计综合性STEM实践课程。""",
            ),
        ]
        return templates

    def _select_template(
        self, request: DynamicCourseRequest
    ) -> Optional[CourseTemplate]:
        """根据请求选择合适的课程模板"""
        for template in self.course_templates:
            if (
                request.subject_area in template.subject_areas
                and request.difficulty_level in template.difficulty_levels
                and request.student_profile.grade in template.target_grades
            ):
                return template
        # 如果没有完全匹配，返回第一个合适的模板
        return self.course_templates[0] if self.course_templates else None

    def _build_prompt(
        self, request: DynamicCourseRequest, template: CourseTemplate
    ) -> str:
        """构建提示词"""
        prompt = template.prompt_template.format(
            grade=request.student_profile.grade,
            learning_style=request.student_profile.learning_style,
            prior_knowledge=(
                "、".join(request.student_profile.prior_knowledge)
                if request.student_profile.prior_knowledge
                else "无"
            ),
            interests=(
                "、".join(request.student_profile.interests)
                if request.student_profile.interests
                else "广泛"
            ),
            learning_objectives="、".join(request.learning_objectives),
            project_type=request.project_type,
            time_constraint=request.time_constraint,
        )
        return prompt

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """调用OpenAI API生成内容"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位经验丰富的教育专家，擅长设计个性化的STEM课程。请用中文回答，确保内容适合对应年龄段的学生。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            logger.info(f"OpenAI API调用成功，使用令牌数: {tokens_used}")

            return {"content": content, "tokens_used": tokens_used, "model": self.model}

        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise

    def _parse_openai_response(self, content: str) -> DynamicCourseResponse:
        """解析OpenAI响应内容"""
        # 这里可以实现更复杂的解析逻辑
        # 目前返回简化版本
        return DynamicCourseResponse(
            course_title=f"{self._extract_title(content)}",
            course_description=self._extract_description(content),
            learning_outcomes=self._extract_learning_outcomes(content),
            project_components=self._extract_project_components(content),
            required_materials=self._extract_materials(content),
            estimated_duration=self._extract_duration(content),
            difficulty_assessment=self._extract_difficulty(content),
            prerequisites=self._extract_prerequisites(content),
            assessment_methods=self._extract_assessment_methods(content),
            generated_at=datetime.now(),
        )

    def _extract_title(self, content: str) -> str:
        """从内容中提取课程标题"""
        # 简单提取逻辑，实际项目中需要更robust的解析
        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("#") or "项目" in line or "课程" in line:
                return line.replace("#", "").strip()
        return "个性化学习项目"

    def _extract_description(self, content: str) -> str:
        """提取课程描述"""
        return content[:200] + "..." if len(content) > 200 else content

    def _extract_learning_outcomes(self, content: str) -> List[str]:
        """提取学习成果"""
        outcomes = []
        if "学习成果" in content or "学习目标" in content:
            # 简化提取逻辑
            outcomes = ["掌握相关技术原理", "培养实践能力", "提升问题解决能力"]
        return outcomes

    def _extract_project_components(self, content: str) -> List[CourseComponent]:
        """提取项目组件"""
        return [
            CourseComponent(
                title="项目介绍",
                description="了解项目背景和目标",
                duration=30,
                materials=["电脑", "网络"],
                steps=["观看介绍视频", "阅读项目说明", "讨论项目意义"],
            )
        ]

    def _extract_materials(self, content: str) -> List[str]:
        """提取所需材料"""
        return ["基础电子元件", "开发板", "传感器", "计算机"]

    def _extract_duration(self, content: str) -> int:
        """提取估计时长"""
        return 120  # 默认2小时

    def _extract_difficulty(self, content: str) -> str:
        """提取难度评估"""
        return "适中"

    def _extract_prerequisites(self, content: str) -> List[str]:
        """提取先修知识"""
        return ["基础计算机操作", "简单电路知识"]

    def _extract_assessment_methods(self, content: str) -> List[str]:
        """提取评估方法"""
        return ["项目展示", "过程记录", "同伴评价"]

    async def generate_course(
        self,
        user_id: int,
        request: DynamicCourseRequest
    ) -> DynamicCourseResponse:
        """
        生成动态课程

        Args:
            user_id: 用户 ID
            request: 课程生成请求

        Returns:
            生成的课程

        Raises:
            HTTPException: Token 余额不足时抛出
        """
        # 评估课程复杂度
        complexity = self._evaluate_complexity(request)

        # Token 计费检查
        if self.billing and self.billing.billing_enabled:
            # 根据复杂度预估 Token 消耗
            cost_map = {
                "simple": 50,
                "medium": 150,
                "complex": 500
            }
            estimated_tokens = cost_map.get(complexity.lower(), 100)

            balance = self.billing.token_service.get_or_create_user_balance(
                user_id)
            if balance.remaining_tokens < estimated_tokens:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "INSUFFICIENT_TOKENS",
                        "message": f"Token 余额不足，当前剩余：{balance.remaining_tokens}，需要：{estimated_tokens}",
                        "required": estimated_tokens,
                        "available": balance.remaining_tokens,
                        "usage_type": "course_generation",
                        "complexity": complexity
                    }
                )

        logger.info(
            f"开始生成动态课程：{request.subject_area} - {request.student_profile.grade}年级"
        )

        # 选择合适的模板
        template = self._select_template(request)
        if not template:
            raise ValueError("未找到合适的课程模板")

        # 构建提示词
        prompt = self._build_prompt(request, template)

        # 调用 AI 生成内容
        ai_response = await self._call_openai(prompt)

        # 解析响应
        course_response = self._parse_openai_response(ai_response["content"])

        logger.info(f"课程生成完成：{course_response.course_title}")

        # Token 扣费
        if self.billing and self.billing.billing_enabled:
            cost_map = {"simple": 50, "medium": 150, "complex": 500}
            actual_tokens = cost_map.get(complexity.lower(), 100)

            success, msg = self.billing.token_service.consume_tokens(
                user_id=user_id,
                token_amount=actual_tokens,
                usage_type="course_generation",
                usage_description=f"生成课程：{request.subject_area} - {request.difficulty_level}",
                resource_type="course"
            )

            if success:
                logger.info(f"用户 {user_id} 课程生成扣费成功：{actual_tokens} tokens")
            else:
                logger.warning(f"用户 {user_id} 课程生成扣费失败：{msg}")

        return course_response

    def _evaluate_complexity(self, request: DynamicCourseRequest) -> str:
        """
        评估课程复杂度

        Args:
            request: 课程请求

        Returns:
            复杂度等级 (simple/medium/complex)
        """
        score = 0

        # 基于学习目标数量
        score += len(request.learning_objectives) * 10

        # 基于时间约束
        if request.time_constraint < 10:
            score += 20
        elif request.time_constraint > 30:
            score -= 10

        # 基于难度等级
        difficulty_scores = {
            "beginner": 0,
            "intermediate": 20,
            "advanced": 40,
            "expert": 60
        }
        score += difficulty_scores.get(request.difficulty_level.lower(), 20)

        # 判断复杂度
        if score < 30:
            return "simple"
        elif score < 70:
            return "medium"
        else:
            return "complex"

    def validate_request(self, request: DynamicCourseRequest) -> bool:
        """验证请求参数"""
        if not request.student_profile.grade or not (
            1 <= request.student_profile.grade <= 12
        ):
            return False
        if not request.subject_area:
            return False
        if not request.learning_objectives:
            return False
        if not request.difficulty_level:
            return False
        return True


# 全局实例
dynamic_course_generator = DynamicCourseGenerator()
