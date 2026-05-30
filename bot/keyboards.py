from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder

MAIN_MENU = (
    "Сегодня",
    "Завтра",
    "Неделя",
    "Ближайшая пара",
    "Дедлайны",
    "Статистика",
    "Группы",
    "Добавить пару",
    "Удалить пару",
    "Добавить задачу",
    "Удалить задачу",
    "Экспорт",
    "Помощь",
)


def main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for label in MAIN_MENU:
        builder.button(text=label)
    builder.adjust(2, 2, 2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def lesson_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Лекция", callback_data="lesson_type:lecture")
    builder.button(text="Практика", callback_data="lesson_type:practice")
    builder.button(text="Лабораторная", callback_data="lesson_type:lab")
    builder.adjust(1)
    return builder.as_markup()


def lesson_week_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Каждую неделю", callback_data="lesson_week:both")
    builder.button(text="Чётные недели", callback_data="lesson_week:even")
    builder.button(text="Нечётные недели", callback_data="lesson_week:odd")
    builder.adjust(1)
    return builder.as_markup()


def delete_lessons_keyboard(lessons: tuple) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, lesson in enumerate(lessons):
        builder.button(
            text=(
                f"{index + 1}. {lesson.subject} "
                f"({lesson.weekday}, {lesson.start.strftime('%H:%M')})"
            ),
            callback_data=f"delete_lesson:{index}",
        )
    builder.adjust(1)
    return builder.as_markup()


def group_menu_keyboard(
    *,
    has_group: bool,
    group_id: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Список групп", callback_data="grp:list")
    builder.button(text="➕ Создать группу", callback_data="grp:create")
    if has_group and group_id:
        builder.button(
            text=f"🔄 Синхронизировать ({group_id})",
            callback_data="grp:sync",
        )
        builder.button(text="ℹ️ Версия на сервере", callback_data="grp:version")
        builder.button(
            text="📤 Опубликовать моё расписание",
            callback_data="grp:publish",
        )
    builder.adjust(1)
    return builder.as_markup()


def groups_pick_keyboard(
    groups: tuple[str, ...] | list[str],
    *,
    action: str,
) -> InlineKeyboardMarkup:
    """action: join | publish — префикс callback grp:{action}:{group_id}."""
    builder = InlineKeyboardBuilder()
    for group_id in groups:
        builder.button(
            text=f"👥 {group_id}",
            callback_data=f"grp:{action}:{group_id}",
        )
    builder.button(text="◀️ В меню групп", callback_data="grp:menu")
    builder.adjust(1)
    return builder.as_markup()


def group_created_keyboard(group_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"✅ Выбрать {group_id}",
        callback_data=f"grp:join:{group_id}",
    )
    builder.button(
        text="📤 Опубликовать расписание",
        callback_data="grp:publish",
    )
    builder.button(text="◀️ В меню групп", callback_data="grp:menu")
    builder.adjust(1)
    return builder.as_markup()


def delete_tasks_keyboard(tasks: tuple) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, task in enumerate(tasks):
        builder.button(
            text=f"{index + 1}. {task.subject}: {task.title} ({task.due.isoformat()})",
            callback_data=f"delete_task:{index}",
        )
    builder.adjust(1)
    return builder.as_markup()
