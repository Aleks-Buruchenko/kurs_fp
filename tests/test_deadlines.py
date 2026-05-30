from datetime import date

from schedule_core.deadlines import tasks_by_subject, upcoming_tasks
from schedule_core.models import Task


def test_upcoming_sorted():
    tasks = (
        Task("ФП", "ЛР2", date(2026, 5, 20)),
        Task("ФП", "ЛР1", date(2026, 5, 10)),
        Task("Алгебра", "ДЗ", date(2026, 4, 1)),
    )
    result = upcoming_tasks(tasks, date(2026, 5, 1))
    assert [task.title for task in result] == ["ЛР1", "ЛР2"]


def test_group_by_subject():
    tasks = (
        Task("ФП", "a", date(2026, 5, 1)),
        Task("Алгебра", "b", date(2026, 5, 2)),
        Task("ФП", "c", date(2026, 5, 3)),
    )
    grouped = tasks_by_subject(tasks)
    assert len(grouped["ФП"]) == 2
