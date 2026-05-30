"""
MatuX 营销页面后端 API
FastAPI 实现
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import hashlib
import jwt

app = FastAPI(
    title="MatuX Marketing API",
    description="营销页面后端 API - 联系表单、订阅管理、数据统计",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储路径
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CONTACTS_FILE = DATA_DIR / "contacts.json"
SUBSCRIBERS_FILE = DATA_DIR / "subscribers.json"
ANALYTICS_FILE = DATA_DIR / "analytics.json"


# ===== 数据模型 =====

class ContactFormSubmit(BaseModel):
    """联系表单提交"""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    type: str  # business, school, personal, technical, investment, other
    message: str
    source: Optional[str] = "direct"
    location: Optional[str] = None

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('姓名至少需要 2 个字符')
        return v.strip()

    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('1'):
            raise ValueError('手机号必须以 1 开头')
        return v

    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('详细信息至少需要 10 个字符')
        return v.strip()


class SubscriptionData(BaseModel):
    """订阅数据"""
    email: EmailStr
    name: Optional[str] = None
    interests: Optional[List[str]] = None
    source: Optional[str] = "direct"
    consentGiven: bool = True


class AnalyticsEvent(BaseModel):
    """分析事件"""
    event: str
    timestamp: str
    sessionId: str
    userId: Optional[str] = None
    page: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None


class ContactFormData(ContactFormSubmit):
    """联系表单数据（包含 ID 和状态）"""
    id: str
    createdAt: str
    status: str = "pending"  # pending, processing, resolved
    typeLabel: str


class SubscriberData(BaseModel):
    """订阅用户数据"""
    email: str
    subscribedAt: str
    status: str
    verified: bool = False
    frequency: str = "weekly"  # daily, weekly, monthly


# ===== 数据存储工具 =====

class DataStore:
    """数据存储管理器"""

    def __init__(self):
        self.contacts: List[ContactFormData] = self._load_json(CONTACTS_FILE, [])
        self.subscribers: List[SubscriberData] = self._load_json(SUBSCRIBERS_FILE, [])
        self.analytics: List[AnalyticsEvent] = self._load_json(ANALYTICS_FILE, [])

    def _load_json(self, file_path: Path, default):
        """加载 JSON 文件"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def _save_json(self, file_path: Path, data):
        """保存 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_all(self):
        """保存所有数据"""
        self._save_json(CONTACTS_FILE, [c.dict() for c in self.contacts])
        self._save_json(SUBSCRIBERS_FILE, [s.dict() for s in self.subscribers])
        self._save_json(ANALYTICS_FILE, [a.dict() for a in self.analytics])


# 全局数据存储
data_store = DataStore()

# JWT 配置
SECRET_KEY = "imatuproject-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 模拟用户数据库（生产环境应使用真实数据库）
USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "email": "admin@imato.com",
        "role": "super_admin",
        "is_active": True
    },
    "orgadmin": {
        "username": "orgadmin",
        "password_hash": hashlib.sha256("password123".encode()).hexdigest(),
        "email": "orgadmin@imato.com",
        "role": "org_admin",
        "is_active": True
    }
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ===== 类型标签映射 =====

TYPE_LABELS = {
    'business': '商务合作',
    'school': '学校采购',
    'personal': '个人学习',
    'technical': '技术支持',
    'investment': '投资合作',
    'other': '其他'
}


# ===== API 路由 =====

@app.post("/api/v1/auth/token", response_model=None)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """用户登录获取访问令牌"""
    import sys
    print(f"DEBUG: 收到登录请求 - username={form_data.username}, password_length={len(form_data.password)}", file=sys.stderr)

    # 查找用户
    user = USERS_DB.get(form_data.username)

    if not user:
        print(f"DEBUG: 用户不存在 - {form_data.username}", file=sys.stderr)
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证密码
    password_hash = hashlib.sha256(form_data.password.encode()).hexdigest()
    print(f"DEBUG: 密码验证 - 输入哈希={password_hash}, 存储哈希={user['password_hash']}", file=sys.stderr)

    if password_hash != user["password_hash"]:
        print(f"DEBUG: 密码不匹配", file=sys.stderr)
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        print(f"DEBUG: 用户已禁用", file=sys.stderr)
        raise HTTPException(
            status_code=403,
            detail="用户已被禁用"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    print(f"DEBUG: 登录成功 - {form_data.username}", file=sys.stderr)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "MatuX Marketing API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ===== 联系表单 API =====

@app.post("/api/marketing/contact")
async def submit_contact_form(
    form_data: ContactFormSubmit,
    background_tasks: BackgroundTasks
):
    """提交联系表单"""
    try:
        # 创建联系表单记录
        contact = ContactFormData(
            id=f"contact_{datetime.now().timestamp()}",
            createdAt=datetime.now().isoformat(),
            status="pending",
            typeLabel=TYPE_LABELS.get(form_data.type, form_data.type),
            **form_data.dict()
        )

        # 保存到数据存储
        data_store.contacts.append(contact)
        data_store.save_all()

        # 后台任务：发送邮件通知（实际项目中实现）
        background_tasks.add_task(send_notification_email, contact)

        return {
            "success": True,
            "message": "提交成功！我们会尽快与您联系。",
            "data": {"id": contact.id}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/marketing/contacts", response_model=List[ContactFormData])
async def get_contacts(
    status: Optional[str] = None,
    type: Optional[str] = None
):
    """获取联系表单列表（Admin 后台使用）"""
    contacts = data_store.contacts

    # 过滤
    if status:
        contacts = [c for c in contacts if c.status == status]
    if type:
        contacts = [c for c in contacts if c.type == type]

    return contacts


@app.put("/api/marketing/contacts/{contact_id}")
async def update_contact_status(
    contact_id: str,
    status: str
):
    """更新联系表单状态"""
    for contact in data_store.contacts:
        if contact.id == contact_id:
            contact.status = status
            data_store.save_all()
            return {
                "success": True,
                "message": "状态已更新"
            }

    raise HTTPException(status_code=404, detail="联系表单未找到")


# ===== 订阅 API =====

@app.post("/api/marketing/subscribe")
async def subscribe_newsletter(subscription_data: SubscriptionData):
    """订阅邮件列表"""
    # 检查是否已订阅
    for subscriber in data_store.subscribers:
        if subscriber.email == subscription_data.email:
            return {
                "success": False,
                "message": "该邮箱已订阅",
                "data": subscriber.dict()
            }

    # 创建订阅记录
    subscriber = SubscriberData(
        email=subscription_data.email,
        subscribedAt=datetime.now().isoformat(),
        status="active",
        verified=False,
        frequency="weekly"
    )

    data_store.subscribers.append(subscriber)
    data_store.save_all()

    # 后台任务：发送验证邮件（实际项目中实现）

    return {
        "success": True,
        "message": "订阅成功！请查收验证邮件。",
        "data": subscriber.dict()
    }


@app.post("/api/marketing/unsubscribe")
async def unsubscribe_newsletter(
    email: EmailStr,
    unsubscribeToken: str
):
    """取消订阅"""
    for i, subscriber in enumerate(data_store.subscribers):
        if subscriber.email == email:
            data_store.subscribers.pop(i)
            data_store.save_all()
            return {
                "success": True,
                "message": "已取消订阅"
            }

    raise HTTPException(status_code=404, detail="订阅记录未找到")


@app.get("/api/marketing/subscribers")
async def get_subscribers(status: Optional[str] = None):
    """获取订阅用户列表（Admin 后台使用）"""
    subscribers = data_store.subscribers

    if status:
        subscribers = [s for s in subscribers if s.status == status]

    return subscribers


# ===== 分析 API =====

@app.post("/api/marketing/analytics/track")
async def track_analytics_event(event: AnalyticsEvent):
    """记录分析事件"""
    data_store.analytics.append(event)
    data_store.save_all()

    return {"success": True}


@app.post("/api/marketing/analytics/contact")
async def track_contact_event(event: AnalyticsEvent):
    """记录联系表单事件"""
    data_store.analytics.append(event)
    data_store.save_all()

    return {"success": True}


@app.post("/api/marketing/analytics/subscription")
async def track_subscription_event(event: AnalyticsEvent):
    """记录订阅事件"""
    data_store.analytics.append(event)
    data_store.save_all()

    return {"success": True}


# ===== Admin 营销数据 API =====

@app.get("/api/admin/marketing/metrics")
async def get_marketing_metrics(days: int = 7):
    """获取营销数据指标"""
    # 计算过去 N 天的数据
    cutoff_date = datetime.now() - timedelta(days=days)

    # 过滤联系表单
    recent_contacts = [
        c for c in data_store.contacts
        if datetime.fromisoformat(c.createdAt) > cutoff_date
    ]

    # 过滤订阅用户
    recent_subscribers = [
        s for s in data_store.subscribers
        if datetime.fromisoformat(s.subscribedAt) > cutoff_date
    ]

    # 过滤页面访问事件
    page_views = [
        a for a in data_store.analytics
        if a.event == 'page_view'
        and datetime.fromisoformat(a.timestamp) > cutoff_date
    ]

    # 计算趋势（简化版，实际应对比前 N 天）
    contacts_trend = 15  # 示例数据
    subscribers_trend = 12  # 示例数据

    return {
        "pageViews": len(page_views),
        "pageViewsTrend": 8,
        "contactForms": len(recent_contacts),
        "contactFormsTrend": contacts_trend,
        "newSubscribers": len(recent_subscribers),
        "newSubscribersTrend": subscribers_trend,
        "avgTimeOnPage": 45,  # 秒
        "avgTimeOnPageTrend": 5
    }


@app.get("/api/admin/marketing/page-stats")
async def get_page_stats():
    """获取页面访问统计"""
    # 统计各页面的访问量
    page_stats: Dict[str, Dict] = {}

    for event in data_store.analytics:
        if event.event == 'page_view' and event.page:
            url = event.page.get('url', 'unknown')
            if url not in page_stats:
                page_stats[url] = {
                    "name": event.page.get('title', url),
                    "views": 0,
                    "uniqueVisitors": set(),
                    "bounceRate": 0,
                    "avgDuration": 0
                }

            page_stats[url]["views"] += 1
            if event.userId:
                page_stats[url]["uniqueVisitors"].add(event.userId)

    # 转换为列表格式
    result = []
    for url, stats in page_stats.items():
        stats["uniqueVisitors"] = len(stats["uniqueVisitors"])
        del stats["uniqueVisitors"]  # 移除集合

        # 将 URL 转换为页面名称（简化版）
        if url == '/marketing':
            stats["name"] = "营销首页"
        elif url == '/marketing/pricing':
            stats["name"] = "价格方案"
        elif url == '/marketing/features':
            stats["name"] = "功能特性"
        elif url == '/marketing/about':
            stats["name"] = "关于我们"
        elif url == '/marketing/contact':
            stats["name"] = "联系我们"

        result.append(stats)

    return result


# ===== 后台任务 =====

async def send_notification_email(contact: ContactFormData):
    """发送邮件通知（占位函数，实际项目中需实现）"""
    # TODO: 使用 SMTP 或邮件服务 API 发送邮件
    print(f"📧 发送邮件通知: {contact.name} ({contact.email}) - {contact.typeLabel}")
    pass


async def send_verification_email(email: str):
    """发送验证邮件（占位函数，实际项目中需实现）"""
    # TODO: 生成验证 token，发送验证链接
    print(f"📧 发送验证邮件: {email}")
    pass


# ===== 启动配置 =====

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════╗
    ║   MatuX Marketing API v1.0.0           ║
    ║   Server running at http://localhost:8000 ║
    ║   API Docs at http://localhost:8000/docs ║
    ╚════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
