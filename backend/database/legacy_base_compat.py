"""副 Base（database.db.Base）的 users 影子映射。

架构债背景：
    项目里存在多套 declarative_base：
      - 主 Base（utils.database.Base）：users / courses 等主业务表
      - 副 Base（database.db.Base）：achievements / leaderboard 等表
    副 Base 的模型用 relationship("User") 指向主 Base 的 users 表，
    但两个 registry 互不可见，configure_mappers() 直接抛
    "expression 'User' failed to locate a name"，导致成就 / 积分 /
    排行榜链路（含首启种子）被整体跳过。

最小修复：
    在副 Base 注册一个仅映射 users.id 的 User 影子类，让 relationship
    能解析。真正的用户字段读写仍走主 Base 的 User。
"""

from database.db import Base as LegacyBase
from database.shadow_registry import register_shadow_model

User = register_shadow_model(LegacyBase, "User", "users")
