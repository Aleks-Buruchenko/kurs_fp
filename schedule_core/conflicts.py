from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from schedule_core.models import Lesson


@dataclass(frozen=True)
class LessonConflict:
    index_a: int
    index_b: int
    lesson_a: Lesson
    lesson_b: Lesson


def lessons_overlap(a: Lesson, b: Lesson) -> bool:
    return a.weekday == b.weekday and a.start < b.end and b.start < a.end


def week_rules_intersect(a: Lesson, b: Lesson) -> bool:
    return a.week == "both" or b.week == "both" or a.week == b.week


def lessons_conflict(a: Lesson, b: Lesson) -> bool:
    return lessons_overlap(a, b) and week_rules_intersect(a, b)


def lesson_pair_conflict(
    index_a: int,
    lesson_a: Lesson,
    index_b: int,
    lesson_b: Lesson,
) -> LessonConflict | None:
    if not lessons_conflict(lesson_a, lesson_b):
        return None
    return LessonConflict(
        index_a=index_a,
        index_b=index_b,
        lesson_a=lesson_a,
        lesson_b=lesson_b,
    )


def find_lesson_conflicts(lessons: tuple[Lesson, ...]) -> tuple[LessonConflict, ...]:
    indexed = tuple(enumerate(lessons))
    return tuple(
        conflict
        for (index_a, lesson_a), (index_b, lesson_b) in combinations(indexed, 2)
        if (
            conflict := lesson_pair_conflict(
                index_a, lesson_a, index_b, lesson_b
            )
        )
        is not None
    )
