# ♟️ Chess Map

Мультисервисное приложение на Docker Compose: 2D-карта, по которой перемещается
персонаж, и шахматная арена в центре, где два игрока играют партию. После
завершения партии фоновый воркер асинхронно анализирует её через Stockfish.

Пет-проект сделан в первую очередь как **инфраструктурная практика**: цель —
собрать реалистичный многосервисный стек (API + БД + кэш/брокер + фоновый
воркер + reverse proxy) и научиться правильно его оркестрировать, а не
написать сложную бизнес-логику.

![status]<img width="1012" height="224" alt="image" src="https://github.com/user-attachments/assets/f1ddda45-9f63-4c49-99a3-e0d6f1cb67a2" />

---

## Архитектура

```
                    ┌────────┐
   браузер  ──────▶ │ nginx  │  :8080  (reverse proxy)
                    └───┬────┘
              ┌─────────┼──────────┐
              ▼                    ▼
        статика (frontend)    /api/ → FastAPI (api)
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              PostgreSQL         Redis          Celery worker
             (users, games,   (кэш позиций    (Stockfish-анализ
              moves, анализ)   на карте +      завершённых партий,
                                Celery-брокер)  фоновая задача)
```

**Почему так:**

- **Redis используется под две разные роли** (кэш + брокер задач) через разные
  логические БД внутри одного инстанса (`/0`, `/1`, `/2`) — не плодил лишний
  контейнер там, где хватает одного процесса.
- **Анализ партии вынесен в отдельный воркер**, а не считается синхронно в
  API-запросе — прогон через Stockfish занимает заметное время, и блокировать
  им HTTP-response было бы плохим UX. API просто ставит задачу в очередь и
  сразу отдаёт ответ.
- **Nginx — единая точка входа**: отдаёт статику фронта и проксирует `/api/`
  на backend, чтобы в браузере не было CORS-плясок и весь стек торчал наружу
  одним портом.
- **api и worker читают одну и ту же схему БД** независимо друг от друга
  (без общего ORM-пакета) — осознанный компромисс ради простоты пет-проекта;
  в проде вынес бы модели в отдельный shared-пакет.

---

## Стек

| Слой | Технологии |
|---|---|
| Backend API | Python, FastAPI, SQLAlchemy, `python-chess` |
| Фоновые задачи | Celery, Redis (broker/backend), Stockfish |
| БД | PostgreSQL 16 |
| Frontend | Vanilla JS, HTML5 Canvas (без фреймворков — намеренно) |
| Инфраструктура | Docker, Docker Compose, Nginx (reverse proxy) |

---

## Быстрый старт

```bash
git clone <repo-url>
cd chess-map
cp .env.example .env
docker compose up --build
```

Открыть **http://localhost:8080**

Проверка, что всё поднялось:

```bash
docker compose ps        # все сервисы healthy
curl localhost:8080/api/health
```

---

## Переменные окружения

См. `.env.example`. Коротко:

| Переменная | Кто использует | Назначение |
|---|---|---|
| `DATABASE_URL` | api, worker | подключение к Postgres |
| `REDIS_URL` | api | кэш позиций игроков на карте |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | api, worker | очередь задач Celery |
| `STOCKFISH_PATH` | worker | путь к бинарнику движка внутри контейнера |

---

## Структура проекта

```
chess-map/
├── docker-compose.yml
├── .env.example
├── api/            # FastAPI: REST для юзеров, карты, партий
│   ├── Dockerfile
│   └── app/
│       ├── main.py
│       ├── models.py        # SQLAlchemy: users, games, moves, game_analysis
│       ├── routers/         # users.py, map.py, games.py
│       └── celery_app.py    # постановка задач в очередь
├── worker/         # Celery-воркер + Stockfish
│   ├── Dockerfile
│   └── tasks.py    # анализ завершённой партии
├── frontend/       # статика: карта на canvas + шахматная доска
└── nginx/
    └── nginx.conf
```

---

## API

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/users` | создать игрока |
| `POST` | `/map/move` | сдвинуть игрока на карте |
| `GET` | `/map/players` | позиции всех игроков + координаты арены |
| `POST` | `/games` | начать партию |
| `POST` | `/games/{id}/moves` | сделать ход (SAN) |
| `GET` | `/games/{id}/analysis` | результат анализа Stockfish |

Полная OpenAPI-схема — на `/api/docs` после запуска (FastAPI генерирует
автоматически).

---

## Что стоило бы доделать дальше

Осознанно оставил как есть для пет-проекта, но в проде добавил бы:

- [ ] Alembic-миграции вместо `Base.metadata.create_all`
- [ ] Тесты (pytest + testcontainers для интеграционных с реальным Postgres)
- [ ] CI: сборка образов + линт на каждый PR (GitHub Actions)
- [ ] Мониторинг: Prometheus + Grafana для api/worker, алерты на упавшие Celery-таски
- [ ] Секреты — вынести из `.env` в Docker secrets / Vault для прод-окружения
- [ ] WebSocket вместо polling для карты и статуса партии (сейчас фронт опрашивает `/map/players` раз в 500мс — рабочий, но не самый эффективный вариант)

---

## Автор

Сделано как практика Docker/Compose-оркестрации многосервисного приложения.
