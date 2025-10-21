"""
Тесты для модуля валидации ввода и загрузок.

Проверяет реализацию ADR-001
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.validation import FileValidationError, InputValidator

client = TestClient(app)


class TestInputValidation:
    """Тесты валидации входных данных"""

    def test_validate_string_input_valid(self):
        """Тест валидации корректных строковых данных"""
        validator = InputValidator()

        result = validator.validate_string_input("Нормальный текст", "test_field")
        assert result == "Нормальный текст"

        result = validator.validate_string_input("", "test_field")
        assert result == ""

    def test_validate_string_input_too_long(self):
        """Тест валидации слишком длинных строк"""
        validator = InputValidator()

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_string_input("x" * 1001, "test_field", max_length=1000)

        assert "слишком длинное" in str(exc_info.value)

    def test_validate_string_input_dangerous_patterns(self):
        """Тест валидации опасных паттернов"""
        validator = InputValidator()

        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "../../etc/passwd",
            "union select * from users",
            "exec('rm -rf /')",
            "eval('malicious_code')",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_string_input(dangerous_input, "test_field")

            assert "небезопасные символы" in str(exc_info.value)

    def test_validate_string_input_sql_injection(self):
        """Тест защиты от SQL инъекций"""
        validator = InputValidator()

        sql_injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        ]

        for sql_injection in sql_injections:
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_string_input(sql_injection, "test_field")

            assert "небезопасные символы" in str(exc_info.value)

    def test_validate_string_input_path_traversal(self):
        """Тест защиты от path traversal атак"""
        validator = InputValidator()

        path_traversals = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..%5c..%5c..%5cwindows%5csystem32",
        ]

        for path_traversal in path_traversals:
            with pytest.raises(FileValidationError) as exc_info:
                validator.validate_string_input(path_traversal, "test_field")

            assert "небезопасные символы" in str(exc_info.value)


class TestFileValidation:
    """Тесты валидации файлов"""

    def test_validate_file_upload_valid_jpeg(self):
        """Тест валидации корректного JPEG файла"""
        validator = InputValidator()

        jpeg_content = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
            b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11"
            b"\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00"
            b"\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11"
            b"\x00\x3f\x00\xaa\xff\xd9"
        )

        result = validator.validate_file_upload(jpeg_content, "test.jpg", "image/jpeg")

        assert result["original_filename"] == "test.jpg"
        assert result["content_type"] == "image/jpeg"
        assert result["size"] == len(jpeg_content)
        assert result["magic_bytes_valid"] is True
        assert "safe_filename" in result

    def test_validate_file_upload_valid_png(self):
        """Тест валидации корректного PNG файла"""
        validator = InputValidator()

        png_content = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00"
            b"\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00"
            b"\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\n"
            b"IDATx\x9cc\xf8\x0f\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00"
            b"IEND\xaeB`\x82"
        )

        result = validator.validate_file_upload(png_content, "test.png", "image/png")

        assert result["original_filename"] == "test.png"
        assert result["content_type"] == "image/png"
        assert result["magic_bytes_valid"] is True

    def test_validate_file_upload_invalid_magic_bytes(self):
        """Тест валидации файла с неверными magic bytes"""
        validator = InputValidator()

        invalid_content = b"This is not a valid image file"

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_file_upload(invalid_content, "fake.jpg", "image/jpeg")

        assert "Неверный тип файла" in str(exc_info.value)

    def test_validate_file_upload_too_large(self):
        """Тест валидации слишком большого файла"""
        validator = InputValidator()

        large_content = b"x" * (validator.MAX_FILE_SIZE + 1)

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_file_upload(large_content, "large.jpg", "image/jpeg")

        assert "слишком большой" in str(exc_info.value)

    def test_validate_file_upload_unsupported_type(self):
        """Тест валидации неподдерживаемого типа файла"""
        validator = InputValidator()

        content = b"Some content"

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_file_upload(
                content, "test.exe", "application/octet-stream"
            )

        assert "Неверный тип файла" in str(exc_info.value)

    def test_generate_safe_filename(self):
        """Тест генерации безопасного имени файла"""
        validator = InputValidator()

        safe_name = validator._generate_safe_filename("test.jpg")
        assert safe_name.endswith(".jpg")
        assert "test" in safe_name

        safe_name = validator._generate_safe_filename("test<script>.jpg")
        assert safe_name.endswith(".jpg")
        assert "<script>" not in safe_name

        long_name = "a" * 100 + ".jpg"
        safe_name = validator._generate_safe_filename(long_name)
        assert len(safe_name) < 100


class TestPathSafety:
    """Тесты безопасности путей"""

    def test_validate_path_safety_valid(self):
        """Тест валидации безопасного пути"""
        validator = InputValidator()

        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            validator.upload_dir = Path(temp_dir)
            safe_path = validator.validate_path_safety(f"{temp_dir}/test.jpg")
            expected_path = os.path.normpath(f"{temp_dir}/test.jpg")
            assert safe_path == expected_path

    def test_validate_path_safety_traversal(self):
        """Тест защиты от path traversal"""
        validator = InputValidator()

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_path_safety("../../../etc/passwd")

        assert "Небезопасный путь" in str(exc_info.value)

    def test_validate_path_safety_symlink(self):
        """Тест защиты от символических ссылок"""
        validator = InputValidator()

        with pytest.raises(FileValidationError) as exc_info:
            validator.validate_path_safety("/dev/null")

        error_message = str(exc_info.value)
        assert (
            "Небезопасный путь" in error_message
            or "Символические ссылки запрещены" in error_message
        )


class TestAPIValidation:
    """Тесты валидации через API"""

    def test_create_item_with_dangerous_input(self):
        """Тест создания элемента с опасным вводом"""
        dangerous_inputs = [
            {"name": "<script>alert('xss')</script>"},
            {"name": "Test", "description": "../../etc/passwd"},
            {"name": "'; DROP TABLE users; --"},
        ]

        for dangerous_input in dangerous_inputs:
            response = client.post("/wishlist/items", json=dangerous_input)
            assert response.status_code in [400, 422]

    def test_create_item_with_valid_input(self):
        """Тест создания элемента с валидным вводом"""
        valid_input = {
            "name": "Безопасный элемент",
            "description": "Обычное описание без опасных символов",
            "price": 100.0,
            "priority": "medium",
        }

        response = client.post("/wishlist/items", json=valid_input)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Безопасный элемент"
        assert data["description"] == "Обычное описание без опасных символов"
