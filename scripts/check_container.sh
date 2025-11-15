#!/bin/bash

set -e

IMAGE_NAME="${IMAGE_NAME:-wishlist-api}"
CONTAINER_NAME="${CONTAINER_NAME:-wishlist-api}"

echo "Проверка контейнера"

echo ""
echo "1. Проверка пользователя (должен быть != 0):"
USER_ID=$(docker compose exec -T app id -u 2>/dev/null || docker compose run --rm app id -u)
echo "   User ID: $USER_ID"
if [ "$USER_ID" = "0" ]; then
    echo "   бяда: Контейнер запущен под root"
    exit 1
else
    echo "   кайфы:Контейнер запущен под non-root пользователем (ID: $USER_ID)"
fi

echo ""
echo "2. Проверка healthcheck:"
HEALTH_STATUS=$(docker compose ps --format json | jq -r '.[0].Health // "unknown"' 2>/dev/null || echo "unknown")
if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo "   Healthcheck: healthy"
elif [ "$HEALTH_STATUS" = "starting" ]; then
    echo "   Healthcheck: starting (подождите немного)"
else
    echo "   Healthcheck: $HEALTH_STATUS"
    echo "   Проверьте логи: docker compose logs app"
fi

echo ""
echo "3. Размер образа:"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "4. История слоёв образа (первые 10):"
docker history "$IMAGE_NAME:latest" --format "table {{.CreatedBy}}\t{{.Size}}" | head -n 11

echo ""
echo "5. Проверка health endpoint:"
sleep 2
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "   Health endpoint доступен"
else
    echo "   Health endpoint недоступен"
    exit 1
fi

echo ""
echo "Все проверки завершены"
