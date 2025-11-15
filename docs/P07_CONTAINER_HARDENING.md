# P07 — Контейнеризация и базовый харднинг

## Описание

Этот документ описывает конфигурацию контейнеризации и базового харднинга для WishList API.

## Структура файлов

- `Dockerfile` — multi-stage build с оптимизацией размера и безопасности
- `docker-compose.yml` — конфигурация для локального запуска
- `.dockerignore` — исключение ненужных файлов из образа
- `.hadolint.yml` — конфигурация линтера Dockerfile
- `Makefile` — команды для сборки, проверки и запуска
- `scripts/` — скрипты для автоматизации проверок

## Особенности реализации

### Dockerfile

- **Multi-stage build**: разделение сборки и runtime для уменьшения размера образа
- **Non-root пользователь**: контейнер запускается под пользователем `appuser` (UID 1000)
- **Healthcheck**: встроенная проверка через Python urllib (без внешних зависимостей)
- **Оптимизация слоёв**: использование wheel-файлов и кэширования pip
- **Базовый образ**: `python:3.11-slim` для минимального размера

### Безопасность

- Запуск под non-root пользователем
- Healthcheck для мониторинга состояния
- Минимальный набор зависимостей в runtime образе
- Исключение dev-зависимостей из финального образа

## Использование

### Быстрый старт

```bash
# Сборка и запуск
make build
make run

# Или через docker compose
docker compose up --build
```

### Проверки

```bash
# Линтинг Dockerfile
make lint

# Сканирование на уязвимости
make scan

# Проверка пользователя и healthcheck
make check-user
make check-health

# Все проверки
make all
```

### Через скрипты

```bash
# Запуск контейнера
bash scripts/run_container.sh

# Проверка контейнера
bash scripts/check_container.sh

# Линтинг Dockerfile
bash scripts/lint_dockerfile.sh

# Сканирование образа
bash scripts/scan_image.sh
```
