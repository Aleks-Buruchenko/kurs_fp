from datetime import date, time

from schedule_core.models import Lesson, LessonType, Task
from schedule_core.stats import deadlines_per_subject, lessons_per_week


def test_deadlines_per_subject():
    tasks = (
        Task("ФП", "a", date(2026, 5, 1)),
        Task("ФП", "b", date(2026, 5, 2)),
        Task("Алгебра", "c", date(2026, 5, 3)),
    )
    assert deadlines_per_subject(tasks) == {"ФП": 2, "Алгебра": 1}


def test_lessons_per_week():
    lessons = (
        Lesson("A", 0, time(9, 0), time(10, 0), "1", "T", LessonType.LECTURE, "both"),
        Lesson("B", 1, time(9, 0), time(10, 0), "1", "T", LessonType.LECTURE, "even"),
        Lesson("C", 2, time(9, 0), time(10, 0), "1", "T", LessonType.LECTURE, "odd"),
    )
    assert lessons_per_week(lessons) == 2
