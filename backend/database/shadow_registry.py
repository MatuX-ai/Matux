"""为「独立 declarative_base」注册跨 Base relationship 的影子类。

架构债背景：
    仓库里存在多个独立的 declarative_base（utils.database.Base、
    database.db.Base、database.Base、models.subscription.Base 等），
    而各模型普遍用 relationship("User") / relationship("UserLicense")
    指向别的 Base 里的类。registry 互不可见 → configure_mappers() 抛
    "expression 'User' failed to locate a name"，整条 ORM 链路（含首启
    种子）被跳过。

最小修复：
    在目标 Base 注册一个只映射主键的影子类，让 relationship 能解析。
    影子类仅供 ORM 关系占位，不得用于业务查询。
"""

from sqlalchemy import Column, Integer, Table


def register_shadow_model(base, class_name: str, table_name: str):
    """在 base 的 metadata 中注册只含主键的占位模型。"""
    table = base.metadata.tables.get(table_name)
    if table is None:
        table = Table(
            table_name,
            base.metadata,
            Column("id", Integer, primary_key=True),
        )
    return type(
        class_name,
        (base,),
        {"__table__": table, "__module__": __name__},
    )
