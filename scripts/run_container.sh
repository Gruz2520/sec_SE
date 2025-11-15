#!/bin/bash

set -e

echo "Сборка и запуск контейнера"

echo "1. Сборка образа..."
docker compose build

echo ""
echo "2. Запуск контейнера..."
docker compose up -d

echo ""
echo "3. Ожидание готовности контейнера..."
sleep 5

echo ""
echo "4. Статус контейнера:"
docker compose ps

echo ""
echo "5. Проверка healthcheck..."
for i in {1..10}; do
    HEALTH=$(docker compose ps --format json | jq -r '.[0].Health // "unknown"' 2>/dev/null || echo "unknown")
    if [ "$HEALTH" = "healthy" ]; then
        echo "   Контейнер healthy"
        break
    fi
    echo "   Ожидание... ($i/10)"
    sleep 3
done

echo ""
echo "Контейнер запущен"
echo "API доступен по адресу: http://localhost:8000"
echo "Health endpoint: http://localhost:8000/health"
echo ""
echo "Логи: docker compose logs -f app"
echo "Остановка: docker compose down"
