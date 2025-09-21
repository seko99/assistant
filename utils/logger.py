"""
Unified logging module for the Speech Assistant application.
Provides centralized logging configuration and emoji-enhanced formatters.
"""

import logging
import sys
from typing import Optional


class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis to log messages based on level"""

    EMOJI_MAP = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '💥'
    }

    def format(self, record):
        # Добавляем эмодзи в начало сообщения
        emoji = self.EMOJI_MAP.get(record.levelname, '📝')
        original_msg = super().format(record)
        return f"{emoji} {original_msg}"


class AssistantLogger:
    """Централизованный логгер для Speech Assistant"""

    def __init__(self, name: str = 'assistant', level: str = 'INFO', use_emoji: bool = True):
        self.logger = logging.getLogger(name)
        self.use_emoji = use_emoji

        # Предотвращаем дублирование хендлеров
        if not self.logger.handlers:
            self._setup_logger(level)

    def _setup_logger(self, level: str):
        """Настраивает логгер с консольным выводом"""
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        # Создаем консольный хендлер
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.logger.level)

        # Выбираем форматтер
        if self.use_emoji:
            formatter = EmojiFormatter('%(message)s')
        else:
            formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        """Отладочное сообщение"""
        self.logger.debug(message)

    def info(self, message: str):
        """Информационное сообщение"""
        self.logger.info(message)

    def warning(self, message: str):
        """Предупреждение"""
        self.logger.warning(message)

    def error(self, message: str):
        """Ошибка"""
        self.logger.error(message)

    def critical(self, message: str):
        """Критическая ошибка"""
        self.logger.critical(message)


# Создаем глобальный экземпляр логгера
_global_logger: Optional[AssistantLogger] = None


def get_logger(name: str = 'assistant', level: str = 'INFO', use_emoji: bool = True) -> AssistantLogger:
    """
    Получает экземпляр логгера с заданными параметрами

    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_emoji: Использовать эмодзи в сообщениях

    Returns:
        Экземпляр AssistantLogger
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = AssistantLogger(name, level, use_emoji)

    return _global_logger


def setup_logging_from_config(config: dict) -> AssistantLogger:
    """
    Настраивает логирование на основе конфигурации

    Args:
        config: Словарь конфигурации

    Returns:
        Настроенный логгер
    """
    interface_config = config.get('interface', {})

    # Получаем настройки из конфига
    use_emoji = interface_config.get('use_emoji', True)
    verbose = interface_config.get('verbose', True)

    # Определяем уровень логирования
    level = 'DEBUG' if verbose else 'INFO'

    return get_logger('assistant', level, use_emoji)


# Convenience функции для быстрого логирования
def log_debug(message: str):
    """Быстрое логирование отладочного сообщения"""
    get_logger().debug(message)


def log_info(message: str):
    """Быстрое логирование информационного сообщения"""
    get_logger().info(message)


def log_warning(message: str):
    """Быстрое логирование предупреждения"""
    get_logger().warning(message)


def log_error(message: str):
    """Быстрое логирование ошибки"""
    get_logger().error(message)


def log_critical(message: str):
    """Быстрое логирование критической ошибки"""
    get_logger().critical(message)