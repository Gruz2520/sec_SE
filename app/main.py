from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

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
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# In-memory database for WishList
_DB = {"wishlist_items": []}


@app.post("/wishlist/items", response_model=WishListItem)
def create_wishlist_item(item: WishListItemCreate):
    """Создать новый элемент в списке желаний"""
    new_id = len(_DB["wishlist_items"]) + 1
    now = datetime.now()

    wishlist_item = {
        "id": new_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "priority": item.priority,
        "is_purchased": False,
        "created_at": now,
        "updated_at": now,
    }

    _DB["wishlist_items"].append(wishlist_item)
    return wishlist_item


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


# Legacy endpoints. Оставим пока что, для совместимости с существующими тестами
@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["wishlist_items"]) + 1, "name": name}
    _DB["wishlist_items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["wishlist_items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)
