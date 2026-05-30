from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import (
    group_created_keyboard,
    group_menu_keyboard,
    groups_pick_keyboard,
)
from bot.storage import get_user, put_user
from bot.sync_client import (
    SyncServerError,
    SyncServerUnavailableError,
    create_group,
    get_group_schedule,
    get_group_version,
    get_groups,
    publish_group_schedule,
)
from bot.sync_format import (
    command_argument,
    format_group_created,
    format_group_joined,
    format_group_menu,
    format_group_version_info,
    format_groups_list_prompt,
    format_publish_success,
    format_server_error_detail,
    format_sync_success,
)
from schedule_core.models import UserData
from schedule_core.user_ops import replace_lessons, set_group_id

router = Router()

SERVER_UNAVAILABLE = "Сервер расписаний сейчас недоступен."


class GroupCreate(StatesGroup):
    name = State()


def parse_grp_callback(data: str) -> tuple[str, str | None]:
    """grp:action или grp:action:group_id → (action, group_id)."""
    parts = data.split(":", 2)
    action = parts[1] if len(parts) > 1 else ""
    group_id = parts[2] if len(parts) > 2 else None
    return action, group_id


async def send_group_menu(message: Message, user: UserData) -> None:
    await message.answer(
        format_group_menu(user.group_id),
        reply_markup=group_menu_keyboard(
            has_group=user.group_id is not None,
            group_id=user.group_id,
        ),
        parse_mode="HTML",
    )


async def edit_group_menu(callback: CallbackQuery, user: UserData) -> None:
    await callback.message.edit_text(
        format_group_menu(user.group_id),
        reply_markup=group_menu_keyboard(
            has_group=user.group_id is not None,
            group_id=user.group_id,
        ),
        parse_mode="HTML",
    )


def perform_join(user_id: int, group_id: str) -> UserData:
    user = get_user(user_id)
    updated = set_group_id(user, group_id)
    put_user(user_id, updated)
    return updated


def perform_sync(user_id: int, group_id: str) -> tuple[str, bool]:
    user = get_user(user_id)
    try:
        version, updated_at, lessons = get_group_schedule(group_id)
    except SyncServerUnavailableError:
        return SERVER_UNAVAILABLE, False
    except SyncServerError as exc:
        if exc.status_code == 404:
            return f"Группа «{group_id}» не найдена на сервере.", False
        return format_server_error_detail(exc.detail), False
    put_user(user_id, replace_lessons(user, lessons))
    return format_sync_success(group_id, version, updated_at, len(lessons)), True


def perform_version(group_id: str) -> tuple[str, bool]:
    try:
        info = get_group_version(group_id)
    except SyncServerUnavailableError:
        return SERVER_UNAVAILABLE, False
    except SyncServerError as exc:
        if exc.status_code == 404:
            return f"Группа «{group_id}» не найдена на сервере.", False
        return format_server_error_detail(exc.detail), False
    return (
        format_group_version_info(
            str(info.get("group_id", group_id)),
            int(info.get("version", 0)),
            info.get("updated_at"),
            int(info.get("lesson_count", 0)),
        ),
        True,
    )


def perform_publish(user_id: int, group_id: str) -> tuple[str, bool]:
    user = get_user(user_id)
    if not user.lessons:
        return "У вас нет пар для публикации.", False
    try:
        result = publish_group_schedule(group_id, user.lessons)
    except SyncServerUnavailableError:
        return SERVER_UNAVAILABLE, False
    except SyncServerError as exc:
        return format_server_error_detail(exc.detail), False
    return (
        format_publish_success(
            group_id,
            int(result.get("version", 0)),
            int(result.get("lesson_count", 0)),
        ),
        True,
    )


def perform_create(group_id: str) -> tuple[str, bool, bool]:
    """Возвращает (текст, успех, уже_существует)."""
    try:
        created = create_group(group_id)
    except SyncServerUnavailableError:
        return SERVER_UNAVAILABLE, False, False
    except SyncServerError as exc:
        if exc.status_code == 409:
            return f"Группа «{group_id}» уже существует.", False, True
        return format_server_error_detail(exc.detail), False, False
    return format_group_created(created), True, False


@router.message(Command("groups"))
@router.message(F.text == "Группы")
async def open_group_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = get_user(message.from_user.id)
    await send_group_menu(message, user)


@router.callback_query(F.data == "grp:menu")
async def cb_group_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user = get_user(callback.from_user.id)
    await edit_group_menu(callback, user)
    await callback.answer()


@router.callback_query(F.data == "grp:list")
async def cb_group_list(callback: CallbackQuery) -> None:
    try:
        groups = tuple(get_groups())
    except SyncServerUnavailableError:
        await callback.answer(SERVER_UNAVAILABLE, show_alert=True)
        return
    except SyncServerError as exc:
        await callback.answer(format_server_error_detail(exc.detail), show_alert=True)
        return
    await callback.message.edit_text(
        format_groups_list_prompt(groups, action="join"),
        reply_markup=groups_pick_keyboard(groups, action="join"),
    )
    await callback.answer()


@router.callback_query(F.data == "grp:create")
async def cb_group_create(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GroupCreate.name)
    await callback.message.edit_text(
        "Введите код новой группы (например <b>ИВТ-31</b>):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(GroupCreate.name)
async def group_create_name(message: Message, state: FSMContext) -> None:
    group_id = (message.text or "").strip()
    if not group_id:
        await message.answer("Название не может быть пустым. Введите код группы:")
        return
    text, ok, exists = perform_create(group_id)
    await state.clear()
    if not ok:
        user = get_user(message.from_user.id)
        if exists:
            await message.answer(
                text,
                reply_markup=groups_pick_keyboard((group_id,), action="join"),
            )
        else:
            await message.answer(text)
        return
    perform_join(message.from_user.id, group_id)
    await message.answer(
        text + f"\n\nГруппа «{group_id}» выбрана автоматически.",
        reply_markup=group_created_keyboard(group_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("grp:join:"))
async def cb_group_join(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    _, group_id = parse_grp_callback(callback.data or "")
    if not group_id:
        await callback.answer("Некорректные данные.", show_alert=True)
        return
    user = perform_join(callback.from_user.id, group_id)
    await callback.message.edit_text(
        format_group_joined(group_id),
        reply_markup=group_menu_keyboard(has_group=True, group_id=user.group_id),
        parse_mode="HTML",
    )
    await callback.answer("Группа выбрана")


@router.callback_query(F.data == "grp:sync")
async def cb_group_sync(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    if not user.group_id:
        await callback.answer("Сначала выберите группу.", show_alert=True)
        return
    text, ok = perform_sync(callback.from_user.id, user.group_id)
    if not ok:
        await callback.answer(text, show_alert=True)
        return
    await callback.message.answer(text)
    await callback.answer("Расписание загружено")


@router.callback_query(F.data == "grp:version")
async def cb_group_version(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    if not user.group_id:
        await callback.answer("Сначала выберите группу.", show_alert=True)
        return
    text, ok = perform_version(user.group_id)
    if not ok:
        await callback.answer(text, show_alert=True)
        return
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "grp:publish")
async def cb_group_publish(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    if user.group_id:
        text, ok = perform_publish(callback.from_user.id, user.group_id)
        if not ok:
            await callback.answer(text, show_alert=True)
            return
        await callback.message.answer(text)
        await callback.answer("Опубликовано")
        return
    try:
        groups = tuple(get_groups())
    except SyncServerUnavailableError:
        await callback.answer(SERVER_UNAVAILABLE, show_alert=True)
        return
    except SyncServerError as exc:
        await callback.answer(format_server_error_detail(exc.detail), show_alert=True)
        return
    if not groups:
        await callback.answer("Сначала создайте группу.", show_alert=True)
        return
    await callback.message.edit_text(
        format_groups_list_prompt(groups, action="publish"),
        reply_markup=groups_pick_keyboard(groups, action="publish"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("grp:publish:"))
async def cb_group_publish_pick(callback: CallbackQuery) -> None:
    _, group_id = parse_grp_callback(callback.data or "")
    if not group_id:
        await callback.answer("Некорректные данные.", show_alert=True)
        return
    text, ok = perform_publish(callback.from_user.id, group_id)
    if not ok:
        await callback.answer(text, show_alert=True)
        return
    user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        text,
        reply_markup=group_menu_keyboard(
            has_group=user.group_id is not None,
            group_id=user.group_id,
        ),
    )
    await callback.answer("Опубликовано")


# Команды /… оставлены для совместимости — открывают то же меню или выполняют действие
@router.message(Command("create_group"))
async def cmd_create_group(message: Message, state: FSMContext) -> None:
    group_id = command_argument(message.text)
    if group_id is None:
        await state.set_state(GroupCreate.name)
        await message.answer(
            "Введите код новой группы (например <b>ИВТ-31</b>):",
            parse_mode="HTML",
        )
        return
    text, ok, exists = perform_create(group_id)
    if not ok:
        await message.answer(text)
        return
    perform_join(message.from_user.id, group_id)
    await message.answer(
        text + f"\n\nГруппа «{group_id}» выбрана.",
        reply_markup=group_created_keyboard(group_id),
    )


@router.message(Command("join_group"))
async def cmd_join_group(message: Message, state: FSMContext) -> None:
    group_id = command_argument(message.text)
    if group_id is None:
        await open_group_menu(message, state)
        return
    user = perform_join(message.from_user.id, group_id)
    await message.answer(
        format_group_joined(group_id),
        reply_markup=group_menu_keyboard(has_group=True, group_id=user.group_id),
        parse_mode="HTML",
    )


@router.message(Command("sync"))
async def cmd_sync(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user.group_id:
        await message.answer("Сначала выберите группу в меню «Группы».")
        return
    text, _ok = perform_sync(message.from_user.id, user.group_id)
    await message.answer(text)


@router.message(Command("group_version"))
async def cmd_group_version(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user.group_id:
        await message.answer("Сначала выберите группу в меню «Группы».")
        return
    text, ok = perform_version(user.group_id)
    await message.answer(text)


@router.message(Command("publish_schedule"))
async def cmd_publish_schedule(message: Message) -> None:
    group_id = command_argument(message.text)
    user = get_user(message.from_user.id)
    target = group_id or user.group_id
    if not target:
        await message.answer("Откройте «Группы» и выберите группу кнопкой.")
        return
    text, ok = perform_publish(message.from_user.id, target)
    await message.answer(text)
