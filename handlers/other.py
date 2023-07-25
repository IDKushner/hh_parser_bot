from aiogram import types
from aiogram.dispatcher import FSMContext, Dispatcher
import re

from db import (
    Vacancy,
    User,
    Review,
    get_user_by_id,
    check_if_user_exists,
    get_vacancy_by_id,
)
from keyboards import (
    desc_cb,
    experience_kb,
    salary_kb,
    tags_kb,
    desired_employer_types_kb,
    all_tags,
    all_salary_types,
    all_desired_employer_types,
    vacancy_kb_hide_desc,
    vacancy_kb_show_desc,
)
from SETTINGS import bot, SUPERUSER_TELEGRAM_IDS as STID
from states import Registration
from utils.general import strong, get_message_text, prefetch_data


async def help_hendler(message: types.Message):
    commands_with_descriptions: list = [
        f"{strong('Список комманд')}:",
        f"{strong('/help')}: вывести список комманд бота",
        f"{strong('/update')}: перепройти регистрацию, чтобы обновить данные о себе",
        f"{strong('/review')}: отправить отзыв",
    ]

    asking_user = await get_user_by_id(message.from_user.id)
    if asking_user.is_admin:
        admin_commands: list = [
            "",
            f"{strong('/get_review')}: получить отзыв для разрешения",
            f"{strong('/vacancy')}: опубликовать вакансию не с hh.ru (нужно заполнить ряд полей, каждое с новой строки)",
        ]

        commands_with_descriptions.extend(admin_commands)

    if message.from_user.id in STID:
        superuser_commands: list = [
            "",
            f"{strong('/enable_admin')}: назначить админа",
            f"{strong('/disable_admin')}: лишить прав админа",
        ]

        commands_with_descriptions.extend(superuser_commands)

    await message.answer(
        "\n".join(commands_with_descriptions), parse_mode=types.ParseMode.HTML
    )


async def register(message: types.Message):
    if not await check_if_user_exists(message.from_user.id):
        await Registration.experience.set()
        response = [
            "Привет!",
            "Чтобы зарегистрироваться, тебе нужно ответить на 4 вопроса",
            "Начнём: 1️⃣ какой у тебя опыт работы?",
        ]
        await message.answer(
            text="\n".join(response), reply_markup=experience_kb.get_kb()
        )

    else:
        response = [
            "Ты уже зарегистрирован, но можешь воспользоваться командой /update",
            " чтобы перепройти регистрацию и обновить информацию о себе",
        ]
        await message.answer(text="".join(response))


async def update(message: types.Message):
    if await check_if_user_exists(message.from_user.id):
        await Registration.experience.set()
        response = [
            "Привет!",
            "Чтобы обновить информацию, тебе нужно ответить на те же 4 вопроса",
            "Начнём: 1️⃣ какой у тебя опыт работы?",
        ]
        await message.answer(
            text="\n".join(response), reply_markup=experience_kb.get_kb()
        )

    else:
        response = [
            "Ты ещё не зарегистрирован, но можешь это сделать",
            " с помощью команды /registration",
        ]
        await message.answer(text="".join(response))


async def add_experience_cb_handler(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    async with state.proxy() as data:
        data["experience_id"] = int(callback_data["button_id"]) + 1

    await Registration.next()
    await bot.edit_message_text(
        f"2️⃣ На какую минимальную зп согласен?",
        query.from_user.id,
        query.message.message_id,
        reply_markup=salary_kb.get_kb(),
    )


async def add_salary_cb_handler(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    async with state.proxy() as data:
        salary_type = all_salary_types[int(callback_data["button_id"])]
        data["salary"] = int("".join(salary_type.split(" ")[1:]))

    await Registration.next()
    await bot.edit_message_text(
        f"3️⃣ Выбери интересные тебе отрасли",
        query.from_user.id,
        query.message.message_id,
        reply_markup=tags_kb.get_kb(),
    )


async def add_tags_cb_handler(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    button_id = int(callback_data["button_id"])
    tag_name = all_tags[button_id]
    prefetched_element_name = "tags"

    async with state.proxy() as data:
        data = prefetch_data(
            data=data, element_name=prefetched_element_name, element_value=tag_name
        )

    await bot.edit_message_text(
        f"3️⃣ Выбери интересные тебе отрасли",
        query.from_user.id,
        query.message.message_id,
        reply_markup=tags_kb.get_kb(data[prefetched_element_name]),
    )


async def transition_to_desired_employer_types(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    await Registration.next()
    await bot.edit_message_text(
        f"4️⃣ Выбери интересующих тебя работодателей",
        query.from_user.id,
        query.message.message_id,
        reply_markup=desired_employer_types_kb.get_kb(),
    )


async def add_desired_employer_types_handler(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    button_id = int(callback_data["button_id"])
    desired_employer_type_name = all_desired_employer_types[button_id]
    prefetched_element_name = "desired_employer_type_names"

    async with state.proxy() as data:
        data = prefetch_data(
            data=data,
            element_name=prefetched_element_name,
            element_value=desired_employer_type_name,
        )

    await bot.edit_message_text(
        f"4️⃣ Выбери интересующих тебя работодателей",
        query.from_user.id,
        query.message.message_id,
        reply_markup=desired_employer_types_kb.get_kb(data[prefetched_element_name]),
    )


async def finish_registration(
    query: types.CallbackQuery, callback_data: dict, state: FSMContext
):
    async with state.proxy() as data:
        user = User(
            telegram_id=query.from_user.id,
            username=query.from_user.username,
            experience_id=data["experience_id"],
            salary=data["salary"],
            tags=data["tags"],
            desired_employer_type_names=data["desired_employer_type_names"],
        )

        await user.add_or_update()

    await bot.edit_message_text(
        f"👌 Я тебя запомнил", query.from_user.id, query.message.message_id
    )
    await state.finish()


async def show_desc_handler(query: types.CallbackQuery, callback_data: dict):
    vacancy_id: str = re.findall(r"ID: \d+", query.message.text)[0]
    vacancy_id: int = int(vacancy_id.split("ID: ")[1])

    vacancy: Vacancy = await get_vacancy_by_id(vacancy_id=vacancy_id)

    try:
        await bot.edit_message_text(
            chat_id=query.from_user.id,
            message_id=query.message.message_id,
            text=get_message_text(vacancy, show_desc=True),
            parse_mode=types.ParseMode.HTML,
            reply_markup=vacancy_kb_hide_desc(vacancy),
        )

    except:
        await bot.edit_message_text(
            chat_id=query.from_user.id,
            message_id=query.message.message_id,
            text=get_message_text(vacancy, show_desc=True),
            parse_mode=types.ParseMode.MARKDOWN,
            reply_markup=vacancy_kb_hide_desc(vacancy),
        )


async def hide_desc_handler(query: types.CallbackQuery, callback_data: dict):
    vacancy_id: str = re.findall(r"ID: \d+", query.message.text)[0]
    vacancy_id: int = int(vacancy_id.split("ID: ")[1])

    vacancy: Vacancy = await get_vacancy_by_id(vacancy_id=vacancy_id)

    await bot.edit_message_text(
        get_message_text(vacancy),
        query.from_user.id,
        query.message.message_id,
        parse_mode=types.ParseMode.HTML,
        reply_markup=vacancy_kb_show_desc(vacancy),
    )


async def send_review(message: types.Message):
    review_text = re.split(r"/review", message.text)[1]

    if len(review_text) >= 20:
        review = Review(
            reviewer_telegram_id=message.from_user.id, description=review_text
        )
        await review.add()
        await message.reply("✍️ Спасибо за отзыв! Передал разработчикам")

    else:
        await message.reply(
            " ".join(
                [
                    "Слишком короткий отзыв. Помните, текст отзыва нужно написать",
                    "в том же сообщении, что и команду /review",
                ]
            )
        )


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(help_hendler, commands=["help"])
    dp.register_message_handler(register, commands=["registration", "start"])
    dp.register_message_handler(update, commands=["update"])
    dp.register_callback_query_handler(
        add_experience_cb_handler,
        experience_kb.cb.filter(),
        state=Registration.experience,
    )
    dp.register_callback_query_handler(
        add_salary_cb_handler, salary_kb.cb.filter(), state=Registration.salary
    )
    dp.register_callback_query_handler(
        add_tags_cb_handler, tags_kb.cb.filter(), state=Registration.tags
    )
    dp.register_callback_query_handler(
        transition_to_desired_employer_types,
        tags_kb.save_button_cb.filter(),
        state=Registration.tags,
    )
    dp.register_callback_query_handler(
        add_desired_employer_types_handler,
        desired_employer_types_kb.cb.filter(),
        state=Registration.desired_employer_types,
    )
    dp.register_callback_query_handler(
        finish_registration,
        desired_employer_types_kb.save_button_cb.filter(),
        state=Registration.desired_employer_types,
    )
    dp.register_callback_query_handler(
        show_desc_handler, desc_cb.filter(description="show")
    )
    dp.register_callback_query_handler(
        hide_desc_handler, desc_cb.filter(description="hide")
    )
    dp.register_message_handler(send_review, commands=["review"])
