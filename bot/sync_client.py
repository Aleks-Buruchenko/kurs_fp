from __future__ import annotations

import os
from typing import Any

import httpx

from schedule_core.io_json import lessons_from_dict, lessons_to_dict
from schedule_core.models import Lesson

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 10.0


class SyncServerUnavailableError(Exception):
    """Сервер синхронизации недоступен или вернул ошибку сети."""


class SyncServerError(Exception):
    """Ошибка ответа сервера с телом detail."""

    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


def base_url() -> str:
    return os.getenv("SYNC_SERVER_URL", DEFAULT_BASE_URL).rstrip("/")


def _request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{base_url()}{path}"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        raise SyncServerUnavailableError(str(exc)) from exc
    if response.status_code >= 400:
        try:
            payload = response.json()
            detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
        except ValueError:
            detail = response.text
        raise SyncServerError(response.status_code, detail)
    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def get_groups() -> list[str]:
    data = _request("GET", "/groups")
    return list(data.get("groups", []))


def create_group(group_id: str) -> str:
    data = _request("POST", "/groups", json={"group_id": group_id})
    return str(data["group_id"])


def get_group_schedule(group_id: str) -> tuple[int, str | None, tuple[Lesson, ...]]:
    data = _request("GET", f"/groups/{group_id}/schedule")
    lessons = lessons_from_dict(data.get("lessons", []))
    return int(data.get("version", 0)), data.get("updated_at"), lessons


def publish_group_schedule(
    group_id: str, lessons: tuple[Lesson, ...]
) -> dict[str, Any]:
    return _request(
        "PUT",
        f"/groups/{group_id}/schedule",
        json={"lessons": lessons_to_dict(lessons)},
    )


def get_group_version(group_id: str) -> dict[str, Any]:
    return _request("GET", f"/groups/{group_id}/version")
