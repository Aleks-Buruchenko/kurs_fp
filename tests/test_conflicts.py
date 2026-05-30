from datetime import time

from schedule_core.conflicts import (
    find_lesson_conflicts,
    lessons_overlap,
    week_rules_intersect,
)
from schedule_core.models import Lesson, LessonType


def _lesson(
    weekday: int = 0,
    start_h: int = 9,
    end_h: int = 10,
    week: str = "both",
    subject: str = "A",
) -> Lesson:
    return Lesson(
        subject=subject,
        weekday=weekday,
        start=time(start_h, 0),
        end=time(end_h, 30),
        room="101",
        teacher="Иванов",
        lesson_type=LessonType.LECTURE,
        week=week,
    )


def test_lessons_overlap_same_day_and_time():
    a = _lesson(start_h=9, end_h=11)
    b = _lesson(start_h=10, end_h=12, subject="B")
    assert lessons_overlap(a, b)


def test_lessons_do_not_overlap_different_days():
    a = _lesson(weekday=0)
    b = _lesson(weekday=1)
    assert not lessons_overlap(a, b)


def test_week_rules_even_odd_do_not_intersect():
    even = _lesson(week="even")
    odd = _lesson(week="odd", subject="B")
    assert not week_rules_intersect(even, odd)


def test_week_rules_both_intersects_with_even():
    both = _lesson(week="both")
    even = _lesson(week="even", subject="B")
    assert week_rules_intersect(both, even)


def test_find_conflicts_even_odd_same_slot():
    lessons = (_lesson(week="even"), _lesson(week="odd", subject="B"))
    assert find_lesson_conflicts(lessons) == ()


def test_find_conflicts_even_even_same_slot():
    lessons = (_lesson(week="even"), _lesson(week="even", subject="B"))
    conflicts = find_lesson_conflicts(lessons)
    assert len(conflicts) == 1
