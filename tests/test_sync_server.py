import pytest
from fastapi.testclient import TestClient

from sync_server import storage
from sync_server.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    return TestClient(app)


def _lesson_payload(subject: str = "Математика", week: str = "both") -> dict:
    return {
        "subject": subject,
        "weekday": 0,
        "start": "09:00",
        "end": "10:30",
        "room": "101",
        "teacher": "Иванов",
        "lesson_type": "лекция",
        "week": week,
    }


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_groups(client):
    response = client.post("/groups", json={"group_id": "ИВТ-31"})
    assert response.status_code == 201
    listed = client.get("/groups")
    assert listed.json()["groups"] == ["ИВТ-31"]


def test_put_schedule_rejects_conflicts(client):
    client.post("/groups", json={"group_id": "ИВТ-32"})
    payload = {
        "lessons": [
            _lesson_payload(week="even"),
            _lesson_payload(subject="Физика", week="even"),
        ]
    }
    response = client.put("/groups/ИВТ-32/schedule", json=payload)
    assert response.status_code == 400
    assert "errors" in response.json()["detail"]


def test_put_schedule_increments_version(client):
    client.post("/groups", json={"group_id": "ИВТ-33"})
    payload = {"lessons": [_lesson_payload()]}
    first = client.put("/groups/ИВТ-33/schedule", json=payload)
    second = client.put("/groups/ИВТ-33/schedule", json=payload)
    assert first.json()["version"] == 1
    assert second.json()["version"] == 2


def test_get_version_and_schedule(client):
    client.post("/groups", json={"group_id": "ИВТ-34"})
    client.put(
        "/groups/ИВТ-34/schedule",
        json={"lessons": [_lesson_payload(), _lesson_payload(subject="Физика", week="odd")]},
    )
    version = client.get("/groups/ИВТ-34/version")
    assert version.status_code == 200
    assert version.json()["lesson_count"] == 2
    schedule = client.get("/groups/ИВТ-34/schedule")
    assert len(schedule.json()["lessons"]) == 2
