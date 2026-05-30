from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.handlers import router
from bot.sync_handlers import router as sync_router
from bot.scheduler import setup_reminder_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv(ROOT / ".env")
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Укажите BOT_TOKEN в файле .env")

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.include_router(sync_router)

    scheduler = setup_reminder_scheduler(bot)
    scheduler.start()

    logger.info("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
