from __future__ import annotations

from datetime import date, datetime, time, timedelta
from operator import attrgetter

from schedule_core.dates import is_even_week, week_matches
from schedule_core.models import Lesson


def lessons_on_day(
    lessons: tuple[Lesson, ...],
    weekday: int,
    semester_start: date,
    day: date,
) -> tuple[Lesson, ...]:
    even = is_even_week(semester_start, day)
    filtered = (
        lesson
        for lesson in lessons
        if lesson.weekday == weekday and week_matches(lesson, even)
    )
    return tuple(sorted(filtered, key=attrgetter("start")))


def lessons_for_date(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    day: date,
) -> tuple[Lesson, ...]:
    return lessons_on_day(lessons, day.weekday(), semester_start, day)


def lessons_today(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    today: date | None = None,
) -> tuple[Lesson, ...]:
    today = today or date.today()
    return lessons_for_date(lessons, semester_start, today)


def lessons_tomorrow(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    today: date | None = None,
) -> tuple[Lesson, ...]:
    today = today or date.today()
    return lessons_for_date(lessons, semester_start, today + timedelta(days=1))


def lessons_week(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    week_start: date,
) -> dict[int, tuple[Lesson, ...]]:
    """Расписание на 7 дней, ключ — weekday (0..6)."""
    return {
        (week_start + timedelta(days=offset)).weekday(): lessons_for_date(
            lessons,
            semester_start,
            week_start + timedelta(days=offset),
        )
        for offset in range(7)
    }


def _upcoming_lesson_slots(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    now: datetime,
) -> tuple[tuple[datetime, Lesson], ...]:
    return tuple(
        (start_dt, lesson)
        for offset in range(14)
        for day in (now.date() + timedelta(days=offset),)
        for lesson in lessons_for_date(lessons, semester_start, day)
        for start_dt in (datetime.combine(day, lesson.start),)
        if start_dt > now
    )


def next_lesson(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    now: datetime | None = None,
) -> tuple[datetime, Lesson] | None:
    now = now or datetime.now()
    candidates = _upcoming_lesson_slots(lessons, semester_start, now)
    if not candidates:
        return None
    return min(candidates, key=lambda pair: pair[0])
