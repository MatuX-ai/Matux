"""
日志配置工具模块
"""

import logging
import os


def setup_logger(level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    配置应用日志

    Args:
        level: 日志级别
        log_file: 日志文件路径

    Returns:
        配置好的logger实例
    """
    # 创建logger
    logger = logging.getLogger("ai_service")
    logger.setLevel(getattr(logging, level))

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 创建格式器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )

    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取指定名称的logger

    Args:
        name: logger名称

    Returns:
        logger实例
    """
    if name:
        return logging.getLogger(f"ai_service.{name}")
    return logging.getLogger("ai_service")
