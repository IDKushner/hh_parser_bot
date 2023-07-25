from aiogram import types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
from sqlalchemy import ChunkedIteratorResult
from typing import Iterable

from handlers import admin, other
from SETTINGS import bot, dp
from db import Base, get_unsent_vacancies, Vacancy, User
from hh_parser import parse_vacancies
from keyboards import vacancy_kb_show_desc
from utils.general import get_message_text


scheduler = AsyncIOScheduler()

today = datetime.datetime.today().strftime("%d.%m.%Y")
today_night = datetime.datetime.strptime(f"{today} 23:30", "%d.%m.%Y %H:%M")

# запуск в 23:30 каждый день
trigger = IntervalTrigger(days=1, start_date=today_night)


async def safe_send_message(telegram_id: int, vacancy: Vacancy):
    """Telegram плохо читает HTML-разметку, а на HH вакансии отформатированы как HTML
    => Если все нечитаемые теги удалось отловить и отформатировать, то отправляю через HTML,
    если удалось отловить не все (и возвращается ошибка из-за нечитаемого тега), то в MD
    """

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=get_message_text(vacancy),
            parse_mode=types.ParseMode.HTML,
            reply_markup=vacancy_kb_show_desc(vacancy),
        )

    except:
        await bot.send_message(
            chat_id=telegram_id,
            text=get_message_text(vacancy),
            parse_mode=types.ParseMode.MARKDOWN,
            reply_markup=vacancy_kb_show_desc(vacancy),
        )


async def send_vacancy(vacancy: Vacancy):
    suitable_users: ChunkedIteratorResult[User] = await vacancy.get_suitable_users()
    # форматируем выдачу ChunkedIteratorResult так, как нам надо
    suitable_users: Iterable[User] = (
        suitable_user[0] for suitable_user in suitable_users
    )
    requests = [
        safe_send_message(telegram_id=suitable_user.telegram_id, vacancy=vacancy)
        for suitable_user in suitable_users
    ]

    await asyncio.gather(*requests)
    await vacancy.change_status()


async def main():
    await parse_vacancies()

    vacancies: ChunkedIteratorResult[Vacancy] = await get_unsent_vacancies()
    requests = [send_vacancy(vacancy[0]) for vacancy in vacancies]

    await asyncio.gather(*requests)


def register_all_handlers(dp: Dispatcher):
    admin.register_handlers_admin(dp)
    other.register_handlers_other(dp)


async def on_startup(_):
    register_all_handlers(dp)
    await Base.start()
    scheduler.start()
    scheduler.add_job(func=main, trigger=trigger, id=main.__name__)


async def on_shutdown(_):
    await Base.shutdown()
    scheduler.shutdown()


if __name__ == "__main__":
    executor.start_polling(
        dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True
    )
