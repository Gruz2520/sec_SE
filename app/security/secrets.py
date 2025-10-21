"""
Модуль управления секретами.

Реализует ADR-003: Управление секретами
"""

import logging
import os
import re
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional


class SecretsManager:
    """Менеджер секретов с защитой от утечек"""

    # Паттерны для обнаружения секретов
    SECRET_PATTERNS = [
        r'password\s*=\s*["\']?[^"\'\s]+["\']?',
        r'secret\s*=\s*["\']?[^"\'\s]+["\']?',
        r'api_key\s*=\s*["\']?[^"\'\s]+["\']?',
        r'token\s*=\s*["\']?[^"\'\s]+["\']?',
        r'key\s*=\s*["\']?[^"\'\s]+["\']?',
        r'pwd\s*=\s*["\']?[^"\'\s]+["\']?',
        r'pass\s*=\s*["\']?[^"\'\s]+["\']?',
    ]

    def __init__(self):
        self.secrets: Dict[str, Any] = {}
        self.rotation_dates: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Получение секрета из переменных окружения

        Args:
            key: Ключ секрета
            default: Значение по умолчанию

        Returns:
            Значение секрета или None
        """
        value = os.getenv(key, default)

        if value:
            if self._is_secret_in_code(value):
                self.logger.warning(f"Потенциальный секрет в коде для ключа: {key}")
                return None

            self.rotation_dates[key] = datetime.now()

        return value

    def get_required_secret(self, key: str) -> str:
        """
        Получение обязательного секрета

        Args:
            key: Ключ секрета

        Returns:
            Значение секрета

        Raises:
            ValueError: Если секрет не найден
        """
        value = self.get_secret(key)
        if not value:
            raise ValueError(f"Обязательный секрет {key} не найден")
        return value

    def _is_secret_in_code(self, value: str) -> bool:
        """Проверка, не является ли значение секретом в коде"""
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    def mask_secret(self, secret: str) -> str:
        """Маскирование секрета для логирования"""
        if not secret or len(secret) < 4:
            return "***"

        return secret[:2] + "*" * (len(secret) - 4) + secret[-2:]

    def validate_secrets_config(self) -> Dict[str, Any]:
        """
        Валидация конфигурации секретов

        Returns:
            Словарь с результатами валидации
        """
        results = {
            "valid": True,
            "missing_secrets": [],
            "expired_secrets": [],
            "warnings": [],
        }

        # Проверяем обязательные секреты
        required_secrets = ["DATABASE_URL", "SECRET_KEY", "JWT_SECRET"]

        for secret in required_secrets:
            if not self.get_secret(secret):
                results["missing_secrets"].append(secret)
                results["valid"] = False

        # Проверяем ротацию секретов
        for key, rotation_date in self.rotation_dates.items():
            if datetime.now() - rotation_date > timedelta(days=30):
                results["expired_secrets"].append(key)
                results["warnings"].append(f"Секрет {key} не обновлялся более 30 дней")

        return results

    def log_secret_access(self, secret_key: str, action: str):
        """Логирование доступа к секретам"""
        self.logger.info(f"Access to secret {secret_key}: {action}")

    def rotate_secret(self, key: str, new_value: str):
        """
        Ротация секрета

        Args:
            key: Ключ секрета
            new_value: Новое значение
        """
        old_value = self.get_secret(key)
        if old_value:
            self.logger.info(f"Rotating secret {key}")

        # В реальном приложении здесь можно было бы влепить интеграцию с Vault/KMS
        os.environ[key] = new_value
        self.rotation_dates[key] = datetime.now()

        self.logger.info(f"Secret {key} rotated successfully")


secrets_manager = SecretsManager()


def require_secret(secret_key: str):
    """Декоратор для проверки наличия секрета"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not secrets_manager.get_secret(secret_key):
                raise ValueError(f"Секрет {secret_key} не настроен")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def mask_in_logs(func):
    """Декоратор для маскирования секретов в логах"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_msg = str(e)
            for pattern in SecretsManager.SECRET_PATTERNS:
                error_msg = re.sub(
                    pattern,
                    lambda m: m.group(0).split("=")[0] + "=***",
                    error_msg,
                    flags=re.IGNORECASE,
                )

            logging.error(f"Error in {func.__name__}: {error_msg}")
            raise

    return wrapper


class SecureConfig:
    """Безопасная конфигурация приложения"""

    def __init__(self):
        self.secrets = secrets_manager

    def get_database_url(self) -> str:
        """Получение URL базы данных"""
        return self.secrets.get_required_secret("DATABASE_URL")

    def get_secret_key(self) -> str:
        """Получение секретного ключа"""
        return self.secrets.get_required_secret("SECRET_KEY")

    def get_jwt_secret(self) -> str:
        """Получение JWT секрета"""
        return self.secrets.get_required_secret("JWT_SECRET")

    def get_redis_url(self) -> Optional[str]:
        """Получение URL Redis (опционально)"""
        return self.secrets.get_secret("REDIS_URL")

    def validate_config(self) -> bool:
        """Валидация всей конфигурации"""
        results = self.secrets.validate_secrets_config()
        return results["valid"]


config = SecureConfig()
