.PHONY: help build run stop test lint scan clean

IMAGE_NAME := wishlist-api
CONTAINER_NAME := wishlist-api
VERSION := latest

help:
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

run:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f app

test:
	docker compose run --rm app pytest -q

lint:
	@echo "Проверка Dockerfile с hadolint..."
	@if command -v hadolint > /dev/null; then \
		hadolint -f tty Dockerfile; \
	else \
		echo "Hadolint не установлен. Установите: https://github.com/hadolint/hadolint"; \
		echo "Или используйте: docker run --rm -i hadolint/hadolint < Dockerfile"; \
	fi

lint-docker:
	docker run --rm -i hadolint/hadolint < Dockerfile

scan:
	@echo "Сканирование образа $(IMAGE_NAME):$(VERSION) с Trivy..."
	@if command -v trivy > /dev/null; then \
		trivy image $(IMAGE_NAME):$(VERSION) --format table --exit-code 0; \
	else \
		echo "Trivy не установлен. Установите: https://github.com/aquasecurity/trivy"; \
		echo "Или используйте: docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image $(IMAGE_NAME):$(VERSION)"; \
	fi

scan-docker:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image $(IMAGE_NAME):$(VERSION) --format table --exit-code 0

scan-report:
	@if command -v trivy > /dev/null; then \
		trivy image $(IMAGE_NAME):$(VERSION) --format json --output trivy-report.json; \
		echo "Отчёт сохранён в trivy-report.json"; \
	else \
		echo "Trivy не установлен. Используйте: make scan-docker-report"; \
	fi

scan-docker-report:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $(PWD):/workspace aquasec/trivy image $(IMAGE_NAME):$(VERSION) --format json --output /workspace/trivy-report.json
	@echo "Отчёт сохранён в trivy-report.json"

check-user:
	@echo "Проверка пользователя в контейнере..."
	@docker compose exec app id -u || docker compose run --rm app id -u
	@echo "Если ID != 0, то контейнер запущен под non-root пользователем"

check-health:
	@echo "Проверка healthcheck..."
	@docker compose ps
	@echo "Статус должен быть 'healthy'"

history:
	docker history $(IMAGE_NAME):$(VERSION)

size:
	docker images $(IMAGE_NAME):$(VERSION)

clean:
	docker compose down -v
	docker rmi $(IMAGE_NAME):$(VERSION) || true

all: build lint scan check-user
