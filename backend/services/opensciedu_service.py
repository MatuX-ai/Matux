"""
OpenSciEDU 公共课程服务

支持两种集成模式：
1. 本地开发模式：直接调用 OpenMTSciEd Next.js API (localhost:3000)
2. 生产模式：调用 opensciedu.matux.tech API

基于 PRD F-18: OpenSciEDU 公共课程自动接入
"""

from datetime import datetime
import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ==================== Pydantic 模型 ====================

class CourseCategory(BaseModel):
    """课程分类"""
    id: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None


class CourseInstructor(BaseModel):
    """课程讲师"""
    id: str
    name: str
    avatar: Optional[str] = None
    title: Optional[str] = None


class CourseChapter(BaseModel):
    """课程章节"""
    id: str
    title: str
    order: int
    lessons: List[Dict[str, Any]] = Field(default_factory=list)
    duration_minutes: Optional[int] = None


class PublicCourse(BaseModel):
    """公共课程"""
    id: str
    title: str
    description: str
    cover_image: Optional[str] = None
    category: Optional[CourseCategory] = None
    instructor: Optional[CourseInstructor] = None
    difficulty: str = Field(
        default="beginner", pattern="^(beginner|intermediate|advanced)$")
    duration_minutes: int = 0
    lesson_count: int = 0
    student_count: int = 0
    rating: float = Field(default=0.0, ge=0, le=5)
    tags: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    is_free: bool = True
    certificate_available: bool = False


class CourseListResponse(BaseModel):
    """课程列表响应"""
    courses: List[PublicCourse]
    total: int
    page: int
    page_size: int
    has_next: bool


class CourseDetail(BaseModel):
    """课程详情"""
    id: str
    title: str
    description: str
    cover_image: Optional[str] = None
    category: Optional[CourseCategory] = None
    instructor: Optional[CourseInstructor] = None
    difficulty: str
    duration_minutes: int
    chapters: List[CourseChapter] = Field(default_factory=list)
    student_count: int
    rating: float
    tags: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    is_free: bool
    certificate_available: bool


class KnowledgeNode(BaseModel):
    """知识图谱节点"""
    id: str
    name: str
    category: str
    level: int = Field(default=0, ge=0, le=3)
    description: Optional[str] = None
    course_count: int = 0
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class KnowledgeEdge(BaseModel):
    """知识图谱边"""
    source: str
    target: str
    relation_type: str = "prerequisite"


class KnowledgeGraphData(BaseModel):
    """知识图谱数据"""
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
    categories: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """搜索结果"""
    courses: List[PublicCourse]
    total: int
    query: str
    suggestions: List[str] = Field(default_factory=list)


# ==================== 内置课程数据（服务端降级） ====================
# 【P0-B 修复】OpenSciEDU 远端（localhost:3000 / opensciedu.matux.tech）不可用时，
#   桌面端仍需能浏览课程目录。前端不再拿 mock，改由后端返回真实 API 结构的内置数据。

_BUILTIN_CATEGORIES: List[CourseCategory] = [
    CourseCategory(id="programming", name="编程入门", icon="code", description="零基础学习编程"),
    CourseCategory(id="algorithm", name="算法与数据结构", icon="psychology", description="算法思维训练"),
    CourseCategory(id="web", name="Web 开发", icon="web", description="前端与后端技术"),
    CourseCategory(id="ai", name="人工智能", icon="smart_toy", description="AI 与机器学习"),
    CourseCategory(id="science", name="科学实验", icon="science", description="跨学科科学探索"),
]

_BUILTIN_INSTRUCTORS: Dict[str, CourseInstructor] = {
    "t1": CourseInstructor(id="t1", name="李老师", title="资深编程讲师"),
    "t2": CourseInstructor(id="t2", name="王博士", title="AI 算法专家"),
    "t3": CourseInstructor(id="t3", name="张工程师", title="全栈开发工程师"),
}

# (id, title, description, category_index, instructor_id, difficulty,
#  duration_minutes, lesson_count, student_count, rating, tags, created_at, is_free)
_BUILTIN_COURSE_ROWS = [
    ("c001", "Python 编程入门", "从零开始学习 Python 编程，掌握基本语法和编程思维。通过趣味实例激发学习兴趣。", 0, "t1", "beginner", 480, 24, 12580, 4.8, ["Python", "编程入门", "青少年"], "2024-01-15T08:00:00Z", True),
    ("c002", "JavaScript 互动编程", "学习 JavaScript 实现网页互动效果，从按钮点击到动画制作。", 2, "t3", "beginner", 360, 18, 8960, 4.6, ["JavaScript", "Web", "互动"], "2024-02-01T09:00:00Z", True),
    ("c003", "Scratch 游戏制作", "使用 Scratch 可视化编程工具，制作自己的小游戏，培养逻辑思维。", 0, "t1", "beginner", 240, 12, 15800, 4.9, ["Scratch", "游戏", "可视化编程"], "2023-11-20T08:00:00Z", True),
    ("c004", "算法入门：排序与搜索", "学习基础算法，理解排序和搜索的原理，培养问题解决能力。", 1, "t2", "intermediate", 420, 21, 5630, 4.7, ["算法", "排序", "搜索"], "2024-03-10T10:00:00Z", True),
    ("c005", "HTML/CSS 网页设计", "学习网页结构与样式设计，从零开始构建精美网页。", 2, "t3", "beginner", 300, 15, 11200, 4.5, ["HTML", "CSS", "网页设计"], "2024-01-25T08:30:00Z", True),
    ("c006", "AI 探索：机器学习基础", "了解人工智能和机器学习的基本概念，体验 AI 的魅力。", 3, "t2", "intermediate", 540, 27, 4280, 4.8, ["AI", "机器学习", "Python"], "2024-04-05T11:00:00Z", False),
    ("c007", "Arduino 电子制作", "通过 Arduino 开发板学习电子电路和编程控制。", 4, "t3", "intermediate", 480, 24, 3450, 4.6, ["Arduino", "电子", "物联网"], "2024-02-15T09:30:00Z", True),
    ("c008", "数据结构：树与图", "深入学习树和图结构，掌握高级数据结构。", 1, "t2", "advanced", 600, 30, 2890, 4.7, ["数据结构", "树", "图"], "2024-05-01T10:00:00Z", False),
]


def _builtin_courses() -> List[PublicCourse]:
    """构造内置课程列表（与前端历史 mock 数据保持一致）"""
    courses: List[PublicCourse] = []
    for (
        cid, title, desc, cat_idx, tid, difficulty, minutes,
        lessons, students, rating, tags, created, is_free,
    ) in _BUILTIN_COURSE_ROWS:
        courses.append(
            PublicCourse(
                id=cid,
                title=title,
                description=desc,
                category=_BUILTIN_CATEGORIES[cat_idx],
                instructor=_BUILTIN_INSTRUCTORS[tid],
                difficulty=difficulty,
                duration_minutes=minutes,
                lesson_count=lessons,
                student_count=students,
                rating=rating,
                tags=list(tags),
                created_at=created,
                updated_at="2024-06-01T10:30:00Z",
                is_free=is_free,
                certificate_available=is_free,
            )
        )
    return courses


# ==================== 服务实现 ====================

class OpenSciEDUService:
    """
    OpenSciEDU API 客户端封装

    支持本地开发和生产两种模式：
    - 本地开发: OPENSCIEDU_LOCAL_MODE=true, 调用 localhost:3000
    - 生产模式: 调用 opensciedu.matux.tech
    """

    def __init__(
        self,
        local_mode: Optional[bool] = None,
        local_url: str = "http://localhost:3000",
        production_url: str = "https://opensciedu.matux.tech",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        cache_ttl: int = 3600
    ):
        """
        初始化 OpenSciEDU 服务

        Args:
            local_mode: 是否使用本地模式，默认从环境变量读取
            local_url: 本地开发 URL
            production_url: 生产环境 URL
            api_key: API 密钥（可选）
            timeout: 请求超时时间（秒）
            cache_ttl: 缓存有效期（秒）
        """
        # 决定使用本地还是生产 URL
        if local_mode is None:
            local_mode = os.getenv(
                "OPENSCIEDU_LOCAL_MODE", "false").lower() == "true"

        if local_mode:
            self.api_url = local_url.rstrip("/")
            logger.info(f"[OpenSciEDU] 使用本地开发模式: {self.api_url}")
        else:
            self.api_url = production_url.rstrip("/")
            logger.info(f"[OpenSciEDU] 使用生产模式: {self.api_url}")

        self.local_mode = local_mode
        self.api_key = api_key or os.getenv("OPENSCIEDU_API_KEY")
        self.timeout = timeout
        self.cache_ttl = cache_ttl

        # HTTP 客户端
        self._client: Optional[httpx.AsyncClient] = None

        # 本地缓存
        self._course_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._knowledge_graph_cache: Optional[KnowledgeGraphData] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=self.timeout
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        if key not in self._cache_timestamps:
            return False
        age = datetime.now().timestamp() - self._cache_timestamps[key]
        return age < self.cache_ttl

    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        self._course_cache[key] = data
        self._cache_timestamps[key] = datetime.now().timestamp()

    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self._is_cache_valid(key):
            return self._course_cache.get(key)
        return None

    async def get_public_courses(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        sort_by: str = "created_at"
    ) -> CourseListResponse:
        """
        获取公共课程列表

        本地模式: GET /api/v1/coursewares
        生产模式: GET /api/v1/courses
        """
        cache_key = f"courses_{page}_{page_size}_{category}_{difficulty}_{sort_by}"

        # 检查缓存
        cached = self._get_cache(cache_key)
        if cached:
            logger.debug(f"[OpenSciEDU] 从缓存获取课程列表: {cache_key}")
            return cached

        try:
            params = {
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by
            }
            if category:
                params["category"] = category
            if difficulty:
                params["difficulty"] = difficulty

            # 根据模式选择 API 路径
            if self.local_mode:
                # 本地开发模式: Next.js API
                path = "/api/v1/coursewares"
                response = await self.client.get(path, params=params)
            else:
                # 生产模式
                path = "/api/v1/courses"
                response = await self.client.get(path, params=params)

            response.raise_for_status()
            data = response.json()

            # 转换响应格式
            result = self._convert_course_list_response(data)
            self._set_cache(cache_key, result)

            logger.info(f"[OpenSciEDU] 获取课程列表成功: 共 {result.total} 门课程")
            return result

        except httpx.HTTPError as e:
            logger.error(f"[OpenSciEDU] 获取课程列表失败: {e}")
            return self._get_fallback_course_list(page, page_size, category, difficulty)

    def _convert_course_list_response(self, data: Any) -> CourseListResponse:
        """转换 API 响应格式"""
        # 根据本地/生产模式转换字段
        courses = []
        items = data.get("coursewares") or data.get("courses") or []

        for item in items:
            course = PublicCourse(
                id=str(item.get("id", item.get("courseId", ""))),
                title=item.get("title", ""),
                description=item.get("description", ""),
                cover_image=item.get("coverImage") or item.get("cover_image"),
                difficulty=item.get("difficulty") or item.get(
                    "complexity", "beginner"),
                duration_minutes=item.get("durationMinutes") or item.get(
                    "duration_minutes", 0),
                lesson_count=item.get("lessonCount") or item.get(
                    "lesson_count", 0),
                student_count=item.get("studentCount") or item.get(
                    "student_count", 0),
                rating=float(item.get("rating", 0)),
                tags=item.get("tags", []),
                created_at=item.get("createdAt") or item.get("created_at", ""),
                updated_at=item.get("updatedAt") or item.get("updated_at", ""),
                is_free=item.get("isFree") or item.get("is_free", True),
                category=CourseCategory(
                    id=item.get("category", {}).get("id", ""),
                    name=item.get("category", {}).get("name", "未分类")
                ) if item.get("category") else None,
                instructor=CourseInstructor(
                    id=item.get("instructor", {}).get("id", ""),
                    name=item.get("instructor", {}).get("name", "未知讲师")
                ) if item.get("instructor") else None,
            )
            courses.append(course)

        total = data.get("total", len(courses))
        page = data.get("page", 1)
        page_size = data.get("pageSize", data.get("page_size", 20))

        return CourseListResponse(
            courses=courses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=total > page * page_size
        )

    def _get_fallback_course_list(
        self,
        page: int,
        page_size: int,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> CourseListResponse:
        """服务端降级：返回内置课程（支持筛选 + 分页），避免桌面端空白目录"""
        courses = _builtin_courses()
        if category:
            courses = [c for c in courses if c.category and c.category.id == category]
        if difficulty:
            courses = [c for c in courses if c.difficulty == difficulty]

        total = len(courses)
        start = max(page - 1, 0) * page_size
        end = start + page_size
        page_courses = courses[start:end]

        return CourseListResponse(
            courses=page_courses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=end < total,
        )

    async def get_course_detail(self, course_id: str) -> Optional[CourseDetail]:
        """
        获取课程详情

        本地模式: GET /api/v1/coursewares/{id}
        """
        cache_key = f"course_detail_{course_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            if self.local_mode:
                path = f"/api/v1/coursewares/{course_id}"
            else:
                path = f"/api/v1/courses/{course_id}"

            response = await self.client.get(path)
            response.raise_for_status()
            data = response.json()

            result = CourseDetail(
                id=str(data.get("id", course_id)),
                title=data.get("title", ""),
                description=data.get("description", ""),
                cover_image=data.get("coverImage"),
                difficulty=data.get("difficulty", "beginner"),
                duration_minutes=data.get("durationMinutes", 0),
                chapters=self._convert_chapters(data.get("chapters", [])),
                student_count=data.get("studentCount", 0),
                rating=float(data.get("rating", 0)),
                tags=data.get("tags", []),
                learning_outcomes=data.get("learningOutcomes", []),
                prerequisites=data.get("prerequisites", []),
                created_at=data.get("createdAt", ""),
                updated_at=data.get("updatedAt", ""),
                is_free=data.get("isFree", True),
                certificate_available=data.get("certificateAvailable", False),
            )

            self._set_cache(cache_key, result)
            return result

        except httpx.HTTPError as e:
            logger.error(f"[OpenSciEDU] 获取课程详情失败 ({course_id}): {e}")
            return None

    def _convert_chapters(self, chapters: List[Any]) -> List[CourseChapter]:
        """转换章节数据"""
        result = []
        for i, ch in enumerate(chapters):
            result.append(CourseChapter(
                id=str(ch.get("id", i)),
                title=ch.get("title", ""),
                order=ch.get("order", i),
                lessons=ch.get("lessons", []),
                duration_minutes=ch.get("durationMinutes")
            ))
        return result

    async def get_knowledge_graph(self, force_refresh: bool = False) -> Optional[KnowledgeGraphData]:
        """
        获取知识图谱数据

        本地模式: GET /api/v1/knowledge-graph
        """
        if not force_refresh and self._knowledge_graph_cache:
            return self._knowledge_graph_cache

        try:
            if self.local_mode:
                path = "/api/v1/knowledge-graph"
            else:
                path = "/api/v1/knowledge-graph"

            response = await self.client.get(path)
            response.raise_for_status()
            data = response.json()

            # 转换节点
            nodes = [
                KnowledgeNode(
                    id=n.get("id", ""),
                    name=n.get("name", ""),
                    category=n.get("category", ""),
                    level=n.get("level", 0),
                    description=n.get("description"),
                    course_count=n.get("courseCount", 0),
                    position_x=n.get("positionX") or n.get("position_x"),
                    position_y=n.get("positionY") or n.get("position_y"),
                )
                for n in data.get("nodes", [])
            ]

            # 转换边
            edges = [
                KnowledgeEdge(
                    source=e.get("source", ""),
                    target=e.get("target", ""),
                    relation_type=e.get("relationType", "prerequisite"),
                )
                for e in data.get("edges", [])
            ]

            result = KnowledgeGraphData(
                nodes=nodes,
                edges=edges,
                categories=data.get("categories", [])
            )

            self._knowledge_graph_cache = result
            logger.info(f"[OpenSciEDU] 获取知识图谱成功: {len(nodes)} 个节点")
            return result

        except httpx.HTTPError as e:
            logger.error(f"[OpenSciEDU] 获取知识图谱失败: {e}")
            return self._knowledge_graph_cache

    async def search_courses(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        搜索课程
        """
        try:
            params = {
                "q": keyword,
                "page": page,
                "page_size": page_size
            }

            if self.local_mode:
                path = "/api/v1/coursewares/search"
            else:
                path = "/api/v1/courses/search"

            response = await self.client.get(path, params=params)
            response.raise_for_status()
            data = response.json()

            courses = [
                PublicCourse(
                    id=str(c.get("id", "")),
                    title=c.get("title", ""),
                    description=c.get("description", ""),
                )
                for c in data.get("courses", [])
            ]

            return SearchResult(
                courses=courses,
                total=data.get("total", 0),
                query=keyword,
                suggestions=data.get("suggestions", [])
            )

        except httpx.HTTPError as e:
            logger.error(f"[OpenSciEDU] 搜索课程失败 ({keyword}): {e}")
            kw = keyword.lower()
            fallback_courses = [
                c for c in _builtin_courses()
                if kw in c.title.lower() or kw in c.description.lower()
            ]
            return SearchResult(
                courses=fallback_courses,
                total=len(fallback_courses),
                query=keyword,
                suggestions=[],
            )

    async def get_categories(self) -> List[CourseCategory]:
        """获取课程分类列表"""
        cache_key = "categories"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            if self.local_mode:
                path = "/api/v1/coursewares/categories"
            else:
                path = "/api/v1/categories"

            response = await self.client.get(path)
            response.raise_for_status()
            data = response.json()

            categories = [
                CourseCategory(
                    id=c.get("id", ""),
                    name=c.get("name", ""),
                    icon=c.get("icon"),
                    description=c.get("description"),
                )
                for c in data.get("categories", [])
            ]

            self._set_cache(cache_key, categories)
            return categories

        except httpx.HTTPError as e:
            logger.error(f"[OpenSciEDU] 获取分类列表失败: {e}")
            return list(_BUILTIN_CATEGORIES)

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            path = "/api/health" if self.local_mode else "/api/v1/health"
            response = await self.client.get(path, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def clear_cache(self):
        """清空缓存"""
        self._course_cache.clear()
        self._cache_timestamps.clear()
        self._knowledge_graph_cache = None
        logger.info("[OpenSciEDU] 缓存已清空")


# ==================== 单例模式 ====================

_opensciedu_service: Optional[OpenSciEDUService] = None


def get_opensciedu_service() -> OpenSciEDUService:
    """获取 OpenSciEDU 服务单例"""
    global _opensciedu_service

    if _opensciedu_service is None:
        local_mode = os.getenv("OPENSCIEDU_LOCAL_MODE",
                               "true").lower() == "true"
        local_url = os.getenv("OPENSCIEDU_LOCAL_URL", "http://localhost:3000")
        production_url = os.getenv(
            "OPENSCIEDU_API_URL", "https://opensciedu.matux.tech")
        api_key = os.getenv("OPENSCIEDU_API_KEY")
        timeout = float(os.getenv("OPENSCIEDU_TIMEOUT", "30.0"))
        cache_ttl = int(os.getenv("OPENSCIEDU_CACHE_TTL", "3600"))

        _opensciedu_service = OpenSciEDUService(
            local_mode=local_mode,
            local_url=local_url,
            production_url=production_url,
            api_key=api_key,
            timeout=timeout,
            cache_ttl=cache_ttl
        )

    return _opensciedu_service


async def shutdown_opensciedu_service():
    """关闭 OpenSciEDU 服务"""
    global _opensciedu_service

    if _opensciedu_service:
        await _opensciedu_service.close()
        _opensciedu_service = None
