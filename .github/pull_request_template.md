## Контекст
(что меняем и зачем)

## Что сделано
- ...

## NFR документы
- [docs/security-nfr/NFR.md](docs/security-nfr/NFR.md)
- [docs/security-nfr/NFR_TRACEABILITY.md](docs/security-nfr/NFR_TRACEABILITY.md)
- [docs/security-nfr/NFR_BDD.md](docs/security-nfr/NFR_BDD.md)

## Backlog / Roadmap
- Issues с меткой `nfr`: добавить ссылки на задачи (AUTH-12, PERF-01, PERF-02, SEC-04, OBS-01 и т.д.)
- Milestones: 2025.10, 2025.11, 2025.12 — указать распределение по матрице трассируемости

## План внедрения
- Кто: владелец модуля (`api`, `auth`, `platform`)
- Когда: в рамках Milestone согласно `NFR_TRACEABILITY.md`
- Где: сервис `WishList API`; окружения: stage → prod

## Как проверял(а)
- [ ] `ruff/black/isort` локально
- [ ] `pytest -q` зелёный
- [ ] `pre-commit run --all-files`

## Чек-лист ревью
[Проверка кода по чек-листу ревью](docs/REVIEW_CHECKLIST.md)
