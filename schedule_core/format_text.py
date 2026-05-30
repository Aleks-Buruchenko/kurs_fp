from __future__ import annotations

from datetime import date, datetime

from schedule_core.dates import WEEKDAY_NAMES
from schedule_core.models import Lesson, Task
from schedule_core.schedule import lessons_week


def _format_time(t) -> str:
    return t.strftime("%H:%M")


def format_lesson(lesson: Lesson) -> str:
    return (
        f"{_format_time(lesson.start)}–{_format_time(lesson.end)} | "
        f"{lesson.subject} ({lesson.lesson_type.value})\n"
        f"  {lesson.room}, {lesson.teacher}"
    )


def format_day_lessons(lessons: tuple[Lesson, ...], day: date) -> str:
    title = f"{WEEKDAY_NAMES[day.weekday()]}, {day.strftime('%d.%m.%Y')}"
    if not lessons:
        return f"{title}\n\nЗанятий нет."
    body = "\n\n".join(format_lesson(lesson) for lesson in lessons)
    return f"{title}\n\n{body}"


def format_week(week: dict[int, tuple[Lesson, ...]], week_start: date) -> str:
    from datetime import timedelta

    lines = [f"Неделя с {week_start.strftime('%d.%m.%Y')}:\n"]
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        lessons = week.get(day.weekday(), ())
        lines.append(f"\n{WEEKDAY_NAMES[day.weekday()]} ({day.strftime('%d.%m')}):")
        if lessons:
            for lesson in lessons:
                lines.append(f"  - {format_lesson(lesson)}")
        else:
            lines.append("  —")
    return "\n".join(lines)


def format_next_lesson(pair: tuple[datetime, Lesson] | None) -> str:
    if pair is None:
        return "Ближайших пар не найдено."
    start_dt, lesson = pair
    return (
        f"Ближайшая пара: {lesson.subject}\n"
        f"Когда: {start_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"{format_lesson(lesson)}"
    )


def format_tasks(tasks: tuple[Task, ...], header: str = "Дедлайны") -> str:
    if not tasks:
        return f"{header}\n\nЗадач нет."
    lines = [header, ""]
    for task in tasks:
        lines.append(
            f"- {task.due.strftime('%d.%m.%Y')} — {task.subject}: {task.title}"
        )
    return "\n".join(lines)


def format_stats(stats: dict[str, object]) -> str:
    from schedule_core.dates import WEEKDAY_NAMES

    lines = [
        "Статистика",
        "",
        f"Пар в неделю: {stats['lessons_per_week']}",
        f"Всего задач: {stats['total_tasks']}",
        "",
        "Дедлайны по предметам:",
    ]
    by_subject: dict[str, int] = stats["deadlines_by_subject"]  # type: ignore[assignment]
    if not by_subject:
        lines.append("  —")
    else:
        for subject, count in sorted(by_subject.items()):
            lines.append(f"  - {subject}: {count}")

    lines.append("")
    lines.append("Загруженность по дням:")
    busiest: list[tuple[int, int]] = stats["busiest_days"]  # type: ignore[assignment]
    for weekday, count in busiest:
        lines.append(f"  - {WEEKDAY_NAMES[weekday]}: {count} пар")

    return "\n".join(lines)


def export_schedule_text(
    lessons: tuple[Lesson, ...],
    semester_start: date,
    week_start: date,
) -> str:
    week = lessons_week(lessons, semester_start, week_start)
    return format_week(week, week_start)


def export_tasks_text(tasks: tuple[Task, ...]) -> str:
    return format_tasks(tasks, header="Экспорт задач")
