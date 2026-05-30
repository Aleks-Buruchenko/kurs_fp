from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from schedule_core.reminders import all_due_reminders
from schedule_core.io_json import load_user

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "users"


def setup_reminder_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def tick() -> None:
        now = datetime.now()
        for path in DATA_DIR.glob("*.json"):
            user = load_user(path)
            if user is None:
                continue
            try:
                user_id = int(path.stem)
            except ValueError:
                continue
            for reminder in all_due_reminders(
                user.lessons,
                user.tasks,
                user.semester_start,
                now=now,
            ):
                try:
                    await bot.send_message(user_id, f"🔔 {reminder.text}")
                except Exception as exc:
                    logger.warning("Не удалось отправить напоминание %s: %s", user_id, exc)

    scheduler.add_job(tick, "interval", minutes=1, id="reminders")
    return scheduler
