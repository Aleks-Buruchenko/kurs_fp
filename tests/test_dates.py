from datetime import date

from schedule_core.dates import is_even_week, week_number
from schedule_core.models import Lesson, LessonType
from schedule_core.dates import week_matches
from datetime import time


def test_week_number_starts_at_one():
    start = date(2026, 2, 1)
    assert week_number(start, start) == 1
    assert week_number(start, date(2026, 2, 8)) == 2


def test_even_week():
    start = date(2026, 2, 1)
    assert is_even_week(start, date(2026, 2, 1)) is True
    assert is_even_week(start, date(2026, 2, 8)) is False


def test_week_matches():
    lesson = Lesson(
        subject="ФП",
        weekday=0,
        start=time(9, 0),
        end=time(10, 30),
        room="301",
        teacher="Иванов",
        lesson_type=LessonType.LECTURE,
        week="even",
    )
    assert week_matches(lesson, True) is True
    assert week_matches(lesson, False) is False
