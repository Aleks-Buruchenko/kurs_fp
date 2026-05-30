from __future__ import annotations

from schedule_core.validators import ScheduleValidationError


def validation_error_item(error: ScheduleValidationError) -> dict:
    return {
        "message": error.message,
        "lesson_index": error.lesson_index,
    }


def validation_errors_to_detail(
    errors: tuple[ScheduleValidationError, ...],
) -> dict:
    return {
        "message": "Расписание содержит ошибки",
        "errors": list(map(validation_error_item, errors)),
    }
