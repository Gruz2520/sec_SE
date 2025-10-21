"""
Модуль обработки ошибок в формате RFC 7807.

Реализует ADR-002
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class RFC7807Error:
    """Класс для создания ошибок в формате RFC 7807"""

    ERROR_TYPES = {
        "validation-error": {
            "type": "https://api.wishlist.com/errors/validation-error",
            "title": "Validation Error",
        },
        "not-found": {
            "type": "https://api.wishlist.com/errors/not-found",
            "title": "Not Found",
        },
        "authentication-error": {
            "type": "https://api.wishlist.com/errors/authentication-error",
            "title": "Authentication Error",
        },
        "authorization-error": {
            "type": "https://api.wishlist.com/errors/authorization-error",
            "title": "Authorization Error",
        },
        "rate-limit-error": {
            "type": "https://api.wishlist.com/errors/rate-limit-error",
            "title": "Rate Limit Exceeded",
        },
        "internal-error": {
            "type": "https://api.wishlist.com/errors/internal-error",
            "title": "Internal Server Error",
        },
    }

    def __init__(
        self,
        error_type: str,
        status: int,
        detail: str,
        instance: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        self.error_type = error_type
        self.status = status
        self.detail = detail
        self.instance = instance
        self.correlation_id = correlation_id or str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON ответа"""
        error_info = self.ERROR_TYPES.get(
            self.error_type,
            {
                "type": f"https://api.wishlist.com/errors/{self.error_type}",
                "title": "Unknown Error",
            },
        )

        return {
            "type": error_info["type"],
            "title": error_info["title"],
            "status": self.status,
            "detail": self._mask_pii(self.detail),
            "instance": self.instance or "/",
            "correlation_id": self.correlation_id,
            "timestamp": datetime.now().isoformat() + "Z",
        }

    def _mask_pii(self, text: str) -> str:
        """Маскирование PII данных в тексте"""
        if not text:
            return text

        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***@***.***", text
        )

        text = re.sub(
            r"\b[A-Za-z0-9]{10,}(?=\b)",
            lambda m: (
                "***TOKEN***" if any(c.isdigit() for c in m.group()) else m.group()
            ),
            text,
        )

        text = re.sub(r"/[A-Za-z0-9/._-]+", "/***PATH***", text)

        text = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "***.***.***.***", text)

        return text


class ErrorHandler:
    """Обработчик ошибок с поддержкой RFC 7807"""

    def __init__(self):
        self.correlation_id_header = "X-Correlation-ID"

    def create_error_response(
        self, error: RFC7807Error, request: Request
    ) -> JSONResponse:
        """Создание JSON ответа с ошибкой"""
        error_dict = error.to_dict()

        headers = {self.correlation_id_header: error.correlation_id}

        return JSONResponse(
            status_code=error.status, content=error_dict, headers=headers
        )

    def get_correlation_id(self, request: Request) -> str:
        """Получение correlation_id из запроса или генерация нового"""
        correlation_id = request.headers.get(self.correlation_id_header)

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        return correlation_id

    def mask_sensitive_data(self, data: Any) -> Any:
        """Рекурсивное маскирование чувствительных данных"""
        if isinstance(data, str):
            return self._mask_pii(data)
        elif isinstance(data, dict):
            return {k: self.mask_sensitive_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.mask_sensitive_data(item) for item in data]
        else:
            return data

    def _mask_pii(self, text: str) -> str:
        """Маскирование PII данных в тексте"""
        if not text:
            return text

        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***@***.***", text
        )

        text = re.sub(
            r"\b[A-Za-z0-9]{10,}(?=\b)",
            lambda m: (
                "***TOKEN***" if any(c.isdigit() for c in m.group()) else m.group()
            ),
            text,
        )

        text = re.sub(r"/[A-Za-z0-9/._-]+", "/***PATH***", text)

        text = re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "***.***.***.***", text)

        return text


error_handler = ErrorHandler()


def create_validation_error(
    detail: str, instance: str, correlation_id: str
) -> RFC7807Error:
    """Создание ошибки валидации"""
    return RFC7807Error(
        error_type="validation-error",
        status=400,
        detail=detail,
        instance=instance,
        correlation_id=correlation_id,
    )


def create_not_found_error(
    detail: str, instance: str, correlation_id: str
) -> RFC7807Error:
    """Создание ошибки 'не найдено'"""
    return RFC7807Error(
        error_type="not-found",
        status=404,
        detail=detail,
        instance=instance,
        correlation_id=correlation_id,
    )


def create_internal_error(
    detail: str, instance: str, correlation_id: str
) -> RFC7807Error:
    """Создание внутренней ошибки сервера"""
    return RFC7807Error(
        error_type="internal-error",
        status=500,
        detail=detail,
        instance=instance,
        correlation_id=correlation_id,
    )


def create_rate_limit_error(
    detail: str, instance: str, correlation_id: str
) -> RFC7807Error:
    """Создание ошибки превышения лимита"""
    return RFC7807Error(
        error_type="rate-limit-error",
        status=429,
        detail=detail,
        instance=instance,
        correlation_id=correlation_id,
    )
