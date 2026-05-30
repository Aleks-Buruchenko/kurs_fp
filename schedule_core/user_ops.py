from __future__ import annotations

from dataclasses import replace
from datetime import date

from schedule_core.models import Lesson, Task, UserData


def set_semester_start(user: UserData, semester_start: date) -> UserData:
    return replace(user, semester_start=semester_start)


def set_group_id(user: UserData, group_id: str | None) -> UserData:
    return replace(user, group_id=group_id)


def replace_lessons(user: UserData, lessons: tuple[Lesson, ...]) -> UserData:
    return replace(user, lessons=lessons)


def remove_lesson_at(lessons: tuple[Lesson, ...], index: int) -> tuple[Lesson, ...]:
    return tuple(item for i, item in enumerate(lessons) if i != index)


def remove_task_at(tasks: tuple[Task, ...], index: int) -> tuple[Task, ...]:
    return tuple(item for i, item in enumerate(tasks) if i != index)


def without_lesson(user: UserData, index: int) -> UserData:
    return replace_lessons(user, remove_lesson_at(user.lessons, index))


def without_task(user: UserData, index: int) -> UserData:
    return replace(user, tasks=remove_task_at(user.tasks, index))
