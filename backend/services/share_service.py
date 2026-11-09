"""
【P3-C】分享卡片服务

负责：
- 创建分享卡片（短链 + 二维码 + 内容自动填充）
- 追踪浏览与分享行为
- 渲染落地页所需数据
- 元数据自动构建（成就/课程/用户）

支持的卡片类型：
- achievement: 成就（badge 图标 + 解锁信息）
- course: 课程（封面 + 简介）
- user_profile: 用户主页（头像 + 学习数据）
- learning_record: 学习记录（时长 + 知识点）
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.achievement import Achievement
from models.share import ShareCard, ShareCardStatus, ShareCardType
from models.user import User
from utils.qrcode_generator import generate_qr_code
from utils.short_code import generate_unique_short_code

logger = logging.getLogger(__name__)


class ShareService:
    """分享卡片服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 创建分享卡片 ==========

    def create_card(
        self,
        card_type: str,
        target_id: int,
        creator_id: int,
        custom_title: Optional[str] = None,
        custom_subtitle: Optional[str] = None,
        custom_description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> ShareCard:
        """
        创建分享卡片（生成短链 + 二维码）

        Args:
            card_type: 卡片类型
            target_id: 目标对象 ID
            creator_id: 创建者用户 ID
            custom_title: 自定义标题（覆盖默认）
            custom_subtitle: 自定义副标题
            custom_description: 自定义描述
            expires_at: 过期时间

        Returns:
            ShareCard 实例

        Raises:
            ValueError: 卡片类型未知或目标对象不存在
        """
        # 加载目标对象
        target = self._load_target(card_type, target_id)
        if target is None:
            raise ValueError(f"目标对象不存在：{card_type}#{target_id}")

        # 加载创建者（用于署名）
        creator = self.db.query(User).filter_by(id=creator_id).first()

        # 构建默认内容
        default_title, default_subtitle, default_description = self._build_default_content(
            card_type, target, creator
        )

        title = custom_title or default_title
        subtitle = custom_subtitle or default_subtitle
        description = custom_description or default_description

        # 生成唯一短链
        short_code = generate_unique_short_code(
            check_exists=self._check_short_code_exists,
            length=8,
        )

        # 创建卡片记录
        card = ShareCard(
            card_type=card_type,
            target_id=target_id,
            creator_id=creator_id,
            title=title,
            subtitle=subtitle,
            cover_image=self._get_cover_image(card_type, target),
            description=description,
            metadata_=self._build_metadata(card_type, target, creator),
            short_code=short_code,
            status=ShareCardStatus.ACTIVE,
            expires_at=expires_at,
        )
        self.db.add(card)
        self.db.flush()  # 获取 card.id

        # 生成二维码（异步失败不阻塞）
        try:
            qr_path = self._generate_qr_code(card)
            card.qr_code_path = str(qr_path)
        except Exception as e:
            logger.warning(f"二维码生成失败：{e}")

        self.db.commit()
        self.db.refresh(card)

        logger.info(
            f"分享卡片已创建：id={card.id} type={card_type} short_code={short_code}"
        )
        return card

    # ========== 查询 ==========

    def get_by_id(self, card_id: int) -> Optional[ShareCard]:
        """通过 ID 查询卡片"""
        return self.db.query(ShareCard).filter_by(id=card_id).first()

    def get_by_short_code(self, short_code: str) -> Optional[ShareCard]:
        """通过短链查询卡片（仅返回 active 状态）"""
        return self.db.query(ShareCard).filter(
            ShareCard.short_code == short_code,
            ShareCard.status == ShareCardStatus.ACTIVE,
        ).first()

    def list_by_creator(
        self, creator_id: int, limit: int = 50, offset: int = 0
    ) -> list:
        """列出某个用户创建的所有分享卡片"""
        return (
            self.db.query(ShareCard)
            .filter_by(creator_id=creator_id)
            .order_by(ShareCard.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def list_by_target(
        self, card_type: str, target_id: int, limit: int = 50
    ) -> list:
        """列出某个目标对象的所有分享卡片"""
        return (
            self.db.query(ShareCard)
            .filter_by(card_type=card_type, target_id=target_id)
            .order_by(ShareCard.view_count.desc())
            .limit(limit)
            .all()
        )

    # ========== 追踪 ==========

    def track_view(self, short_code: str) -> bool:
        """
        追踪浏览行为（+1 view_count）

        Returns:
            bool: 是否成功（卡片存在且 active）
        """
        card = self.get_by_short_code(short_code)
        if not card:
            return False
        card.view_count = (card.view_count or 0) + 1
        self.db.commit()
        return True

    def track_share(self, short_code: str, channel: str = "link") -> bool:
        """
        追踪分享行为（+1 share_count）

        Args:
            short_code: 短链代码
            channel: 分享渠道（wechat/weibo/x/link/copy）
        """
        card = self.get_by_short_code(short_code)
        if not card:
            return False
        card.share_count = (card.share_count or 0) + 1
        # 同时写入 metadata
        if not card.metadata_:
            card.metadata_ = {}
        share_history = card.metadata_.get("share_history", [])
        share_history.append({
            "channel": channel,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # 只保留最近 100 条
        if len(share_history) > 100:
            share_history = share_history[-100:]
        card.metadata_["share_history"] = share_history
        self.db.commit()
        return True

    # ========== 落地页数据 ==========

    def render_landing_data(self, short_code: str) -> Dict[str, Any]:
        """
        渲染落地页所需数据

        Raises:
            LookupError: 卡片不存在或不可用
        """
        card = self.get_by_short_code(short_code)
        if not card:
            raise LookupError(f"分享卡片不存在：{short_code}")

        # 加载目标对象
        target = self._load_target(card.card_type, card.target_id)
        target_dict = target.to_dict() if target and hasattr(target, "to_dict") else None

        # 浏览计数 +1
        self.track_view(short_code)

        # 加载创建者信息
        creator = self.db.query(User).filter_by(id=card.creator_id).first()
        creator_info = None
        if creator:
            creator_info = {
                "id": creator.id,
                "username": creator.username,
                "role": creator.role.value if creator.role else None,
            }

        # 短链 URL（用于 OG / 分享按钮）
        from config.settings import get_settings
        try:
            base_url = get_settings().SHARE_BASE_URL
        except Exception:
            base_url = "http://localhost:8000"
        short_url = f"{base_url.rstrip('/')}/share/{card.short_code}"

        return {
            "card": card.to_dict(),
            "target": target_dict,
            "creator": creator_info,
            "og_title": card.title,
            "og_description": card.description or card.subtitle or "",
            "og_image": card.cover_image or "",
            "og_url": short_url,
            "short_url": short_url,
        }

    # ========== 内部方法 ==========

    def _check_short_code_exists(self, code: str) -> bool:
        """检查短链是否已存在"""
        return (
            self.db.query(ShareCard)
            .filter_by(short_code=code)
            .first()
            is not None
        )

    def _load_target(self, card_type: str, target_id: int) -> Optional[Any]:
        """加载目标对象"""
        if card_type == ShareCardType.ACHIEVEMENT:
            return self.db.query(Achievement).filter_by(id=target_id).first()
        elif card_type == ShareCardType.COURSE:
            try:
                from models.course import Course
                return self.db.query(Course).filter_by(id=target_id).first()
            except ImportError:
                logger.warning("Course 模型未加载")
                return None
        elif card_type == ShareCardType.USER_PROFILE:
            return self.db.query(User).filter_by(id=target_id).first()
        else:
            logger.warning(f"未知卡片类型：{card_type}")
            return None

    def _build_default_content(
        self, card_type: str, target: Any, creator: Optional[User]
    ) -> tuple:
        """构建默认标题、副标题、描述"""
        creator_name = creator.username if creator else "我"

        if card_type == ShareCardType.ACHIEVEMENT:
            title = f"🎉 {creator_name}解锁了成就：{target.name}！"
            subtitle = target.description or ""
            description = (
                f"我在 iMato 解锁了【{target.name}】，获得 {target.points_reward or 0} 积分！"
                f"快来和我一起学习吧～"
            )
        elif card_type == ShareCardType.COURSE:
            title = f"📚 推荐课程：{target.title if hasattr(target, 'title') else '课程'}"
            subtitle = target.description[:100] if hasattr(target, "description") and target.description else ""
            description = f"我在 iMato 发现了一门好课程，分享给你～"
        elif card_type == ShareCardType.USER_PROFILE:
            title = f"👤 {creator_name} 的学习主页"
            subtitle = "一起来 iMato 学习吧～"
            description = "查看我的学习进度、成就和课程"
        else:
            title = "分享卡片"
            subtitle = ""
            description = ""

        return title, subtitle, description

    def _build_metadata(
        self, card_type: str, target: Any, creator: Optional[User]
    ) -> Dict[str, Any]:
        """构建 metadata 字典"""
        meta = {
            "card_type": card_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if creator:
            meta["creator_id"] = creator.id
            meta["creator_username"] = creator.username

        if card_type == ShareCardType.ACHIEVEMENT:
            meta["achievement"] = {
                "id": target.id,
                "name": target.name,
                "category": target.category.value if target.category else None,
                "badge_icon": target.badge_icon,
                "badge_color": target.badge_color,
                "badge_rarity": target.badge_rarity,
                "points_reward": target.points_reward,
                "rarity": target.badge_rarity,
            }
        elif card_type == ShareCardType.COURSE:
            if hasattr(target, "to_dict"):
                meta["course"] = target.to_dict()

        return meta

    def _get_cover_image(self, card_type: str, target: Any) -> Optional[str]:
        """获取封面图 URL"""
        if card_type == ShareCardType.ACHIEVEMENT:
            return getattr(target, "badge_icon", None)
        elif card_type == ShareCardType.COURSE:
            return getattr(target, "cover_image", None) or getattr(target, "thumbnail", None)
        return None

    def _generate_qr_code(self, card: ShareCard) -> Path:
        """生成二维码并返回路径"""
        from config.settings import get_settings
        try:
            base_url = get_settings().SHARE_BASE_URL
        except Exception:
            base_url = "http://localhost:8000"

        url = f"{base_url.rstrip('/')}/share/{card.short_code}"

        # 存储到 static/qrcodes/ 目录
        qr_dir = Path(__file__).parent.parent / "static" / "qrcodes"
        qr_filename = f"{card.short_code}.png"
        qr_path = qr_dir / qr_filename

        return generate_qr_code(url=url, save_path=qr_path, box_size=10, border=2)


# ==================== 工厂方法 ====================


def get_share_service(db: Session) -> ShareService:
    """获取分享服务实例（工厂方法）"""
    return ShareService(db)


__all__ = ["ShareService", "get_share_service"]