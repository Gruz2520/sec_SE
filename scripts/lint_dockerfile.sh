#!/bin/bash

set -e

DOCKERFILE="${1:-Dockerfile}"

echo "Проверка Dockerfile с hadolint"

if command -v hadolint > /dev/null; then
    echo "Используется локальная установка hadolint"
    hadolint -f tty "$DOCKERFILE"
elif command -v docker > /dev/null; then
    echo "Используется hadolint через Docker"
    docker run --rm -i hadolint/hadolint < "$DOCKERFILE"
else
    echo "БЯДА: hadolint не найден и Docker недоступен"
    exit 1
fi

echo ""
echo "Проверка завершена"
