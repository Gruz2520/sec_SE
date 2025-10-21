"""
Модуль валидации ввода и загрузок файлов.

Реализует ADR-001: Валидация ввода и загрузок
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict


class FileValidationError(Exception):
    """Ошибка валидации файла"""

    pass


class InputValidator:
    """Валидатор входных данных и файлов"""

    # Разрешенные типы файлов с их magic bytes
    ALLOWED_FILE_TYPES = {
        "image/jpeg": [b"\xff\xd8\xff"],
        "image/png": [b"\x89PNG\r\n\x1a\n"],
        "application/pdf": [b"%PDF-"],
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024
    UPLOAD_TIMEOUT = 30

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    def validate_file_upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Dict[str, Any]:
        """
        Валидация загружаемого файла

        Args:
            file_content: Содержимое файла
            filename: Имя файла
            content_type: MIME тип файла

        Returns:
            Dict с информацией о валидном файле

        Raises:
            FileValidationError: При ошибке валидации
        """
        # Проверка размера файла
        if len(file_content) > self.MAX_FILE_SIZE:
            raise FileValidationError(
                f"Файл слишком большой. Максимальный размер: {self.MAX_FILE_SIZE} байт"
            )

        # Проверка magic bytes
        if not self._validate_magic_bytes(file_content, content_type):
            raise FileValidationError("Неверный тип файла. Проверьте содержимое файла")

        safe_filename = self._generate_safe_filename(filename)

        return {
            "original_filename": filename,
            "safe_filename": safe_filename,
            "content_type": content_type,
            "size": len(file_content),
            "magic_bytes_valid": True,
        }

    def _validate_magic_bytes(self, file_content: bytes, content_type: str) -> bool:
        """Проверка magic bytes файла"""
        if content_type not in self.ALLOWED_FILE_TYPES:
            return False

        expected_magic = self.ALLOWED_FILE_TYPES[content_type]
        return any(
            file_content.startswith(magic_bytes) for magic_bytes in expected_magic
        )

    def _generate_safe_filename(self, original_filename: str) -> str:
        """Генерация безопасного имени файла с UUID"""
        file_ext = Path(original_filename).suffix.lower()

        file_uuid = str(uuid.uuid4())

        safe_name = "".join(c for c in original_filename if c.isalnum() or c in "._-")
        safe_name = safe_name[:50]

        return f"{file_uuid}_{safe_name}{file_ext}"

    def validate_path_safety(self, file_path: str) -> str:
        """
        Проверка безопасности пути файла

        Args:
            file_path: Путь к файлу

        Returns:
            Канонический безопасный путь

        Raises:
            FileValidationError: При обнаружении небезопасного пути
        """
        canonical_path = os.path.realpath(file_path)

        upload_dir_path = (
            str(self.upload_dir.resolve())
            if hasattr(self.upload_dir, "resolve")
            else str(self.upload_dir)
        )
        if not canonical_path.startswith(upload_dir_path):
            raise FileValidationError("Небезопасный путь к файлу")

        if os.path.islink(file_path):
            raise FileValidationError("Символические ссылки запрещены")

        return canonical_path

    def validate_string_input(
        self, value: str, field_name: str, max_length: int = 1000
    ) -> str:
        """
        Валидация строкового ввода

        Args:
            value: Значение для валидации
            field_name: Имя поля
            max_length: Максимальная длина

        Returns:
            Валидное значение

        Raises:
            FileValidationError: При ошибке валидации
        """
        if not isinstance(value, str):
            raise FileValidationError(f"{field_name} должно быть строкой")

        if len(value) > max_length:
            raise FileValidationError(
                f"{field_name} слишком длинное. Максимум: {max_length} символов"
            )

        dangerous_patterns = [
            "<script",
            "javascript:",
            "data:",
            "vbscript:",
            "../",
            "..\\",
            "..%2f",
            "..%5c",
            "union select",
            "drop table",
            "delete from",
            "exec(",
            "eval(",
            "system(",
            "';",
            "1'",
            "admin'",
            "insert into",
            "update set",
            "or '1'='1",
            "or 1=1",
            "union all",
        ]

        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if pattern in value_lower:
                raise FileValidationError(f"{field_name} содержит небезопасные символы")

        return value.strip()


input_validator = InputValidator()
