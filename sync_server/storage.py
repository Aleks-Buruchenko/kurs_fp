from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from schedule_core.models import Lesson
from sync_server.schedule_data import (
    StoredGroupSchedule,
    resolve_publish_version,
    schedule_from_dict,
    schedule_to_dict,
)

GROUP_ID_PATTERN = re.compile(r"^[A-Za-z0-9А-Яа-яЁё._-]{1,64}$")

DATA_DIR = Path(__file__).resolve().parent.parent / "server_data" / "groups"


def normalize_group_id(group_id: str) -> str:
    return group_id.strip()


def is_valid_group_id(group_id: str) -> bool:
    return bool(GROUP_ID_PATTERN.match(group_id))


def group_dir(group_id: str) -> Path:
    return DATA_DIR / group_id


def schedule_path(group_id: str) -> Path:
    return group_dir(group_id) / "schedule.json"


def list_groups() -> list[str]:
    if not DATA_DIR.exists():
        return []
    return sorted(
        path.name
        for path in DATA_DIR.iterdir()
        if path.is_dir() and is_valid_group_id(path.name)
    )


def group_exists(group_id: str) -> bool:
    return schedule_path(group_id).exists()


def read_schedule_file(path: Path) -> StoredGroupSchedule:
    with path.open(encoding="utf-8") as file:
        return schedule_from_dict(json.load(file))


def write_schedule_file(path: Path, schedule: StoredGroupSchedule) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(schedule_to_dict(schedule), file, ensure_ascii=False, indent=2)


def load_schedule(group_id: str) -> tuple[int, datetime | None, tuple[Lesson, ...]]:
    path = schedule_path(group_id)
    if not path.exists():
        raise FileNotFoundError(group_id)
    stored = read_schedule_file(path)
    return stored.version, stored.updated_at, stored.lessons


def create_group(group_id: str) -> None:
    path = schedule_path(group_id)
    if path.exists():
        return
    write_schedule_file(
        path,
        StoredGroupSchedule(version=0, updated_at=None, lessons=()),
    )


def save_schedule(
    group_id: str,
    lessons: tuple[Lesson, ...],
    *,
    version: int | None = None,
) -> tuple[int, datetime]:
    path = schedule_path(group_id)
    exists = path.exists()
    current_version = 0
    if exists:
        current_version = read_schedule_file(path).version
    next_version = resolve_publish_version(
        explicit=version,
        file_exists=exists,
        current_version=current_version,
    )
    updated_at = datetime.now(timezone.utc)
    write_schedule_file(
        path,
        StoredGroupSchedule(
            version=next_version,
            updated_at=updated_at,
            lessons=lessons,
        ),
    )
    return next_version, updated_at
