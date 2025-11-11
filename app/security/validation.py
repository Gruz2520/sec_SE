"""
Модуль валидации ввода и загрузок файлов.

Реализует ADR-001: Валидация ввода и загрузок
"""

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Optional


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

    # Magic bytes для определения типа файла
    PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
    JPEG_SOI = b"\xff\xd8"
    JPEG_EOI = b"\xff\xd9"

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

    def validate_decimal(
        self,
        value: Any,
        field_name: str,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        max_digits: int = 12,
        decimal_places: int = 2,
    ) -> Decimal:
        """
        Валидация и нормализация Decimal значения

        Args:
            value: Значение для валидации (str, int, float, Decimal)
            field_name: Имя поля
            min_value: Минимальное значение
            max_value: Максимальное значение
            max_digits: Максимальное количество цифр
            decimal_places: Количество знаков после запятой

        Returns:
            Валидное Decimal значение

        Raises:
            FileValidationError: При ошибке валидации
        """
        try:
            if isinstance(value, str):
                # Используем parse_float=str для безопасного парсинга
                decimal_value = Decimal(value)
            elif isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            elif isinstance(value, Decimal):
                decimal_value = value
            else:
                raise FileValidationError(
                    f"{field_name} должно быть числом (str, int, float, Decimal)"
                )

            # Проверка диапазона
            if min_value is not None and decimal_value < min_value:
                raise FileValidationError(
                    f"{field_name} должно быть не меньше {min_value}"
                )

            if max_value is not None and decimal_value > max_value:
                raise FileValidationError(
                    f"{field_name} должно быть не больше {max_value}"
                )

            # Проверка точности
            sign, digits, exponent = decimal_value.as_tuple()
            total_digits = len(digits)

            if total_digits > max_digits:
                raise FileValidationError(
                    f"{field_name} содержит слишком много цифр. Максимум: {max_digits}"
                )

            if exponent < -decimal_places:
                raise FileValidationError(
                    f"{field_name} содержит слишком много знаков после запятой. "
                    f"Максимум: {decimal_places}"
                )

            # Нормализация (округление до нужного количества знаков)
            decimal_value = decimal_value.quantize(Decimal(10) ** -decimal_places)

            return decimal_value

        except (InvalidOperation, ValueError, TypeError) as e:
            raise FileValidationError(f"{field_name} имеет неверный формат: {str(e)}")

    def normalize_datetime_utc(self, dt: datetime) -> datetime:
        """
        Нормализация datetime в UTC

        Args:
            dt: datetime объект

        Returns:
            datetime в UTC без timezone info
        """
        if dt.tzinfo is None:
            # Если timezone не указан, считаем что это UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Конвертируем в UTC
            dt = dt.astimezone(timezone.utc)

        # Убираем timezone info для хранения
        return dt.replace(tzinfo=None)

    def sniff_file_type(self, data: bytes) -> Optional[str]:
        """
        Определение типа файла по magic bytes

        Args:
            data: Содержимое файла

        Returns:
            MIME тип файла или None
        """
        if data.startswith(self.PNG_MAGIC):
            return "image/png"
        # JPEG: проверяем SOI в начале и EOI в конце (если файл достаточно большой)
        if data.startswith(self.JPEG_SOI):
            # Для JPEG достаточно проверить SOI, EOI может быть в конце большого файла
            # Дополнительно проверяем наличие JFIF или Exif маркеров
            if len(data) > 4 and (
                b"JFIF" in data[:20]
                or b"Exif" in data[:20]
                or data.endswith(self.JPEG_EOI)
            ):
                return "image/jpeg"
            # Простой JPEG без маркеров, но с правильным SOI
            if len(data) > 10:
                return "image/jpeg"
        if data.startswith(b"%PDF-"):
            return "application/pdf"
        return None

    def secure_save(self, file_content: bytes, filename: Optional[str] = None) -> Path:
        """
        Безопасное сохранение файла с проверкой magic bytes, канонизацией пути
        и защитой от симлинков

        Args:
            file_content: Содержимое файла
            filename: Оригинальное имя файла (опционально)

        Returns:
            Path к сохраненному файлу

        Raises:
            FileValidationError: При ошибке валидации или сохранения
        """
        # Проверка размера
        if len(file_content) > self.MAX_FILE_SIZE:
            raise FileValidationError(
                f"Файл слишком большой. Максимальный размер: {self.MAX_FILE_SIZE} байт"
            )

        # Определение типа по magic bytes
        detected_type = self.sniff_file_type(file_content)
        if not detected_type:
            raise FileValidationError("Неверный тип файла. Проверьте содержимое файла")

        # Определение расширения
        if detected_type == "image/png":
            ext = ".png"
        elif detected_type == "image/jpeg":
            ext = ".jpg"
        elif detected_type == "application/pdf":
            ext = ".pdf"
        else:
            ext = ""

        # Канонизация корневой директории
        root = self.upload_dir.resolve(strict=True)

        # Генерация безопасного имени с UUID
        file_uuid = uuid.uuid4()
        safe_filename = f"{file_uuid}{ext}"

        # Формирование полного пути
        file_path = (root / safe_filename).resolve()

        # Проверка, что путь находится в разрешенной директории
        if not str(file_path).startswith(str(root)):
            raise FileValidationError("Обнаружена попытка path traversal")

        # Проверка на симлинки в родительских директориях
        for parent in file_path.parents:
            if parent.is_symlink():
                raise FileValidationError("Обнаружена символическая ссылка в пути")

        # Сохранение файла
        try:
            file_path.write_bytes(file_content)
            return file_path
        except Exception as e:
            raise FileValidationError(f"Ошибка при сохранении файла: {str(e)}")


input_validator = InputValidator()
