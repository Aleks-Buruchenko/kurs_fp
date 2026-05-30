from __future__ import annotations

from dataclasses import dataclass

from schedule_core.conflicts import LessonConflict, find_lesson_conflicts
from schedule_core.models import Lesson


@dataclass(frozen=True)
class ScheduleValidationError:
    message: str
    lesson_index: int | None = None


def _with_index(
    error: ScheduleValidationError, lesson_index: int
) -> ScheduleValidationError:
    return ScheduleValidationError(
        message=error.message,
        lesson_index=lesson_index,
    )


def time_range_error(lesson: Lesson) -> ScheduleValidationError | None:
    if lesson.start < lesson.end:
        return None
    return ScheduleValidationError(
        message=(
            f"Время начала ({lesson.start.strftime('%H:%M')}) "
            f"должно быть раньше окончания ({lesson.end.strftime('%H:%M')})"
        ),
    )


def weekday_range_error(lesson: Lesson) -> ScheduleValidationError | None:
    if lesson.weekday in range(7):
        return None
    return ScheduleValidationError(
        message=f"День недели должен быть от 0 до 6, получено: {lesson.weekday}",
    )


def validate_lesson(lesson: Lesson) -> tuple[ScheduleValidationError, ...]:
    checks = (time_range_error(lesson), weekday_range_error(lesson))
    return tuple(error for error in checks if error is not None)


def conflict_to_validation_error(
    conflict: LessonConflict,
) -> ScheduleValidationError:
    return ScheduleValidationError(
        message=(
            f"Конфликт пар #{conflict.index_a + 1} ({conflict.lesson_a.subject}, "
            f"{conflict.lesson_a.start.strftime('%H:%M')}–"
            f"{conflict.lesson_a.end.strftime('%H:%M')}, "
            f"неделя {conflict.lesson_a.week}) и #{conflict.index_b + 1} "
            f"({conflict.lesson_b.subject}, "
            f"{conflict.lesson_b.start.strftime('%H:%M')}–"
            f"{conflict.lesson_b.end.strftime('%H:%M')}, "
            f"неделя {conflict.lesson_b.week})"
        ),
        lesson_index=conflict.index_a,
    )


def lesson_errors_for_schedule(
    lessons: tuple[Lesson, ...],
) -> tuple[ScheduleValidationError, ...]:
    return tuple(
        _with_index(error, index)
        for index, lesson in enumerate(lessons)
        for error in validate_lesson(lesson)
    )


def conflict_errors_for_schedule(
    lessons: tuple[Lesson, ...],
) -> tuple[ScheduleValidationError, ...]:
    return tuple(
        conflict_to_validation_error(conflict)
        for conflict in find_lesson_conflicts(lessons)
    )


def validate_schedule(lessons: tuple[Lesson, ...]) -> tuple[ScheduleValidationError, ...]:
    return lesson_errors_for_schedule(lessons) + conflict_errors_for_schedule(lessons)
