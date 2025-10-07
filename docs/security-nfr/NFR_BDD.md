
  # NFR-03: p95 GET /wishlist ≤ 150 ms @ 30 RPS (stage)
  - Scenario: p95 GET /wishlist держится под порогом на stage
    - Given сервис развернут на stage и сгенерирована нагрузка 30 RPS на GET /wishlist
    - When выполняется 5-минутный нагрузочный тест
    - Then p95 времени ответа для GET /wishlist ≤ 150 ms

  # NFR-04: p95 POST /wishlist ≤ 200 ms @ 20 RPS (stage)
  - Scenario: p95 POST /wishlist держится под порогом на stage
    - Given сервис развернут на stage и сгенерирована нагрузка 20 RPS на POST /wishlist
    - When выполняется 5-минутный нагрузочный тест
    - Then p95 времени ответа для POST /wishlist ≤ 200 ms

  # NFR-02: Формат ошибок и отсутствие PII
  - Scenario: ошибки возвращаются в едином формате без PII
    - Given эндпойнты вызываются с некорректными параметрами
    - When сервис возвращает ошибку
    - Then тело ответа содержит поле error.code и error.message + поля не включают email, phone, password, token или иные PII

  # Негативные/граничные сценарии
  # NFR-05: %5xx ≤ 0.5% за 24ч
  - Scenario: всплеск 5xx не превышает порог
    - Given сервис получает всплеск запросов с ошибочными payload
    - When количество запросов вызывает 5xx ответы
    - Then доля ответов 5xx за 10 минут не превышает 0.5%

  # NFR-9: rate limiting 100 rpm на мутирующих эндпойнтах
  - Scenario: превышение лимита на POST /wishlist ограничивается
    - Given один клиент посылает более 100 запросов на POST /wishlist за минуту
    - When лимит исчерпан
    - Then последующие запросы получают статус 429 в течение текущей минуты
