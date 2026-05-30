from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, time
from enum import Enum
from typing import Literal

WeekType = Literal["even", "odd", "both"]


class LessonType(str, Enum):
    LECTURE = "лекция"
    PRACTICE = "практика"
    LAB = "лабораторная"


@dataclass(frozen=True)
class Lesson:
    subject: str
    weekday: int  # 0 = понедельник … 6 = воскресенье
    start: time
    end: time
    room: str
    teacher: str
    lesson_type: LessonType
    week: WeekType = "both"


@dataclass(frozen=True)
class Task:
    subject: str
    title: str
    due: date


@dataclass(frozen=True)
class UserData:
    semester_start: date
    lessons: tuple[Lesson, ...] = ()
    tasks: tuple[Task, ...] = ()
    group_id: str | None = None

    def with_lesson(self, lesson: Lesson) -> UserData:
        return replace(self, lessons=self.lessons + (lesson,))

    def with_task(self, task: Task) -> UserData:
        return replace(self, tasks=self.tasks + (task,))
