from __future__ import annotations

from datetime import date
from itertools import groupby
from operator import attrgetter

from schedule_core.models import Task


def upcoming_tasks(
    tasks: tuple[Task, ...],
    today: date | None = None,
    limit: int | None = 10,
) -> tuple[Task, ...]:
    today = today or date.today()
    future = (task for task in tasks if task.due >= today)
    sorted_tasks = tuple(sorted(future, key=attrgetter("due")))
    if limit is None:
        return sorted_tasks
    return sorted_tasks[:limit]


def tasks_by_subject(tasks: tuple[Task, ...]) -> dict[str, tuple[Task, ...]]:
    sorted_tasks = sorted(tasks, key=attrgetter("subject", "due"))
    return {
        subject: tuple(group)
        for subject, group in groupby(sorted_tasks, key=attrgetter("subject"))
    }


def add_task(tasks: tuple[Task, ...], task: Task) -> tuple[Task, ...]:
    return tasks + (task,)
