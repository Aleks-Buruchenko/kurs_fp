from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from schedule_core.io_json import lessons_from_dict, lessons_to_dict
from schedule_core.validators import validate_schedule
from sync_server import storage
from sync_server.responses import validation_errors_to_detail

app = FastAPI(
    title="StudyBot Sync Server",
    description="Сервер групповых расписаний для StudyBot",
    version="1.0.0",
)


class CreateGroupRequest(BaseModel):
    group_id: str = Field(min_length=1, max_length=64)


class SchedulePayload(BaseModel):
    lessons: list[dict]


def _ensure_valid_group_id(group_id: str) -> str:
    normalized = storage.normalize_group_id(group_id)
    if not storage.is_valid_group_id(normalized):
        raise HTTPException(
            status_code=400,
            detail="Некорректный идентификатор группы",
        )
    return normalized


def _ensure_group_exists(group_id: str) -> str:
    group_id = _ensure_valid_group_id(group_id)
    if not storage.group_exists(group_id):
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group_id


def _schedule_response(
    group_id: str,
    version: int,
    updated_at,
    lessons: tuple,
) -> dict:
    return {
        "group_id": group_id,
        "version": version,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "lessons": lessons_to_dict(lessons),
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/groups")
def get_groups() -> dict[str, list[str]]:
    return {"groups": storage.list_groups()}


@app.post("/groups", status_code=201)
def create_group(body: CreateGroupRequest) -> dict[str, str]:
    group_id = _ensure_valid_group_id(body.group_id)
    if storage.group_exists(group_id):
        raise HTTPException(status_code=409, detail="Группа уже существует")
    storage.create_group(group_id)
    return {"group_id": group_id}


@app.get("/groups/{group_id}/schedule")
def get_group_schedule(group_id: str) -> dict:
    group_id = _ensure_group_exists(group_id)
    version, updated_at, lessons = storage.load_schedule(group_id)
    return _schedule_response(group_id, version, updated_at, lessons)


@app.put("/groups/{group_id}/schedule")
def put_group_schedule(group_id: str, body: SchedulePayload) -> dict:
    group_id = _ensure_valid_group_id(group_id)
    if not storage.group_exists(group_id):
        storage.create_group(group_id)
    lessons = lessons_from_dict(body.lessons)
    errors = validate_schedule(lessons)
    if errors:
        raise HTTPException(status_code=400, detail=validation_errors_to_detail(errors))
    version, updated_at = storage.save_schedule(group_id, lessons)
    return {
        "group_id": group_id,
        "version": version,
        "updated_at": updated_at.isoformat(),
        "lesson_count": len(lessons),
    }


@app.get("/groups/{group_id}/version")
def get_group_version(group_id: str) -> dict:
    group_id = _ensure_group_exists(group_id)
    version, updated_at, lessons = storage.load_schedule(group_id)
    return {
        "group_id": group_id,
        "version": version,
        "updated_at": updated_at.isoformat() if updated_at else None,
        "lesson_count": len(lessons),
    }
