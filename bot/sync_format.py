from __future__ import annotations

from typing import Any


def command_argument(text: str | None) -> str | None:
    parts = (text or "").split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else None


def format_group_menu(group_id: str | None) -> str:
    if group_id:
        return (
            "<b>Групповое расписание</b>\n\n"
            f"Ваша группа: <b>{group_id}</b>\n"
            "Выберите действие кнопками ниже."
        )
    return (
        "<b>Групповое расписание</b>\n\n"
        "Группа не выбрана.\n"
        "Откройте «Список групп» и нажмите на нужную."
    )


def format_groups_list_prompt(groups: tuple[str, ...] | list[str], *, action: str) -> str:
    if not groups:
        return (
            "На сервере пока нет групп.\n"
            "Нажмите «Создать группу» в меню."
        )
    if action == "join":
        return "Выберите группу, чтобы подписаться на её расписание:"
    return "Выберите группу, куда опубликовать ваше расписание:"


def format_validation_error_line(item: dict[str, Any]) -> str:
    prefix = ""
    lesson_index = item.get("lesson_index")
    if lesson_index is not None:
        prefix = f"Пара #{lesson_index + 1}: "
    return f"• {prefix}{item.get('message', item)}"


def format_server_error_detail(detail: Any) -> str:
    if not isinstance(detail, dict):
        return str(detail)
    if "errors" in detail:
        header = detail.get("message", "Ошибки валидации:")
        lines = (header,) + tuple(
            map(format_validation_error_line, detail["errors"])
        )
        return "\n".join(lines)
    if "message" in detail:
        return str(detail["message"])
    return str(detail)


def format_group_created(group_id: str) -> str:
    return (
        f"Группа «{group_id}» создана на сервере.\n"
        "Нажмите кнопку ниже, чтобы выбрать её или опубликовать расписание."
    )


def format_group_joined(group_id: str) -> str:
    return (
        f"Группа выбрана: <b>{group_id}</b>\n"
        "Нажмите «Синхронизировать», чтобы загрузить расписание."
    )


def format_sync_success(
    group_id: str,
    version: int,
    updated_at: str | None,
    lesson_count: int,
) -> str:
    return (
        f"Расписание группы «{group_id}» загружено.\n"
        f"Версия: {version}, обновлено: {updated_at or 'неизвестно'}\n"
        f"Пар: {lesson_count}. Дедлайны сохранены."
    )


def format_group_version_info(
    group_id: str,
    version: int,
    updated_at: str | None,
    lesson_count: int,
) -> str:
    return (
        f"Группа: {group_id}\n"
        f"Версия: {version}\n"
        f"Обновлено: {updated_at or '—'}\n"
        f"Пар в расписании: {lesson_count}"
    )


def format_publish_success(group_id: str, version: int, lesson_count: int) -> str:
    return (
        f"Расписание опубликовано для группы «{group_id}».\n"
        f"Версия: {version}, пар: {lesson_count}"
    )
