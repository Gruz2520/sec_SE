"""
Тесты для модуля управления секретами.

Проверяет реализацию ADR-003
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.secrets import SecretsManager, SecureConfig, config, secrets_manager

client = TestClient(app)


class TestSecretsManager:
    """Тесты класса SecretsManager"""

    def test_get_secret_from_environment(self):
        """Тест получения секрета из переменных окружения"""
        manager = SecretsManager()

        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            secret = manager.get_secret("TEST_SECRET")
            assert secret == "test_value"

    def test_get_secret_with_default(self):
        """Тест получения секрета со значением по умолчанию"""
        manager = SecretsManager()

        secret = manager.get_secret("NONEXISTENT_SECRET", default="default_value")
        assert secret == "default_value"

    def test_get_required_secret_success(self):
        """Тест получения обязательного секрета (успех)"""
        manager = SecretsManager()

        with patch.dict(os.environ, {"REQUIRED_SECRET": "required_value"}):
            secret = manager.get_required_secret("REQUIRED_SECRET")
            assert secret == "required_value"

    def test_get_required_secret_missing(self):
        """Тест получения обязательного секрета (отсутствует)"""
        manager = SecretsManager()

        with pytest.raises(ValueError) as exc_info:
            manager.get_required_secret("MISSING_SECRET")

        assert "Обязательный секрет MISSING_SECRET не найден" in str(exc_info.value)

    def test_mask_secret(self):
        """Тест маскирования секрета"""
        manager = SecretsManager()

        masked = manager.mask_secret("very_long_secret_key_12345")
        assert masked == "ve**********************45"

        masked = manager.mask_secret("abc")
        assert masked == "***"

        masked = manager.mask_secret("")
        assert masked == "***"

    def test_detect_secret_in_code(self):
        """Тест обнаружения секретов в коде"""
        manager = SecretsManager()

        secret_patterns = [
            'password="secret123"',
            "api_key=abc123def456",
            'token = "my_token"',
            "secret=very_secret_value",
            "pwd=password123",
        ]

        for pattern in secret_patterns:
            assert manager._is_secret_in_code(pattern) is True

        normal_strings = [
            'name="John Doe"',
            "age=25",
            'city="New York"',
            'description="Some text"',
        ]

        for normal_string in normal_strings:
            assert manager._is_secret_in_code(normal_string) is False

    def test_validate_secrets_config_success(self):
        """Тест валидации конфигурации секретов (успех)"""
        manager = SecretsManager()

        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
                "SECRET_KEY": "secret_key_123",
                "JWT_SECRET": "jwt_secret_456",
            },
        ):
            results = manager.validate_secrets_config()

            assert results["valid"] is True
            assert len(results["missing_secrets"]) == 0
            assert len(results["expired_secrets"]) == 0

    def test_validate_secrets_config_missing_secrets(self):
        """Тест валидации конфигурации секретов (отсутствующие секреты)"""
        manager = SecretsManager()

        with patch.dict(os.environ, {}, clear=True):
            results = manager.validate_secrets_config()

            assert results["valid"] is False
            assert "DATABASE_URL" in results["missing_secrets"]
            assert "SECRET_KEY" in results["missing_secrets"]
            assert "JWT_SECRET" in results["missing_secrets"]

    def test_rotate_secret(self):
        """Тест ротации секрета"""
        manager = SecretsManager()

        with patch.dict(os.environ, {"OLD_SECRET": "old_value"}):
            manager.rotate_secret("OLD_SECRET", "new_value")

            assert os.getenv("OLD_SECRET") == "new_value"

            assert "OLD_SECRET" in manager.rotation_dates

    def test_log_secret_access(self):
        """Тест логирования доступа к секретам"""
        manager = SecretsManager()

        with patch.object(manager.logger, "info") as mock_logger:
            manager.log_secret_access("TEST_SECRET", "read")
            mock_logger.assert_called_once_with("Access to secret TEST_SECRET: read")


class TestSecureConfig:
    """Тесты класса SecureConfig"""

    def test_get_database_url(self):
        """Тест получения URL базы данных"""
        secure_config = SecureConfig()

        with patch.dict(
            os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost/db"}
        ):
            db_url = secure_config.get_database_url()
            assert db_url == "postgresql://user:pass@localhost/db"

    def test_get_database_url_missing(self):
        """Тест получения URL базы данных (отсутствует)"""
        secure_config = SecureConfig()

        with pytest.raises(ValueError):
            secure_config.get_database_url()

    def test_get_secret_key(self):
        """Тест получения секретного ключа"""
        secure_config = SecureConfig()

        with patch.dict(os.environ, {"SECRET_KEY": "my_secret_key"}):
            secret_key = secure_config.get_secret_key()
            assert secret_key == "my_secret_key"

    def test_get_jwt_secret(self):
        """Тест получения JWT секрета"""
        secure_config = SecureConfig()

        with patch.dict(os.environ, {"JWT_SECRET": "jwt_secret_key"}):
            jwt_secret = secure_config.get_jwt_secret()
            assert jwt_secret == "jwt_secret_key"

    def test_get_redis_url_optional(self):
        """Тест получения URL Redis (опционально)"""
        secure_config = SecureConfig()

        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
            redis_url = secure_config.get_redis_url()
            assert redis_url == "redis://localhost:6379"

        with patch.dict(os.environ, {}, clear=True):
            redis_url = secure_config.get_redis_url()
            assert redis_url is None

    def test_validate_config_success(self):
        """Тест валидации конфигурации (успех)"""
        secure_config = SecureConfig()

        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
                "SECRET_KEY": "secret_key_123",
                "JWT_SECRET": "jwt_secret_456",
            },
        ):
            is_valid = secure_config.validate_config()
            assert is_valid is True

    def test_validate_config_failure(self):
        """Тест валидации конфигурации (ошибка)"""
        secure_config = SecureConfig()

        with patch.dict(os.environ, {}, clear=True):
            is_valid = secure_config.validate_config()
            assert is_valid is False


class TestSecretsDecorators:
    """Тесты декораторов для секретов"""

    def test_require_secret_decorator_success(self):
        """Тест декоратора require_secret (успех)"""
        from app.security.secrets import require_secret

        @require_secret("TEST_SECRET")
        def test_function():
            return "success"

        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            result = test_function()
            assert result == "success"

    def test_require_secret_decorator_failure(self):
        """Тест декоратора require_secret (ошибка)"""
        from app.security.secrets import require_secret

        @require_secret("MISSING_SECRET")
        def test_function():
            return "success"

        with pytest.raises(ValueError) as exc_info:
            test_function()

        assert "Секрет MISSING_SECRET не настроен" in str(exc_info.value)

    def test_mask_in_logs_decorator(self):
        """Тест декоратора mask_in_logs"""
        from app.security.secrets import mask_in_logs

        @mask_in_logs
        def test_function_with_secret():
            raise Exception("Error with password=secret123")

        with patch("logging.error") as mock_logger:
            with pytest.raises(Exception):
                test_function_with_secret()

            mock_logger.assert_called_once()
            log_message = mock_logger.call_args[0][0]
            assert "password=***" in log_message
            assert "secret123" not in log_message


class TestAPIHealthSecrets:
    """Тесты API для проверки состояния секретов"""

    def test_health_secrets_success(self):
        """Тест эндпойнта /health/secrets (успех)"""
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://user:pass@localhost/db",
                "SECRET_KEY": "secret_key_123",
                "JWT_SECRET": "jwt_secret_456",
            },
        ):
            response = client.get("/health/secrets")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "secrets_validation" in data

    def test_health_secrets_failure(self):
        """Тест эндпойнта /health/secrets (ошибка)"""
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/health/secrets")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "secrets_validation" in data

    def test_health_secrets_exception(self):
        """Тест эндпойнта /health/secrets (исключение)"""
        with patch.object(
            secrets_manager,
            "validate_secrets_config",
            side_effect=Exception("Test error"),
        ):
            response = client.get("/health/secrets")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to validate secrets configuration" in data["message"]


class TestSecretsIntegration:
    """Интеграционные тесты для секретов"""

    def test_secrets_manager_global_instance(self):
        """Тест глобального экземпляра SecretsManager"""
        assert secrets_manager is not None
        assert isinstance(secrets_manager, SecretsManager)

    def test_config_global_instance(self):
        """Тест глобального экземпляра SecureConfig"""
        assert config is not None
        assert isinstance(config, SecureConfig)

    def test_secrets_patterns_comprehensive(self):
        """Тест всех паттернов обнаружения секретов"""
        manager = SecretsManager()

        test_cases = [
            ('password="secret"', True),
            ('password = "secret"', True),
            ("api_key=abc123", True),
            ('token="my_token"', True),
            ("secret=value", True),
            ('key="secret_key"', True),
            ("pwd=password", True),
            ("pass=secret", True),
            ('name="John"', False),
            ("age=25", False),
            ('description="text"', False),
        ]

        for test_input, expected in test_cases:
            result = manager._is_secret_in_code(test_input)
            assert result == expected, f"Failed for input: {test_input}"

    def test_secrets_rotation_tracking(self):
        """Тест отслеживания ротации секретов"""
        manager = SecretsManager()

        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            secret = manager.get_secret("TEST_SECRET")
            assert secret == "test_value"

            assert "TEST_SECRET" in manager.rotation_dates

            from datetime import datetime, timedelta

            rotation_date = manager.rotation_dates["TEST_SECRET"]
            assert datetime.now() - rotation_date < timedelta(seconds=1)
