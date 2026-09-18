"""
Smoke-тест: прогоняет весь путь по API.
Запуск: python -m scripts.smoke
Требует запущенный сервер на http://127.0.0.1:8000
"""
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8000/api/v1"


def _rand_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@smoke.local"


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30.0)
    suffix = uuid.uuid4().hex[:6]

    # 1. Регистрация препода и студента
    r = client.post("/auth/register", json={
        "first_name": "Препод",
        "last_name": "Тестов",
        "email": _rand_email("teacher"),
        "password": "qwerty12345",
        "role": "teacher",
    })
    assert r.status_code == 201, r.text
    t = r.json()
    t_token = t["tokens"]["access_token"]
    t_id = t["user"]["id"]

    r = client.post("/auth/register", json={
        "first_name": "Студент",
        "last_name": "Тестов",
        "email": _rand_email("student"),
        "password": "qwerty12345",
        "role": "student",
        "group_hint": f"99{suffix[:2].upper()}",
    })
    assert r.status_code == 201, r.text
    s = r.json()
    s_token = s["tokens"]["access_token"]
    s_id = s["user"]["id"]

    t_h = {"Authorization": f"Bearer {t_token}"}
    s_h = {"Authorization": f"Bearer {s_token}"}

    # 2. Студент уже создал группу через group_hint — найдём её
    r = client.get("/groups", headers=s_h)
    assert r.status_code == 200, r.text
    groups = r.json()
    assert groups, "Студент должен быть в группе"
    group_id = groups[0]["id"]
    group_name = groups[0]["name"]
    print(f"✔ Группа создана: {group_name} (id={group_id})")

    # 3. Препод «забирает» группу
    r = client.post(f"/groups/{group_id}/claim", headers=t_h)
    assert r.status_code == 200, r.text
    print("✔ Препод забрал группу")

    # 4. Препод создаёт задание
    r = client.post("/tasks", headers=t_h, json={
        "title": "Smoke task",
        "description": "Напиши функцию hello()",
        "deadline": "2030-01-01T00:00:00+00:00",
        "group_id": group_id,
    })
    assert r.status_code == 201, r.text
    task_id = r.json()["id"]
    print(f"✔ Задание создано: id={task_id}")

    # 5. Студент сдаёт
    r = client.post("/submissions", headers=s_h, json={
        "task_id": task_id,
        "student_comment": "def hello(): return 'hi'",
    })
    assert r.status_code == 201, r.text
    sub_id = r.json()["id"]
    print(f"✔ Сдача создана: id={sub_id}")

    # 6. AI-проверка (синхронная)
    r = client.post(f"/ai/check/{sub_id}", headers=s_h, json={"force": True})
    assert r.status_code == 200, r.text
    ai = r.json()
    assert ai["status"] == "done", ai
    print(f"✔ AI проверка: score={ai['score']}")

    # 7. Препод видит сдачу и комментирует
    r = client.get(f"/submissions/{sub_id}", headers=t_h)
    assert r.status_code == 200, r.text

    r = client.post(f"/submissions/{sub_id}/comments", headers=t_h, json={
        "text": "Хорошо, но добавь тесты"
    })
    assert r.status_code == 201, r.text
    print("✔ Комментарий препода добавлен")

    # 8. Проверка прав
    r = client.get(f"/submissions/{sub_id}")
    assert r.status_code == 401, r.text
    print("✔ Без токена — 401")

    print("\n🎉 SMOKE OK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"\n❌ FAIL: {e}")
        sys.exit(1)