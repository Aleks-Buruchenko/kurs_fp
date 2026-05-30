from datetime import date, datetime, time

from schedule_core.models import Lesson, LessonType
from schedule_core.schedule import lessons_for_date, next_lesson


def _lesson(weekday: int, hour: int, week: str = "both") -> Lesson:
    return Lesson(
        subject="Математика",
        weekday=weekday,
        start=time(hour, 0),
        end=time(hour + 1, 30),
        room="101",
        teacher="Петров",
        lesson_type=LessonType.LECTURE,
        week=week,
    )


def test_lessons_sorted_by_time():
    start = date(2026, 2, 1)
    day = date(2026, 2, 2)
    lessons = (
        _lesson(day.weekday(), 11),
        _lesson(day.weekday(), 9),
    )
    result = lessons_for_date(lessons, start, day)
    assert [lesson.start.hour for lesson in result] == [9, 11]


def test_next_lesson_picks_earliest():
    start = date(2026, 2, 1)
    day = date(2026, 2, 2)
    lessons = (_lesson(day.weekday(), 14), _lesson(day.weekday(), 10))
    now = datetime.combine(day, time(8, 0))
    nxt = next_lesson(lessons, start, now)
    assert nxt is not None
    assert nxt[1].start.hour == 10
