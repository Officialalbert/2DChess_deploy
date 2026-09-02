"""
Интеграционный тест бьёт по реальному FastAPI-приложению через TestClient,
а оно, в свою очередь, ходит в настоящий Postgres и Redis.
В CI эти два сервиса поднимаются через `services:` в workflow (см. ci.yml).
Локально можно запустить так же, если поднять их из docker-compose и
экспортировать DATABASE_URL/REDIS_URL/CELERY_* до запуска pytest.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_full_game_flow():
    # 1. создаём пользователя
    res = client.post("/users", json={"username": "integration_test_user"})
    assert res.status_code == 200

    # 2. создаём партию
    res = client.post("/games", json={"white_name": "alice", "black_name": "bob"})
    assert res.status_code == 200
    game = res.json()
    game_id = game["id"]
    assert game["status"] == "active"

    # 3. валидный ход проходит
    res = client.post(f"/games/{game_id}/moves", json={"san": "e4"})
    assert res.status_code == 200
    assert len(res.json()["moves"]) == 1

    # 4. невалидный ход отклоняется с понятной ошибкой
    res = client.post(f"/games/{game_id}/moves", json={"san": "Ke9"})
    assert res.status_code == 400

    # 5. доигрываем детский мат и проверяем, что партия закрылась
    for san in ["e5", "Bc4", "Nc6", "Qh5", "Nf6", "Qxf7#"]:
        res = client.post(f"/games/{game_id}/moves", json={"san": san})
        assert res.status_code == 200

    finished_game = res.json()
    assert finished_game["status"] == "finished"
    assert finished_game["result"] == "1-0"

    # 6. на завершённой партии новый ход должен отклоняться
    res = client.post(f"/games/{game_id}/moves", json={"san": "e4"})
    assert res.status_code == 400
