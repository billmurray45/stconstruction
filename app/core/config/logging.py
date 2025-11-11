import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config.settings import settings


# Создание директории для логов
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Настройка логирования для приложения
    - Development: Console + File (DEBUG уровень)
    - Production: File только (INFO уровень)
    """

    # Определяем уровень логирования
    log_level = logging.DEBUG if not settings.is_production else logging.INFO

    # Формат логов
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Очистка существующих handlers (если есть)
    root_logger.handlers.clear()

    # 1. Console Handler (всегда в development, WARNING в production)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if not settings.is_production else logging.WARNING)
    console_formatter = logging.Formatter(log_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 2. File Handler - Основной лог (app.log)
    app_log_file = LOGS_DIR / "app.log"
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 3. File Handler - Только ошибки (errors.log)
    error_log_file = LOGS_DIR / "errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # Отключаем логи библиотек (слишком много шума)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Логируем успешную инициализацию
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Environment: {settings.ENVIRONMENT}, Level: {logging.getLevelName(log_level)}")

    return logger


# Хелпер для логирования событий безопасности
def log_security_event(event_type: str, details: dict, level: str = "WARNING"):
    """
    Логирование событий безопасности

    Args:
        event_type: Тип события (login_failed, csrf_error, rate_limit, etc.)
        details: Детали события (ip, user_email, endpoint, etc.)
        level: Уровень логирования (INFO, WARNING, ERROR)
    """
    logger = logging.getLogger("security")

    # Маскируем чувствительные данные
    safe_details = details.copy()
    if "password" in safe_details:
        safe_details["password"] = "***"
    if "token" in safe_details:
        safe_details["token"] = "***"

    message = f"[{event_type.upper()}] {' | '.join(f'{k}={v}' for k, v in safe_details.items())}"

    log_func = getattr(logger, level.lower(), logger.warning)
    log_func(message)


# Получение logger для модуля
def get_logger(name: str) -> logging.Logger:
    """Получить logger для конкретного модуля"""
    return logging.getLogger(name)
