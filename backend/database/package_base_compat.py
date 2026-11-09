"""database 包级 Base（database.Base）的跨 Base 影子映射。

架构债背景：
    `database/__init__.py` 又声明了一个 declarative_base（database.Base），
    content_store / hardware_module 等模型基于它定义，但同样用
    relationship("User") / relationship("UserLicense") 指向 users 与
    user_licenses 表 —— 该 registry 里没有对应类，configure_mappers()
    会整体失败，连带成就 / 积分 / 排行榜 mapper 都无法初始化。

最小修复：
    在 database.Base 注册只含主键的影子类供 relationship 解析。
"""

from database import Base as PackageBase
from database.shadow_registry import register_shadow_model

User = register_shadow_model(PackageBase, "User", "users")
UserLicense = register_shadow_model(PackageBase, "UserLicense", "user_licenses")
