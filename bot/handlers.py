from __future__ import annotations

from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    delete_lessons_keyboard,
    delete_tasks_keyboard,
    lesson_type_keyboard,
    lesson_week_keyboard,
    main_keyboard,
)
from bot.storage import get_user, put_user
from schedule_core.user_ops import set_semester_start, without_lesson, without_task
from schedule_core.dates import monday_of_week, parse_date, parse_time
from schedule_core.deadlines import upcoming_tasks
from schedule_core.format_text import (
    export_schedule_text,
    export_tasks_text,
    format_day_lessons,
    format_next_lesson,
    format_stats,
    format_tasks,
)
from schedule_core.models import Lesson, LessonType, Task
from schedule_core.schedule import lessons_today, lessons_tomorrow, next_lesson
from schedule_core.stats import summary_stats

router = Router()

HELP_TEXT = """
<b>Учебный бот — расписание и дедлайны</b>

<b>Расписание:</b>
/today — пары на сегодня
/tomorrow — на завтра
/week — на текущую неделю
/next — ближайшая пара

<b>Дедлайны:</b>
/deadlines — ближайшие задачи
/add_task — добавить задачу
/delete_task — удалить задачу

<b>Пары:</b>
/add_lesson — добавить пару
/delete_lesson — удалить пару

<b>Групповое расписание:</b>
кнопка <b>Группы</b> в меню — список, создание, синхронизация, публикация
(всё через кнопки под сообщением)

<b>Прочее:</b>
/stats — статистика
/export — экспорт в текст
/set_semester YYYY-MM-DD — начало семестра (для чётности недель)
/import — вставьте JSON после команды

Кнопки меню дублируют основные команды.
Напоминания: за 1 ч до пары, за 1 день до дедлайна.
""".strip()


class AddLesson(StatesGroup):
    subject = State()
    weekday = State()
    start = State()
    end = State()
    room = State()
    teacher = State()
    lesson_type = State()
    week = State()


class AddTask(StatesGroup):
    subject = State()
    title = State()
    due = State()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    get_user(message.from_user.id)
    await message.answer(
        "Привет! Я помогу с расписанием и дедлайнами.\n"
        "Нажми /help или кнопки меню.",
        reply_markup=main_keyboard(),
    )


@router.message(Command("help"))
@router.message(F.text == "Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("set_semester"))
async def cmd_set_semester(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /set_semester 2026-02-01")
        return
    try:
        semester_start = parse_date(parts[1])
    except ValueError as exc:
        await message.answer(str(exc))
        return
    user = get_user(message.from_user.id)
    put_user(message.from_user.id, set_semester_start(user, semester_start))
    await message.answer(f"Начало семестра: {semester_start.strftime('%d.%m.%Y')}")


@router.message(Command("today"))
@router.message(F.text == "Сегодня")
async def cmd_today(message: Message) -> None:
    user = get_user(message.from_user.id)
    today = date.today()
    lessons = lessons_today(user.lessons, user.semester_start, today)
    await message.answer(format_day_lessons(lessons, today))


@router.message(Command("tomorrow"))
@router.message(F.text == "Завтра")
async def cmd_tomorrow(message: Message) -> None:
    user = get_user(message.from_user.id)
    tomorrow = date.today() + timedelta(days=1)
    lessons = lessons_tomorrow(user.lessons, user.semester_start, date.today())
    await message.answer(format_day_lessons(lessons, tomorrow))


@router.message(Command("week"))
@router.message(F.text == "Неделя")
async def cmd_week(message: Message) -> None:
    user = get_user(message.from_user.id)
    week_start = monday_of_week(date.today())
    text = export_schedule_text(user.lessons, user.semester_start, week_start)
    await message.answer(text)


@router.message(Command("next"))
@router.message(F.text == "Ближайшая пара")
async def cmd_next(message: Message) -> None:
    user = get_user(message.from_user.id)
    await message.answer(format_next_lesson(next_lesson(user.lessons, user.semester_start)))


@router.message(Command("deadlines"))
@router.message(F.text == "Дедлайны")
async def cmd_deadlines(message: Message) -> None:
    user = get_user(message.from_user.id)
    tasks = upcoming_tasks(user.tasks)
    await message.answer(format_tasks(tasks))


@router.message(Command("stats"))
@router.message(F.text == "Статистика")
async def cmd_stats(message: Message) -> None:
    user = get_user(message.from_user.id)
    stats = summary_stats(user.lessons, user.tasks, user.semester_start)
    await message.answer(format_stats(stats))


@router.message(Command("export"))
@router.message(F.text == "Экспорт")
async def cmd_export(message: Message) -> None:
    user = get_user(message.from_user.id)
    week_start = monday_of_week(date.today())
    schedule_text = export_schedule_text(user.lessons, user.semester_start, week_start)
    tasks_text = export_tasks_text(user.tasks)
    await message.answer(f"{schedule_text}\n\n{tasks_text}")


@router.message(Command("import"))
async def cmd_import(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Вставьте JSON после команды:\n/import {\"semester_start\": \"...\", ...}"
        )
        return
    try:
        from schedule_core.io_json import import_user_json

        user = import_user_json(parts[1])
        put_user(message.from_user.id, user)
        await message.answer("Данные импортированы.")
    except (ValueError, KeyError) as exc:
        await message.answer(f"Ошибка импорта: {exc}")


@router.message(Command("add_lesson"))
@router.message(F.text == "Добавить пару")
async def start_add_lesson(message: Message, state: FSMContext) -> None:
    await state.set_state(AddLesson.subject)
    await message.answer("Название предмета:")


@router.message(AddLesson.subject)
async def lesson_subject(message: Message, state: FSMContext) -> None:
    await state.update_data(subject=message.text.strip())
    await state.set_state(AddLesson.weekday)
    await message.answer("День недели (0=пн … 6=вс):")


@router.message(AddLesson.weekday)
async def lesson_weekday(message: Message, state: FSMContext) -> None:
    try:
        weekday = int(message.text.strip())
        if weekday not in range(7):
            raise ValueError
    except ValueError:
        await message.answer("Введите число от 0 до 6.")
        return
    await state.update_data(weekday=weekday)
    await state.set_state(AddLesson.start)
    await message.answer("Время начала (HH:MM):")


@router.message(AddLesson.start)
async def lesson_start(message: Message, state: FSMContext) -> None:
    try:
        start = parse_time(message.text)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(start=start)
    await state.set_state(AddLesson.end)
    await message.answer("Время окончания (HH:MM):")


@router.message(AddLesson.end)
async def lesson_end(message: Message, state: FSMContext) -> None:
    try:
        end = parse_time(message.text)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(end=end)
    await state.set_state(AddLesson.room)
    await message.answer("Аудитория:")


@router.message(AddLesson.room)
async def lesson_room(message: Message, state: FSMContext) -> None:
    await state.update_data(room=message.text.strip())
    await state.set_state(AddLesson.teacher)
    await message.answer("Преподаватель:")


@router.message(AddLesson.teacher)
async def lesson_teacher(message: Message, state: FSMContext) -> None:
    await state.update_data(teacher=message.text.strip())
    await state.set_state(AddLesson.lesson_type)
    await message.answer(
        "Выберите тип пары:",
        reply_markup=lesson_type_keyboard(),
    )


@router.callback_query(AddLesson.lesson_type, F.data.startswith("lesson_type:"))
async def lesson_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    mapping = {
        "lecture": LessonType.LECTURE,
        "practice": LessonType.PRACTICE,
        "lab": LessonType.LAB,
    }
    value = callback_query.data.split(":", maxsplit=1)[1]
    if value not in mapping:
        await callback_query.answer("Неверный тип пары.", show_alert=True)
        return
    await state.update_data(lesson_type=mapping[value])
    await state.set_state(AddLesson.week)
    await callback_query.message.answer(
        "Выберите, по каким неделям проходит пара:",
        reply_markup=lesson_week_keyboard(),
    )
    await callback_query.answer()


@router.callback_query(AddLesson.week, F.data.startswith("lesson_week:"))
async def lesson_week(callback_query: CallbackQuery, state: FSMContext) -> None:
    week = callback_query.data.split(":", maxsplit=1)[1]
    if week not in ("both", "even", "odd"):
        await callback_query.answer("Неверный тип недели.", show_alert=True)
        return
    data = await state.get_data()
    lesson = Lesson(
        subject=data["subject"],
        weekday=data["weekday"],
        start=data["start"],
        end=data["end"],
        room=data["room"],
        teacher=data["teacher"],
        lesson_type=data["lesson_type"],
        week=week,
    )
    user = get_user(callback_query.from_user.id)
    conflict = next(
        (
            existing
            for existing in user.lessons
            if existing.weekday == lesson.weekday and existing.start == lesson.start
        ),
        None,
    )
    if conflict is not None:
        await callback_query.message.answer(
            "Ошибка: на этот день и время уже стоит пара "
            f"({conflict.subject}, {conflict.start.strftime('%H:%M')})."
        )
        await callback_query.answer()
        return
    put_user(callback_query.from_user.id, user.with_lesson(lesson))
    await state.clear()
    await callback_query.message.answer(f"Пара добавлена: {lesson.subject}")
    await callback_query.answer()


@router.message(Command("add_task"))
@router.message(F.text == "Добавить задачу")
async def start_add_task(message: Message, state: FSMContext) -> None:
    await state.set_state(AddTask.subject)
    await message.answer("Предмет:")


@router.message(AddTask.subject)
async def task_subject(message: Message, state: FSMContext) -> None:
    await state.update_data(subject=message.text.strip())
    await state.set_state(AddTask.title)
    await message.answer("Название задачи:")


@router.message(AddTask.title)
async def task_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AddTask.due)
    await message.answer("Срок сдачи (YYYY-MM-DD):")


@router.message(AddTask.due)
async def task_due(message: Message, state: FSMContext) -> None:
    try:
        due = parse_date(message.text)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    data = await state.get_data()
    task = Task(subject=data["subject"], title=data["title"], due=due)
    user = get_user(message.from_user.id)
    put_user(message.from_user.id, user.with_task(task))
    await state.clear()
    await message.answer(f"Задача добавлена: {task.title} ({task.due})")


@router.message(Command("delete_lesson"))
@router.message(F.text == "Удалить пару")
async def start_delete_lesson(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user.lessons:
        await message.answer("Удалять нечего: у вас пока нет пар.")
        return
    await message.answer(
        "Выберите пару для удаления:",
        reply_markup=delete_lessons_keyboard(user.lessons),
    )


@router.callback_query(F.data.startswith("delete_lesson:"))
async def delete_lesson(callback_query: CallbackQuery) -> None:
    try:
        index = int(callback_query.data.split(":", maxsplit=1)[1])
    except ValueError:
        await callback_query.answer("Некорректный идентификатор.", show_alert=True)
        return
    user = get_user(callback_query.from_user.id)
    if index < 0 or index >= len(user.lessons):
        await callback_query.answer("Запись не найдена.", show_alert=True)
        return
    lesson = user.lessons[index]
    put_user(callback_query.from_user.id, without_lesson(user, index))
    await callback_query.message.edit_text(
        f"Пара удалена: {lesson.subject} ({lesson.start.strftime('%H:%M')})"
    )
    await callback_query.answer("Пара удалена")


@router.message(Command("delete_task"))
@router.message(F.text == "Удалить задачу")
async def start_delete_task(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user.tasks:
        await message.answer("Удалять нечего: у вас пока нет задач.")
        return
    await message.answer(
        "Выберите задачу для удаления:",
        reply_markup=delete_tasks_keyboard(user.tasks),
    )


@router.callback_query(F.data.startswith("delete_task:"))
async def delete_task(callback_query: CallbackQuery) -> None:
    try:
        index = int(callback_query.data.split(":", maxsplit=1)[1])
    except ValueError:
        await callback_query.answer("Некорректный идентификатор.", show_alert=True)
        return
    user = get_user(callback_query.from_user.id)
    if index < 0 or index >= len(user.tasks):
        await callback_query.answer("Запись не найдена.", show_alert=True)
        return
    task = user.tasks[index]
    put_user(callback_query.from_user.id, without_task(user, index))
    await callback_query.message.edit_text(
        f"Задача удалена: {task.subject}: {task.title}"
    )
    await callback_query.answer("Задача удалена")
