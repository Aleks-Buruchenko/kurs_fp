from datetime import time

from schedule_core.models import Lesson, LessonType
from schedule_core.validators import validate_lesson, validate_schedule


def _lesson(
    weekday: int = 0,
    start_h: int = 9,
    end_h: int = 10,
    week: str = "both",
) -> Lesson:
    return Lesson(
        subject="Математика",
        weekday=weekday,
        start=time(start_h, 0),
        end=time(end_h, 30),
        room="101",
        teacher="Иванов",
        lesson_type=LessonType.LECTURE,
        week=week,
    )


def test_validate_lesson_start_not_before_end():
    lesson = _lesson(start_h=12, end_h=10)
    errors = validate_lesson(lesson)
    assert len(errors) == 1
    assert "раньше" in errors[0].message


def test_validate_lesson_weekday_range():
    lesson = _lesson(weekday=7)
    errors = validate_lesson(lesson)
    assert any("0 до 6" in error.message for error in errors)


def test_validate_schedule_detects_conflict():
    lessons = (_lesson(week="both"), _lesson(week="both", start_h=9, end_h=11))
    errors = validate_schedule(lessons)
    assert any("Конфликт" in error.message for error in errors)
