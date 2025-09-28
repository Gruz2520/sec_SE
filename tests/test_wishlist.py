from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_wishlist_item():
    """Тест создания элемента списка желаний"""
    item_data = {
        "name": "Новый iPhone",
        "description": "Последняя модель iPhone",
        "price": 999.99,
        "priority": "high",
    }

    response = client.post("/wishlist/items", json=item_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == item_data["name"]
    assert data["description"] == item_data["description"]
    assert data["price"] == item_data["price"]
    assert data["priority"] == item_data["priority"]
    assert data["is_purchased"] is False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_wishlist_item_minimal():
    """Тест создания элемента с минимальными данными"""
    item_data = {"name": "Простая вещь"}

    response = client.post("/wishlist/items", json=item_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Простая вещь"
    assert data["description"] is None
    assert data["price"] is None
    assert data["priority"] == "medium"


def test_create_wishlist_item_validation_error():
    """Тест валидации при создании элемента"""
    # Пустое имя
    response = client.post("/wishlist/items", json={"name": ""})
    assert response.status_code == 422

    # Неверный приоритет
    response = client.post(
        "/wishlist/items", json={"name": "Тест", "priority": "invalid"}
    )
    assert response.status_code == 422

    # Отрицательная цена
    response = client.post("/wishlist/items", json={"name": "Тест", "price": -10})
    assert response.status_code == 422


def test_get_wishlist_items():
    """Тест получения всех элементов списка желаний"""
    # Создаем несколько элементов
    items_data = [
        {"name": "Элемент 1", "priority": "high"},
        {"name": "Элемент 2", "priority": "low", "is_purchased": True},
        {"name": "Элемент 3", "priority": "medium"},
    ]

    created_items = []
    for item_data in items_data:
        response = client.post("/wishlist/items", json=item_data)
        created_items.append(response.json())

    # Получаем все элементы
    response = client.get("/wishlist/items")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= len(created_items)


def test_get_wishlist_items_with_filters():
    """Тест получения элементов с фильтрацией"""
    # Создаем элементы с разными приоритетами
    client.post("/wishlist/items", json={"name": "High priority", "priority": "high"})
    client.post("/wishlist/items", json={"name": "Low priority", "priority": "low"})

    # Фильтр по приоритету
    response = client.get("/wishlist/items?priority=high")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["priority"] == "high"

    # Фильтр по статусу покупки
    response = client.get("/wishlist/items?is_purchased=false")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["is_purchased"] is False


def test_get_wishlist_item_by_id():
    """Тест получения конкретного элемента по ID"""
    # Создаем элемент
    item_data = {"name": "Тестовый элемент", "description": "Описание"}
    response = client.post("/wishlist/items", json=item_data)
    created_item = response.json()
    item_id = created_item["id"]

    # Получаем элемент по ID
    response = client.get(f"/wishlist/items/{item_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == item_id
    assert data["name"] == "Тестовый элемент"
    assert data["description"] == "Описание"


def test_get_wishlist_item_not_found():
    """Тест получения несуществующего элемента"""
    response = client.get("/wishlist/items/99999")
    assert response.status_code == 404

    data = response.json()
    assert data["error"]["code"] == "not_found"
    assert "wishlist item not found" in data["error"]["message"]


def test_update_wishlist_item():
    """Тест обновления элемента списка желаний"""
    # Создаем элемент
    item_data = {"name": "Исходный элемент", "priority": "low"}
    response = client.post("/wishlist/items", json=item_data)
    created_item = response.json()
    item_id = created_item["id"]

    # Обновляем элемент
    update_data = {
        "name": "Обновленный элемент",
        "priority": "high",
        "is_purchased": True,
    }
    response = client.put(f"/wishlist/items/{item_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Обновленный элемент"
    assert data["priority"] == "high"
    assert data["is_purchased"] is True
    assert data["id"] == item_id


def test_update_wishlist_item_not_found():
    """Тест обновления несуществующего элемента"""
    update_data = {"name": "Новое имя"}
    response = client.put("/wishlist/items/99999", json=update_data)
    assert response.status_code == 404

    data = response.json()
    assert data["error"]["code"] == "not_found"


def test_delete_wishlist_item():
    """Тест удаления элемента списка желаний"""
    # Создаем элемент
    item_data = {"name": "Элемент для удаления"}
    response = client.post("/wishlist/items", json=item_data)
    created_item = response.json()
    item_id = created_item["id"]

    # Удаляем элемент
    response = client.delete(f"/wishlist/items/{item_id}")
    assert response.status_code == 200

    data = response.json()
    assert "deleted successfully" in data["message"]

    # Проверяем, что элемент действительно удален
    response = client.get(f"/wishlist/items/{item_id}")
    assert response.status_code == 404


def test_delete_wishlist_item_not_found():
    """Тест удаления несуществующего элемента"""
    response = client.delete("/wishlist/items/99999")
    assert response.status_code == 404

    data = response.json()
    assert data["error"]["code"] == "not_found"
