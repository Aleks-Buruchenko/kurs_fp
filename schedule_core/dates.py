from __future__ import annotations

from datetime import date, timedelta

from schedule_core.models import Lesson, WeekType

WEEKDAY_NAMES = (
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
)


def week_number(semester_start: date, today: date) -> int:
    """Номер учебной недели от начала семестра (1-based)."""
    if today < semester_start:
        return 1
    delta_days = (today - semester_start).days
    return delta_days // 7 + 1


def is_even_week(semester_start: date, today: date) -> bool:
    return week_number(semester_start, today) % 2 == 0


def week_matches(lesson: Lesson, even: bool) -> bool:
    week: WeekType = lesson.week
    if week == "both":
        return True
    return (week == "even") == even


def monday_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def parse_date(value: str) -> date:
    """YYYY-MM-DD."""
    parts = value.strip().split("-")
    if len(parts) != 3:
        raise ValueError(f"Ожидается YYYY-MM-DD, получено: {value!r}")
    year, month, day = (int(p) for p in parts)
    return date(year, month, day)


def parse_time(value: str):
    from datetime import time

    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Ожидается HH:MM, получено: {value!r}")
    hour, minute = (int(p) for p in parts)
    return time(hour, minute)
