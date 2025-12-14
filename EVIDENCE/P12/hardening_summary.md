# Hardening Summary - P12

## Dockerfile Hardening

### Применённые меры:

1. **Фиксированная версия базового образа**
   - Используется `python:3.11-slim` вместо `python:latest`
   - Снижает риск неожиданных изменений в базовом образе

2. **Non-root пользователь**
   - Создан пользователь `appuser` с UID 1000
   - Приложение запускается от имени non-root пользователя
   - Снижает риск привилегированных атак

3. **Multi-stage build**
   - Разделение этапов сборки и выполнения
   - Минимизация размера финального образа
   - Исключение build-зависимостей из runtime-образа

4. **Очистка кэша**
   - Удаление apt-кэша после установки пакетов
   - Использование `--no-cache-dir` для pip
   - Удаление временных файлов сборки

5. **Healthcheck**
   - Настроен healthcheck для мониторинга состояния контейнера
   - Интервал: 30s, таймаут: 3s

## Docker Compose Hardening

### Применённые меры:

1. **Security options**
   - `no-new-privileges: true` - предотвращает повышение привилегий

2. **Capabilities**
   - `cap_drop: ALL` - удаление всех capabilities
   - `cap_add: NET_BIND_SERVICE` - добавление только необходимой capability для привязки к порту

3. **Read-only filesystem**
   - `read_only: true` - файловая система только для чтения
   - `tmpfs` для `/tmp` и `/var/tmp` - временные файлы в памяти

## Kubernetes IaC Hardening

### Применённые меры:

1. **Security Context**
   - `runAsNonRoot: true` - запрет запуска от root
   - `runAsUser: 1000` - запуск от пользователя с UID 1000
   - `fsGroup: 1000` - установка группы файловой системы

2. **Resource limits**
   - Установлены requests и limits для CPU и памяти
   - Предотвращение исчерпания ресурсов

3. **Service type**
   - Используется `ClusterIP` вместо `LoadBalancer` или `NodePort`
   - Ограничение доступа только внутри кластера

4. **Health probes**
   - Настроены liveness и readiness probes
   - Обеспечение автоматического перезапуска неработающих подов

## Результаты сканирования

### Hadolint
- Отчёт: `hadolint_report.json`
- Основные проверки: использование latest, non-root user, очистка кэша

### Checkov
- Отчёт: `checkov_report.json`
- Проверка IaC-манифестов на соответствие best practices

### Trivy
- Отчёт: `trivy_report.json`
- Сканирование образа на уязвимости в зависимостях и конфигурации

## Дальнейшие шаги

- [ ] Регулярное обновление базового образа для устранения уязвимостей
- [ ] Мониторинг отчётов Trivy на критические уязвимости
- [ ] Применение политик безопасности на уровне кластера (Pod Security Policies/Standards)
- [ ] Настройка network policies для ограничения сетевого доступа
