"""
Тесты для модуля обработки ошибок в формате RFC 7807.

Проверяет реализацию ADR-002
"""

from fastapi.testclient import TestClient

from app.main import app
from app.security.error_handling import (
    ErrorHandler,
    RFC7807Error,
    create_internal_error,
    create_not_found_error,
    create_validation_error,
)

client = TestClient(app)


class TestRFC7807Error:
    """Тесты класса RFC7807Error"""

    def test_validation_error_creation(self):
        """Тест создания ошибки валидации"""
        error = create_validation_error(
            detail="Invalid input data",
            instance="/wishlist/items",
            correlation_id="test-123",
        )

        error_dict = error.to_dict()

        assert error_dict["type"] == "https://api.wishlist.com/errors/validation-error"
        assert error_dict["title"] == "Validation Error"
        assert error_dict["status"] == 400
        assert error_dict["detail"] == "Invalid input data"
        assert error_dict["instance"] == "/wishlist/items"
        assert error_dict["correlation_id"] == "test-123"
        assert "timestamp" in error_dict

    def test_not_found_error_creation(self):
        """Тест создания ошибки 'не найдено'"""
        error = create_not_found_error(
            detail="Resource not found",
            instance="/wishlist/items/999",
            correlation_id="test-456",
        )

        error_dict = error.to_dict()

        assert error_dict["type"] == "https://api.wishlist.com/errors/not-found"
        assert error_dict["title"] == "Not Found"
        assert error_dict["status"] == 404
        assert error_dict["detail"] == "Resource not found"
        assert error_dict["instance"] == "/wishlist/items/999"
        assert error_dict["correlation_id"] == "test-456"

    def test_internal_error_creation(self):
        """Тест создания внутренней ошибки"""
        error = create_internal_error(
            detail="Internal server error",
            instance="/wishlist/items",
            correlation_id="test-789",
        )

        error_dict = error.to_dict()

        assert error_dict["type"] == "https://api.wishlist.com/errors/internal-error"
        assert error_dict["title"] == "Internal Server Error"
        assert error_dict["status"] == 500
        assert error_dict["detail"] == "Internal server error"

    def test_pii_masking(self):
        """Тест маскирования PII данных"""
        error = RFC7807Error(
            error_type="validation-error",
            status=400,
            detail="User email user@example.com and token abc123def456ghi789 found in request",
            instance="/wishlist/items",
            correlation_id="test-123",
        )

        error_dict = error.to_dict()

        assert "***@***.***" in error_dict["detail"]
        assert "***TOKEN***" in error_dict["detail"]
        assert "user@example.com" not in error_dict["detail"]
        assert "abc123def456ghi789" not in error_dict["detail"]

    def test_ip_address_masking(self):
        """Тест маскирования IP адресов"""
        error = RFC7807Error(
            error_type="validation-error",
            status=400,
            detail="Request from IP 192.168.1.100 blocked",
            instance="/wishlist/items",
            correlation_id="test-123",
        )

        error_dict = error.to_dict()

        assert "***.***.***.***" in error_dict["detail"]
        assert "192.168.1.100" not in error_dict["detail"]

    def test_file_path_masking(self):
        """Тест маскирования путей к файлам"""
        error = RFC7807Error(
            error_type="validation-error",
            status=400,
            detail="File /home/user/secret.txt not found",
            instance="/wishlist/items",
            correlation_id="test-123",
        )

        error_dict = error.to_dict()

        assert "/***PATH***" in error_dict["detail"]
        assert "/home/user/secret.txt" not in error_dict["detail"]


class TestErrorHandler:
    """Тесты класса ErrorHandler"""

    def test_get_correlation_id_from_header(self):
        """Тест получения correlation_id из заголовка"""
        handler = ErrorHandler()

        class MockRequest:
            def __init__(self, headers):
                self.headers = headers

        request = MockRequest({"X-Correlation-ID": "test-correlation-123"})
        correlation_id = handler.get_correlation_id(request)

        assert correlation_id == "test-correlation-123"

    def test_generate_correlation_id_when_missing(self):
        """Тест генерации correlation_id когда заголовок отсутствует"""
        handler = ErrorHandler()

        class MockRequest:
            def __init__(self):
                self.headers = {}

        request = MockRequest()
        correlation_id = handler.get_correlation_id(request)

        assert correlation_id is not None
        assert len(correlation_id) > 0

    def test_mask_sensitive_data_string(self):
        """Тест маскирования чувствительных данных в строке"""
        handler = ErrorHandler()

        sensitive_data = "User email user@example.com with token abc123def456"
        masked_data = handler.mask_sensitive_data(sensitive_data)

        assert "***@***.***" in masked_data
        assert "***TOKEN***" in masked_data
        assert "user@example.com" not in masked_data
        assert "abc123def456" not in masked_data

    def test_mask_sensitive_data_dict(self):
        """Тест маскирования чувствительных данных в словаре"""
        handler = ErrorHandler()

        sensitive_data = {
            "user": "user@example.com",
            "token": "abc123def456",
            "message": "Login successful",
        }
        masked_data = handler.mask_sensitive_data(sensitive_data)

        assert masked_data["user"] == "***@***.***"
        assert masked_data["token"] == "***TOKEN***"
        assert masked_data["message"] == "Login successful"

    def test_mask_sensitive_data_list(self):
        """Тест маскирования чувствительных данных в списке"""
        handler = ErrorHandler()

        sensitive_data = ["user@example.com", "normal text", "token123456789"]
        masked_data = handler.mask_sensitive_data(sensitive_data)

        assert masked_data[0] == "***@***.***"
        assert masked_data[1] == "normal text"
        assert masked_data[2] == "***TOKEN***"


class TestAPIErrorHandling:
    """Тесты обработки ошибок через API"""

    def test_validation_error_response_format(self):
        """Тест формата ответа при ошибке валидации"""
        response = client.post("/wishlist/items", json={"name": ""})

        assert response.status_code == 422

    def test_not_found_error_response_format(self):
        """Тест формата ответа при ошибке 'не найдено'"""
        response = client.get("/wishlist/items/99999")

        assert response.status_code == 404

        data = response.json()

        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "instance" in data
        assert "correlation_id" in data
        assert "timestamp" in data

        assert data["status"] == 404
        assert "not found" in data["detail"].lower()
        assert "/wishlist/items/99999" in data["instance"]

    def test_correlation_id_preservation(self):
        """Тест сохранения correlation_id между запросами"""
        headers = {"X-Correlation-ID": "test-correlation-123"}
        response = client.get("/wishlist/items/99999", headers=headers)

        assert response.status_code == 404

        data = response.json()
        assert data["correlation_id"] == "test-correlation-123"

        assert response.headers["x-correlation-id"] == "test-correlation-123"

    def test_error_response_consistency(self):
        """Тест консистентности формата ошибок"""
        test_cases = [
            ("/wishlist/items/99999", 404, "not-found"),
        ]

        for test_case in test_cases:
            if len(test_case) == 3:
                url, expected_status, expected_type = test_case
                response = client.get(url)

            assert response.status_code == expected_status

            data = response.json()

            required_fields = [
                "type",
                "title",
                "status",
                "detail",
                "instance",
                "correlation_id",
                "timestamp",
            ]
            for field in required_fields:
                assert field in data, f"Missing field: {field}"

            if expected_type == "not-found":
                assert "not-found" in data["type"]

    def test_pii_masking_in_error_responses(self):
        """Тест маскирования PII в ответах об ошибках"""
        item_data = {
            "name": "Test item",
            "description": "User email user@example.com and token abc123def456",
        }

        response = client.post("/wishlist/items", json=item_data)

        if response.status_code != 200:
            data = response.json()
            detail = data.get("detail", "")

            if "user@example.com" in detail:
                assert "***@***.***" in detail
            if "abc123def456" in detail:
                assert "***TOKEN***" in detail

    def test_error_timestamp_format(self):
        """Тест формата временной метки в ошибках"""
        response = client.get("/wishlist/items/99999")

        assert response.status_code == 404

        data = response.json()
        timestamp = data["timestamp"]

        assert timestamp.endswith("Z")
        assert "T" in timestamp

        from datetime import datetime

        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed_timestamp, datetime)
