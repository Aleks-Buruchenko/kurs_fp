from __future__ import annotations

from datetime import date
from pathlib import Path

from schedule_core.io_json import load_user, save_user
from schedule_core.models import UserData

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "users"


def user_path(user_id: int) -> Path:
    return DATA_DIR / f"{user_id}.json"


def get_user(user_id: int) -> UserData:
    existing = load_user(user_path(user_id))
    if existing is not None:
        return existing
    default = UserData(semester_start=date.today())
    save_user(user_path(user_id), default)
    return default


def put_user(user_id: int, user: UserData) -> None:
    save_user(user_path(user_id), user)
