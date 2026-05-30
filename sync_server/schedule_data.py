from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from schedule_core.io_json import lessons_from_dict, lessons_to_dict
from schedule_core.models import Lesson


@dataclass(frozen=True)
class StoredGroupSchedule:
    version: int
    updated_at: datetime | None
    lessons: tuple[Lesson, ...]


def parse_updated_at(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def schedule_from_dict(data: dict) -> StoredGroupSchedule:
    return StoredGroupSchedule(
        version=int(data.get("version", 0)),
        updated_at=parse_updated_at(data.get("updated_at")),
        lessons=lessons_from_dict(data.get("lessons", [])),
    )


def schedule_to_dict(schedule: StoredGroupSchedule) -> dict:
    return {
        "version": schedule.version,
        "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
        "lessons": lessons_to_dict(schedule.lessons),
    }


def resolve_publish_version(
    *,
    explicit: int | None,
    file_exists: bool,
    current_version: int,
) -> int:
    if explicit is not None:
        return explicit
    return 1 if not file_exists else current_version + 1
