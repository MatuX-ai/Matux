"""
【P3-C】短链生成工具

生成短链代码（base62 字母数字混合），用于分享卡片和邀请码。

特性：
- 使用 secrets 模块保证密码学强度随机性
- 默认 8 字符（base62 约 218 万亿种组合，足够不冲突）
- 支持自定义长度
- 提供唯一性生成函数（带重试上限）

使用：
    code = generate_short_code()           # 生成 8 字符短链
    code = generate_short_code(10)        # 生成 10 字符短链

    # 唯一性生成（带 DB 唯一性校验）
    def check_exists(code):
        return db.query(ShareCard).filter_by(short_code=code).first() is not None
    code = generate_unique_short_code(check_exists)
"""
import secrets
import string
from typing import Callable


# base62 字母表（a-z, A-Z, 0-9）
_ALPHABET = string.ascii_letters + string.digits

# 默认短链长度
DEFAULT_LENGTH = 8

# 最大重试次数（防止唯一性检查卡死）
MAX_RETRY = 5


def generate_short_code(length: int = DEFAULT_LENGTH) -> str:
    """
    生成随机短链代码

    Args:
        length: 字符串长度（默认 8）

    Returns:
        str: 随机短链代码

    Raises:
        ValueError: 长度无效时
    """
    if length < 1:
        raise ValueError(f"短链长度必须 >= 1，实际 {length}")
    if length > 32:
        raise ValueError(f"短链长度过长（最大 32），实际 {length}")

    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def generate_unique_short_code(
    check_exists: Callable[[str], bool],
    max_retry: int = MAX_RETRY,
    length: int = DEFAULT_LENGTH,
) -> str:
    """
    生成唯一短链代码（依赖 check_exists 回调判断是否已存在）

    Args:
        check_exists: 回调函数，接收 code 返回是否已存在（True=已存在，需重试）
        max_retry: 最大重试次数（默认 5）
        length: 短链长度（默认 8）

    Returns:
        str: 唯一短链代码

    Raises:
        RuntimeError: 达到最大重试次数仍未生成唯一短链
    """
    for attempt in range(max_retry):
        code = generate_short_code(length)
        if not check_exists(code):
            return code
    raise RuntimeError(
        f"短链生成失败：达到最大重试次数 {max_retry}（考虑增加 length）"
    )


# ==================== 唯一性理论分析 ====================
# base62 8 位短链：62^8 ≈ 218 万亿种组合
# 碰撞概率（生日悖论）：
# - 100 万条记录：约 1/4.4 亿 概率碰撞
# - 10 万条记录：约 1/440 万 概率碰撞
# - 1 万条记录：约 1/4400 万 概率碰撞
# 结论：8 位 base62 在 10 万级别数据下碰撞概率极低
# 对于更大规模，建议：
# - 增加 length（9-10 位）
# - 或使用 hashids（有规律的可解码短链）


__all__ = [
    "generate_short_code",
    "generate_unique_short_code",
    "DEFAULT_LENGTH",
    "MAX_RETRY",
]