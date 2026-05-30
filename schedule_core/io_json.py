from __future__ import annotations

import json
from datetime import date, time
from pathlib import Path

from schedule_core.models import Lesson, LessonType, Task, UserData


def lesson_to_dict(lesson: Lesson) -> dict:
    return {
        "subject": lesson.subject,
        "weekday": lesson.weekday,
        "start": lesson.start.strftime("%H:%M"),
        "end": lesson.end.strftime("%H:%M"),
        "room": lesson.room,
        "teacher": lesson.teacher,
        "lesson_type": lesson.lesson_type.value,
        "week": lesson.week,
    }


def lesson_from_dict(data: dict) -> Lesson:
    h, m = (int(x) for x in data["start"].split(":"))
    eh, em = (int(x) for x in data["end"].split(":"))
    return Lesson(
        subject=data["subject"],
        weekday=int(data["weekday"]),
        start=time(h, m),
        end=time(eh, em),
        room=data.get("room", ""),
        teacher=data.get("teacher", ""),
        lesson_type=LessonType(data["lesson_type"]),
        week=data.get("week", "both"),
    )


def _task_to_dict(task: Task) -> dict:
    return {
        "subject": task.subject,
        "title": task.title,
        "due": task.due.isoformat(),
    }


def _task_from_dict(data: dict) -> Task:
    return Task(
        subject=data["subject"],
        title=data["title"],
        due=date.fromisoformat(data["due"]),
    )


def lessons_to_dict(lessons: tuple[Lesson, ...]) -> list[dict]:
    return [lesson_to_dict(lesson) for lesson in lessons]


def lessons_from_dict(items: list[dict]) -> tuple[Lesson, ...]:
    return tuple(lesson_from_dict(item) for item in items)


def user_to_dict(user: UserData) -> dict:
    data = {
        "semester_start": user.semester_start.isoformat(),
        "lessons": lessons_to_dict(user.lessons),
        "tasks": [_task_to_dict(task) for task in user.tasks],
    }
    if user.group_id is not None:
        data["group_id"] = user.group_id
    return data


def user_from_dict(data: dict) -> UserData:
    return UserData(
        semester_start=date.fromisoformat(data["semester_start"]),
        lessons=lessons_from_dict(data.get("lessons", [])),
        tasks=tuple(_task_from_dict(item) for item in data.get("tasks", [])),
        group_id=data.get("group_id"),
    )


def load_user(path: Path) -> UserData | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as file:
        return user_from_dict(json.load(file))


def save_user(path: Path, user: UserData) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(user_to_dict(user), file, ensure_ascii=False, indent=2)


def import_user_json(text: str) -> UserData:
    return user_from_dict(json.loads(text))
