"""
【P3-C】二维码生成工具

基于 qrcode + Pillow 生成分享卡片对应的二维码图片。

特性：
- 高纠错率（ERROR_CORRECT_M，约 15% 数据丢失可恢复）
- 自适应大小（box_size）
- 自动创建父目录
- 支持 PNG 输出

使用：
    path = generate_qr_code(
        url="https://imato.app/share/abc12345",
        save_path=Path("static/qrcodes/abc12345.png"),
    )
"""
import io
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


def generate_qr_code(
    url: str,
    save_path: Union[str, Path],
    box_size: int = 10,
    border: int = 2,
    error_correction: str = "M",
    fill_color: str = "black",
    back_color: str = "white",
) -> Path:
    """
    生成二维码图片

    Args:
        url: 要编码的 URL（短链）
        save_path: 保存路径
        box_size: 每个方块像素大小（默认 10）
        border: 边框宽度（默认 2 个方块）
        error_correction: 纠错级别 L/M/Q/H（默认 M = 15%）
        fill_color: 前景色
        back_color: 背景色

    Returns:
        Path: 实际保存路径

    Raises:
        ImportError: 缺少 qrcode/Pillow 依赖
    """
    try:
        import qrcode
        from qrcode.constants import (
            ERROR_CORRECT_H,
            ERROR_CORRECT_L,
            ERROR_CORRECT_M,
            ERROR_CORRECT_Q,
        )
    except ImportError as e:
        raise ImportError(
            "二维码生成需要 qrcode 库，请运行：pip install 'qrcode[pil]'"
        ) from e

    # 纠错级别映射
    ec_map = {
        "L": ERROR_CORRECT_L,   # 7%
        "M": ERROR_CORRECT_M,   # 15%
        "Q": ERROR_CORRECT_Q,   # 25%
        "H": ERROR_CORRECT_H,   # 30%
    }

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=ec_map.get(error_correction, ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img.save(save_path)

    logger.debug(f"二维码已生成：{save_path}（{save_path.stat().st_size} bytes）")
    return save_path


def generate_qr_code_bytes(
    url: str,
    box_size: int = 10,
    border: int = 2,
    error_correction: str = "M",
    fill_color: str = "black",
    back_color: str = "white",
    img_format: str = "PNG",
) -> bytes:
    """
    生成二维码图片并返回二进制数据（适用于 FileResponse 响应）

    Args:
        url: 要编码的 URL
        box_size: 方块大小
        border: 边框宽度
        error_correction: 纠错级别 L/M/Q/H
        fill_color: 前景色
        back_color: 背景色
        img_format: 图片格式 PNG/JPEG

    Returns:
        bytes: 二进制图片数据
    """
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q
    except ImportError as e:
        raise ImportError(
            "二维码生成需要 qrcode 库，请运行：pip install 'qrcode[pil]'"
        ) from e

    ec_map = {
        "L": ERROR_CORRECT_L,
        "M": ERROR_CORRECT_M,
        "Q": ERROR_CORRECT_Q,
        "H": ERROR_CORRECT_H,
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=ec_map.get(error_correction, ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buf = io.BytesIO()
    img.save(buf, format=img_format)
    return buf.getvalue()


def generate_qr_with_logo(
    url: str,
    save_path: Union[str, Path],
    logo_path: Optional[Union[str, Path]] = None,
    logo_size_ratio: float = 0.2,
    box_size: int = 10,
    border: int = 2,
) -> Path:
    """
    生成带中心 Logo 的二维码（高级功能）

    Args:
        url: 短链 URL
        save_path: 保存路径
        logo_path: 中心 Logo 图片路径（可选）
        logo_size_ratio: Logo 占二维码宽度的比例（默认 0.2 = 20%）
        box_size: 方块大小
        border: 边框宽度

    Returns:
        Path: 保存路径
    """
    try:
        import qrcode
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "二维码生成需要 qrcode + Pillow 库"
        ) from e

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 必须 H 才容得下 Logo
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if logo_path and Path(logo_path).exists():
        logo = Image.open(logo_path)
        logo_size = int(img.size[0] * logo_size_ratio)
        logo = logo.resize((logo_size, logo_size))
        # 居中粘贴
        pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
        img.paste(logo, pos)

    img.save(save_path)
    logger.debug(f"带 Logo 二维码已生成：{save_path}")
    return save_path


__all__ = [
    "generate_qr_code",
    "generate_qr_code_bytes",
    "generate_qr_with_logo",
]