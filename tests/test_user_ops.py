from datetime import date, time

from schedule_core.models import Lesson, LessonType, UserData
from schedule_core.user_ops import replace_lessons, set_group_id, without_lesson


def _lesson() -> Lesson:
    return Lesson(
        subject="A",
        weekday=0,
        start=time(9, 0),
        end=time(10, 0),
        room="1",
        teacher="T",
        lesson_type=LessonType.LECTURE,
    )


def test_replace_lessons_returns_new_user():
    user = UserData(semester_start=date(2026, 2, 1), lessons=())
    updated = replace_lessons(user, (_lesson(),))
    assert user.lessons == ()
    assert len(updated.lessons) == 1


def test_without_lesson_immutable():
    user = UserData(semester_start=date(2026, 2, 1), lessons=(_lesson(), _lesson()))
    updated = without_lesson(user, 0)
    assert len(user.lessons) == 2
    assert len(updated.lessons) == 1


def test_set_group_id():
    user = UserData(semester_start=date(2026, 2, 1))
    updated = set_group_id(user, "ИВТ-31")
    assert user.group_id is None
    assert updated.group_id == "ИВТ-31"
