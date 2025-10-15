# STRIDE Threat Model

| Поток/Элемент | Угроза | STRIDE | Контроль (NFR) | Обоснование / Проверка |
|---------------|--------|--------|----------------|-------------------------|
| F2 (POST /wishlist) | Flood-атака | Denial of Service | Rate limiting 100 rpm/IP (NFR-9) | BDD-сценарий: 429 после 100 запросов/мин |
| F3 (JWT AuthZ) | Подделка токена | Spoofing | Валидация JWT, секреты в Vault (NFR-08) | Превентивно: pre-commit scan + ревью |
| F4 (Hash pwd) | Перебор слабых хешей | Brute Force | Использовать Argon2id (t=3, m=256MB) (NFR-01) | Unit-тест проверяет параметры хеширования |
| F5 (Insert item) | SQL-инъекция | Injection | ORM (SQLAlchemy), нет raw query (NFR-07) | Сканер: osv-scanner, pip-audit |
| F6 (Log req) | Утечка PII (email, token) | Information Disclosure | Маскирование PII, structured logs (NFR-10, NFR-02) | Линтер: регулярки в CI против `.*password.*` |
| F7 (Brute Force /login) | Перебор паролей | Denial of Service | Rate limit на /login (NFR-9) | Интеграционный тест (pytest-faker) |
| F8 (High freq POST) | Атака на производительность | Denial of Service | p95 ≤ 200 ms @ 20 RPS (NFR-04) | Нагрузочный тест в CI (k6) |
| F1 (HTTPS) | MITM | Spoofing | HSTS + редирект HTTP→HTTPS (NFR-02) | ZAP baseline scan в CI |
| Auth Service | Утечка секретов из кода | Information Disclosure | Запрет коммитов с секретами (pre-commit) (NFR-08) | git-secrets hook |
| Legacy `/items` | Неконтролируемый endpoint | Exposure | Удалить или вернуть 410 Gone (NFR-02) | e2e тест: status_code == 410 |
| Logging | Нет correlation_id | Information Disclosure | Все логи с `correlation_id` (NFR-10) | Линтер: проверка формата JSON |
| FastAPI | Уязвимые зависимости | Tampering | SCA сканирование в CI (pip-audit) (NFR-07) | Отчёт в PR: osv-scanner |