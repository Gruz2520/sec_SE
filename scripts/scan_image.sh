#!/bin/bash

set -e

IMAGE_NAME="${IMAGE_NAME:-wishlist-api:latest}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-table}"
OUTPUT_FILE="${OUTPUT_FILE:-trivy-report.json}"

echo "Сканирование образа $IMAGE_NAME"

if command -v trivy > /dev/null; then
    echo "Используется локальная установка Trivy"
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        trivy image --format json --output "$OUTPUT_FILE" "$IMAGE_NAME"
        echo "Отчет сохранен в $OUTPUT_FILE"
    else
        trivy image --format table "$IMAGE_NAME"
    fi
elif command -v docker > /dev/null; then
    echo "Используется Trivy через Docker"
    if [ "$OUTPUT_FORMAT" = "json" ]; then
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v "$(pwd):/workspace" \
            aquasec/trivy image \
            --format json \
            --output "/workspace/$OUTPUT_FILE" \
            "$IMAGE_NAME"
        echo "Отчёт сохранён в $OUTPUT_FILE"
    else
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy image \
            --format table \
            "$IMAGE_NAME"
    fi
else
    echo "БЯДА: Trivy не найден и Docker недоступен"
    echo "Установите Trivy: https://github.com/aquasecurity/trivy"
    exit 1
fi

echo ""
echo "Сканирование завершено"
