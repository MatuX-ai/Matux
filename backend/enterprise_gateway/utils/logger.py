"""
企业网关日志工具模块
提供统一的日志配置和管理功能
"""

from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os


def setup_enterprise_logger(
    log_level: str = "INFO", log_file: str = "logs/enterprise_gateway.log"
) -> logging.Logger:
    """
    设置企业网关日志配置

    Args:
        log_level: 日志级别
        log_file: 日志文件路径

    Returns:
        配置好的Logger实例
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建logger
    logger = logging.getLogger("enterprise_gateway")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )

    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def log_enterprise_event(
    logger: logging.Logger, event_type: str, client_id: str, details: dict = None
):
    """
    记录企业网关事件日志

    Args:
        logger: Logger实例
        event_type: 事件类型
        client_id: 企业客户ID
        details: 详细信息
    """
    log_data = {
        "event_type": event_type,
        "client_id": client_id,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {},
    }

    logger.info(f"Enterprise Event: {log_data}")


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    client_id: str,
    severity: str = "INFO",
    details: dict = None,
):
    """
    记录安全相关事件

    Args:
        logger: Logger实例
        event_type: 事件类型
        client_id: 企业客户ID
        severity: 严重程度
        details: 详细信息
    """
    log_data = {
        "event_type": event_type,
        "client_id": client_id,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {},
    }

    if severity.upper() == "CRITICAL":
        logger.critical(f"Security Event: {log_data}")
    elif severity.upper() == "ERROR":
        logger.error(f"Security Event: {log_data}")
    elif severity.upper() == "WARNING":
        logger.warning(f"Security Event: {log_data}")
    else:
        logger.info(f"Security Event: {log_data}")
