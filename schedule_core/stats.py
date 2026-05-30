from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from schedule_core.dates import monday_of_week
from schedule_core.models import Lesson, Task
from schedule_core.schedule import lessons_week


def lessons_per_week(lessons: tuple[Lesson, ...]) -> int:
    """Число занятий за одну типовую неделю (both считается один раз)."""
    both = sum(1 for lesson in lessons if lesson.week == "both")
    alternating = sum(1 for lesson in lessons if lesson.week != "both")
    return both + alternating // 2 + alternating % 2


def deadlines_per_subject(tasks: tuple[Task, ...]) -> dict[str, int]:
    return dict(Counter(task.subject for task in tasks))


def busiest_days(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    week_start: date | None = None,
) -> list[tuple[int, int]]:
    week_start = week_start or monday_of_week(date.today())
    week = lessons_week(lessons, semester_start, week_start)
    counts = [(weekday, len(week.get(weekday, ()))) for weekday in range(7)]
    return sorted(counts, key=lambda item: (-item[1], item[0]))


def summary_stats(
    lessons: tuple[Lesson, ...],
    tasks: tuple[Task, ...],
    semester_start: date,
) -> dict[str, object]:
    return {
        "lessons_per_week": lessons_per_week(lessons),
        "deadlines_by_subject": deadlines_per_subject(tasks),
        "busiest_days": busiest_days(lessons, semester_start),
        "total_tasks": len(tasks),
    }
