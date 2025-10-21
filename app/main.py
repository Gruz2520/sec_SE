from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

# Импорт модулей безопасности
from app.security.error_handling import (
    create_internal_error,
    create_not_found_error,
    create_validation_error,
    error_handler,
)
from app.security.secrets import secrets_manager
from app.security.validation import FileValidationError, input_validator

app = FastAPI(title="WishList API", version="0.1.0")


class WishListItemBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=200, description="Название элемента"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Описание элемента"
    )
    price: Optional[float] = Field(None, ge=0, description="Цена элемента")
    priority: str = Field(
        "medium", pattern="^(low|medium|high)$", description="Приоритет элемента"
    )


class WishListItemCreate(WishListItemBase):
    pass


class WishListItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, ge=0)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    is_purchased: Optional[bool] = None


class WishListItem(WishListItemBase):
    id: int
    is_purchased: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    correlation_id = error_handler.get_correlation_id(request)

    if exc.status == 404:
        error = create_not_found_error(
            detail=exc.message, instance=str(request.url), correlation_id=correlation_id
        )
    else:
        error = create_validation_error(
            detail=exc.message, instance=str(request.url), correlation_id=correlation_id
        )

    return error_handler.create_error_response(error, request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = error_handler.get_correlation_id(request)
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"

    if exc.status_code == 404:
        error = create_not_found_error(
            detail=detail, instance=str(request.url), correlation_id=correlation_id
        )
    elif exc.status_code == 410:
        error = create_validation_error(
            detail=detail, instance=str(request.url), correlation_id=correlation_id
        )
        error.status = 410  # Сохраняем оригинальный статус код
    else:
        error = create_validation_error(
            detail=detail, instance=str(request.url), correlation_id=correlation_id
        )

    return error_handler.create_error_response(error, request)


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    """Обработчик ошибок валидации FastAPI"""
    correlation_id = error_handler.get_correlation_id(request)
    error = create_validation_error(
        detail="Validation error",
        instance=str(request.url),
        correlation_id=correlation_id,
    )
    return error_handler.create_error_response(error, request)


@app.exception_handler(FileValidationError)
async def file_validation_error_handler(request: Request, exc: FileValidationError):
    correlation_id = error_handler.get_correlation_id(request)
    error = create_validation_error(
        detail=str(exc), instance=str(request.url), correlation_id=correlation_id
    )
    return error_handler.create_error_response(error, request)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    correlation_id = error_handler.get_correlation_id(request)
    error = create_internal_error(
        detail="Internal server error",
        instance=str(request.url),
        correlation_id=correlation_id,
    )
    return error_handler.create_error_response(error, request)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/secrets")
def health_secrets():
    """Проверка состояния секретов"""
    try:
        validation_results = secrets_manager.validate_secrets_config()
        return {
            "status": "ok" if validation_results["valid"] else "error",
            "secrets_validation": validation_results,
        }
    except Exception:
        return {
            "status": "error",
            "message": "Failed to validate secrets configuration",
        }


# In-memory database for WishList
_DB = {"wishlist_items": []}


@app.post("/wishlist/items", response_model=WishListItem)
def create_wishlist_item(item: WishListItemCreate):
    """Создать новый элемент в списке желаний"""
    try:
        # Валидация входных данных
        validated_name = input_validator.validate_string_input(
            item.name, "name", max_length=200
        )
        validated_description = None
        if item.description:
            validated_description = input_validator.validate_string_input(
                item.description, "description", max_length=1000
            )

        new_id = len(_DB["wishlist_items"]) + 1
        now = datetime.now()

        wishlist_item = {
            "id": new_id,
            "name": validated_name,
            "description": validated_description,
            "price": item.price,
            "priority": item.priority,
            "is_purchased": False,
            "created_at": now,
            "updated_at": now,
        }

        _DB["wishlist_items"].append(wishlist_item)
        return wishlist_item

    except FileValidationError as e:
        raise e
    except Exception as e:
        # Логируем ошибку с маскированием секретов
        secrets_manager.logger.error(f"Error creating wishlist item: {str(e)}")
        raise


@app.get("/wishlist/items", response_model=List[WishListItem])
def get_wishlist_items(
    priority: Optional[str] = None, is_purchased: Optional[bool] = None
):
    """Получить все элементы списка желаний с возможностью фильтрации"""
    items = _DB["wishlist_items"].copy()

    if priority is not None:
        items = [item for item in items if item["priority"] == priority]

    if is_purchased is not None:
        items = [item for item in items if item["is_purchased"] == is_purchased]

    return items


@app.get("/wishlist/items/{item_id}", response_model=WishListItem)
def get_wishlist_item(item_id: int):
    """Получить конкретный элемент списка желаний по ID"""
    for item in _DB["wishlist_items"]:
        if item["id"] == item_id:
            return item

    raise ApiError(code="not_found", message="wishlist item not found", status=404)


@app.put("/wishlist/items/{item_id}", response_model=WishListItem)
def update_wishlist_item(item_id: int, item_update: WishListItemUpdate):
    """Обновить элемент списка желаний"""
    for i, item in enumerate(_DB["wishlist_items"]):
        if item["id"] == item_id:
            update_data = item_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                item[field] = value

            item["updated_at"] = datetime.now()
            _DB["wishlist_items"][i] = item
            return item

    raise ApiError(code="not_found", message="wishlist item not found", status=404)


@app.delete("/wishlist/items/{item_id}")
def delete_wishlist_item(item_id: int):
    """Удалить элемент из списка желаний"""
    for i, item in enumerate(_DB["wishlist_items"]):
        if item["id"] == item_id:
            deleted_item = _DB["wishlist_items"].pop(i)
            return {"message": f"Item '{deleted_item['name']}' deleted successfully"}

    raise ApiError(code="not_found", message="wishlist item not found", status=404)


# Legacy endpoints.
@app.post("/items")
def deprecated_item():
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use /wishlist/items instead.",
    )
