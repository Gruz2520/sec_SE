# Backlog / Roadmap для Security NFR

## Labels
- `nfr`: для всех задач по нефункциональным требованиям
- `security`: для задач безопасности
- `performance`: для задач производительности
- `observability`: для логов/метрик/алёртов

## Issues
1. `API-01: Единый формат ошибок, маскирование PII` — NFR-02
2. `PERF-01: Нагрузочный тест GET /wishlist (p95 ≤ 150 ms @ 30 RPS)` — NFR-03
3. `PERF-02: Нагрузочный тест POST /wishlist (p95 ≤ 200 ms @ 20 RPS)` — NFR-04
4. `SEC-04: Автоскан зависимостей (SCA/SBOM) в CI` — NFR-07
5. `OBS-01: Структурированные логи с correlation_id` — NFR-9
6. `OBS-03: Дашборд 5xx и алёрты` — NFR-05
7. `OPS-02: Uptime мониторинг (blackbox)` — NFR-06
8. `SEC-07: Rate limiting для POST/PUT/DELETE` — NFR-9
9. `AUTH-12: Хеширование Argon2id` — NFR-01
10. `AUTH-15: JWT TTL/Refresh и валидация клеймов` — NFR-09
11. `OPS-05: План бэкапов и DR-тест восстановления` — NFR-11
