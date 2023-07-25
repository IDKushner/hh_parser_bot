import asyncio
from aiogram import types
from aiogram.dispatcher import Dispatcher
import re
from datetime import datetime

from db import (
    Vacancy,
    Review,
    enable_or_disable_admin,
    get_random_review,
    get_review_by_id,
)
from keyboards import resolve_review_kb
from main import send_vacancy
from SETTINGS import bot
from utils.general import strong, admin_only
from utils.prefetch_vacancy import prefetch_vacancy


@admin_only(superadmin=True)
async def enable_or_disable_admin_handler(message: types.Message):
    command, telegram_id = re.split(r"\s+", message.text)
    command = True if command.strip("/") == "enable_admin" else False

    if telegram_id:
        try:
            telegram_id = int(telegram_id)
        except:
            await message.answer(
                "Введён неверный Telegram_id пользователя. Проверить его можно здесь: @getmyid_bot"
            )

        try:
            await enable_or_disable_admin(telegram_id=telegram_id, is_admin=command)
            await message.answer("👌 Изменено")
        except:
            text = [
                "Для этой операции пользователю нужно сначала пройти регистрацию (/registration)",
                " в боте со своей учётной записи",
            ]
            await message.answer("".join(text))

    else:
        await message.answer(
            "Введён неверный Telegram_id пользователя. Проверить его можно здесь: @getmyid_bot"
        )


@admin_only()
async def get_review_to_resolve_handler(message: types.Message):
    review: Review = await get_random_review()

    await message.answer(
        f"<strong>Отзыв</strong>:\n{review.description}\n\nID отзыва: {review.id}",
        parse_mode=types.ParseMode.HTML,
        reply_markup=resolve_review_kb.get_kb(),
    )


@admin_only()
async def resolve_review_handler(query: types.CallbackQuery):
    """Помечает Review как разрешённый, удаляет сообщение админу о разрешении,
    и уведомляет юзера-ревьюера о разрешении"""
    review_id: str = re.findall(r"ID отзыва: \d+", query.message.text)[0]
    review_id: int = int(re.split(r"ID отзыва: ", review_id)[1])
    review: Review = await get_review_by_id(review_id=review_id)

    await review.resolve(
        admin_telegram_id=query.from_user.id, resolution_date=datetime.now()
    )

    await bot.edit_message_text(
        f"👌 Разрешено", query.from_user.id, query.message.message_id
    )

    await asyncio.sleep(10)
    await query.message.delete()


@admin_only()
async def custom_vacancy(message: types.Message):
    response = []

    try:
        validated_vacancy: Vacancy = await prefetch_vacancy(
            vacancy_text=message.text, from_admin=True
        )
        await send_vacancy(vacancy=validated_vacancy)

    except BaseException as e:
        response = [
            f"{e}\n",
            f'Нужно ввести следующую информацию {strong("строго каждое поле на отдельной строке")}',
            f'• {strong("id")}: id вакансии одним числом длиной до 10 цифр. Вводить на отдельной строке после команды /vacancy',
            f'• {strong("Название позиции")}: кого вы ищете. Например "Младший юрист в практику корпоративного права"',
            f'• {strong("Название работодателя")}',
            f'• {strong("Тип работодателя")}: "консалтинг" или "инхаус"',
            f'• {strong("Опыт")}: сколько лет опыта работы нужно для этой вакансии:'
            f'"0" (без опыта) или "1-3" (1-3 года опыта)',
            f'• {strong("Зарплата")}: зарплата/зарплатная вилка в формате "число - число", "от число" или "до число"',
            f'• {strong("Описание вакансии")} длиной не более 3900 символов.',
        ]

        await message.answer(text="\n".join(response), parse_mode=types.ParseMode.HTML)


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(
        enable_or_disable_admin_handler, commands=["enable_admin", "disable_admin"]
    )
    dp.register_message_handler(get_review_to_resolve_handler, commands=["get_review"])
    dp.register_callback_query_handler(
        resolve_review_handler, resolve_review_kb.cb.filter()
    )
    dp.register_message_handler(custom_vacancy, commands=["vacancy"])
