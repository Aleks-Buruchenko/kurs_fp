from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from schedule_core.deadlines import upcoming_tasks
from schedule_core.models import Lesson, Task
from schedule_core.schedule import next_lesson


@dataclass(frozen=True)
class Reminder:
    kind: str  # "lesson" | "deadline"
    text: str
    fire_at: datetime


def lesson_reminders(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    lead_minutes: int = 60,
    now: datetime | None = None,
) -> tuple[Reminder, ...]:
    now = now or datetime.now()
    nxt = next_lesson(lessons, semester_start, now)
    if nxt is None:
        return ()

    start_dt, lesson = nxt
    fire_at = start_dt - timedelta(minutes=lead_minutes)
    if fire_at <= now:
        return ()

    return (
        Reminder(
            kind="lesson",
            text=(
                f"Через {lead_minutes} мин: {lesson.subject} "
                f"({lesson.lesson_type.value}, {lesson.room})"
            ),
            fire_at=fire_at,
        ),
    )


def deadline_reminders(
    tasks: tuple[Task, ...],
    lead_days: int = 1,
    notify_hour: int = 9,
    now: datetime | None = None,
) -> tuple[Reminder, ...]:
    now = now or datetime.now()
    today = now.date()
    result: list[Reminder] = []

    for task in upcoming_tasks(tasks, today, limit=None):
        reminder_day = task.due - timedelta(days=lead_days)
        fire_at = datetime.combine(reminder_day, time(notify_hour, 0))
        if fire_at <= now:
            continue
        when = "сегодня" if lead_days == 0 else f"через {lead_days} дн."
        result.append(
            Reminder(
                kind="deadline",
                text=f"Дедлайн {when}: {task.subject} — {task.title} (до {task.due})",
                fire_at=fire_at,
            )
        )

    return tuple(result)


def all_due_reminders(
    lessons: tuple[Lesson, ...],
    tasks: tuple[Task, ...],
    semester_start: date,
    now: datetime | None = None,
    lesson_lead_minutes: int = 60,
    deadline_lead_days: int = 1,
) -> tuple[Reminder, ...]:
    now = now or datetime.now()
    window_end = now + timedelta(minutes=1)
    reminders = lesson_reminders(
        lessons, semester_start, lesson_lead_minutes, now
    ) + deadline_reminders(tasks, deadline_lead_days, now=now)

    return tuple(
        reminder
        for reminder in reminders
        if now <= reminder.fire_at < window_end
    )
