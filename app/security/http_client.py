"""
Модуль безопасного HTTP-клиента.

Реализует безопасные HTTP-запросы с таймаутами, ретраями и лимитами.
"""

import time
from typing import Any, Dict, Optional

import httpx


class SecureHTTPClient:
    """Безопасный HTTP-клиент с таймаутами и ретраями"""

    DEFAULT_TIMEOUT = httpx.Timeout(5.0, read=5.0, connect=3.0)
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 0.5
    DEFAULT_MAX_REDIRECTS = 5

    def __init__(
        self,
        timeout: Optional[httpx.Timeout] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
    ):
        """
        Инициализация безопасного HTTP-клиента

        Args:
            timeout: Таймауты для запросов
            max_retries: Максимальное количество попыток
            retry_delay: Задержка между попытками (базовая)
            max_redirects: Максимальное количество редиректов
        """
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_redirects = max_redirects

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Безопасный GET запрос с ретраями

        Args:
            url: URL для запроса
            headers: Заголовки запроса
            params: Параметры запроса

        Returns:
            Response объект

        Raises:
            httpx.HTTPError: При ошибке после всех попыток
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(
                    timeout=self.timeout,
                    follow_redirects=True,
                    max_redirects=self.max_redirects,
                ) as client:
                    response = client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    return response

            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Экспоненциальная задержка
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    raise

        # Если все попытки исчерпаны
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("Все попытки запроса исчерпаны")

    def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Безопасный POST запрос с ретраями

        Args:
            url: URL для запроса
            json: JSON данные
            data: Form данные
            headers: Заголовки запроса

        Returns:
            Response объект

        Raises:
            httpx.HTTPError: При ошибке после всех попыток
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(
                    timeout=self.timeout,
                    follow_redirects=True,
                    max_redirects=self.max_redirects,
                ) as client:
                    response = client.post(url, json=json, data=data, headers=headers)
                    response.raise_for_status()
                    return response

            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Экспоненциальная задержка
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)
                else:
                    raise

        # Если все попытки исчерпаны
        if last_exception:
            raise last_exception
        raise httpx.HTTPError("Все попытки запроса исчерпаны")

    def health_check(self, url: str) -> bool:
        """
        Проверка доступности сервиса

        Args:
            url: URL для проверки

        Returns:
            True если сервис доступен, False иначе
        """
        try:
            response = self.get(url)
            return response.status_code == 200
        except Exception:
            return False


# Глобальный экземпляр безопасного HTTP-клиента
secure_http_client = SecureHTTPClient()
