import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
import logging
import smtplib
from typing import Any, Dict, List, Optional

from .integral_decay_calculator import decay_calculator
from .reward_event_bus import RewardEvent, reward_event_bus

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """通知类型"""

    DECAY_WARNING = "decay_warning"  # 衰减警告
    DECAY_COMPLETED = "decay_completed"  # 衰减完成
    ACTIVITY_REMINDER = "activity_reminder"  # 活动提醒
    DECAY_PROJECTION = "decay_projection"  # 衰减预测
    IMMUNITY_EXPIRING = "immunity_expiring"  # 免疫期即将到期


class NotificationChannel(Enum):
    """通知渠道"""

    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"


@dataclass
class NotificationTemplate:
    """通知模板"""

    template_id: str
    name: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    subject_template: str
    content_template: str
    priority: str  # low, medium, high
    cooldown_hours: int  # 冷却时间


@dataclass
class UserNotificationPreference:
    """用户通知偏好设置"""

    user_id: int
    enabled_channels: List[NotificationChannel]
    decay_warning_threshold: int  # 积分衰减警告阈值
    activity_reminder_days: int  # 活动提醒间隔天数
    timezone: str
    language: str


class DecayNotificationService:
    """积分衰减通知服务"""

    def __init__(self):
        self.templates: Dict[str, NotificationTemplate] = {}
        self.user_preferences: Dict[int, UserNotificationPreference] = {}
        self.notification_history: Dict[int, List[Dict[str, Any]]] = {}
        self.email_config = self._load_email_config()
        self._initialize_templates()
        self._setup_event_handlers()

    def _load_email_config(self) -> Dict[str, str]:
        """加载邮件配置"""
        # 实际应该从配置文件或环境变量加载
        return {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": "587",
            "username": "noreply@imato.com",
            "password": "your_app_password",
            "sender_name": "iMato积分系统",
        }

    def _initialize_templates(self):
        """初始化通知模板"""
        templates = [
            NotificationTemplate(
                template_id="decay_warning_high",
                name="高额衰减警告",
                notification_type=NotificationType.DECAY_WARNING,
                channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.PUSH,
                    NotificationChannel.IN_APP,
                ],
                subject_template="⚠️ 您的积分即将大幅衰减",
                content_template="""
                亲爱的用户，

                检测到您的积分账户({current_points}积分)在过去{days_inactive}天内没有活跃，
                根据系统规则，您的积分将在近期发生衰减。

                预计衰减: {estimated_decay}积分
                衰减后余额: {projected_balance}积分

                💡 建议您尽快完成以下任一活动来避免积分衰减：
                • 完成一个AR实验场景
                • 参与语音纠错练习
                • 完成手势挑战任务

                如有任何疑问，请联系客服。

                此致
                iMato团队
                """,
                priority="high",
                cooldown_hours=24,
            ),
            NotificationTemplate(
                template_id="decay_completed",
                name="衰减完成通知",
                notification_type=NotificationType.DECAY_COMPLETED,
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                subject_template="📊 积分衰减报告 - {date}",
                content_template="""
                亲爱的用户，

                本期积分衰减已完成，详情如下：

                📅 衰减日期: {date}
                🔢 衰减前余额: {before_points}积分
                📉 本次衰减: {decay_amount}积分
                💰 衰减后余额: {after_points}积分

                📈 累计衰减: {total_decayed}积分

                感谢您的理解与支持！

                iMato团队
                """,
                priority="medium",
                cooldown_hours=168,  # 一周
            ),
            NotificationTemplate(
                template_id="activity_reminder",
                name="活动提醒",
                notification_type=NotificationType.ACTIVITY_REMINDER,
                channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH],
                subject_template="🚀 快来完成任务，保持积分活跃！",
                content_template="""
                亲爱的用户，

                您已经有{days_since_activity}天没有在iMato平台进行活动了。

                🎯 您可以通过以下方式快速获得积分：
                1. 完成AR电路搭建练习 (+50~200积分)
                2. 参与语音纠错挑战 (+20~100积分)
                3. 解锁隐藏手势任务 (+100~300积分)

                🏆 完成任务还能获得成就徽章哦！

                快来参与吧！

                iMato团队
                """,
                priority="medium",
                cooldown_hours=48,
            ),
            NotificationTemplate(
                template_id="decay_projection",
                name="衰减预测",
                notification_type=NotificationType.DECAY_PROJECTION,
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                subject_template="🔮 您的积分衰减预测",
                content_template="""
                亲爱的用户，

                根据您的当前活跃情况，为您生成积分衰减预测：

                📊 未来30天积分预测：
                {projection_table}

                💡 建议行动：
                {recommendations}

                🎯 想要阻止衰减？立即完成任务！

                iMato团队
                """,
                priority="low",
                cooldown_hours=168,
            ),
            NotificationTemplate(
                template_id="immunity_expiring",
                name="免疫期到期提醒",
                notification_type=NotificationType.IMMUNITY_EXPIRING,
                channels=[NotificationChannel.EMAIL, NotificationChannel.PUSH],
                subject_template="🛡️ 您的积分免疫期即将到期",
                content_template="""
                亲爱的用户，

                您的积分免疫期将在{expiration_date}到期。

                到期后，系统将按照正常规则对您的积分进行衰减。

                📅 免疫期剩余: {days_remaining}天
                💰 当前积分: {current_points}积分

                建议您在免疫期结束前积极参与平台活动，保持积分活跃。

                iMato团队
                """,
                priority="high",
                cooldown_hours=24,
            ),
        ]

        for template in templates:
            self.templates[template.template_id] = template

    def _setup_event_handlers(self):
        """设置事件处理器"""
        reward_event_bus.subscribe(
            "daily_decay_completed", self.handle_daily_decay_completed
        )
        reward_event_bus.subscribe(
            "user_near_decay_threshold", self.handle_decay_warning
        )
        reward_event_bus.subscribe(
            "user_immunity_expiring", self.handle_immunity_expiring
        )

    async def handle_daily_decay_completed(self, event: RewardEvent):
        """处理每日衰减完成事件"""
        try:
            decay_data = event.data

            # 向受影响的用户发送衰减完成通知
            affected_users = await self._get_affected_users_from_decay(decay_data)

            for user_id in affected_users:
                await self.send_notification(
                    user_id=user_id,
                    template_id="decay_completed",
                    data={
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "before_points": await self._get_user_previous_points(user_id),
                        "decay_amount": await self._get_user_today_decay(user_id),
                        "after_points": await self._get_user_current_points(user_id),
                        "total_decayed": await self._get_user_total_decayed(user_id),
                    },
                )

        except Exception as e:
            logger.error(f"处理每日衰减完成事件失败: {e}")

    async def handle_decay_warning(self, event: RewardEvent):
        """处理衰减警告事件"""
        try:
            user_id = event.user_id
            warning_data = event.data

            await self.send_notification(
                user_id=user_id,
                template_id="decay_warning_high",
                data={
                    "current_points": warning_data.get("current_points", 0),
                    "days_inactive": warning_data.get("days_inactive", 0),
                    "estimated_decay": warning_data.get("estimated_decay", 0),
                    "projected_balance": warning_data.get("projected_balance", 0),
                },
            )

        except Exception as e:
            logger.error(f"处理衰减警告事件失败: {e}")

    async def handle_immunity_expiring(self, event: RewardEvent):
        """处理免疫期到期事件"""
        try:
            user_id = event.user_id
            immunity_data = event.data

            await self.send_notification(
                user_id=user_id,
                template_id="immunity_expiring",
                data={
                    "expiration_date": immunity_data.get("expiration_date", ""),
                    "days_remaining": immunity_data.get("days_remaining", 0),
                    "current_points": immunity_data.get("current_points", 0),
                },
            )

        except Exception as e:
            logger.error(f"处理免疫期到期事件失败: {e}")

    async def send_notification(
        self, user_id: int, template_id: str, data: Dict[str, Any]
    ) -> bool:
        """发送通知"""
        try:
            # 检查冷却时间
            if not self._check_cooldown(user_id, template_id):
                logger.debug(f"通知冷却中，跳过发送: 用户{user_id}, 模板{template_id}")
                return False

            # 获取模板和用户偏好
            template = self.templates.get(template_id)
            preference = self._get_user_preference(user_id)

            if not template or not preference:
                logger.warning(f"缺少模板或用户偏好: {template_id}, 用户{user_id}")
                return False

            # 准备通知内容
            subject = self._render_template(template.subject_template, data)
            content = self._render_template(template.content_template, data)

            # 发送到各个渠道
            success_channels = []

            for channel in template.channels:
                if channel in preference.enabled_channels:
                    success = await self._send_via_channel(
                        user_id, channel, subject, content, template
                    )
                    if success:
                        success_channels.append(channel.value)

            # 记录发送历史
            self._record_notification_history(
                user_id, template_id, success_channels, data
            )

            logger.info(
                f"通知发送完成: 用户{user_id}, 模板{template_id}, 渠道{success_channels}"
            )
            return len(success_channels) > 0

        except Exception as e:
            logger.error(f"发送通知失败: 用户{user_id}, 模板{template_id}, 错误: {e}")
            return False

    async def _send_via_channel(
        self,
        user_id: int,
        channel: NotificationChannel,
        subject: str,
        content: str,
        template: NotificationTemplate,
    ) -> bool:
        """通过指定渠道发送通知"""
        try:
            if channel == NotificationChannel.EMAIL:
                return await self._send_email(user_id, subject, content)
            elif channel == NotificationChannel.PUSH:
                return await self._send_push_notification(user_id, subject, content)
            elif channel == NotificationChannel.SMS:
                return await self._send_sms(user_id, content)
            elif channel == NotificationChannel.IN_APP:
                return await self._send_in_app_notification(
                    user_id, subject, content, template.priority
                )

            return False

        except Exception as e:
            logger.error(f"通过{channel.value}渠道发送失败: {e}")
            return False

    async def _send_email(self, user_id: int, subject: str, content: str) -> bool:
        """发送邮件"""
        try:
            user_email = await self._get_user_email(user_id)
            if not user_email:
                return False

            msg = MIMEMultipart()
            msg["From"] = (
                f"{self.email_config['sender_name']} <{self.email_config['username']}>"
            )
            msg["To"] = user_email
            msg["Subject"] = subject

            msg.attach(MIMEText(content, "plain", "utf-8"))

            # 实际发送邮件
            # with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            #     server.starttls()
            #     server.login(self.email_config['username'], self.email_config['password'])
            #     server.send_message(msg)

            logger.debug(f"邮件已发送: {user_email}")
            return True

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    async def _send_push_notification(
        self, user_id: int, title: str, content: str
    ) -> bool:
        """发送推送通知"""
        try:
            # 这里应该调用推送服务API
            device_token = await self._get_user_device_token(user_id)
            if not device_token:
                return False

            # 模拟推送发送
            logger.debug(f"推送通知已发送: 用户{user_id}")
            return True

        except Exception as e:
            logger.error(f"发送推送通知失败: {e}")
            return False

    async def _send_sms(self, user_id: int, content: str) -> bool:
        """发送短信"""
        try:
            phone_number = await self._get_user_phone(user_id)
            if not phone_number:
                return False

            # 这里应该调用短信服务API
            logger.debug(f"短信已发送: {phone_number}")
            return True

        except Exception as e:
            logger.error(f"发送短信失败: {e}")
            return False

    async def _send_in_app_notification(
        self, user_id: int, title: str, content: str, priority: str
    ) -> bool:
        """发送应用内通知"""
        try:
            notification_data = {
                "user_id": user_id,
                "title": title,
                "content": content,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "read": False,
            }

            # 存储到数据库或缓存
            await self._store_in_app_notification(notification_data)
            logger.debug(f"应用内通知已存储: 用户{user_id}")
            return True

        except Exception as e:
            logger.error(f"发送应用内通知失败: {e}")
            return False

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        result = template
        for key, value in data.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        return result

    def _check_cooldown(self, user_id: int, template_id: str) -> bool:
        """检查冷却时间"""
        template = self.templates.get(template_id)
        if not template or template.cooldown_hours == 0:
            return True

        if user_id not in self.notification_history:
            return True

        recent_notifications = [
            record
            for record in self.notification_history[user_id]
            if record["template_id"] == template_id
        ]

        if not recent_notifications:
            return True

        last_sent = max(record["sent_at"] for record in recent_notifications)
        cooldown_end = last_sent + timedelta(hours=template.cooldown_hours)

        return datetime.now() > cooldown_end

    def _record_notification_history(
        self, user_id: int, template_id: str, channels: List[str], data: Dict[str, Any]
    ):
        """记录通知历史"""
        if user_id not in self.notification_history:
            self.notification_history[user_id] = []

        record = {
            "template_id": template_id,
            "channels": channels,
            "data": data,
            "sent_at": datetime.now(),
            "notification_id": f"{user_id}_{template_id}_{int(datetime.now().timestamp())}",
        }

        self.notification_history[user_id].append(record)

        # 保持历史记录在合理范围内
        if len(self.notification_history[user_id]) > 100:
            self.notification_history[user_id] = self.notification_history[user_id][
                -100:
            ]

    def _get_user_preference(self, user_id: int) -> UserNotificationPreference:
        """获取用户通知偏好"""
        if user_id not in self.user_preferences:
            # 创建默认偏好
            self.user_preferences[user_id] = UserNotificationPreference(
                user_id=user_id,
                enabled_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.IN_APP,
                ],
                decay_warning_threshold=100,
                activity_reminder_days=3,
                timezone="Asia/Shanghai",
                language="zh-CN",
            )

        return self.user_preferences[user_id]

    async def schedule_activity_reminders(self):
        """安排活动提醒"""
        try:
            inactive_users = await self._find_inactive_users_for_reminder()

            for user_id in inactive_users:
                days_inactive = await self._get_user_days_inactive(user_id)
                preference = self._get_user_preference(user_id)

                if days_inactive >= preference.activity_reminder_days:
                    await self.send_notification(
                        user_id=user_id,
                        template_id="activity_reminder",
                        data={"days_since_activity": days_inactive},
                    )

        except Exception as e:
            logger.error(f"安排活动提醒失败: {e}")

    async def send_decay_projections(self):
        """发送衰减预测"""
        try:
            users_needing_projection = await self._find_users_needing_projection()

            for user_id in users_needing_projection:
                projection = decay_calculator.get_decay_projection(user_id, 30)
                if projection:
                    table_content = self._format_projection_table(projection)
                    recommendations = self._generate_recommendations(projection)

                    await self.send_notification(
                        user_id=user_id,
                        template_id="decay_projection",
                        data={
                            "projection_table": table_content,
                            "recommendations": recommendations,
                        },
                    )

        except Exception as e:
            logger.error(f"发送衰减预测失败: {e}")

    def _format_projection_table(self, projection: List[Dict[str, Any]]) -> str:
        """格式化预测表格"""
        table_lines = ["日期\t预计积分\t日衰减"]
        for item in projection[::5]:  # 每5天显示一次
            line = f"{item['date']}\t{item['projected_points']}\t{item['daily_decay']}"
            table_lines.append(line)
        return "\n".join(table_lines)

    def _generate_recommendations(self, projection: List[Dict[str, Any]]) -> str:
        """生成建议"""
        total_decay = sum(item["daily_decay"] for item in projection)
        if total_decay > 1000:
            return "• 建议每天完成至少一个任务\n• 参与多人协作项目\n• 完成挑战任务"
        elif total_decay > 500:
            return "• 保持每周3-4次活跃\n• 完成日常任务\n• 参与社区活动"
        else:
            return "• 继续保持当前活跃度\n• 尝试新的功能模块"

    # 以下方法需要根据实际的数据访问层实现
    async def _get_user_email(self, user_id: int) -> Optional[str]:
        return "user@example.com"

    async def _get_user_device_token(self, user_id: int) -> Optional[str]:
        return "device_token"

    async def _get_user_phone(self, user_id: int) -> Optional[str]:
        return "+8613800138000"

    async def _get_affected_users_from_decay(
        self, decay_data: Dict[str, Any]
    ) -> List[int]:
        return [1, 2, 3]

    async def _get_user_previous_points(self, user_id: int) -> int:
        return 1000

    async def _get_user_today_decay(self, user_id: int) -> int:
        return 50

    async def _get_user_current_points(self, user_id: int) -> int:
        return 950

    async def _get_user_total_decayed(self, user_id: int) -> int:
        return 200

    async def _find_inactive_users_for_reminder(self) -> List[int]:
        return [1001, 1002]

    async def _get_user_days_inactive(self, user_id: int) -> int:
        return 5

    async def _find_users_needing_projection(self) -> List[int]:
        return [2001, 2002]

    async def _store_in_app_notification(self, data: Dict[str, Any]):
        pass


# 全局实例
decay_notification_service = DecayNotificationService()
